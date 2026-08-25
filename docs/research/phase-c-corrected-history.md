> **SUPERSEDED (2026-07-11).** These numbers were produced from worklists whose sites were
> derived from `gold.delta_total` (post-review revision data) — a future-state leak; see the
> postmortem in `src/datasets/pr_review_v2/site_worklist.py::pr_sites_with_spans`. All runs
> scored here are **oracle-site diagnostics**, not deployable measurements. Kept for
> provenance; the raw-site (leak-free) reruns replace them.

# Phase C — the corrected history under intervention gold (judge v7.1)

*2026-07-10. All full-57 systems re-scored against `interventions_v4.jsonl` (91 judgeable non-meta
interventions) with the two-level judge (v7.1, post-audit) and tiered metrics. This table is the
foundation of the paper's results section; the v6 comment-level numbers are superseded and kept
only as an appendix for provenance.*

## The table

| run | T1 identify | T2 issue | T2 resolution | T3@3 recall | T3@3 precision | issue CI95 |
|---|---|---|---|---|---|---|
| idiom baseline | 37% | 12% | 4% | 9% | 23% | [4, 22] |
| idiom primed | 38% | 15% | 7% | 13% | 24% | [7, 24] |
| decide v1 | 47% | 19% | 10% | 19% | 34% | [11, 28] |
| decide v2 | 37% | 18% | 8% | 18% | 36% | [9, 26] |
| **apply-all 1b** | **84%** | **40%** | **21%** | **26%** | 20% | **[28, 50]** |
| **apply-all 2b** | **86%** | **43%** | **23%** | **31%** | 22% | **[31, 55]** |

Judge audit (standing gate): v7 17/20 → v7.1 clean on re-audit (defend-the-code pattern rejected;
accepted pairs all assert the problem). Denominator: judgeable, non-meta interventions;
headline outcome-weighting (adopted+partially_adopted) tracks these numbers closely.

## What is settled

1. **The measurement works.** Twin runs (identical config) agree within 1–4 points on every
   metric; under v6 comment-gold the same pair swung ±5–7. Intervention units + two-level judging
   made ~5pp effects readable — the redesign's core promise, delivered.
2. **Exhaustive site-first instantiation (apply-all) is the real result of the project so far**:
   identifies the maintainer's problem for **40–43%** of interventions (~2.2× the best generative
   checker, CIs essentially separated), resolves **~22%**, and — at maintainer-like volume via
   confidence-ranked top-3 — delivers **26–31% recall at ~21% precision**. Replicated, CI'd,
   judge-audited.
3. **Closed questions**: precedent priming is null at every level (idiom 15% vs 12% issue);
   decide-v1 vs v2 identical (the v6 "19 vs 12" was noise); the decide→apply-all gap is entirely
   the removal of the voluntary APPLY/SKIP layer (T1 47% → 85%).
4. **Of genuinely identified problems, over half get the right resolution** (19/36, 21/39): the
   earlier "instantiation content is the wall" read was inflated by defend-findings; the
   issue→resolution gap is real but smaller than v7 suggested.
5. **Within-PR relative confidence ranking works** (top-3 keeps ~67–72% of issue coverage) even
   though absolute confidence thresholds were uninformative — selection at fixed volume is in
   materially better shape than the v6-era analysis concluded.

## Where the losses are now (apply-all funnel, twin-averaged)

identify 85% → issue 41% → resolution 22% → top-3 recall 29%

- **T1 gap (15%)**: interventions at sites/concerns the worklist never surfaced (profiler misses,
  unanchored asks).
- **identify→issue (85→41)**: findings at the right site about the wrong aspect — the residual
  "generic instantiation" problem; the concern label + precedents under-determine WHICH aspect.
- **issue→resolution (41→22)**: right problem, different fix than the maintainer's.
- **T3 compression (41→29)**: modest; selection is no longer the dominant loss.

## Standing caveats

- Judge leniency is now audited at ~19–20/20 but the audit is 20 pairs/run; keep the standing
  audit on every re-judge.
- n=91 interventions from one 57-PR window; CIs are honest but wide — the scale-up (Phase D,
  ~150–200 gold-bearing PRs via the windowed collection pipeline) halves them.
- All systems share gpt_5.2 generation; model-generality unmeasured.
