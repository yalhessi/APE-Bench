# The PR model for #34935 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(AlgebraicGeometry): `Semiring` structure on ideal sheaves
- description: (not recoverable at review start)
- changed files: Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean, Mathlib/AlgebraicGeometry/Scheme.lean

## Objects

### `section in Basic.lean` (command, added) [0cb9bc9e44]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Semiring
```

### `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply` (lemma, added) [0f9bc103a6]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
lemma equivOfIsAffine_symm_apply [IsAffine X] (I : Ideal Γ(X, ⊤)) :
    equivOfIsAffine.symm I = ofIdealTop I := rfl
```

### `declaration in Basic.lean` (instance, added) [10ed9e50f6]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : Pow X.IdealSheafData ℕ where
  pow I n := mkOfMemSupportIff (I.ideal ^ n) (by simp [Ideal.map_pow, map_ideal_basicOpen])
    (if n = 0 then ∅ else I.supportSet) fun U x hxU ↦ .symm <| by
    induction n <;> simp_all [-mem_zeroLocus_iff, zeroLocus_mul,
      pow_succ, mem_support_iff_of_mem hxU]
```

### `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow` (lemma, added) [15931fb8c7]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma ideal_pow (n : ℕ) : (I ^ n).ideal = I.ideal ^ n := rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul` (lemma, added) [1971fd431b]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma ideal_mul : (I * J).ideal = I.ideal * J.ideal := rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine` (def, modified) [1d1b182a02]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:removed, statement_or_type:modified, value_or_body:modified
- before the PR:
```lean
@[simps]
def equivOfIsAffine [IsAffine X] : IdealSheafData X ≃o Ideal Γ(X, ⊤) where
  toFun := (ideal · ⟨⊤, isAffineOpen_top X⟩)
  invFun := ofIdealTop
  left_inv I := ext_of_isAffine (by simp)
  right_inv I := by simp
  map_rel_iff' {I J} := ⟨le_of_isAffine, (· _)⟩
```
- as the PR leaves it:
```lean
def equivOfIsAffine [IsAffine X] : IdealSheafData X ≃+*o Ideal Γ(X, ⊤) where
  toFun := (ideal · ⟨⊤, isAffineOpen_top X⟩)
  invFun := ofIdealTop
  left_inv I := ext_of_isAffine (by simp)
  right_inv I := by simp
  map_mul' := by simp
  map_add' := by simp
  map_le_map_iff' := ⟨le_of_isAffine, (· _)⟩
```

### `AlgebraicGeometry.Scheme.IdealSheafData.zero_eq_bot` (lemma, added) [2b1fcf59de]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma zero_eq_bot : (0 : X.IdealSheafData) = ⊥ := rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` (lemma, added) [4099de86ce]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma support_mul : (I * J).support = I.support ⊔ J.support := rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support` (lemma, added) [424f68c65a]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma mem_supportSet_iff_mem_support {I : IdealSheafData X} {x} :
    x ∈ I.supportSet ↔ x ∈ I.support := .rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.inf_mul` (lemma, added) [43c3f5de2a]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma inf_mul : (I ⊔ J) * K = I * K ⊔ J * K := by ext U : 2; exact add_mul _ _ _
```

### `AlgebraicGeometry.Scheme.IdealSheafData.mul_top` (lemma, added) [49914577c2]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma mul_top : I * ⊤ = I := by ext; simp
```

### `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot` (lemma, added) [4b229cb3a2]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma mul_bot : I * ⊥ = ⊥ := by ext; simp
```

### `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` (lemma, added) [5e61935368]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma support_pow (n : ℕ) (hn : n ≠ 0) : (I ^ n).support = I.support := by cases n <;> simp_all
```

### `module_doc in Basic.lean` (module_doc, added) [607ffa67af]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-! We follow `Ideal` and set the simp normal form to be `⊥` and `⊤` and `⊔`. -/
```

### `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul` (lemma, added) [64d34c6412]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma bot_mul : ⊥ * I = ⊥ := by ext; simp
```

### `AlgebraicGeometry.Scheme.IdealSheafData.add_eq_sup` (lemma, added) [6d55d7b081]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl
```

### `declaration in Basic.lean` (instance, added) [6dc0d5ff4e]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : Zero X.IdealSheafData where zero := ⊥
```

