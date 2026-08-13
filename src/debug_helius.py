"""
Debug helper: calls Helius for a given address with NO type filter, and
prints out what transaction types actually come back. Run this when
get_early_buyers finds 0 results, to see whether the issue is the type
filter, the address itself, or something else.
"""

import argparse
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    api_key = os.getenv("HELIUS_API_KEY")
    if not api_key:
        raise SystemExit("HELIUS_API_KEY not found in .env")

    url = f"https://api.helius.xyz/v0/addresses/{args.address}/transactions"
    params = {"api-key": api_key, "limit": args.limit}

    resp = requests.get(url, params=params, timeout=20)
    print(f"HTTP status: {resp.status_code}")

    if resp.status_code != 200:
        print("Raw response text:")
        print(resp.text[:2000])
        return

    data = resp.json()
    print(f"Number of transactions returned: {len(data)}")

    if not data:
        print("\nNo transactions at all for this address with this endpoint.")
        print("This likely means the address isn't the right one to query")
        print("(e.g. it's a display/pair ID rather than the actual on-chain")
        print("account Helius indexes activity under).")
        return

    types_seen = {}
    for tx in data:
        t = tx.get("type", "UNKNOWN")
        types_seen[t] = types_seen.get(t, 0) + 1

    print("\nTransaction types seen in this sample:")
    for t, count in sorted(types_seen.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    print("\nFull first transaction (for field inspection):")
    print(json.dumps(data[0], indent=2)[:3000])


if __name__ == "__main__":
    main()