# Phase 9 fixed-orchestration three-repetition verdict

## Verdict

Pass the implementation-readiness gate and proceed to the broader pilot. Do not claim an issue-recall
gain over holistic review.

Fixed orchestration is stable, selective, control-safe, and cheaper. It ties the call-matched
holistic union on mean issue recall, improves mean resolution recall and paired precision, and emits
far fewer candidates. The two systems recover different obligations, so the current registered
methods reorganize the judgment budget around high-confidence issue families rather than raising the
overall recall ceiling on this development PR.

## Aggregate

| Metric | Fixed pipeline | Call-matched holistic union |
| --- | ---: | ---: |
| Mean issue recall | 33.3% | 33.3% |
| Mean resolution recall | 25.0% | 16.7% |
| Mean paired-candidate issue precision | 88.9% | 61.7% |
| Raw candidates by repetition | 3, 3, 3 | 8, 7, 7 |
| Raw PR 33438 control candidates | 0, 0, 0 | 2, 2, 2 |
| Stable issue-hit obligations (at least 2/3) | 3 | 3 |
| Mean positive-scope cost | $0.1491 | $0.2278 |
| Mean cost including control | $0.1491 | $0.2993 |

The comparator is call-matched, not dollar-matched. The fixed pipeline is approximately 35% cheaper
on the positive scope and 50% cheaper when the holistic control call is included.

## Stability

Every fixed repetition accepted the same three opportunity IDs:

- `naming_contrast.v1` for `Metric.card_maximalSeparatedSet`;
- `canonical_api_search.v1` for `Metric.isCover_maximalSeparatedSet`;
- `wrapper_composition.v1` for `Metric.coveringNumber_le_packingNumber`.

Both model-generated edits compiled in every repetition. Naming and canonical API issue- and
resolution-matched in 3/3 samples. Wrapper issue-matched in 2/3 and resolution-matched in 0/3; its
candidate action and compiling edit were effectively identical across all repetitions, so the 2/3
variation is semantic-judge instability rather than generator instability.

The holistic union also had three stable issue families, but a different set: maximal-separated-set
proof simplification, cardinality-proof simplification, and empty-branch handling. Naming and
canonical API were largely absent. The systems are complementary rather than one dominating the
other.

## Coverage wall

Corrected stage attribution keeps context-only related changes out of issue scope. Across all 14
eligible PR 33098 obligations:

| Stage | Rep 1 | Rep 2 | Rep 3 |
| --- | ---: | ---: | ---: |
| Recovered | 2 | 3 | 3 |
| Candidate semantics | 2 | 1 | 1 |
| Source retrieval | 10 | 10 | 10 |

Ten obligations never receive a primary opportunity. This is now the dominant measured limitation.
No amount of adjudication stabilization or synthesis can recover those obligations. It does not
justify adding PR-33098-specific methods: the next useful evidence is whether the existing operators
produce valid opportunities across the other pilot PRs and which concern families remain uncovered
there.

## Additional observation

The holistic extension found the real `extenal` documentation typo in 3/3 repetitions, although it
is absent from benchmark gold. A weak missing-docstring request appeared only once. This is a useful
reminder that maintainer-comment recall is not complete review-quality recall and that unpaired
candidates require manual validity and worthiness audit, not automatic classification as false.

## Corrections made during inspection

- Partial semantic-judge JSON now preserves explicit boolean fields instead of defaulting to false.
- Miss attribution keys semantic results by candidate and obligation, not candidate alone.
- Related change IDs remain context evidence and cannot become issue anchors.
- The aggregate reports per-obligation frequencies, raw candidate/control pressure, and actual cost.
- The baseline is labeled call-matched rather than incorrectly called cost-matched.

The final machine-readable report is
`results/pr_review_v4/audits/phase9-fixed-orchestration-v4/report.json`.

## Decision

Phase 9 is complete. Freeze the current methods, policies, prompts, and thresholds. Implement the
nine-PR execution path next, beginning with a small diverse subset and using the same stage ledger.
Do not add a style-norm rule from the PR 33098 misses before broader results are available.
