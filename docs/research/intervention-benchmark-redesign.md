# Intervention-level benchmark redesign — spec

> **Generation-design update (2026-07-11):** The intervention lens remains the benchmark basis,
> but this document's assumption that the hunk/site generation pipeline stays unchanged is
> superseded by [PR Review v4: Semantic Targets and Evidence-Backed Review](pr-review-v4-evidence-pipeline-design.md).
> V4 migrates i5 into a judgment graph and derives the intervention lens as a versioned evaluation
> view, preserving intervention-level reporting without making one grouping policy permanent.

*2026-07-09, v0.1 (draft for review). Motivation: after the apply-all twins, every remaining
measurement problem traces to the formulation, not the pipeline. The gold unit (individual
comments) double-counts judgments and inflates variance; the judge conflates issue-identification
with resolution-equivalence and wobbles exactly on that seam (30–40% generous accepts, near-miss
rejects, one same-site accept/reject inconsistency); a slice of gold is unjudgeable indexical
fragments ("Same here"); and one open-ended generation metric smears three separable capabilities
(identification / instantiation / selection) whose states are wildly different (≈solved / ≈half /
≈absent). This spec redesigns the measurement. The generation pipeline, strata, drift-proof delta
anchoring, corpus, and verified-edit infrastructure are unchanged.*

## 1. The new gold unit: the intervention

> **intervention** := one maintainer judgment + the set of sites it applies to + its outcome.

```jsonc
{
  "intervention_id": "pr33098_i03",
  "pr_number": 33098,
  "stratum": "V2",                      // V1..V4, unchanged rubric
  "concern": "proof-golf",              // the 7-way taxonomy already used by the profiler
  "canonical_ask": "Prove encard_minimalCover and the three sibling lemmas with the new
      IsCover.coveringNumber_le_encard lemma; add `attribute [grind] finite_empty` so it also
      closes finite_minimalCover.",     // SELF-CONTAINED: thread context resolved, referents named
  "rationale": "shorter, reuses the API introduced in this PR review round",
  "anchors": [                          // one judgment, MANY sites (the 33098 ask spans 4 lemmas)
    {"path": "...", "hunk_id": "...", "line_start": 210, "line_end": 218, "decl": "encard_minimalCover"},
    {"path": "...", "hunk_id": "...", "line_start": 221, "line_end": 229, "decl": "finite_minimalCover"}
  ],
  "source_comments": [{"id": "rc_...", "body": "...", "author": "...", "submitted_at": "..."}],
  "severity": "advisory",
  "outcome": "adopted",                 // adopted | partially_adopted | contested | dropped | unknown
  "outcome_evidence": "delta_near hunks r2 rewrite all four proofs via coveringNumber_le_encard",
  "judgeable": true                     // false => excluded from denominators, kept for audit
}
```

Construction from the existing 57-PR gold (204 comments, 129 actionable):

1. **Thread grouping** (mechanical): replies in one review thread belong to one intervention.
2. **Propagation resolution** (mechanical + LLM): "Same here / Same below / and the other ones /
   Same comment" attach to the nearest preceding substantive comment by the same author; the LLM
   resolves which sibling site each marker points at (the delta parser supplies sibling
   declarations).
3. **Cross-comment merge** (LLM-proposed, human-confirmed): same PR + same concern + same
   transformation described ⇒ propose merge (catches the 33145 dualization plan, six comments =
   one refactor).
4. **Enrichment** (LLM + human skim): write `canonical_ask` — self-contained, referents named,
   thread context inlined. Comments with no recoverable ask ("I don't think there is consensus?")
   get `judgeable: false`.
5. **Outcome labeling** (LLM + human skim): compare the intervention's anchors/ask against later
   revisions (`delta_near`/`delta_total` across rounds, already collected) and `thread_resolved`;
   emit adopted / partially_adopted / contested / dropped with quoted evidence. This labels
   *maintainer comments by consequence* — it does not mine author edits as a taste source (out of
   scope by prior decision).

Expected shape: ~75–85 interventions from the current ~120 anchored comments; cluster-size
distribution and % judgeable are Phase-A sanity gates (expect ≥90% judgeable).

## 2. The new judge: two-level, canonical-ask-referenced

Both levels judge the prediction against `canonical_ask` (never the raw indexical comment), with
anchor matching = overlap with **any** anchor of the intervention (slack unchanged).

- **issue-match**: the prediction identifies the same problem — same site(s) and the same
  *specific aspect* of the code (not merely the same concern category). It may propose a different
  fix. *"The private helper's status/purpose needs addressing"* issue-matches both "document why
  it is private" and "make it public".
- **resolution-match** (implies issue-match): the prediction's concrete change achieves the
  canonical ask's resolution, judged by comparing the changes (v6's change-comparison machinery is
  kept). This is the strict, headline-quality level.

Mechanics carried over: per-pair content-keyed cache, prompt versioning (`v7`), model-in-the-loop
only at judge time. Added from day one: a **standing audit protocol** — every re-judge samples 10
accepted + 10 rejected pairs for hand-verification before its numbers are used (both prior audits
found miscalibration only after the fact).

