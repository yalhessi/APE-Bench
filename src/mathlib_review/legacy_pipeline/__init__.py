"""Spent one-shot builders and inspectors from the v4 pipeline's construction.

Each module here produced a frozen artifact that is still load-bearing — the release
chain from the raw event ledger through gold construction to `dev-pilot-0.9.0`, plus the
review digests used during curation. The artifacts remain at their recorded paths under
`inputs/pr_review_v4/`; only the code that produced them moved.

**Do not run these.** They write with `io.write_once`, so re-running against changed
inputs raises rather than corrupting an artifact, but they are unmaintained and their
defaults point at releases that are already sealed.

Deliberately NOT archived here: `phase3_canonical_smoke`, `phase4_naming_smoke`, and
`phase5_wrapper_smoke`. The Step 5 equivalence gate found that `opportunity_executor`
reproduces their discovery layer but not their evidence prose, so they remain the
authoritative producers of the frozen 0.9.1-0.9.3 smoke releases that Phase 9 consumes.
See `results/pr_review_v4/audits/phase10-executor-equivalence-verdict.md`.
"""
