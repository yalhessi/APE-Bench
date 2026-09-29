# The PR model for #33285 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(*): golf, add missing lemmas
- description: Cherry-picked parts of #33241
- changed files: Mathlib/Algebra/Module/Submodule/Map.lean, Mathlib/Analysis/Calculus/ImplicitContDiff.lean, Mathlib/Analysis/InnerProductSpace/Orthogonal.lean, Mathlib/Analysis/Normed/Operator/Banach.lean, Mathlib/Analysis/Normed/Operator/LinearIsometry.lean, Mathlib/LinearAlgebra/Matrix/Rank.lean, Mathlib/LinearAlgebra/Prod.lean, Mathlib/RingTheory/Ideal/Cotangent.lean, Mathlib/Topology/Algebra/Module/Equiv.lean

## Objects

### `Submodule.inf_comap_le_comap_add` (theorem, modified) [3a67c51b10]
- file: `Mathlib/Algebra/Module/Submodule/Map.lean`; changed: proof:modified
- before the PR:
```lean
theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂) :
    comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q := by
  rw [SetLike.le_def]
  intro m h
  change f₁ m + f₂ m ∈ q
  change f₁ m ∈ q ∧ f₂ m ∈ q at h
  apply q.add_mem h.1 h.2
```
- as the PR leaves it:
```lean
theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂) :
    comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q := by
  rw [SetLike.le_def]
  intro m h
  simp only [mem_comap, mem_inf, LinearMap.add_apply] at h ⊢
  exact add_mem h.1 h.2
```

### `IsContDiffImplicitAt.implicitFunctionData` (def, modified) [29adb79a6d]
- file: `Mathlib/Analysis/Calculus/ImplicitContDiff.lean`; changed: value_or_body:modified
- before the PR:
```lean
def implicitFunctionData (h : IsContDiffImplicitAt n f f' a) :
    ImplicitFunctionData 𝕜 (E × F) E G where
  leftFun := Prod.fst
  leftDeriv := ContinuousLinearMap.fst 𝕜 E F
  rightFun := f
  rightDeriv := f'
  pt := a
  hasStrictFDerivAt_leftFun := by fun_prop
  hasStrictFDerivAt_rightFun := h.contDiffAt.hasStrictFDerivAt' h.hasFDerivAt h.ne_zero
  range_leftDeriv := LinearMap.range_eq_top_of_surjective _ fun x ↦ ⟨(x, 0), rfl⟩
  range_rightDeriv := by
    apply top_unique
    rw [← LinearMap.range_eq_top_of_surjective _ h.bijective.surjective]
    exact LinearMap.range_comp_le_range _ _
  isCompl_ker := by
    apply IsCompl.of_eq
    · ext x
      rw [Submodule.mem_inf, Submodule.mem_bot, LinearMap.mem_ker, ContinuousLinearMap.coe_fst',
        LinearMap.mem_ker]
      constructor
      · intro ⟨h1, h2⟩
        rw [← Prod.mk.eta (p := x), h1] at h2
        rw [Prod.ext_iff]
        refine ⟨h1, h.bijective.injective ?_⟩
        simp [h2, map_zero]
      · rintro rfl
        exact ⟨rfl, map_zero _⟩
    · ext x
      simp only [Submodule.mem_sup, Submodule.mem_top, iff_true]
      obtain ⟨y, hy⟩ := h.bijective.surjective (f' x)
      exact ⟨(0, y), by simp, x - (0, y), by simp [map_sub, ← hy], by abel⟩
```
- as the PR leaves it:
```lean
def implicitFunctionData (h : IsContDiffImplicitAt n f f' a) :
    ImplicitFunctionData 𝕜 (E × F) E G where
  leftFun := Prod.fst
  leftDeriv := ContinuousLinearMap.fst 𝕜 E F
  rightFun := f
  rightDeriv := f'
  pt := a
  hasStrictFDerivAt_leftFun := by fun_prop
  hasStrictFDerivAt_rightFun := h.contDiffAt.hasStrictFDerivAt' h.hasFDerivAt h.ne_zero
  range_leftDeriv := LinearMap.range_eq_top_of_surjective _ fun x ↦ ⟨(x, 0), rfl⟩
  range_rightDeriv := by
    apply top_unique
    rw [← LinearMap.range_eq_top_of_surjective _ h.bijective.surjective]
    exact LinearMap.range_comp_le_range _ _
  isCompl_ker := by
    apply IsCompl.of_eq
    · ext ⟨x, y⟩
      rw [Submodule.mem_inf, Submodule.mem_bot, LinearMap.mem_ker, ContinuousLinearMap.coe_fst',
        LinearMap.mem_ker, Prod.ext_iff, ← h.bijective.injective.eq_iff]
      simp +contextual [Prod.mk_zero_zero]
    · ext x
      simp only [Submodule.mem_sup, Submodule.mem_top, iff_true]
      obtain ⟨y, hy⟩ := h.bijective.surjective (f' x)
      exact ⟨(0, y), by simp, x - (0, y), by simp [map_sub, ← hy], by abel⟩
```

