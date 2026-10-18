# Review notes: PR #33285 "chore(*): golf, add missing lemmas"

I read pr.md, model.md and diff.patch, then checked each changed object with the ptool tools.
Every proposed edit was compiled with `lean_verify_edit` against the PR workspace.

## Submodule.inf_comap_le_comap_add (Algebra/Module/Submodule/Map.lean)
- The PR replaces the `change` steps with `simp only`. The statement holds definitionally, so
  `fun _ h ↦ q.add_mem h.1 h.2` compiles. The unqualified `add_mem h.1 h.2` does not: it gives a
  type mismatch, so `q.` is needed. -> finding (proof-golf, advisory).

## IsContDiffImplicitAt.implicitFunctionData (Analysis/Calculus/ImplicitContDiff.lean)
- The new `ext ⟨x, y⟩; rw [...]; simp +contextual [Prod.mk_zero_zero]` is terminal.
  `Prod.mk_zero_zero` is not a simp lemma (it is `@[to_additive]` without `simp`, in
  Algebra/Notation/Prod.lean), so it is a genuine hint. Nothing to request.

## Submodule.IsOrtho.map (Analysis/InnerProductSpace/Orthogonal.lean)
- The proof is now `aesop (add simp [isOrtho_iff_inner_eq])`. `simpa [isOrtho_iff_inner_eq] using h`
  compiles. -> finding (advisory): prefer the simp call over an aesop search.
- `precedent_search` returned nothing relevant.

## ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range (Banach.lean)
- The term proof `⟨_, .comp (.subtype_coe _) (f.equivRange hf hf').antilipschitz⟩` is fine. The
  docstring is unchanged and correct. Nothing to request.

## ContinuousLinearMap.equivRange_symm_apply (Banach.lean)
- The PR proof `simp [ContinuousLinearEquiv.symm_apply_eq, Subtype.ext_iff]` is fine, and the
  removed `-- is there an API lemma` comment was correctly dropped.
- `(f.equivRange hinj hclo).symm_apply_eq.2 rfl` compiles. -> finding (proof-golf, advisory).
- The lemma has no other users in Mathlib.

## LinearIsometry.isComplete_image_iff / isComplete_image_iff' (LinearIsometry.lean)
- I checked that the new `@[simp]` on the class-generic lemma actually fires: replacing the
  deprecated lemma's proof with `by simp` compiles.
- The deprecated lemma has no users in Mathlib (content_search), so the deprecation breaks nothing.
  The date 2025-12-25 matches the review time (the precedent corpus is as of 2025-12-25).
- I did not ask for the `alias` form. The signatures differ (explicit `LinearIsometry` versus a
  class-generic `𝓕`), so a deprecated theorem is acceptable.
- The same lean4#3107 workaround comments remain on `SemilinearIsometryClass.nnnorm_map` (l.99),
  `LinearIsometry.nnnorm_map` (l.200), `LinearIsometry.enorm_map` (l.204) and
  `LinearIsometryEquiv.nnnorm_map` (l.873). `simp only [SemilinearIsometryClass.nnnorm_map]`
  proves `LinearIsometry.nnnorm_map`, so simp can use the class lemma. -> file-level finding
  (scope/consistency, advisory).

## Matrix.rank_eq_finrank_range_toLin (LinearAlgebra/Matrix/Rank.lean)
- The model lists it as both "modified" and "removed". That is the same declaration seen twice;
  it is not removed in the diff.
- The change replaces a 3-line `have range_e₂` with `e₂.range`, which is fine. Nothing to request.

## LinearEquiv.symm_prodComm (LinearAlgebra/Prod.lean, new)
- It is not a duplicate: `LinearEquiv.prodComm_symm` is absent at base, and `prodComm` is only
  `@[simps apply]`.
- Naming: 8 sibling `prodComm` structures name this lemma `prodComm_symm`, including the direct
  analogue `ContinuousLinearEquiv.prodComm_symm`. Only `LinearIsometryEquiv.symm_prodComm` uses
  the other order. `naming_norm` is insufficient_evidence at the leading-token level, so I judged
  it on the sibling family. -> finding (naming, blocking).
- The attribute `@[simp]` and the `rfl` proof are fine.

## Ideal.cotangentEquivIdeal_symm_apply (RingTheory/Ideal/Cotangent.lean)
- Removing the `(R₂ := R)`, `(R := R)` and `by exact ... (F := ...)` workarounds and their comments
  is good, and the new statement elaborates.
- `I.cotangentEquivIdeal.symm_apply_eq.2 rfl` compiles, with no timeout. -> finding
  (proof-golf, advisory).

## ContinuousLinearMap.iInfKerProjEquiv (Topology/Algebra/Module/Equiv.lean)
- Dropping the explicit `@continuous_subtype_val _ _ fun x => ...` is good.
- `(continuous_apply (i : ι)).comp continuous_subtype_val` compiles. `by dsimp; fun_prop` does not.
  -> finding (style, advisory).

## ContinuousLinearEquiv.submoduleMap (Topology/Algebra/Module/Equiv.lean)
- The PR changes the type from `Submodule.map e p` to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p`.
  The PR's new body compiles against the original type. The unchanged sibling
  `submoduleMap_symm_apply` still states `x : p.map e`, and `LinearIsometryEquiv.submoduleMap`
  uses `Submodule.map e p`. -> finding (correctness/API, blocking): revert the type change.
- The continuity fields can both be `(e(.symm).continuous.comp continuous_subtype_val).subtype_mk _`,
  with `__ := e.toLinearEquiv.submoduleMap p`. This compiles. -> finding (proof-golf, advisory).
- Downstream users of the name are all `LinearMap.submoduleMap` or `LinearEquiv.submoduleMap`, so
  none of them is affected either way.

## PR-level
- "add missing lemmas" covers only `LinearEquiv.symm_prodComm`. The simp/deprecation change in
  LinearIsometry.lean is not mentioned in the description. I made no code finding for this.
