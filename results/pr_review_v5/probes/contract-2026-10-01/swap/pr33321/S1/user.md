# Pull request #33321

**Title:** feat: linear independence of indecomposable roots of a root system

**Description:**
Work toward https://github.com/leanprover-community/mathlib4/issues/28717

**Changed files:**
  - `Mathlib.lean`
  - `Mathlib/Algebra/Group/Hom/Basic.lean`
  - `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`
  - `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`
  - `Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean`
  - `Mathlib/LinearAlgebra/RootSystem/RootPositive.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33321 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: linear independence of indecomposable roots of a root system
- description: Work toward https://github.com/leanprover-community/mathlib4/issues/28717
- changed files: Mathlib.lean, Mathlib/Algebra/Group/Hom/Basic.lean, Mathlib/Algebra/Group/Irreducible/Indecomposable.lean, Mathlib/LinearAlgebra/RootSystem/BaseExists.lean, Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean, Mathlib/LinearAlgebra/RootSystem/RootPositive.lean

## Objects

### `import in Mathlib.lean` (import, modified) [6e05913552]
- file: `Mathlib.lean`; changed: imports:added

### `invMonoidHom_apply` (theorem, modified) [0d8e8df9b0]
- file: `Mathlib/Algebra/Group/Hom/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem invMonoidHom_apply (a : α) : invMonoidHom a = a⁻¹ := rfl
```
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem invMonoidHom_apply (a : α) : invMonoidHom a = a⁻¹ := rfl
```

### `coe_invMonoidHom` (theorem, modified) [9db156d451]
- file: `Mathlib/Algebra/Group/Hom/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem coe_invMonoidHom : (invMonoidHom : α → α) = Inv.inv := rfl
```
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem coe_invMonoidHom : (invMonoidHom : α → α) = Inv.inv := rfl
```

### `invMonoidHom_comp_invMonoidHom` (theorem, added) [d8c5c998e4]
- file: `Mathlib/Algebra/Group/Hom/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem invMonoidHom_comp_invMonoidHom : (invMonoidHom (α := α)).comp invMonoidHom = .id _ := by
  ext; simp
```

### `IsMulIndecomposable.image_baseOf_inv_comp_eq` (lemma, added) [0ebd514624]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma IsMulIndecomposable.image_baseOf_inv_comp_eq [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) :
    v '' baseOf v (invMonoidHom.comp f) = (invMonoidHom ∘ v) '' baseOf v f := by
  suffices ∀ (f : G →* S),
      v '' baseOf v (invMonoidHom.comp f) ⊆ (invMonoidHom ∘ v) '' baseOf v f by
    apply subset_antisymm (this f)
    replace this := image_mono (f := invMonoidHom) <| this (invMonoidHom.comp f)
    rw [← MonoidHom.comp_assoc, invMonoidHom_comp_invMonoidHom, MonoidHom.id_comp, image_comp,
      ← image_comp invMonoidHom invMonoidHom, ← MonoidHom.coe_comp, invMonoidHom_comp_invMonoidHom,
      ← image_comp] at this
    simpa using this
  clear f
  rintro f g ⟨i, ⟨hi, hi'⟩, rfl⟩
  refine ⟨i⁻¹, ⟨by simpa [hv_inv] using hi, fun j hj k hk hi ↦ ?_⟩, by simp [hv_inv]⟩
  replace hi : v i = v j⁻¹ * v k⁻¹ := by
    rwa [hv_inv, inv_eq_iff_eq_inv, mul_inv, ← hv_inv, ← hv_inv] at hi
  specialize hi' j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv]) hi
  aesop
```

