import argparse
import json
import os

from dotenv import load_dotenv

from onchain import get_early_buyers, enrich_with_funding_sources, detect_bundles, detect_sniper_window
from social import analyze_social_csv
from correlate import build_report

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Coordination detector for a Solana token launch")
    parser.add_argument("--token", required=True, help="Token mint address")
    parser.add_argument("--pool", required=True, help="Pool/pair address")
    parser.add_argument("--social-csv", required=True, help="Path to CSV of social posts about the token")
    parser.add_argument("--launch-timestamp", type=int, default=None, help="Unix seconds of pool creation, if known")
    parser.add_argument("--max-buyers", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--out", default="report.json")
    args = parser.parse_args()

    api_key = os.getenv("HELIUS_API_KEY")
    if not api_key:
        raise SystemExit("Set HELIUS_API_KEY in your .env file first (see .env.example).")

    print(f"Pulling early buyers for pool {args.pool} ...")
    buyers = get_early_buyers(
        args.pool, api_key,
        launch_timestamp=args.launch_timestamp,
        max_buyers=args.max_buyers,
    )
    max_pages=args.max_pages,
    print(f"Found {len(buyers)} early buyers. Tracing funding sources (this is the slow part)...")
    buyers = enrich_with_funding_sources(buyers, api_key)

    bundles = detect_bundles(buyers)
    sniper_windows = detect_sniper_window(buyers)

    print(f"Analyzing social CSV: {args.social_csv}")
    social_result = analyze_social_csv(args.social_csv)

    report = build_report(buyers, bundles, sniper_windows, social_result)

    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)

    print("\n--- SUMMARY ---")
    print(f"Composite coordination score: {report['composite_score']}/100")
    for k, v in report["breakdown"].items():
        print(f"  {k}: {v}")
    print(f"\nFull report written to {args.out}")


if __name__ == "__main__":
    main()
