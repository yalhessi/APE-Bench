public theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) (hf : Continuous f) :
    ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv := by
  by_cases! hV : Subsingleton V
  · by_cases! hV : Subsingleton W
    · use { toLinearEquiv := 0, norm_map' _ := by simp [Subsingleton.eq_zero] }
      exact ext fun _ ↦ Subsingleton.allEq _ _
    simpa using congr(f $(Subsingleton.allEq 0 1))
  obtain ⟨y, hy⟩ := (ContinuousAlgEquiv.ofAlgEquiv f.toAlgEquiv hf
    (f.toAlgEquiv.toLinearEquiv.continuous_symm hf)).eq_continuousLinearEquivConjContinuousAlgEquiv
  have (x : V →L[𝕜] V) : adjoint (f x) = f (adjoint x) := map_star _ _ |>.symm
  rw [ContinuousAlgEquiv.ext_iff, ContinuousAlgEquiv.coe_ofAlgEquiv] at hy
  simp_rw [← StarAlgEquiv.coe_toAlgEquiv, hy, conjContinuousAlgEquiv_apply, adjoint_comp] at this
  replace this (x : V →L[𝕜] V) : adjoint y.toContinuousLinearMap ∘L y ∘L adjoint x ∘L y.symm =
      adjoint x ∘L adjoint y.toContinuousLinearMap := by
    simp_rw [← this x, ← comp_assoc, ← adjoint_comp]
    simp
  replace this (x : V →L[𝕜] V) : Commute x (adjoint y.toContinuousLinearMap ∘L y) := by
    have hx := this (adjoint x)
    rw [adjoint_adjoint] at hx
    simp_rw [commute_iff_eq, mul_def, ← comp_assoc, ← hx, comp_assoc]
    simp
  obtain ⟨α, hα⟩ := (Algebra.IsCentral.mem_center_iff 𝕜).mp <|
    (Subalgebra.mem_center_iff (R := 𝕜)).mpr fun _ ↦ this _
  rw [Algebra.algebraMap_eq_smul_one] at hα
  have this : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
    isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
      simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
        ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
  have hα0 : α ≠ 0 := fun h ↦ by simp [h, hα] at this
  have hα_nonneg : 0 ≤ α := by
    have h := isPositive_adjoint_comp_self y.toContinuousLinearMap
    rw [hα] at h
    exact (LinearMap.isPositive_one.isPositive_smul_iff (E := V) one_ne_zero).mp h.toLinearMap
  obtain ⟨r, hr, rfl⟩ := RCLike.pos_iff_exists_ofReal.mp (lt_of_le_of_ne' hα_nonneg hα0)
  have hyy : y.toContinuousLinearMap ∘L adjoint y.toContinuousLinearMap =
      (r : 𝕜) • ContinuousLinearMap.id 𝕜 _ := by
    ext x
    simpa using congr(y (($hα ∘L y.symm.toContinuousLinearMap) x))
  set s : 𝕜 := (((√r)⁻¹ : ℝ) : 𝕜)
  have hs : s * s = (r : 𝕜)⁻¹ := by
    simp [s, ← RCLike.ofReal_mul, ← mul_inv, Real.mul_self_sqrt hr.le]
  set U := auxIsometry y hα0 hs hα hyy (by simp [s])
  use U
  have hs' : s⁻¹ * s = 1 := inv_mul_cancel₀ (by simpa [s] using (Real.sqrt_pos.mpr hr).ne')
  ext
  simp [U.conjStarAlgEquiv_apply, U, smul_smul, hs', ← conjContinuousAlgEquiv_apply, ← hy]
