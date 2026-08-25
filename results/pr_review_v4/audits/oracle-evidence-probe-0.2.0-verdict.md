# PR Review v4 oracle evidence-sufficiency probe 0.2.0 verdict

## Verdict

Partial pass. The run misses the pre-registered aggregate success threshold of at least three of five
intervention requests, so it does not justify implementing broad norm discovery. It passes two
method-specific mechanism tests: compile-backed wrapper-API comparison and quantitative naming
evidence both changed a prior `no_request` into a precise request, while all five matched controls
remained `no_request`.

Frozen semantic judging confirms both candidates as issue matches. The naming candidate is also a
resolution match; the wrapper-composition candidate is not, because it omits the maintainer's exact
`by_cases!` pattern and complete requested refactor. Aggregate issue recall is `2/6`, resolution
recall is `1/6`, and paired-candidate issue precision is `1.0`.

## Results

| Arm | Opportunities | Requests | No request |
| --- | ---: | ---: | ---: |
| Gold-targeted PR 33098 | 5 | 2 | 3 |
| Matched control PR 33438 | 5 | 0 | 5 |

Accepted intervention opportunities:

1. Replace direct `iInf` reasoning in `coveringNumber_le_packingNumber` with the existing
   `IsCover.coveringNumber_le_encard` abstraction and new maximal-set API.
2. Rename `card_maximalSeparatedSet` to `encard_maximalSeparatedSet` based on quantified declaration
   naming evidence.

Rejected intervention opportunities:

1. `grind` for `maximalSeparatedSet_subset` remained an optional preference despite a compiling
   one-line replacement.
2. `grind` for the maximal-set cardinality proof remained an optional preference despite compiling.
3. Replacing the named empty equality with `rfl` remained too minor despite compiling and being the
   majority repository pattern.

## Interpretation

The first oracle run showed that a concrete canonical API can recover the
`isCover_maximalSeparatedSet` obligation. This follow-up shows that evidence quality matters for two
additional classes:

- objective abstraction-boundary evidence can make an API-composition request actionable;
- scoped prevalence with meaningful counterexamples can make a naming convention actionable.

The semantic split sharpens this conclusion: wrapper evidence recovered the right problem and broad
API direction, but not the complete human resolution. The production operator must therefore measure
transformation construction separately from source retrieval and issue discovery.

Compilation alone does not make proof golf or small syntax preferences review-worthy. Recovering
those maintainer requests requires historical preference/selection evidence, not a larger code
index. Their continued rejection should not block implementation of the two methods that passed.

Across the two oracle diagnostics, the system recovered both obligations that were never hit in the
three stable baseline repetitions: `isCover_maximalSeparatedSet` and
`coveringNumber_le_packingNumber`. The retrospective union with the baseline repetitions reaches all
six smoke obligations, but this is not a single-run or production result.

## Decision

Do not implement a monolithic repository norm index. Implement a narrow next slice:

1. typed canonical/wrapper API retrieval using declaration types and dependency neighborhoods;
2. compile-backed comparative edits that record removed implementation dependencies;
3. scoped naming statistics conditioned on semantic subject such as `Set.encard`, with explicit
   counterexamples;
4. inventory routing and opportunity records for those two methods;
5. defer `grind` and `rfl` preference recovery to a separate historical adopted-transformation
   experiment.

After that narrow implementation, run three repetitions on the same intervention/control pair before
expanding beyond the smoke. Treat naming as a demonstrated issue-and-resolution diagnostic and wrapper
composition as a demonstrated issue-only diagnostic until the exact transformation is recovered.

Generator cost: $0.156828 total ($0.10914925 intervention, $0.04767875 control).

## Commands to run

```bash
./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/candidates.jsonl \
  --work-units inputs/pr_review_v4/treatments/oracle-evidence-probe-0.2.0/derived/work_units.jsonl \
  --work-unit-ids \
    wu:oracle-evidence:8df666b9fb141d606cb0 \
    wu:oracle-evidence:31e8ae1ffd989229d385 \
  --model gpt_5_mini \
  --concurrency 1 \
  --out-dir results/pr_review_v4/runs/oracle-evidence-probe-0.2.0/semantic-judge-v1
```

Return after semantic judging completes. No further candidate-generation run is needed for this
experiment.
