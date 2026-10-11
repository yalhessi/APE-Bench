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
  set s : 𝕜 := (((√r)⁻¹ : ℝ) : 𝕜)
  have hs0 : s ≠ 0 := by simpa [s] using (Real.sqrt_pos.mpr hr).ne'
  have hs : s * s = (r : 𝕜)⁻¹ := by
    simp [s, ← RCLike.ofReal_mul, ← mul_inv, Real.mul_self_sqrt hr.le]
  have hT : ∀ x, ‖(s • y.toContinuousLinearMap) x‖ = ‖x‖ :=
    (norm_map_iff_adjoint_comp_self _).mpr <| by
      simp only [MulActionSemiHomClass.map_smulₛₗ, comp_smulₛₗ, RingHom.id_apply, smul_comp,
        smul_smul, hα, ← mul_assoc, show starRingEnd 𝕜 s = s by simp [s], hs]
      simp [hr.ne', one_def]
  let U : V ≃ₗᵢ[𝕜] W := .ofSurjective ⟨(s • y.toContinuousLinearMap).toLinearMap, hT⟩ fun z ↦
    ⟨s⁻¹ • y.symm z, by simp [smul_smul, hs0]⟩
  have hU (x : V) : U x = s • y x := rfl
  have hU' (z : W) : U.symm z = s⁻¹ • y.symm z := by
    apply U.injective
    rw [U.apply_symm_apply, hU]
    simp [smul_smul, hs0]
  refine ⟨U, StarAlgEquiv.ext fun x ↦ ContinuousLinearMap.ext fun z ↦ ?_⟩
  rw [← StarAlgEquiv.coe_toAlgEquiv, hy]
  simp [hU, hU', smul_smul, hs0]
