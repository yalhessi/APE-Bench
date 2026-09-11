---
paths:
  - "src/datasets/pull_requests/**"
  - "src/datasets/pr_review_v2/**"
  - "src/mathlib_review/retrieval/**"
  - "src/mathlib_review/conventions/**"
  - "tests/datasets/test_pull_requests_*"
---
# PR data: one store, many projections

- `src/datasets/pull_requests/definitions.py` is the ONLY home for is_bot / is_reviewer / substance /
  Lean predicates. Never write a new reviewer test; call `classify_commenter`. GitHub's
  `author_association` alone loses most review (maintainers show as CONTRIBUTOR, PR authors pass):
  measured 33% recall / 62% precision against spec §3.1 on the 201 cached bundles.
- The store (`data/pull_requests/pr/<n>/`, gitignored) is immutable and neutral: a null may be filled
  once, a value never changes; exclusion happens in projections. Index and projections pin the store
  content digest; the precedent index refuses a corpus-sha mismatch. Provenance is tracked under
  `inputs/pull_requests/`. Never name the store after one use (it was `pull_reviews` for a day).
- **Never write under `data/pr_review_v2/`**: eleven frozen manifests hash `bundles/` and `compares/`
  as trees. The store, the v2 fetcher and the roster writer all refuse; keep it that way.
- **`src/datasets/pr_review_v2` cannot be deleted.** Nine frozen release manifests pin
  `pr_review_v2/data/mathlib_roster.txt` by path and hash. A test pins this and asks to be *deleted*,
  not relaxed, if the manifests ever stop referencing the file. The old corpus collector refuses to
  run; its 43,881-row corpus is the frozen acceptance baseline.
- GitHub's `/pulls/comments` listing returns HTTP 500 for mathlib4 and the search API has its own
  30 req/min bucket. Collection is per-PR on the core quota, tiered and resumable.
- After the full collection passes acceptance: repoint `paths.PRECEDENT_CORPUS` to
  `data/pull_requests/projections/corpus/reviewer_view.jsonl`, rebuild the precedent index, rerun
  `conventions.review_join --write`, re-measure. Until then the index is built from the old
  33%-recall corpus, and every corpus-derived level understates by roughly 2.5×.
- GitHub ends a review comment's `diff_hunk` at the commented line, so the situated declaration is
  the one enclosing the hunk's *tail*. Facets are conditioning metadata, never the join key (a
  facet-keyed join fit 4–8% of requests); the enforced component is the A→B ledger from
  ```suggestion blocks.