### `Submodule.IsOrtho.map` (theorem, modified) [5f14939051]
- file: `Mathlib/Analysis/InnerProductSpace/Orthogonal.lean`; changed: proof:modified
- before the PR:
```lean
theorem IsOrtho.map (f : E →ₗᵢ[𝕜] F) {U V : Submodule 𝕜 E} (h : U ⟂ V) : U.map f ⟂ V.map f := by
  rw [isOrtho_iff_inner_eq] at *
  simp_rw [mem_map, forall_exists_index, and_imp, forall_apply_eq_imp_iff₂,
    LinearIsometry.inner_map_map]
  exact h
```
- as the PR leaves it:
```lean
theorem IsOrtho.map (f : E →ₗᵢ[𝕜] F) {U V : Submodule 𝕜 E} (h : U ⟂ V) : U.map f ⟂ V.map f := by
  aesop (add simp [isOrtho_iff_inner_eq])
```

### `ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range` (lemma, modified) [00bd927941]
- file: `Mathlib/Analysis/Normed/Operator/Banach.lean`; changed: proof:modified
- before the PR:
```lean
lemma antilipschitz_of_injective_of_isClosed_range (f : E →L[𝕜] F)
    (hf : Injective f) (hf' : IsClosed (Set.range f)) : ∃ K, AntilipschitzWith K f := by
  let S : (LinearMap.range f) →L[𝕜] E := (f.equivRange hf hf').symm
  use ⟨S.opNorm, S.opNorm_nonneg⟩
  apply ContinuousLinearMap.antilipschitz_of_bound
  intro x
  calc ‖x‖
    _ = ‖S ⟨f x, by simp⟩‖ := by simp [S]
    _ ≤ S.opNorm * ‖f x‖ := le_opNorm S ⟨f x, by simp⟩
```
- as the PR leaves it:
```lean
lemma antilipschitz_of_injective_of_isClosed_range (f : E →L[𝕜] F)
    (hf : Injective f) (hf' : IsClosed (Set.range f)) : ∃ K, AntilipschitzWith K f :=
  ⟨_, .comp (.subtype_coe (Set.range f)) (f.equivRange hf hf').antilipschitz⟩
```

### `ContinuousLinearMap.equivRange_symm_apply` (lemma, modified) [3b51ade302]
- file: `Mathlib/Analysis/Normed/Operator/Banach.lean`; changed: documentation:removed, proof:modified
- before the PR:
```lean
@[simp]
lemma equivRange_symm_apply (hinj : Injective f) (hclo : IsClosed (range f))
    (x : E) : (f.equivRange hinj hclo).symm ⟨f x, by simp⟩ = x := by
  suffices f ((f.equivRange hinj hclo).symm ⟨f x, by simp⟩) = f x from hinj this
  trans f ((f.equivRange hinj hclo).symm.toLinearEquiv ⟨f x, by simp⟩)
  · rfl -- is there an API lemma for this already?
  simp only [ContinuousLinearEquiv.toLinearEquiv_symm, equivRange_symm_toLinearEquiv]
  set x' : LinearMap.range f := ⟨f x, by simp⟩
  set f' : E →ₛₗ[σ] F := ↑f
  change f' ((LinearEquiv.ofInjective f' hinj).symm x') = _
  rw [LinearEquiv.ofInjective_symm_apply (f := f') (h := hinj) x']
```
- as the PR leaves it:
```lean
@[simp]
lemma equivRange_symm_apply (hinj : Injective f) (hclo : IsClosed (range f))
    (x : E) : (f.equivRange hinj hclo).symm ⟨f x, by simp⟩ = x := by
  simp [ContinuousLinearEquiv.symm_apply_eq, Subtype.ext_iff]
```

### `LinearIsometry.isComplete_image_iff` (theorem, modified) [17af210b39]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: attributes:added, documentation:removed, name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
lemma isEmbedding (f : F →ₛₗᵢ[σ₁₂] E₂) : IsEmbedding f := f.isometry.isEmbedding

