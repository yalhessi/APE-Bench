# Subject-general naming checker: measured reach, and why it stops where it does

*2026-08-05. Built `operators/naming_norm.py` and measured it against the real Mathlib
snapshots for every naming obligation in the medium benchmark. No model calls — the whole
measurement is a snapshot scan plus lexical analysis, so it carries no judge noise.*

## What was built

The frozen `naming_contrast` hardcodes `SUBJECT = "Set.encard"` and the single rename
`card_ → encard_`. `naming_norm` instead derives the subject from the target's own
conclusion and mines the snapshot for *that* subject's prefix convention:

- **projection** — `(maximalSeparatedSet ε A).encard` → `encard`
- **application head** — `upperBounds (f '' S)` → `upperBounds`
- **coercion ascription** — `(K.orthogonalProjection : E →ₗ[𝕜] K)` → `→ₗ`
  (the B1 probe's naive head rule read the bound variable `K` here, which is why it
  over-counted this obligation as reachable)

A rename is proposed only when the corpus has a *strong* convention (≥20 supporting
declarations, ≥80% share) and the current prefix is not itself well attested for that
subject. The frozen operator is untouched: it produces the 0.9.1–0.9.3 releases Phase 9
consumes.

Scanning PR 33098's base: **7,409 files, 6,387 distinct subjects, 237 with a strong prefix
norm** — so the rule has real material to work with, and `encard` reproduces at 84/88.

## Measured reach on the 8 medium naming obligations

| PR | subject | strong norm? | reachable | note |
|---|---|---|---|---|
| 33098 ×3 | `encard` | yes (84/88) | **yes** | reproduces the frozen operator |
| 33145 | `upperBounds` / `lowerBounds` | yes (27/27, 25/25) | **yes** | the one new obligation |
| 33294 | `IsFundamentalSeq` | no | no | ask is dot-notation restructuring |
| 33337 ×2 | `toLinearMap` / `→ₗ` | **no** | no | see below |
| 33421 | `round` | yes | no | correctly silent: ask is primed-name disambiguation, prefix already conforms |

**Outside the development PR the generalization reaches exactly 1 obligation, on 1 PR, via
1 implementation.** The reachability gate requires ≥3 obligations across ≥2 PRs via ≥2
implementations, so it remains `static_reachability_rejected` — and by a wider margin than
the B1 probe estimated (which predicted 2, or 3 with the ascription fix).

## Why PR 33337 is unreachable — the finding that matters

The maintainer's ask is explicit: rename "using the `toLinearMap_...` naming convention".
But at that PR's base snapshot:

| subject | members | prefix distribution |
|---|---|---|
| `toLinearMap` | 121 | `toLinearMap` 21 (**17%**), `coe` 7, `map` 5, `comp` 4, … |
| `→ₗ` (coercion) | 124 | **`coe` 48 (39%)**, `toLinearMap` 9, … |

**The corpus does not yet exhibit the convention the maintainer is asking for.** `coe_` is
still the plurality spelling; `toLinearMap_` is a minority at 17%. The maintainer is
*establishing* a norm, not *enforcing* one.

A frequency-based checker cannot fire here by construction — it would have to argue
against the current majority. Raising the thresholds would not help; lowering them to 17%
would make the rule fire on essentially any minority spelling and destroy the control
safety that makes the deterministic arm valuable.

This is the **`grind` phenomenon reappearing in the naming family**. Phase 6 was deferred
because the corpus contained too little evidence for an emerging tactic norm; the same
structure defeats naming here. It is direct evidence for the roadmap's L0
norm-provisioning layer: **a nontrivial share of maintainer naming asks are
norm-establishing, and no amount of implementation breadth reaches them — they need a
dated norm source that can represent a convention before it is dominant.**

## A second, smaller honesty note

For PR 33145 the rule identifies the issue correctly (the prefix should be `upperBounds`,
not `continuous`) but proposes `Dense.upperBounds_upperBounds`, where gold asks for
`Dense.upperBounds_image`. The mechanical rule keeps the original remainder. That is an
issue-level match with a resolution-level miss, and it is the expected ceiling of a
prefix-rewriting rule: choosing the *rest* of the name requires understanding what the
lemma says, not just what it is about.

## Consequences for the plan

1. **Naming generalization is worth keeping** — it triples dev-PR reach into a principled
   rule and adds one real obligation — but it does not move the gate, and now demonstrably
   cannot on its own.
2. **The second implementation must come from a different family.** Style-norm (5
   obligations) and docs (3) remain the largest uncovered classes and do not depend on
   frequency conventions.
3. **The naming residual is a norms problem, not a breadth problem.** 2 of 8 naming
   obligations are unreachable by any prefix rule (dot-notation, primed-name
   disambiguation) and 2 more are norm-establishing. Only 4 of 8 are the kind of
   convention-enforcement a population rule can express, and 4 of those 4 are now reached.
4. **The measurement cost nothing and carries no judge noise**, which is the argument for
   continuing to make C2 the decision variable rather than recall.
