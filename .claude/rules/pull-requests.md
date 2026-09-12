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
- **A heavy endpoint can 502 permanently, and retrying is not the answer.** `/pulls/4197/comments`
  is 1.2 MB; GitHub times out generating it and fails identically through 62 s and 242 s of backoff.
  The collector defers such an endpoint -- unrecorded, never written empty, refetched by the next
  run -- and the retry budget stays at five attempts, because a longer one is paid per dead endpoint
  across 32k PRs and buys nothing. Do not raise it again; `test_the_5xx_budget_stays_short_because_
  deferring_is_the_defence` pins this.
- **Scope a collection run with `--created-from/--created-to`, never a narrower `--start/--end`.**
  The window string keys the tier-0 cache, so a new one re-walks the listing -- and a second walk
  over an overlapping window meets rows whose `updated_at` has moved, which the store refuses. The
  walk now keeps the recorded row, but the re-walk is still hundreds of wasted pages. Slicing reads
  the cached list and spends nothing.
- **Tier 1 feeds the corpus; tier 2 feeds episodes.** `project_corpus` gates only on
  `review_comments` -- no tier-2 endpoint anywhere -- so the precedent/conventions thread needs
  only tier 1. `project_episodes` goes through `load_bundle`, which requires tier 2 (diff at the
  reviewed head, base commit, commit timestamps for the cutoff, `body_edits` for leak-safety).
  Measured 2026-09-12 on the finished tier 1: 107,187 reviewer_view rows from 14,981 PRs, against
  the 43,881-row frozen baseline -- the ~2.5x the corpus repoint was predicted to gain.
- **A deferred PR may stay dropped, so quote the collected count, not the window count.** Dropped
  PRs sit at tier 0 and are counted in the tracked manifest's `prs_by_complete_tier` -- as of
  2026-09-12, 32,851 in the window, 32,805 at tier 1. That gap is the denominator correction; it is
  recorded, not silent, and `pre_gate` reports each as `tier1_incomplete` rather than as a PR with
  no comments.
- After the full collection passes acceptance: repoint `paths.PRECEDENT_CORPUS` to
  `data/pull_requests/projections/corpus/reviewer_view.jsonl`, rebuild the precedent index, rerun
  `conventions.review_join --write --end <date>`, re-measure. Until then the index is built from the
  old 33%-recall corpus, and every corpus-derived level understates by roughly 2.5×.
- **The corpus's end date is no longer a date gate, so state the window.** It stopped at 2025-08-31,
  before every eval PR, so the analysis readers were leak-safe whether or not they gated; collection
  now runs to 2026-08-31. `precedent_bench.load_corpus` and `review_join.load_*` therefore take a
  **required** `end` and `review_join --write` a required `--end`, recorded in `report.json`'s
  `window`. A join that feeds a *brief* must be gated at `commit_date(base_sha)`; `--end all` is only
  for descriptive month statistics. The live retrieval path is separately safe -- `precedent_index`
  goes through `RetrievalGate`, where an undated row is `UNDATED = -1` and never eligible.
- GitHub ends a review comment's `diff_hunk` at the commented line, so the situated declaration is
  the one enclosing the hunk's *tail*. Facets are conditioning metadata, never the join key (a
  facet-keyed join fit 4–8% of requests); the enforced component is the A→B ledger from
  ```suggestion blocks.
