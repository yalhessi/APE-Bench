# PR Review v4 0.8.8 grounding smoke plan

## Purpose

This is a three-work-unit real run, not a score-estimation run. It tests whether the grounded-ask
contract and maintainer-request prompt changed behavior in the intended direction before any larger
pilot is launched.

## Surfaces

- PR 33057: known target-local compile failure and evidence-conditioned blocking publication.
- PR 33098: one unit containing `isCover_maximalSeparatedSet`,
  `coveringNumber_le_packingNumber`, and `coveringNumber_two_mul_le_externalCoveringNumber`; this
  covers three of the four eligible atomic maintainer requests and the prior neighbor-target error.
- PR 33438: approved theorem control for raw and selected false-positive pressure.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:affa940a910a57dde99ca141","wu:7f49ec598feffd681a14def8","wu:d59cd1a05d1bce6367174cc7"]' \
  dataset.run_name=pr_review_v4_pilot_088_grounding_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.8-grounding-smoke3/candidate_responses.jsonl
```

## Acceptance gates

1. Execution: 3/3 terminal work units succeed and preserve three workspace roots.
2. Contract: every accepted candidate has a valid primary change/entity/subject and no model-authored
   evidence requests.
3. Grounding: no candidate attached to `coveringNumber_two_mul_le_externalCoveringNumber` primarily
   discusses `coveringNumber_le_packingNumber` or another neighbor.
4. Register: candidates are concrete requested transformations, not "worth checking", "may be
   brittle", or no-change observations.
5. Semantic direction: at least one of the three in-scope PR 33098 atomic asks issue-matches. This is
   a directional smoke gate, not a statistical recall estimate.
6. Publication: PR 33057's compiler-supported finding is factual and blocking; it must not retain
   "likely fine" or an unverified fix.
7. Control: PR 33438 has zero selected findings. Raw control candidates are reported and inspected,
   not silently discarded.

Any contract/grounding failure blocks prompt interpretation. A clean contract with 0/3 semantic
matches means the implementation landed but the register intervention failed and should be revised
before adding exemplars or retrieval.
