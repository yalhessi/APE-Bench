# Review notes: PR #42814 (fundamental discriminants)

I read `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe` and used the tools listed
under each object. As a baseline, `lean_verify_edit` with no edit on
`Mathlib/NumberTheory/FundamentalDiscriminant.lean` reported `compiles: true` with no errors or
warnings. As a control, I submitted a deliberately wrong proof (bare `simp`) for
`Int.squarefree_iff_prime_sq_not_dvd`, and the verifier rejected it. So its `success` results mean
something. One edit (below) hit an environment/process failure, which the tool reported as such;
I did not rely on that one.

`naming_norm` returned `subject_unresolved` for every declaration I tried. I judged naming instead
from `content_search` over the base tree.

## Mathlib.lean
- Import `Mathlib.NumberTheory.FundamentalDiscriminant` added in alphabetical position, between
  `FunctionField` and `GaussSum`. Nothing wrong.

## Mathlib/Data/Nat/Prime/Basic.lean
- `Nat.forall_prime_iff_two_and_odd` and its docstring. The statement and docstring are fine, and
  it sits next to `Prime.odd_of_ne_two`, which is the right place. **Finding (proof-golf):** the
  manual `eq_or_ne p 2` split can use the existing `Prime.eq_two_or_odd'` (Basic.lean:45). The
  term proof compiled with `lean_verify_edit`. I left the name alone: nothing in the tree gives a
  competing convention.

## Mathlib/Data/Nat/Squarefree.lean
- `namespace Int` / `end Int` block after `end Nat`. The file's module doc is about ℕ, but the
  lemma needs `Nat.squarefree_iff_prime_squarefree` (same file), while `Int.squarefree_natAbs` is
  in `Algebra/Squarefree/Basic.lean`. The placement is therefore forced, and I raised no scope ask.
- `Int.squarefree_iff_prime_sq_not_dvd` and its docstring. I searched for an existing ℤ version
  and found none; the ℕ analogue is `Nat.squarefree_iff_prime_squarefree`, stated with `x * x`.
  The docstring is accurate. The name parallels
  `squarefree_iff_irreducible_sq_not_dvd_of_ne_zero` and I raised no naming ask.
  **Finding (proof-golf):** the local `bridge` plus hand-written transport is a
  `rw …; simp_rw [← sq, ← Int.natCast_dvd, Nat.cast_pow]`, and a one-line `simp` also works.
  Both compiled.

## Mathlib/RingTheory/Coprime/Basic.lean
- `IsCoprime.dvd_mul_right_iff`, `IsCoprime.dvd_mul_left_iff`. The statements and proofs are
  correct and well placed, next to `dvd_of_dvd_mul_*`. I found no existing `IsCoprime` version,
  so there is no duplication. **Finding (naming):** `Nat.Coprime.dvd_mul_right/left`,
  `IsUnit.dvd_mul_right/left` and `Units.dvd_mul_right/left` are the same kind of iff and carry no
  `_iff`. The rename compiled in-file.
- `Odd.isCoprime_two`. It is correct, and it needs `CommRing` (in ℕ, `IsCoprime 3 2` is false),
  so it cannot be generalized. `Int.isCoprime_two_right` is not imported by the new file (I tried
  it: unknown identifier), so the general lemma is justified. **Finding (naming):** the sibling
  lemmas use `_right`/`_left` (`Odd.coprime_two_right`, `Int.isCoprime_two_right`); rename to
  `Odd.isCoprime_two_right` and add `_left`. This compiled.

## Mathlib/NumberTheory/FundamentalDiscriminant.lean
- Header, `module`, `public import Mathlib.Data.Nat.Squarefree`, `@[expose] public section`: fine.
  The def must be exposed for `h.1` to work downstream.
- Module docstring. **Finding (documentation/correctness, blocking):** it says fundamental
  discriminants "are exactly the discriminants of quadratic fields", but `IsFundamentalDiscr 1`
  is provable (verified with `lean_verify_edit`). The rest of the doc and its list of main
  results match the file.
- `Int.IsFundamentalDiscr` and its docstring. By hand I checked D = 1, -3, -4, -7, -8, 5, 8, 12
  (included) and 4, 16, 0 (excluded), and all behave as expected. The docstring matches the body.
  I tried restating the second conjunct uniformly, as `x % 4 = 2 ∨ x % 4 = 3` and as
  `x % 4 ≠ 0 ∧ x % 4 ≠ 1`. The first makes the `grind` calls in
  `isFundamentalDiscr_iff_squarefree` time out. The second also broke that proof (a grind error
  at the same step, seen only in the stdout tail of a run the verifier reported as a process
  failure). The author's form is evidently tuned for `grind`, so I raised no style ask.
- `Int.isFundamentalDiscr_def` (`Iff.rfl`). `grind [IsFundamentalDiscr]` also closes `ne_zero`,
  so the lemma is not strictly needed. A `_def` lemma is still ordinary API, so no ask.
- `Int.IsFundamentalDiscr.ne_zero`: a one-line `grind`. An alternative `rintro rfl; simpa using
  h.2.1 0` also compiles, but it is no improvement. No ask.
- `Int.IsFundamentalDiscr.emod_four_eq_zero_or_one`: fine.
- `Int.isFundamentalDiscr_iff_squarefree` and its docstring. The statement and docstring are
  accurate. **Finding (style):** name the two anonymous, shadowing `have`s that `grind` picks up
  implicitly; this compiled with `hsq`/`hdvd`. **Finding (proof-golf):**
  `simp +contextual only [Int.mul_ediv_cancel_left …]` is a plain `rw`, which compiled, and so did
  `simp only` without `+contextual`. The `by_cases` split is necessary: a single `grind` without it
  fails on non-linear divisibility by `D / 4`.
- `Int.isFundamentalDiscr_four_mul_add_one`, `Int.isFundamentalDiscr_four_mul`: correct
  one-line corollaries matching the module doc. No ask.

## Searched and not raised
- Zulip ("fundamental discriminant quadratic field", "IsCoprime dvd_mul_left iff name"): nothing
  that bears on these names or definitions beyond the author's quadratic-fields programme.
- `precedent_search` on the def, the Int squarefree lemma, the IsCoprime lemmas,
  `forall_prime_iff_two_and_odd` and `Odd.isCoprime_two`: nothing relevant.
- Decidability: only `DecidablePred (Squarefree : ℕ → Prop)` exists. A `Decidable` instance for
  `IsFundamentalDiscr` would be nice to have, but nothing supports asking for it in this PR.
- Scope: the three helper lemmas in other files are small and all used by the new file. I did not
  ask for them to be split out.
