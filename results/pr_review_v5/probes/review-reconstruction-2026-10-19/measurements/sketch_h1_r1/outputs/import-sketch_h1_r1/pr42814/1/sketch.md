# Sketch: fundamental discriminants

All Lean below is unchecked.

## 1. Whether D = 1 counts
- **Choice:** include 1 (reading i): the characterization and (a) need no `D ≠ 1`; the docstring says quadratic-field discriminants are those with `D ≠ 1`.
- **Alternatives:** exclude 1 with a third conjunct `D ≠ 1`, carrying `D ≠ 1` into the characterization and (a).
- **References:** `NumberField.discr ℚ = 1` (S1); `squarefree_one` (S2) makes 1 fall out of both descriptions unless removed by hand. Recalled, not seen: OEIS A003658 lists 1 first.
- **What would decide it:** the first consumer: quadratic characters want 1 (trivial character), quadratic-field classification does not. S3 excludes units only on a reminder, no reason given.

## 2. Which description is the definition
- **Choice:** the minimality description, phrased like `Squarefree` (S2): a square factor leaving a discriminant cofactor must be a unit.
  ```lean
  def Int.IsFundamentalDiscr (D : ℤ) : Prop :=
    (D % 4 = 0 ∨ D % 4 = 1) ∧
      ∀ f E : ℤ, f ^ 2 * E = D → (E % 4 = 0 ∨ E % 4 = 1) → IsUnit f
  ```
  `D = 0` is excluded automatically (`2 ^ 2 * 0 = 0`).
- **Alternatives:** `2 ≤ f` for `IsUnit f` (equivalent); the characterization as definition; a `structure`; cofactor as `QuadraticAlgebra.discr a b` (S5).
- **References:** `Squarefree` (S2, `Algebra/Squarefree/Basic.lean:40`); witness order `f ^ 2 * E` follows S8 (`Data/Nat/Squarefree.lean:306`).
- **What would decide it:** open: conceptual definition plus `_iff`, or the computable one.

## 3. Residue-class form
- **Choice:** `D % 4 = r` (`Int.emod`, nonnegative for negative `D`), closed by `omega`.
- **Alternatives:** `D ≡ r [ZMOD 4]`; `(D : ZMod 4) = r`.
- **References:** S6 (`ZModChar.lean:97`), `QuadraticReciprocity.lean:133`, `JacobiSymbol.lean:330`; `Nat.Prime.eq_two_or_odd` (`base/Mathlib/Data/Nat/Prime/Basic.lean:41`) uses `%`.
- **What would decide it:** `%` is the pattern found; no `[ZMOD 4]` hypothesis was.

## 4. Name
- **Choice:** `Int.IsFundamentalDiscr`, lemmas `isFundamentalDiscr_*` / `IsFundamentalDiscr.*`; `%` lemmas say `emod`.
- **Alternatives:** `IsFundamentalDiscriminant`; root namespace; `FundamentalDiscr` without `Is`.
- **References:** `discr` (S1, S5); `IsCoprime` (`base/Mathlib/RingTheory/Coprime/Basic.lean:45`); `Nat.Prime` for a type-specific predicate. Recalled: `Int.emod_two_eq_zero_or_one`.
- **What would decide it:** open; nothing on naming this notion was found.

## 5. The characterization and special cases
- **Choice:**
  ```lean
  theorem isFundamentalDiscr_iff {D : ℤ} : IsFundamentalDiscr D ↔
      D % 4 = 1 ∧ Squarefree D ∨ ∃ m, 4 * m = D ∧ Squarefree m ∧ (m % 4 = 2 ∨ m % 4 = 3)
  theorem isFundamentalDiscr_iff_squarefree (hD : D % 4 = 1) :
      IsFundamentalDiscr D ↔ Squarefree D
  theorem isFundamentalDiscr_four_mul_iff {m : ℤ} :
      IsFundamentalDiscr (4 * m) ↔ Squarefree m ∧ (m % 4 = 2 ∨ m % 4 = 3)
  ```
  (a) takes a residue hypothesis; (b) the expression `4 * m`, avoiding `D / 4`.
