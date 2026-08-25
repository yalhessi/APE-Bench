# PR Review v4 Phase 3 canonical API verdict

## Verdict

Pass Phase 3. The canonical API smoke exceeded every pre-registered gate. Proceed to Phase 4 naming
contrast without further prompt or threshold tuning on this case.

## Results

| Gate | Result |
| --- | ---: |
| Successful generation calls | 6/6 |
| Positive requests | 3/3 |
| Positive Lean verification | 3/3 |
| Positive issue matches | 3/3 |
| Positive resolution matches | 3/3 |
| Control `no_request` | 3/3 |
| Control candidates | 0/3 |
| Paired-candidate issue precision | 3/3 |

Every positive candidate named `Metric.isSeparated_insert_of_notMem`, targeted
`Metric.isCover_maximalSeparatedSet`, and requested replacement of the manual inserted-set case
analysis. The three candidates differed slightly in edit shape, but all compiled and all matched the
same issue and adopted resolution under the frozen semantic rubric.

The control consistently recognized that `Real.arctan_tan` was already used and that no replacement
had been discovered. It emitted no candidate in any repetition.

Generator cost was $0.7286055 across all six calls: $0.6268395 on the three positive adjudications
and $0.101766 on controls. Semantic-judge cost is not included in that total.

## Interpretation

This is the first clean demonstration that deterministic opportunity discovery can remove the
voluntary-generation instability seen in earlier holistic and retrieval-primed runs. Retrieval was
fixed before the model call; the model's role was bounded to applicability, norm strength, and review
worthiness. Wording varied, but issue selection did not.

The result supports the systematic-opportunity architecture, not a broad claim that canonical API
discovery is solved. It contains one positive operation shape and one negative control. The relevant
next question is whether other independently specified methods can reproduce this pattern, beginning
with naming contrast, before the fixed nine-PR pilot tests breadth.

## Audit correction

Two raw candidates serialized `proposed_edit.path` with a leading `target/`. Lean verification used
the correct path, so the semantic and applicability verdicts are unaffected, but downstream evidence
collection would have failed. Submission and ingestion now normalize common workspace/diff prefixes
and submission validates the normalized path against the PR's changed files. Normalized candidate
artifacts were regenerated as `candidates-normalized.jsonl` for all three repetitions.

## Commands

No further API-backed command is required for Phase 3. The local regression command is:

```bash
./ape/bin/python -m pytest tests/datasets -q
```

The next implementation step is Phase 4 naming contrast. Its real smoke commands should be supplied
only after its offline retrieval and control gates pass.
