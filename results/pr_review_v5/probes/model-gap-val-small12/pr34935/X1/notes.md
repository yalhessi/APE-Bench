# Review notes: PR #34935, `Semiring` structure on ideal sheaves

## Method

I read `pr.md`, `model.md` and `diff.patch`, then read the PR's versions of
`Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean` (lines 1-700) and
`Mathlib/AlgebraicGeometry/Scheme.lean` (the ZeroLocus section) with `file_read` (the workspace
prefix is `target/`). The file as the PR leaves it compiles with no errors or warnings
(`lean_verify_edit`, no edit). I tested every proposed edit with `lean_verify_edit`. Scratch
inputs are in `tmp/`.

## Object by object

### Basic.lean

- **`mem_supportSet_iff_mem_support`** (`@[simp]`, `.rfl`): the `Mul`/`Pow` support proofs use it,
  and it normalises the internal `supportSet` to `support`, which is what the structure docstring
  recommends. It does not clash with the existing `mem_supportSet_iff` (a different RHS). No finding.
- **`section Semiring` / `variable (I J K)`**: nothing wrong.
- **`Zero` / `One` / `Add` instances** (`⊥`, `⊤`, `⊔`): these match `Ideal`. The later `rfl` lemmas
  hold. No finding.
- **`Mul` instance**: the support set `I.supportSet ∪ J.supportSet` is correct, and the proofs are
  short. No finding.
- **`Pow` instance**: the support `if n = 0 then ∅ else I.supportSet` is correct. The instance on its
  own is fine. The problem is that the semiring instance does not reuse it (see below).
- **`ideal_mul`, `support_mul`, `ideal_pow`, `support_pow_succ`**: all `rfl`. Their names mirror the
  siblings `ideal_sup`/`ideal_inf`/`support_sup`. No finding.
- **`support_pow`**: correct. `n` is explicit although `hn : n ≠ 0` determines it, whereas
  `PrimeSpectrum.zeroLocus_pow` uses `{n : ℕ}`. **Finding (advisory)**; the implicit version compiles.
- **`top_mul`, `mul_top`, `bot_mul`, `mul_bot`** (`@[simp]`): these are needed because the simp normal
  form is `⊤`/`⊥` rather than `1`/`0`. They match `Ideal.top_mul`/`Ideal.mul_top`. No finding.
- **`mul_inf`, `inf_mul`**: the statements are about `⊔`, so the names are wrong. `Ideal.mul_sup` and
  `Ideal.sup_mul` (RingTheory/Ideal/Operations.lean:335,338) have exactly these statements.
  **Two findings (blocking)**, one per declaration. The rename to `mul_sup`/`sup_mul`, with the
  instance updated, compiles.
- **`IdemCommSemiring` instance**: `npow` is not given, so it defaults to `npowRec`, which is not
  defeq to the PR's `Pow` instance. I confirmed the diamond by unfolding at instance transparency
  (`npowRec n I` against `mkOfMemSupportIff (I.ideal ^ n) ...`, `isDefEq` = false). `pow_succ I n`,
  `rw [pow_succ]` and `pow_le_pow_left₀` all fail on `I ^ n`. **Finding (blocking, correctness).**
  Adding `npow n I := I ^ n`, with the tested `npow_zero`/`npow_succ` proofs, makes the whole file
  compile and those examples check. I also checked `nsmul := nsmulRec`: removing it breaks the
  instance (the field has no default), so it is needed. No finding.
- **`IsOrderedRing` instance** (empty `where`): no existing instance supplies it (`inferInstance`
  fails without it; `Kleene.lean` provides only `IsOrderedAddMonoid`, `CanonicallyOrderedAdd`,
  `MulLeftMono` and `MulRightMono`), so it is not redundant. No finding.
- **`/-! ... -/` note and `zero_eq_bot`, `one_eq_top`, `add_eq_sup`**: these mirror
  `Ideal.zero_eq_bot` and the others. `simp` terminates on goals that mix `0`, `⊥` and `+` (checked
  `⊥ + I = I`, `0 * I = 0`, `I ^ 0 = ⊤`, `(I ^ (n+2)).support = I.support`). No finding.
- **`equivOfIsAffine`** (now `≃+*o`, `@[simps]` removed): I checked whether `@[simps]` or
  `@[simps! apply symm_apply]` could replace the two hand-written lemmas. Both fail:
  `OrderRingIso` has no `apply` simps projection registered (its known projections are only raw
  fields). So removing `@[simps]` and writing `equivOfIsAffine_apply`/`_symm_apply` by hand is
  justified. These are the same names the old `≃o` `@[simps]` generated, so the API does not break.
  The `map_mul'`/`map_add'` proofs by `simp` are fine. The docstring ("in bijection") is still true.
  No finding.
- **`equivOfIsAffine_apply`, `equivOfIsAffine_symm_apply`**: `rfl` and correct. No finding.
- **`radical_inf`**: the only change is dropping redundant parentheses. Fine.
- **`radical_mul`**: correct, and matches `Ideal.radical_mul` and the style of `radical_inf`. No
  finding.

### Scheme.lean

- **`zeroLocus_setMul`**: correct. The name has precedent (`toAdd_image_setMul`) and the `_mul` name
  is taken by the ideal version. No finding.
- **`zeroLocus_mul`**: its name and statement mirror `PrimeSpectrum.zeroLocus_mul`, and the proof is
  short. No finding.
- **`open scoped Pointwise in`**: needed for the set product in both lemmas. No finding.

## Considered and not raised

- Asking for more counterparts, such as `radical_pow`, `Scheme.zeroLocus_pow` or
  `support_pow_zero`. They would be nice to have, but nothing in the PR makes them necessary.
- Golfing `mul_sup`/`sup_mul` to `IdealSheafData.ext (mul_add _ _ _)`. The difference is cosmetic.
- Registering `initialize_simps_projections OrderRingIso` upstream. That is out of scope for this PR.
