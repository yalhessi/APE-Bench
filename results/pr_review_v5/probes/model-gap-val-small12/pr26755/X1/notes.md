# Review notes: PR #26755 (remove `noncomputable` from Set/Finset Monoid instances)

## What I did

1. Read brief.md, pr.md, model.md, diff.patch. The PR only drops `noncomputable` from 11 pointwise
   declarations and deletes one `#adaptation_note` (lean4#7824, nightly-2025-04-07) on `Finset.monoid`.
2. `lean_verify_edit` with no edit on both changed files: `Set/Basic.lean` compiles, `Finset/Basic.lean`
   compiles, no errors or warnings.
3. Control probe: added `def testNoncompProbe : Nat := Classical.choice ⟨0⟩` to Finset/Basic.lean. The
   tool reported the codegen error ("consider marking definition as 'noncomputable'"), so it does catch
   a missing `noncomputable`. A successful edit that drops the modifier therefore means the declaration
   really is computable.
4. Searched for leftover `noncomputable` and `#adaptation_note`s in the Pointwise area and library-wide.

## Object by object

- `command in Basic.lean` (removed adaptation note, Finset/Basic): the removal is right, because
  `Finset.monoid` now compiles without `noncomputable`. An identical note is still on `Finset.mulAction`
  in `Mathlib/Algebra/Group/Action/Pointwise/Finset.lean`. It is the only remaining copy of that
  lean4#7824 note in the library, and it is now false. Removing it together with `noncomputable`
  compiles (finding 2). A probe in that file (`def ... := Finset.monoid`, `def ... := Set.monoid`)
  compiled, which confirms the check ran against the PR's computable versions.
- `Finset.monoid`: fine; the file compiles. The same file still has `noncomputable` on
  `Finset.commMonoid`, `Finset.divisionMonoid`, `Finset.divisionCommMonoid` and `Finset.coeMonoidHom`.
  Each can be dropped, both separately and all at once (finding 1).
- `Set.one`, `Set.singletonOneHom`, `Set.involutiveInv`, `Set.singletonMulHom`, `Set.mulOneClass`,
  `Set.singletonMonoidHom`, `Set.monoid`, `Set.commMonoid`, `Set.divisionMonoid`,
  `Set.divisionCommMonoid`: all compile without `noncomputable` (the whole-file check passed, and the
  `to_additive` versions are generated in the same file). No `noncomputable` is left in
  `Set/Basic.lean`. Nothing to request here.
- Downstream: `Set.mulAction` (Action/Pointwise/Set/Basic.lean), `Set.hasDistribNeg`
  (Ring/Pointwise/Set.lean) and `Finset.distribNeg` (Ring/Pointwise/Finset.lean) each compile once the
  modifier is dropped (finding 3, advisory: this PR or a named follow-up).

## Concern families checked with nothing to request

- proof-golf: no proofs changed.
- generalization: no statements changed.
- duplication: nothing new is introduced.
- naming: no renames.
- documentation: no docstrings changed. The pre-existing "locale `Pointwise`" wording in `Set.one`'s
  docstring and the trailing space in `Finset.monoid`'s additive docstring are outside this chore's scope.
  I am not requesting either.
- style: the diff only drops modifiers, and formatting is unchanged.
- correctness: both files compile. Removing `noncomputable` cannot break a dependent. Zulip context
  (Kim Morrison, 2025-04-08/09) says these `noncomputable`s were temporary lean4#7824 churn, which is
  consistent with undoing them.
- The PR description could not be recovered, so I make no claim about it.

## Findings written: 3 (all advisory)
