"""
Runs the scoring/correlation engine against synthetic data -- no Helius
key, no network calls. This proves the logic in onchain.py's pure
functions (detect_bundles, detect_sniper_window) and correlate.py works
correctly, so you're not debugging API integration and scoring logic at
the same time.

Two scenarios:
  1. "Coordinated" launch: 6 wallets share a funder and buy within a tight
     window, matched by a same-day-created social cluster posting in the
     same window. Should score high.
  2. "Clean" launch: buyers are spread out with distinct funding sources,
     no social cluster. Should score low.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from onchain import detect_bundles, detect_sniper_window
from social import analyze_social_csv
from correlate import build_report

T0 = 1750000000  # matches data/sample/social_example.csv


def coordinated_scenario():
    buyers = [
        {"wallet": "buyerA", "timestamp": T0 + 2, "funding_source": "FUNDER_X"},
        {"wallet": "buyerB", "timestamp": T0 + 4, "funding_source": "FUNDER_X"},
        {"wallet": "buyerC", "timestamp": T0 + 6, "funding_source": "FUNDER_X"},
        {"wallet": "buyerD", "timestamp": T0 + 9, "funding_source": "FUNDER_X"},
        {"wallet": "buyerE", "timestamp": T0 + 11, "funding_source": "FUNDER_X"},
        {"wallet": "buyerF", "timestamp": T0 + 15, "funding_source": "FUNDER_X"},
        {"wallet": "organic1", "timestamp": T0 + 400, "funding_source": "exchange_wallet_1"},
    ]
    bundles = detect_bundles(buyers)
    sniper_windows = detect_sniper_window(buyers, window_seconds=30, min_cluster_size=5)

    social_csv = os.path.join(os.path.dirname(__file__), "..", "data", "sample", "social_example.csv")
    social_result = analyze_social_csv(social_csv)

    return build_report(buyers, bundles, sniper_windows, social_result)


def clean_scenario():
    buyers = [
        {"wallet": "buyerA", "timestamp": T0 + 30, "funding_source": "exchange_wallet_1"},
        {"wallet": "buyerB", "timestamp": T0 + 900, "funding_source": "exchange_wallet_2"},
        {"wallet": "buyerC", "timestamp": T0 + 2200, "funding_source": "exchange_wallet_3"},
        {"wallet": "buyerD", "timestamp": T0 + 5000, "funding_source": "exchange_wallet_4"},
    ]
    bundles = detect_bundles(buyers)
    sniper_windows = detect_sniper_window(buyers, window_seconds=30, min_cluster_size=5)
    social_result = {"same_day_clusters": {}, "burst_windows": [], "total_posts_analyzed": 4}
    return build_report(buyers, bundles, sniper_windows, social_result)


def print_report(label, report):
    print(f"\n=== {label} ===")
    print(f"Composite score: {report['composite_score']}/100")
    for k, v in report["breakdown"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    print_report("Coordinated launch (should score HIGH)", coordinated_scenario())
    print_report("Clean launch (should score LOW)", clean_scenario())
