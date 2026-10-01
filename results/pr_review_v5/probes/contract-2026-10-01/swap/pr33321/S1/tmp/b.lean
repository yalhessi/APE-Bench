lemma mem_or_inv_mem_closure_baseOf [Finite ι] [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) {i : ι} (hf : f (v i) ≠ 1) :
    v i ∈ Submonoid.closure (v '' baseOf v f) ∨
      (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by
  rw [Submonoid.closure_image_isMulIndecomposable_baseOf v f]
  rcases lt_or_gt_of_ne hf with hi | hi
  · right
    exact Submonoid.subset_closure ⟨i⁻¹, by simpa [hv_inv]⟩
  · left
    exact Submonoid.subset_closure ⟨i, by simpa⟩
