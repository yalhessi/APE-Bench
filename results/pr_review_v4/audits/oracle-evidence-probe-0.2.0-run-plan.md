# PR Review v4 oracle evidence-sufficiency probe 0.2.0

## Purpose

Test whether materially stronger evidence changes adjudication for the five opportunities rejected by
the first oracle-opportunity run before implementing repository-wide norm discovery.

The intervention packets add either a coherent compiling replacement or quantitative review-time
repository statistics. The matched control packets add equally explicit evidence for alternatives
that compile but remove no semantic step, or evidence that the current code already follows its local
pattern. The adjudication system prompt is unchanged from 0.1.0.

This is diagnostic-only. Development outcomes were used to instantiate oracle replacement edits, but
no maintainer comment, adoption label, or post-review provenance is rendered to the model.

## Pre-registered interpretation

| Result | Decision |
| --- | --- |
| At least 3/5 intervention requests and 0/5 control requests | Evidence sufficiency passes; implement the discovery methods that produced accepted packets |
| Proof requests move only after compiling alternatives | Prioritize proof search and compile-backed comparison |
| Naming or `rfl` remains rejected despite quantitative evidence | Historical preference/selection evidence is the missing input |
| Wrapper-API composition remains rejected despite a compiling abstraction-preserving edit | Norm application or review-worthiness calibration is the bottleneck |
| Any control request | The adjudicator overweights explicit evidence; revise calibration before retrieval work |
| 0-1/5 intervention requests with clean control | Do not build broad norm retrieval; repository evidence alone has a low application ceiling |

One run is exploratory. Replicate only if it crosses the success gate.

## Commands to run

```bash
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is not set"; exit 1; }

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_oracle_evidence.yaml \
  dataset.dry_run=false
```

After completion:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.oracle_opportunities ingest \
  --release inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0 \
  --responses results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/candidate_responses.jsonl \
  --out-dir results/pr_review_v4/runs/oracle-evidence-probe-0.2.0
```

Return after these two commands finish. Semantic judging should be run only for emitted candidates.
