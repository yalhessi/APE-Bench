# First full deterministic execution over medium

*2026-08-06. All 16 medium PRs, all seven implementations, 2,253 tasks, 158 opportunities.
Judge-free, no model calls, no cost. The first time the deterministic arm has been
**executed** — rather than statically assessed — beyond the development PR.*

## Headline

| claim | verdict |
|---|---|
| Control PRs stay silent at the **runner** | **holds** — 0 opportunities on 33304, 33315, 33438 |
| The arm is byte-reproducible | **holds, after a fix** — two independent runs, all six artifacts identical |
| C2 predicts what the arm actually finds | **fails for `naming_norm`** — 8 C2 obligations outside dev, 2 opportunities |
| `baseline_failure` is precise at scale | **fails** — 128 opportunities from 12 distinct failures |

## Control safety survives generalization — but only the runner shows it

This was the property at risk. `naming_norm`'s capability predicate is far more permissive
than its predecessors: it accepts any conclusion with a high-confidence direct left-hand
subject, and is `supported` on 66 assessments across 11 PRs including **2 on control PR
33438**. Assessment-level control silence, which the v2 census reported, is gone.

**It does not matter, because the runner makes the decision.** The `MIN_SUPPORT=20` /
`MIN_SUPPORT_RATIO=0.80` / `MAX_CONFLICT_RATIO=0.05` filter rejected both control targets,
and every other implementation was silent on controls. The arm produced **zero** candidates
on all three control PRs.

The lesson is about measurement, not the checkers: **control safety cannot be read off the
census.** A capability assessment says "this shape is in scope"; only execution says "this
is a finding." The earlier zero-control-firing claim was measured at the assessment layer
and happened to coincide with runner behaviour. That coincidence has broken, and the
runner-level measurement is the one to quote.

## The arm was not byte-reproducible, and now is

Comparing two executions on identical inputs produced 158 opportunities each with identical
content but **different hashes**. Cause: Lean reports diagnostics against the throwaway
`.lean` file it is handed, whose name is random, and that name was stored in the evidence
content. **129 of 410 evidence artifacts re-hashed on every run**, and every opportunity ID
derived from them changed with it.

This is worse than cosmetic. Reproducibility of the deterministic arm is the project's
strongest differentiator; `write_once` would raise on any rebuild; and the freeze ledger
could never verify a re-derivation. It stayed invisible because nothing had ever run this
stage twice on the same inputs — the 3-repetition protocol had only ever been applied to the
model-driven stages.

Three sites compiled temporary files and had the identical defect —
`opportunity_executor._baseline_runner`, `operators/canonical_api.check_applicability`, and
`evidence.py`. The first fix caught only the first, and a full re-run was needed to find the
other two, so the regression test now asserts the property **per module**: any module that
compiles a temporary `.lean` file must substitute `io.COMPILED_TARGET`.

**Verification:** two independent full runs, byte-identical across `opportunities.jsonl`,
`opportunity_evidence.jsonl`, `operator_runs.jsonl`, `investigation_records.jsonl`,
`pipeline_ledger.jsonl` and `report.json`; zero residual temp paths.

`EXECUTOR_VERSION` is now `generic-opportunity-executor/3`. No frozen release contained a
temp path, so nothing already sealed is affected; `/2` and `/3` artifacts are
content-comparable but not hash-comparable.

## C2 overstates `naming_norm`'s reach by about 4×

| | census C2 (shape accepted) | executed (opportunity emitted) |
|---|---:|---:|
| outside the dev PR | 8 obligations | **2 opportunities** |
| PRs outside the dev PR | 6 | **1** (33145) |

The two are `Dense.continuous_upperBounds` (27/27 population support) and
`Dense.continuous_lowerBounds` (25/25). Everything else counted as C2 was a target whose
*shape* was in scope but whose subject has no strong norm in the snapshot, so the runner
correctly returned `checked_no_opportunity`. This reproduces the earlier
`naming-generalization-measured` finding exactly.

The reachability gate's conclusion is unaffected — it was already cleared on `lint_norm` and
`repository_policy`, whose predicates are near-exact — but **C2 is no longer uniform across
implementations, and reach should be quoted from execution.** The repair is a precomputed
per-snapshot subject-norm index carried as a release artifact, letting the predicate ask the
real question cheaply and gold-free. It has not been built.

