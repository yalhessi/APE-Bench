# PR Review v4 0.8.10 synthetic exemplar smoke plan

## Treatment

Version 0.8.10 differs from 0.8.9 only by three synthetic examples showing how to turn a weak code
observation into a concrete maintainer request. None contains a PR 33098 target, identifier, or
requested transformation. Byte-level regression tests verify that removing the exemplar block
reproduces every 0.8.9 prompt and that all dataset/gold/tool contracts are unchanged.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:24dac0bba5d216fc1ef940f3","wu:dde1bfbbaa031aa0a2fac1fb","wu:5f5a5a2a755d7e82671bca36"]' \
  dataset.run_name=pr_review_v4_pilot_0810_exemplar_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.10-exemplar-smoke3/candidate_responses.jsonl
```

## Acceptance gates

1. Execution/grounding: 3/3 success and every model candidate passes grounded ingestion.
2. Frozen deterministic channel: exactly one PR 33057 compile candidate, no deterministic control
   candidate, and one supported blocking PR 33057 finding.
3. Exemplar semantic effect: the frozen semantic judge finds at least one issue match among the
   three visible PR 33098 atomic obligations; resolution is reported separately.
4. Register: no defenses, vague risks, neighboring-target claims, or copied synthetic identifiers.
5. Control: zero selected PR 33438 findings; all raw control candidates are reported.
6. Attribution: compare model candidate count, targets, and semantic matches with 0.8.9. Increased
   volume without increased issue recall is a treatment failure.
7. Audit: manually verify every judged pair in this tiny run. A successful single run is directional
   and must be replicated once before expanding to the nine-PR pilot.

If issue recall remains 0/3, reject generic exemplars and next test temporally valid idiom/ask
retrieval as its own treatment. Do not combine another prompt change with retrieval.
