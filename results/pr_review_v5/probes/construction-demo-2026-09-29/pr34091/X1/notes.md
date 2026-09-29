# Review notes: PR #34091 (reviewer X1)

Inputs read: `pr.md`, `model.md`, `diff.patch`. All tool calls went through `./ptool`. Workspace
paths live under `target/`.

## Baseline
- `lean_verify_edit` with no edit: all three changed files compile as the PR leaves them
  (`Pigeonhole.lean`, `Basis/Cardinality.lean`, `Dimension/StrongRankCondition.lean`), with no
  warnings.
- `content_search` for every changed name across `target/`: the only callers of
  `exists_infinite_fiber(')` and `le_range_of_union_finset_eq_*` are the two LinearAlgebra call
  sites the PR updates. `infinite_pigeonhole_card_lt` is used only inside Pigeonhole.lean. No other
  caller is broken by the signature changes.

## Object by object

### `Cardinal.infinite_pigeonhole_card_lt` (modified)
- The generalization from `ℵ₀ ≤ #α` to `ℵ₀ ≤ #β` is sound and strictly weaker, since `#α < #β`.
- Docstring: "strictly greater than its domain's" should say codomain's; "but" should be "and";
  "strictly great than" is a typo -> finding 1 (blocking).
- Proof: the case split plus two `infinite_pigeonhole_card` calls can be replaced by
  `mk_le_mk_mul_of_mk_preimage_le` (SetTheory/Cardinal/Order.lean:481) and `mul_lt_of_lt`, which
  gives a two-line proof. Verified with `lean_verify_edit` (success) -> finding 4 (advisory).
- Also checked, not submitted: a generalization `∃ a, c < #(f ⁻¹' {a})` for any `c < #β` (given
  `#α < #β`, `ℵ₀ ≤ #β`) compiles (a line-mode edit of lines 67-105 succeeded) and yields both this
  lemma (`c = #α`) and `exists_uncountable_fiber` (`c = ℵ₀`) as one-liners. Not a finding, because
  the golfs in findings 4 and 5 get the same simplification without adding new API, and I can't
  say a maintainer would ask for the extra lemma.

### `Cardinal.exists_infinite_fiber` (modified)
- The switch from `Infinite α` to `Infinite β` is a genuine generalization, and the only caller
  that relied on the old form now uses `exists_infinite_fiber'`.
- Docstring has the same "domain's ... domain's" error -> finding 2 (blocking).
- Binder: `(hβ : Infinite β)` is an explicit Prop-class argument. Every caller passes
  `(by infer_instance)`, and the sibling `Finite.exists_infinite_fiber` uses `[Infinite α] [Finite β]`.
  An instance-binder version of all three fiber lemmas compiled in-file -> finding 6 (advisory).
- Tried a golf of the finite-codomain case through `Finite.exists_infinite_fiber`, but that constant
  is not imported into this file ("Unknown constant"), so I dropped it. The case split that remains
  is needed: `#α < #fiber` alone does not give an infinite fiber when `α` is finite.

### `Cardinal.exists_infinite_fiber'` (added)
- The statement is the old `exists_infinite_fiber`, and the proof is correct. A primed name for the
  weaker, convenience form is acceptable. I found no existing duplicate.
- Docstring nit, not submitted because it is too minor: "requires codomain" should be "requires
  the codomain".
- `naming_norm`: subject unresolved (unmeasured).

### `Cardinal.exists_uncountable_fiber` (added)
- `declaration_search` and `content_search` found no existing uncountable-fiber lemma, so this is
  not a duplicate.
- Docstring has the same "domain's ... domain's" error -> finding 3 (blocking).
- Proof: the ℵ₁/succ rewriting and the case split can go. A three-line proof through
  `mk_le_mk_mul_of_mk_preimage_le` with bound `ℵ₀` compiled -> finding 5 (advisory).
- `naming_norm`: subject unresolved (unmeasured). The name matches its siblings.

### `Cardinal.le_range_of_union_finset_eq_univ` (renamed from `..._eq_top`) and deprecated alias
- The rename resolves the file's own TODO (`Set.univ` instead of `⊤`). The alias uses the standard
  `@[deprecated (since := "2026-01-17")] alias` form. That date is consistent with the tool's as-of
  of 2026-01-18.
- The proof is correctly shortened: the `k : Infinite (range f)` block is no longer needed, because
  `exists_infinite_fiber` now takes infinitude of the domain `β`, which is an instance. Nothing else
  to request.
- Observed, not submitted: `union_finset_finite_of_range_finite` was the only reason for
  `public import Mathlib.Data.Set.Finite.Lattice` that I could find. Pigeonhole.lean compiles with
  that import removed (verified). Not a finding, because I could not check whether downstream files
  (for example `Basis/Cardinality.lean`) rely on it transitively.

### Doc comments (modified, added, removed)
- The removed TODO comment is correctly removed along with the rename.
- The three modified or added docstrings are covered by findings 1-3. The `exists_infinite_fiber'`
  docstring nit is recorded above and not submitted.

### `infinite_basis_le_maximal_linearIndependent'` (Basis/Cardinality.lean)
- The only change is the rename at the call site. It compiles, and there is nothing to request. The
  self-referential comment below it is pre-existing and not touched.

### `linearIndependent_le_infinite_basis` (StrongRankCondition.lean)
- The call switches to `exists_infinite_fiber'`, which is correct: `Infinite κ` is not available as
  an instance there, but `Infinite (Finset ι)` is. It compiles. The only follow-up is the
  `(by infer_instance)` drop, which comes with finding 6.

## Other families checked
- Scope: all changes belong to the PR's stated purpose. There is nothing to move or split.
- Universe generalization: the module TODO ("Generalize universes of results") covers the whole
  file, so I did not ask for it here.
- `precedent_search` and `zulip_search` turned up nothing that bears directly on this code.
