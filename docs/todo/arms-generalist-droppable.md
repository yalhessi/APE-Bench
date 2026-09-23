# Is the generalist droppable once the specialists speak?

**Status** — open, 2026-09-23; **deferred** behind `docs/plans/2026-09-23-one-run-to-move-the-wall.md`.
**Partly measured elsewhere (corrected the same day):** the `work-enumeration` branch's contract
ceiling runs with `generalist_floor: false` on four stage1 PRs (`pr5_V2_verdicts_fanout4_rep*` and
their controls), so its reps are the first specialist-only numbers under a new contract. What they
cannot answer is the twelve-PR, generalist-in comparison this entry closes on
**Cost** — one 12-PR rep with the floor off (~$5–10 billed, the floor is most of a rep's spend), three to conclude
**Owner question** — the user's hypothesis, 2026-09-23: the specialists should be strict improvements
over the generalist, so the generalist should be droppable when everything else works. Stated as a
hypothesis to test, not a design to assume.

## Motivating example

On `pr5_A_lead_heldout12_v2_rep{1,2,3}` the generalist produced 772 findings / 64 gold matches and
hit 6 of the 7 obligations the three reps reach; the ten specialists together 135 / 7 / 3. Per rep,
the generalist is the **sole finder of 4, 3 and 5** of the obligations hit (7, 5, 6) — without it
today's system recovers 3, 2, 1. Every one of those is inside some specialist's remit: `correctness`
filed nothing on both of 33149's axiom obligations, which the generalist hit in all three reps, and
`docs` matched nothing on 33321's docstring typo. Against that, the specialists are silent rather than
worse — `naming` matches 3 of 7 findings (43%), `proof_golf` 3 of 14, the generalist 8.3% — and the
retracted "the generalist arm dominates on quality" (`docs/dead-ends.md`) was a volume artifact.

## What would close it

A specialist-only condition (`--set dataset.generalist_floor=false`; every unit on release 0.3.0 has at
least one specialist proposal, `agenda_report.units_without_specialist: []`, and preflight's
`assert_coverage_is_reachable` checks it) under the same contract as the with-generalist condition.
"Drop it" is supported only if, over three reps, the specialist-only condition recovers at least the
with-generalist mean with control emission no worse. Otherwise each generalist-only obligation names
which arm's question is still missing.

## Start here

- **read:** `src/mathlib_review/agenda/agenda.py` (the generalist floor loop in `build_agenda`),
  `src/mathlib_review/review/runner.py` (`generalist_floor`, `assert_coverage_is_reachable`),
  `docs/research/ab-heldout12-obligation-spine.md` §5 (per-arm matches).
- **run:** after the one-run plan's commits, `report buckets --audit` on any judged run prints
  `hits_by_arm` including the sole-finder count this entry is about:
  `ape/bin/python -m src.mathlib_review.review.cli report buckets --run pr5_A_lead_heldout12_v2_rep1 --audit`.
- **bounded by:** `results/pr_review_v5/runs/pr_review_v5_specialist4_rep1` is the one earlier
  floor-off run (smoke4, `completion_status: failed`) and is not a measurement of this; the one-run plan
  comes first because a specialist-only run under today's contract measures the withholding, not the arms.

## Risk

The generalist is also the only arm whose prompt is frozen in the release, so it is the stable control
every run is compared against. Dropping it removes the comparison as well as the coverage.
