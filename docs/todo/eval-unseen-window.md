# A 46-PR window no v5 design has touched, to test whatever breaks the wall

**Status** — **superseded (2026-09-24)** by the sealed test set `eval-2025-06-2026-03-v1` and the validation set `val-2025-06-2026-03-v1` (docs/todo/eval-set-selection.md). **Not the evaluation set (user, 2026-09-24).** The 46 are biased too, just differently from
the dev set: they are the residual of the gold-driven selection that made the medium tier (style-heavy,
25 of 58 obligations; mostly single-file PRs, median 3.5k-char diff), and v2-exposed. There is budget for
**one** big run, on roughly 50 PRs, so the set it runs on must not share the dev set's bias and must not
swap it for another; choosing it needs careful consideration, and building it once chosen can be
parallelized in a few hours. This entry stays as the verified description of one candidate pool and
of the defects any pool inherits (the tool-schema gold leak, the builder blockers, the missing
hittability audit). Previously: open, verified 2026-09-23 (one assessor, three adversarial verifiers)
**Cost** — build is free (about 6-8 hours of work plus 5-11 hours of reviewed-workspace machine time,
after the live paid runs finish); reading it is a winner plus its own baseline, three reps each, about
$10-15 per rep in lead shape and about $70-90 per rep in fanout-verdicts shape
**Motivating example** — every design since August was tuned on the held-out 12, so a result above
7 of 23 there is in-sample by construction. The v4 benchmark's large tier minus its small and medium
gold PRs is exactly 46 PRs (`inputs/pr_review_v4/benchmarks/tiers-v1.json`,
`unseen_slice_definition`). All 46 have gold in `dev-judgment-stable-0.9.0` (62 judgments; 53 included
views over 42 PRs give **58 eligible obligations**, against 23 on the held-out 12, so one flip is 1.7pp
rather than 4.3pp). All 37 base commits are built, all 46 have round-1 episodes in `dev-raw-0.3.0`, and
none of the 46 appears in any v5 run, config, rule or code literal.

## What it is and is not

**v5-unseen, v2-exposed, not a temporal holdout.** 19 v2 runs scored all 46 in June-July 2026, about
half of today's `focused_prompts.py` lines are v2 checker text measured on them, and the medium tier was
drawn from the same 57 on gold concern statistics, so the 46 are a selection residual. Report any
treatment as a **paired delta against a matched control on the same code**, per PR and pooled, never as
an absolute level. The tiers doc gives large-tier results no publication-grade weight; the temporal
window from the PR store (`operational-floor.md` §3) remains the only generalisation claim.

**Harder for v5 as it stands, and differently shaped.** Of the 58: style 25, naming 11, docs 10,
duplication 5, scope 3, correctness 3, proof-golf 1; 50 advisory, 8 blocking. The held-out 12 are
duplication-heavy. Weighting the held-out reps' per-family hit rates by this mix predicts roughly 13-18%
recall for today's system, against 26% observed on the held-out 12. Per-family reporting is required.

## Found while verifying, and to fix before any read

- **A gold identifier in every arm's tool schema.** `lean_verify_edit`'s `declaration_name` description
  says "e.g. Subgroup.closure_pow_le" (`src/ape/tasks/lean_tasks/formal_math/review/base.py:472`), the
  gold target of PR 33401. The contamination gate misses it twice: it sweeps arm system prompts, the
  contract and the lead prompt but no tool description, and `contracts.prompt_leaks` matches the bare
  `closure_pow_le` but returns nothing for the namespaced form. Extend the gate (tool descriptions;
  a namespace-suffix match) with a test that fails on 33401, and change the example **at a run
  boundary** so both conditions of any comparison see the same schema.
- **Two builder blockers.** `release/modification_inventory.build_inventory` refuses three
  whitespace-only modified targets (window PR 33081; control candidates 33171, 33174) -- fix the
  builder with a version bump, do not drop 33081. And the fanout / `generalist_floor: false` shape is
  refused at plan time (`CoverageGapAtPlanTime`) because two window units (33207 section targets, 33092
  a command) have no eligible specialist; neither carries gold, but the winning config needs a decision.
- **The 58 obligations have no hittability audit**; the judge treats absent as hittable. Several are
  exact-script asks of the kind the hittability criterion excludes. About an hour, gold-only, done blind
  to agent output and outside design sessions.
- **Disclose one aggregate prior.** The unified contract's "Two strengths of ask" section (`+target_verdicts`) motivates its advisory
  section with "91 of 113 advisory", and 62 of those 113 judgments are the 46. The sentence holds on the
  held-out 12 alone (19 of 24 judgments advisory), so the text needs no change; the motivation is
  disclosed beside any window number.

## The three decisions, before building

1. **Override the tiers doc's gate for building only.** `docs/research/pr-review-v4-benchmark-tiers.md`
   says of large "Do NOT start this until the medium tier has justified it"; its reason was human
   decomposition review, which the held-out 12 never had either. Build now; read only after a treatment
   beats its baseline on the held-out 12.
2. **The 46 are the window, not census input.** The deferred ask-census in
   `docs/plans/2026-09-23-one-run-to-move-the-wall.md` ("After the wall moves", item 3) covers the 65
   non-held-out gold PRs, which include all 46 (style 25 of 34, naming 13 of 16, docs 10 of 14 there).
   Reserving them leaves a 19-PR census, or the census waits for the PR-store window.
3. **Tell `work-enumeration`** that if its question list is ever scored on the 46, Phase 1's date gate
   must sit at or before 2025-12-18T16:55:47Z (PR 33048), not the 2025-12-20 its plan quotes.

## Start here

- **read:** `inputs/pr_review_v4/benchmarks/tiers-v1.json`; `src/mathlib_review/legacy_pipeline/pilot.py`
  (`CASE_REGISTRIES` at :75 knows `pilot` and `medium`; `CONTROL_SEMANTICS`);
  `src/mathlib_review/release/rerender_release.py` (0.1.0 -> 0.3.0 was a rerender to `candidate-prompt/12`);
  `src/mathlib_review/release/modification_inventory.py:284` (the refusal);
  `tests/datasets/test_prompt_contamination.py` and `src/mathlib_review/release/contracts.py::prompt_leaks`.
- **run (free):** rebuilding medium with current code reproduces 0.3.0's 225 work-unit ids and every
  prompt hash, which is the check that the tooling still works; then a `large_unseen` case registry
  derived from the tiers file (46 plus seeded controls from the 48 funnel PRs meeting the control
  semantics on built bases -- not 33165 or 33210), the release through the tooling and
  `ape/bin/python -m src.mathlib_review.release.verify_frozen build-lock`, then
  `ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --config <new config>` and
  `ape/bin/python -m src.mathlib_review.review.cli plan --config <new config> --run-name <name>`, both
  without `--execute`. The prebuild `--execute` waits until no paid run is live: it copies ~2.9 GB per
  episode over the same NFS.
- **bounded by:** selection stays parked (score pre-gate); controls are chosen from funnel and v2-record
  facts, never agent output; the frozen root is written only through the tooling.

## Risk

A null on the 46 does not cleanly refute a held-out gain -- the family mix and the gold audit differ --
and the tiers doc allows at most three uses, so every read spends a third of the window.
