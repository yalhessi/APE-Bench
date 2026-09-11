# One PR store, many projections — as built

*2026-09-11. The plan this implements was approved the same day; it is summarised here with what
each step actually produced. Commits `ac27912` … on `september-checkpoint`.*

## Why

Three pipelines extracted Mathlib pull requests from GitHub and disagreed about what a review
comment is. `docs/research/review-task-spec.md` §3.1 defines a reviewer by three rules — not a bot,
**not the PR author**, and on the curated roster with `author_association` as fallback. The eval
side implemented all three; the retrieval corpus (`pr_review_v2/corpus.py: keep_comment`)
implemented neither of the last two. On the 201 cached bundles:

```
old corpus gate kept                          115 comments
  genuine reviewer comments                    71
  PR authors replying on their own PRs         44   collaborators pass the association test
roster reviewers the old gate dropped         144   YaelDillies, j-loreaux, grunweg, …
=> as a set of reviewer comments: recall 71/215 = 33 %, precision 71/115 = 62 %
```

This corrects the 40 % recall reported earlier, which compared two definitions that both omitted
the author rule. j-loreaux wrote PR 33098's gold and was never in the corpus the convention work
read. It was one of fourteen verified divergences (five copies of the association set, four bot
predicates, three `.lean` filters over three objects, five roster loaders, two funnels differing in
three gates, …) plus a live leak: four research readers loading a corpus that now reached
December 2025 with neither eval-PR exclusion nor a date window.

## What exists now

```
src/datasets/pull_reviews/
  definitions.py      the one home for what a review comment is (spec §3.1 and its neighbours)
  roster.py           the roster fetch, shared with Zulip identities; writes dated snapshots only
  github.py           GitHubClient (moved; pr_review_v2/github.py re-exports), GraphQL, compares
  store.py            one directory per PR; immutable payloads; a per-PR ledger
  seed.py             imports the frozen v2 caches read-only
  index.py            sqlite index (a cache that refuses to be read stale) + tracked export
  collect.py          tiered, resumable collection on the core quota
  projections/
    episodes.py       the funnel over the store -> reviewable episodes and releases
    corpus.py         the review-comment corpus, reviewer status tagged; acceptance report
    ledger.py         the A->B ledger from suggestion blocks

data/pull_reviews/                gitignored; authoritative raw data
  pr/<n>/{listing.json, review_comments.jsonl, reviews.jsonl, issue_comments.jsonl,
          pr.json, commits.jsonl, files.jsonl, timeline.jsonl, review_threads.jsonl,
          body_edits.jsonl, compares/<head>.json, fetch.json}
  index.sqlite3  collect.state.json  manifest.json  projections/{corpus,ledger}/
inputs/pull_reviews/              tracked provenance
  manifest.json  prs.jsonl  collection_report.json  acceptance_baseline.json
  acceptance_report.json  rosters/mathlib_roster_<date>.txt
```

**Invariants, each tested:**

* Payload files are immutable (`io.write_once`); an endpoint offered different bytes raises. A
  recorded null may be filled once — a failed GraphQL fetch must not omit a description forever —
  and a later failure never erases a value.
* Null is not empty: `body_edits` is null in 1 of the 201 bundles and empty in 124, and the
  funnel treats them differently.
* Nothing writes under `data/pr_review_v2/`: the store refuses such a root, the v2 fetcher
  refuses to add files to the caches eleven and eight frozen manifests hash, and the roster
  writer refuses the pinned roster (it used to overwrite it by default).
* The index and every projection pin the store's content digest; the precedent index pins its
  corpus's sha and refuses a mismatch (it had drifted 7,000 rows behind unnoticed).
* The store is neutral — scored PRs are collected like any other — and exclusion is a
  projection's job (`definitions.scored_pr_numbers`, which raises rather than return an empty set).

## Evidence, step by step

