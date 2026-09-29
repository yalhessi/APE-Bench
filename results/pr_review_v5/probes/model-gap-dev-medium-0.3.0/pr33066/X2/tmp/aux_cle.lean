noncomputable abbrev auxContinuousLinearEquiv :
    V ≃L[𝕜] W :=
  .equivOfInverse' (α' • e.toContinuousLinearMap) (α' • e.toContinuousLinearMap.adjoint)
    (by simp [comp_smul, he', smul_smul, hα2, hα, ← mul_assoc])
    (by simp [comp_smul, he, smul_smul, hα2, hα, ← mul_assoc])
