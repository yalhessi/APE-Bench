import json
rep = r'''@[to_additive]
lemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v := by
  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
  refine pairwise_div_notMem_range v hv_one hv_inv _ _ (.refl _) fun i ↦ ?_
  simpa [hv_inv] using (hf i).symm'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":160,"line_end":175,"replacement":rep}))
