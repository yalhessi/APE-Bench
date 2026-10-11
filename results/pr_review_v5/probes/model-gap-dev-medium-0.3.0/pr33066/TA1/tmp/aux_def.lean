/-- The continuous linear equivalence `α' • e`, with inverse `α' • adjoint e`, given that
`α' * α' = α⁻¹`, `adjoint e ∘L e = α • id` and `e ∘L adjoint e = α • id`. -/
private noncomputable def smulContinuousLinearEquivOfAdjoint :
    V ≃L[𝕜] W where
  toLinearMap := (α' • e.toContinuousLinearMap).toLinearMap
  invFun := (α' • e.toContinuousLinearMap.adjoint).toLinearMap
  left_inv x := by
    have := by simpa using congr($he x)
    simp [smul_smul, hα2, this, hα, ← mul_assoc]
  right_inv x := by
    have := by simpa using congr($he' x)
    simp [smul_smul, hα2, this, hα, ← mul_assoc]
  continuous_toFun := (α' • e.toContinuousLinearMap).continuous
  continuous_invFun := (α' • e.toContinuousLinearMap.adjoint).continuous

@[simp] private lemma coe_smulContinuousLinearEquivOfAdjoint :
    (smulContinuousLinearEquivOfAdjoint e hα hα2 he he').toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl

/-- The linear isometric equivalence `α' • e`, for a real scalar `α'` with `α' * α' = α⁻¹`, when
`adjoint e ∘L e = α • id` and `e ∘L adjoint e = α • id`. -/
private noncomputable def smulLinearIsometryEquivOfAdjoint (hαa : starRingEnd 𝕜 α' = α') :
    V ≃ₗᵢ[𝕜] W where
  __ := smulContinuousLinearEquivOfAdjoint e hα hα2 he he' |>.toLinearEquiv
  norm_map' := by
    rw [ContinuousLinearEquiv.coe_toLinearEquiv, ← ContinuousLinearEquiv.coe_coe,
      norm_map_iff_adjoint_comp_self, coe_smulContinuousLinearEquivOfAdjoint,
      MulActionSemiHomClass.map_smulₛₗ]
    simp only [hαa, comp_smulₛₗ, RingHom.id_apply, smul_comp, smul_smul, hα2]
    simp [he, smul_smul, hα, one_def]

@[simp] private lemma coe_smulLinearIsometryEquivOfAdjoint (hαa : starRingEnd 𝕜 α' = α') :
    (smulLinearIsometryEquivOfAdjoint e hα hα2 he he' hαa).toContinuousLinearEquiv.toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl

@[simp] private lemma coe_symm_smulLinearIsometryEquivOfAdjoint (hαa : starRingEnd 𝕜 α' = α') :
    (smulLinearIsometryEquivOfAdjoint e hα hα2 he he' hαa).toContinuousLinearEquiv.symm.toContinuousLinearMap =
      α'⁻¹ • e.symm.toContinuousLinearMap := by
  ext y
  apply (smulLinearIsometryEquivOfAdjoint e hα hα2 he he' hαa).toContinuousLinearEquiv.injective
  simp [smul_smul, inv_mul_cancel₀ (a := α') (by grind)]

end auxiliaryDefs

open ComplexOrder

/-- Every continuous ⋆-algebra equivalence between the algebras of continuous endomorphisms of two
Hilbert spaces is given by conjugation by a linear isometric equivalence. -/
