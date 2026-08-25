# Phase 8 residual open-review smoke plan

## Purpose

Run one residual novelty pass on PR 33098 and the matched control PR 33438 after deterministic
synthesis. This is two model calls total. The prompt exposes all changed targets and already covered
method outcomes, while excluding gold comments and outcomes.

## Run

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.release=inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.0 \
  dataset.dry_run=false \
  dataset.run_name=pr_review_v4_phase8_residual_smoke_rep1 \
  dataset.output_file=results/pr_review_v4/runs/phase8-residual-smoke-rep1/candidate_responses.jsonl
```

## Ingest

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase8_residual \
  --release inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.0 \
  --responses results/pr_review_v4/runs/phase8-residual-smoke-rep1/candidate_responses.jsonl \
  --out results/pr_review_v4/runs/phase8-residual-smoke-rep1/ingested
```

## Initial gate

- Exactly one successful terminal response exists for each PR.
- Both `residual-review-pass1` records become terminal, including abstentions.
- PR 33438 publishes no repeated or novel candidate unless it has independently verifiable evidence.
- PR 33098 does not repeat the accepted canonical, naming, or wrapper findings.
- Any novel candidate names a real inventory target and proceeds through the ordinary evidence and
  semantic gates before synthesis.

Stop after ingestion and inspect the candidates before paying for semantic judging.
