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

## Post hoc, exploratory: the two calibration PRs matched (2026-09-30, at the user's request)

Not Phase 2's result, which is pre-registered for the main runs; two PRs, 11 asks, one ask is 0.09.
Seal acf2e521 (X1 X2 Grc1 Lc), two blind matchers audited clean (4 and 6 calls), agreeing on 37 of
44 cells.

| reviewer | asks reached (matcher 1 / 2) | findings |
|---|---|---|
| Claude X1 / X2 | 6 / 4, 5 / 3 | 10, 12 |
| gpt_5.2 solo carried (Grc1) | 2 / 2 | 3 |
| gpt_5.2 lead carried (Lc) | 3 / 2 | 21 |
| Lc, gate-published findings only | 3 / 2 | 11 |

- The lead reaches what solo reaches, within one ask, with seven times the findings: it gains `simpa
  using` on 32875 (v0092) and, on one matcher, the `gcongr` step (v0068), and loses the `ha` naming
  (v0065) that solo reached incidentally.
- Every ask the lead reached, the gate published: under reasoning, the gate did not suppress hits here.
- About half the lead's findings are the same claim from two to five arms (`posLog_pow` four times,
  `grind` five times).
- Both lead and solo asked to remove `grind` where the maintainer asked for `@[grind]` tags
  (v0090, v0091): decomposition carries the same convention gap Phase 1 labelled.

## Claude through the judge (2026-09-30), on the held-out 12 gold

`cli probe import` (9603b6f7) wrote each dev Claude probe session as a solo-shaped run
(`probe_dev_claude_X{1,2}`), through the solo runner's own anchoring and finalize; then `cli judge`
with `configs/pr_review_v5_medium_heldout_judge.yaml`, the gold and judge behind the historical wall
(23 obligations, 12 reachable). Anchoring lost 4.7% / 2.9% of Claude findings, against 4.2% for gpt.

| reviewer (dev held-out 12, judge v9) | issue recall | reachable | hits (reachable + other) |
|---|---|---|---|
| **Claude X1** (probe session) | **0.478** | **0.583** | 7 + 4 |
| **Claude X2** (probe session) | **0.478** | **0.583** | 7 + 4 |
| historical lead, reasoning off (v2 reps) | 0.22-0.30 | 0.33-0.42 | |
| historical solo, reasoning off (v2 reps) | 0.04-0.17 | 0.00-0.25 | |
| gpt_5.2 solo, reasoning carried (Grc1) | 0.130 | 0.250 | 3 + 0 |
| gpt_5.2 solo, reasoning off (G_rep1) | 0.174 | 0.083 | 1 + 3 |

On the judge, Claude is about 1.6x the best historical pipeline run and about 3.7x carried gpt_5.2
solo. Caveats: dev is inside Claude's training window; the imported findings carry concern family
`other` (the judge's prompt shows the family; gpt's carry its own) and no evidence chain; n is 23.
**Next, not done:** re-judge Grc1 with families set to `other` (a control for the label); the
pre-registered main Phase 2 runs (awaiting the user's go-ahead on cost); route B (judge gold for
post-cutoff, the only set clean for Claude).

## gpt-5.4 and gpt-5.5 on dev, for the judge (pre-registered 2026-09-30, before the runs)

`probe_dev_gpt5{4,5}_Grc_rep1`: `configs/pr_review_v5_dev_medium_gpt5{4,5}_Grc.yaml`, solo, brief G,
high effort, Responses, reasoning carried, the models' carried caps (160 turns; $12 / 14.4M, $20 /
24M), the 15 dev PRs. No carried run of either model had touched dev, so neither could be judged.
Expected about $10 and $18 billed.

Read, on the held-out 12 gold with `configs/pr_review_v5_medium_heldout_judge.yaml`: issue recall
and reachable recall beside Claude X1 / X2 (0.478 / 0.583), gpt_5.2 carried (0.130 / 0.250) and the
historical reasoning-off lead (0.22-0.30 / 0.33-0.42). One run each, 23 obligations: provisional,
and read as a level against those references, not as a ranking between the two models. The runs
also join the dev probe seal later, so both measures can be read on the same reviewers.

### Result (2026-09-30): gpt-5.4 and gpt-5.5 carried on the judge

Both runs complete, 30 of 30 sessions, $9.02 and $18.42 billed; judged with the held-out 12 config.

| reviewer (dev held-out 12, judge v9, 23 obligations) | issue recall | reachable (12) | obligations issue-matched |
|---|---|---|---|
| Claude X1 / X2 (probe sessions, imported) | 0.478 / 0.478 | 0.583 / 0.583 | 11 / 11 (each hits one the other misses) |
| gpt-5.5, reasoning carried | 0.130 | 0.167 | 3 |
| gpt_5.2, reasoning carried | 0.130 | 0.250 | 3 |
| gpt-5.4, reasoning carried | 0.087 | 0.000 | 2 |
| gpt_5.2, reasoning off | 0.174 | 0.083 | 4 |
| historical lead, reasoning off (v2 reps) | 0.22-0.30 | 0.33-0.42 | |

All four gpt solo conditions sit between 0.09 and 0.17, inside the historical solo spread (0.04-0.17)
and below the historical reasoning-off lead; Claude is about three times any of them. The gpt runs'
union is 10 obligations, Claude's 12. One run each, so the order among the gpt conditions (one or two
obligations apart) is noise; the gap to Claude is not.
