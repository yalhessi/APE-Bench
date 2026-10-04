# Review notes: PR #34091 (generalize infinite pigeonhole principle)

Inputs read: `pr.md`, `model.md`, `diff.patch`. The workspace root for the tools is `target/`. I
read `target/Mathlib/SetTheory/Cardinal/Pigeonhole.lean` in full, as the PR leaves it. All three
changed files compile as the PR leaves them (lean_verify_edit with no edit: `compiles: true`, no
errors).

## Object by object

- **`Cardinal.infinite_pigeonhole_card_lt`** (modified; the hypothesis moves from `ℵ₀ ≤ #α` to
  `ℵ₀ ≤ #β`).
  - The generalization is correct: when α is finite, an infinite fiber exists. The hypothesis
    `ℵ₀ ≤ #β` cannot be dropped: with #α = 2 and #β = 3 no fiber has more than 2 elements.
  - No other callers exist in Mathlib (content_search), so the signature change breaks nothing
    in tree.
  - The proof's case split is reasonable.
  - Docstring: wrong ("strictly greater than its domain's"), and it keeps the old typo "great
    than" (finding 1).
- **`Cardinal.exists_infinite_fiber`** (modified; the hypothesis moves from `Infinite α` to
  `Infinite β`, a strict strengthening).
  - The signature change is not deprecatable. That is normal Mathlib practice, and the old form
    survives as `exists_infinite_fiber'`.
  - Docstring: the same domain/codomain error (finding 2).
  - The explicit `(hβ : Infinite β)` binder is the only explicit `Infinite` binder in
    `Mathlib/SetTheory`, and both PR call sites pass `(by infer_instance)`. I request instance
    binders across the family (finding 4, construction verified).
  - The first case of its proof repeats the first case of `infinite_pigeonhole_card_lt`. That is
    addressed by the generalization (finding 6).
- **`Cardinal.exists_infinite_fiber'`** (added; exactly the old signature of
  `exists_infinite_fiber`).
  - It is used once, in `linearIndependent_le_infinite_basis`. Without it that call site would
    need a clumsy `Infinite κ` proof, so keeping it is reasonable, and I make no removal request.
  - Name: `naming_norm` could not resolve the subject, so the name is unmeasured. A primed
    variant is acceptable, so I make no rename request.
  - The docstring "requires codomain to be infinite" lacks an article ("the codomain"). That is
    too minor for a finding, and it is folded into the finding 4 construction.
- **`Cardinal.exists_uncountable_fiber`** (added).
  - The statement is correct and there is no existing duplicate: content_search for
    `uncountable_fiber` and for `Uncountable (… ⁻¹' …)` finds only this declaration.
  - Requests:
    - docstring error (finding 3);
    - golf, by splitting on ℵ₁ and dropping the redundant `Cardinal.`/`Order.` prefixes
      (finding 5, verified);
    - generalization to any regular θ, which subsumes it and `exists_infinite_fiber`
      (finding 6, verified). Regularity is necessary; the ℵ_ω counterexample is in the finding.
- **`Cardinal.le_range_of_union_finset_eq_univ`** (renamed from `..._eq_top`, `⊤` replaced by
  `Set.univ`).
  - This resolves the removed TODO.
  - The `have k` removal is correct because `exists_infinite_fiber` now needs `Infinite β`, which
    is an instance here.
  - The docstring is still accurate. Nothing to request beyond `(by infer_instance)` going away
    under finding 4.
- **Deprecated alias `le_range_of_union_finset_eq_top`**: the form and date (2026-01-17) are
  consistent with the review time (tool `as_of` 2026-01-18). The two-line layout is forced by line
  length. Nothing to request.
- **`infinite_basis_le_maximal_linearIndependent'`** (Basis/Cardinality.lean): this is only the
  rename at the call site, and it compiles. The comment after it refers to the theorem itself;
  that predates the PR and is outside its scope.
- **`linearIndependent_le_infinite_basis`** (StrongRankCondition.lean): this only switches to
  `exists_infinite_fiber'`, and it compiles. Finding 4 would drop `(by infer_instance)` here.
- **Removed doc comment / TODO**: the removal is correct, since the TODO is done.

## Other checks with no finding

- **Import.** Removing `public import Mathlib.Data.Set.Finite.Lattice` (whose
  `union_finset_finite_of_range_finite` was the only direct user) still compiles, because the
  import is transitively available. It is a public import, so removing it can affect downstream
  files, and `shake` owns that question. No request.
- **Tool searches.** `precedent_search` and `zulip_search` returned nothing that bears on this
  code.

## Constructions verified with lean_verify_edit (all success, no errors)

1. Corrected docstrings, spliced at lines 67-68, 78-79 and 95-96.
2. Instance-binder versions of `exists_infinite_fiber`, `exists_infinite_fiber'` and
   `exists_uncountable_fiber`, with the updated `le_range_of_union_finset_eq_univ`, spliced over
   lines 78-122.
3. Golfed `exists_uncountable_fiber`, by declaration replacement.
4. `infinite_pigeonhole_card_of_isRegular`, with `exists_infinite_fiber` and
   `exists_uncountable_fiber` derived from it, spliced over lines 78-105.
