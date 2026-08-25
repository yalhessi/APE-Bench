# Baseline: agentic merge-readiness review on Mathlib PRs

**Status:** baseline locked 2026-06-18. Supersedes the optimistic recall numbers in earlier notes
(they were metric artifacts; see §3).

## 1. Question and setup

Can a capable agent recover the findings a Mathlib maintainer would raise on a pull request —
*at the same place, about the same concern*? We measure two review implementations on the same
30-PR slice, the same materialization (merge-base snapshot + δ₀), the same finding contract, and
the same evaluator, so they are directly comparable:

- **Holistic** (`lean_pr_review_v2`, `acceptability_v2` prompt): one agent reads the diff and the
  reviewed tree (read/search/verify tools) and submits the findings it judges worth raising.
- **Composed / decomposed** (`golf` + `dup` + `gen` checkers, union-aggregated): three focused,
  kernel-verified-at-submission checkers; every submitted finding carries a Lean artifact the
  kernel re-checked.

Model: `gpt_5.4`. Gold: maintainer comments on the 30 PRs, stratified V1–V4 by mechanizability
(V1 decidable, V2 checkable-by-computation, V3 codifiable-convention, V4 genuine-preference;
non-findings tagged P/Q) per [stratum-rubric.md](stratum-rubric.md), then quality-filtered to
**actionable, in-scope** findings (§4).

## 2. Metric: location is necessary but not sufficient

A finding is **covered** iff a prediction is (a) in the same file within a line window of the
maintainer's anchor *and* (b) confirmed by an LLM judge (`MATCH_PROMPT`) to address the **same
concern** — not merely the same location. The topical gate matters: a checker that floods golf
suggestions will, by chance, land some near unrelated maintainer comments (a golf next to a
docstring request), and pure-location matching scores those as hits. Precision is reported as the
**on-target rate** (predictions on some actionable target / predictions made), which stays
kernel-anchored for the verified checkers. Evaluator: `evaluate_d2.py mode=target topical_gate=True`.

## 3. The metric had to be fixed before any number was trustworthy

Three corrections, each of which moved the result materially. They are part of the result:

1. **Path normalization.** Predicted findings carried workspace-relative paths (`target/Mathlib/…`),
   gold paths were repo-relative (`Mathlib/…`); the location gate compared raw strings and silently
   failed on every prefixed path. Fixing it roughly doubled raw location-recall (e.g. golf anchor
   recall 0.097 → 0.194). Every pre-fix "recall ≈ 0" was partly an artifact.
2. **Topical gate.** Pure location *over*-counts via coincidental co-location; strict
   claim-equivalence *under*-counts (a valid different golf for the same proof reads as a mismatch).
   The truth is between. Pure location credited holistic 8/27 and composed 9/27 (union 52%), which
   looked like strong complementarity; under the topical gate both collapse to ~2 (§5), and the
   apparent complementarity was almost entirely coincidence.
3. **Gold quality.** Some comments labelled as findings are not actionable requests — approvals
   ("I like this the best"), indecision ("I'll wait for another opinion"), content-free pointers
   ("Same here"). They inflate the denominator. A cached, audited re-classification
   (`actionability.py`) moved 10/153 (6.5%) to non-finding `P`; pre-existing/out-of-scope comments
   were *kept* as actionable by choice.

Lesson, recorded honestly: every loose metric flattered the agents, and the conclusion only
stabilized after reading the actual comments / using a strict audited judge. Small-N here means the
metric, not the eyeball, must be the arbiter — but the metric must first be made honest.

## 4. Result

Topical-gated coverage on the cleaned, actionable gold (23 anchored findings on the 30 PRs):

| review        | findings made | covered (of 23) | recall | on-target rate | V2     | V3     | V4    |
|---------------|--------------:|----------------:|-------:|---------------:|--------|--------|-------|
| holistic      | 10            | 2               | 8.7%   | 20% (2/10)     | 1/9    | 1/11   | 0/2   |
| composed      | 56            | 2               | 8.7%   | 3.6% (2/56)    | 2/9    | 0/11   | 0/2   |

