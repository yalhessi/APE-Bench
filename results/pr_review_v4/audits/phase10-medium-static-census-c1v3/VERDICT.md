# Census under annotation protocol v3: the C1 gap is real, and now attributable

*2026-08-05. Re-ran the static census after extending the transformation vocabulary from 5
to 11 classes. Judge-free; consumes one medium look under the standing rule.*

## Headline: my hypothesis was wrong

I predicted that C1 = 15/40 understated method-expressibility because the vocabulary could
not express half the maintainer acts. **The number barely moved.**

| | protocol v2 | protocol v3 |
|---|---:|---:|
| transformation abstentions | 21/43 | **3/43** |
| **C1 (included)** | 15/40 | **15/40** |
| **C2 (included)** | 5/40 | **5/40** |
| C1 outside the dev PR | 9/26 | 9/26 |
| C2 outside the dev PR | 0/26 | **0/26** |
| decision | `static_reachability_rejected` | `static_reachability_rejected` |

Resolving 18 abstentions changed C1 by zero. The reason is structural: C1 requires a
**method contract** to cover the (issue, transformation) pair, and I deliberately extended
only the annotation protocol, not the contracts. Newly classified obligations therefore
still fail C1 — correctly, because we genuinely have no method for those acts.

**The C1 gap is not a measurement artifact. It is missing methods.** That is a cleaner and
more useful conclusion than the one I set out to confirm.

## What the fix did buy: attribution

Under v2, 21 obligations were "unclassifiable" — uninformative, and impossible to
prioritise against. Under v3 every gap names the maintainer act we cannot serve:

| issue class | transformation | obligations | distinct PRs |
|---|---|---:|---|
| `style_norm_violation` | `reformat_source` | **3** | **3** — 33066, 33294, 33305 |
| `documentation_gap` | `edit_documentation` | 3 | 2 — 33066, 33321 |
| `duplicate_implementation` | `extract_shared_declaration` | 2 | 2 — 33145, 33421 |
| `proof_simplification` | `rewrite_proof` | 2 | 2 — 33145, 33285 |
| `correctness_policy` | `remove_declaration` | 2 | 1 — 33149 |
| `scope_placement` | `relocate_declaration` | 1 | 1 — 33362 |
| others | | 3 | |

This is the first time the project has had a ranked, evidence-derived list of *which
method to build next* rather than a family-level guess.

## The gate is now reachable by one method

The reachability gate needs ≥3 C2 obligations outside the dev PR, across ≥2 PRs, via ≥2
implementations. `(style_norm_violation, reformat_source)` alone supplies **3 obligations
across 3 PRs**, and its three obligations need three different implementations:

| obligation | mechanical signal | measured false positives across all 16 medium PRs |
|---|---|---|
| PR33305 "wrap the overly long doc comment line" | 1 line >100 chars | **0** — including all 3 control PRs |
| PR33294 "replace `Order.IsNormal.map_iSup h …` with `h.map_iSup …`" | dot-notation-eligible call site | to measure |
| PR33066 "insert a blank line after `section …` and move the `variable`" | section/variable layout | to measure |

Adding `(correctness_policy, remove_declaration)` — the PR33149 axioms, **19 targets with
`declaration_kind == axiom` and 0 anywhere else in medium** — gives 5 obligations across 4
PRs via 4 implementations, clearing the gate with margin.

## Protocol changes, and the two ordering bugs found

Six classes added, derived from the leading-verb distribution of all 92 judgeable
interventions across the 75-PR corpus: `rewrite_proof`, `extract_shared_declaration`,
`edit_documentation`, `reformat_source`, `relocate_declaration`, `remove_declaration`.

Two bugs were caught by regression-checking against v2 rather than by inspection:

1. **`"shared"` as an extraction marker** matched *"the **shared** grind-based
   formulation"* in six resolution criteria, misclassifying six proof rewrites as
   extractions. Markers must be act-bearing phrases, not ordinary adjectives; `"into a"`
   was tightened for the same reason.
2. **`remove_declaration` preempting `replace_with_repository_declaration`** flipped
   PR33066 ("Delete the custom definition … and instead construct … using the **existing
   constructor** `ContinuousAlgEquiv.mk`") from C1 true to false. That ask is a replacement
   whose deletion is a consequence. The removal rule is now narrow — it fires ahead of
   repository reuse only for policy-forbidden constructs (`axiom`, `sorry`), which is what
   PR33149 actually is — and a general removal rule sits after it.

All five frozen C2 hits classify identically under v2 and v3, verified explicitly.

## Standing caveats

- **v3 numbers are comparable only to v3 numbers.** The v2 census stays as recorded.
- The extension changed C1 for three obligations, all in the direction of a more accurate
  act (two axiom removals, one generalisation). None affected C2.
- 2 obligations still abstain and remain in the human-audit queue.
- This consumed a medium look. The next census run should follow the *methods* being
  built, not further protocol tuning.