-- Should be `@[simp]` but it doesn't fire due to https://github.com/leanprover/lean4/issues/3107.
```
- as the PR leaves it:
```lean
@[simp]
theorem isComplete_image_iff [SemilinearIsometryClass 𝓕 σ₁₂ E E₂] (f : 𝓕) {s : Set E} :
    IsComplete (f '' s) ↔ IsComplete s :=
  _root_.isComplete_image_iff (SemilinearIsometryClass.isometry f).isUniformInducing
```

### `LinearIsometry.isComplete_image_iff'` (theorem, modified) [3a3d5869ad]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: attributes:modified, documentation:removed
- before the PR:
```lean
@[simp] -- Should be replaced with `LinearIsometry.isComplete_image_iff` when https://github.com/leanprover/lean4/issues/3107 is fixed.
theorem isComplete_image_iff' (f : LinearIsometry σ₁₂ E E₂) {s : Set E} :
    IsComplete (f '' s) ↔ IsComplete s :=
  LinearIsometry.isComplete_image_iff _
```
- as the PR leaves it:
```lean
@[deprecated LinearIsometry.isComplete_image_iff (since := "2025-12-25")]
theorem isComplete_image_iff' (f : LinearIsometry σ₁₂ E E₂) {s : Set E} :
    IsComplete (f '' s) ↔ IsComplete s :=
  LinearIsometry.isComplete_image_iff _
```

### `Matrix.rank_eq_finrank_range_toLin` (theorem, modified) [9288162f03]
- file: `Mathlib/LinearAlgebra/Matrix/Rank.lean`; changed: proof:modified
- before the PR:
```lean
theorem rank_eq_finrank_range_toLin [Finite m] [DecidableEq n] {M₁ M₂ : Type*} [AddCommGroup M₁]
    [AddCommGroup M₂] [Module R M₁] [Module R M₂] (A : Matrix m n R) (v₁ : Basis m R M₁)
    (v₂ : Basis n R M₂) : A.rank = finrank R (LinearMap.range (toLin v₂ v₁ A)) := by
  cases nonempty_fintype m
  let e₁ := (Pi.basisFun R m).equiv v₁ (Equiv.refl _)
  let e₂ := (Pi.basisFun R n).equiv v₂ (Equiv.refl _)
  have range_e₂ : LinearMap.range e₂ = ⊤ := by
    rw [LinearMap.range_eq_top]
    exact e₂.surjective
  refine LinearEquiv.finrank_eq (e₁.ofSubmodules _ _ ?_)
  rw [← LinearMap.range_comp, ← LinearMap.range_comp_of_range_eq_top (toLin v₂ v₁ A) range_e₂]
  congr 1
  apply LinearMap.pi_ext'
  rintro i
  apply LinearMap.ext_ring
  have aux₁ := toLin_self (Pi.basisFun R n) (Pi.basisFun R m) A i
  have aux₂ := Basis.equiv_apply (Pi.basisFun R n) i v₂
  rw [toLin_eq_toLin', toLin'_apply'] at aux₁
  rw [Pi.basisFun_apply] at aux₁ aux₂
  simp only [e₁, e₂, LinearMap.comp_apply, LinearEquiv.coe_coe, Equiv.refl_apply,
    aux₁, aux₂, LinearMap.coe_single, toLin_self, map_sum, map_smul, Basis.equiv_apply]
```
- as the PR leaves it:
```lean
theorem rank_eq_finrank_range_toLin [Finite m] [DecidableEq n] {M₁ M₂ : Type*} [AddCommGroup M₁]
    [AddCommGroup M₂] [Module R M₁] [Module R M₂] (A : Matrix m n R) (v₁ : Basis m R M₁)
    (v₂ : Basis n R M₂) : A.rank = finrank R (LinearMap.range (toLin v₂ v₁ A)) := by
  cases nonempty_fintype m
  let e₁ := (Pi.basisFun R m).equiv v₁ (Equiv.refl _)
  let e₂ := (Pi.basisFun R n).equiv v₂ (Equiv.refl _)
  refine LinearEquiv.finrank_eq (e₁.ofSubmodules _ _ ?_)
  rw [← LinearMap.range_comp, ← LinearMap.range_comp_of_range_eq_top (toLin v₂ v₁ A) e₂.range]
  congr 1
  apply LinearMap.pi_ext'
  rintro i
  apply LinearMap.ext_ring
  have aux₁ := toLin_self (Pi.basisFun R n) (Pi.basisFun R m) A i
  have aux₂ := Basis.equiv_apply (Pi.basisFun R n) i v₂
  rw [toLin_eq_toLin', toLin'_apply'] at aux₁
  rw [Pi.basisFun_apply] at aux₁ aux₂
  simp only [e₁, e₂, LinearMap.comp_apply, LinearEquiv.coe_coe, Equiv.refl_apply,
    aux₁, aux₂, LinearMap.coe_single, toLin_self, map_sum, map_smul, Basis.equiv_apply]
```