| step | what | verified by |
|---|---|---|
| 0 | guards first; two stale artifacts made loud | helper guard scans the new package; review-join pin is a staleness check; `load_table` checks versions |
| 1 | `definitions.py`; every caller thin | old predicates kept verbatim as oracles over every login/body/path in the 201 bundles and 43,881 baseline rows; the only corpus-rule change is spec §3.1, exactly 44 + 144 |
| 2 | store + seed | all 201 bundles reassemble exactly, nulls kept; 230 compare copies byte-identical; caches unchanged; reseed is a no-op |
| 3 | index + tracked export | every conversation row indexed once; deterministic rebuild; stale index refused |
| 4 | funnel on the store | **`dev-raw-0.3.0` and `dev-raw-multiround-0.4.0` rebuild byte for byte from the v2 cache *and* from the store** — funnel, episodes, boundaries, round segments, event ledgers |
| 5 | cutoff off the frozen cache | all 193 distinct (PR, reviewed head) pairs across every release resolve identically from either source |
| 6 | collector | fake-GitHub tests incl. collect → tier 2 → episode → cutoff with no v2 cache; **on the real 201 the pre-gate keeps all 138 PRs the funnel includes** (over-fetches 51, mostly size-gated) |
| 7 | corpus projection | on real payloads: old gate's 115 rows all present and agreeing, 144 roster reviewers attributed, reviewer view 215 |
| 8 | consumers | stale precedent index refused (rebuilt, 43,881 rows); the four research readers exclude scored PRs and pin their window to 2025-08-31 |
| 9 | A→B ledger | single-line, multi-line ranges on the comment's side, tail-only flagged |
| 11 | retire | old corpus command refuses and prints the new ones; v2 fetcher cannot write frozen caches |

Gate after every step: full suite green (1,529+ tests), `verify_frozen` 551 refs / 1,132 locked / ok.

## Run order (step 10, in your shell, needs `GITHUB_TOKEN`)

The window is 2024-03-01 → 2025-12-31: 23,092 PRs measured with the search API.

```bash
# tiers 0+1: ~400 listing pages + ~69,000 conversation requests, ~14 h of core quota, resumable
./ape/bin/python -m src.datasets.pull_reviews.collect --start 2024-03-01 --end 2025-12-31
#   ends with a NEXT line: how many PRs pass the pre-gate and what tier 2 costs

# tier 2 for pre-gate survivors (PR object, commits, files, timeline, GraphQL, compares)
./ape/bin/python -m src.datasets.pull_reviews.collect --start 2024-03-01 --end 2025-12-31 --tier 2

./ape/bin/python -m src.datasets.pull_reviews.index build
./ape/bin/python -m src.datasets.pull_reviews.projections.corpus --acceptance   # exits non-zero if it fails
./ape/bin/python -m src.datasets.pull_reviews.projections.ledger
```

Rerun any command to resume. Then, once acceptance passes: repoint `paths.PRECEDENT_CORPUS` to
`data/pull_reviews/projections/corpus/reviewer_view.jsonl`, rebuild the precedent index (it records
the view), rerun `conventions.review_join --write`, and re-measure the convention numbers on the
reviewer view beside the old ones.

## Deviations from the plan, and why

* The event ledger for a store-built release pins each PR's assembled-bundle sha, not each endpoint
  file: it reproduces the frozen ledgers byte for byte and still changes if any endpoint byte does.
* The acceptance baseline keeps PR authors' self-comments (tagged `commenter_is_author`), so the new
  corpus is a strict superset; `reviewer_view` removes them.
* `PRECEDENT_CORPUS` is repointed after collection, not in step 8. Until then the store holds only
  the 201 seeded bundles: 138 are scored and excluded, and the other 63 (PRs the funnel dropped,
  mostly for size) yield 74 corpus rows, 42 in the reviewer view. Pointing retrieval at that would
  shrink its corpus from 43,881 rows to 42. (The step 8 commit message says the projection "holds
  only scored PRs"; that is wrong in the way just described, and the conclusion is unchanged.)
