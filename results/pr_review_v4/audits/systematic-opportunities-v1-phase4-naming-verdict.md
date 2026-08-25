# PR Review v4 Phase 4 naming contrast verdict

## Verdict

Pass Phase 4. The naming contrast smoke exceeded the pre-registered gate. Proceed to Phase 5 wrapper
and intra-PR composition without further tuning on this case.

## Results

| Gate | Result |
| --- | ---: |
| Successful generation calls | 6/6 |
| Positive rename requests | 3/3 |
| Positive issue matches | 3/3 |
| Positive resolution matches | 3/3 |
| Control `no_request` | 3/3 |
| Control candidates | 0/3 |
| Exact-obligation paired precision | 3/3 |

Every positive candidate identified the direct `Set.encard` subject of
`Metric.card_maximalSeparatedSet` and requested the exact collision-free
`Metric.encard_maximalSeparatedSet` rename. Wording varied, but target, diagnosis, requested name,
advisory force, and semantic outcome were stable.

Every control recognized that `Metric.exists_set_encard_eq_packingNumber` has an existential role,
already includes the semantic subject in its name, and has no supported alternative. No control
candidate was emitted.

Generator cost was $0.3409175 across all six calls: $0.1715245 on positives and $0.169393 on
controls. Semantic-judge cost is not included.

## Interpretation

Phase 4 independently reproduces the Phase 3 pattern: deterministic, auditable opportunity discovery
stabilizes which issue is considered, while the model performs bounded validity, norm, and
review-worthiness adjudication. This is stronger evidence for the architecture than either smoke
alone because naming uses repository-wide convention evidence rather than an exact replacement API.

The claim remains method- and subject-bounded. The experiment demonstrates one `Set.encard` naming
norm, not general naming discovery across Mathlib. The 91-member population, all four exceptions, and
collision result are frozen, but generalization still belongs to the nine-PR pilot and temporal
holdout.

## Scope audit

The third candidate suggested that `card_minimalCover` might be considered in a separate follow-up,
while explicitly stating that it was not part of the current opportunity. It did not add another
change ID or request and therefore does not invalidate this gate. It does expose a future synthesis
requirement: published candidates should not carry side suggestions outside their opportunity scope.

Exact obligation scoping worked as intended. The naming report evaluates only
`obligation:45433fc367bdd15dc606eaabeadaa16ad98077afec83ca662fe39bcf938632ad`,
not the proof-compression obligation sharing the same change target.

## Commands

No further API-backed command is required for Phase 4. The local regression command is:

```bash
./ape/bin/python -m pytest tests/datasets -q
```

The next implementation step is Phase 5 wrapper and intra-PR composition. Its real smoke commands
should be supplied only after its offline source, composition, and control gates pass.