### `Matrix.rank_eq_finrank_range_toLin` (theorem, removed) [d6ee612016]
- file: `Mathlib/LinearAlgebra/Matrix/Rank.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem rank_eq_finrank_range_toLin [Finite m] [DecidableEq n] {M₁ M₂ : Type*} [AddCommGroup M₁]
    [AddCommGroup M₂] [Module R M₁] [Module R M₂] (A : Matrix m n R) (v₁ : Basis m R M₁)
    (v₂ : Basis n R M₂) : A.rank = finrank R (LinearMap.range (toLin v₂ v₁ A)) := by
  cases nonempty_fintype m
  let e₁ := (Pi.basisFun R m).equiv v₁ (Equiv.refl _)
  let e₂ := (Pi.basisFun R n).equiv v₂ (Equiv.refl _)
  have range_e₂ : LinearMap.range e₂ = ⊤ := by
    rw [LinearMap.range_eq_top]
    exact e₂.surjective
  refine LinearEquiv.finrank_eq (e₁.ofSubmodules _ _ ?_)
  rw [← LinearMap.range_comp, ← LinearMap.range_comp_of_range_eq_top (toLin v₂ v₁ A) range_e₂]
  congr 1
  apply LinearMap.pi_ext'
  rintro i
  apply LinearMap.ext_ring
  have aux₁ := toLin_self (Pi.basisFun R n) (Pi.basisFun R m) A i
  have aux₂ := Basis.equiv_apply (Pi.basisFun R n) i v₂
  rw [toLin_eq_toLin', toLin'_apply'] at aux₁
  rw [Pi.basisFun_apply] at aux₁ aux₂
  simp only [e₁, e₂, LinearMap.comp_apply, LinearEquiv.coe_coe, Equiv.refl_apply,
    aux₁, aux₂, LinearMap.coe_single, toLin_self, map_sum, map_smul, Basis.equiv_apply]
```

### `LinearEquiv.symm_prodComm` (theorem, added) [862a7d5a10]
- file: `Mathlib/LinearAlgebra/Prod.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem symm_prodComm : (prodComm R M M₂).symm = prodComm R M₂ M := rfl
```

### `Ideal.cotangentEquivIdeal_symm_apply` (theorem, modified) [5d5034afc1]
- file: `Mathlib/RingTheory/Ideal/Cotangent.lean`; changed: documentation:removed, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem cotangentEquivIdeal_symm_apply (x : R) (hx : x ∈ I) :
    -- Note: https://github.com/leanprover-community/mathlib4/pull/8386 had to specify `(R₂ := R)` because `I.toCotangent` suggested `R ⧸ I^2` instead
    I.cotangentEquivIdeal.symm ⟨(I ^ 2).mkQ x,
      -- timeout (200000 heartbeats) without `by exact`
      by exact Submodule.mem_map_of_mem (F := R →ₗ[R] R ⧸ I ^ 2) (f := (I ^ 2).mkQ) hx⟩ =
      I.toCotangent (R := R) ⟨x, hx⟩ := by
  apply I.cotangentEquivIdeal.injective
  rw [I.cotangentEquivIdeal.apply_symm_apply]
  ext
  rfl
```
- as the PR leaves it:
```lean
theorem cotangentEquivIdeal_symm_apply (x : R) (hx : x ∈ I) :
    I.cotangentEquivIdeal.symm ⟨(I ^ 2).mkQ x, Submodule.mem_map_of_mem hx⟩ =
      I.toCotangent ⟨x, hx⟩ := by
  rw [I.cotangentEquivIdeal.symm_apply_eq]
  ext
  simp
