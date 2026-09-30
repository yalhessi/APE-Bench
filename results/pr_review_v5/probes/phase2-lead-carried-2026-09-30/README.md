# Phase 2: the pipeline as built, under reasoning carried (2026-09-30)

Phase 2 of `docs/plans/2026-09-30-post-carryover-replan.md`, reopened at the user's request after
Phase 1: every Phase 0-3.1 number is a *solo* reviewer (or Claude through the probe packets), and the
lead + arms + gate path has been measured once in this thread, at reasoning off
(`probe_postcutoff_lead_rep{1,2}`, reach 0.12 = solo). No pipeline run in the record has reasoned.

## What can be measured where

- **`cli judge` needs judge gold** (`gold/judgments.jsonl`, intervention views). Only the dev lineage
  has it (`dev-medium-0.3.0` and siblings). Validation (`val-2025-06-2026-03-v1`) and post-cutoff have
  episode boundaries only, so the judge cannot score a run on them.
- **The probe matchers** score any set with extracted asks: post-cutoff, validation, dev.

## Step 1: calibration (this section, before any main run)

`probe_val_small12_lead_carried_calib`: `configs/pr_review_v5_val_small12_lead_carried.yaml` on two
validation PRs, 30641 (1 work unit, 5 asks) and 32875 (7 units, 6 asks). The caps are set loose so
they cannot bind ($2.00 / 2.4M an arm job, $6.00 / 7.2M the lead, $20 / 24M a PR, 80 turns), because
every cap in the base was calibrated at reasoning off (arm jobs p50 $0.034 / 35K tokens). Read:
per-arm-job and per-PR billed and tokens, turns, any paused job, and the lead's delegation count.
The main runs' caps are set from these, and the main design and its cost go to the user before any
main run starts. Nothing here is scored.
