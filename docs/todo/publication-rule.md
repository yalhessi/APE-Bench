# The admission gate drops most of what the run finds, on the wrong axis

**Status** — **PARKED 2026-09-22 by the user's ruling, the same day it was written.** "Talking
about publishing is talking about selection. We currently don't have a good enough reviewer to
start talking about selection." The measurement below stands and its instrument is kept; the
*change* is not to be designed or costed until the generator is worth selecting from. Do not
reopen this as a ranking, a keep-rule, a threshold or a channel without that ruling being revisited
— those are the same proposal wearing different words, which is how it got written in the first
place. See `docs/dead-ends.md`, "Publication as selection".
**Cost** — the measurement was free and is done; the change is code plus one rep to confirm
**Owner question** — the gate keeps published control-PR emission at zero and costs 71–83% of the
obligations the run already found. Is there a rule that keeps the first and not the second?

## Motivating result

`docs/research/the-admission-gate-2026-09.md`, from `report buckets --audit`'s `gate` block over
`pr5_A_lead_heldout12_v2_rep{1,2,3}`:

| | rep1 | rep2 | rep3 |
|---|---|---|---|
| gold obligations hit by some finding | 7 | 5 | 6 |
| hit by a **published** finding | **2** | **1** | **1** |
| findings → published | 285→25 | 318→28 | 304→27 |
| control findings → published | 3→0 | 4→0 | 5→0 |

21 of rep1's 24 suppressed hit-findings carry one reason, `no collector can support this claim's
concern family`. Pooled by family, the families that hit are not the families that publish:
`correctness` 161 findings / 39 hits / **2 published**, `naming` 66 / 10 / **0**, `scope` 87 / 6 /
**0**, against `proof-golf` 41 / 3 / 25 and `generalization` 15 / **0** / 6. By producing arm the
generalist holds **64 of 71 hits** and is published 2.8% of the time.

**The precision objection is answerable on this data.** All 12 control findings across the three
reps are `documentation` (11) and `style` (1) — the two families that also never hit. Leave-one-PR-out,
admitting a family only if on the other eleven PRs it hit at least once and emitted nothing on a
control: obligations published **2 → 6 of 7**, findings published 80 → 241, control emission **0**.

## Why it is parked, and what it does not license

The finding is a measurement and is kept as one: every recall figure in the record is pre-gate,
and what a maintainer would see is 2/1/1 of the 7/5/6 obligations. That correction is worth
having and `report buckets --audit` keeps printing it.

What it is not is a direction. Deciding which of the system's findings to show is selection, and
this project has an ordering rule that comes before any of it: **fix the generator first**. The
arms are not yet good enough reviewers for the question "which of their output should a
maintainer see" to be the binding one — and the one intervention that raised issue recall
(0.20 → 0.50, `forbid_abstention`) did it by changing what the arms *say*, not by re-ranking what
they had already said.

The entry is kept rather than deleted because the numbers are real and because a later session
that measures the gate again should find the ruling rather than the proposal.

## What would close it, IF the ruling is ever revisited

1. **Re-judge the same artifacts under unanimity** (free, not done). The 7 pre-gate hits are
   majority verdicts, and the gate's loss should be quoted against the stricter denominator too.
2. **Decide what the rule is.** Three shapes, none designed here: keep the collector warrant but
   publish an unwarranted claim in a separate lower-confidence channel; replace the family gate with
   a measured per-family keep rule, refreshed per release; or keep the gate and raise the arms that
   have collectors to cover the families that hit (which is the `specialist-arm-contents.md`
   direction, and is slower).
3. **One rep to confirm**, because a re-scoring says what recorded findings would have done under a
   different rule, not what a run produces when the rule has changed.

## Risk

- **Volume is the unmeasured cost.** 241 published against 80 is three times the reading, and ~90%
  of it is off-gold and unadjudicated, so "dominates" holds on the two axes this project measures
  and on no others. Blocked on [adjudication-rubric.md](adjudication-rubric.md), whose store is
  empty.
- **Small denominators**: 7 obligations found, 2 control PRs, 3 reps, one release, one model.
- The family set is chosen from measured hit rates, which is a selector over artifact-only
  information — close to `dead-ends.md`'s standing refusal. The distinction: that entry refuses
  predicting *which valid change a maintainer raises*; this ranks *families* by their observed hit
  rate, out of sample, and does not score individual findings. Keep it that way or the entry bites.

## Evidence

- `docs/research/the-admission-gate-2026-09.md`; `cli report buckets --run <run> --audit`.
- `src/mathlib_review/review/finalize.py` (`_unwarranted_findings`, `checkable_arms`),
  `src/ape/tasks/lean_tasks/formal_math/review/candidates.py` (`CHECKABLE_CONCERN_FAMILIES`).
- Related: [specialist-arm-contents.md](specialist-arm-contents.md) (`style` publishes nothing —
  recorded there as an arm property, and it is also 38% of total output with zero hits),
  [selection-signal.md](selection-signal.md) (what may and may not be ranked on),
  [adjudication-rubric.md](adjudication-rubric.md) (the blocker on the volume cost).
