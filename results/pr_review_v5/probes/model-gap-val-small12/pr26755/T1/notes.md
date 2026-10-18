# Review notes: PR #26755 (remove `noncomputable` from Set/Finset Monoid instances)

## What I did

1. Read `pr.md`, `model.md` and `diff.patch`. The PR deletes `noncomputable` from 11 declarations
   (10 in `Set/Basic.lean`, `Finset.monoid` in `Finset/Basic.lean`) and removes the
   `#adaptation_note /-- nightly-2025-04-07` above `Finset.monoid`.
2. Compiled both changed files as the PR leaves them (`lean_verify_edit`, no edit):
   `Finset/Basic.lean` and `Set/Basic.lean` both `compiled`, with no errors and no warnings.
3. Looked for every `noncomputable` left in `Mathlib/Algebra/Group/Pointwise`, and for any other
   copy of the adaptation note (searched `7824`). Then surveyed pointwise-adjacent directories
   (GroupWithZero, Module, Order/Filter, Data/Set, Ring) for `noncomputable` defs on Set/Finset
   structures.
4. Tested each candidate removal with `lean_verify_edit`. As a control, a `def` built on
   `Classical.choice` in a downstream file was rejected with "consider marking definition as
   noncomputable". So the tool checks computability, and the downstream files are compiled
   against the PR's rebuilt `Set/Basic`.
5. Searched Zulip: the 2025-04-09 #nightly-testing thread says adaptation notes went on exactly the two
   `noncomputable`s flagged in review. Ran one precedent search (no relevant hits).

## Object by object

- **`command in Basic.lean` (the adaptation note removed from Finset/Basic):** the removal is
  correct now that `Set.monoid` is computable. Its twin above `Finset.mulAction` in
  `Algebra/Group/Action/Pointwise/Finset.lean` is still present and now false, so I filed a finding.
  Removing that note and the `noncomputable` compiles.
- **`Finset.monoid`:** the change compiles. No issue with the change itself. But the same file still has
  `noncomputable` on `Finset.commMonoid`, `Finset.divisionMonoid`, `Finset.divisionCommMonoid` and
  `Finset.coeMonoidHom`. Each compiles without it, and all four removed together also compile.
  The Set side of the PR does fix the corresponding `commMonoid`, `divisionMonoid` and
  `divisionCommMonoid`, so the Finset side is left inconsistent. I filed four findings.
- **`Set.one`, `Set.mulOneClass`, `Set.monoid`, `Set.commMonoid`, `Set.divisionMonoid`,
  `Set.divisionCommMonoid`, `Set.involutiveInv`:** correct, and the file compiles. No `noncomputable`
  remains in `Set/Basic.lean`. Docstrings and `to_additive` strings are unchanged by the PR. "locale"
  in the `Set.one` docstring is old Lean 3 wording, but it predates the PR and is outside its diff,
  so I did not raise it.
- **`Set.singletonOneHom`, `Set.singletonMulHom`, `Set.singletonMonoidHom`:** correct. Nothing to request.
- **Naming, generalization, duplication, proof-golf:** the PR changes no statement, name or proof,
  so none of these applies.
- **Downstream follow-through (scope).** These definitions still carry `noncomputable`, and each now
  compiles without it in the reviewed workspace. I filed them as advisory findings:
  - `Set.mulAction` (Action/Pointwise/Set/Basic.lean);
  - `Set.hasDistribNeg` (Ring/Pointwise/Set.lean, built on `Set.involutiveNeg`);
  - `Set.distribSMulSet`, `Set.distribMulActionSet` and `Set.mulDistribMulActionSet`
    (GroupWithZero/Action/Pointwise/Set.lean);
  - `Finset.distribSMul`, `Finset.distribMulAction` and `Finset.mulDistribMulAction`
    (GroupWithZero/Action/Pointwise/Finset.lean);
  - `Finset.distribNeg` (Ring/Pointwise/Finset.lean);
  - the `SetSemiring` instances and `imageHom` (Data/Set/Semiring.lean);
  - `Submodule.pointwiseSetMulAction` and `pointwiseSetDistribMulAction`, which must go together;
  - `Filter.mulDistribMulActionFilter`.

  Caveat: the Finset ones compiled even with their Set or Finset dependencies still
  `noncomputable`, so this PR does not strictly enable them. They are the same cleanup.
- **Seen but not raised:**
  - `noncomputable instance : Inhabited (SetSemiring α)` also compiles without the modifier. It does
    not depend on the pointwise structures, so it is outside this PR's theme.
  - `Filter.mulDistribMulActionFilter` is stated on `Set β`, not `Filter β`, so it looks like a
    duplicate of `Set.mulDistribMulActionSet`. That is pre-existing and unrelated to the PR.

## Findings: 13

The strongest are the stale adaptation note on `Finset.mulAction` and the four remaining
`noncomputable`s in `Finset/Basic.lean`. The rest are verified downstream cleanups, filed as
advisory.
