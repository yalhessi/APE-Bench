# Review notes: PR #26755 (remove `noncomputable` from Set/Finset Monoid instances)

## Method
- Read brief.md, pr.md, model.md and diff.patch. Every change is either the removal of the
  `noncomputable` modifier or the deletion of one `#adaptation_note`. No body, statement, name or
  docstring changes.
- Baseline: `lean_verify_edit` with no edit, on both changed files. Both compile as the PR leaves
  them (compiles=true, no errors).
- Controls, to make sure a "success" from the verifier means the code generator accepted the
  declaration:
  - Adding `def testNCControl : ℕ := Classical.choice ⟨0⟩` in Finset/Basic.lean failed with
    "not supported by code generator; consider marking definition as 'noncomputable'".
  - In the downstream file GroupWithZero/Action/Pointwise/Finset.lean, a `def` that depends on a
    `noncomputable def` failed with "failed to compile definition ... depends on ..., which is
    'noncomputable'".
  - So computability is checked, in changed files and downstream files alike.
- Searched for leftover `noncomputable`, and for leftover copies of the nightly-2025-04-07 /
  lean4#7824 adaptation note, across the Pointwise directories and all of Mathlib (content_search).
- Zulip context: the new compiler landed in June 2025, and there are several threads saying it no
  longer needs such `noncomputable`s. The #23806 thread says exactly two adaptation notes were added
  for these noncomputables: `Finset.monoid` and `Finset.mulAction`.
- precedent_search on the `Set.monoid` code returned nothing relevant.

## Objects

- **`command in Basic.lean` (the deleted `#adaptation_note` above `Finset.monoid`)**: correct to
  delete, because `Finset.monoid` no longer needs `noncomputable`. Its twin on `Finset.mulAction`
  in Action/Pointwise/Finset.lean is still there (finding 2).
- **`Finset.monoid`**: the `noncomputable` removal is fine; the file compiles. Nothing else to ask
  of the declaration itself. The docstring's trailing space in the additive string
  ("if `α` is. ") is pre-existing, so not raised.
- **Rest of Finset/Basic.lean**: `Finset.commMonoid`, `Finset.divisionMonoid`,
  `Finset.divisionCommMonoid` and `Finset.coeMonoidHom` keep `noncomputable`, but all four compile
  without it (one verified edit covering the whole span). Finding 1.
- **`Set.one`**: the removal is fine. The docstring says "locale `Pointwise`" (Lean 3 wording),
  but that is pre-existing and not touched here, so not raised.
- **`Set.singletonOneHom`, `Set.singletonMulHom`, `Set.singletonMonoidHom`**: the removals are
  consistent across the family, and the file compiles. Nothing to request.
- **`Set.involutiveInv`**: the removal is fine. The `@[to_additive (attr := simp)]` on an instance
  is pre-existing and not the PR's concern.
- **`Set.mulOneClass`, `Set.monoid`, `Set.commMonoid`, `Set.divisionMonoid`,
  `Set.divisionCommMonoid`**: the removals are fine and consistent. No `noncomputable` is left in
  Set/Basic.lean. Nothing to request.
- **Downstream declarations outside the diff**: `Finset.mulAction` still has the stale
  adaptation note and `noncomputable` (finding 2). `Set.mulAction` and the other pointwise
  DistribNeg / DistribSMul / DistribMulAction / MulDistribMulAction instances, plus
  `Submodule.pointwiseSetMulAction`, all compile without `noncomputable` (finding 3, advisory,
  possibly for a follow-up).
- Noticed but not raised, because it is unrelated to this PR: `Filter.mulDistribMulActionFilter`
  in Order/Filter/Pointwise.lean is typed `MulDistribMulAction α (Set β)` instead of `Filter β`.
  This is a pre-existing oddity.

## Concern families checked
- proof-golf, generalization, naming: no proof, statement or name changes, so nothing applies.
- duplication: none.
- documentation: the deleted note was correctly removed; the stale twin is finding 2.
- style: the diff is clean.
- scope: the incomplete cleanup is findings 1 and 3.
- correctness: both files compile, and the removals are valid (verified with the codegen controls).
