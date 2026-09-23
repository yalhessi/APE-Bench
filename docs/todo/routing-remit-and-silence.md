# The arms at a gold site are mostly not the ones whose remit covers the ask

**Status** — open, written 2026-09-21 from the step-0 silence read; **no spend to measure further**
**Cost** — free to measure; a change is one rep ($7.26)
**Owner question** — the agenda schedules the right arm at every gold site *and* several wrong ones.
Is the dilution costing anything, and is a correct silence from a wrong arm worth what it costs?

## Motivating result

`report silences --run pr5_A_lead_heldout12_v2_rep1` over the 22 counted gold obligations, with each
arm's remit taken from `expected_concerns` and bridged to gold's own `concern_labels` through
`benches.gold_labels_for`:

| | |
|---|---|
| silent cells at gold sites | **76** |
| the ask is in that arm's remit | **13** |
| the ask is not | **53** |
| the generalist, which has no remit | 10 |
| obligations where no on-concern arm was *proposed* | **0 of 22** |
| obligations where no on-concern arm was *executed* | **10 of 22** (all three reps) |

**Corrected 2026-09-22.** This row read "obligations where *no* on-concern arm was scheduled | 0 of
22", and concluded "Routing is not failing to send the right arm: it sent one to every single
counted obligation." That counted **proposals**: `report silences` builds its cells from every row
of `delegations.jsonl`, `disposition: pruned` included. Executed, the on-concern arm reaches **12 of
22**; the lead prunes it at the other 10, identically in reps 1, 2 and 3, with
`"not selected by the lead"` on 1,087 of 1,089 prune rows. The rest of the entry stands: routing
also sends four or five arms whose remit does not cover the ask, and those correctly say nothing —
`duplication` at a rename, `naming` at "factor out the repeated `Tendsto` argument", four arms at a
docstring.

**And pruning is still not the binding constraint, measured.** `pr5_F_fanout_stage1_rep1` runs every
specialist at every eligible slot with no lead and no pruning, and covers 3 of those 10 obligations.
At all three, every on-concern arm the lead prunes ran to `success` and **submitted nothing — 7 of 7
arm-cells**: 33421 `38e722` (api_reuse, duplication, family_design), 33145 `7fef91` (the same three),
33145 `e8e028` (style). So un-pruning buys their silence, which is what `dead-ends.md`'s fanout entry
found at its ceiling. Caveats: 3 of 10, one rep, one release, and all three are coordinated design
asks — the shape the arms cannot emit at all
(`docs/plans/2026-09-22-coordinated-emission.md`) — so this subset was the one most likely to come out
this way. The other 7 need a run and are not free.

This matters because "41 of 45 gold-site silences reproduce under replay"
(`docs/research/decision-replay-gold-abstentions-2026-09.md`) has been read as a statement about
arms withholding findings. Most of it is a statement about which arms were asked.

**The cost side, stated narrowly.** Among the silent gold-site jobs in that run, the off-concern ones
billed **$1.93** against **$0.39** for the on-concern ones and $0.31 for the generalist
(`delegations.jsonl`, joined on `invocation_id`). That is not a waste figure: an arm scheduled at a
gold site can file something legitimate elsewhere in its unit, and ~90% of this system's output is
off-gold and unadjudicated, so what those jobs produced cannot currently be valued. It is the price
of the current breadth, measured, and nothing more.

## What would close it

Cheapest first; the first two are free and change what the third would even mean.

1. **Count the same split away from gold sites.** The measurement above is conditioned on a gold
   obligation, which is 22 sites out of a run that schedules hundreds of jobs. Whether off-concern
   scheduling is the norm or an artifact of where gold happens to be needs the unconditioned number,
   and `report silences` does not produce it — `buckets` only walks obligations. Free.
2. **Value the off-concern jobs by what they filed elsewhere.** An arm silent at the gold site that
   filed a useful candidate two declarations away is not dilution. This is blocked on the same thing
   everything else is: nothing adjudicates off-gold findings
   (`adjudication-rubric.md`, and `cli adjudicate` is the socket).
3. **Only then, a routing change.** Two shapes, neither designed here: score an (arm, site) pair by
   whether the arm's remit intersects anything the site plausibly raises, or let the lead see the
   remit table it is dispatching against. Both need a rep. **A remit floor — making the on-concern
   arm non-prunable — is the targeted version, and the 2026-09-22 measurement argues against it**:
   where it can be checked, the pruned arm runs and says nothing.

## What this is not

- **Not the fanout question.** `dead-ends.md`, "Specialists as the coverage floor", settled that
  *more* slots do not help: at its ceiling, fanout recovered exactly what `lead` recovered, and
  104 of 136 abstentions were `already_correct`. This is the opposite direction — fewer, better
  matched — and it is not a coverage claim at all, since coverage is already 22 of 22.
- **Not a claim that the off-concern arms are wrong.** Their silence is correct. That is precisely
  why no contract or prompt change reaches them, and why they were separated out before the
  interventions in `specialist-abstention-interventions.md` were costed.

## Risk

The remit test is only as good as gold's `concern_labels`, and those are noisy: PR 33145's
"generalize the supremum result into `Dense.ciSup'`" is labelled `duplication`. The hand labelling
that step 0 ran over the same 76 cells is the check on it, and where the two disagree the hand read
is the one to trust. One source rep, one release, 12 PRs.

## Evidence

- `report silences --run pr5_A_lead_heldout12_v2_rep1`; the store at
  `results/pr_review_v5/adjudications/silence_labels.jsonl`.
- `src/mathlib_review/agenda/registry.py` (`expected_concerns`),
  `src/mathlib_review/analysis/benches.py` (`gold_labels_for`),
  `src/mathlib_review/agenda/routing.py` (`_GRAIN_REQUIREMENTS`, `_ONCE_PER_PR`).
- Related: [specialist-abstention-interventions.md](specialist-abstention-interventions.md),
  [specialist-arm-contents.md](specialist-arm-contents.md) (seven arms match nothing, three causes),
  [adjudication-rubric.md](adjudication-rubric.md) (what blocks step 2).
