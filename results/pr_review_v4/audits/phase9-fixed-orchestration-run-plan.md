# Phase 9 fixed-orchestration real smoke plan

## Scope

- Three fixed-pipeline repetitions, two model calls each.
- Three holistic extension repetitions, one model call each.
- Existing holistic samples supply the other matched PR 33098 unit and PR 33438 control.
- Semantic evaluation uses eight matched-scope obligations; miss attribution retains all 14 eligible
  PR 33098 obligations.

## 1. Run model calls

```bash
for rep in 1 2 3; do
  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_pilot.yaml \
    dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.9.4-fixed-smoke \
    dataset.dry_run=false \
    dataset.run_name=pr_review_v4_phase9_fixed_smoke_rep${rep} \
    dataset.output_file=results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/candidate_responses.jsonl

  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_pilot.yaml \
    dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.9.0 \
    dataset.dry_run=false \
    'dataset.work_unit_ids=["wu:9354e29b0912d17d60b1d3e1"]' \
    dataset.run_name=pr_review_v4_phase9_holistic_extension_rep${rep} \
    dataset.output_file=results/pr_review_v4/runs/phase9-holistic-extension-rep${rep}/candidate_responses.jsonl
done
```

Stop and inspect execution before semantic judging.

## 2. Ingest and construct baseline unions

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration scope \
  --out results/pr_review_v4/audits/phase9-fixed-smoke-evaluation-scope.json

PRIMARY=(
  results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3
  results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2
  results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3
)

for i in 0 1 2; do
  rep=$((i + 1))
  ./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration ingest \
    --responses results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/candidate_responses.jsonl \
    --out results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/ingested

  ./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration baseline-union \
    --primary-responses "${PRIMARY[$i]}/candidate_responses.jsonl" \
    --extension-responses results/pr_review_v4/runs/phase9-holistic-extension-rep${rep}/candidate_responses.jsonl \
    --out results/pr_review_v4/runs/phase9-baseline-union-rep${rep}

  ./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration scope \
    --out results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/semantic-judge-v1/evaluation_scope.json

  ./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration scope \
    --out results/pr_review_v4/runs/phase9-baseline-union-rep${rep}/semantic-judge-v1/evaluation_scope.json
done
```

## 3. Run frozen semantic judge

```bash
mapfile -t OBLIGATIONS < <(
  jq -r '.obligation_ids[]' results/pr_review_v4/audits/phase9-fixed-smoke-evaluation-scope.json
)

for rep in 1 2 3; do
  ./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
    --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
    --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
    --candidates results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/ingested/candidates.jsonl \
    --out-dir results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/semantic-judge-v1 \
    --model gpt_5_mini \
    --obligation-ids "${OBLIGATIONS[@]}"

  ./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
    --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
    --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
    --candidates results/pr_review_v4/runs/phase9-baseline-union-rep${rep}/candidates.jsonl \
    --out-dir results/pr_review_v4/runs/phase9-baseline-union-rep${rep}/semantic-judge-v1 \
    --model gpt_5_mini \
    --obligation-ids "${OBLIGATIONS[@]}"
done
```

## 4. Finalize and aggregate

```bash
for rep in 1 2 3; do
  ./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration finalize \
    --ingested results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/ingested \
    --semantic results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/semantic-judge-v1 \
    --out results/pr_review_v4/runs/phase9-fixed-smoke-rep${rep}/final-v4
done

./ape/bin/python -m src.datasets.pr_review_v4.phase9_fixed_orchestration aggregate \
  --repetition-report results/pr_review_v4/runs/phase9-fixed-smoke-rep1/final-v4/report.json \
  --repetition-report results/pr_review_v4/runs/phase9-fixed-smoke-rep2/final-v4/report.json \
  --repetition-report results/pr_review_v4/runs/phase9-fixed-smoke-rep3/final-v4/report.json \
  --baseline-report results/pr_review_v4/runs/phase9-baseline-union-rep1/semantic-judge-v1/report.json \
  --baseline-report results/pr_review_v4/runs/phase9-baseline-union-rep2/semantic-judge-v1/report.json \
  --baseline-report results/pr_review_v4/runs/phase9-baseline-union-rep3/semantic-judge-v1/report.json \
  --out results/pr_review_v4/audits/phase9-fixed-orchestration
```
