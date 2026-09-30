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

## Calibration result (2026-09-30, $5.94, `probe_val_small12_lead_carried_calib`)

Both PRs completed, 33 arm jobs, all `success`, none capped; every lead and arm turn a Responses call
with reasoning, every conversation carrying its encrypted items.

| PR | work units | lead + arms billed | lead turns | arm jobs (waves) | arm job billed p50 / max | arm tokens p50 / max |
|---|---|---|---|---|---|---|
| 30641 | 1 | $2.03 | 7 | 11 (7 / 3 / 1) | $0.173 / $0.370 | 102K / 250K |
| 32875 | 7 | $3.91 | 5 | 22 (17 / 5) | $0.143 / $0.690 | 108K / 674K |

Against the reasoning-off lead (post-cutoff, 69 arm jobs): arm jobs cost about 4x at the median
($0.034 → $0.15) and 8x at the max ($0.085 → $0.69), and 3x the tokens at the median (35K → 102K).
The base's arm caps ($0.30 / 360K) would have bound on the largest jobs. Findings: 21, of which the
gate published 11 -- reported here only as a shape, from two PRs.

**Main-run caps from this** (about 2x the calibration's maxima, in step at 1.2M tokens a dollar): arm
job $1.50 / 1.8M, lead $3.00 / 3.6M, per PR $8.00 / 9.6M. Expected cost a validation rep (11 PRs, 36
work units): about $25-35.
