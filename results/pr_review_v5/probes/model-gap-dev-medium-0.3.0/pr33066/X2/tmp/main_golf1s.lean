public theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) (hf : Continuous f) :
    ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv := by
  /- Assume nontriviality of `V`.
    Then by `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`,
    we know there exists a continuous linear equivalence `y : V ≃L[𝕜] W` such that
    `f = y.conjAlgEquiv`.
    Our goal will be to construct an isometry from `y`. We do this by first showing
    `adjoint y ∘ y` is in the center of the endormorphisms, and as the algebra of endomorphisms
    are central, `adjoint y ∘ y` is a scalar multiple of the identity.
    Let `α : 𝕜` be that scalar, i.e., `adjoint y ∘ y = α • id`. This scalar is clearly real.
    Also, it's easy to see that `adjoint y ∘ y` is invertible, so `α ≠ 0`.
    As `adjoint y ∘ y` is positive, we get `0 < α`.
    We also get `y ∘ adjoint y = α • id`.
    Finally, we construct our isometry `1/√(re α) • y`. -/
  by_cases! hV : Subsingleton V
  · by_cases! hV : Subsingleton W
    · use { toLinearEquiv := 0, norm_map' _ := by simp [Subsingleton.eq_zero] }
      exact ext fun _ ↦ Subsingleton.allEq _ _
    simpa using congr(f $(Subsingleton.allEq 0 1))
  obtain ⟨y, hy⟩ := (ContinuousAlgEquiv.ofAlgEquiv f.toAlgEquiv hf
    (f.toAlgEquiv.toLinearEquiv.continuous_symm hf)).eq_continuousLinearEquivConjContinuousAlgEquiv
  have (x : V →L[𝕜] V) : adjoint (f x) = f (adjoint x) := map_star _ _ |>.symm
  rw [ContinuousAlgEquiv.ext_iff] at hy
  simp_rw [← StarAlgEquiv.coe_toAlgEquiv, ContinuousAlgEquiv.coe_ofAlgEquiv f.toAlgEquiv hf _ ▸ hy,
    conjContinuousAlgEquiv_apply, adjoint_comp] at this
  replace this (x : V →L[𝕜] V) : adjoint y.toContinuousLinearMap ∘L y ∘L adjoint x ∘L y.symm =
      adjoint x ∘L adjoint y.toContinuousLinearMap := by
    simp_rw [← this x, ← comp_assoc, ← adjoint_comp]
    simp
  replace this (x : V →L[𝕜] V) : Commute x (adjoint y.toContinuousLinearMap ∘L y) := by
    simp_rw [commute_iff_eq, mul_def, ← comp_assoc, ← (adjoint_adjoint x ▸ this _), comp_assoc]
    simp
  obtain ⟨α, hα⟩ := (Algebra.IsCentral.mem_center_iff 𝕜).mp <|
    Subalgebra.mem_center_iff.mpr fun _ ↦ this _
  rw [Algebra.algebraMap_eq_smul_one, eq_comm] at hα
  have this : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
    isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
      simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
        ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
  have hα0 : α ≠ 0 := fun h ↦ by simp [h, ← hα] at this
  have hαpos : 0 < α := by
    sorry
  obtain ⟨r, hr, rfl⟩ := RCLike.pos_iff_exists_ofReal.mp hαpos
  have thisU : y.toContinuousLinearMap ∘L adjoint y.toContinuousLinearMap =
      (r : 𝕜) • ContinuousLinearMap.id 𝕜 _ := by
    ext x
    simpa using congr(y (($hα ∘L y.symm.toContinuousLinearMap) x)).symm
  set αa := (((√r)⁻¹ : ℝ) : 𝕜)
  have αa2 : αa * αa = (r : 𝕜)⁻¹ := by
    simp [αa, ← RCLike.ofReal_mul, ← mul_inv, Real.mul_self_sqrt hr.le]
  set U := auxIsometry y hα0 αa2 hα.symm thisU (by simp [αa])
  use U
  have la : αa⁻¹ * αa = 1 := inv_mul_cancel₀ (by simp [αa, Real.sqrt_eq_zero', hr])
  ext
  simp [U.conjStarAlgEquiv_apply, U, smul_smul, la, ← conjContinuousAlgEquiv_apply, ← hy]
