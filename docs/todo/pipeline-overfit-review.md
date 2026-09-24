# What in the v5 pipeline is fitted to the dev set -- reviewed against the validation set

**Status**: open, 2026-09-24, **for a fresh session** in the worktree `pipeline-overfit-review`.
The user asked for it at the end of the eval-set-selection session:

> *"using the new validation set, could you review the pipeline we have designed so far and identify
> all the weaknesses in it that were overfit on the dev set we were studying? For example, I'm not
> sure the division of the specialist arms appropriately maps onto the subtasks of reviewing.
> Additionally, I'm not sure the descriptions of each of the arms is as general and clear as possible."*

**Cost**: the audit is free. The validation set's reviewer comments are readable (it is the
development set now), and nothing needs a run. A change that comes out of it is then measured on
`val-2025-06-2026-03-v1_small12` (about $6-24 a rep) before the full validation set.

## Motivating examples

Every design since August was tuned on 16 dev PRs, the held-out 12 plus smoke4. Those were chosen on
gold concern statistics from fast-closing Dec 2025 PRs (`docs/todo/eval-set-selection.md`). The
pipeline carries that fit in at least four visible places:

- **The arms' remits were cut around specific dev PRs.**
  - `src/mathlib_review/agenda/registry.py` re-scopes arms around 33305 (wrapping a module-doc
    line) and 33362 ("move the declarations inside `namespace Complex`"), 33321's documentation
    obligations, and 33098's `grind` (lines 94-95, 121, 147-148, 198-202).
  - `proof_idiom`'s remit names `grw`/`gcongr`/`omega`/`grind` (line 142).
  - Measured on dev: 37 of 58 gold-site specialist silences were an arm correctly quiet about
    another arm's concern. The generalist holds 64 of 71 held-out hits. On the unified contract,
    4 of 7 misses were design-scale asks that no arm's question reaches
    (`docs/research/unified-contract-fanout4-2026-09.md`).
- **The arm prompts quote dev gold.**
  - The naming prompt's model-visible worked example is PR 33337's own counts: "of 121
    declarations whose conclusion is about `toLinearMap`, 21 use `toLinearMap_` and 7 use `coe_`"
    (`src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py:381-382`).
  - About half of `focused_prompts.py` is v2 checker text measured on the 46-PR window
    (`docs/todo/eval-unseen-window.md`).
  - The prompt-contamination gate does not sweep tool descriptions: `lean_verify_edit`'s example is
    33401's gold target (`review/base.py:481`).
- **The thresholds and rosters were set on dev.**
  - The lean five-arm roster says of itself "do not carry this roster to another PR set"
    (`configs/pr_review_v5_contract_fanout4_lean.yaml`).
  - `naming_norm` counts leaf prefixes only, and its `established` bar is 0.80, set against 33337's
    21 of 121 (`docs/todo/specialist-arm-contents.md`).
- **The grain was tuned on one PR.** The /13-/14 packer exists because 33149 held 108 of 203 work
  units. The validation set has two PRs at 66 and 59 units under that packer.

## What would close it

A written audit, at `docs/research/pipeline-overfit-2026-09.md`, with three measured parts, each
counted on the validation set's 60 PRs and not on dev:

1. **Coverage of the review work by the arm division.**
   - Take every roster-reviewer comment on the validation PRs' first round (the store's corpus
     projection, reviewer_view).
   - Map each to the arm whose remit owns it, or to none. Two readers, disagreements reported.
   - Report the share no arm owns, the arms that own nothing, and the asks split across arms.
   - Set that against the question taxonomy in `docs/plans/2026-09-23-work-enumeration.md`.
2. **Dev-specific text in everything model-visible.** Cover arm prompts, remits, contract text and
   tool descriptions. Give each item's provenance (which dev PR or run motivated it), and a general
   rewrite or a reason to keep it.
3. **Dev-tuned knobs:** caps, thresholds, rosters, packer, rules. For each, what it was tuned on
   and what the validation set's gold-free features say about it.

Then a proposal for a re-division or rewrite, with each change justified by validation counts. It is
measured on the validation small12 before the full set.

## Start here

- **read:**
  - `docs/plans/2026-09-23-work-enumeration.md`. The same premise ("specialists map poorly onto
    maintainer work"). Its Phase 0 is done and its corpus-derived question list is not; this audit
    can *be* its Phase 1 on the validation set, rather than a parallel taxonomy.
  - `docs/todo/specialist-arm-contents.md`: the arm-by-arm audit it superseded.
  - `src/mathlib_review/agenda/registry.py` (`ARM_DEFINITIONS`).
  - `src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py`.
  - `docs/research/specialist-silences-2026-09.md` and `docs/research/unified-contract-fanout4-2026-09.md`.
  - The validation set: `inputs/pull_requests/evaluation/val-2025-06-2026-03-v1/` and the release
    `inputs/pr_review_v4/releases/val-2025-06-2026-03-v1`.
- **run (free):** the validation PRs' reviewer comments come from
  `data/pull_requests/projections/corpus/reviewer_view.jsonl` (rows whose PR is in the validation
  release's `pr_numbers`), or from `PullRequestStore().read(n, "review_comments")`.
  `ape/bin/python -c "from src.mathlib_review.agenda.arms import _grant_for; print(_grant_for('naming'))"`
  shows an arm's tools.
- **bounded by:**
  - **Never read the test set's reviews** (`eval-2025-06-2026-03-v1`, its 60 PRs). They are in
    `scored_pr_numbers()`, so corpus consumers already exclude them; a hand query must too.
  - Selection stays parked (`.claude/rules/mathlib-review.md`).
  - `docs/dead-ends.md`, "Specialists as the coverage floor" (more slots buy abstentions) and the
    unified-contract entry.
  - The live `naming-from-statement` thread (11 commits ahead of develop) redesigns the naming
    arm's evidence. Coordinate before rewriting the naming prompt.

## Risk

The validation set becomes in-sample for whatever this audit changes. That is its job, and the test
set stays clean. Sixty PRs carry about 150 first-round reviewer comments, which is enough for a
coverage matrix and thin for per-family rates, so report counts rather than rates.
