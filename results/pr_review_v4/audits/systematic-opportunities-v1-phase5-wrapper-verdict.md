# PR Review v4 Phase 5 wrapper composition verdict

## Verdict

Pass Phase 5. The wrapper-composition smoke exceeded the pre-registered real gate. Proceed to Phase
6, while keeping the claim limited to reliable adjudication of this automatically constructed
opportunity rather than general wrapper discovery.

## Results

| Gate | Result |
| --- | ---: |
| Successful generation calls | 6/6 |
| Positive wrapper requests | 3/3 |
| Positive issue matches | 3/3 |
| Positive resolution matches | 0/3 |
| Positive Lean verification | 3/3 |
| Control `no_request` | 3/3 |
| Control candidates | 0/3 |
| Exact-obligation paired precision | 3/3 |

All three positives requested replacing the low-level `iInf_le`/`trans`/`le_of_eq` derivation in
`Metric.coveringNumber_le_packingNumber` with `Metric.IsCover.coveringNumber_le_encard`, composed
with `Metric.isCover_maximalSeparatedSet` and `Metric.maximalSeparatedSet_subset` after the
cardinality rewrite. Each trajectory called `lean_verify_edit`; all three returned success with no
errors, warnings, or axioms.

All three controls recognized that the parallel `Real.arctan_sqrt_three` proof does not by itself
establish a wrapper-composition opportunity. Each returned `no_request` and emitted no candidate.

Generator cost was $0.657305 across all six calls. Per-repetition costs were $0.162983, $0.325946,
and $0.168376. Semantic-judge cost is not included.

## Interpretation

Phase 5 demonstrates that deterministic PR-relation traversal, review-base wrapper retrieval, and a
concrete composition plan can stabilize bounded model judgment. Unlike the earlier voluntary
generation runs, the model selected the intended issue in every repetition and did not turn parallel
shape into a criticism on the control.

Resolution recall is 0/3 for a known, informative reason. The Phase 5 plan uses
`card_maximalSeparatedSet` and ordinary `by_cases`; the frozen maintainer resolution uses the separate
Phase 4 `encard_maximalSeparatedSet` rename and `by_cases!`. The judge consistently accepted the issue
and rejected exact resolution. This is not a Phase 5 source-recovery failure, but it is evidence that
independently discovered opportunities do not yet synthesize into one adopted maintainer edit.

The claim remains narrow. The smoke operator recovered one pre-registered wrapper family and its
three required current-PR witnesses. The result validates the architecture and smoke mechanism, not
coverage or generalization over arbitrary Mathlib wrapper compositions. Those belong to later
holdout and synthesis gates.

## Commands

No additional API-backed Phase 5 command is required. Local regression remains:

```bash
./ape/bin/python -m pytest tests/datasets -q
```

The next implementation step is Phase 6, the historical adopted-transformation store.
