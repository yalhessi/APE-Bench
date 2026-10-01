lemma Subgroup.closure_image_isMulIndecomposable_baseOf [Finite ι] [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    closure (v '' IsMulIndecomposable.baseOf v f) = closure (range v) := by
  refine le_antisymm (closure_mono (image_subset_range _ _)) ((closure_le _).mpr ?_)
  rintro - ⟨i, rfl⟩
  have key (j : ι) (hj : 1 < f (v j)) : v j ∈ closure (v '' IsMulIndecomposable.baseOf v f) := by
    apply le_closure_toSubmonoid
    rw [Submonoid.closure_image_isMulIndecomposable_baseOf]
    exact Submonoid.subset_closure ⟨j, hj, rfl⟩
  rcases lt_or_gt_of_ne (hf i) with hi | hi
  · simpa [hv_inv] using inv_mem (key i⁻¹ (by simpa [hv_inv]))
  · exact key i hi
