# PR Review v4 0.8.10 synthetic exemplar smoke verdict

## Verdict

Reject generic exemplars as the next design direction. The treatment increased target-location
coverage, but it did not recover a maintainer issue. This is the failure condition precommitted in
the smoke plan: more candidates and more location overlap without increased semantic issue recall.

The automated semantic judge could not run in the Codex shell because `OPENAI_API_KEY` is unset.
Manual adjudication of both generated pairs is unambiguous and should be confirmed by the frozen
judge when credentials are available.

## Gates

| Gate | Result | Evidence |
| --- | --- | --- |
| Execution and ingestion | Pass | 3/3 model calls succeeded; all four model candidates ingested. |
| Deterministic discovery | Pass | Exactly one PR 33057 compile candidate was produced and selected as a supported blocking finding. |
| Semantic effect | Fail (manual) | Both PR 33098 location-overlapping candidates concern a different issue from the maintainer request. Expected issue recall remains 0/3. |
| Register | Mixed | No exemplar copying or defenses, but both PR 33098 outputs are wrong-aspect suggestions. |
| Control | Pass | PR 33438 produced two raw style candidates and zero selected findings. |
| Attribution | Fail treatment | Model candidates increased from 3 to 4 and location recall from 0.25 to 0.50, while semantic recall remained zero. |

## Pair audit

1. `Metric.card_maximalSeparatedSet`: the candidate asks to simplify that theorem's own proof. The
   gold request changes `coveringNumber_le_packingNumber` to use `encard_maximalSeparatedSet` and
   `IsCover.coveringNumber_le_encard`. Same change scope, different subject and transformation.
2. `Metric.isCover_maximalSeparatedSet`: the candidate asks for a clearer docstring. The gold
   request restructures the proof using `C := {x} union maximalSeparatedSet`,
   `isSeparated_insert_of_notMem`, and encard lemmas. Same target, different issue and resolution.

Both pairs should be `issue_match=false` and `resolution_match=false` under the frozen v7.1 rubric.

## Metrics

- Total candidates: 5 (4 model, 1 deterministic), versus 4 in 0.8.9.
- Supported and selected findings: 1, the unchanged deterministic PR 33057 compile failure.
- Evidence status: 1 supported, 4 inconclusive.
- Location candidate recall: 0.50, versus 0.25 in 0.8.9.
- Location selected recall: 0.00 in both releases.
- Control false-finding rate: 0.00.
- Generator cost reported by the three samples: $0.216573.

## Required judge confirmation

```bash
./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.8.10/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.8.10/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.8.10-exemplar-smoke3/candidates.jsonl \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.8.10/derived/work_units.jsonl \
  --work-unit-ids wu:24dac0bba5d216fc1ef940f3 wu:dde1bfbbaa031aa0a2fac1fb wu:5f5a5a2a755d7e82671bca36 \
  --model gpt_5_mini \
  --concurrency 1 \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.8.10-exemplar-smoke3/semantic-judge-v1
```

## Next step

Follow the precommitted sequence and test temporally valid idiom/ask retrieval as one isolated
treatment. Keep the 0.8.10 grounding, deterministic discovery, selection, and semantic judge frozen;
do not retain the generic exemplar block in that treatment.
