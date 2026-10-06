# Review notes: PR #42814 (fundamental discriminants)

I read `pr.md`, `model.md` and `diff.patch`, and called the tools only through `./ptool`. First I confirmed
that `Mathlib/NumberTheory/FundamentalDiscriminant.lean` compiles as the PR leaves it (`lean_verify_edit`
with no edit: compiled, no warnings). Seven findings went to `findings.json`. Notes by object follow.

## Mathlib.lean
- The added `public import Mathlib.NumberTheory.FundamentalDiscriminant` is required, because every new
  file must be listed in the umbrella file. It sits in the right alphabetical place (`FunctionField` <
  `FundamentalDiscriminant` < `GaussSum`). The convention item suggesting it is unused does not apply.
  No finding.

## Mathlib/Data/Nat/Prime/Basic.lean: `Nat.forall_prime_iff_two_and_odd`
- Proof golf. `Nat.Prime.eq_two_or_odd'` exists (line 45), and a term proof built on it compiles. That is
  finding 6.
- Strict-implicit `∀ ⦃p⦄`: I dropped this item. The sibling `Nat.squarefree_iff_prime_squarefree` and much
  of the library state such statements with `∀ x, Prime x → ...`, so this is not a convention a
  maintainer would hold the PR to.
- Name, docstring and placement (next to `Prime.odd_of_ne_two` and `Prime.even_sub_one`): nothing to ask.
- Scope (splitting into its own PR): the PR is small and its only use is in this PR. I would not ask.

## Mathlib/Data/Nat/Squarefree.lean: `Int.squarefree_iff_prime_sq_not_dvd`
- Duplication: `Int.squarefree_iff_nat_prime_sq_not_dvd` does not exist. The general
  `squarefree_iff_irreducible_sq_not_dvd_of_ne_zero` is stated over irreducibles in ℤ, not over ℕ primes,
  so the lemma is new.
- Proof golf. One `simp [← Int.squarefree_natAbs, Nat.squarefree_iff_prime_squarefree, ← Int.natCast_dvd,
  sq]` compiles. That is finding 5. It also removes the `=>`-style lambdas.
- Name: `sq_not_dvd` matches the general `squarefree_iff_irreducible_sq_not_dvd_*` family, so no ask.
  `naming_norm` could not resolve the subject, so the name is unmeasured by that tool.
- Placement: it uses `Nat.squarefree_iff_prime_squarefree` from this file, so this file is a natural home.
- Module docstring: the file's "Main Results" lists only one theorem and was never exhaustive. I would not
  ask for an addition.
- alias / `grind =` / strict-implicit items: dropped. None is a convention a maintainer would require here.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_left_iff` / `dvd_mul_right_iff`:
  - Naming. The library's analogous cancellation iffs drop `_iff`: `Nat.Coprime.dvd_mul_left/right`,
    `IsUnit.dvd_mul_left/right`, `Units.dvd_mul_left/right`. The renamed pair compiles. That is finding 4.
  - Duplication: no `IsCoprime` iff of this shape existed before the PR (`declaration_search`,
    `content_search`).
  - `to_additive`: not applicable (`IsCoprime` is a ring notion).
  - IsRelPrime counterparts: `IsRelPrime.dvd_of_dvd_mul_right` lives in
    `Algebra/Divisibility/Units.lean`, not in this file. I did not request an IsRelPrime iff.
- `Odd.isCoprime_two`:
  - Existing `Int.isCoprime_two_right : IsCoprime m 2 ↔ Odd m` (RingTheory/Int/Basic.lean) is not imported
    by the new file, and using it there fails with an unknown-constant error. So the general lemma is
    justified.
  - Naming. Its analogues carry `_right` (`Int.isCoprime_two_right`, `Odd.coprime_two_right` for ℕ), and
    the `_left` mirror is missing. The rename plus the `_left` version compiles. That is finding 3.
  - Generality: `CommRing` is needed. In a semiring (ℕ), `IsCoprime 3 2` fails (`Nat.isCoprime_iff`). No ask.
  - Variable reuse: the enclosing `section CommRing` declares only `R`, and the neighbouring lemmas bind
    `{x y : R}` themselves, so the binder is consistent. I dropped that item.
  - `theorem` vs `lemma`: the file mixes both. No ask.

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Module docstring / `Int.IsFundamentalDiscr`. The docstring says these are "exactly the discriminants of
  quadratic fields", but `IsFundamentalDiscr 1` is provable, both from the iff and from the definition.
  That is finding 1, marked blocking because it is a false mathematical statement in the docs.
- `Int.IsFundamentalDiscr`, definition shape. Restating the second conjunct as
  `4 ∣ D → D / 4 % 4 = 2 ∨ D / 4 % 4 = 3` compiles with every downstream proof unchanged. That is
  finding 2. The variant `∀ x, D = 4 * x → x % 4 = 2 ∨ x % 4 = 3` made `grind` time out.
- I checked the equivalence that the definition docstring's "primitive, i.e. ..." asserts, by hand: odd
  `p²` ≡ 1 mod 4, and squares are 0 or 1 mod 4. The two are equivalent, so the docstring is correct there.
  `D = 0` is excluded, which agrees with `ne_zero`. Negative discriminants behave correctly under `%`
  (e.g. -3, -4).
- `isFundamentalDiscr_def` (`Iff.rfl`) is a standard `_def` API lemma and is used as a `grind` hint.
  `emod_four_eq_zero_or_one` and `ne_zero` are reasonable API. No ask for any of them.
- `isFundamentalDiscr_iff_squarefree`:
  - `+contextual` is unnecessary (verified). That is finding 7.
  - Removing the `simp` line entirely could not be verified: `environment_failure` twice.
  - The `simpa using` alternative for the second `have` compiles, but it is not clearly better, so I made no
    finding.
  - The anonymous `have`s used by `grind` are documented by a comment. No ask.
- `isFundamentalDiscr_four_mul_add_one`, `isFundamentalDiscr_four_mul`: terminal `simp`, fine.
- Missing docstrings on theorems, line-wrapping and `variable {D}` items: Mathlib does not require these,
  so I would not request them.
- Import `Mathlib.Data.Nat.Squarefree`: needed for `Squarefree`, the new Int lemma and
  `Nat.forall_prime_iff_two_and_odd`. No ask.
- I also tried a `DecidablePred IsFundamentalDiscr` instance via the iff. It fails because `Squarefree` on
  ℤ has no decidability instance, so I made no request.

## Tools that returned nothing useful
- `naming_norm` returned `subject_unresolved` or `population_too_small` for every new name.
- `precedent_search` returned unrelated hits.
- `zulip_search` found no discussion of this definition.
