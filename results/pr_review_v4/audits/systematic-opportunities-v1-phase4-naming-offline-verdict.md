# PR Review v4 Phase 4 naming contrast offline verdict

## Verdict

Pass the Phase 4 offline gate. Proceed to the two-call repeated real smoke, but do not mark Phase 4
complete until the 2/3 positive and 0/3 control gate passes.

## Offline results

| Check | Result |
| --- | ---: |
| Review-base files parsed | 7,409 |
| Parse failures | 0 |
| Direct `Set.encard` subject population | 91 |
| `encard_` leaf prefix | 87 |
| Meaningful `encard` elsewhere | 4 |
| Conflicting `card_` prefix | 0 |
| Unrelated leaf names | 0 |
| Proposed target name collision | false |

The positive target is `Metric.card_maximalSeparatedSet`. Its outer conclusion left side is
`(maximalSeparatedSet ε A).encard`, so the subject classifier assigns `Set.encard`, `direct_lhs`, and
high confidence. The collision-free proposal is `Metric.encard_maximalSeparatedSet`.

The control is `Metric.exists_set_encard_eq_packingNumber`. Its conclusion is existential, its name
already includes `encard`, and the operator records `role_conditioned` with no proposed rename. This
tests whether the method respects declaration roles rather than mechanically requiring every
`encard` theorem to begin with `encard_`.

Every counted declaration is frozen in `derived/naming_population.jsonl`. Prompt evidence includes
the population definition, exact counts, representative support, all four exceptions, and exact
collision results. Generation reads no gold, comments, outcomes, or future code.

## Evaluation correction

`card_maximalSeparatedSet` has both naming and proof-compression obligations on the same change ID.
The semantic judge now supports `--obligation-ids`, preventing the naming smoke from being penalized
for not also requesting proof compression. The frozen naming obligation is:

`obligation:45433fc367bdd15dc606eaabeadaa16ad98077afec83ca662fe39bcf938632ad`

## Real gate

Phase 4 passes if at least two of three repetitions request the exact `encard_` rename, the frozen
judge issue- and resolution-matches those requests, and all three role-conditioned controls emit no
candidate.

## Commands to run

```bash
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is not set"; exit 1; }

for rep in 1 2 3; do
  run="results/pr_review_v4/runs/dev-pilot-0.9.2-naming-smoke-rep${rep}"

  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_naming_smoke.yaml \
    dataset.dry_run=false \
    dataset.run_name="pr_review_v4_naming_smoke_rep${rep}" \
    dataset.output_file="${run}/candidate_responses.jsonl"

  ./ape/bin/python -m src.datasets.pr_review_v4.candidates \
    --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.2-naming-smoke/derived/work_units.jsonl \
    --responses "${run}/candidate_responses.jsonl" \
    --out "${run}/candidates.jsonl"

  ./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
    --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
    --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
    --candidates "${run}/candidates.jsonl" \
    --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.2-naming-smoke/derived/work_units.jsonl \
    --work-unit-ids \
      wu:naming-smoke:f92805bdf8cc092588cd \
      wu:naming-smoke:37a48404f86da71520a5 \
    --obligation-ids \
      obligation:45433fc367bdd15dc606eaabeadaa16ad98077afec83ca662fe39bcf938632ad \
    --model gpt_5_mini \
    --concurrency 1 \
    --out-dir "${run}/semantic-judge-v1"
done
```

Return after the loop completes. API-backed commands are intentionally left for manual execution.

## Verification

```bash
./ape/bin/python -m pytest tests/datasets -q
```
