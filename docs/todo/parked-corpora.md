# Built corpora with no consumer, and two gates that were never opened

**Status** — open; each item is a build that already exists and is not being read
**Cost** — no API spend on any of them except the precedent re-bench's judge step

## 1. The A→B ledger is built and nothing reads it

`data/pull_requests/projections/ledger/ab_ledger.jsonl`: **30,297 rows**, 2024-03 to 2025-12,
21,562 line-resolved, 4,358 distinct transformations. Grepping `src/`, `tests/` and `configs/` for
`ab_ledger` or `projections.ledger` returns **exactly one hit — a test**.

Motivating example: the `grind` adoption curve the convention-drift plan wanted as its "enforced"
component is directly countable in it. Suggestion blocks whose B text contains `grind`, by month:
1 (2025-06), 12 (07), 42 (08), 46 (09), 59 (10), 66 (11), 87 (12).

`dead-ends.md` records the constraint that survived the rejected proxies: evidence must carry what
the code was *for* and how it was *expressed*, together — and a modified declaration has both. The
ledger is that shape, at 30k rows, on disk.

What would close it: run the plan's four remaining items against the existing rows — multi-line A
spans (11,219 rows are already `range`), a transformation clustering coarser than leading tokens,
the NL half, and facet conditioning — and put one query behind a reviewer-facing tool.

## 2. The Zulip citation benchmark's 45% unresolved rate is a build-scope artifact

`inputs/zulip/review_citations_report.json`: 147 maintainer citations, 143 unique URLs, 80 resolved,
75 resolved and predating the comment. The 67 unresolved break down **exhaustively** into
`outside_build_window` 45 and `stream_not_ingested` 22, across exactly five stream ids
(116395:12, 113489:4, 252551:3, 345428:2, 335062:1). The store is 9 core streams from 2024-11-01;
the local mirror it syncs from holds 121 streams and 60,758 topic files.

So the 45% is not a corpus limit and not a retrieval failure — it is two build parameters.

What would close it: re-run the sync with the five stream ids added and the window pushed back far
enough to cover the 45, then re-run `-m src.datasets.zulip.citations`. Local mirror, no API cost.

## 3. The precedent index's STRONG-GO gate was never measured on the shipped index

`inputs/pr_review_v2/precedent_bench/report.json` (written 2026-07-04) records dense_code hit@5
53/109 (49%) and V2 stratum 28/50 (56%), and `PROJECT-STATUS.md:213` reads "STRONG GO at 0.615".

Two things are wrong with carrying that number forward. Four commits since changed the index recipe
(`0812828` moved the embedded slice to the hunk tail because 53.2% of hunks overflowed the 256-token
window from the front; `663026f` added `commenter_is_pr_author` — 16,361 of 43,881 rows — and
`pr_refs`; `e86498d` added one-hit-per-hunk ranking; `2d95f72` bumped the identity to
`v5-precedent-index/2` precisely because "rebuild the index and the same query returns something
else, with nothing in the run saying so"). And, worse: `precedent_bench.py:253-281` builds its own
embeddings in-process from the raw corpus and has **no reference to the shipped index at all** — so
the gate has never measured the artifact the reviewer actually queries.

What would close it: re-run `precedent_bench retrieve --design dense_code` and `report` against the
v2 corpus with the current recipe, wired to the shipped index. Steps 1, 2 and 4 are free; the judge
step only pays for pairs the cache misses. Report the delta against 49% / 56%.

## 4. Condition C has never run, and its gate does not exist

`configs/pr_review_v5_solo_claude_heldout12.yaml:3-4` opens "DO NOT READ A NUMBER FROM THIS UNTIL THE
TRANSCRIPT LEAK AUDIT EXISTS AND HAS BEEN SHOWN TO FIRE ON A PLANTED LURE." Grepping `src/` and
`tests/` for lure or leak-audit finds only three comments describing what such an audit would read.
There is no `pr5_C_*` run and no `pr5-C-*` audit.

This is already written down — `ab-heldout12-obligation-spine.md:256-258` states it verbatim under
"What this cannot support" — so it belongs here as a scheduled build, not as a discovery.

What would close it: build the audit as an analysis module over the scaffold transcript, plant a
gold-only string somewhere reachable, run one smoke4 C task, and assert the audit names it. **Fix
`proof_profile`'s missing trace row first** (see
[evidence-tiers-and-traces.md](evidence-tiers-and-traces.md)) or the audit will pass over a tool
whose calls it cannot see.

## 5. A retraction that now has counterexamples

`dead-ends.md` retracts "arms are competent locally but structurally cannot reach design" on the
grounds that design recall ≥ local in every audited run with hits. Over the six committed held-out
audits (11 design / 10 local / 2 borderline of 23): condition A holds it — design
0.364/0.273/0.273 against local 0.300/0.200/0.300 — but condition B breaks it twice (rep2 design
0.091 < local 0.300; rep3 design 0.000 < local 0.100).

And the more interesting fact underneath: **design obligations are located far more often than local
ones** (A locates 9/7/7 of 11 design against 4/5/5 of 10 local), and the two obligations nobody ever
located — 33294's fully-qualified `rw`, 33305's over-long doc line — are both local style.

What would close it: update the retraction with the six-run numbers, the design-vs-local location
split, and the condition qualifier. It is a docs edit; the measurement is done.
