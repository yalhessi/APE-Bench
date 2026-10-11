import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp"
F = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
block = """namespace IsMulIndecomposable

variable [InvolutiveInv ι] (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
include hv_inv

@[to_additive]
lemma pairwise_div_notMem_range (hv_one : ∀ i, v i ≠ 1) (s t : Set ι)
    (hst : s ⊆ IsMulIndecomposable v t) (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
    s.Pairwise fun i j ↦ v i / v j ∉ range v := by
  have h_sub : s ⊆ t := hst.trans (IsMulIndecomposable.subset _ _)
  rintro i hi j hj - ⟨k, hk⟩
  rcases hv_t k with hk' | hk'
  · exact ((hst hi).2 k hk' j (h_sub hj) (by simp [hk])).elim (hv_one k) (hv_one j)
  · exact ((hst hj).2 k⁻¹ hk' i (h_sub hi) (by simp [hv_inv, hk])).elim (hv_one _) (hv_one i)

variable [CommGroup S] [IsOrderedMonoid S] (f : G →* S) (hf : ∀ i, f (v i) ≠ 1)
include hf

@[to_additive]
lemma pairwise_baseOf_div_notMem : (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v := by
  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
  refine pairwise_div_notMem_range v hv_inv hv_one _ {i | 1 < f (v i)} subset_rfl fun i ↦ ?_
  simpa [hv_inv] using (hf i).symm

@[to_additive]
lemma mem_or_inv_mem_closure_baseOf [Finite ι] (i : ι) :
    v i ∈ Submonoid.closure (v '' baseOf v f) ∨ (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by
  rw [Submonoid.closure_image_isMulIndecomposable_baseOf v f]
  rcases lt_or_gt_of_ne (hf i) with hj | hj
  · right
    exact Submonoid.subset_closure ⟨i⁻¹, by simpa [hv_inv]⟩
  · left
    exact Submonoid.subset_closure ⟨i, by simpa⟩

end IsMulIndecomposable"""
spec = [("namespace block with variables", {"path":F, "line_start":138, "line_end":190, "replacement":block})]
json.dump(spec, open(D + "/ind6.json", "w"))
