# PR Review v4 0.8.9 discovery and battery smoke plan

## Purpose

Repeat the exact three work units from 0.8.8 while separating two channels:

- deterministic discovery must recover factual compiler/linter failures;
- model generation must recover maintainer transformations from the explicit per-target checklist.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:45201a19e9bc4d6a23013291","wu:b5d86477bfa706af0077b107","wu:4ba70bd37a066bfd7486d2cf"]' \
  dataset.run_name=pr_review_v4_pilot_089_discovery_battery_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/candidate_responses.jsonl
```

## Post-run discovery command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.candidates \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.8.9/derived/work_units.jsonl \
  --responses results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/candidate_responses.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.8.9/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/candidate_responses_workspace_map.json \
  --allow-subset --deterministic-discovery \
  --out results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/candidates.jsonl
```

## Acceptance gates

1. Execution and grounding: 3/3 success; all model candidates pass grounded-ask ingestion.
2. Deterministic channel: exactly one target-local compile candidate for
   `PowerSeries.expand_apply`; no deterministic control candidate; no discovery failures.
3. Deterministic publication: PR 33057 yields one factual blocking finding after evidence selection.
4. Model semantic direction: at least one of the three visible PR 33098 atomic asks issue-matches.
5. Model register: no defenses, "worth checking" notes, or neighboring-target claims.
6. Control: zero selected PR 33438 findings; report every raw model and deterministic control
   candidate separately.
7. Volume: report candidates by producer and PR. A volume increase is not success unless semantic
   issue recall improves.

Passing deterministic gates with 0/3 model semantic recall means universal checks worked but the
facet battery did not. In that case, do not expand; next isolate generic maintainer-ask exemplars
from temporal idiom retrieval rather than adding both at once.
