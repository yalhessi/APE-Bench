# Executor `/4`: one finding per failing file — and the arm publishes almost nothing

*2026-08-06. All 16 medium PRs, 2,253 tasks, 42 opportunities, judge-free, no model calls.
Supersedes `phase10-medium-executor-v4` (executor `/3`, 158 opportunities), which is
preserved. Sealed as `inputs/pr_review_v4/releases/dev-medium-0.2.1-systematic`.*

## What changed: 158 → 42

`_baseline_runner` compiles the whole reconstructed **file**, then under `/3` emitted one
opportunity per **target** in it. A file with seventy declarations produced seventy
near-identical "fails to compile" findings backed by the same cached compile — 128
opportunities from **12 distinct failing files**, 81% of the arm's output, and every target
containing no error was told it "fails to compile".

`/4` reports a failing file once. A single scheduled target carries the finding, chosen by a
claimant computed **up front from the whole task set** (not accumulated during dispatch, or
each task's outcome would depend on which ran before it) and **among supported tasks only** —
3 of 85 files have a lowest-`change_id` target that is not scheduled, so anchoring on the
change graph alone would have silently dropped those findings.

Diagnostic attribution now enriches the prose without gating the finding:

> `Family.lean` fails to compile at lines 866, 867. The diagnostics fall inside 3 changed
> declarations: `Ordinal.IsNormal.apply_omega0`, …

> `Expand.lean` fails to compile at line 35. **None of the diagnostics fall inside the lines
> this PR changed, so the change breaks code elsewhere in the file.**

Those are different review findings; `/3` rendered both as the same sentence, repeated. Line
attribution is deliberately *not* the dedup mechanism: 53/150 targets attribute, one file
attributes 16 of 18 (hunk spans are coarse), and two attribute nothing at all.

| implementation | opportunities | PRs |
|---|---:|---|
| `baseline_failure.target_compile.v1` | 12 | 33057, 33066, 33294, 33321, 33337, 33421 |
| `repository_policy.forbidden_construct.v1` | 19 | 33149 |
| `naming_norm.subject_prefix.v1` | 5 | 33098, 33145 |
| `naming_contrast.encard_subject_prefix.v1` | 3 | 33098 |
| `canonical_api.insert_separation.v1` | 1 | 33098 |
| `lint_norm.text_style.v1` | 1 | 33305 |
| `wrapper_composition.packing_cover_chain.v1` | 1 | 33098 |
| **total** | **42** | **0 on any control PR** |

## Byte-reproducible, now genuinely

Two independent full runs on identical inputs produce byte-identical `opportunities.jsonl`,
`opportunity_evidence.jsonl`, `operator_runs.jsonl`, `investigation_records.jsonl`,
`pipeline_ledger.jsonl` and `report.json`.

This did not hold before. Lean names diagnostics after the random temporary file it compiles,
and **129 of 410 evidence artifacts stored that name**, so every affected hash — and every
opportunity ID derived from it — changed on every run: identical findings, different bytes.
Three sites had the defect (`_baseline_runner`, `operators/canonical_api.check_applicability`,
`evidence.py`); the first fix caught only one, and a full re-run was needed to find the
others. The regression test now asserts the property **per module**, so a fourth site fails
immediately rather than after an hour-long run.

It stayed hidden because nothing had ever run this stage twice on the same inputs — the
3-repetition protocol had only ever been applied to model-driven stages.

## The Phase 0 finding: 42 opportunities are 3 published findings

Required before quoting the arm's yield. Running the frozen adjudication policy
(`phase7_adjudication._classify`, deterministic, free) over all 42:

| method | policy branch | worthiness | n |
|---|---|---|---:|
| `naming_contrast.v1` | `strong-naming` | **request** | **3** |
| `baseline_failure.v1` | `baseline-failure` | defer | 12 |
| `repository_policy.v1` | **`unresolved`** | defer | 19 |
| `naming_norm.v1` | **`unresolved`** | defer | 5 |
| `lint_norm.v1` | **`unresolved`** | defer | 1 |
| `canonical_api_search.v1` | `canonical-api` | defer | 1 |
| `wrapper_composition.v1` | `wrapper-composition` | defer | 1 |

**The deterministic arm's published tier outside the development PR is zero.** All three
requests come from `naming_contrast.v1` on PR 33098 — the frozen `encard`-specific
implementation that `naming_norm` now subsumes.

Two distinct causes, both pre-existing (executor `/3` gives the same 3 requests / 155
defers, so this is not a `/4` regression):

1. **Policy coverage gap.** `_classify` has no branch for `lint_norm.v1`, `naming_norm.v1` or
   `repository_policy.v1` — the three methods added since it was written. 25 of 42
   opportunities (60%) fall through to the `unresolved` fallback, which defers by
   construction.
2. **Evidence-vocabulary mismatch.** The `baseline_failure` branch gates on evidence text
   matching `{"compiled=false", "fails to compile", "compile failure"}` (`:184`). The
   executor writes `exit_code=1\n<compiled-target>:35:78: error: …`. The phrase "fails to
   compile" appears in the opportunity's `observed_pattern`, which is not an evidence
   artifact. So 12 genuine file-level build failures — the most objectively actionable
   findings in the corpus — can never reach `request`.

**Consequence for the merged ensemble:** as it stands, the published tier would be
holistic-only everywhere except PR 33098, which defeats the arm comparison the ensemble
exists to make. This must be resolved before the tier-small conditions are meaningful.

**A deferred opportunity is not free.** 39 defers would trigger 39 LLM redundancy requests
(2 votes each). The plan keeps `defer` out of LLM voting for this run — those votes are
non-deterministic and cost money, and would forfeit the arm's only two durable properties.
Deferred opportunities are `diagnostic`.

## Provenance

- Release `dev-medium-0.1.0`, treatment `systematic-opportunities-v3-medium`
- Executor `generic-opportunity-executor/4`, 2,253 tasks, 0 model calls, 0 `execution_failed`
- Sealed as `dev-medium-0.2.1-systematic`, whose manifest names `0.2.0-systematic` under the
  `supersedes` role. Both releases and both runs stay on disk so each manifest's provenance
  remains resolvable.
