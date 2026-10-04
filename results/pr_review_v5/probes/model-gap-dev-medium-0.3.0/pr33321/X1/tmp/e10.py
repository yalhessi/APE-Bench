import json
rep = r'''@[to_additive]
lemma pairwise_div_notMem_range [InvolutiveInv ι]
    (v : ι → G) (hv_one : ∀ i, v i ≠ 1) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (t : Set ι) (hv_t : ∀ i, i ∈ t ∨ i⁻¹ ∈ t) :
    {i | IsMulIndecomposable v t i}.Pairwise fun i j ↦ v i / v j ∉ range v := by
  intro i hi j hj hne
  by_contra! ⟨k, hk⟩
  rcases hv_t k with hk' | hk'
  · suffices ¬ IsMulIndecomposable v t i from this hi
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k, hk', j, hj.1, by simp [hk]⟩
  · suffices ¬ IsMulIndecomposable v t j from this hj
    simp only [IsMulIndecomposable, hv_one, or_self, imp_false, not_and, not_forall, not_not]
    exact fun _ ↦ ⟨k⁻¹, hk', i, hi.1, by simp [hv_inv, hk]⟩

@[to_additive]
lemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v := by
  have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩
  refine pairwise_div_notMem_range v hv_one hv_inv _ fun i ↦ ?_
  simpa [hv_inv] using (hf i).symm'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":140,"line_end":175,"replacement":rep}))
