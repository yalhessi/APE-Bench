import json
F = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
pw = """@[to_additive]
lemma pairwise_div_notMem_range [InvolutiveInv ι] (v : ι → G) (hv_one : ∀ i, v i ≠ 1)
    (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹) (s t : Set ι) (hst : s ⊆ IsMulIndecomposable v t)
    (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
  have h_sub : s ⊆ t := hst.trans (IsMulIndecomposable.subset _ _)
  rintro i hi j hj - ⟨k, hk⟩
  rcases hv_t k with hk' | hk'
  · exact ((hst hi).2 k hk' j (h_sub hj) (by simp [hk])).elim (hv_one k) (hv_one j)
  · exact ((hst hj).2 k⁻¹ hk' i (h_sub hi) (by simp [hv_inv, hk])).elim (hv_one _) (hv_one i)"""
pw_min = """@[to_additive]
lemma pairwise_div_notMem_range [InvolutiveInv ι] (v : ι → G) (hv_one : ∀ i, v i ≠ 1)
    (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹) (s t : Set ι) (hst : s ⊆ IsMulIndecomposable v t)
    (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
  have h_sub : s ⊆ t := hst.trans (IsMulIndecomposable.subset _ _)
  rintro i hi j hj hne ⟨k, hk⟩
  rcases hv_t k with hk' | hk'
  · suffices ¬ IsMulIndecomposable v t i from this (hst hi)
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k, hk', j, h_sub hj, by simp [hk]⟩
  · suffices ¬ IsMulIndecomposable v t j from this (hst hj)
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k⁻¹, hk', i, h_sub hi, by simp [hv_inv, hk]⟩"""
noprime = """@[to_additive]
lemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹) (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v := by
  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
  refine pairwise_div_notMem_range v hv_one hv_inv _ {i | 1 < f (v i)} subset_rfl fun i ↦ ?_
  simpa [hv_inv] using (hf i).symm"""
mem = """@[to_additive]
lemma mem_or_inv_mem_closure_baseOf [Finite ι] [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹) (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) (i : ι) :
    v i ∈ Submonoid.closure (v '' baseOf v f) ∨ (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by
  rw [Submonoid.closure_image_isMulIndecomposable_baseOf v f]
  rcases lt_or_gt_of_ne (hf i) with hj | hj
  · right
    exact Submonoid.subset_closure ⟨i⁻¹, by simpa [hv_inv]⟩
  · left
    exact Submonoid.subset_closure ⟨i, by simpa⟩"""
spec = [
 ("pairwise golf", {"path":F,"declaration_name":"IsMulIndecomposable.pairwise_div_notMem_range","new_declaration":pw}),
 ("pairwise minimal rintro", {"path":F,"declaration_name":"IsMulIndecomposable.pairwise_div_notMem_range","new_declaration":pw_min}),
 ("remove prime lemma", {"path":F,"line_start":160,"line_end":175,"replacement":noprime}),
 ("mem spacing", {"path":F,"declaration_name":"IsMulIndecomposable.mem_or_inv_mem_closure_baseOf","new_declaration":mem}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/ind2.json","w"))
for l in mem.splitlines(): print(len(l), l[:30])
