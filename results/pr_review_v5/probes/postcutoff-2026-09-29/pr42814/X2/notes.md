# Review notes: PR #42814 (fundamental discriminants)

I read `pr.md`, `model.md` and `diff.patch`, then used the tools through `./ptool`. The workspace
paths are `target/Mathlib/...` for reads and searches, and `Mathlib/...` for `lean_verify_edit`.
The PR's `FundamentalDiscriminant.lean` compiles as submitted (`lean_verify_edit` with no edit
returned `compiles: true` with no errors). There are 6 findings, in `findings.json`.

## Mathlib.lean
- One import added, `Mathlib.NumberTheory.FundamentalDiscriminant`, placed between
  `FunctionField` and `GaussSum`. The alphabetical order is correct. No finding.

## Mathlib/Data/Nat/Prime/Basic.lean: `Nat.forall_prime_iff_two_and_odd`
- The statement is correct and the docstring is fine. It is not a duplicate:
  `declaration_search` found it only in this PR.
- Placement next to `Prime.odd_of_ne_two` is fine.
- Proof-golf (finding): `Nat.Prime.eq_two_or_odd'` (same file, l.45) already gives the
  `p = 2 ∨ Odd p` split. A term-mode proof built on it compiles (`lean_verify_edit` success).
- Naming: `naming_norm` could not resolve a subject, so naming is unmeasured. I saw no convention
  the name clearly breaks.

## Mathlib/Data/Nat/Squarefree.lean: `Int.squarefree_iff_prime_sq_not_dvd`
- Not a duplicate: it exists only in this PR. The existing neighbours are `Int.squarefree_natAbs`
  (Algebra/Squarefree/Basic), `Nat.squarefree_iff_prime_squarefree`, and the general
  `squarefree_iff_irreducible_sq_not_dvd_of_*`.
- The name follows the `..._irreducible_sq_not_dvd...` pattern, so no naming ask.
- Placement: the file's docstring says "natural numbers", but the lemma depends on
  `Nat.squarefree_iff_prime_squarefree`, which lives there. I considered a move and did not ask
  for one.
- Proof-golf (finding): a single `simp_rw [← Int.squarefree_natAbs,
  Nat.squarefree_iff_prime_squarefree, sq, ← Int.natCast_mul, Int.natCast_dvd]` compiles
  (verified). It replaces the `bridge` have and the `=>`-style anonymous-constructor proof.
- The `namespace Int` / `end Int` wrapper is fine.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_right_iff` / `dvd_mul_left_iff`: correct, and new (`declaration_search`).
  - Naming (finding, advisory): every analogue is an iff with no `_iff` suffix:
    `Nat.Coprime.dvd_mul_right/left`, `IsUnit.dvd_mul_right/left` and `Units.dvd_mul_right/left`.
    The rename compiles and does not clash with root `dvd_mul_right` (verified).
  - This is one finding for the pair, since the model lists them as one family.
- `Odd.isCoprime_two`: correct. It needs `CommRing`, because in a semiring such as ℕ, `3` and `2`
  are not `IsCoprime`, so there is no generalization ask.
  - Naming (finding): the existing names are `Int.isCoprime_two_right/left` and
    `Odd.coprime_two_right/left` (ℕ).
  - The ask is to rename it to `Odd.isCoprime_two_right` and add a `_left` companion; both compile
    (verified).
  - `Int.isCoprime_two_right.mpr` would also serve the use site, but it lives in
    `RingTheory/Int/Basic`. The general lemma is the better addition, so I made no duplication
    finding.

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Header, `module`, `public import`, `@[expose] public section` and the namespace are fine.
  `@[expose]` is appropriate for a Prop-valued def that downstream proofs unfold.
- Module docstring (finding, blocking): it claims these are "exactly the discriminants of
  quadratic fields". I verified that `IsFundamentalDiscr 1` is provable (via
  `isFundamentalDiscr_four_mul_add_one` at `m = 0`), and 1 is not a quadratic-field discriminant.
  The ask is to fix the doc, or to exclude 1 in the definition.
- `Int.IsFundamentalDiscr`: the docstring matches the body.
  - I weighed asking for the clause `¬ 4 ∣ x ∧ x % 4 ≠ 1` to be spelled consistently as
    `x % 4 = 2 ∨ x % 4 = 3`. I tested that change on the def plus `_def`: it makes the `grind`
    proof of `isFundamentalDiscr_iff_squarefree` time out.
  - The current spelling is therefore load-bearing for the proof, and I did not file it.
  - I also weighed asking for the literal "primitive" definition. That is a design preference I
    could not ground in a concrete defect, so I did not file it.
  - `D = 0` is correctly excluded.
- `Int.isFundamentalDiscr_def`: `Iff.rfl` unfolding lemma, the same pattern as
  `QuadraticAlgebra.discr_def` by the same author. No finding.
- `IsFundamentalDiscr.ne_zero` and `IsFundamentalDiscr.emod_four_eq_zero_or_one`: correct.
  `emod` is the right token for Int `%`. No finding.
- `Int.isFundamentalDiscr_iff_squarefree`: the statement and docstring are correct.
  - Style (finding): the two anonymous `have`s shadow each other as `this`, and `+contextual` is
    unnecessary. Naming them and using a plain `simp only` compiles (verified).
  - I tested whether the `by_cases` could be dropped: a single `grind` fails, so it stays.
- `Int.isFundamentalDiscr_four_mul_add_one` and `Int.isFundamentalDiscr_four_mul`: correct
  one-line `simp` corollaries.
  - They have no docstrings, but they are theorems and the module doc lists them, so there is no
    ask.
  - I considered `@[simp]` and did not file it, since nothing supports it concretely.

## Other tool use
- `zulip_search` for fundamental-discriminant and quadratic-field threads found only general
  quadratic-field planning, with nothing about this definition.
- `precedent_search` on the def and on the squarefree lemma returned unrelated hits.
- `naming_norm` returned `subject_unresolved` for all five helper lemmas.
