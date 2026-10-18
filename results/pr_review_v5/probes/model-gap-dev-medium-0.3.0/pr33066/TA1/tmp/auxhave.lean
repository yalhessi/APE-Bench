noncomputable abbrev auxContinuousLinearEquiv : V ≃L[𝕜] W where
  toLinearMap := (α' • e.toContinuousLinearMap).toLinearMap
  invFun := (α' • e.toContinuousLinearMap.adjoint).toLinearMap
  left_inv x := by
    have hx : adjoint e.toContinuousLinearMap (e x) = α • x := by simpa using congr($he x)
    simp [smul_smul, hα2, hx, hα, ← mul_assoc]
  right_inv x := by
    have hx : e (adjoint e.toContinuousLinearMap x) = α • x := by simpa using congr($he' x)
    simp [smul_smul, hα2, hx, hα, ← mul_assoc]
  continuous_toFun := (α' • e.toContinuousLinearMap).continuous
  continuous_invFun := (α' • e.toContinuousLinearMap.adjoint).continuous
