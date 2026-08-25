# PR Review v4 oracle opportunity adjudication verdict

## Verdict

Pass as a mechanism diagnostic and control-discipline test. Fail as an end-to-end replacement for
candidate discovery. Do not interpret the run as an oracle upper bound on norm discovery: the
opportunities named useful alternatives, but most packets did not establish that the alternative
compiled or that maintainers historically preferred it.

The run completed both calls, adjudicated all 12 opportunities, emitted one intervention candidate,
and emitted no control candidate. The frozen semantic judge confirmed the candidate as both an issue
and resolution match for the `isCover_maximalSeparatedSet` canonical-API obligation.

## Results

| Arm | Opportunities | Requests | No request |
| --- | ---: | ---: | ---: |
| Gold-targeted PR 33098 | 6 | 1 | 5 |
| Matched control PR 33438 | 6 | 0 | 6 |

The intervention adjudications classified four alternatives as valid and two as uncertain. Their
norm strengths were one canonical, three common, and two preference. Only the canonical API case
crossed the request threshold.

## Interpretation

The positive result is targeted and important: supplying the exact
`Metric.isSeparated_insert_of_notMem` API recovered one of the two obligations never recovered by
the three stable baseline repetitions. Combined with the baseline union, this mechanism would cover
five of six smoke obligations in at least one run. It does not yet make single-run judgment reliable.

The five rejections expose different missing evidence:

- the two `grind` opportunities lacked compiling replacement artifacts and adopted historical
  preference evidence;
- the `encard_` rename was recognized as valid and advisory, but rejected using unsupported
  counterevidence that `card_` is widely used;
- the covering-number composition was recognized as valid, but the packet did not quantify the
  abstraction or dependency advantage of the wrapper API;
- the `rfl` case pattern was recognized as common but treated as an optional preference.

The trace confirms that the agent searched for the cardinality name and inspected the source, but it
did not compile the proposed replacements. Dynamic tool observations also cannot currently be cited
as opportunity evidence IDs. The experiment therefore tests routed hypotheses plus sparse evidence,
not fully adjudicated oracle norm packets.

## Decision

Retain the inventory/PR-graph/opportunity/adjudication decomposition. Implement canonical API search
as the first discovery operator. Do not build the full repository-wide norm index yet.

Next, run an evidence-sufficiency ladder over the five rejected intervention opportunities while
keeping the six controls and adjudication prompt frozen:

1. add compiling replacement artifacts and objective proof-compression comparisons;
2. add snapshot-scoped prevalence and counterexample statistics for naming and syntax patterns;
3. add temporally prior trigger/request/adopted-resolution triples for preference evidence;
4. require every dynamic tool-derived claim to become a cited evidence artifact;
5. measure source retrieval separately from application and final selection.

This determines whether the remaining wall is missing evidence, norm application, or genuinely
underdetermined maintainer preference.

Generator cost: $0.35983675 total ($0.30955925 intervention, $0.05027750 control).

## Commands to run

The frozen semantic judge command, retained for reproducibility, is:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/oracle-opportunity-probe-0.1.0-manual/candidates.jsonl \
  --work-units inputs/pr_review_v4/treatments/oracle-opportunity-probe-0.1.0/derived/work_units.jsonl \
  --work-unit-ids \
    wu:oracle-opportunity:880ddc477e24b3fa19ef \
    wu:oracle-opportunity:e0f4619cc95bec34ac77 \
  --model gpt_5_mini \
  --concurrency 1 \
  --out-dir results/pr_review_v4/runs/oracle-opportunity-probe-0.1.0-manual/semantic-judge-v1
```

No additional candidate-generation run is recommended until the evidence ladder is built.
