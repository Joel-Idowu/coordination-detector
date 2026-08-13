# Build Plan: Coordination Detector Prototype

## Goal
Validate whether cross-referencing social shill-cluster coordination with
on-chain wallet buy timing can flag known Solana rug pulls, using only
free tools. This is a validation exercise, not a product build — the exit
criteria is a real conversation with a launchpad or platform, not a
polished app.

## Non-goals (explicitly out of scope until validation succeeds)
- No dashboard/UI — CLI + JSON report is enough
- No multi-chain support — Solana only for now
- No scoring-weight optimization — keep the formula simple and readable
  so we can see *why* something scored the way it did
- No outreach to platforms until Phase 5 produces real evidence

## Phase 0 — Environment (in progress)
- [ ] VS Code installed, project open, venv created, `requirements.txt` installed
- [ ] `python src/demo.py` runs and matches expected output (96.4 / 0.0)

## Phase 1 — Scoring engine validated on synthetic data (done)
- [x] `correlate.py`, `social.py`, and the pure functions in `onchain.py`
      proven correct against synthetic data in `demo.py`

## Phase 2 — Real on-chain data integration
- [ ] Get free Helius API key, add to `.env`
- [ ] Pick ONE real, low-stakes token (not a rug case yet) to test plumbing
- [ ] Run `main.py` against it, inspect raw `report.json`
- [ ] Fix any field-name mismatches in `onchain.py` against Helius's
      actual current response shape (documented in code comments as the
      most likely place for drift)
## Phase 3/4 — Merged into Phase 5
Decided not to collect a throwaway social CSV for BONK just to test the
parser, then do it again for real rug cases. Instead: the first real
rug case's social data collection (below) doubles as the parser's first
real-world test. If it breaks on a comma or emoji, fix it there, on data
that actually matters.

## Phase 5 — Validate against known rugs (the actual test)
- [ ] Pick 2–3 known rug-pull tokens NOW, before running anything, so
      there's no cherry-picking after the fact — write them here:
      1. _______________
      2. _______________
      3. _______________
- [ ] For each: pull on-chain data, collect social data from the launch
      window, run the pipeline
- [ ] Check whether it would have flagged the token BEFORE the rug,
      using only data available at that time — not hindsight
- [ ] Write up what fired and what didn't for each case, honestly,
      including any that it missed

## Phase 6 — Decide
- [ ] If it caught most of the known cases cleanly: package the writeup
      as the artifact for a first platform conversation
- [ ] If it didn't: figure out why before doing anything else — no
      point pitching a detector that doesn't detect

## Open questions to keep visible, not bury
- Do platforms actually treat social-coordination signals as
  must-have vs. nice-to-have? Unvalidated — Phase 6's conversation is
  what answers this, not more building.
- Pricing/deal shape is deliberately undecided until there's a working
  proof point to anchor it to.
