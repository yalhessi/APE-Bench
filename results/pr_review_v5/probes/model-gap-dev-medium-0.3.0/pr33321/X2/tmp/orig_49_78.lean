def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  IsMulIndecomposable v {i | 1 < f (v i)}

@[to_additive]
lemma IsMulIndecomposable.baseOf_subset_one_lt [Monoid S] (v : ι → M) (f : M →* S) :
    IsMulIndecomposable.baseOf v f ⊆ {i | 1 < f (v i)} :=
  IsMulIndecomposable.subset _ _

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

