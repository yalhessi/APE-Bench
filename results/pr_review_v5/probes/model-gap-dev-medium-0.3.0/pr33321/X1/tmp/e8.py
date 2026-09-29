import json
rep = r'''@[to_additive]
lemma IsMulIndecomposable.inv_mem_baseOf_iff [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (i : ι) :
    i⁻¹ ∈ baseOf v f ↔ i ∈ baseOf v (invMonoidHom.comp f) := by
  change IsMulIndecomposable v _ i⁻¹ ↔ IsMulIndecomposable v _ i
  simp only [IsMulIndecomposable, mem_setOf_eq, MonoidHom.coe_comp, Function.comp_apply,
    invMonoidHom_apply, hv_inv, map_inv, one_lt_inv']
  refine and_congr_right fun _ ↦ ?_
  constructor
  · intro h j hj k hk hjk
    simpa [hv_inv] using h j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv])
      (by rw [hv_inv, hv_inv, ← mul_inv, ← hjk])
  · intro h j hj k hk hjk
    simpa [hv_inv] using h j⁻¹ (by simpa [hv_inv]) k⁻¹ (by simpa [hv_inv])
      (by rw [hv_inv, hv_inv, ← mul_inv, ← hjk, inv_inv])

@[to_additive]
lemma IsMulIndecomposable.image_baseOf_inv_comp_eq [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) :
    v '' baseOf v (invMonoidHom.comp f) = (invMonoidHom ∘ v) '' baseOf v f := by
  ext x
  constructor
  · rintro ⟨i, hi, rfl⟩
    exact ⟨i⁻¹, (inv_mem_baseOf_iff v hv_inv f i).2 hi, by simp [hv_inv]⟩
  · rintro ⟨i, hi, rfl⟩
    exact ⟨i⁻¹, (inv_mem_baseOf_iff v hv_inv f i⁻¹).1 (by simpa using hi), by simp [hv_inv]⟩'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":57,"line_end":77,"replacement":rep}))