## `naming_norm` subsumes `naming_contrast`

On PR 33098 both fire on the same three declarations (`card_le_of_isSeparated`,
`card_maximalSeparatedSet`, `card_minimalCover`), the subject-general rule reporting 84/88
support where the `encard`-specific rule reports 87/91 — the same convention over slightly
different populations, because one keys on `encard` and the other on `Set.encard`.

`naming_contrast.encard_subject_prefix.v1` reaches nothing `naming_norm.subject_prefix.v1`
does not. Retiring it would remove a duplicate candidate per target; it is kept only because
Phase 9's frozen results depend on it.

## `baseline_failure` duplicates one failure into many findings — pre-existing

| PR | opportunities | distinct failing files |
|---|---:|---:|
| 33057 | 8 | 1 |
| 33066 | 11 | 1 |
| 33294 | 70 | 5 |
| 33321 | 13 | 2 |
| 33337 | 2 | 1 |
| 33421 | 24 | 2 |
| **total** | **128** | **12** |

The runner patches and compiles the whole *file*, then emits one opportunity per *target*, so
a file with seventy declarations yields seventy near-identical findings backed by the same
cached compile. At small-tier scale this was invisible; at medium it is **81% of the arm's
output**.

This is not introduced here — `_baseline_runner`'s dispatch logic is unchanged — and is
deliberately **not** fixed, because that runner is on the code path covered by the Phase 9
executor byte-equivalence proof. Changing its deduplication would invalidate that proof, so
it needs to be a versioned, pre-registered change rather than a quiet edit.

The underlying failures look genuine: sampled diagnostics are real Lean errors at the
review-time head (deprecations with changed types, application type mismatches, unsolved
goals), not reconstruction artifacts.

## Three crashes the census could not have found

All three new runners failed on **every** task in the first execution (86 `execution_failed`);
the second still failed 61:

| bug | symptom |
|---|---|
| `population.counts` — the field is `prefix_counts` | `AttributeError` × 66 |
| `kind="lint_report"` / `"policy_report"` absent from the schema literal | `ValidationError` × 20 |
| `status="skipped"` absent from `OperatorRun.status` | `ValidationError` × 61 |

None produced a traceback: the executor catches runner exceptions and records only the
exception *type* in the ledger. Each cost a full 2,253-task run to discover.

`tests/datasets/test_pr_review_v4_executor_runners.py` closes this. Besides executing the
two workspace-free runners end to end, it **statically** walks the executor's AST and asserts
every string literal passed into a closed schema enum (`OperatorRun.status`,
`OpportunityEvidenceArtifact.kind`) is declared there — covering the workspace-dependent
runners that cannot be executed in a unit test — and asserts the registry and
`DEFAULT_RUNNERS` agree, so a registered implementation can never again lack a runner.

## What the arm produces on medium

| implementation | opportunities | PRs |
|---|---:|---|
| `baseline_failure.target_compile.v1` | 128 | 33057, 33066, 33294, 33321, 33337, 33421 |
| `repository_policy.forbidden_construct.v1` | 19 | 33149 |
| `naming_norm.subject_prefix.v1` | 5 | 33098, 33145 |
| `naming_contrast.encard_subject_prefix.v1` | 3 | 33098 |
| `canonical_api.insert_separation.v1` | 1 | 33098 |
| `lint_norm.text_style.v1` | 1 | 33305 |
| `wrapper_composition.packing_cover_chain.v1` | 1 | 33098 |
| **total** | **158** | 0 on any control PR |

Outside the development PR (33098), collapsing both duplication effects, the arm finds: two
renames (33145), one style violation (33305), nineteen axiom introductions answering one
maintainer ask (33149), and twelve file-level build failures across six PRs.

## Provenance

- Release `inputs/pr_review_v4/releases/dev-medium-0.1.0`, treatment
  `inputs/pr_review_v4/treatments/systematic-opportunities-v3-medium`
- Executor `generic-opportunity-executor/3`, 2,253 tasks, 0 model calls
- Sealed as `inputs/pr_review_v4/releases/dev-medium-0.2.0-systematic`
  (`medium-execution-release/1`), which refuses any run from a different executor version or
  with a non-zero `execution_failed` count
