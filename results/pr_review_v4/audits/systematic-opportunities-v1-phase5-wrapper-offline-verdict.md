# PR Review v4 Phase 5 wrapper composition offline verdict

## Verdict

Pass the Phase 5 offline gate. Proceed to the two-call repeated real smoke, but do not mark Phase 5
complete until the 2/3 positive issue-match and 0/3 control gate passes.

## Offline results

| Gate | Result |
| --- | --- |
| Positive composition source retrieval | pass |
| Repository wrapper | `Metric.IsCover.coveringNumber_le_encard` |
| Current-PR source roles | cardinality, cover, and subset witnesses |
| Cross-work-unit related IDs preserved | 3/3 |
| Dependencies removed | `iInf_le`, `iInf_pos`, `le_of_eq`, `.trans` |
| Parallel-proof control | `no_composition` |
| Local Lean compilation | unavailable |
| Focused regression tests | 7/7 pass |

The positive target is `Metric.coveringNumber_le_packingNumber`. Deterministic PR-relation traversal
finds `Metric.card_maximalSeparatedSet`, `Metric.isCover_maximalSeparatedSet`, and
`Metric.maximalSeparatedSet_subset`; review-base dependency indexing finds
`Metric.IsCover.coveringNumber_le_encard`. The operator constructs their concrete composition and
records the old, new, and removed dependency sets.

The control is `Real.arctan_inv_sqrt_three`. It has the adjacent parallel sibling
`Real.arctan_sqrt_three`, but no compatible repository wrapper and changed-sibling chain. It receives
an explicit `no_composition` plan and no proposed transformation.

The frozen workspace has no usable `lake`, so compilation is recorded as `unavailable`. This is a
separate gate: the real adjudicator must call `lean_verify` before requesting the positive edit.

## Semantic scope

Evaluate only:

`obligation:a58d0d5ea6ca1dcb635a19a06e272cb7e73adefa96272448dca2e373aeb72a4b`

The obligation's adopted resolution combines wrapper composition with the independently discovered
`encard_maximalSeparatedSet` rename and `by_cases!`. Phase 5 passes on stable issue recognition of the
wrapper opportunity; exact resolution recall and compilation must be reported separately and cannot
retroactively redefine source-retrieval success.

## Real gate

Run three independent repetitions. Pass only if at least two positives issue-match the scoped
obligation, every requested composition is Lean-verified, and all three controls emit no candidate.
Report exact resolution recall even though it is not the Phase 5 source-recovery gate.

## Commands to run

Confirm the frozen release, focused tests, and dry-run wiring locally:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase5_wrapper_smoke

./ape/bin/python -m pytest -q \
  tests/datasets/test_pr_review_v4_wrapper_composition.py

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_wrapper_smoke.yaml \
  dataset.dry_run=true
```

Run generation, ingestion, and exact-obligation judging for all three repetitions:

```bash
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is not set"; exit 1; }

for rep in 1 2 3; do
  run="results/pr_review_v4/runs/dev-pilot-0.9.3-wrapper-smoke-rep${rep}"

  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_wrapper_smoke.yaml \
    dataset.dry_run=false \
    dataset.run_name="pr_review_v4_wrapper_smoke_rep${rep}" \
    dataset.output_file="${run}/candidate_responses.jsonl"

  ./ape/bin/python -m src.datasets.pr_review_v4.candidates \
    --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.3-wrapper-smoke/derived/work_units.jsonl \
    --responses "${run}/candidate_responses.jsonl" \
    --out "${run}/candidates.jsonl"

  ./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
    --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
    --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
    --candidates "${run}/candidates.jsonl" \
    --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.3-wrapper-smoke/derived/work_units.jsonl \
    --work-unit-ids \
      wu:wrapper-smoke:1b3f1a9d8824f00092fa \
      wu:wrapper-smoke:30bb4f6c5a4cd78ef84c \
    --obligation-ids \
      obligation:a58d0d5ea6ca1dcb635a19a06e272cb7e73adefa96272448dca2e373aeb72a4b \
    --model gpt_5_mini \
    --concurrency 1 \
    --out-dir "${run}/semantic-judge-v1"
done
```

Return after the loop completes. API-backed commands are intentionally left for manual execution.