### `declaration in Basic.lean` (instance, added) [6f961b2d77]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : Mul X.IdealSheafData where
  mul I J := mkOfMemSupportIff (I.ideal * J.ideal) (by simp [Ideal.map_mul, map_ideal_basicOpen])
    (I.supportSet ∪ J.supportSet) fun U x hxU ↦ by
    simp [-mem_zeroLocus_iff, zeroLocus_mul, mem_support_iff_of_mem hxU]
```

### `section in Basic.lean` (command, added) [75c11543ea]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable (I J K : X.IdealSheafData)
```

### `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul` (lemma, added) [839f865112]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
lemma radical_mul {I J : IdealSheafData X} :
    radical (I * J) = radical I ⊓ radical J := by
  ext U : 2
  simp only [radical_ideal, ideal_mul, Pi.mul_apply, Ideal.radical_mul, ideal_inf, Pi.inf_apply]
```

### `declaration in Basic.lean` (instance, added) [8c5bce832c]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added
- as the PR leaves it:
```lean
instance : IsOrderedRing X.IdealSheafData where
```

### `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf` (lemma, modified) [8f33abb036]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:modified
- before the PR:
```lean
@[simp]
lemma radical_inf {I J : IdealSheafData X} :
    radical (I ⊓ J) = (radical I ⊓ radical J) := by
  ext U : 2
  simp only [radical_ideal, ideal_inf, Pi.inf_apply, Ideal.radical_inf]
```
- as the PR leaves it:
```lean
@[simp]
lemma radical_inf {I J : IdealSheafData X} :
    radical (I ⊓ J) = radical I ⊓ radical J := by
  ext U : 2
  simp only [radical_ideal, ideal_inf, Pi.inf_apply, Ideal.radical_inf]
```

### `declaration in Basic.lean` (instance, added) [96915113ce]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : Add X.IdealSheafData where add := (· ⊔ ·)
```

### `declaration in Basic.lean` (instance, added) [9b0deaf320]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : IdemCommSemiring X.IdealSheafData where
  add_assoc := sup_assoc
  zero_add := bot_sup_eq
  add_zero := sup_bot_eq
  add_comm := sup_comm
  mul_assoc _ _ _ := IdealSheafData.ext (mul_assoc _ _ _)
  mul_comm _ _ := IdealSheafData.ext (mul_comm _ _)
  zero_mul := bot_mul
  mul_zero := mul_bot
  one_mul := top_mul
  mul_one := mul_top
  nsmul := nsmulRec
  left_distrib := mul_inf
  right_distrib := inf_mul
  npow_zero _ := by ext; rfl
  npow_succ _ _ := by ext; rfl
  bot_le _ := bot_le
```

### `AlgebraicGeometry.Scheme.IdealSheafData.top_mul` (lemma, added) [b04a9e8f3b]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma top_mul : ⊤ * I = I := by ext; simp
```

### `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf` (lemma, added) [bcfaa90af0]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma mul_inf : I * (J ⊔ K) = I * J ⊔ I * K := by ext U : 2; exact mul_add _ _ _
```

### `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` (lemma, added) [e0156884c7]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma support_pow_succ (n : ℕ) : (I ^ (n + 1)).support = I.support := rfl
```

### `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply` (lemma, added) [e52e2c940b]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
lemma equivOfIsAffine_apply [IsAffine X] (I : IdealSheafData X) :
    equivOfIsAffine I = I.ideal ⟨⊤, isAffineOpen_top X⟩ := rfl
```

### `declaration in Basic.lean` (instance, added) [e64ca0cb2e]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance : One X.IdealSheafData where one := ⊤
```

