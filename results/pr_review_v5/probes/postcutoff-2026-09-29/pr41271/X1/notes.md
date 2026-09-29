# Review notes: PR #41271 (Matrix/Nondegenerate: generalize lemmas to CommSemiring)

What I read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. I also read the whole changed file as the PR
leaves it, through `ptool file_read` on `target/Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`.
Baseline: `lean_verify_edit` with no edit reports that the file compiles, with no errors or warnings.

## Object by object

### `section CommSemiring` + `variable {m n R : Type*} [CommSemiring R] {M : Matrix m n R}` (1763da9512, 50baf4736e)
- The generalization is correct: the file compiles.
- I probed how far each lemma can be generalized by editing the variable line (line 51):
  - `[NonUnitalNonAssocSemiring R]`: only the vecMul/mulVec characterisations fail (lines 73-74 and 82:
    `dotProduct_mulVec` needs associativity, and `Pi.single i 1` needs `One`), plus the transpose lemmas
    (lines 102 and 111: `dotProduct_transpose_mulVec` needs commutativity). The `_def` lemmas and the
    `Nondegenerate.eq_zero_of_ortho*` / `exists_not_ortho*` family all elaborate.
  - `[Semiring R]`: only the transpose lemmas fail (lines 102 and 111).
  - `dotProduct_transpose_mulVec` is stated under `section NonUnitalCommSemiring` in `Data/Matrix/Mul.lean`.
  - A full three-way split (NonUnitalNonAssocSemiring / Semiring / CommSemiring, or NonUnitalCommSemiring
    for the last section) compiles cleanly with the `Determinant` section and the trailing
    `LinearIndependent` lemma unchanged.
- **Finding (advisory, generalization):** split the section so that each lemma sits at its natural
  generality, matching the `NonUnitalNonAssocSemiring` generality of the definitions. This is in scope
  because the PR's stated purpose is exactly this generalization.
- Downstream breakage risk: I searched for `@Matrix.separating*` / `@Matrix.nondegenerate*` and found no
  explicit-argument uses. The `_def` lemmas are used downstream only by `rw`/`simpa`/`.mpr`
  (ToLinearEquiv.lean:218, SesquilinearForm.lean:678-697), so the generalization is safe.

### `Matrix.nondegenerate_def` (3eec003058), proof golfed to `rw [nondegenerate_iff, separatingLeft_def, separatingRight_def]`
- It compiles, and it uses the `@[mk_iff]`-generated `nondegenerate_iff`, as
  `nondegenerate_iff_forall_vecMul_and_mulVec_eq_zero` already does. A term-mode
  `nondegenerate_iff.trans (and_congr separatingLeft_def separatingRight_def)` is equivalent and no
  better. Nothing to request.
- It also holds at `NonUnitalNonAssocSemiring`, which the finding above covers.

### `section Determinant` variable line: now `{m R : Type*} [CommRing R] [Fintype m] [DecidableEq m] {M : Matrix m m R}` (7cc3db6c76)
- Re-binding `m R` and `[Fintype m]` is required, because the enclosing variables now end with
  `section CommSemiring`. `CommRing` is required, because `det` / `cramer` are stated for `CommRing`.
  The PR states this intentionally. Nothing to request.

### `end CommSemiring` (df7020fb11)
- It closes the section correctly, just before `section Determinant`. Nothing to request.

## Checked and not raised
- Naming: the PR adds or renames no declarations, so `naming_norm` does not apply.
- Existing docstring defects that the PR does not touch: `SeparatingLeft`'s docstring says
  "right-separating", and the `Nondegenerate.eq_zero_of_ortho*` docstrings swap `v`/`w` relative to the
  statements. They are real, but they predate this PR and lie outside the diff, so I did not raise them
  as requests for this PR.
- `LinearIndependent.sum_smul_of_nondegenerate` stays at `CommRing`/`AddCommGroup`. It relies on
  `Fintype.linearIndependent_iff` (the ring form), and the PR does not touch it. Not raised.
- The `precedent_search` and `zulip_search` hits were about the Nondegenerate definition debate
  (#34110) and unrelated generalizations. None bears on a specific request here.

## Tool calls
- `ptool describe`, `file_search`, `file_read`
- `lean_verify_edit` ×5: as-is; NUNA-semiring probe; Semiring probe; three-way split; split with
  NonUnitalCommSemiring
- `precedent_search`, `zulip_search`, `declaration_search` (`Matrix.dotProduct_transpose_mulVec`)
- `content_search` ×3: explicit-arg uses; `_def` uses; section context in `Data/Matrix/Mul.lean`
