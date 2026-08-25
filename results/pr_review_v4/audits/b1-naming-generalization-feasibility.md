# B1 feasibility probe: what a subject-general naming checker would reach

*Offline probe, 2026-08-05. No model calls. Estimates the C2 ceiling of generalizing
`naming_contrast` before building it, so the build decision rests on a number rather than
an intuition.*

## Question

The current naming implementation hardcodes `SUBJECT = "Set.encard"` and a `card_` →
`encard_` rename, which is why C2 is 5/40 with nothing outside the development PR. A
subject-general version would derive the subject from the target's own conclusion and
mine the snapshot for that subject's prefix norm. **Would that alone clear the
reachability gate?**

The gate requires ≥3 C2-supported obligations outside PR 33098, across ≥2 PRs, via ≥2
distinct implementations.

## Method

For each of the 8 included obligations the frozen annotation protocol classes as
`naming_convention_violation`, parse the obligation's change targets, extract the outer
left-hand side of the conclusion, and check whether a subject token is recoverable and
differs from the declaration's current leaf prefix. That is the precondition any
subject-general rule must satisfy — an upper bound, since a real rule also demands a
strong population norm and a collision check.

## Result: 2 clearly reachable outside the dev PR, not 3

| PR | declaration | conclusion LHS | subject | current prefix | verdict |
|---|---|---|---|---|---|
| 33098 | `Metric.card_maximalSeparatedSet` | `(maximalSeparatedSet ε A).encard` | `encard` | `card` | reachable (already C2) |
| 33098 | `Metric.card_minimalCover` | — | `encard` | `card` | reachable (already C2) |
| 33098 | `Metric.card_le_of_isSeparated` | — | `encard` | `card` | reachable (already C2) |
| **33145** | `Dense.continuous_upperBounds` | `upperBounds (f '' S)` | `upperBounds` | `continuous` | **genuinely reachable** — gold asks to rename to `Dense.upperBounds…` |
| **33337** | `coe_starProjection_eq_isComplProjection` | `K.starProjection.toLinearMap` | `toLinearMap` | `coe` | **genuinely reachable** — gold asks to rename to `toLinearMap_…` |
| 33337 | `coe_orthogonalProjection_eq_linearProjOfIsCompl` | `(K.orthogonalProjection : E →ₗ[𝕜] K)` | *not recoverable* | `coe` | **not reachable** by a naive head rule — the subject sits inside a coercion type ascription, and the probe's initial "hit" here was an artifact of extracting the bound variable `K` |
| 33294 | `isFundamentalSequence_of_isNormal` | — | — | — | not reachable: the ask is dot-notation restructuring, not a subject-prefix conflict |
| 33421 | `round_eq'` → `round_eq_div` | — | — | — | not reachable: primed-name disambiguation, no subject norm involved |

## Reading

**Generalizing the naming checker is necessary but not sufficient.** It would add ~2
obligations outside the development PR across 2 PRs — through a *single* implementation.
That satisfies the "≥2 PRs" condition but fails both "≥3 obligations" and "≥2
implementations", so the reachability gate would still return
`static_reachability_rejected`.

This confirms the roadmap's ordering on measured ground rather than intuition: naming
generalization must be paired with at least one more family. The largest uncovered
classes are style-norm (5 obligations) and docs (3), which is where the second
implementation should come from.

**One bounded extension is worth pricing separately.** Making the subject extractor
understand coercion type ascriptions (`(x : T)`) would recover the third 33337 obligation
and take naming to 3 outside the dev PR. That is a small, well-scoped change to
`outer_lhs`/subject inference rather than a new family — likely the cheapest single
increment toward the gate, though still short of the ≥2-implementations condition on its
own.

**Two of the eight naming obligations are out of reach of any prefix-norm rule** (33294
dot-notation, 33421 primed-name disambiguation). They are naming asks that no
subject-conditioned convention expresses, so they belong to a different method, not a
broader implementation of this one.

## Caveat

This is an upper bound on a precondition, not a prediction of C2. A real rule additionally
requires a strong snapshot population norm for the derived subject (the current rule
demands ≥20 supporting declarations at ≥80% with ≤5% conflicts) and a collision check.
Whether `upperBounds` and `toLinearMap` have populations that strong is unverified here —
that check needs the snapshot scan, and it can only lower this number.

Reproduce: `scratchpad/b1_probe.py` (probe source retained with the session artifacts).
