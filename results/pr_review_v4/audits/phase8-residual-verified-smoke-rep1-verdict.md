# Phase 8 verification-backed residual smoke rep1 verdict

## Verdict

The verification-backed submission fix passes. The residual discovery method does not yet pass its
positive-recovery gate.

Both work units completed and ingestion closed cleanly. The run produced zero candidates, zero
verification artifacts, zero evidence packets, and zero selected findings. This is correct for the
PR 33438 control, but PR 33098 also produced no novel candidate. The change therefore improves raw
precision and operational safety without improving residual issue recall.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Execution | Pass | 2/2 terminal responses succeeded. |
| Ingestion | Pass | Both PR units have terminal residual records. |
| Tool distinction | Pass | Agents used `lean_verify_edit` for reviewed-file checks; no invalid `lean_verify target/...` calls occurred. |
| Verification enforcement | Pass | Failing edits were discarded before submission; no unverified checkable candidate entered ingestion. |
| Control precision | Pass | PR 33438 produced zero submitted and selected candidates. |
| Positive residual recovery | Fail | PR 33098 produced zero candidates and recovered no missed obligation. |
| Publication safety | Pass | Evidence and selection both terminate at zero. |

## Trace interpretation

On PR 33098, the agent read the complete 422-line changed file in three chunks, compiled the reviewed
file successfully with `lean_verify_edit`, and abstained. This is not an execution failure or a prompt
truncation artifact. It simply did not infer a request-worthy residual concern, including the missed
calc-layout style obligation at `Metric.coveringNumber_subset_le`.

On control PR 33438, the agent compiled the baseline successfully, then tested two explicit rewrites
of the `all_goals` proofs. Both rewrites failed because `constructor` was applied to individual
inequality goals. The agent correctly submitted an empty list. This directly eliminates the two
false blocking candidates from the unverified 0.1.0 run.

## Comparison with 0.1.0

| Metric | Unverified 0.1.0 | Verified 0.1.1 |
| --- | ---: | ---: |
| Raw candidates | 3 | 0 |
| Raw control candidates | 2 | 0 |
| Supported candidates | 0 | 0 |
| Selected findings | 0 | 0 |
| Invalid verification attempts | 2 | 0 |
| Persisted unsupported candidates | 3 | 0 |

The final published result is unchanged, but invalid hypotheses are now rejected before they become
candidate records. Generator cost was approximately $0.2456, versus approximately $0.1798 for the
unverified run; the extra cost bought real verification and false-positive suppression, not recall.

## Decision

Keep verification-backed submission as an infrastructure invariant. Do not expand the residual pass
or run a semantic judge on this repetition. Treat open residual review as a conservative fallback,
not as the mechanism expected to raise recall.

The next accuracy experiment should return to structured opportunity generation for the missed
calc-layout norm. A targeted method should expose concrete style transformations and repository
contrast evidence before adjudication; asking one holistic residual agent to rediscover that norm
from a complete file did not work.

## Inspection commands

```bash
jq . results/pr_review_v4/runs/phase8-residual-verified-smoke-rep1/ingested/report.json

jq -s 'map({work_unit_id, success, error, response})' \
  results/pr_review_v4/runs/phase8-residual-verified-smoke-rep1/candidate_responses.jsonl

wc -l results/pr_review_v4/runs/phase8-residual-verified-smoke-rep1/ingested/{candidates.jsonl,verification_artifacts.jsonl,evidence/packets.jsonl,evidence/assertions.jsonl,findings.jsonl}
```

No additional command or paid judge should be run for this repetition.