### `section in Basic.lean` (command, added) [eeff7d9ad8]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Semiring
```

### `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top` (lemma, added) [fcd1f1fddd]
- file: `Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma one_eq_top : (1 : X.IdealSheafData) = ⊤ := rfl
```

### `namespace in Scheme.lean` (command, added) [6734d9edb8]
- file: `Mathlib/AlgebraicGeometry/Scheme.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open scoped Pointwise in
```

### `AlgebraicGeometry.Scheme.zeroLocus_mul` (lemma, added) [85a0136ba7]
- file: `Mathlib/AlgebraicGeometry/Scheme.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma zeroLocus_mul {U : X.Opens} (I J : Ideal Γ(X, U)) :
    X.zeroLocus (U := U) ↑(I * J) = X.zeroLocus (U := U) I ∪ X.zeroLocus (U := U) J := by
  rw [← X.zeroLocus_setMul, ← X.zeroLocus_span (U := U) (↑I * ↑J), ← Ideal.span_mul_span]
  simp
```

### `AlgebraicGeometry.Scheme.zeroLocus_setMul` (lemma, added) [da9985e78b]
- file: `Mathlib/AlgebraicGeometry/Scheme.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma zeroLocus_setMul {U : X.Opens} (s t : Set Γ(X, U)) :
    X.zeroLocus (s * t) = X.zeroLocus s ∪ X.zeroLocus t := by
  simp only [← Set.image2_mul, zeroLocus_def, Set.biInter_image2]
  simp [Set.compl_inter, ← Set.union_iInter₂, ← Set.iInter₂_union]
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`, `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot`, `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf`, `AlgebraicGeometry.Scheme.IdealSheafData.mul_top` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine`, `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply`, `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact]  -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `AlgebraicGeometry.Scheme.zeroLocus_mul`, `AlgebraicGeometry.Scheme.zeroLocus_setMul` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf`, `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `AlgebraicGeometry.Scheme.IdealSheafData.add_eq_sup`, `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top`, `AlgebraicGeometry.Scheme.IdealSheafData.zero_eq_bot` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply`, `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow`, `AlgebraicGeometry.Scheme.IdealSheafData.inf_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support`, `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot`, `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf`, `AlgebraicGeometry.Scheme.IdealSheafData.mul_top`, `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`, `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`, `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`, `AlgebraicGeometry.Scheme.IdealSheafData.top_mul` -- 12 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact]  -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.add_eq_sup` -> `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_top`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply` -> `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply` -> `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.inf_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot` -> `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf` -> `AlgebraicGeometry.Scheme.IdealSheafData.inf_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_inf` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_bot`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_top` -> `AlgebraicGeometry.Scheme.IdealSheafData.top_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mul_top` -> `AlgebraicGeometry.Scheme.IdealSheafData.bot_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top` -> `AlgebraicGeometry.Scheme.IdealSheafData.add_eq_sup`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top` -> `AlgebraicGeometry.Scheme.IdealSheafData.zero_eq_bot`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf` -> `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.top_mul`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -> `AlgebraicGeometry.Scheme.IdealSheafData.ideal_pow`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.top_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.top_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.mul_top`
- changed_siblings [high]: `AlgebraicGeometry.Scheme.IdealSheafData.zero_eq_bot` -> `AlgebraicGeometry.Scheme.IdealSheafData.one_eq_top`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- changed_siblings [high]: `declaration in Basic.lean` -> `declaration in Basic.lean`
- declaration_dependency [exact]: `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_apply` -> `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine`
- declaration_dependency [exact]: `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine_symm_apply` -> `AlgebraicGeometry.Scheme.IdealSheafData.equivOfIsAffine`
- direct_use_of_changed_declaration [exact]: `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.ideal_mul`
- direct_use_of_changed_declaration [exact]: `AlgebraicGeometry.Scheme.zeroLocus_mul` -> `AlgebraicGeometry.Scheme.zeroLocus_setMul`
- direct_use_of_changed_declaration [exact]: `declaration in Basic.lean` -> `AlgebraicGeometry.Scheme.zeroLocus_mul`
- direct_use_of_changed_declaration [exact]: `declaration in Basic.lean` -> `AlgebraicGeometry.Scheme.zeroLocus_mul`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf` -> `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.radical_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.radical_inf`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_mul` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_pow`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -> `AlgebraicGeometry.Scheme.IdealSheafData.mem_supportSet_iff_mem_support`
- name_family [high]: `AlgebraicGeometry.Scheme.IdealSheafData.support_pow_succ` -> `AlgebraicGeometry.Scheme.IdealSheafData.support_mul`
