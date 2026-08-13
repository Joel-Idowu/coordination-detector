# Coordination Detector (prototype)

Detects coordinated token launches on Solana by cross-referencing two signals
that no existing tool correlates together:

1. **On-chain wallet clustering** — do the earliest buyers share a funding
   source (bundled supply)? Did an unusual number of wallets buy within a
   tight time window after launch (sniper cluster)?
2. **Social coordination** — same-day-created accounts and tight
   engagement-burst windows shilling the token (reused logic from the
   X/Twitter engagement-audit tool).
3. **Cross-correlation** — do the on-chain buy burst and the social shill
   burst line up in time? That overlap is the actual novel signal.

This is a **validation prototype**, not a product. The goal is to run it
against a handful of tokens that are *already known* to have rugged, and see
whether the score would have flagged them early — before investing further
in turning this into anything platforms would pay for.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then paste your Helius key into .env
```

Get a free Helius API key at https://helius.dev — no credit card required,
1M credits/month, plenty for testing a handful of tokens.

## Usage

```bash
python src/main.py \
  --token <TOKEN_MINT_ADDRESS> \
  --pool <POOL_ADDRESS> \
  --social-csv data/sample/social_example.csv
```

Outputs a JSON report (`--out report.json`) plus a human-readable summary
printed to the terminal: bundle flags, sniper-window flags, social cluster
flags, and a composite coordination score with the breakdown that produced
it.

## Testing the logic without a live API key

`src/demo.py` runs the scoring/correlation engine end-to-end against
synthetic mock data (no network calls), so you can sanity-check the logic
before spending real API credits:

```bash
python src/demo.py
```

## Validation plan (do this before showing anyone else)

1. Pick 2–3 tokens you already know rugged — decide this *before* running
   the tool, so you're not tempted to cherry-pick afterward.
2. Run the tool against each using its real token/pool address and whatever
   tweet data you can collect from around its launch window.
3. Check: did it flag bundling, sniper clustering, or social-onchain
   overlap *before* the rug happened (i.e., using only data available at
   launch time, not hindsight)?
4. That result — not the code — is what you bring to a platform
   conversation.

## Project structure

```
src/
  onchain.py    — Helius-based early-buyer + funding-source tracing
  social.py     — social coordination detection (adapted from your
                  engagement-audit tool)
  correlate.py  — cross-domain scoring and time-window overlap
  main.py       — CLI entry point (real data, needs Helius key)
  demo.py       — runs the same engine on synthetic data (no key needed)
data/sample/    — example social CSV for testing the format
```