```

### `ContinuousLinearMap.iInfKerProjEquiv` (def, modified) [539d6f89f2]
- file: `Mathlib/Topology/Algebra/Module/Equiv.lean`; changed: value_or_body:modified
- before the PR:
```lean
def iInfKerProjEquiv {I J : Set ι} [DecidablePred fun i => i ∈ I] (hd : Disjoint I J)
    (hu : Set.univ ⊆ I ∪ J) :
    (⨅ i ∈ J, ker (proj i : (∀ i, φ i) →L[R] φ i) :
    Submodule R (∀ i, φ i)) ≃L[R] ∀ i : I, φ i where
  toLinearEquiv := LinearMap.iInfKerProjEquiv R φ hd hu
  continuous_toFun :=
    continuous_pi fun i =>
      Continuous.comp (continuous_apply (A := φ) i) <|
        @continuous_subtype_val _ _ fun x =>
          x ∈ (⨅ i ∈ J, ker (proj i : (∀ i, φ i) →L[R] φ i) : Submodule R (∀ i, φ i))
  continuous_invFun :=
    Continuous.subtype_mk
      (continuous_pi fun i => by
        dsimp
        split_ifs <;> [apply continuous_apply; exact continuous_zero])
      _
```
- as the PR leaves it:
```lean
def iInfKerProjEquiv {I J : Set ι} [DecidablePred fun i => i ∈ I] (hd : Disjoint I J)
    (hu : Set.univ ⊆ I ∪ J) :
    (⨅ i ∈ J, ker (proj i : (∀ i, φ i) →L[R] φ i) :
    Submodule R (∀ i, φ i)) ≃L[R] ∀ i : I, φ i where
  toLinearEquiv := LinearMap.iInfKerProjEquiv R φ hd hu
  continuous_toFun :=
    continuous_pi fun i =>
      Continuous.comp (continuous_apply (A := φ) i) <| continuous_subtype_val
  continuous_invFun :=
    Continuous.subtype_mk
      (continuous_pi fun i => by
        dsimp
        split_ifs <;> [apply continuous_apply; exact continuous_zero])
      _
```

### `ContinuousLinearEquiv.submoduleMap` (def, modified) [7a136bf3d8]
- file: `Mathlib/Topology/Algebra/Module/Equiv.lean`; changed: statement_or_type:modified, value_or_body:modified
- before the PR:
```lean
def submoduleMap (e : M ≃SL[σ₁₂] M₂) (p : Submodule R M) :
    p ≃SL[σ₁₂] Submodule.map e p where
  toLinearMap := (e.comp p.subtype).codRestrict (p.map e) (fun ⟨c, hc⟩ ↦ by simpa)
  invFun := (e.symm.comp (p.map e).subtype).codRestrict p (fun ⟨c, y, hy, eyc⟩ ↦ by
    simpa [← eyc, e.symm_apply_apply])
  left_inv x := by ext; simp
  right_inv x := by ext; simp
  continuous_toFun := by
    have : Continuous (e.comp p.subtype) := by dsimp; fun_prop
    dsimp
    exact continuous_induced_rng.mpr this
  continuous_invFun := by
    have : Continuous (e.symm.comp (p.map e).subtype) := by dsimp; fun_prop
    dsimp
    exact continuous_induced_rng.mpr this
```
- as the PR leaves it:
```lean
def submoduleMap (e : M ≃SL[σ₁₂] M₂) (p : Submodule R M) :
    p ≃SL[σ₁₂] Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p where
  __ := LinearEquiv.submoduleMap e.toLinearEquiv p
  continuous_toFun := map_continuous ((e.toContinuousLinearMap.comp p.subtypeL).codRestrict _ _)
  continuous_invFun := (map_continuous e.symm).restrict fun x hx ↦
    ((LinearEquiv.submoduleMap e.toLinearEquiv p).symm ⟨x, hx⟩).2
```

## Removed or renamed

- `Matrix.rank_eq_finrank_range_toLin`

## Families (declarations that may be one decision)

- [exact] `Matrix.rank_eq_finrank_range_toLin` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `LinearIsometry.isComplete_image_iff`, `LinearIsometry.isComplete_image_iff'` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `LinearIsometry.isComplete_image_iff` -> `LinearIsometry.isComplete_image_iff'`
- changed_siblings [high]: `LinearIsometry.isComplete_image_iff'` -> `LinearIsometry.isComplete_image_iff`
- direct_use_of_changed_declaration [exact]: `LinearIsometry.isComplete_image_iff'` -> `LinearIsometry.isComplete_image_iff`
- name_family [high]: `LinearIsometry.isComplete_image_iff` -> `LinearIsometry.isComplete_image_iff'`
- name_family [high]: `LinearIsometry.isComplete_image_iff'` -> `LinearIsometry.isComplete_image_iff`
- name_family [high]: `Matrix.rank_eq_finrank_range_toLin` -> `Matrix.rank_eq_finrank_range_toLin`
- name_family [high]: `Matrix.rank_eq_finrank_range_toLin` -> `Matrix.rank_eq_finrank_range_toLin`
