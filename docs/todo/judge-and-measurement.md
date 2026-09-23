# The judge and the denominators — what every recall number in the record is conditioned on

**Status** — open; all four items are re-scoring or docs edits on committed artifacts
**Cost** — no generation spend

## 1. The judge only ever pairs at `anchor`

**705 of 705 pairs across all 50 v5 audits carry `pairing_tier: anchor`. No other tier has ever been
emitted.** A correct arm ask that lands on a neighbouring `change_id` in the same file is never shown
to the judge at all.

Motivating example: on PR 33362 the `style` arm submitted "Move `schwarz_aux` inside the existing
`namespace Complex` (dropping the `Complex.` prefix)" against a gold obligation reading "Move the
relevant declarations a few lines down so they are inside the `namespace Complex`". The candidate
anchors to `change:744403789c64b230…`, the obligation to `change:26e35f26fa007867…`, and
`semantic_pairs.jsonl` for that PR in that rep has **zero rows**.

**Honest caveat, which is why this is item 1 and not a headline:** pairing it would not
automatically have made it a hit. That obligation was judged 6 times by candidates that *did* carry
the gold change_id, and the judge said `issue_match=False` on 4 of them; only solo's two were hits.

**Recounted 2026-09-23:** 998 of 998 pairs across 58 v5 audits are `anchor`. **And the prepared
widened node fails open.** `dev-medium-0.3.0/derived/` has no `pr_relations.jsonl`, and
`judge/runner.py::collect_pairs` falls back to `relations = []` when it is missing, so the pipeline's
`judge_relation` node (`configs/pipelines/heldout12_judged.yaml`) would re-judge the anchor pairs
under a new identity and label the result widened. Nor would `[anchor, relation]` reach the
motivating example above: `schwarz_aux`'s namespace ask pairs only at the `file` tier. With relations
derived in memory (`build_relations`, 1,005), widening adds 75 / 106 / 83 relation and 598 / 591 / 616
file pairs to lead v2 reps 1-3 (546 of rep1's file pairs are PR 33149); of 16 / 18 / 17 misses, 8 / 9
/ 9 have no anchor-paired candidate and widening reaches 7 / 7 / 8, but a read of those widened claims
finds almost none naming the gold issue -- about 0-1 obligations a rep, the 33362 namespace ask the
plausible one. At $0.0064 a judged pair (554 held-out pairs cost $3.57) the misses-only re-judge is
~$1.83 for lead v2. Widening can only raise recall, so a widened number is never the "beats 7" claim
and is reported beside anchor, for baselines and new runs alike. **First, free:** make
`collect_pairs` refuse a non-anchor tier when the relations file is absent (or derive and hash it),
with a test. Note `cli judge` without `--execute` returns before any pair is built, so pair counts
come from calling `build_pairs` directly, and `--of` with the default node writes into the anchor
audit, whose identity guard would refuse the widened one.

What would close it: re-run `judge` on the three held-out lead reps with
`pairing_tiers=[anchor, relation]` — the code path exists at `semantic_judge.py:66` — and report how
many specialist findings move from unpaired to paired-and-matched. Every per-arm recall number in
the record, including "seven specialists matched nothing" and the fanout-vs-lead comparison, is
currently computed under a rule that discards arm findings that are right about the file and
anchored one change away.

## 2. The active judge splits its own vote on 10.8% of pairs

`protocol.py:34` has read `v4-semantic-v3-v9-rubric` since the v4 move-in refactor. Pooled over all
50 v5 audits: **705 pairs, all at 3 samples, 76 with 0 < issue_votes < 3 — a 89.2% self-agreement
ceiling.** Restricted to the six held-out A/B runs the 2026-09-14 comparison rests on: 22 of 221 =
10.0%.

`results/pr_review_v4/audits/judge-v8/VERDICT.md` records 0/18 splits under v8 and concludes
"v8-scored comparisons carry approximately no judge noise"; the roadmap's R0 row still says v8 is
active. **That zero did not carry forward**, and nothing currently being scored inherits it.

What would close it: write the n=705 v9 measurement into `dead-ends.md` beside the existing ~11%
line and correct the R0 row in `pr-review-next-iteration-roadmap.md`. Zero cost — the number above
is the measurement.

## 3. One PR is most of condition A

Pooled over the three held-out A reps: **907 findings, 625 of them on PR 33149 (68.9%)**; 560
blocking demands, **478 on 33149 (85.4%)**. Outside it, A issues 25, 28 and 29 blocking demands per
rep, not ~167. The largest off-gold concern, `style` (348 pooled), is 251 on 33149 alone.

33149's own gold includes "rewrite the file to Mathlib standards", so most of that volume may be
correct-but-unmatched rather than false — which is exactly why the aggregate cannot be read as a
precision measurement.

What would close it: re-report §6 of the spine write-up twice — all 12 PRs, and with 33149 excluded
— plus a median-PR figure. Zero cost; the artifacts are committed.

## 4. `manual_audit_required` is a constant, and no manual audit has ever been written

`semantic_judge.py:532` writes `"manual_audit_required": True` as a bare literal with no condition.
All 50 v5 semantic reports carry it. `find results/pr_review_v5/audits -name '*.md'` returns
nothing — **51 audit directories, zero verdict documents** — while the v4 tree has 40+ hand-written
verdicts.

What would close it: make the flag conditional on something real (ambiguous rate, split votes
present, gold provisional) or drop it; and hand-audit one held-out rep's 60 pairs, writing
`VERDICT.md` the way the v4 tree does. One sitting, no spend.

## Why these four sit together

Items 1–3 each change what a recall number *means*, and all three are cheaper than any new run. Any
experiment scheduled before they land will be interpreted against denominators that are known to be
wrong in a known direction.
