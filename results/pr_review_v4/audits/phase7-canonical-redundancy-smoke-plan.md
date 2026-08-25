# Phase 7 canonical redundancy smoke plan

## Purpose

Exercise the live Phase 7 boundary with two independent adjudications of the same low-confidence
canonical opportunity. Terminal submission recompiles a concrete requested edit and persists the
successful check as an `adjudication-verification-artifact1`. Ingestion requires both votes and
defers on disagreement.

This smoke is two model calls total. It excludes the deterministic control because the offline replay
already establishes its `no_request` disposition.

## Run

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:canonical-smoke:3b0c794370968125d9be"]' \
  dataset.run_name=pr_review_v4_phase7_canonical_redundancy_rep1b \
  dataset.output_file=results/pr_review_v4/runs/phase7-canonical-redundancy-rep1b/candidate_responses.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.release=inputs/pr_review_v4/releases/dev-pilot-0.9.1-canonical-smoke \
  dataset.dry_run=false \
  'dataset.work_unit_ids=["wu:canonical-smoke:3b0c794370968125d9be"]' \
  dataset.run_name=pr_review_v4_phase7_canonical_redundancy_rep2 \
  dataset.output_file=results/pr_review_v4/runs/phase7-canonical-redundancy-rep2/candidate_responses.jsonl
```

## Ingest

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase7_adjudication \
  --gate-dir results/pr_review_v4/audits/phase7-adjudication-gate-0.1.1 \
  --responses \
    results/pr_review_v4/runs/phase7-canonical-redundancy-rep1b/candidate_responses.jsonl \
    results/pr_review_v4/runs/phase7-canonical-redundancy-rep2/candidate_responses.jsonl \
  --out results/pr_review_v4/runs/phase7-canonical-redundancy-smoke-0.1.1
```

## Gate

- Both terminal responses succeed.
- Every `valid` request includes a persisted successful Lean verification artifact.
- Exactly two votes from distinct run IDs are ingested.
- Agreement retains the shared worthiness decision; any axis disagreement yields `defer`.
- No result from this smoke changes the frozen deterministic policy artifacts.
