# gpt_5.2 as judge: more deterministic, but it collapses the rubric

*Run 2026-08-05, same 18 pairs, same budget (`max_tokens=4000 / thinking_budget_tokens=3000`),
`sample_count=3`. Complete coverage (18/18). Artifacts: `budgeted-rep-gpt-5-2-{1,2,3}/`.*

## Short answer

**No — the verdict is not the same, and gpt_5.2 should not replace `gpt_5_mini` as the
judge.** It fixes the determinism problem and it fixes `gpt_5_mini`'s stable error, but it
does so by applying a *different rubric*: it collapses `issue_match` into
`resolution_match`, which is the exact distinction the two-level design exists to make.

## What improved

| | gpt_5_mini | gpt_5.2 |
|---|---|---|
| split-vote pairs (self-disagreement) | 4/18 | **0/18** |
| self-agreement ceiling | 90.1% | **100%** |
| bimodal obligations | 2 (`…4bfe0de1d5f6`, `…0898b0478443`) | **none** |
| verdict on `gpt_5_mini`'s stable error (`…e373aeb72a4b`) | wrong (True 3/3) | **right (False 0/9)** |

On its own terms this is a better-behaved judge: perfectly reproducible across samples,
and it correctly rejects the pair where `gpt_5_mini` voted `issue=True` while its own
stated reason said the candidate did not do what was asked.

## What broke

| | gpt_5_mini | gpt_5.2 | script (mini, 1 sample) |
|---|---|---|---|
| pairs with `issue_match` | 9/18 (50%) | **1/18 (6%)** | 6/18 (33%) |
| pairs with `resolution_match` | 4/18 | 1/18 | — |
| pairs where `issue_match == resolution_match` | 13/18 | **18/18** | — |
| "same issue, different fix" verdicts | 5 | **0** | — |

The last two rows are the finding. The rubric says explicitly:

> issue_match … **A different fix may still issue-match.**
> resolution_match: true only when issue_match is true **and** the candidate's concrete
> transformation achieves the maintainer's requested result.

`gpt_5.2` never once returned `issue=True, resolution=False`. For it the two levels are
identical on all 18 pairs — the two-level rubric has degenerated into a single level, and
the level it kept is the stricter one.

## The mechanism, in its own words

Two cases where `gpt_5_mini` says True and `gpt_5.2` says False, both about simplifying
*the same declaration's proof*:

| | |
|---|---|
| **Gold** | "Simplify `maximalSeparatedSet_subset` using grind and the requested `IsSeparated.empty` support." |
| **Candidate** | the same proof "manually splits on `packingNumber ε A ≠ ⊤` … repetitive boilerplate"; asks for a `by_cases … <;> simp` refactor |
| `gpt_5_mini` | True — same target, same defect, different tactic |
| `gpt_5.2` | False — "the gold requires a **grind-based** proof …, while the candidate proposes a **by_cases+simp** refactor" |

| | |
|---|---|
| **Gold** | "Simplify the maximal-separated-set cardinality proof with the requested grind-based treatment." |
| **Candidate** | the same proof "is a `simp`-then-`exact` … can be expressed as a single `by simpa`" |
| `gpt_5_mini` | True |
| `gpt_5.2` | False — "the gold asks for a **grind-based** concise formulation …, while the candidate asks for a **single by simpa** rewrite" |

In both, the two parties identify the same problem in the same declaration and propose
different tactics for it. That is the textbook `issue_match=True, resolution_match=False`
case. `gpt_5.2` scores the *fix* and reports the result as the *issue*.

Only the third divergent case (`…0898b0478443`, dead-code vs binder form) is genuinely
borderline, and there `gpt_5.2`'s stricter reading is defensible.

## Why this matters more than the determinism win

Adopting `gpt_5.2` would cut measured issue recall by roughly **a factor of 5** (50% → 6%
of pairs) — not because the system got worse, but because the metric changed definition.
Every historical number in this project was measured under the two-level reading. Swapping
in a judge that collapses the levels would silently redefine "issue recall" as "resolution
recall" and make all prior results incomparable.

The determinism gain is real but cannot be bought at that price: a judge that is perfectly
reproducible about the wrong quantity is worse than one that is noisy about the right one.

## Recommendation

1. **Keep `gpt_5_mini` as the judge of record.** The R0 conclusions stand:
   `sample_count=3`, ~11% bimodal pairs, ±1 obligation at n≈8 (≈±12pp).
2. **Do not read this run as "gpt_5.2 is a worse judge."** It is a stronger model applying
   a stricter rubric than the one it was given. The defect is in prompt adherence on the
   `issue_match` clause, not in capability — as evidenced by it being the only arm to get
   `…e373aeb72a4b` right.
3. **Try a rubric-clarification pass before abandoning it.** The single sentence "A
   different fix may still issue-match" is evidently too weak for this model. An explicit
   worked example of `issue=True, resolution=False` in the prompt is the cheapest thing to
   test, and if it restores the two-level behaviour, `gpt_5.2` becomes the better judge on
   every axis measured here (deterministic, and right on the hard pair).
   That is a **new rubric version** and would require re-baselining — it must not be
   slipped into the current one.
4. **Keep both runs.** `gpt_5.2`'s verdicts are the closest thing we have to an
   independent second opinion on the contested pairs, and it agrees with the script arm
   that `…e373aeb72a4b` is not a match — which retires that question.

## What this adds to the standing lesson

Round 1: same prompt ≠ same judge (decode parameters).
Round 2: … nor the same submission protocol.
Round 3: an equivalence gate must be calibrated to the judge's own self-agreement.
**Now: a stronger model is not a drop-in judge upgrade. Judge swaps change the metric's
definition unless two-level agreement is verified first, and `issue==resolution` on every
pair is the diagnostic that catches it.**
