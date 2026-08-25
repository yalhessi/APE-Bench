# PR Review v4 stable-core gate

## Current verdict

The development core is structurally stable enough to begin controlled expansion and shrink
ablations. The canonical release is `dev-pilot-0.9.0`, built from reviewed atomic judgments and a
treatment-neutral prompt. Dataset validation, run accounting, evidence lineage, semantic pairing,
and evaluator scoping pass the local regression suite.

The gate is not an empirical claim that the reviewer performs well. A new real three-unit smoke,
human audit of supported evidence packets, a full nine-PR development run, and a frozen temporal
holdout still remain.

## Deferred work

1. Recover or explicitly freeze out four unavailable later-round compares and export self-contained
   Git source objects. This does not affect the nine round-one pilot inputs.
2. Audit evidence support precision and add collectors only for claim families that fail for a known
   missing evidence type.
3. Run the stable three-unit smoke below, then the full nine-PR development pilot.
4. Freeze a mixed temporal holdout before tuning against more PRs.
5. Treat historical retrieval, prompt facets, deterministic discovery, structured edits, and selector
   policies as independent expansion or shrink ablations over the same stable core.

## Three-unit smoke

This smoke covers a known compile-sensitive intervention, a multi-obligation proof/naming case, and
a substantive theorem control. Use a fresh output directory exactly as shown.

```bash
./ape/bin/python -m src.datasets.pr_review_v4.prebuild \
  --config configs/pr_review_v4_pilot.yaml \
  --out data/pr_review_v4/dev-pilot-0.9.0-stable-smoke3-base-commits.jsonl \
  dataset.work_unit_ids='["wu:4c8e8d9471d9110b64a05169","wu:b017b7314c4bea62d8f968c3","wu:20910b2d076223021ce8926e"]'

export PATH=/research/projects/proofedit/ya475/.elan/bin:$PATH
./ape/bin/python -m ape.toolkits.execute.lean.build \
  --input_file data/pr_review_v4/dev-pilot-0.9.0-stable-smoke3-base-commits.jsonl \
  --num_processes 2

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.work_unit_ids='["wu:4c8e8d9471d9110b64a05169","wu:b017b7314c4bea62d8f968c3","wu:20910b2d076223021ce8926e"]' \
  dataset.run_name=pr_review_v4_090_stable_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses.jsonl \
  dataset.dry_run=true

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.work_unit_ids='["wu:4c8e8d9471d9110b64a05169","wu:b017b7314c4bea62d8f968c3","wu:20910b2d076223021ce8926e"]' \
  dataset.run_name=pr_review_v4_090_stable_smoke3 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses.jsonl \
  dataset.dry_run=false
```

After candidate generation completes, run the deterministic post-processing path:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.candidates \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/work_units.jsonl \
  --responses results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses_workspace_map.json \
  --allow-subset --deterministic-discovery \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/work_units.jsonl \
  --work-unit-ids wu:4c8e8d9471d9110b64a05169 wu:b017b7314c4bea62d8f968c3 wu:20910b2d076223021ce8926e \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/semantic-judge-v1

./ape/bin/python -m src.datasets.pr_review_v4.evidence \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidate_responses_workspace_map.json \
  --boundaries inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/episode_boundaries.jsonl \
  --events inputs/pr_review_v4/releases/dev-pilot-0.9.0/source/events.jsonl \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evidence

./ape/bin/python -m src.datasets.pr_review_v4.select \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl \
  --packets results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evidence/assertions.jsonl \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/findings.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.evaluate \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --pilot-cases inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/pilot_cases.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl \
  --findings results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/findings.jsonl \
  --semantic-matches results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/semantic-judge-v1/matches.jsonl \
  --packets results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evidence/assertions.jsonl \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/work_units.jsonl \
  --work-unit-ids wu:4c8e8d9471d9110b64a05169 wu:b017b7314c4bea62d8f968c3 wu:20910b2d076223021ce8926e \
  --pr-numbers 33057 33098 33438 \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evaluation.json

./ape/bin/python -m src.datasets.pr_review_v4.run_contract seal \
  --run-dir results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3
```

Return after all commands finish. The gate is: `run_manifest.json` reports `complete`, all evidence
packets are terminal, semantic denominators cover exactly six obligations across the three executed
units, the known compiler-sensitive case is recovered, and the control has no unsupported finding.
