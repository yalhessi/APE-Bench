/-- Scalar multiple of a continuous linear equivalence (given certain properties are satisfied). -/
noncomputable def auxContinuousLinearEquiv :
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

@[simp] theorem coe_auxContinuousLinearEquiv :
    (auxContinuousLinearEquiv e hα hα2 he he').toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl

/-- Construct an isometry linear equivalence from a continuous linear equivalence
and that its adjoint is a real-scalar multiple of its inverse. -/
noncomputable def auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    V ≃ₗᵢ[𝕜] W where
  __ := auxContinuousLinearEquiv e hα hα2 he he' |>.toLinearEquiv
  norm_map' := by
    rw [ContinuousLinearEquiv.coe_toLinearEquiv, ← ContinuousLinearEquiv.coe_coe,
      norm_map_iff_adjoint_comp_self, coe_auxContinuousLinearEquiv,
      MulActionSemiHomClass.map_smulₛₗ]
    simp only [hαa, comp_smulₛₗ, RingHom.id_apply, smul_comp, smul_smul, hα2]
    simp [he, smul_smul, hα, one_def]

@[simp] theorem coe_auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl

@[simp] theorem coe_symm_auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.symm.toContinuousLinearMap =
      α'⁻¹ • e.symm.toContinuousLinearMap := by
  ext y
  apply (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.injective
  simp [auxIsometry, auxContinuousLinearEquiv, smul_smul, inv_mul_cancel₀ (a := α') (by grind)]
