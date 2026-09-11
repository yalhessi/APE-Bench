"""One raw store of Mathlib pull requests, and the projections every dataset is derived from.

Three pipelines used to collect PRs from GitHub, and they disagreed about what a review comment
is. The retrieval corpus kept comments by `author_association` alone, so it dropped every roster
reviewer GitHub reports as CONTRIBUTOR (GitHub only reports MEMBER for *public* org membership)
and kept PR authors replying on their own PRs. Measured on the 201 cached bundles against
`docs/research/review-task-spec.md` §3.1: recall 71/215, precision 71/115. The reviewer whose
comments generated PR 33098's gold was never in the corpus.

So this package separates two things that were fused:

* **Collection** writes what GitHub returned, verbatim, one directory per PR, and interprets
  nothing. There is no `keep_comment` at write time; that filter was the bug.
* **Projection** turns the store into each consumer's dataset -- corpus rows for retrieval,
  episodes for review tasks, the A→B ledger for convention discovery -- through the single
  definitions module, so a rule like "who is a reviewer" exists in exactly one place.

Layout and durability follow the Zulip store: payloads under gitignored `data/pull_reviews/`,
provenance (manifest, per-PR endpoint hashes, collection report) tracked under
`inputs/pull_reviews/`, so a wiped store is a resumable refetch of a known list rather than a
rediscovery.

Two caches this package must never write: `data/pr_review_v2/cache/{bundles,compares}`. Eleven
and eight frozen release manifests hash those directories as trees, so one added file breaks them.
The seeder reads them; nothing here writes there.
"""
