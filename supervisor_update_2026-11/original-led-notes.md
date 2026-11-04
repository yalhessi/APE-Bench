# Framing and narrative notes

Current presentation: [HTML](original-led.html), [PDF](original-led.pdf),
[Markdown and speaker notes](original-led.md). Revised for 4 November 2026.

## Framing changes

The first section keeps the October objects and progression: library and PR purpose,
solution set, APE-Bench, reviewing, worked PR examples, reviewer work and limitations.
The boxed closing sentences are removed. The framing now follows the user's
division of work: compilers, kernels and tests help separate solutions from
non-solutions; reviewers identify accepted or preferred solutions; an automated
reviewer captures human review, or a useful subset, as additional checks.

The refined solution set is written `S_R = {δ ∈ S : δ passes the additional review
checks R}`. The aim is to exclude more unacceptable contributions from what passes,
while retaining acceptable ones. This describes extending the combined system's
requirements; it does not claim that the existing reviewers achieve that aim.
Tests can miss specification failures, and automated review can reject a change
incorrectly. Both kinds of error matter.

Two distinctions remain explicit:

- **Solutions and acceptance:** S consists of diffs that compile and accomplish the
  stated task p. A_t consists of those the community would merge without requiring
  revision. This distinction assumes p does not already encode all library standards.
  Several differently preferred solutions can be acceptable. The preference relation
  does not determine an acceptance threshold by itself. Required changes can become
  checks that narrow S_R; optional preferences can guide improvements within it.
- **Conventions:** contextual practices supply reasons for preferences and, when
  treated as requirements, constrain acceptance. Their scope, period, exceptions
  and force must be discovered. A census entry is a candidate description of a
  practice, not a fully validated rule.

This clarifies the intended meanings; it does not claim to recover A_t from the
historical data. The old phrase “the region the preference does not require leaving”
was circular. The old completeness condition, requiring one test shared by every
acceptable revision, was stronger than this account justified. It is replaced by
an aim of identifying a required change when revision is necessary. The examples
also stop treating an empty historical review as proof of acceptability.

## Main presentation

| Slides | Question or role |
|---|---|
| 1–10 | Automated checks, human review, the refined solution set, conventions and examples |
| 11–13 | Build a reviewing system; choose a solo baseline; inspect its failures |
| 14–16 | Would dedicated specialists help? Result, cost and shared-context limitation |
| 17–18 | Was the issue overlooked? What happens when the check is explicit? |
| 19–21 | What standard should apply? Convention discovery, census and favorable supply test |
| 22–24 | Can the knowledge arrive without the answer? Which applicability assumptions were wrong? |
| 25 | Related branch: generate an alternative and compare it with the submission |
| 26–29 | Independently acquired notes, whole-review test, focus and the generality example |
| 30–31 | Current status and questions for discussion |
| 32–42 | Supporting results, historical model comparison, library diagnostic and prior work |

The argument order follows the user's requested progression. It does not claim
that the studies were designed in this chronological order. “Models make similar
decisions regardless of focus” is deliberately narrowed to what the records show:
reviewers can inspect the relevant object, or receive a specific check, without
producing the maintainer's request. Pruning, contracts, missing alternatives and
judgment all occur in the record. E13 in the [evidence register](evidence.md) gives
the distinctions and the development-set limitations.

The design-space section is removed. MathlibPR, SWR-Bench/SWE-PRBench, Di Biase,
Tricorder/AutoCommenter and ProofJudge appear at the questions they bear on, before
our results. The former comparison tables remain in backups 41–42.

## Why comparisons are a branch, rather than the whole narrative

The formulation suggests producing an alternative δ′ and comparing it with δ.
That requires both a relevant pair and a sound judgment of the difference. A
preference for δ′ still does not imply that δ is unacceptable or worth revising.
ProofJudge studies supplied pairs; our reconstruction experiment tested one route
for generating alternatives and supplying them to an ordinary reviewer. It did not
meet the main recovery criterion, though some proposals transferred. It is not a
negative result about all pairwise judgment. E14 records the exact experiment.

## Contemporaneous motivation for conventions

- **10–11 September:** the [drift plan](../docs/plans/2026-09-10-convention-drift-mechanics.md)
  addressed missed evolving idioms. The [catalogue](../docs/research/mathlib-convention-catalogue.md)
  sought a denominator beyond a few familiar examples. Early interpretations in
  those records are historical hypotheses.
- **29 September:** [conventions-nature](../docs/todo/conventions-nature.md), recorded
  in `b291e80d`, quotes the user's question about “what conventions hold at a given
  point and in a given window/scope.” The design-ask reading found principles behind
  30/31 asks but only eight documented. This motivated count, scope, conflict and
  maturity studies.
- **30 September:** the [residual audit](../results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md)
  and [replan](../docs/plans/2026-09-30-post-carryover-replan.md) identified knowledge
  supply as a lever at already-inspected objects, alongside trying concrete checks.
- **4 October:** the [ceiling brief](../docs/todo/conventions-ceiling-probe.md), recorded
  in `898a7be5`, requested a favorable test before further designs. Entries were
  deliberately selected from target asks. Its positive result motivates transfer
  experiments; it is not a strict upper bound on all possible review systems.

All earlier decks remain preserved. The immediately preceding original-led version
is in commit `7ff09a23`; the preferred [October source](../supervisor_update_2026-10/slides.md)
and [detailed November reference](slides.md) are unchanged. No new model runs or
literature searches were performed for this revision.
