# Choosing the one evaluation set the next big run is spent on

**Status** — open, 2026-09-24, **for a fresh session** (a thread of its own: selection design, then a build
that parallelizes in a few hours once the set is settled)
**Cost** — the selection design is free; the build is free apart from gold-stage model calls; the run it
exists for is the one big run the budget allows, on roughly 50 PRs
**Motivating example** — every design since August was tuned on the dev set (the 16 medium PRs: the
held-out 12 plus smoke4), so any result there is in-sample, and the unified contract's 3 / 10 on four of them
cannot be told from judge noise (one obligation is 10 pp). The obvious fresh pool, the 46 large-tier PRs no v5
run touched (`eval-unseen-window.md`), is biased too, only differently: it is the residual of the gold-driven
selection that produced the medium tier -- style-heavy (25 of 58 obligations), mostly single-file (median
3.5k-char diff against the held-out 12's 10.4k over 6.5 files), and scored by 19 v2 runs. The user,
2026-09-24: only one ~50-PR run is affordable, so the set must not share the dev set's bias and must not swap
it for another.

## What the selection has to settle

1. **A sampling frame fixed without looking at gold.** The dev set was chosen from the 57 on gold concern
   statistics; any pool chosen by gold, or by where the system does well, inherits a bias. Draw with a seed
   from a defined frame (for example every included first-round episode in one window), stratified only on
   gold-free features: diff size, file count, Mathlib area, author.
2. **The window.** The PR store holds tier-2 data for January 2026 -- 1,046 PRs, 712 included first-round
   episodes over 318 base commits (measured 2026-09-23, read-only funnel run) -- later than anything the
   designs were tuned on, and clean with respect to `work-enumeration` Phase 1's corpus pool (reviewer
   comments before 2025-12-18 on unscored PRs). A December 2025 window is not clean against that pool; the
   v2 window (2025-09 to 2025-12) is exposed.
3. **Clean versus gold-bearing mix.** In the original 138 reviewed PRs, 72 carried an actionable finding and
   66 were clean (`docs/PROJECT-STATUS.md` §2). The natural rate keeps precision measurable through control-PR
   emission; enriching for gold-bearing PRs buys recall power. Decide which, explicitly, with the trade stated.
4. **Size.** Cap or stratify by work-unit count so no single PR dominates: on the held-out 12, PR 33149 was
   ~70% of findings and 48% of billed cost.
5. **Gold, the long pole.** No gold pipeline reads the PR store today (the dev gold chain is v2 derive ->
   stratum and actionability labels -> v3 interventions -> the legacy scope and migration stages ->
   codex-assisted decomposition; `eval-unseen-window.md` and the 2026-09-23 survey trace it). The dev gold
   itself is LLM-built (`migration_proposal`, no human sitting). Whatever builds the new gold must not reuse
   labels produced by the systems under test (`.claude/rules/mathlib-review.md`, "A label is not gold").
6. **Buildability must not select.** 27 of the 318 January base commits have built workspaces; choosing PRs on
   built bases would bias toward busy commits. Draw first, then build what was drawn (`prebuild --reviewed`,
   ~2.9 GB and 2.4-16.6 min per episode, only while no paid run is live).
7. **The config, chosen with the set.** At the rates measured on 2026-09-23 a 50-PR run bills roughly: lean-
   roster fanout ~$35 (five arms, `configs/pr_review_v5_contract_fanout4_lean.yaml` scaled), lead ~$58, full
   fanout ~$70; judge extra (~$0.006 a pair). The set's size, mix and config trade against each other and
   should be fixed together.
8. **Pre-registration.** Frame, strata, seed, exclusions (AI-authored, abandoned, a reviewed state that does
   not compile -- 33057 round 1 is the example), controls, and the reading rule, frozen with a digest before
   anyone reads the new gold.

## Start here

- **read:** `docs/todo/eval-unseen-window.md` (one candidate pool and the defects every pool inherits: the
  tool-schema gold leak in `review/base.py`'s `lean_verify_edit` example, the inventory builder's refusal on
  whitespace-only targets, the missing hittability audit); `inputs/pr_review_v4/benchmarks/tiers-v1.json` and
  `docs/research/pr-review-v4-benchmark-tiers.md` (how the tiers were cut); `docs/plans/2026-09-11-pull-request-store.md`
  and `docs/todo/operational-floor.md` §3 (the store, its acceptance report and the one explained mismatch --
  the store floor should be closed before it backs a set); `src/datasets/pull_requests/projections/episodes.py`
  (the funnel); `src/mathlib_review/legacy_pipeline/pilot.py` (`CASE_REGISTRIES`, `CONTROL_SEMANTICS`).
- **run (free):** the funnel in memory over a January 2026 frame, to count included episodes by stratum
  before any rule is fixed; `ape/bin/python -m src.mathlib_review.review.cli plan --config <new config>
  --run-name <name>` once a release exists (prices it, spends nothing).
- **bounded by:** selection of *findings* stays parked (this is selection of *PRs to evaluate on*, which is
  measurement); `docs/dead-ends.md` "Specialists as the coverage floor" and the no-pruning ruling (no broad
  coverage runs); three reps is the project's floor for a rate, so a single ~50-PR run is read as a level with
  its denominator stated, not as a rate.

## Risk

Any window the store can serve today is Mathlib-in-early-2026: one community at one moment, with its
conventions in flux (`grind`, `toLinearMap_`). A clean draw removes the selection bias, not that one.