## 3. Tiered metrics (the three separable capabilities)

Per system run, over judgeable interventions:

- **T1 identification**: fraction of interventions whose (any-anchor site, concern) appears among
  the system's candidate items — measures enumeration + concern profiling + checker attempt.
  Current pipeline: ~85–90%.
- **T2 instantiation** (conditional on T1): issue-match rate and resolution-match rate. Current
  estimate: ~50% / ~35% respectively, conflated in today's single number.
- **T3 selection**: the system nominates at most k findings per PR (k≈3, matching maintainer
  volume); precision and intervention-recall of that top-k set. This is where the 9%-precision
  flood is punished and where selection ideas are tested. Self-ranking is falsified; T3 exists to
  measure whatever external signal we try next.
- **Reporting axes**: stratum (V1–V4), outcome (headline = adopted + partially_adopted;
  all-judgeable as secondary), and per-tier funnels. PR-level bootstrap CIs on everything — the
  twins put the comment-level noise floor at ±5/120; intervention units + CIs make effect
  readability explicit rather than folklore.

## 4. Worked examples (what the redesign fixes, from real failures)

1. **The 33098 six-fold golf** ("This and the next three lemmas can be proven with this…", ×6
   comments). Today: 6 gold points; apply-all matched 1 → recall 1/6, and a "sibling propagation"
   post-processor was the proposed fix — a hack compensating for the unit. Redesigned: **one**
   intervention, multi-anchor; the existing match = 1/1 resolution-match. The judgment was found;
   the metric finally says so.
2. **"Same here" (33349) / "(and the other ones)" (33283)**. Today: standalone unjudgeable golds —
   the v6 judge itself said *"A's terse prose doesn't identify the concern so B cannot be judged"*;
   they sit in denominators as guaranteed misses. Redesigned: propagation markers resolved into
   their parent intervention's anchor set; judgeable, and no longer double-counted.
3. **The 33092 accept/reject inconsistency**. Same private-helper site; pred "make it public" was
   accepted (run2b) while pred "reuse existing API / expose it" was rejected (run1b) — the v6 gate
   forced one bit onto a two-part question. Redesigned: both preds **issue-match** (the helper's
   private status/purpose is the flagged problem); neither **resolution-matches** the maintainer's
   "document why". Consistent, and the partial credit is visible instead of coin-flipped.
4. **The `mul_fract` near-miss (33421)**. Maintainer wrote out the generalized statement; the model
   proposed exactly that generalization by name, judged reject under v6's fused criterion.
   Redesigned: issue-match ✓, resolution-match borderline — scored as identification-with-imperfect-
   instantiation instead of a zero.
5. **The apply-all "regression" confusion**. Decide-v2 (12 covered, 44 findings) vs apply-all
   (30–35 covered, 425 findings) were incomparable under one number — recall and flood moved
   together. Redesigned: decide-v2 = lower T1-attempt, similar T2, no T3; apply-all = high T1,
   measured T2, failing T3. Three numbers, no confusion, and the week of re-analysis those runs
   required becomes the default report.
6. **Outcome weighting**. *"How about `round_eq_div`?"* (adopted — author renamed) and *"I don't
   think there is consensus here?"* (contested) currently carry equal weight. Headline metrics on
   adopted interventions measure "matches the judgment that shaped the PR", which is the claim we
   actually want to defend to maintainers.

## 5. Phases, gates, and cost

- **A. Intervention dataset** from the existing 57 gold-bearing PRs: clustering + enrichment +
  outcome pipeline (LLM-assisted, human-reviewed; ~204 comments, an afternoon of review).
  *Gate:* ≥90% judgeable; cluster sizes match the known clusters (33098=1, 33145=1–2); spot-check
  10 canonical_asks against threads.
- **B. Judge v7 + tiered evaluator** (`evaluate_i1.py`), with the standing audit protocol.
  *Gate:* 20-pair audit ≥85% agreement with hand judgment on both levels.
- **C. Re-score history** from cached prediction files (mechanical; matcher-style cache). Deliver
  the corrected historical table + intervention-level noise floor from the apply-all twins.
  *Gate:* twin |Δ| under intervention scoring ≤ comment-level |Δ| (expected, since clusters no
  longer flip together).
- **D. Scale** (after C, decision point): extend to ~150–200 gold-bearing PRs via the existing
  collection pipeline to halve CI widths. Deferred until C shows the floor.

Old v6 numbers are kept as an appendix for continuity; all live comparisons move to the new metric.

## 6. Non-goals

- Changing the target: gold remains real maintainer comments on real PRs (no maintainer
  annotation campaigns, no synthetic gold, no author-edit-derived taste — all previously ruled out).
- Redesigning the generation pipeline: site enumeration, concern profiles, precedents, verified
  edits, apply-all mode are all unchanged and keep their roles.
- Solving T3 in this redesign: the spec makes selection *measurable*; the selection idea itself
  (external grounding signals) is the next research step, not a benchmark property.
