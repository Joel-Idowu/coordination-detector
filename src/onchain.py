"""
On-chain signal extraction for the coordination detector.

Uses the Helius Enhanced Transactions API to pull early buyers of a pool
and trace each buyer's funding source, then flags:
  - bundled supply: multiple early buyers funded by the same wallet
  - sniper clustering: an unusual number of buyers within a tight window
    after launch

NOTE: written from documented Helius v0 API patterns. This build
environment has no live network access, so these calls have not been run
against the real API yet -- `demo.py` proves the downstream scoring logic
with synthetic data, but run `main.py` against a real token early and
check the raw JSON output before trusting it. Helius occasionally tweaks
field names/response shape, so if a field lookup fails, print the raw
response and adjust the parsing below.
"""

import time
import requests

HELIUS_BASE = "https://api.helius.xyz/v0"


def _get_transactions(address, api_key, tx_type=None, before=None, limit=100):
    """Fetch a page of parsed transactions for an address."""
    url = f"{HELIUS_BASE}/addresses/{address}/transactions"
    params = {"api-key": api_key, "limit": limit}
    if tx_type:
        params["type"] = tx_type
    if before:
        params["before"] = before

    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code == 404:
        # Helius returns 404 for some addresses with little/no history
        # under this filter, rather than 200 + []. Treat as "no data"
        # instead of crashing the whole batch.
        return []
    resp.raise_for_status()
    return resp.json()


def get_early_buyers(pool_address, api_key, launch_timestamp=None,
                      max_buyers=50, max_pages=5, page_size=100):
    """
    Return the earliest buy transactions into a pool.

    launch_timestamp: unix seconds of pool creation, if known. Used to
    stop paginating once we've gone far enough back in time.
    """
    collected = []
    before_cursor = None

    for _ in range(max_pages):
        page = _get_transactions(
            pool_address, api_key, tx_type="SWAP",
            before=before_cursor, limit=page_size,
        )
        if not page:
            break

        for tx in page:
            buyer = tx.get("feePayer")
            ts = tx.get("timestamp")
            if buyer and ts:
                collected.append({
                    "wallet": buyer,
                    "timestamp": ts,
                    "signature": tx.get("signature"),
                })

        before_cursor = page[-1].get("signature")

        oldest_ts = page[-1].get("timestamp")
        if launch_timestamp and oldest_ts and oldest_ts < launch_timestamp:
            break

    collected.sort(key=lambda x: x["timestamp"])

    if launch_timestamp:
        collected = [c for c in collected if c["timestamp"] >= launch_timestamp]

    return collected[:max_buyers]


def trace_funding_source(wallet, api_key, page_size=100):
    """Find the earliest incoming transfer to a wallet and its sender."""
    page = _get_transactions(wallet, api_key, tx_type="TRANSFER", limit=page_size)
    if not page:
        return None

    incoming = []
    for tx in page:
        ts = tx.get("timestamp")
        for transfer in tx.get("nativeTransfers", []) + tx.get("tokenTransfers", []):
            to_account = transfer.get("toUserAccount")
            from_account = transfer.get("fromUserAccount")
            if to_account == wallet and from_account:
                incoming.append({"from": from_account, "timestamp": ts})

    if not incoming:
        return None

    incoming.sort(key=lambda x: x["timestamp"])
    return incoming[0]


def enrich_with_funding_sources(buyers, api_key, delay_seconds=0.2):
    """Attach a funding_source field to each buyer dict. Rate-limited."""
    for buyer in buyers:
        try:
            source = trace_funding_source(buyer["wallet"], api_key)
            buyer["funding_source"] = source["from"] if source else None
        except requests.exceptions.RequestException as e:
            print(f"  Warning: couldn't trace funding for {buyer['wallet']}: {e}")
            buyer["funding_source"] = None
        time.sleep(delay_seconds)  # be polite to the free tier
    return buyers


def detect_bundles(buyers, min_cluster_size=2):
    """Group buyers by shared funding source; flag clusters of size >= min."""
    by_funder = {}
    for b in buyers:
        funder = b.get("funding_source")
        if funder:
            by_funder.setdefault(funder, []).append(b["wallet"])

    return {
        funder: wallets
        for funder, wallets in by_funder.items()
        if len(wallets) >= min_cluster_size
    }


def detect_sniper_window(buyers, window_seconds=30, min_cluster_size=5):
    """Flag windows where an unusual number of buyers bought in quick succession."""
    if not buyers:
        return []

    timestamps = sorted(b["timestamp"] for b in buyers)
    clusters = []
    i = 0
    for j in range(len(timestamps)):
        while timestamps[j] - timestamps[i] > window_seconds:
            i += 1
        window_size = j - i + 1
        if window_size >= min_cluster_size:
            clusters.append({
                "start": timestamps[i],
                "end": timestamps[j],
                "count": window_size,
            })

    # dedupe overlapping windows, keep the largest per region
    deduped = []
    for c in clusters:
        if not deduped or c["start"] > deduped[-1]["end"]:
            deduped.append(c)
        elif c["count"] > deduped[-1]["count"]:
            deduped[-1] = c

    return deduped
