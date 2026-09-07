# Next iteration: architecture and the results still to generate

*Written 2026-08-05, after the v4 cleanup pass. Companion to
`pr-review-v4-system-manual.md` (how the current system works) and
`pr-review-v4-phase10-medium-executor-and-census-design.md` (the census that produced
the wall this roadmap attacks).*

---

## 1. Where the evidence actually leaves us

Three measured facts constrain everything below.

**The two arms are complementary, not competing.** On the development PR, the fixed
deterministic pipeline and the call-matched holistic reviewer tie on mean issue recall
(33.3% each) while recovering **nearly disjoint** obligations — their union is ~6/8 on
matched scope. The deterministic arm wins on precision (88.9% vs 61.7%), control safety
(0 vs 2 false candidates per repetition), cost (~35% cheaper), and reproducibility
(identical accepted opportunities in 3/3 repetitions — the only structurally
reproducible result in the project's history). The holistic arm wins on breadth, and
found a real docstring typo absent from gold in 3/3 repetitions.

**The binding constraint is implementation reach, not method design.** The static
coverage census over the 16-PR medium benchmark scored all 40 evaluation-eligible
obligations: C0 (a scheduled investigation overlaps the code) 40/40, C1 (a frozen method
contract covers the ask) 15/40, **C2 (an executable implementation accepts the target
shape) 5/40 — all five on the development PR, 0/26 elsewhere.** The pre-registered gate
returned `static_reachability_rejected`, so the paid medium run was skipped at zero model
cost. The cause is that implementations are single-shape: `operators/naming_contrast.py`
hardcodes `SUBJECT = "Set.encard"` and requires a `card_` prefix, so it cannot fire on
PR 33337's `toLinearMap_` renames even though the naming *method* covers them.

**Generalizing the operators is not free.** The Step 5 equivalence replay found that
`opportunity_executor` reproduces the phase3/4/5 **discovery** layer exactly — same
opportunities, same `discovery_score` and rank, same canonical transformation, zero
control candidates — but emits **weaker evidence prose**. Where the frozen text supplies
the quantitative warrant ("87/91 direct-subject declarations with an `encard_` prefix and
no `card_` examples", "the top retrieval (score 28)"), the executor asserts the
conclusion without it. Those strings are rendered into the adjudication prompt, and
Phase 9's precision and stability numbers were measured against the frozen prose. Full
verdict: `results/pr_review_v4/audits/phase10-executor-equivalence-verdict.md`.

---

## 2. Target architecture

Preserve what makes the deterministic arm valuable — pure, gold-free, shape-predicated
operators — while making its reach an improvable quantity and letting the holistic arm
cover the residual.

**L0 — Norm provisioning (`norms/`).** A dated store with
`lifecycle ∈ {announced, emerging, contested, established, hardened}`, `as_of_date`, and
`evidence_refs`, mined from in-tree adoption trends, recency-weighted precedent, and
dated repo artifacts (lint rules, `@[deprecated]`, style-guide diffs). The Phase 6 lesson
is the design requirement: **the store must declare its own coverage.** Below an evidence
threshold it emits `insufficient_evidence` and does not provision, which turns "`grind`
has two temporally-eligible mentions in an 8,161-event ledger" from a silent blocker into
a publishable measurement.

**L1 — Generalized checkers (`checkers/`).** Same purity contract; that property is what
buys reproducibility and control safety and must survive generalization.
- `naming_norm.py`: run the population scan over *the target's own conclusion subject*
  rather than a fixed token — `SubjectPrefixNormImplementation(subject_token, prefix_norm)`
  mined from the snapshot. The operator already computes `scan_repository_population` and
  `strong_subject_prefix_norm`; this is the smallest change with the largest expected C2
  lift. **BUILT and MEASURED 2026-08-05** (`operators/naming_norm.py`;
  `audits/naming-generalization-measured.md`) — the estimate was optimistic. Against the
  real snapshots it reaches **1** obligation outside the dev PR (PR 33145 `upperBounds`/
  `lowerBounds`, 27/27 and 25/25), on 1 PR via 1 implementation. Control safety is
  preserved (0 proposals on all three control PRs). PR 33337 is **not** reachable: the
  maintainer asks for the `toLinearMap_` convention, but at that snapshot `toLinearMap_`
  holds only 17% (121 members) and the `→ₗ` coercion is dominated by `coe_` at 39% — the
  ask is norm-*establishing*, not norm-*enforcing*, so a frequency rule is structurally
  blind to it. This is the `grind` phenomenon in the naming family and is direct evidence
  for L0. Of the 8 naming obligations only 4 are convention-enforcement a population rule
  can express, and all 4 are now reached.
- `canonical_api.py`: `match_insert_separation_template` becomes a template *set*, plus a
  template-free fallback ranked by dependency-neighborhood retrieval and gated on the
  applicability compile.
- `wrapper_composition.py`: fixed witness roles → goal-shape-derived required roles.
- New families for the 12 obligations no method expresses, cheapest first: `style_norm`
  (5 obligations), `docs_gap` (3), `scope_placement` (1). **Two of the three are now
  falsified as designs**, both by measurement rather than by argument:
  - `docs_gap` — **rejected 2026-08-05** (`audits/convention-class-reach.md`). Only 8% of
    Mathlib lemmas and 67% of definitions carry a docstring, so a missing-docstring rule
    would fire on 92% of new lemmas. The corpus's docs asks are selective editorial
    judgements, not applications of a blanket rule.
  - `style_norm` — **capped 2026-08-06** (`audits/phase10-medium-static-census-v3methods`).
    `lint_norm` was rebuilt from one hand-picked rule into a faithful reimplementation of
    Mathlib's own text-style linters (18 rules, Mathlib's own ERR codes). Across all 16
    medium PRs this produces **one** finding — the same one the single-rule version found —
    and **zero** on 192 already-merged targets, which is the check that the rules are
    correctly transcribed rather than broken. The reason is structural: **Mathlib runs
    these linters in CI, so mechanically-detectable style violations are already gone by
    the time a human reviews.** What remains in human style review is by construction the
    residue no linter catches, and no amount of rule completeness recovers it.

**Every generalization is gated on control PRs still yielding zero candidates**, and — new
requirement from Step 5 — **on evidence-prose parity**: a generalized checker must emit
the quantitative warrant its narrow predecessor did.

**L2 — Router (`route.py`).** Split the census: the gold-side scoring stays
evaluation-side (`census.py`); the gold-free half (`assess_capabilities`) becomes a
runtime router emitting `covered_scope` (≥1 `supported` assessment → deterministic arm)
and `residual_scope` (→ holistic arm, with the covered part named and excluded, as
`phase8_residual`'s prompt already does). Because the partition is gold-free it is
**pre-registerable**, which is what makes a union claim honest rather than post-hoc.

**L3/L4 — Two arms, one evidence machinery, then merge and judge.** A single `merge.py`
dedupe primitive replaces the three current implementations, feeding one judge run.

**Framework mapping.** Checkers are **not** tasks — they are pure and LLM-free, and the
orchestrator exists to manage conversations, turns, and cost, of which they have none.
They stay operators, additionally exposed as a `ReviewCheckerToolsProvider` so the
holistic agent can call the same code (`canonical_api_search`, `naming_norm_lookup`,
`wrapper_compose`, `norm_lookup`). The residual pass is a **task variant**
(`review_mode`, `excluded_findings`, `norm_pack_ids`), not a new task type. The judge is
a registered task run **top-level** — never nested inside the reviewer, because it reads
gold and the reviewer's run tree must stay gold-free. The norm pack is prompt-injected
with its sha256 recorded in the `RunPlan`.

---

## 3. Results still to generate

Budgets: small (3 PRs) unlimited; **medium pre-registered only — the static census counts
as a look**; large ≤3 lifetime uses; holdout frozen. Three repetitions minimum; report
mean, union, and stable, via `reports.rep_summary`.

| # | Result | Cost | Establishes | Gate |
|---|---|---|---|---|
| **R0** | Judge equivalence: current script vs registered task | ~$0.6 over 3 rounds | **DONE 2026-08-05** (`audits/r0-judge-equivalence/VERDICT-final.md`). Migration is sound; the **gate was mis-specified**. The judge is not deterministic: ~11% of pairs (2 of 18) are bimodal, giving a self-agreement ceiling of **90.1%** — a judge compared to *itself* could not clear the original 95% bar. On deterministic pairs the arms agree 11/12, the miss being a diagnosable task-arm rubric error. **Noise floor: ±1 obligation at n≈8 ≈ ±12pp for v7.1-scored results** (which is everything reported through Phase 9). **v8 is the active rubric as of 2026-08-05**; v7.1 is retired to `src/mathlib_review/legacy_pipeline/judge_v71.py` for provenance only. Under v8 the judge measured 0/18 split pairs and a 100% self-agreement ceiling, so v8-scored comparisons carry approximately no judge noise — see `audits/judge-v8/VERDICT.md`. Numbers are comparable only within a rubric version. | restated: ≥95% on deterministic pairs + published bimodal set + zero coverage loss |
| **R0b** | *(new, from Step 5)* Executor evidence-prose parity | no LLM | that a generalized checker emits the same quantitative warrant as its narrow predecessor | **DONE 2026-08-05 — PASS.** `generic-opportunity-executor/2` reproduces the frozen canonical-API and naming prose **exactly**; wrapper carries all the frozen warrant plus the wrapper name and witness count, with `transformation.kind` moved onto the frozen contract vocabulary. Pinned by `test_pr_review_v4_evidence_warrant.py` |
| **R1b** | Human audit of the 21 pending-C1 and 12 no-method obligations | no compute | the true C1 ceiling, and which new checker family is worth building | must precede R1 |
| **R1** | Generalization sweep: re-run `assess_capabilities` + census | **one medium look** | the new C2 count | the existing pre-registered gate: ≥3 C2 obligations outside the dev PR, across ≥2 PRs, via ≥2 implementations. Develop against tier-small + R1b; run the medium census **once**, on frozen implementations |
| **R2** | Holistic under-sampling curve: 3 → 9 repetitions, tier-small | zero look cost | whether holistic recall is a sampling problem or a capability ceiling | union saturates by rep 5 → fix n=5 everywhere; if not, "present but under-sampled" is a headline and n must be budgeted explicitly |
| **R3** | Checker-as-tool ablation, tier-small, 3 reps × 2 conditions | small | whether unification helps the broad arm | precision ≥ 61.7%; control candidates ≤ 2/rep |
| **R4** | Routed hybrid, tier-small, 3 reps | small | that the partition is pre-computable, non-overlapping, and recovers the ~6/8 union **in one condition** rather than as a post-hoc union | routed recall ≥ max(arm recalls) and ≥ union − 1; precision ≥ 80%; controls ≤ holistic-alone |
| **R5** | Norm coverage report | no LLM | whether the evolving-norm hypothesis is testable in this corpus at all | too few norms reach emerging/established → **R6 is cancelled** and the coverage number is reported as the negative result |
| **R6** | Norm-provisioned vs not, both arms, tier-small, 3 reps | small | the "checkers win especially with recent evolving norms" hypothesis | only if R5 passes |
| **R7** | Medium pre-registered run, 3 reps | medium | generalization beyond the development PR | only after R1 flips to `authorized_for_paid_smoke`; `create_run_plan` seals work units, prompt hashes, model, arm assignment, judge version, norm-pack hash, metrics, and the decision rule **before** execution |
| **R8** | Large tier | 1 of 3 lifetime looks | confirmation at scale | only after medium is stable across 3 reps; reserve the other 2 looks |
| **R9** | Temporal holdout | once, final | the generalization claim | reported regardless of outcome |
| **R∞** | Reproducibility receipt | continuous | promote "identical accepted opportunities in 3/3" from a run verdict to a first-class artifact, re-verified at every tier | if generalization breaks it, that is a first-order finding |

---

## 4. Sequencing note

R0 and R0b are both free and both block real work: R0 because judge noise (~4pp at n=8)
otherwise contaminates every comparison, R0b because generalized checkers cannot be
trusted to carry a treatment arm until they present evidence as well as their narrow
predecessors did. Do them first, in either order. R1b is a human sitting and gates R1,
which is the one medium look that decides whether a paid run happens at all.
