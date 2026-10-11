@[to_additive]
lemma IsMulIndecomposable.image_baseOf_inv_eq [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) :
    v '' baseOf v f⁻¹ = (invMonoidHom ∘ v) '' baseOf v f := by
  suffices ∀ (f : G →* S), v '' baseOf v f⁻¹ ⊆ (invMonoidHom ∘ v) '' baseOf v f by
    refine subset_antisymm (this f) ?_
    simpa [image_comp, image_image] using image_mono (f := invMonoidHom) <| this f⁻¹
  clear f
  rintro f g ⟨i, ⟨hi, hi'⟩, rfl⟩
  refine ⟨i⁻¹, ⟨by simpa [hv_inv] using hi, fun j hj k hk hi ↦ ?_⟩, by simp [hv_inv]⟩
  replace hi : v i = v j⁻¹ * v k⁻¹ := by
    rwa [hv_inv, inv_eq_iff_eq_inv, mul_inv, ← hv_inv, ← hv_inv] at hi
  specialize hi' j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv]) hi
  aesop
