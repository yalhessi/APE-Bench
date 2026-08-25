# Selector upper-bound: can a judge separate maintainer-worthy findings from the flood?

*2026-06-19. Follow-up to the [miss decomposition](miss-decomposition-2026-06.md), which found
that 81% of gold sits at a predicted location — the wall is **selection**, not coverage. This tests
the selection lever's ceiling. Reproduce: `python -m src.datasets.pr_review_v2.selector
pool={gpt52_holistic,grand_union} selector_model=gpt_5.4`. Raw:
[selector_grand_union_gpt_5.4.json](../../inputs/pr_review_v2/predictions/selector_grand_union_gpt_5.4.json).*

## Setup

Each pooled prediction is labelled **on-target** (covers a gold maintainer finding, via the frozen
topical-judge cache) or **off-target**. A **selector** — gpt_5.4, pointwise, prompt v1 — then scores
each finding 0–100 for *"would a Mathlib maintainer actually raise this?"*, seeing the PR
(title + description + diff, capped 12k) and the finding, but **not** the gold and **not** the other
findings (a realizable per-finding selector). We measure how well the score separates on- from
off-target: AUC, and the gold-recall / finding-precision frontier vs keeping everything.

## Headline: weak, and concentrated in the wrong strata

| pool | candidates | on-target | covered gold | **selector AUC** | severity-flag AUC |
|---|---:|---:|---:|---:|---:|
| gpt_5.2 holistic (eager single agent) | 168 | 37 | 36 | **0.615** | 0.529 |
| grand union (all 6 runs) | 594 | 119 | 54 | **0.625** | 0.521 |

There **is** signal — AUC ~0.62 beats the agent's own severity flag (~0.52) and chance, and
on-target findings score ~9 points higher on average (38.7 vs 29.9). But it is far from a clean
separator, and the precision frontier is nearly flat:

**grand union frontier** (keep findings with score ≥ threshold):

| keep | findings | finding-precision | gold-recall retained | covered gold |
|---:|---:|---:|---:|---:|
| 100% | 594 | 0.200 | 1.00 | 54 |
| 72% | 425 | 0.252 | 0.93 | 50 |
| 60% | 359 | 0.262 | 0.85 | 46 |
| 48% | 283 | 0.269 | 0.74 | 40 |
| 35% | 206 | **0.282** | 0.56 | 30 |
| 23% | 136 | 0.228 | 0.28 | 15 |

To keep 90% of recoverable gold you must keep 72% of the pool, and precision rises only 0.20 → 0.25.
Precision peaks at ~0.28 (cutting 65% of findings) — then *falls*, because past that the selector is
discarding on-target findings as fast as off-target ones. **There is no threshold that delivers the
hoped Pareto win** (high recall *and* high precision). The pointwise diff-only selector does not
crack selection.

## Why: the signal lives in the decidable tail, not the V2 core

Mean selector score of on-target findings, by the stratum of the gold they hit (grand union):

| stratum | n | mean selector score | AUC vs off-target |
|---|---:|---:|---:|
| V1 — decidable (axioms) | 4 | **99.8** | — |
| V2 — golf / dup / generality | 54 | **32.6** | **0.574** (≈ chance) |
| V3 — naming / docs / style | 51 | 43.3 | 0.664 |
| V4 — genuine preference | 10 | 23.4 | (below off-target, 29.9) |
| *off-target* | 475 | 29.9 | — |

The selector is **perfect on V1** (decidable policy violations — new axioms — score ~100), **partial
on V3** conventions (AUC 0.66), and **at chance on V2** (AUC 0.574; mean 32.6 ≈ the off-target mean
29.9). On **V4** it actively *down-*scores genuinely-raised findings (it reads them as "just taste").

This is the V2 instance-selection wall, now demonstrated at the **selection** layer. Reading the
selector's own reasons on the V2 on-target findings it cut:

- *"This is just a stylistic micro-golf with no clear readability benefit, so a maintainer is very
  unlikely to mention it."* — on a golf the maintainer **did** request.
- *"maintainers would not reach into an untouched file to suggest this."* — likewise on-target.

The selector's prior — *maintainers don't bother with golf* — is wrong precisely for the golfs they
bothered with. It cannot tell **which** of many valid V2 improvements the maintainer will pick,
because that choice is not a function of the finding's intrinsic merit (all the golfs are valid; the
maintainer picks one for reasons outside the diff). Robustness: excluding the one pathological
axiom-flooded PR (33149, where many near-duplicate "block this" findings correctly score ~100 but
only the co-located one counts as on-target) moves AUC only 0.625 → 0.647 — not a single-PR artifact.

## Interpretation (provisional)

A reading consistent with the data so far, stated tentatively:

1. **This simple selector separates where the concern is codifiable or decidable** (V1 strongly, V3
   partially) and **not** where it is "pick one of many verifiable-equivalent options" (V2, the
   largest stratum; V4). A content+diff selector appears to re-rank by *codifiability*, which is a
   different axis from *which instance the maintainer wants*.
2. **The selector lever looks narrow, not dead.** It helps for conventions/policy (V1/V3) and not yet
   for the V2/V4 taste core. A "verify + select" system would clean up convention/policy precision and
   leave V2 selection as an open problem — for which the designs below are not yet tried.

These are working hypotheses about *this* selector, not a claim about the task's ceiling.

## The tool-grounded selector does not lift V2 either

The diff-only result above could be dismissed as "the selector couldn't see the code." So we built
an **agentic** selector (`lean_pr_review_selector`): a per-PR agent that materializes the reviewed
workspace and scores each candidate *after investigating* with `file_read`, `content_search`, and
`lean_verify` — it can check whether a golf is genuinely worthwhile, whether a claimed duplicate
exists, whether a generalization holds. Run on grand union, gpt_5.4, same labels and metrics.

It genuinely investigated: ~10 tool calls/PR, **113 `lean_verify` compiles** (89% of PRs verified at
least once), and it discriminates *hard within each PR* (median score spread 76.5/100). This is not a
hedging run. And the result is unchanged — slightly worse:

| selector | overall AUC | **V2 AUC** | base precision | peak precision (sweep) |
|---|---:|---:|---:|---:|
| diff-only, pointwise | 0.625 | 0.586 | 0.20 | 0.375 |
| **agentic (read+search+verify)** | **0.585** | **0.563** | 0.20 | 0.252 |

**Tools did not lift V2 (0.586 → 0.563, both ≈ chance) — or anything.** Overall AUC and peak precision
*fell*. Reading the agent's grounded reasoning shows exactly why:

- **On the maintainer's V2 golfs, it confidently scored ~0–3**, judging *"merely a tiny stylistic
  shortening,"* *"the existing proof is perfectly fine and clear,"* *"an alternative golf for an
  already tiny proof — maintainers are very unlikely to request this."* It can confirm the golf is
  *valid*; it cannot predict that **this** maintainer cared. Its prior — maintainers don't bother
  with minor golf — is wrong for precisely the golfs they bothered with.
- **The findings it scored 100 are gross correctness issues it confirmed with `lean_verify`** —
  unreachable declarations, new axioms, vacuous (`:= True`) definitions. Real, defensible *blocking*
  objections — but not the specific anchored concerns the maintainer raised. Verification makes the
  agent **more** confident about decidable correctness (and V1 actually *drops*, 0.99 → 0.75, as
  these new grounded objections pull off-target findings up), which is orthogonal to V2 taste.

So with the proof and the library in hand, the agent makes confident, kernel-grounded, well-spread
selectivity judgments — in the settings we tried, they are a *different* selection than the
maintainer's.

## What we've tried so far — a preliminary picture, not a conclusion

So far V2 separability stays around chance (~0.56–0.59) across the selector variants we've run:

| variant | V2 AUC |
|---|---:|
| diff-only pointwise (gpt_5.4) | 0.586 |
| diff-only listwise (comparative triage) | ~unchanged ("barely moved the needle") |
| agentic: read + search + verify | 0.563 |

That covers model capability (gpt_5.4), formulation (pointwise/listwise), and tool grounding with
kernel verification. **This is not evidence that V2 selection is irreducible** — it is evidence that
the few *content-and-code* signals we gave the selector don't capture it. Several plausible designs
are untried, and each tests a different hypothesis about where the maintainer's signal lives:

- **Centrality / importance weighting.** A golf may be worth raising not because of the proof in
  isolation but because the affected declaration is *central* to the PR (a main result, depended on by
  the rest, named in the title/description) vs an incidental helper. The current selector sees each
  finding without a sense of how much its target matters. → cheap first cut: does any centrality proxy
  (declaration named in title/description; new vs pre-existing; proof/hunk size; intra-diff reference
  count) separate on- from off-target? (probed below). Then an LLM/agentic centrality-weighted scorer.
- **Natural-language distillation.** Distill the PR (or each changed proof) into a natural-language
  argument, then score a finding higher when the Lean proof *diverges from or obscures* that argument
  — the hypothesis being maintainers flag proofs that are hard to follow relative to the intended
  math, which the raw Lean doesn't surface.
- **Second frontier family / un-primed prompt** — minor; would mostly re-trade recall for precision.
- **Human ceiling / inter-annotator agreement** — whether a second maintainer would raise the same
  V2 golfs at all. Deferred by choice (no maintainer annotation until the agent is more mature); noted
  as the eventual denominator, not a near-term step.

Caveats on the numbers: single run per setting; the on-target label carries ~10–15% topical-judge
slack; the selector prompt primes "maintainers are selective," which may depress golf scores. The
measured statement is narrow and provisional: **the content-and-code signals we have tried so far do
not predict which valid V2 improvement a maintainer raises** — with several untried designs that
could.

### First (cheap, no-API) probe of the centrality idea

Before building a centrality-weighted selector, test whether crude offline proxies already carry the
signal (`centrality_probe.py`; reuses the diff-only selector's cached scores). The key distinction is
**global** separability (across all candidates — helps a global precision threshold) vs **within-PR**
separability (ranking a *single PR's* findings — the axis the selector must actually win):

| feature (V2) | global AUC | within-PR AUC |
|---|---:|---:|
| diff-only selector score | 0.586 | 0.583 |
| declaration named in PR title/description | **0.623** | 0.548 |
| smaller PR (diff size) | 0.70 | 0.50 (PR-level — can't rank within a PR) |
| selector + centrality (combined) | 0.634 | 0.584 |

Read honestly: the centrality proxies carry **real cross-PR signal** (maintainers flag golfs on the
declarations a small, focused PR is *about*) but **almost none within a PR** — "is this the named
declaration" barely separates which of a PR's findings the maintainer picked (0.548), and combining it
with the selector doesn't move the within-PR number (0.583 → 0.584). The within-PR V2 core stays ~0.55.

That cross-PR signal still helps the **deployable global frontier**, though: the combined ranker lifts
overall AUC 0.625 → 0.650 and peak precision **0.375 → 0.529** (it cuts candidates from sprawling PRs
like the axiom-flood 33149). So the takeaway is balanced, not a win or a wall: a cheap centrality proxy
improves *which PRs/findings to scrutinize*, but does **not** crack *which golf within a PR* the
maintainer wants. A richer centrality signal (an LLM/agentic rating of how central a declaration is to
the PR's stated contribution) or the NL-distillation angle would test the within-PR axis the crude
proxy can't.

### NL-distillation probe (diff-only) — signal is real but the cheap version under-expresses it

We distilled each PR into per-declaration (NL statement, NL proof sketch, **legibility** 0–100 = how
directly the Lean proof follows the natural argument, divergence notes) — `distillation.py`,
`distillation_probe.py` — and used *obscurity* (100 − legibility) of the declaration a finding targets
as a selection signal. At the metric level it does **not** separate:

| feature (V2) | global AUC | within-PR AUC |
|---|---:|---:|
| diff-only selector | 0.586 | 0.583 |
| **distillation legibility** | 0.527 | 0.501 |
| selector + legibility | 0.544 | 0.565 |

But the diagnosis matters more than the number, and points the other way:

- **The legibility scale collapsed** — median 93, mean 89 (min 40). Distilling *from the diff alone*,
  the model rates almost every proof highly legible, so obscurity is near-zero for most declarations
  and has no spread to separate on. **48% of findings** also failed to match a distilled declaration
  (lead-identifier heuristic), defaulting to neutral.
- **Yet among matched findings the direction is correct** (on-target V2 obscurity 14.8 vs off-target
  9.6), and **where the model did rate a proof less legible, its divergence notes match the
  maintainer's complaint almost verbatim**: `injective_of_lt_imp_ne` — maintainer *"uses `grind`,
  heavier/less stable"* / distill *"compressed into `grind [Injective]`, the case split is hidden"*;
  `closure_pow_le` — maintainer *"unnecessarily complex and hard to read"* / distill *"the `n=0` case
  is proved indirectly by unpacking membership"*; `subsingleton_hom` — maintainer *"quite elaborate
  (custom `MorphismProperty`)"* / distill *"packages through an auxiliary MorphismProperty."*

So the legibility hypothesis has a **real qualitative basis** — it correctly identifies the proofs
maintainers call convoluted — but the cheap diff-only pass is too charitable (and too lossy on
matching) to turn that into a separating score. Two things follow:

1. **The fair test is workspace-grounded distillation** — the agent reads the *full* proof and the
   lemmas it uses (not a diff hunk) and can judge obscurity against what a clean proof would look like,
   which should de-compress the legibility scale. `distillation.py` is built to be promoted to exactly
   this (`lean_pr_review_distill` subclassing `BasePRReviewTask`, emitting the same artifact) — that is
   the next iteration, not a dead end.
2. **Legibility likely captures a *subset* of V2** — the genuinely convoluted proofs ("hard to read")
   — distinct from the bulk of V2 golf, which is minor brevity/idiom on already-legible proofs. So even
   a sharp legibility signal would address part of V2, and is best seen as one composable feature, not
   the whole answer.

### Workspace-grounded distillation — confirms (2) precisely

We then built and ran the grounded task (`lean_pr_review_distill`): per-PR agent reads the full proofs
(validated: file_read mean 3/PR, 0% skipped; + content_search, lean_verify) and emits the same
artifact. Result, vs the diff-only probe and the selector:

| feature (V2) | global AUC | within-PR AUC |
|---|---:|---:|
| diff-only selector | 0.586 | 0.583 |
| diff-only legibility | 0.527 | 0.501 |
| **grounded legibility** | 0.619 | 0.561 |
| selector + grounded legibility | 0.588 | 0.599 |

Grounding helped at the margin — match rate 52% → 71%, within-PR 0.501 → 0.561, and the combination
edges the selector within-PR (0.599 vs 0.583) — but it does **not** move the deployable frontier
(combo overall AUC 0.615 < selector 0.625). Crucially, the legibility scale **stayed compressed**
(561 decls: 73% rated ≥90, median 95) *even though the agent read the proofs* — because, having read
them, it judges most genuinely legible. On-target V2 proofs are only modestly less legible (mean 87 vs
91), and the clearly-obscure ones (<75) are a **handful (3)** — where the divergence note matches the
maintainer verbatim (`round_eq'` "normalization-heavy `rw` chain"; `injective_of_lt_imp_ne` "the Lean
script delegates all substance to `grind`"; `subsingleton_hom` "divergence from the shortest
argument").

So legibility is a **real but narrow, high-precision/low-recall** signal: it cleanly flags the small
convoluted-proof slice of V2 and is flat on the rest — confirming (2) with grounded data. The bulk of
V2 (brevity/idiom golf on already-legible proofs) is not a legibility phenomenon and remains
unexplained by the content/code/centrality/legibility signals tried. The distillation *artifact* (NL
statement + proof sketch per declaration) is now a validated, reusable asset that may serve other
consumers (semantic duplication, the review agent's comprehension) independent of this selection
result.
