# PR 27099 review notes (condition X)

## Mathlib.lean
- Checked the new import's position: `Arithmetic` sorts between `Algebra.Ring.FreeCommRing` and `Basic`, so it is correct. Nothing to ask.

## Basic.lean: header and imports
- Compared the header with the ring language file (`ModelTheory/Algebra/Ring/Basic.lean`). Main Definitions lists only the language, though the file also adds term instances, `succ`, the sum, and a structure instance. Asked for these to be listed (advisory).
- `import Mathlib.Algebra.Group.Basic` looks redundant. `add_nsmul`/`succ_nsmul` are in `Algebra/Group/Defs.lean`, and `Semantics` → `Basic` → `SetTheory.Cardinal.Basic` → `Data.Fintype.BigOperators` already imports big operators. Mathlib does not enforce minimal imports, so I did not raise it.

## presburgerFunc, Language.presburger
- These mirror `ringFunc` / `Language.ring` exactly: same `deriving DecidableEq` and `deriving IsAlgebraic`, and `Relations := fun _ => Empty`. The docstring has no final period, but neither does the sibling's, so nothing to ask.

## Zero / One / Add instances on terms
- Same shape as the ring file's instances (`Constants.term`, `Functions.apply₂`). The ring file adds `zero_def`/`add_def` lemmas, but here `realize_*` are `rfl`, so they are not needed. Nothing to ask.

## NatCast instance, natCast_zero, natCast_succ
- `Nat.unaryCast` is the right cast for a structure with no algebraic laws (`Data/Nat/Cast/Defs.lean:29`). The lemmas are stated with the raw `NatCast.natCast`, whereas siblings (`Tactic/Ring/Basic.lean:500`, `Ordinal/Basic.lean:887`) use the coercion. Asked for the coercion form.
- Considered asking for `protected` because the names match root `Nat.cast_*`/`natCast_*` lemmas. Precedent (`Ordinal.natCast_succ`, `Tropical.succ_nsmul`) is unprotected, so I did not ask.

## SMul ℕ instance, zero_nsmul, succ_nsmul
- `nsmulRec` with `rfl` lemmas is fine. The name clash with root `zero_nsmul`/`succ_nsmul` has unprotected precedent (see above). Nothing to ask.

## succ
- The definition has no result type. Asked for `: presburger.Term α` (minor). I did not ask to remove it, because the PR says the follow-up #27100 uses these for definability.

## finsum
- The name clashes in meaning with Mathlib's `finsum`/`∑ᶠ` (`Finprod.lean:96`), and the realize lemma is a `Finset.sum`. Asked for a rename to `sum` (blocking).
- Restricting to `Fintype`/univ is unnecessary. Asked for it to take `s : Finset β`.
- The foldr it builds is `List.sum`. Asked for it to be defined that way, which lets the proof use `Finset.sum_map_toList` (`Finset/Defs.lean:393`).

## Structure instance and funMap_* lemmas
- The global instance departs from the `def orderStructure` / `def compatibleRingOfRing` convention (`Order.lean:202-204`, `Ring/Basic.lean:214-218`), where both files say a global instance clashes when a `Structure` is given first. Asked for a def plus `letI`, or else a justification (advisory).
- The `.one` alternative binds an unused `v`, which the unused-variables linter flags. Asked for `_`.
- `@Structure.funMap presburger M _ _ ...` in the `funMap_*` lemmas matches the `@funMap` precedent in `LanguageMap.lean:237`. The `{v}` binder shadows the section variable `v : α → M`, which is mildly confusing but not worth a request.

## realize_zero / one / succ / add
- `rfl` proofs under `[Zero M] [One M] [Add M]` are the minimal hypotheses and match the ring `realize_*` lemmas. Nothing to ask.

## realize_natCast
- `AddMonoidWithOne` is the minimal class for `Nat.cast_succ`, and `induction n with simp [*]` is already short. Nothing to ask.

## realize_nsmul, realize_finsum
- Neither lemma needs the `NatCast` part of `...WithOne`. Asked for `[AddMonoid M] [One M]` and `[AddCommMonoid M] [One M]`.
- The `realize_finsum` proof uses `←X` without a space and `conv => rhs;`. Mathlib counts are 26840 vs 10 for the arrow spacing and 485 vs 16 for `conv_rhs`, so I asked for the fix. The longer golf to `List.sum` plus `Finset.sum_map_toList` is in the finsum finding.
