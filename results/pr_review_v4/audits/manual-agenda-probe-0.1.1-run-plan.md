# Manual inventory-agenda probe 0.1.1 run plan

## Purpose

This is a six-call behavioral probe over the stable v4 core. It compares three specialist passes
for one intervention-bearing work unit and one theorem control against the union of three existing
holistic baseline repetitions. It does not implement or claim to test the full inventory or ledger.

The frozen passes are:

1. statement and API investigation;
2. proof implementation investigation;
3. relational and family investigation.

The intervention and control receive the same scheduling logic. Prompt hashes and expected task IDs
are sealed in `results/pr_review_v4/runs/manual-agenda-probe-0.1.1/run_plan.json`.

## Execution

Both required snapshots are already `ready`. Run the six model calls:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_agenda_probe.yaml \
  dataset.dry_run=false
```

## Postprocessing

```bash
./ape/bin/python -m src.datasets.pr_review_v4.candidates \
  --work-units inputs/pr_review_v4/treatments/manual-agenda-probe-0.1.1/derived/work_units.jsonl \
  --responses results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidate_responses.jsonl \
  --out results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates-unmerged.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.agenda_probe merge-candidates \
  --input results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates-unmerged.jsonl \
  --out results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --report results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidate_merge_report.json

./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --work-units inputs/pr_review_v4/treatments/manual-agenda-probe-0.1.1/derived/work_units.jsonl \
  --work-unit-ids \
    wu:agenda-probe:84a591e0837117115f3f \
    wu:agenda-probe:9e3b7914f12c955fce1f \
    wu:agenda-probe:582fa3d5f12a7b48f980 \
    wu:agenda-probe:8aa21383d2230a2f6ac2 \
    wu:agenda-probe:b037429b24ffa91bdc9f \
    wu:agenda-probe:21bb73baeab56cbf1829 \
  --out-dir results/pr_review_v4/runs/manual-agenda-probe-0.1.1/semantic-judge-v1

./ape/bin/python -m src.datasets.pr_review_v4.evidence \
  --candidates results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidate_responses_workspace_map.json \
  --boundaries inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/episode_boundaries.jsonl \
  --events inputs/pr_review_v4/releases/dev-pilot-0.9.0/source/events.jsonl \
  --out-dir results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evidence

./ape/bin/python -m src.datasets.pr_review_v4.select \
  --candidates results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --packets results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evidence/assertions.jsonl \
  --out results/pr_review_v4/runs/manual-agenda-probe-0.1.1/findings.jsonl

./ape/bin/python -m src.datasets.pr_review_v4.evaluate \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --pilot-cases inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/pilot_cases.jsonl \
  --candidates results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --findings results/pr_review_v4/runs/manual-agenda-probe-0.1.1/findings.jsonl \
  --semantic-matches results/pr_review_v4/runs/manual-agenda-probe-0.1.1/semantic-judge-v1/matches.jsonl \
  --packets results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evidence/assertions.jsonl \
  --work-units inputs/pr_review_v4/treatments/manual-agenda-probe-0.1.1/derived/work_units.jsonl \
  --work-unit-ids \
    wu:agenda-probe:84a591e0837117115f3f \
    wu:agenda-probe:9e3b7914f12c955fce1f \
    wu:agenda-probe:582fa3d5f12a7b48f980 \
    wu:agenda-probe:8aa21383d2230a2f6ac2 \
    wu:agenda-probe:b037429b24ffa91bdc9f \
    wu:agenda-probe:21bb73baeab56cbf1829 \
  --pr-numbers 33098 33438 \
  --out results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evaluation.json

./ape/bin/python -m src.datasets.pr_review_v4.agenda_probe compare \
  --probe-evaluation results/pr_review_v4/runs/manual-agenda-probe-0.1.1/evaluation.json \
  --probe-candidates results/pr_review_v4/runs/manual-agenda-probe-0.1.1/candidates.jsonl \
  --baseline-evaluations \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/evaluation.json \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2/evaluation.json \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3/evaluation.json \
  --baseline-candidates \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3/candidates.jsonl \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep2/candidates.jsonl \
    results/pr_review_v4/runs/dev-pilot-0.9.0-stable-smoke3-rep3/candidates.jsonl \
  --out results/pr_review_v4/runs/manual-agenda-probe-0.1.1/agenda_probe_comparison.json

./ape/bin/python -m src.datasets.pr_review_v4.run_contract seal \
  --run-dir results/pr_review_v4/runs/manual-agenda-probe-0.1.1
```

## Decision rule

- `very_strong_pass`: 5-6 of 6 issue hits.
- `strong_pass`: 4 of 6 issue hits, acceptable precision, and no selected control finding.
- `ambiguous_repeat_once`: 3 of 6 issue hits; run one more six-call bundle.
- `fail_or_revise`: 0-2 of 6 issue hits or unacceptable control behavior.

Return after all commands finish. The primary artifact for interpretation is
`agenda_probe_comparison.json`; the run is valid only if `run_manifest.json` reports `complete`.
