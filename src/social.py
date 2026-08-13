"""
Social coordination signal extraction.

Adapted from the existing X/Twitter engagement-audit tool: the two
strongest inauthentic-behavior signals there were (a) accounts created on
the same day clustering together, and (b) tight engagement-burst windows.
This module applies the same two checks to a CSV of posts about a token.

Expected CSV columns (header row required):
  account_handle, account_created_date, post_timestamp, likes, retweets, replies

- account_created_date: YYYY-MM-DD
- post_timestamp: unix seconds (convert your export to this if needed)

NOTE: commas inside quoted fields corrupted parsing last time -- this uses
Python's csv module (not manual splitting) specifically to avoid repeating
that bug.
"""

import csv
from collections import defaultdict


def load_social_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["post_timestamp"] = int(row["post_timestamp"])
            except (KeyError, ValueError):
                continue
            rows.append(row)
    return rows


def detect_same_day_clusters(rows, min_cluster_size=3):
    """Group posting accounts by creation date; flag same-day clusters."""
    by_date = defaultdict(set)
    for r in rows:
        date = r.get("account_created_date")
        handle = r.get("account_handle")
        if date and handle:
            by_date[date].add(handle)

    return {
        date: sorted(handles)
        for date, handles in by_date.items()
        if len(handles) >= min_cluster_size
    }


def detect_burst_windows(rows, window_seconds=600, min_cluster_size=5):
    """Flag windows where an unusual number of distinct accounts posted in quick succession."""
    if not rows:
        return []

    events = sorted(
        ({"handle": r["account_handle"], "ts": r["post_timestamp"]} for r in rows),
        key=lambda e: e["ts"],
    )

    clusters = []
    i = 0
    for j in range(len(events)):
        while events[j]["ts"] - events[i]["ts"] > window_seconds:
            i += 1
        window_accounts = {events[k]["handle"] for k in range(i, j + 1)}
        if len(window_accounts) >= min_cluster_size:
            clusters.append({
                "start": events[i]["ts"],
                "end": events[j]["ts"],
                "accounts": sorted(window_accounts),
            })

    deduped = []
    for c in clusters:
        if not deduped or c["start"] > deduped[-1]["end"]:
            deduped.append(c)
        elif len(c["accounts"]) > len(deduped[-1]["accounts"]):
            deduped[-1] = c

    return deduped


def analyze_social_csv(path, same_day_min=3, burst_window_seconds=600, burst_min=5):
    rows = load_social_csv(path)
    return {
        "same_day_clusters": detect_same_day_clusters(rows, same_day_min),
        "burst_windows": detect_burst_windows(rows, burst_window_seconds, burst_min),
        "total_posts_analyzed": len(rows),
    }
