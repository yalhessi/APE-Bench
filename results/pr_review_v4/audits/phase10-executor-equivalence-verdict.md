# Executor-vs-phase3/4/5 equivalence gate: FAILED at `/1`, RESOLVED at `/2`

*Run 2026-08-05 as Step 5 of the Phase 10 cleanup. Replay artifacts:
`scratchpad/equiv/` (not checked in — regenerate with the command below).*

> **Update (same day, result R0b).** The evidence-presentation gap below was closed in
> `generic-opportunity-executor/2`. The runners now render the quantitative warrant they
> already computed — population counts from `scan_repository_population`, the retrieval
> score from `rank_declarations`, and the named witness roles from the composition plan.
> On replay the executor now reproduces the frozen canonical-API and naming opportunities
> **exactly** (`observed_pattern`, `transformation.description`, and `transformation.kind`
> all byte-identical). Wrapper composition still differs, deliberately and in the
> executor's favour: its prose additionally names the repository wrapper and counts the
> witnesses, and its `transformation.kind` is `compose_wrapper_with_witnesses` — the term
> in the frozen method-expression contracts — rather than phase5's ad-hoc
> `compose_repository_wrapper`. That label is consumed by `synthesis.py` as a finding's
> action kind, so the change is real and is isolated behind the `/2` version bump.
>
> **This does not retroactively license archiving phase3/4/5.** They remain the producers
> of the frozen `dev-pilot-0.9.{1,2,3}` releases Phase 9 consumes, and the `/1` executor
> artifacts under `results/pr_review_v4/runs/phase10-executor-smoke-*` predate the change
> and are not comparable to `/2` output. The verdict below records the `/1` state that
> motivated the fix.

## Verdict

**The generic executor reproduces the discovery layer exactly, but not the
evidence-presentation layer.** Under the pre-registered rule ("if equivalence fails, stop
and document"), `phase3_canonical_smoke.py`, `phase4_naming_smoke.py`, and
`phase5_wrapper_smoke.py` are **retained, not archived**, and the frozen releases
`dev-pilot-0.9.{1,2,3}-*-smoke` remain the authoritative source for Phase 9.

## What was compared

The three frozen smoke releases were built by phase3/4/5 from `dev-pilot-0.9.0` using
cloned work units with synthetic investigation IDs (`investigation:canonical-smoke:…`).
The executor uses the real scheduled IDs from the Phase 2 treatment, and the
investigation ID is part of the sealed payload, so **artifact hashes cannot match by
construction**. Equivalence therefore had to be judged on content.

Because the Phase 2 treatment predates the implementation registry, capability
assessments were generated into a scratch treatment (the frozen treatment was not
touched) and the six relevant investigations replayed:

```
python -m src.datasets.pr_review_v4.opportunity_executor \
  --release inputs/pr_review_v4/releases/dev-pilot-0.9.0 \
  --treatment <scratch>/pilot-treatment --out <scratch>/equiv \
  --investigation-id investigation:ce06c3fea2e4bef4f76e149a  # canonical, PR 33098
  --investigation-id investigation:18b3ad0f78585f3ca183ec6c  # naming,    PR 33098
  --investigation-id investigation:1958654558fd4e4d01d2b7ad  # wrapper,   PR 33098
  --investigation-id investigation:0b89ac17a75fd56eb3aa8727  # canonical control, 33438
  --investigation-id investigation:2e8175ba04fe6f8b301109c1  # naming control,    33438
  --investigation-id investigation:d4e217104dbcef3090c697ad  # wrapper control,   33438
```

## What matches — the detection layer is equivalent

| Property | Result |
| --- | --- |
| Opportunities discovered, keyed by (method, primary_change_id) | identical set, 3/3 |
| `discovery_score` | identical (0.7 canonical, 0.9560439560439561 naming, 1.0 wrapper) |
| `discovery_rank` | identical (1, 1, 1) |
| Control PRs (33438) | zero opportunities in both — the executor's predicates return `unsupported_shape`, so the control targets are never even executed |
| canonical `transformation.kind` and `.description` | byte-identical |
| naming rename target | identical (`Metric.card_maximalSeparatedSet` → `Metric.encard_maximalSeparatedSet`) |

So the operators, retrieval, scoring, and applicability decisions are faithfully
generalized. The control-safety property that distinguishes the deterministic arm
survives.

## What differs — the prose the model actually reads

All three `observed_pattern` strings, one transformation description, and one
transformation `kind` differ. The executor's prose is **more generic and carries less
evidence**:

| | frozen (phase3/4/5) | executor |
| --- | --- | --- |
| canonical `observed_pattern` | "…`Metric.isSeparated_insert_of_notMem` is the top dependency-neighborhood retrieval **(score 28)** and is not used by the target." | "…is a high-confidence unused dependency-neighborhood retrieval." |
| naming `observed_pattern` | "…The scoped review-base population has **87/91** direct-subject declarations with an `encard_` leaf prefix and **no `card_` examples**." | "…has a direct `Set.encard` subject but a conflicting `card_` prefix." |
| naming `transformation.description` | "…and update all references in the PR **so the declaration's direct `Set.encard` subject is reflected in its leaf name**." | "…and update its references." |
| wrapper `observed_pattern` | "The target reconstructs an inequality through **low-level infimum reasoning** even though a frozen repository wrapper composes with **three current-PR witnesses**." | "A repository wrapper and current-PR witness chain form a concrete replacement." |
| wrapper `transformation.kind` | `compose_repository_wrapper` | `compose_wrapper_with_witnesses` |
| wrapper `transformation.description` | "…the generated composition of the repository wrapper and current-PR **cardinality, cover, and subset** witnesses." | "…the composed wrapper and witnesses." |

## Why this blocks archival

`observed_pattern` and `transformation.description` are not bookkeeping — they are
rendered into the adjudication prompt the model sees. The frozen prose supplies the
quantitative warrant (`87/91`, `score 28`, the three named witness roles); the executor's
prose asserts a conclusion without it.

Phase 9's headline numbers — 88.9% paired precision, resolution recall 25.0%, and the
identical-accepted-opportunities-in-3/3-repetitions stability that is the only
structurally reproducible result in this project — were measured against the **frozen**
prose. Swapping in weaker evidence text is a plausible cause of different adjudication
outcomes, so treating the executor as a drop-in replacement would silently put the
project's flagship result on an unvalidated code path.

The `transformation.kind` change is a second, narrower issue: the executor emits
`compose_wrapper_with_witnesses`, which is the vocabulary term used by the frozen
method-expression contracts (`implementation_registry.TRANSFORMATION_CLASSES`), whereas
the frozen artifact says `compose_repository_wrapper`. The executor's label is arguably
the better one, but it is a divergence from what Phase 9 consumed and must be a
deliberate, versioned change rather than a side effect of a refactor.

## Consequences

1. `phase3/4/5_*_smoke.py` stay live; the anti-duplication tests exempt them.
2. Phase 9 continues to consume the frozen `dev-pilot-0.9.{1,2,3}-*-smoke` releases.
3. Before the executor can carry a treatment arm, its evidence rendering must reach
   parity — the operators already compute the missing quantities (the naming population
   counts come from `scan_repository_population`, the retrieval score from
   `rank_declarations`), so this is a presentation gap, not a discovery gap.
4. That parity work belongs to the next treatment version with its own registry hashes,
   not to this cleanup.

## Reproducing

Re-run the command above and diff `opportunities.jsonl` against the three frozen
releases on `(method_id, primary_change_id)`, comparing `observed_pattern`,
`discovery_score`, `discovery_rank`, and `proposed_transformation`.