- **Both recover < 10% of actionable maintainer findings**, same place and same concern.
- **They are tied, and their two hits overlap** (both catch the PR33373 `iteratedDeriv`
  duplication/golf). The decomposed checkers add **zero** genuine coverage over the single agent.
- **Holistic's only robust advantage is precision** (20% vs 3.6%): it makes 10 findings for 2 hits;
  the composed run makes 56 for the same 2.
- **~21 of 23 actionable findings are caught by neither**, dominated by the **V3 convention**
  bucket (naming, namespace placement, explicitness, restatement) — non-verifiable conventions that
  the kernel-checked checkers structurally cannot target and the holistic agent's merge-ready
  threshold skips.

## 5. What does *not* move the result (ablations already run)

- **Scale.** Larger models did not push the precision/recall frontier out (earlier runs).
- **Decomposition.** Per-concern checkers flood off-target findings without adding coverage; the
  single holistic agent's implicit selectivity is more efficient.
- **Exhaustive enumeration.** The missed findings are *not* a coverage failure: in a transcript
  audit of the holistic agent's missed V2 targets, the agent had `file_read` the exact file
  containing the target and deliberately concluded merge-ready. It looked and passed — a *judgment*
  gap, not an attention gap. Forcing it to consider every declaration would not recover them.

## 6. Interpretation and next step

Verifiable correctness is solved by construction (any improvement the checkers propose is
kernel-checked), but that is not the bottleneck. The bottleneck is **judgment calibration**:
matching the maintainer's threshold for *which* improvements — largely codifiable conventions — are
worth requesting. The open question this baseline sets up:

> Does giving the agent the community's **stated norms** (the Mathlib guidelines) close the
> convention gap, or is the residual irreducible taste?

The next experiment injects the Mathlib guidelines into the holistic agent and measures the same
topical-gated, actionable frontier — watching recall **and** off-target rate, so we credit a pushed
frontier, not merely more flagging. See the guidelines-agent design.

## 7. Powered run (57 PRs, N=115) and the guidelines result

The 30-PR slice (N=23, 1–2 hits) is too coarse to compare interventions. Re-run on all 57
gold-bearing PRs (115 anchored actionable findings), baseline vs a **guidelines-supplied** agent
(`lean_pr_review_guidelines` = the holistic agent with the distilled Mathlib guidelines appended to
its system prompt — the only variable):

| stratum | gold | baseline covered | guidelines covered |
|---------|-----:|-----------------:|-------------------:|
| V2      | 56   | 2 (3.6%)         | 2 (3.6%)           |
| V3      | 53   | 8 (15%)          | 6 (11%)            |
| V1/V4   | 6    | 2                | 2                  |
| **all** | 115  | **12 (10.4%)**   | **10 (8.7%)**      |

Baseline made 33 findings (34/57 approved); guidelines made 31 (39/57 approved).

- **Guidelines is a negative result.** Supplying the community guidelines produced no recall
  improvement — slightly *lower* on every axis, and more lenient (more approvals). The ~2-finding
  gap is within noise, so not a real *harm*, but a large positive effect is ruled out (guidelines
  came out slightly lower in both the 30-PR and 57-PR runs). Explicit norms do not close the gap.
- **The apparent "guidelines re-orient behaviour toward conventions" from the 30-PR run did not
  replicate**: at N=57 the two concern-type mixes are nearly identical. That signal was small-N.
- **The real, powered finding is the stratum structure.** V2 — the largest stratum and the
  *verifiable* one (golf / duplication / generality, checkable by computation) — is the
  **worst-recovered (~4%)**; codifiable conventions (V3) are caught **3–4× better**. The bottleneck
  is **instance selection**: many proofs are golfable and many results generalizable, so the agent
  flags *different* instances than the maintainer and overlap collapses. Conventions are more
  deterministic (a naming violation is objectively one), so agent and maintainer agree more often.
  This sharpens the thesis: the stratum where verification *should* help is the least recovered, and
  the wall is selecting the specific instance a maintainer cares about — which neither verification
  nor supplied norms address.

