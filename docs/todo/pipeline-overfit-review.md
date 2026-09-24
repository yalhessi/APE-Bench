# What in the v5 pipeline is fitted to the dev set -- reviewed against the validation set

**Status**: **audit done, 2026-09-24**. It is [`docs/research/pipeline-overfit-2026-09.md`](../research/pipeline-overfit-2026-09.md),
with its two appendices and the labels in
`results/pr_review_v5/adjudications/arm-coverage-val-2025-06-2026-03-v1/`. **Open:** the proposal
(Track A hygiene, Track B re-division) and its measurement, which is blocked on small12's reviewed
workspaces. See "After the audit" at the foot.
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

## After the audit (2026-09-24)

**What it found, in one line each** (counts, not rates; model readers):
- **Coverage.**
  - 32 to 36 of the validation set's 107 round-1 asks belong to no arm's written remit.
  - Only 40 fit an arm explicitly, 29 of them the proof arms or `style`'s binder bullet.
  - No arm owns:
    - attribute and instance registration (10 asks, 6 PRs);
    - PR-level asks (15 asks, 11 PRs, and no unit exists at PR grain).

    Statement and API design (8 asks) has no explicit owner.
- **The dev set is one reviewer.** One person wrote 30 of the dev set's 52 round-1 comments, on 4
  PRs. Naming is 29% of dev asks and 3% of validation's.
- **Dev text ships.**
  - About a dozen dev-derived strings reach a model: the naming example (33337, and wrong on the
    elaborated corpus), `coe_starProjection_eq_x` and `closure_pow_le` in tool descriptions,
    33145's `(α := αᵒᵈ)`, and `family_design`'s five dev-obligation bullets.
  - The contamination gate cannot see any of them.
  - The lead is told what 4 of its 10 arms are for.
- **Knobs.**
  - The packer charges a hunk the renderer no longer prints: 138 of 425 validation units.
  - Nothing filters whitespace-only changes: 85 units.
  - Flat per-PR lead limits meet agendas of up to 649 proposals.
  - The required-row cap fills in hash order.

**Next, in order:**
1. **Regenerate `reviewer_view.jsonl` on `develop`.** It holds 198 test-set rows (see
   `.claude/rules/pull-requests.md`). The Start-here line above that reads it is safe only because
   it filters to the validation PRs. Nothing else is safe without a re-filter.
2. **Track A** (free, run-boundary hygiene):
   - dev strings out of tool schemas and served docstrings, and the gate extended to see them;
   - the checklist contradiction removed from specialist prompts;
   - all ten arms described to the lead;
   - the packer charge and a whitespace filter, as a new renderer version.
3. **`prebuild --reviewed` for small12**, then `cli plan` for both conditions.
4. **Track B** measurement, with the reading rule fixed in the audit:
   - current ten arms against the proposed nine, fanout, three reps each;
   - findings matched by two blind readers to small12's 31 round-1 asks;
   - **through if** at least 5 more asks are reached on the mean, 3 of them in F2, F3, F6 or F12;
   - the stable set does not shrink;
   - findings rise by at most 1 per rep on the two feedback-free PRs.
5. The size knobs (packer, lead limits, cap order) are readable only on the full 60: small12
   excludes PRs over 8 units.

**Coordinate:** the naming worked example and `naming_norm`'s tiers belong to `naming-from-statement`
and `arm-naming-bar`. That branch's new `naming_statement` description uses `round_eq'`, 33421's
gold subject, as its example. Flag it before that merge.

## Replication on a 1,000-PR validation set (pre-registered 2026-09-24, before any label)

The user, after reading the audit: *"Before we commit to this, let's generate a much larger
validation set and run the same analysis over it."*

**The set.** `val1000-2025-06-2026-03-v1` was sealed in `052a79b`:
- 850 main + 150 AI PRs;
- no author cap;
- a short AI stratum completes with every AI member that passes;
- disjoint from test and from the 60.

It is an analysis set: no frozen release and no reviewed workspaces.

**The instrument.** Rubric v2, the same as the audit's plus a frozen codebook of the twelve
families, with `NEW` for anything outside them. Two blind Claude readers per batch.
- *Calibrated on the audit's 144 comments:* each reader against the auditor's adjudication,
  κ 0.95 and 0.94; reader against reader, κ 0.99; unowned asks 34 of 107.

**The claims under test**, each read on asks both readers agree are asks:

| | claim from the 60-PR audit | replicates if |
|---|---|---|
| R1 | about a third of asks have no owning arm | the unowned share (both readers `primary: none`) lies in [25%, 40%] |
| R2 | registration (F3) and PR-level (F12) asks exist and no arm owns them | each is at least 5% of asks, and at most 10% of each has a primary owner |
| R3 | naming is a small share of review work | F8 is at most 6% of asks |
| R4 | the remits name little of the work explicitly | explicit fits (both readers, same arm) are at most 45% of asks |
| R5 | a PR-level unit is needed | PR-grain asks (both readers) are at least 8% |
| R6 | `api_reuse` owns nothing | it is the primary owner of at most 1% of asks |
| R7 | the families cover the work | `NEW` is at most 10% of asks |

A claim that fails is reported as failed; the proposal changes to follow the larger set.

**Result, 2026-09-24** (`docs/research/pipeline-overfit-2026-09-replication.md`; labels in
`results/pr_review_v5/adjudications/arm-coverage-val1000-2025-06-2026-03-v1/`).
- **Failed:**
  - R1: unowned 21.4% (18.9-24.2);
  - R2 on F3: registration 4.3%, 14% owned (F12 holds: 6.3%, 1% owned);
  - R3: naming 9.7%;
  - R6: `api_reuse` owns 3.8%.
- **Held:**
  - R4: explicit 42.0%;
  - R5: PR grain 9.3%;
  - R7: NEW 0.3%.
- **At scale:**
  - the largest unowned family is statement and API design (14.3% of asks, 61% unowned);
  - PR-level asks are 16% of AI-PR asks against 5% of the rest.
- **Proposal:** `design` becomes the main lever and `pr_level` an AI-PR arm; `interface` shrinks
  to registration. The
exploratory readings are not pre-registered: the family ranking, the AI stratum against main, and
the month-by-month shape. Shares get a 95% interval from a bootstrap over PRs.
