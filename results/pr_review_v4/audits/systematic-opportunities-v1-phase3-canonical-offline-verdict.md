# PR Review v4 Phase 3 canonical API offline verdict

## Verdict

Pass the offline source-retrieval gate. Proceed to the two-call real smoke, but do not mark Phase 3
complete or claim a judgment gain until the three-repetition gate passes.

The production operator recovered `Metric.isSeparated_insert_of_notMem` without oracle text. It is
rank 1 of 382 declarations in the positive target's base-snapshot dependency neighborhood, with
score 28 and `already_used=false`. The arctan control ranks `Real.arctan_tan` first of 125
declarations, with score 19 and `already_used=true`; no replacement is proposed.

## Implemented boundary

- immutable declaration records with base snapshot, source path, line, signature, type-shape tokens,
  and lexical dependencies;
- target-module plus direct-import indexing at the PR's review-time base SHA;
- local-reconstruction-focused retrieval with a complete top-20 trace;
- already-used API suppression and a high-confidence insert/separation template;
- source-derived replacement text and explicit applicability status;
- production opportunity evidence, operator runs, terminal investigation records, and runner support;
- a one-target intervention and one-target negative-control adjudication release.

Generated artifacts contain 507 declaration records, 40 retrieval hits, eight evidence artifacts,
two investigation records, and two adjudication hypotheses. Generation succeeds while access to any
path containing `gold` is denied by a regression test.

## Remaining gate

The local Codex environment has no `lake` executable, so the proposed replacement is labeled
`unavailable`, not compiled. Each real adjudication must use `lean_verify`. Phase 3 passes only if:

1. at least two of three repetitions request the correct canonical replacement on PR 33098;
2. the request identifies `Metric.isSeparated_insert_of_notMem` and verifies an applicable edit;
3. all three control adjudications emit no request;
4. semantic issue and resolution outcomes are reported separately.

## Commands to run

First confirm the frozen release and dry-run wiring:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase3_canonical_smoke

./ape/bin/python -m src.datasets.pr_review_v4.runner \
  --config configs/pr_review_v4_canonical_smoke.yaml \
  dataset.dry_run=true \
  dataset.run_name=pr_review_v4_canonical_smoke_dryrun \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.9.1-canonical-smoke-dryrun/candidate_responses.jsonl
```

Then run three independent two-call repetitions:

```bash
test -n "${OPENAI_API_KEY:-}" || { echo "OPENAI_API_KEY is not set"; exit 1; }

for rep in 1 2 3; do
  ./ape/bin/python -m src.datasets.pr_review_v4.runner \
    --config configs/pr_review_v4_canonical_smoke.yaml \
    dataset.dry_run=false \
    dataset.run_name="pr_review_v4_canonical_smoke_rep${rep}" \
    dataset.output_file="results/pr_review_v4/runs/dev-pilot-0.9.1-canonical-smoke-rep${rep}/candidate_responses.jsonl"
done
```

Return after all three finish. Candidate ingestion and frozen semantic judging should be applied to
each repetition independently before the 2/3 gate is evaluated.

## Verification

```bash
./ape/bin/python -m pytest \
  tests/datasets/test_pr_review_v4_canonical_api.py \
  tests/datasets/test_pr_review_v4_systematic_opportunities.py -q

./ape/bin/python -m pytest tests/datasets -q
```