## 8. Composed at scale: the architectures are complementary (hybrid → 20%)

Running the decomposed checkers (golf+dup+gen, kernel-verified) on the same 57 PRs, topical-gated:

| review     | covered (115) | V2 (56)  | V3 (53)  | on-target rate |
|------------|--------------:|---------:|---------:|---------------:|
| holistic   | 12 (10.4%)    | 2 (3.6%) | 8 (15%)  | 36%            |
| guidelines | 10 (8.7%)     | 2        | 6        | 29%            |
| composed   | 13 (11.3%)    | **8 (14%)** | 4 (7.5%) | 12.8%       |

Overlap of holistic vs composed coverage: **both 2, holistic-only 10, composed-only 11, union
23/115 (20%)** — nearly double either alone, with a clean stratum division of labour: composed owns
V2 (its target, the verifiable stratum: 8 vs 2; 6 of its hits are V2 findings holistic missed),
holistic owns V3 conventions (8 vs 4, *zero* overlap).

This **overturns the 30-PR conclusion** (§5) that "decomposition adds nothing": that was an
underpowered artifact (N=23, ~2 hits each, complementarity invisible). At N=115 the verified
checkers recover **4× more V2** than the selective holistic agent — exhaustive verified generation
partway breaks the instance-selection wall, at a steep precision cost (125 findings, 109 off-target).
Two consequences:

1. **The frontier is pushable — by combining architectures, not by scale, decomposition-alone, or
   norms (all of which failed individually).** A holistic+composed hybrid covers 20%, ~2× either.
2. **Selectivity is now a well-posed problem.** The union candidate set (33 + 125 = 158 findings)
   genuinely *contains* 23 gold; a selector that keeps them while cutting the off-target pile would
   trade composed's flooding for precision. (Earlier dismissed because a single agent's candidates
   lacked the gold; the powered union refutes that.)

## 9. Second model (gpt_5.2): threshold, not capability

Repeating all three on gpt_5.2 (same 57 PRs, same metric):

| | gpt_5.4 | gpt_5.2 |
|---|---:|---:|
| holistic recall | 12 (10.4%) | **36 (31.9%)** |
| holistic findings / approvals(57) | 33 / 34 | 168 / 16 |
| holistic precision (on-target) | 36% | 24% |
| guidelines recall | 10 | 32 |
| composed recall | 13 | 15 |
| holistic V2 / composed V2 | 2 / 8 | 15 / 9 |
| composed-only (adds over holistic) | 11 | 6 |
| union | 23 (20%) | 42 (36.5%) |

- **The model difference is a flagging *threshold*, not capability.** gpt_5.2 is far more eager (168
  findings vs 33; approves 16/57 vs 34/57), so it scores 3× the recall at lower precision. The two
  models *bracket* the maintainer's threshold — gpt_5.4 under-flags, gpt_5.2 over-flags; neither is
  well-calibrated.
- **The guidelines null replicates** (gpt_5.2 guidelines 32 < holistic 36), on two models now.
- **Composed recall is nearly model-invariant (13 → 15)** because the kernel-verification gate, not
  the model's eagerness, bounds checker output. Holistic recall is whatever the model's threshold is
  (12 → 36).
- **The composed "V2 rescue / complementarity" (§8) is gpt_5.4-specific.** It depends on the
  holistic agent under-flagging V2; gpt_5.2's eager holistic catches V2 itself (15 > 9), so composed
  adds only 6 (vs 11). Decomposition helps **when the base agent is conservative.**

Robust across both models: guidelines don't help; verified-checker recall is stable; the agents
trace different points on one precision/recall frontier via their thresholds.

## Caveats

Single stochastic run per configuration; the per-stratum counts are small (V1/V4 especially).
Directional, not precise — but the V2≪V3 gap (2/56 vs 6–8/53) and the guidelines null are now on
N=115, not N=23. The topical judge (`gpt_5_mini`, `MATCH_PROMPT v3`) was spot-checked and is
well-calibrated but is itself an LLM; recall uses it, precision (on-target / verified) stays
kernel-anchored.
