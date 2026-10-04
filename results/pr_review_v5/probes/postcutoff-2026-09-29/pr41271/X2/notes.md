# Review notes: PR #41271 (Matrix/Nondegenerate: lemmas CommRing -> CommSemiring)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`; then the full file as the PR leaves it
(`ptool file_read target/Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`, workspace root is `target/`).

Baseline: `lean_verify_edit` with no edit -> the file compiles as the PR leaves it, no errors, no warnings.

## Objects

### `section CommSemiring` opening + `variable ... [CommSemiring R]` (1763da9512, 50baf4736e)
- Checked which lemmas actually need commutativity by weakening the section's typeclass with
  `lean_verify_edit` (line mode on line 51):
  - `[Semiring R]`: only the two `simp_rw [..., dotProduct_transpose_mulVec]` lines fail
    (`separatingLeft_transpose_iff`, `separatingRight_transpose_iff`); `nondegenerate_transpose_iff`
    builds on them.
  - `[NonUnitalSemiring R]`: additionally the two `Pi.single i 1` steps fail (needs `One`).
  - `[NonAssocSemiring R]` / `[NonUnitalNonAssocSemiring R]`: additionally `dotProduct_mulVec`
    (needs associativity) fails; the `_def` lemmas and the `eq_zero_of_ortho` family still compile.
- `dotProduct_transpose_mulVec` (Mathlib/Data/Matrix/Mul.lean:1096) is the commutative-only step.
- Verified a full restructure (section Semiring with every non-transpose lemma, then section
  CommSemiring with the three transpose lemmas and aliases, proofs unchanged): compiles cleanly.
- -> Finding 1 (advisory, generalization): state everything except the transpose lemmas for `Semiring`.
  I did not ask for a three-tier split down to `NonUnitalNonAssocSemiring`; recorded in the evidence only,
  since the fragmentation is unlikely to be wanted.

### `Matrix.nondegenerate_def` (3eec003058, proof golfed)
- New proof `rw [nondegenerate_iff, separatingLeft_def, separatingRight_def]` is the natural one-liner using
  the `@[mk_iff]` lemma; compiles. A term-mode `nondegenerate_iff.trans (and_congr ...)` would be no better.
  Nothing to request.
- Statement unchanged; implicit-argument arity unchanged (only the class on `R` changed), and downstream
  users (ToLinearEquiv.lean:218 `rw [nondegenerate_def, nondegenerate_def]`, SesquilinearForm.lean:678-697
  for the `separating*_def` lemmas) use it unqualified with no `@`-explicit arguments
  (content_search for `@...` forms: none).

### `end CommSemiring` (df7020fb11) and Determinant section variable line (7cc3db6c76)
- The Determinant section now re-declares `{m R : Type*} [CommRing R] [Fintype m] [DecidableEq m]`,
  which is required: the outer `variable` is now scoped to `section CommSemiring`, and a
  `[CommRing R]` on top of an ambient `[CommSemiring R]` would have given two unrelated instances.
  `[Fintype m]` used to come from the `variable [Fintype m] [Fintype n]` inside the old top-level scope;
  it is correctly re-supplied. `Matrix.det`/`cramer` need `CommRing`, so keeping `CommRing` here is right.
  Nothing to request.

## Other checks, nothing requested
- Naming: the PR adds or renames no declaration.
- Documentation: no docstring touched by the diff. Pre-existing, outside the diff and not asked for:
  `SeparatingLeft`'s docstring says "right-separating" (line 37); the `eq_zero_of_ortho` docstrings
  swap `v`/`w` relative to the statements; the module doc lists only `Matrix.Nondegenerate` under main
  definitions.
- Scope: `LinearIndependent.sum_smul_of_nondegenerate` stays at `CommRing`; its proof relies on
  `Fintype.linearIndependent_iff` (ring-level), so it is not a missed generalization of this PR.
- Style: section layout is conventional; no binder or attribute issues.
- Correctness: file compiles; generalizing the class on `R` does not change any statement's shape.
- Context: precedent_search returned nothing bearing on this change; zulip_search shows the 2026-01
  "Nondegenerate bilinear / quadratic forms" thread (aligning `Matrix.Nondegenerate` with the
  left+right `LinearMap` notion), which motivates the earlier definition change, not anything here.
