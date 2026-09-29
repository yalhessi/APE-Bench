# Review notes: PR #33285 "chore(*): golf, add missing lemmas"

## How I worked

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then used `ptool` for everything else.

- Workspace paths take the `target/` prefix (for example `target/Mathlib/...`). `lean_verify_edit` takes the bare `Mathlib/...` path.
- I tested every proposed edit with `lean_verify_edit`. Argument files are in `tmp/`.
- I also compiled `Mathlib/LinearAlgebra/Prod.lean` once as the PR leaves it: it compiles with no errors.

## Object by object

### `Submodule.inf_comap_le_comap_add` (Map.lean): proof golf, finding 4
- The PR swaps two `change` lines for `simp only [mem_comap, mem_inf, LinearMap.add_apply] at h ⊢`. The result is still a four-line tactic block.
- `fun _ h ↦ q.add_mem h.1 h.2` compiles.
- `fun _ h ↦ add_mem h.1 h.2` fails with a type mismatch: it elaborates against `comap f₁ q`.
- I did not raise the sibling `comap_le_comap_smul`, which uses the same `change` pattern: the PR does not touch it.

### `IsContDiffImplicitAt.implicitFunctionData` (ImplicitContDiff.lean): no finding
- The new `ext ⟨x, y⟩; rw [..., Prod.ext_iff, ← h.bijective.injective.eq_iff]; simp +contextual [Prod.mk_zero_zero]` compiles.
- I tried dropping `Prod.mk_zero_zero`: the goal is left unsolved, so the lemma is needed.
- Nothing to ask.

### `Submodule.IsOrtho.map` (Orthogonal.lean): finding 7
- The PR proves it with `aesop (add simp [isOrtho_iff_inner_eq])`.
- Three plain alternatives all compile: `simpa [isOrtho_iff_inner_eq] using h`, `simp_all [isOrtho_iff_inner_eq]`, and `rw ... at *; simpa using h`.
- I ask for the `simpa` form, as advisory.
- `precedent_search` returned nothing relevant.

### `ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range` (Banach.lean): no finding
- The term proof `⟨_, .comp (.subtype_coe (Set.range f)) (f.equivRange hf hf').antilipschitz⟩` is clean.
- The file compiles with it.

### `ContinuousLinearMap.equivRange_symm_apply` (Banach.lean): finding 5
- The PR's proof is `simp [symm_apply_eq, Subtype.ext_iff]`.
- `(f.equivRange hinj hclo).symm_apply_apply x` compiles as a term, because `equivRange` is `rangeRestrict` by `rfl`.
- Removing the old "is there an API lemma" comment is fine.

### `LinearIsometry.isComplete_image_iff` / `isComplete_image_iff'` (LinearIsometry.lean): finding 8
- I checked the new `@[simp]` works: `by simp` proves `IsComplete (g '' s) ↔ IsComplete s` for a `LinearIsometry` `g`.
- The deprecation is correct:
  - The date 2025-12-25 matches the review-time cutoff reported by `precedent_search` (as_of 2025-12-25).
  - The primed lemma has no other users.
- No finding on these two declarations themselves.
- Finding 8 is a scope ask. The same lean4#3107 workaround is still present on `SemilinearIsometryClass.nnnorm_map`, `LinearIsometry.nnnorm_map`, `LinearIsometry.enorm_map` and `LinearIsometryEquiv.nnnorm_map`.
  - I checked that the class lemma fires under `simp only` on a concrete `LinearIsometry`.
  - I checked that tagging it `@[simp]` keeps the file compiling.

### `Matrix.rank_eq_finrank_range_toLin` (Rank.lean): no finding
- Replacing the `range_e₂` helper by `e₂.range` is fine.
- The model lists this declaration as both "modified" and "removed". That is one declaration, split in two by the diff; nothing was actually removed.

### `LinearEquiv.symm_prodComm` (Prod.lean): finding 1
- It is a new `@[simp]` lemma proved by `rfl`.
- Duplication: `@[simps apply]` on `prodComm` generates no symm lemma, so the new lemma duplicates nothing.
- Naming: the sibling pattern is `prodComm_symm`, used by eight equivalence types, including `ContinuousLinearEquiv.prodComm_symm` in a file this PR edits. `LinearIsometryEquiv` is the only other `symm_prodComm`.
- The `naming_norm` prefix census was inconclusive (`insufficient_evidence`), so the finding rests on the sibling census.
- The rename compiles.

### `Ideal.cotangentEquivIdeal_symm_apply` (Cotangent.lean): finding 6
- Removing the obsolete porting notes, the `by exact` timeout workaround and `(R := R)` is fine: the statement elaborates without them.
- The proof `rw [symm_apply_eq]; ext; simp` can be the term `I.cotangentEquivIdeal.symm_apply_eq.mpr rfl`, which compiles.
- This is advisory only.

### `ContinuousLinearMap.iInfKerProjEquiv` (Equiv.lean): no finding
- Dropping the explicit `@continuous_subtype_val _ _ (fun x => ...)` is a good change.
- I tried alternatives:
  - `by fun_prop` fails.
  - `(continuous_apply i).comp continuous_subtype_val` without `(A := φ)` fails.
  - `(continuous_apply (A := φ) i).comp continuous_subtype_val` works, but it would not fit on one line under 100 characters.
- Not worth asking.

### `ContinuousLinearEquiv.submoduleMap` (Equiv.lean): findings 2 and 3
- Finding 2 (statement): the PR changed the result type to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p`. The original `Submodule.map e p` compiles with the new body, and the rest of the file compiles too. The change is unneeded, and it disagrees with `submoduleMap_symm_apply (x : p.map e)` and with `LinearIsometryEquiv.submoduleMap`.
- Finding 3 (proof): the continuity fields can be the symmetric `(e.continuous.comp continuous_subtype_val).subtype_mk _` and `(e.symm.continuous.comp continuous_subtype_val).subtype_mk _`. The PR's `continuous_invFun` instead rebuilds the linear equivalence's inverse only to get a membership proof. Both variants compile: with `__ :=`, and with `toLinearEquiv :=`.
- `ContinuousLinearEquiv.submoduleMap` has no users outside this file; `ofSubmodules` is the only one.

## Families
- The `isComplete_image_iff` / `isComplete_image_iff'` pair is one decision (un-simp and deprecate the specialised copy). It is consistent.
- The two `rank_eq_finrank_range_toLin` entries are one declaration.

## Severity
All eight findings are advisory. None is a build or correctness error: every file I compiled compiles as the PR leaves it.
