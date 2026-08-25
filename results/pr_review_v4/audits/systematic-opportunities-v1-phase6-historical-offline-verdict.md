# PR Review v4 Phase 6 historical transformation offline verdict

## Verdict

The Phase 6 implementation passes its integrity tests but fails the pre-registered source-coverage
gate. Do not run the paid technical-only versus historical-evidence smoke. The current corpus cannot
test the intended causal hypothesis without using target-PR or post-cutoff information.

## Implemented

- separately hashed historical trigger, maintainer request, observed resolution, and join records;
- review-time code, declaration, snapshot, reviewer, timestamp, outcome confidence, transformation
  features, and explicit partial/dropped/unknown exceptions;
- method-specific proof-compression and structural-rewrite trigger retrieval;
- hard exclusion of the target PR, missing timestamps, and events at or after the target cutoff;
- retained adopted, partially adopted, dropped, and unknown records as precedents or anti-precedents;
- gold-free target queries and hidden-feature source-recall evaluation;
- a complete raw-event audit in addition to the curated intervention store.

## Corpus

| Record class | Count |
| --- | ---: |
| Historical transformations | 113 |
| Code-grounded triggers | 99 |
| Adopted outcomes | 52 |
| Partially adopted outcomes | 16 |
| Dropped outcomes | 32 |
| Unknown outcomes | 13 |
| Proof-compression records | 9 |
| Structural-rewrite records | 4 |
| Raw events audited | 8,161 |

## Offline gate

The pre-registered gate requires at least one useful adopted source in each method family and useful
source recall@5 on at least two of the three smoke queries.

| Family | Queries | Useful hit@5 | Recall@5 |
| --- | ---: | ---: | ---: |
| Proof compression | 2 | 0 | 0.0 |
| Structural rewrite | 1 | 0 | 0.0 |

For both `grind` queries, the only eligible feature-bearing curated source is `pr33111_i02`. It is
partially adopted and concerns replacing an already-`grind` proof with a new helper lemma; it is not
an adopted precedent for changing an explicit conditional proof to `grind`. The other `grind`
sources are the target PR itself or occur after the cutoff and are not adopted.

For the `rfl` query, the only matching adoption is `pr33098_i04`, from the target PR itself. It is
correctly excluded. No pre-cutoff external review comment in the complete event ledger requests the
empty-branch-to-`rfl` transformation.

The raw ledger contains two eligible `grind` mentions, both in PR 33111's discussion of the same
already-`grind` proof, and zero eligible `rfl`-pattern comments. Increasing `k`, adding embeddings, or
making the prompt larger cannot recover a source that is absent.

## Decision

Pause Phase 6 before candidate generation. Do not:

- use PR 33098's own review comments as its norm evidence;
- use comments after `2025-12-23T13:41:22Z`;
- promote partial or dropped outcomes to adopted precedent;
- report technical compilation as historical preference evidence.

Resume only after expanding the corpus farther back in Mathlib history and materializing actual
adopted resolutions. Keep the current three queries and gate frozen when evaluating that expansion.

## Commands

Rebuild and inspect the offline store:

```bash
./ape/bin/python -m src.datasets.pr_review_v4.phase6_historical_store
```

Run focused and full local verification:

```bash
./ape/bin/python -m pytest -q \
  tests/datasets/test_pr_review_v4_historical_transformations.py

./ape/bin/python -m pytest tests/datasets -q
```

No API-backed command is authorized for this phase yet.
