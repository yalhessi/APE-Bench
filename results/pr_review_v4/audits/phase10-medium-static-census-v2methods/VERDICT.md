# Reachability gate CLEARED: `authorized_for_paid_smoke`

*2026-08-05. First time the pre-registered gate has passed. Judge-free measurement; two new
methods and two new implementations, both mechanical.*

## Result

| | v1 methods (protocol v3) | **v2 methods** |
|---|---:|---:|
| C1 (included) | 15/40 | **20/40** |
| C2 (included) | 5/40 | **7/40** |
| C1 outside dev PR | 9/26 | **14/26** |
| **C2 outside dev PR** | **0/26** | **3/26** |
| distinct PRs outside dev | 0 | **2** — 33149, 33305 |
| distinct implementations outside dev | 0 | **2** |
| decision | rejected | **`authorized_for_paid_smoke`** |

All three gate conditions met: ≥3 C2 obligations outside the development PR (3), across ≥2
PRs (2), via ≥2 implementations (2).

## What was added

Two methods, each with one implementation, both decidable from the change target alone —
no norm mining, no retrieval, no model, no snapshot scan.

| method | implementation | rule |
|---|---|---|
| `lint_norm.v1` | `lint_norm.line_length.v1` | a reviewed line exceeds Mathlib's 100-character `text_width` limit |
| `repository_policy.v1` | `repository_policy.forbidden_construct.v1` | the PR introduces an `axiom` (or leaves a `sorry`) that was not there before |

Contracts: `lint_norm.v1` covers (`style_norm_violation`, `reformat_source`);
`repository_policy.v1` covers (`policy_violation` ∪ `correctness_policy`) ×
(`remove_declaration` ∪ `apply_repository_policy`).

## Precision, measured before the methods were written

Across all 16 medium PRs and 2,041 capability assessments:

| implementation | supported assessments | PRs | control PRs |
|---|---:|---|---|
| `lint_norm.line_length.v1` | 1 | 33305 | **none** |
| `repository_policy.forbidden_construct.v1` | 19 | 33149 | **none** |

Zero assessments failed. The line-length rule fires on exactly the one line PR 33305's
maintainer asked about, and nowhere else in the corpus; the policy rule fires on exactly
the 19 axiom declarations PR 33149's maintainer asked to remove, and nowhere else. Control
safety — the property that distinguishes the deterministic arm — is intact.

Two design choices carry that precision:

- **Only `reviewed_code` is examined.** A pre-existing long line is not this review's
  business. Restricting to what the PR touched is what keeps the rule silent on controls
  rather than reporting whole files.
- **Introduction, not presence.** A forbidden construct is reported only when the PR adds
  it; an `axiom` merely being moved is not a finding.

## One bug worth recording

The line-length implementation initially produced **no** C2 hit despite firing correctly.
Cause: it declared `reviewed_declaration` as its required input, and PR 33305's target is a
`module_doc` — not a declaration — so the capability assessment returned `missing_input`,
which overrides `supported`.

The fix was a new input kind, `reviewed_source`, available for any target with reviewed
content. This is a real distinction rather than a workaround: lint rules apply to whatever
the PR touched, while retrieval-based methods genuinely need a parsed declaration. Had the
assessment silently reported `unsupported_shape` instead of `missing_input`, the cause
would have been much harder to find — the terminal-state taxonomy earned its keep here.

## What this does and does not license

**Does:** a four-PR paid smoke may now be pre-registered for this arm (33098, 33145, 33337,
33438 per the Phase 10 design), because the arm can demonstrably reach obligations beyond
the PR it was built from.

**Does not:**

- It does not show these methods find anything *hard*. Line length and axiom introduction
  are the two most mechanical signals in the corpus. The gate tests reachability, not
  value, and it was explicitly designed to be asymmetric — passing authorises testing only.
- It does not move the 71% convention class. `style_norm_violation` is served here by a
  single formatting rule; the 37 style interventions in the corpus are mostly not line
  length.
- It does not touch the norm-establishing problem (PR 33337's `toLinearMap_` at 17%
  prevalence), which remains the structural blocker for conventions.

## Provenance

- Treatment: `inputs/pr_review_v4/treatments/systematic-opportunities-v2-medium`
- Registries: method `systematic-opportunity-methods/2`, implementation
  `implementation-capability-registry/2`, contracts `method-expression-contracts/2`
- Annotation protocol: `obligation-expression-class/3` (unchanged from the previous run)
- The v1-method census under the same protocol stays at
  `audits/phase10-medium-static-census-c1v3` for comparison; numbers are comparable
  because only the methods changed.
