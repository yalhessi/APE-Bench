# PR Review v4 0.8.11 temporal retrieval smoke replication plan

## Frozen replication contract

Replicate the first 0.8.11 smoke without changing the release, prompts, retrieval artifacts, model
configuration, work units, deterministic discovery, evidence policy, selector, or semantic judge.
Only the run name and output directory change. The fresh run must contain new terminal model responses;
artifacts from the first smoke are comparison inputs only.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:2b90f62f628fe3c4b85f80e6","wu:a0ca0f4fe2020cb90e566181","wu:a760602702a7288361685f67"]' \
  dataset.run_name=pr_review_v4_pilot_0811_temporal_retrieval_smoke3_rep2 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.11-temporal-retrieval-smoke3-rep2/candidate_responses.jsonl
```

## Acceptance gates

1. Execution: 3/3 calls succeed with one terminal response per work unit.
2. Semantic replication: the frozen judge reports at least one issue hit among the same three
   included PR 33098 obligations. Resolution recall remains a separately reported metric.
3. Control: PR 33438 has zero selected findings; raw control candidates are reported even if
   evidence rejects them.
4. Deterministic stability: PR 33057 yields exactly one supported blocking compile finding and no
   deterministic control finding.
5. Transfer discipline: copied historical asks that do not match current code are false positives.
6. Pending-decomposition diagnostic: report target-level matches to `pr33098_i01` separately without
   adding them to the frozen headline denominator.

If included issue recall is again nonzero and control selection remains zero, proceed to decompose
`pr33098_i01` and then run the nine-PR pilot. If issue recall returns to zero, treat the first result
as unstable and inspect candidate variance before expanding.