### `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` (lemma, added) [263e325729]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma mem_or_inv_mem_closure_baseOf [Finite ι] [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) (i : ι) :
     v i    ∈ Submonoid.closure (v '' baseOf v f) ∨
    (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by
  rw [Submonoid.closure_image_isMulIndecomposable_baseOf v f]
  rcases lt_or_gt_of_ne (hf i) with hj | hj
  · right
    exact Submonoid.subset_closure ⟨i⁻¹, by simpa [hv_inv]⟩
  · left
    exact Submonoid.subset_closure ⟨i, by simpa⟩
```

### `import in Indecomposable.lean` (import, modified) [2643c4c816]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: imports:added

### `Submonoid.closure_image_isMulIndecomposable_baseOf` (lemma, modified) [32f7e07b63]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
@[to_additive /-- Given a finite family of points `v` in an additive monoid `M`, together with a
morphism into a linearly-ordered additive monoid `f : M →+ S`, the submonoid generated by those
points of `v` which lie in the half space where `f > 0` is generated by the subset of such points
which are indecomposable with respect to points in this half space.

If `v` is the set of roots of a crystallographic root system and `S = ℚ`, then this is
[serre1965](Ch. V, §9, Lemma 2) and it may be used to prove that the root system has a base. -/]
lemma Submonoid.closure_image_one_lt_and_isMulIndecomposable [Finite ι]
    {S : Type*} [CommMonoid S] [LinearOrder S] [IsOrderedCancelMonoid S]
    (v : ι → M) (f : M →* S) :
    closure (v '' {i | IsMulIndecomposable v {j | 1 < f (v j)} i}) =
      closure (v '' {i | 1 < f (v i)}) := by
  refine le_antisymm (closure_mono (image_mono <| by aesop)) (closure_le.mpr ?_)
  rintro - ⟨i, hi : 1 < f (v i), rfl⟩
  by_contra hi'
  let t : Set ι := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}
  let s : Set ι := {j | 1 < f (v j) ∧ v j ∉ closure (v '' t)}
  have hne : s.Nonempty := ⟨i, hi, hi'⟩
  clear! i
  obtain ⟨i, hi⟩ := s.toFinite.exists_minimalFor (f ∘ v) s hne
  have ⟨(hi₀ : 1 < f (v i)), (hi₁ : v i ∉ _)⟩ : i ∈ s := hi.prop
  have hi₂ (k : ι) (hk₀ : 1 < f (v k)) (hk₁ : f (v k) < f (v i)) : v k ∈ closure (v '' t) := by
    by_contra hk₂; exact not_le.mpr hk₁ <| hi.le_of_le ⟨hk₀, hk₂⟩ hk₁.le
  have hi₃ : i ∉ t := by contrapose! hi₁; exact subset_closure <| mem_image_of_mem v hi₁
  obtain ⟨j, k, hj, hk, hjk⟩ : ∃ (j k : ι) (hj : 1 < f (v j)) (hk : 1 < f (v k)),
      v i = v j * v k := by
    grind [IsMulIndecomposable]
  have hj' : v j ∈ closure (v '' t) := hi₂ j hj <| by aesop
  have hk' : v k ∈ closure (v '' t) := hi₂ k hk <| by aesop
  replace hjk : v i ∈ closure (v '' t) := hjk ▸ mul_mem hj' hk'
  exact hi₁ hjk
```
- as the PR leaves it:
```lean
@[to_additive /-- Given a finite family of points `v` in an additive monoid `M`, together with a
morphism into a linearly-ordered additive monoid `f : M →+ S`, the submonoid generated by those
points of `v` which lie in the half space where `f > 0` is generated by the subset of such points
which are indecomposable with respect to points in this half space.

If `v` is the set of roots of a crystallographic root system and `S = ℚ`, then this is
[serre1965](Ch. V, §9, Lemma 2) and it may be used to prove that the root system has a base. -/]
lemma Submonoid.closure_image_isMulIndecomposable_baseOf [Finite ι]
    [CommMonoid S] [IsOrderedCancelMonoid S]
    (v : ι → M) (f : M →* S) :
    closure (v '' IsMulIndecomposable.baseOf v f) = closure (v '' {i | 1 < f (v i)}) := by
  refine le_antisymm (closure_mono (image_mono <| IsMulIndecomposable.baseOf_subset_one_lt v f))
    (closure_le.mpr ?_)
  rintro - ⟨i, hi : 1 < f (v i), rfl⟩
  by_contra hi'
  let t : Set ι := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}
  let s : Set ι := {j | 1 < f (v j) ∧ v j ∉ closure (v '' t)}
  have hne : s.Nonempty := ⟨i, hi, hi'⟩
  clear! i
  obtain ⟨i, hi⟩ := s.toFinite.exists_minimalFor (f ∘ v) s hne
  have ⟨(hi₀ : 1 < f (v i)), (hi₁ : v i ∉ _)⟩ : i ∈ s := hi.prop
  have hi₂ (k : ι) (hk₀ : 1 < f (v k)) (hk₁ : f (v k) < f (v i)) : v k ∈ closure (v '' t) := by
    by_contra hk₂; exact not_le.mpr hk₁ <| hi.le_of_le ⟨hk₀, hk₂⟩ hk₁.le
  have hi₃ : i ∉ t := by contrapose! hi₁; exact subset_closure <| mem_image_of_mem v hi₁
  obtain ⟨j, k, hj, hk, hjk⟩ : ∃ (j k : ι) (hj : 1 < f (v j)) (hk : 1 < f (v k)),
      v i = v j * v k := by
    grind [IsMulIndecomposable]
  have hj' : v j ∈ closure (v '' t) := hi₂ j hj <| by aesop
  have hk' : v k ∈ closure (v '' t) := hi₂ k hk <| by aesop
  replace hjk : v i ∈ closure (v '' t) := hjk ▸ mul_mem hj' hk'
  exact hi₁ hjk
```

### `section in Indecomposable.lean` (command, modified) [3e04d8311f]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: namespace:modified
- before the PR:
```lean
variable {ι M : Type*} [Monoid M]
```
- as the PR leaves it:
```lean
variable {ι M G S : Type*} [Monoid M] [CommGroup G] [LinearOrder S]
```

### `IsMulIndecomposable.pairwise_div_notMem_range` (lemma, added) [4c92bdbde5]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma pairwise_div_notMem_range [InvolutiveInv ι]
    (v : ι → G)
    (hv_one : ∀ i, v i ≠ 1)
    (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (s t : Set ι)
    (hst : s ⊆ IsMulIndecomposable v t)
    (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
  have h_sub : s ⊆ t := hst.trans (IsMulIndecomposable.subset _ _)
  intro i hi j hj hne
  by_contra! ⟨k, hk⟩
  rcases hv_t k with hk' | hk'
  · suffices ¬ IsMulIndecomposable v t i from this (hst hi)
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k, hk', j, h_sub hj, by simp [hk]⟩
  · suffices ¬ IsMulIndecomposable v t j from this (hst hj)
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k⁻¹, hk', i, h_sub hi, by simp [hv_inv, hk]⟩
```

### `IsMulIndecomposable.pairwise_div_notMem_range'` (lemma, added) [63c3fb4fae]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma pairwise_div_notMem_range' [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1)
    (s : Set ι) (hst : s ⊆ IsMulIndecomposable v {i | 1 < f (v i)}) :
    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
  apply pairwise_div_notMem_range v hv_one hv_inv s {i | 1 < f (v i)} hst fun i ↦ ?_
  simpa [hv_inv] using (hf i).symm
```

### `IsMulIndecomposable.baseOf_subset_one_lt` (lemma, added) [75b93aa1e1]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma IsMulIndecomposable.baseOf_subset_one_lt [Monoid S] (v : ι → M) (f : M →* S) :
    IsMulIndecomposable.baseOf v f ⊆ {i | 1 < f (v i)} :=
  IsMulIndecomposable.subset _ _
```

### `namespace in Indecomposable.lean` (command, added) [a614fe9037]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace IsMulIndecomposable
```

### `section in Indecomposable.lean` (command, added) [a8618e71ef]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end IsMulIndecomposable
```

### `IsMulIndecomposable.baseOf` (def, added) [bc8651a645]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, documentation:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
@[to_additive /-- The "base" of `v` relative to a morphism `f`.

In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
base of the root system associated to `f`. -/]
def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  IsMulIndecomposable v {i | 1 < f (v i)}
```

### `IsMulIndecomposable.pairwise_baseOf_div_notMem` (lemma, added) [c5df667ef5]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v :=
  pairwise_div_notMem_range' v hv_inv f hf (baseOf v f) (.refl _)
```

### `IsMulIndecomposable.subset` (lemma, added) [d7f263bf30]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
protected lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) :
    {i | IsMulIndecomposable v s i} ⊆ s := by
  aesop
```

### `command in Indecomposable.lean` (command, added) [ead4a5a012]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
```

### `Subgroup.closure_image_isMulIndecomposable_baseOf` (lemma, added) [ee40dc9497]
- file: `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma Subgroup.closure_image_isMulIndecomposable_baseOf [Finite ι] [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    closure (v '' IsMulIndecomposable.baseOf v f) = closure (range v) := by
  rw [← image_univ]
  refine le_antisymm (closure_mono (image_mono <| by simp)) ((closure_le _).mpr ?_)
  have : univ = {i | 1 < f (v i)} ∪ {i | f (v i) < 1} := by ext i; simp [(hf i).symm]
  rw [this, image_union, union_subset_iff]
  refine ⟨le_trans ?_ (le_closure_toSubmonoid (v '' IsMulIndecomposable.baseOf v f)), ?_⟩
  · simp [Submonoid.closure_image_isMulIndecomposable_baseOf]
  · let f' : G →* S := invMonoidHom.comp f
    have h₁ : (invMonoidHom ∘ v) '' IsMulIndecomposable.baseOf v f' =
        v '' IsMulIndecomposable.baseOf v f := by
      rw [image_comp, IsMulIndecomposable.image_baseOf_inv_comp_eq v hv_inv f, image_comp,
        ← image_comp]
      simp
    have h₂ : v '' {i | f (v i) < 1} = v '' {i | 1 < f' (v i)} := by simp [f']
    rw [h₂, ← h₁, image_comp, coe_invMonoidHom, image_inv_eq_inv, closure_inv]
    refine le_trans ?_ (le_closure_toSubmonoid (v '' IsMulIndecomposable.baseOf v f'))
    simp [Submonoid.closure_image_isMulIndecomposable_baseOf]
```

### `section in BaseExists.lean` (command, added) [0048493eaf]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {ι R M N : Type*} [Finite ι] [AddCommGroup M] [AddCommGroup N]
```

### `command in BaseExists.lean` (command, added) [0927a7c92d]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- This is [serre1965](Ch. V, §9, Lemma 3). -/
```

### `RootPairing.linearIndepOn_root_baseOf'` (lemma, added) [1463dc51e4]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma linearIndepOn_root_baseOf' [IsDomain R] {S : Type*}
    [LinearOrder S] [CommRing S] [IsStrictOrderedRing S] [Algebra S R] [FaithfulSMul S R]
    [Module S M] [IsScalarTower S R M] [Module S N] [IsScalarTower S R N]
    [P.IsValuedIn S] [P.IsCrystallographic]
    (f : Dual S M) (hf : ∀ i, f (P.root i) ≠ 0) :
    LinearIndepOn S P.root (baseOf P.root (f : M →+ S)) := by
  have : CharZero R := Algebra.charZero_of_charZero S R
  have : Fintype ι := Fintype.ofFinite ι
  let M₀ := span S (range P.root)
  let v (i : baseOf P.root (f : M →+ S)) : M₀ := P.rootSpanMem S i
  change LinearIndependent S (M₀.subtype ∘ v)
  suffices LinearIndependent S v by
    rwa [LinearMap.linearIndependent_iff_of_disjoint M₀.subtype (by simp)]
  let f' : Dual S M₀ := f ∘ₗ M₀.subtype
  obtain ⟨B, hB⟩ : ∃ B : P.RootPositiveForm S, B.posForm.toQuadraticMap.PosDef :=
    ⟨P.posRootForm S, by simpa using P.posRootForm_rootFormIn_posDef S⟩
  have hp (i : baseOf P.root (f : M →+ S)) : 0 < f' (v i) := by obtain ⟨i, -, hi⟩ := i; simpa
  have hn : Pairwise fun (i j : baseOf P.root (f : M →+ S)) ↦ B.posForm (v i) (v j) ≤ 0 := by
    rintro ⟨i, hi⟩ ⟨j, hj⟩ hij
    rw [B.posForm_apply_root_root_le_zero_iff, ← P.algebraMap_pairingIn' S ℤ]
    simpa using P.baseOf_pairwise_pairing_le_zero _ hf (by simpa) (by simpa) (by aesop : i ≠ j)
  exact LinearMap.BilinForm.linearIndependent_of_pairwise_le_zero B.posForm hB f' v hp hn
```

### `section in BaseExists.lean` (command, added) [17a6d57886]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Field
```

### `RootPairing.baseOf_pairwise_pairing_le_zero` (lemma, added) [43382ed889]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma baseOf_pairwise_pairing_le_zero [CharZero R] [IsDomain R] [P.IsCrystallographic]
    (hf : ∀ i, f (P.root i) ≠ 0) :
    (baseOf P.root f).Pairwise fun i j ↦ P.pairingIn ℤ i j ≤ 0 := by
  letI _i := P.indexNeg
  intro i hi j hj hne
  have := IsAddIndecomposable.pairwise_baseOf_sub_notMem P.root (by simp) f hf hi hj hne
  contrapose! this
  exact P.root_sub_root_mem_of_pairingIn_pos this hne
```

### `section in BaseExists.lean` (command, added) [593648e19f]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)
  {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)
```

### `section in BaseExists.lean` (command, added) [68bc7d261e]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end RootPairing
```

### `section in BaseExists.lean` (command, added) [7d1999d176]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [Field R] [CharZero R] [Module R M] [Module R N] (P : RootPairing ι R M N)
  [P.IsRootSystem] [P.IsCrystallographic]
```

### `command in BaseExists.lean` (command, added) [862506394e]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- This lemma is usually established for root systems with coefficients `R` equal to `ℚ` or `ℝ`, in
which case one may take `S = R`. However our statement allows for more general coefficients such as
`R = ℂ` and `S = ℚ`.

This lemma is mostly a stepping stone en route to `RootPairing.linearIndepOn_root_baseOf` (where
linear independence is established over `R` rather than just `S`) except that this version does not
make the field assumption and so covers the case `S = R = ℤ` which the latter does not. -/
```

### `section in BaseExists.lean` (command, added) [8cf79df453]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section CommRing
```

### `module_doc in BaseExists.lean` (module_doc, added) [a778bc7ea8]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Existence of bases for crystallographic root systems

## Implementation details

The proof needs a set of ordered coefficients, even though the existence ultimate statement does
not. There are at least two ways to deal with this:
 (a) Using the fact that a crystallographic root system induces a `ℚ`-structure, pass to the root
     system over `ℚ` defined by `RootPairing.restrictScalarsRat`, and develop a theory of base
     change for root system bases.
 (b) Introduce a second set of ordered coefficients (ultimately taken to be `ℚ`) and develop a
     theory with two sets of coefficients simultaneously in play.

It is not really clear which is the better approach but here we opt for approach (b) as it seems
to yield slightly more general results.

## TODO

1. Prove that for crystallographic reduced root systems, the axiom `coroot_mem_or_neg_mem` appearing
   in `RootPairing.Base` follows from the others, and combine this with
   `RootPairing.linearIndepOn_coroot_iff` to thus provide an alternate constructor for
   `RootPairing.Base` which demands only the hypotheses on the roots.
2. [Easy given 1 above] Prove that every reduced crystallographic root system has a base by
   combining the constructor in 1 above with `RootPairing.linearIndepOn_root_baseOf`,
   `IsAddIndecomposable.mem_or_neg_mem_closure_baseOf`, `Module.exists_dual_forall_apply_ne_zero`.

-/
```

### `command in BaseExists.lean` (command, added) [b947499043]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
@[expose] public section
```

### `section in BaseExists.lean` (command, added) [c1b1c66635]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Field
```

### `section in BaseExists.lean` (command, added) [cb2fc3f86b]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end CommRing
```

### `RootPairing.linearIndepOn_root_baseOf` (lemma, added) [ce00c1368a]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma linearIndepOn_root_baseOf [Module ℚ M] [Module ℚ N]
    (f : Dual ℚ M) (hf : ∀ i, f (P.root i) ≠ 0) :
    LinearIndepOn R P.root (baseOf P.root (f : M →+ ℚ)) := by
  letI := P.indexNeg
  have : Fintype (baseOf P.root (f : M →+ ℚ)) := Fintype.ofFinite _
  let v (i : baseOf P.root (f : M →+ ℚ)) : P.rootSpan ℚ := P.rootSpanMem ℚ i
  change LinearIndependent R ((P.rootSpan ℚ).subtype ∘ v)
  have h_span : span ℚ (range v) = ⊤ := by
    suffices span ℚ (range v) = span ℚ (range (P.rootSpanMem ℚ)) by
      rw [this, eq_top_iff, ← LinearMap.map_le_map_iff' (f := (P.rootSpan ℚ).subtype) (by simp),
        map_span, ← image_univ, ← image_comp]
      simp
    apply le_antisymm (span_mono fun x i ↦ by aesop) (span_le.mpr ?_)
    rintro - ⟨i, rfl⟩
    suffices (P.rootSpanMem ℚ i : M) ∈ span ℚ (P.root '' baseOf P.root (f : M →+ ℚ)) by
      rw [← (injective_subtype (P.rootSpan ℚ)).mem_set_image, ← map_coe, SetLike.mem_coe, map_span,
        ← image_univ, ← image_comp]
      convert this
      aesop
    rw [← span_span_of_tower ℤ, ← Submodule.coe_toAddSubgroup, span_int_eq_addSubgroupClosure,
      AddSubgroup.closure_image_isAddIndecomposable_baseOf P.root (by simp) (f : M →+ ℚ) (by simpa)]
    exact subset_span <| AddSubgroup.subset_closure <| by simp
  have h_card : Nat.card (baseOf P.root (f : M →+ ℚ)) = finrank R M := by
    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := by
      replace this : LinearIndependent ℚ v :=
        .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf
      exact Basis.mk this (by rw [h_span])
    rw [← RootPairing.finrank_rootSpanIn ℚ P, finrank_eq_nat_card_basis b]
  have hv : span R (range <| (P.rootSpan ℚ).subtype ∘ v) = ⊤ := by
    rw [range_comp, ← span_span_of_tower ℚ, span_image, h_span]
    simp
  rw [linearIndependent_iff_card_eq_finrank_span, Set.finrank, hv, finrank_top, ← h_card,
    Fintype.card_eq_nat_card]
```

### `namespace in BaseExists.lean` (command, added) [de11fc7786]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open Function IsAddIndecomposable Module Set Submodule
```

### `namespace in BaseExists.lean` (command, added) [e241051b79]
- file: `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace RootPairing
```

### `RootPairing.algebraMap_pairingIn'` (lemma, added) [817a296a96]
- file: `Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma algebraMap_pairingIn' (T : Type*)
    [CommRing T] [Algebra T S] [Algebra T R] [IsScalarTower T S R] [P.IsValuedIn T] [P.IsValuedIn S]
    [FaithfulSMul S R] (i j : ι) :
    algebraMap T S (P.pairingIn T i j) = P.pairingIn S i j := by
  apply FaithfulSMul.algebraMap_injective S R
  rw [← RingHom.comp_apply, ← IsScalarTower.algebraMap_eq]
  simp
```

### `RootPairing.pairingIn_rat` (lemma, modified) [a15168b159]
- file: `Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean`; changed: proof:modified
- before the PR:
```lean
@[simp] lemma pairingIn_rat [Nontrivial R] [P.IsCrystallographic] [Algebra ℚ R] (i j : ι) :
    P.pairingIn ℚ i j = P.pairingIn ℤ i j := by
  apply FaithfulSMul.algebraMap_injective ℚ R
  have : algebraMap ℤ R = algebraMap ℚ R ∘ algebraMap ℤ ℚ := by simp
  rw [← eq_intCast (algebraMap ℤ ℚ), ← comp_apply (f := algebraMap ℚ R) (g := algebraMap ℤ ℚ),
    ← this, algebraMap_pairingIn, algebraMap_pairingIn]
```
- as the PR leaves it:
```lean
@[simp] lemma pairingIn_rat [Nontrivial R] [P.IsCrystallographic] [Algebra ℚ R] (i j : ι) :
    P.pairingIn ℚ i j = P.pairingIn ℤ i j := by
  simp [← P.algebraMap_pairingIn' ℚ ℤ]
```

### `RootPairing.RootPositiveForm.posForm_apply_root_root_le_zero_iff` (lemma, added) [be6778c4d1]
- file: `Mathlib/LinearAlgebra/RootSystem/RootPositive.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
lemma posForm_apply_root_root_le_zero_iff [IsStrictOrderedRing S]
    (hi : P.root i ∈ span S (range P.root) := subset_span (mem_range_self i))
    (hj : P.root j ∈ span S (range P.root) := subset_span (mem_range_self j)) :
    B.posForm ⟨P.root i, hi⟩ ⟨P.root j, hj⟩ ≤ 0 ↔ P.pairingIn S i j ≤ 0 := by
  rw [← not_iff_not, not_le, not_le, zero_lt_apply_root_root_iff]
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `coe_invMonoidHom`, `invMonoidHom_apply`, `invMonoidHom_comp_invMonoidHom` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `RootPairing.algebraMap_pairingIn'`, `RootPairing.baseOf_pairwise_pairing_le_zero`, `RootPairing.pairingIn_rat` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf`, `IsMulIndecomposable.pairwise_baseOf_div_notMem`, `IsMulIndecomposable.pairwise_div_notMem_range`, `IsMulIndecomposable.pairwise_div_notMem_range'` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `IsMulIndecomposable.pairwise_baseOf_div_notMem`, `IsMulIndecomposable.pairwise_div_notMem_range`, `IsMulIndecomposable.pairwise_div_notMem_range'` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `IsMulIndecomposable.baseOf`, `IsMulIndecomposable.baseOf_subset_one_lt` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `IsMulIndecomposable.baseOf_subset_one_lt`, `IsMulIndecomposable.image_baseOf_inv_comp_eq` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Subgroup.closure_image_isMulIndecomposable_baseOf`, `Submonoid.closure_image_isMulIndecomposable_baseOf` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `RootPairing.linearIndepOn_root_baseOf`, `RootPairing.linearIndepOn_root_baseOf'` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `IsMulIndecomposable.baseOf_subset_one_lt` -> `IsMulIndecomposable.image_baseOf_inv_comp_eq`
- changed_siblings [high]: `IsMulIndecomposable.image_baseOf_inv_comp_eq` -> `IsMulIndecomposable.baseOf_subset_one_lt`
- changed_siblings [high]: `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` -> `IsMulIndecomposable.pairwise_baseOf_div_notMem`
- changed_siblings [high]: `IsMulIndecomposable.pairwise_baseOf_div_notMem` -> `IsMulIndecomposable.pairwise_div_notMem_range'`
- changed_siblings [high]: `IsMulIndecomposable.pairwise_baseOf_div_notMem` -> `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf`
- changed_siblings [high]: `IsMulIndecomposable.pairwise_div_notMem_range` -> `IsMulIndecomposable.pairwise_div_notMem_range'`
- changed_siblings [high]: `IsMulIndecomposable.pairwise_div_notMem_range'` -> `IsMulIndecomposable.pairwise_baseOf_div_notMem`
- changed_siblings [high]: `IsMulIndecomposable.pairwise_div_notMem_range'` -> `IsMulIndecomposable.pairwise_div_notMem_range`
- changed_siblings [high]: `RootPairing.algebraMap_pairingIn'` -> `RootPairing.pairingIn_rat`
- changed_siblings [high]: `RootPairing.pairingIn_rat` -> `RootPairing.algebraMap_pairingIn'`
- changed_siblings [high]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `Submonoid.closure_image_isMulIndecomposable_baseOf`
- changed_siblings [high]: `Submonoid.closure_image_isMulIndecomposable_baseOf` -> `Subgroup.closure_image_isMulIndecomposable_baseOf`
- changed_siblings [high]: `coe_invMonoidHom` -> `invMonoidHom_apply`
- changed_siblings [high]: `invMonoidHom_apply` -> `coe_invMonoidHom`
- changed_siblings [high]: `invMonoidHom_apply` -> `invMonoidHom_comp_invMonoidHom`
- changed_siblings [high]: `invMonoidHom_comp_invMonoidHom` -> `invMonoidHom_apply`
- declaration_dependency [exact]: `IsMulIndecomposable.baseOf_subset_one_lt` -> `IsMulIndecomposable.baseOf`
- declaration_dependency [exact]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `IsMulIndecomposable.baseOf`
- declaration_dependency [exact]: `Submonoid.closure_image_isMulIndecomposable_baseOf` -> `IsMulIndecomposable.baseOf`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.baseOf_subset_one_lt` -> `IsMulIndecomposable.subset`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.image_baseOf_inv_comp_eq` -> `invMonoidHom_comp_invMonoidHom`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` -> `Subgroup.closure_image_isMulIndecomposable_baseOf`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` -> `Submonoid.closure_image_isMulIndecomposable_baseOf`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.pairwise_baseOf_div_notMem` -> `IsMulIndecomposable.pairwise_div_notMem_range'`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.pairwise_div_notMem_range` -> `IsMulIndecomposable.subset`
- direct_use_of_changed_declaration [exact]: `IsMulIndecomposable.pairwise_div_notMem_range'` -> `IsMulIndecomposable.pairwise_div_notMem_range`
- direct_use_of_changed_declaration [exact]: `RootPairing.linearIndepOn_root_baseOf` -> `RootPairing.linearIndepOn_root_baseOf'`
- direct_use_of_changed_declaration [exact]: `RootPairing.linearIndepOn_root_baseOf'` -> `RootPairing.RootPositiveForm.posForm_apply_root_root_le_zero_iff`
- direct_use_of_changed_declaration [exact]: `RootPairing.linearIndepOn_root_baseOf'` -> `RootPairing.baseOf_pairwise_pairing_le_zero`
- direct_use_of_changed_declaration [exact]: `RootPairing.linearIndepOn_root_baseOf'` -> `RootPairing.algebraMap_pairingIn'`
- direct_use_of_changed_declaration [exact]: `RootPairing.pairingIn_rat` -> `RootPairing.algebraMap_pairingIn'`
- direct_use_of_changed_declaration [exact]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `coe_invMonoidHom`
- direct_use_of_changed_declaration [exact]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `IsMulIndecomposable.baseOf`
- direct_use_of_changed_declaration [exact]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `IsMulIndecomposable.image_baseOf_inv_comp_eq`
- direct_use_of_changed_declaration [exact]: `Subgroup.closure_image_isMulIndecomposable_baseOf` -> `Submonoid.closure_image_isMulIndecomposable_baseOf`
- direct_use_of_changed_declaration [exact]: `Submonoid.closure_image_isMulIndecomposable_baseOf` -> `IsMulIndecomposable.baseOf_subset_one_lt`
- name_family [high]: `IsMulIndecomposable.pairwise_baseOf_div_notMem` -> `IsMulIndecomposable.pairwise_div_notMem_range`
- name_family [high]: `IsMulIndecomposable.pairwise_baseOf_div_notMem` -> `IsMulIndecomposable.pairwise_div_notMem_range'`
- name_family [high]: `IsMulIndecomposable.pairwise_div_notMem_range` -> `IsMulIndecomposable.pairwise_baseOf_div_notMem`
- name_family [high]: `IsMulIndecomposable.pairwise_div_notMem_range` -> `IsMulIndecomposable.pairwise_div_notMem_range'`
- name_family [high]: `IsMulIndecomposable.pairwise_div_notMem_range'` -> `IsMulIndecomposable.pairwise_baseOf_div_notMem`
- name_family [high]: `IsMulIndecomposable.pairwise_div_notMem_range'` -> `IsMulIndecomposable.pairwise_div_notMem_range`
- name_family [high]: `RootPairing.algebraMap_pairingIn'` -> `RootPairing.baseOf_pairwise_pairing_le_zero`
- name_family [high]: `RootPairing.algebraMap_pairingIn'` -> `RootPairing.pairingIn_rat`
- name_family [high]: `RootPairing.baseOf_pairwise_pairing_le_zero` -> `RootPairing.algebraMap_pairingIn'`
- name_family [high]: `RootPairing.baseOf_pairwise_pairing_le_zero` -> `RootPairing.pairingIn_rat`
- name_family [high]: `RootPairing.pairingIn_rat` -> `RootPairing.baseOf_pairwise_pairing_le_zero`
- name_family [high]: `RootPairing.pairingIn_rat` -> `RootPairing.algebraMap_pairingIn'`

---

## The diff

```diff
diff --git a/Mathlib.lean b/Mathlib.lean
--- a/Mathlib.lean
+++ b/Mathlib.lean
@@ -4724,6 +4724,7 @@ public import Mathlib.LinearAlgebra.Ray
 public import Mathlib.LinearAlgebra.Reflection
 public import Mathlib.LinearAlgebra.RootSystem.Base
 public import Mathlib.LinearAlgebra.RootSystem.BaseChange
+public import Mathlib.LinearAlgebra.RootSystem.BaseExists
 public import Mathlib.LinearAlgebra.RootSystem.Basic
 public import Mathlib.LinearAlgebra.RootSystem.CartanMatrix
 public import Mathlib.LinearAlgebra.RootSystem.Chain
diff --git a/Mathlib/Algebra/Group/Hom/Basic.lean b/Mathlib/Algebra/Group/Hom/Basic.lean
--- a/Mathlib/Algebra/Group/Hom/Basic.lean
+++ b/Mathlib/Algebra/Group/Hom/Basic.lean
@@ -63,12 +63,16 @@ def invMonoidHom : α →* α where
   map_one' := inv_one
   map_mul' := mul_inv
 
-@[simp]
+@[to_additive (attr := simp)]
 theorem coe_invMonoidHom : (invMonoidHom : α → α) = Inv.inv := rfl
 
-@[simp]
+@[to_additive (attr := simp)]
 theorem invMonoidHom_apply (a : α) : invMonoidHom a = a⁻¹ := rfl
 
+@[to_additive (attr := simp)]
+theorem invMonoidHom_comp_invMonoidHom : (invMonoidHom (α := α)).comp invMonoidHom = .id _ := by
+  ext; simp
+
 end DivisionCommMonoid
 
 namespace OneHom
diff --git a/Mathlib/Algebra/Group/Irreducible/Indecomposable.lean b/Mathlib/Algebra/Group/Irreducible/Indecomposable.lean
--- a/Mathlib/Algebra/Group/Irreducible/Indecomposable.lean
+++ b/Mathlib/Algebra/Group/Irreducible/Indecomposable.lean
@@ -6,7 +6,11 @@ Authors: Oliver Nash
 module
 
 public import Mathlib.Algebra.Group.Irreducible.Defs
+public import Mathlib.Algebra.Group.Subgroup.Lattice
+public import Mathlib.Algebra.Group.Subgroup.Pointwise
 public import Mathlib.Algebra.Group.Submonoid.Basic
+public import Mathlib.Algebra.Order.Group.Defs
+public import Mathlib.Algebra.Order.Group.Basic
 public import Mathlib.Algebra.Order.Monoid.Defs
 public import Mathlib.Order.Preorder.Finite
 
@@ -18,7 +22,7 @@ public import Mathlib.Order.Preorder.Finite
 
 open Set
 
-variable {ι M : Type*} [Monoid M]
+variable {ι M G S : Type*} [Monoid M] [CommGroup G] [LinearOrder S]
 
 /-- Given a family of elements of a monoid, a member is said to be indecomposable if it cannot be
 written as a product of two others in a non-trivial way. -/
@@ -27,11 +31,51 @@ to be indecomposable if it cannot be written as a sum of two others in a non-tri
 def IsMulIndecomposable (v : ι → M) (s : Set ι) (i : ι) : Prop :=
   i ∈ s ∧ ∀ᵉ (j ∈ s) (k ∈ s), v i = v j * v k → v j = 1 ∨ v k = 1
 
+@[to_additive]
+protected lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) :
+    {i | IsMulIndecomposable v s i} ⊆ s := by
+  aesop
+
 @[to_additive]
 lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) :
     IsMulIndecomposable id univ x ↔ Irreducible x :=
   ⟨fun h ↦ ⟨by simpa, by simpa using h⟩, fun h ↦ by simpa using h.isUnit_or_isUnit⟩
 
+/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
+@[to_additive /-- The "base" of `v` relative to a morphism `f`.
+
+In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
+base of the root system associated to `f`. -/]
+def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
+  IsMulIndecomposable v {i | 1 < f (v i)}
+
+@[to_additive]
+lemma IsMulIndecomposable.baseOf_subset_one_lt [Monoid S] (v : ι → M) (f : M →* S) :
+    IsMulIndecomposable.baseOf v f ⊆ {i | 1 < f (v i)} :=
+  IsMulIndecomposable.subset _ _
+
+@[to_additive]
+lemma IsMulIndecomposable.image_baseOf_inv_comp_eq [InvolutiveInv ι]
+    [CommGroup S] [IsOrderedMonoid S]
+    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (f : G →* S) :
+    v '' baseOf v (invMonoidHom.comp f) = (invMonoidHom ∘ v) '' baseOf v f := by
+  suffices ∀ (f : G →* S),
+      v '' baseOf v (invMonoidHom.comp f) ⊆ (invMonoidHom ∘ v) '' baseOf v f by
+    apply subset_antisymm (this f)
+    replace this := image_mono (f := invMonoidHom) <| this (invMonoidHom.comp f)
+    rw [← MonoidHom.comp_assoc, invMonoidHom_comp_invMonoidHom, MonoidHom.id_comp, image_comp,
+      ← image_comp invMonoidHom invMonoidHom, ← MonoidHom.coe_comp, invMonoidHom_comp_invMonoidHom,
+      ← image_comp] at this
+    simpa using this
+  clear f
+  rintro f g ⟨i, ⟨hi, hi'⟩, rfl⟩
+  refine ⟨i⁻¹, ⟨by simpa [hv_inv] using hi, fun j hj k hk hi ↦ ?_⟩, by simp [hv_inv]⟩
+  replace hi : v i = v j⁻¹ * v k⁻¹ := by
+    rwa [hv_inv, inv_eq_iff_eq_inv, mul_inv, ← hv_inv, ← hv_inv] at hi
+  specialize hi' j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv]) hi
+  aesop
+
 /-- Given a finite family of points `v` in a monoid `M`, together with a morphism into a
 linearly-ordered monoid `f : M →* S`, the submonoid generated by those points of `v` which lie in
 the "half space" where `f > 1` is generated by the subset of such points which are indecomposable
@@ -43,12 +87,12 @@ which are indecomposable with respect to points in this half space.
 
 If `v` is the set of roots of a crystallographic root system and `S = ℚ`, then this is
 [serre1965](Ch. V, §9, Lemma 2) and it may be used to prove that the root system has a base. -/]
-lemma Submonoid.closure_image_one_lt_and_isMulIndecomposable [Finite ι]
-    {S : Type*} [CommMonoid S] [LinearOrder S] [IsOrderedCancelMonoid S]
+lemma Submonoid.closure_image_isMulIndecomposable_baseOf [Finite ι]
+    [CommMonoid S] [IsOrderedCancelMonoid S]
     (v : ι → M) (f : M →* S) :
-    closure (v '' {i | IsMulIndecomposable v {j | 1 < f (v j)} i}) =
-      closure (v '' {i | 1 < f (v i)}) := by
-  refine le_antisymm (closure_mono (image_mono <| by aesop)) (closure_le.mpr ?_)
+    closure (v '' IsMulIndecomposable.baseOf v f) = closure (v '' {i | 1 < f (v i)}) := by
+  refine le_antisymm (closure_mono (image_mono <| IsMulIndecomposable.baseOf_subset_one_lt v f))
+    (closure_le.mpr ?_)
   rintro - ⟨i, hi : 1 < f (v i), rfl⟩
   by_contra hi'
   let t : Set ι := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}
@@ -67,3 +111,80 @@ lemma Submonoid.closure_image_one_lt_and_isMulIndecomposable [Finite ι]
   have hk' : v k ∈ closure (v '' t) := hi₂ k hk <| by aesop
   replace hjk : v i ∈ closure (v '' t) := hjk ▸ mul_mem hj' hk'
   exact hi₁ hjk
+
+@[to_additive]
+lemma Subgroup.closure_image_isMulIndecomposable_baseOf [Finite ι] [InvolutiveInv ι]
+    [CommGroup S] [IsOrderedMonoid S]
+    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
+    closure (v '' IsMulIndecomposable.baseOf v f) = closure (range v) := by
+  rw [← image_univ]
+  refine le_antisymm (closure_mono (image_mono <| by simp)) ((closure_le _).mpr ?_)
+  have : univ = {i | 1 < f (v i)} ∪ {i | f (v i) < 1} := by ext i; simp [(hf i).symm]
+  rw [this, image_union, union_subset_iff]
+  refine ⟨le_trans ?_ (le_closure_toSubmonoid (v '' IsMulIndecomposable.baseOf v f)), ?_⟩
+  · simp [Submonoid.closure_image_isMulIndecomposable_baseOf]
+  · let f' : G →* S := invMonoidHom.comp f
+    have h₁ : (invMonoidHom ∘ v) '' IsMulIndecomposable.baseOf v f' =
+        v '' IsMulIndecomposable.baseOf v f := by
+      rw [image_comp, IsMulIndecomposable.image_baseOf_inv_comp_eq v hv_inv f, image_comp,
+        ← image_comp]
+      simp
+    have h₂ : v '' {i | f (v i) < 1} = v '' {i | 1 < f' (v i)} := by simp [f']
+    rw [h₂, ← h₁, image_comp, coe_invMonoidHom, image_inv_eq_inv, closure_inv]
+    refine le_trans ?_ (le_closure_toSubmonoid (v '' IsMulIndecomposable.baseOf v f'))
+    simp [Submonoid.closure_image_isMulIndecomposable_baseOf]
+
+namespace IsMulIndecomposable
+
+@[to_additive]
+lemma pairwise_div_notMem_range [InvolutiveInv ι]
+    (v : ι → G)
+    (hv_one : ∀ i, v i ≠ 1)
+    (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (s t : Set ι)
+    (hst : s ⊆ IsMulIndecomposable v t)
+    (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
+    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
+  have h_sub : s ⊆ t := hst.trans (IsMulIndecomposable.subset _ _)
+  intro i hi j hj hne
+  by_contra! ⟨k, hk⟩
+  rcases hv_t k with hk' | hk'
+  · suffices ¬ IsMulIndecomposable v t i from this (hst hi)
+    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
+    exact fun _ ↦ ⟨k, hk', j, h_sub hj, by simp [hk]⟩
+  · suffices ¬ IsMulIndecomposable v t j from this (hst hj)
+    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
+    exact fun _ ↦ ⟨k⁻¹, hk', i, h_sub hi, by simp [hv_inv, hk]⟩
+
+@[to_additive]
+lemma pairwise_div_notMem_range' [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
+    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1)
+    (s : Set ι) (hst : s ⊆ IsMulIndecomposable v {i | 1 < f (v i)}) :
+    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
+  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
+  apply pairwise_div_notMem_range v hv_one hv_inv s {i | 1 < f (v i)} hst fun i ↦ ?_
+  simpa [hv_inv] using (hf i).symm
+
+@[to_additive]
+lemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
+    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
+    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v :=
+  pairwise_div_notMem_range' v hv_inv f hf (baseOf v f) (.refl _)
+
+@[to_additive]
+lemma mem_or_inv_mem_closure_baseOf [Finite ι] [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
+    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
+    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) (i : ι) :
+     v i    ∈ Submonoid.closure (v '' baseOf v f) ∨
+    (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by
+  rw [Submonoid.closure_image_isMulIndecomposable_baseOf v f]
+  rcases lt_or_gt_of_ne (hf i) with hj | hj
+  · right
+    exact Submonoid.subset_closure ⟨i⁻¹, by simpa [hv_inv]⟩
+  · left
+    exact Submonoid.subset_closure ⟨i, by simpa⟩
+
+end IsMulIndecomposable
diff --git a/Mathlib/LinearAlgebra/RootSystem/BaseExists.lean b/Mathlib/LinearAlgebra/RootSystem/BaseExists.lean
--- /dev/null
+++ b/Mathlib/LinearAlgebra/RootSystem/BaseExists.lean
@@ -0,0 +1,138 @@
+/-
+Copyright (c) 2025 Oliver Nash. All rights reserved.
+Released under Apache 2.0 license as described in the file LICENSE.
+Authors: Oliver Nash
+-/
+module
+
+public import Mathlib.Algebra.Group.Irreducible.Indecomposable
+public import Mathlib.Algebra.Module.Submodule.Union
+public import Mathlib.LinearAlgebra.Dimension.OrzechProperty
+public import Mathlib.LinearAlgebra.QuadraticForm.Dual
+public import Mathlib.LinearAlgebra.RootSystem.Base
+
+/-!
+# Existence of bases for crystallographic root systems
+
+## Implementation details
+
+The proof needs a set of ordered coefficients, even though the existence ultimate statement does
+not. There are at least two ways to deal with this:
+ (a) Using the fact that a crystallographic root system induces a `ℚ`-structure, pass to the root
+     system over `ℚ` defined by `RootPairing.restrictScalarsRat`, and develop a theory of base
+     change for root system bases.
+ (b) Introduce a second set of ordered coefficients (ultimately taken to be `ℚ`) and develop a
+     theory with two sets of coefficients simultaneously in play.
+
+It is not really clear which is the better approach but here we opt for approach (b) as it seems
+to yield slightly more general results.
+
+## TODO
+
+1. Prove that for crystallographic reduced root systems, the axiom `coroot_mem_or_neg_mem` appearing
+   in `RootPairing.Base` follows from the others, and combine this with
+   `RootPairing.linearIndepOn_coroot_iff` to thus provide an alternate constructor for
+   `RootPairing.Base` which demands only the hypotheses on the roots.
+2. [Easy given 1 above] Prove that every reduced crystallographic root system has a base by
+   combining the constructor in 1 above with `RootPairing.linearIndepOn_root_baseOf`,
+   `IsAddIndecomposable.mem_or_neg_mem_closure_baseOf`, `Module.exists_dual_forall_apply_ne_zero`.
+
+-/
+
+@[expose] public section
+
+open Function IsAddIndecomposable Module Set Submodule
+
+namespace RootPairing
+
+variable {ι R M N : Type*} [Finite ι] [AddCommGroup M] [AddCommGroup N]
+
+section CommRing
+
+variable [CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)
+  {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)
+
+/-- This is [serre1965](Ch. V, §9, Lemma 3). -/
+lemma baseOf_pairwise_pairing_le_zero [CharZero R] [IsDomain R] [P.IsCrystallographic]
+    (hf : ∀ i, f (P.root i) ≠ 0) :
+    (baseOf P.root f).Pairwise fun i j ↦ P.pairingIn ℤ i j ≤ 0 := by
+  letI _i := P.indexNeg
+  intro i hi j hj hne
+  have := IsAddIndecomposable.pairwise_baseOf_sub_notMem P.root (by simp) f hf hi hj hne
+  contrapose! this
+  exact P.root_sub_root_mem_of_pairingIn_pos this hne
+
+/-- This lemma is usually established for root systems with coefficients `R` equal to `ℚ` or `ℝ`, in
+which case one may take `S = R`. However our statement allows for more general coefficients such as
+`R = ℂ` and `S = ℚ`.
+
+This lemma is mostly a stepping stone en route to `RootPairing.linearIndepOn_root_baseOf` (where
+linear independence is established over `R` rather than just `S`) except that this version does not
+make the field assumption and so covers the case `S = R = ℤ` which the latter does not. -/
+lemma linearIndepOn_root_baseOf' [IsDomain R] {S : Type*}
+    [LinearOrder S] [CommRing S] [IsStrictOrderedRing S] [Algebra S R] [FaithfulSMul S R]
+    [Module S M] [IsScalarTower S R M] [Module S N] [IsScalarTower S R N]
+    [P.IsValuedIn S] [P.IsCrystallographic]
+    (f : Dual S M) (hf : ∀ i, f (P.root i) ≠ 0) :
+    LinearIndepOn S P.root (baseOf P.root (f : M →+ S)) := by
+  have : CharZero R := Algebra.charZero_of_charZero S R
+  have : Fintype ι := Fintype.ofFinite ι
+  let M₀ := span S (range P.root)
+  let v (i : baseOf P.root (f : M →+ S)) : M₀ := P.rootSpanMem S i
+  change LinearIndependent S (M₀.subtype ∘ v)
+  suffices LinearIndependent S v by
+    rwa [LinearMap.linearIndependent_iff_of_disjoint M₀.subtype (by simp)]
+  let f' : Dual S M₀ := f ∘ₗ M₀.subtype
+  obtain ⟨B, hB⟩ : ∃ B : P.RootPositiveForm S, B.posForm.toQuadraticMap.PosDef :=
+    ⟨P.posRootForm S, by simpa using P.posRootForm_rootFormIn_posDef S⟩
+  have hp (i : baseOf P.root (f : M →+ S)) : 0 < f' (v i) := by obtain ⟨i, -, hi⟩ := i; simpa
+  have hn : Pairwise fun (i j : baseOf P.root (f : M →+ S)) ↦ B.posForm (v i) (v j) ≤ 0 := by
+    rintro ⟨i, hi⟩ ⟨j, hj⟩ hij
+    rw [B.posForm_apply_root_root_le_zero_iff, ← P.algebraMap_pairingIn' S ℤ]
+    simpa using P.baseOf_pairwise_pairing_le_zero _ hf (by simpa) (by simpa) (by aesop : i ≠ j)
+  exact LinearMap.BilinForm.linearIndependent_of_pairwise_le_zero B.posForm hB f' v hp hn
+
+end CommRing
+
+section Field
+
+variable [Field R] [CharZero R] [Module R M] [Module R N] (P : RootPairing ι R M N)
+  [P.IsRootSystem] [P.IsCrystallographic]
+
+lemma linearIndepOn_root_baseOf [Module ℚ M] [Module ℚ N]
+    (f : Dual ℚ M) (hf : ∀ i, f (P.root i) ≠ 0) :
+    LinearIndepOn R P.root (baseOf P.root (f : M →+ ℚ)) := by
+  letI := P.indexNeg
+  have : Fintype (baseOf P.root (f : M →+ ℚ)) := Fintype.ofFinite _
+  let v (i : baseOf P.root (f : M →+ ℚ)) : P.rootSpan ℚ := P.rootSpanMem ℚ i
+  change LinearIndependent R ((P.rootSpan ℚ).subtype ∘ v)
+  have h_span : span ℚ (range v) = ⊤ := by
+    suffices span ℚ (range v) = span ℚ (range (P.rootSpanMem ℚ)) by
+      rw [this, eq_top_iff, ← LinearMap.map_le_map_iff' (f := (P.rootSpan ℚ).subtype) (by simp),
+        map_span, ← image_univ, ← image_comp]
+      simp
+    apply le_antisymm (span_mono fun x i ↦ by aesop) (span_le.mpr ?_)
+    rintro - ⟨i, rfl⟩
+    suffices (P.rootSpanMem ℚ i : M) ∈ span ℚ (P.root '' baseOf P.root (f : M →+ ℚ)) by
+      rw [← (injective_subtype (P.rootSpan ℚ)).mem_set_image, ← map_coe, SetLike.mem_coe, map_span,
+        ← image_univ, ← image_comp]
+      convert this
+      aesop
+    rw [← span_span_of_tower ℤ, ← Submodule.coe_toAddSubgroup, span_int_eq_addSubgroupClosure,
+      AddSubgroup.closure_image_isAddIndecomposable_baseOf P.root (by simp) (f : M →+ ℚ) (by simpa)]
+    exact subset_span <| AddSubgroup.subset_closure <| by simp
+  have h_card : Nat.card (baseOf P.root (f : M →+ ℚ)) = finrank R M := by
+    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := by
+      replace this : LinearIndependent ℚ v :=
+        .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf
+      exact Basis.mk this (by rw [h_span])
+    rw [← RootPairing.finrank_rootSpanIn ℚ P, finrank_eq_nat_card_basis b]
+  have hv : span R (range <| (P.rootSpan ℚ).subtype ∘ v) = ⊤ := by
+    rw [range_comp, ← span_span_of_tower ℚ, span_image, h_span]
+    simp
+  rw [linearIndependent_iff_card_eq_finrank_span, Set.finrank, hv, finrank_top, ← h_card,
+    Fintype.card_eq_nat_card]
+
+end Field
+
+end RootPairing
diff --git a/Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean b/Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean
--- a/Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean
+++ b/Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean
@@ -137,12 +137,17 @@ lemma IsValuedIn.trans (T : Type*) [CommRing T] [Algebra T S] [Algebra T R] [IsS
 instance [P.IsCrystallographic] [Algebra ℚ R] : P.IsValuedIn ℚ :=
   IsValuedIn.trans P (T := ℤ) (S := ℚ)
 
+@[simp] lemma algebraMap_pairingIn' (T : Type*)
+    [CommRing T] [Algebra T S] [Algebra T R] [IsScalarTower T S R] [P.IsValuedIn T] [P.IsValuedIn S]
+    [FaithfulSMul S R] (i j : ι) :
+    algebraMap T S (P.pairingIn T i j) = P.pairingIn S i j := by
+  apply FaithfulSMul.algebraMap_injective S R
+  rw [← RingHom.comp_apply, ← IsScalarTower.algebraMap_eq]
+  simp
+
 @[simp] lemma pairingIn_rat [Nontrivial R] [P.IsCrystallographic] [Algebra ℚ R] (i j : ι) :
     P.pairingIn ℚ i j = P.pairingIn ℤ i j := by
-  apply FaithfulSMul.algebraMap_injective ℚ R
-  have : algebraMap ℤ R = algebraMap ℚ R ∘ algebraMap ℤ ℚ := by simp
-  rw [← eq_intCast (algebraMap ℤ ℚ), ← comp_apply (f := algebraMap ℚ R) (g := algebraMap ℤ ℚ),
-    ← this, algebraMap_pairingIn, algebraMap_pairingIn]
+  simp [← P.algebraMap_pairingIn' ℚ ℤ]
 
 lemma coroot'_apply_apply_mem_of_mem_span [Module S M] [IsScalarTower S R M] [P.IsValuedIn S]
     {x : M} (hx : x ∈ span S (range P.root)) (i : ι) :
diff --git a/Mathlib/LinearAlgebra/RootSystem/RootPositive.lean b/Mathlib/LinearAlgebra/RootSystem/RootPositive.lean
--- a/Mathlib/LinearAlgebra/RootSystem/RootPositive.lean
+++ b/Mathlib/LinearAlgebra/RootSystem/RootPositive.lean
@@ -204,6 +204,13 @@ lemma zero_lt_apply_root_root_iff [IsStrictOrderedRing S]
     _ ↔ 0 < P.pairingIn S i j * B.posForm rj rj := by rw [this]
     _ ↔ 0 < P.pairingIn S i j := by rw [mul_pos_iff_of_pos_right (B.zero_lt_posForm_apply_root j)]
 
+@[simp]
+lemma posForm_apply_root_root_le_zero_iff [IsStrictOrderedRing S]
+    (hi : P.root i ∈ span S (range P.root) := subset_span (mem_range_self i))
+    (hj : P.root j ∈ span S (range P.root) := subset_span (mem_range_self j)) :
+    B.posForm ⟨P.root i, hi⟩ ⟨P.root j, hj⟩ ≤ 0 ↔ P.pairingIn S i j ≤ 0 := by
+  rw [← not_iff_not, not_le, not_le, zero_lt_apply_root_root_iff]
+
 end RootPositiveForm
 
 include B

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.