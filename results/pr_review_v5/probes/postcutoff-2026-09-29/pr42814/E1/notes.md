# Review notes: PR #42814 (fundamental discriminants)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools went only through `./ptool`. Temporary
argument files are in `tmp/`.

## Mathlib.lean
- The added import is in alphabetical order (FunctionField < FundamentalDiscriminant). Nothing to ask.

## Mathlib/Data/Nat/Prime/Basic.lean: `Nat.forall_prime_iff_two_and_odd` (and its docstring)
- Checked for duplicates. A search for `forall_prime` declarations found nothing equivalent.
- Proof: the `eq_or_ne` + `odd_of_ne_two` case split duplicates `Prime.eq_two_or_odd'` (line 45).
  A term-mode proof compiles (lean_verify_edit: compiled). Finding 7, advisory.
- The name and docstring are acceptable, and the placement next to `Prime.odd_of_ne_two` is fine.
  naming_norm could not resolve a subject.

## Mathlib/Data/Nat/Squarefree.lean: `Int.squarefree_iff_prime_sq_not_dvd`
- Duplicates: the only squarefree iff lemmas are the Nat (`x * x`) and general-irreducible
  versions. No Int prime version exists, so the lemma is new.
- Placement: `Int.squarefree_natAbs` is in Algebra/Squarefree/Basic. That file lacks
  `Nat.squarefree_iff_prime_squarefree`, so putting the lemma in Data/Nat/Squarefree is
  reasonable. No scope ask.
- Proof golf: a one-line `simp_rw` compiles (finding 6). The first attempt duplicated the docstring
  because I included it in `new_declaration`; resubmitted without it, compiled.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_right_iff` / `IsCoprime.dvd_mul_left_iff`: neither name nor any iff form
  existed before. The sibling iff lemmas `Nat.Coprime.dvd_mul_right/left` and
  `IsUnit.dvd_mul_right/left` carry no `_iff` suffix, and the suffix-free IsCoprime names are free.
  Finding 4 (naming, one decision for the pair). The proofs are fine.
- `Odd.isCoprime_two`: the general CommRing statement is justified, because
  `Int.isCoprime_two_right` lives in RingTheory/Int/Basic, which the new file does not import
  (lean_verify_edit: unknown constant). The name lacks the `_right` suffix used by
  `Odd.coprime_two_right` and `Int.isCoprime_two_right`, and the `_left` twin is missing. A rename
  plus twin compiles. Finding 5.

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Module doc: it claims these are exactly the discriminants of quadratic fields, but
  `IsFundamentalDiscr 1` holds (lean_verify_edit: compiled). Finding 1, documentation correctness.
- `Int.IsFundamentalDiscr` / `isFundamentalDiscr_def` / `emod_four_eq_zero_or_one`: the def is
  checked mathematically correct. It enforces the 2-part primitivity through the `4 * x` clause and
  the odd-p part through the odd-prime-square clause, since p^2 ≡ 1 mod 4. The handwritten
  characterisation and projection are what `@[mk_iff] structure` generates. The restructured file
  compiles (finding 2).
- Tried restating the def's middle clause as `x % 4 = 2 ∨ x % 4 = 3`, for consistency with the
  first conjunct. `grind` in `isFundamentalDiscr_iff_squarefree` then times out, so I did not
  submit it: the current spelling is load-bearing for the proof.
- Repeated `{D : ℤ}` / `{m : ℤ}` binders: the `variable` refactor compiles (finding 3).
- `IsFundamentalDiscr.ne_zero`, `isFundamentalDiscr_iff_squarefree` (grind with context `have`s,
  commented), `isFundamentalDiscr_four_mul_add_one`, `isFundamentalDiscr_four_mul`: statements and
  proofs are fine. Their docstrings, where present, match the statements. No asks beyond the above.
- Conventions checked with no finding: alias for iff directions (no iff here has its directions
  used separately); generalization from a concrete type (`Odd.isCoprime_two` and the IsCoprime
  lemmas are already general; the Int- and Nat-specific lemmas are inherently specific).
- Zulip and precedent searches turned up nothing bearing on this code.

Seven findings: one blocking (docs correctness) and six advisory.
