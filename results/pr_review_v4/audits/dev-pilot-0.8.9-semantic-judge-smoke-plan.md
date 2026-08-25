# PR Review v4 semantic judge one-pair smoke plan

## Purpose

Validate the v7.1 rubric port on the exact PR 33098 near miss already judged manually. This invokes
one `gpt_5_mini` pair, not another reviewer run.

## Real-run command

```bash
./ape/bin/python -m src.datasets.pr_review_v4.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.8.9/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.8.9/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/candidates.jsonl \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.8.9/derived/work_units.jsonl \
  --work-unit-ids wu:45201a19e9bc4d6a23013291 wu:b5d86477bfa706af0077b107 wu:4ba70bd37a066bfd7486d2cf \
  --model gpt_5_mini --concurrency 1 \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.8.9-discovery-battery-smoke3/semantic-judge-v1
```

## Expected pair

- Candidate: remove the unused `h_nonempty` binder/case split in
  `Metric.coveringNumber_two_mul_le_externalCoveringNumber`.
- Gold: replace the empty branch binder `h_empty` with `rfl`, then discharge it with `simp`.

## Acceptance gates

1. Exactly one candidate-obligation pair is judged across three scoped atomic obligations.
2. `issue_match=false` and `resolution_match=false` with a reason identifying the different branch
   or transformation, not merely different wording.
3. Reported location recall is `1/3`; issue and resolution recall are both `0/3`.
4. `audit.jsonl` contains the full pair with empty human-verdict fields for manual confirmation.
5. Re-running the command reports zero uncached pairs and regenerates byte-identical artifacts.

A lenient issue acceptance fails the port and requires prompt revision plus another one-pair run.
After this passes, the next generation release may add generic maintainer-ask exemplars while this
judge, deterministic discovery, grounding, and publication remain frozen.