- **Alternatives:** (a) on `4 * m + 1`; (b) with `4 ∣ D` and `D / 4`; the second disjunct as `D % 4 = 0 ∧ Squarefree (D / 4) ∧ …`, which is decidable.
- **References:** S6 versus S7 (`Algebra/Ring/Parity.lean:128`).
- **What would decide it:** whether a decidability instance is wanted, and how callers hold `D`.

## 6. Basic API
- **Choice:** `IsFundamentalDiscr.ne_zero`, `IsFundamentalDiscr.emod_four_eq_zero_or_one`, `not_isFundamentalDiscr_zero`, `isFundamentalDiscr_one` (under 1), and a prime-reduction lemma replacing `f` by a prime `p : ℕ` in the definition.
- **Alternatives:** inline the prime reduction in the proof.
- **References:** the analogue `Nat.squarefree_iff_prime_squarefree` (`base/Mathlib/Data/Nat/Squarefree.lean:47`).
- **What would decide it:** both characterization cases reuse the reduction.

## 7. Supporting facts in the base files
- **Choice:** only general facts, added: `Int.squarefree_iff_prime_squarefree` (`Squarefree n ↔ ∀ p : ℕ, p.Prime → ¬(p * p : ℤ) ∣ n`, via `Int.squarefree_natAbs`) beside its ℕ twin at `Data/Nat/Squarefree.lean:47`; cancelling an odd prime square against `4` stated as coprimality (`IsCoprime.dvd_of_dvd_mul_left`, `Coprime/Basic.lean:105`; an ℤ `coprime_two_left`, cf. `Prime/Basic.lean:145`). Mod-4 helpers stay private.
- **Alternatives:** everything private; ℤ lemmas beside S4 in `Algebra/Squarefree/Basic.lean`.
- **References:** S4, S12 (`Data/Nat/Squarefree.lean:322`); that file's header (line 15) says "natural numbers".
- **What would decide it:** whether the proof needs them, and whether S4's file imports `Nat.Prime`.

## 8. Registration with automation
- **Choice:** `@[simp]` only on `not_isFundamentalDiscr_zero` and `isFundamentalDiscr_one`; no `Decidable` instance in this change; `@[wikidata …]` if an item exists.
- **Alternatives:** `DecidablePred (Squarefree : ℤ → Prop)` via `squarefree_natAbs` beside `Data/Nat/Squarefree.lean:235`, then one for the predicate via the division form.
- **References:** S10, S11 (`Coprime/Basic.lean:44`). `minSqFacAux` is well-founded (`Data/Nat/Squarefree.lean:110-122`), its norm_num extension commented out (`:390-571`), so `decide` would rarely evaluate.
- **What would decide it:** a concrete need to evaluate on numerals.

## 9. Placement, and the link to quadratic fields
- **Choice:** integer arithmetic only, in a new `Mathlib/NumberTheory/FundamentalDiscriminant.lean` importing `Mathlib.Data.Nat.Squarefree`; the docstring names the quadratic-field connection.
- **Alternatives:** prove `NumberField.discr` of `ℚ(√d)` is fundamental; place under `NumberField/Discriminant/`.
- **References:** no quadratic-field type at base; S9 shows its modelling unsettled.
- **What would decide it:** that modelling settling.

## 10. Proof route
- **Choice:** prime reduction (a non-unit nonzero `f` has a prime factor; `g ^ 2 * E` stays `≡ 0, 1`), then split on `D % 4`. Odd `p`: `p ^ 2 % 4 = 1` (recalled `Int.sq_mod_four_eq_one_of_odd`) keeps the residue; `p = 2`: cofactor `m`.
- **Alternatives:** case analysis in `ZMod 4` with `decide`; go through ℕ by `natAbs` (sign bookkeeping).
- **References:** S4, S12; `Int.isUnit_iff` (recalled).
- **What would decide it:** proof length.
