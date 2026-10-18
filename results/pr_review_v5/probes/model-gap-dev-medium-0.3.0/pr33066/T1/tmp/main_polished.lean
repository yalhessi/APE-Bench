public theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) (hf : Continuous f) :
    ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv := by
  /- Assume nontriviality of `V`.
    Then by `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`,
    we know there exists a continuous linear equivalence `y : V ≃L[𝕜] W` such that
    `f = y.conjContinuousAlgEquiv`.
    Our goal will be to construct an isometry from `y`. We do this by first showing
    `adjoint y ∘ y` is in the center of the endomorphisms, and as the algebra of endomorphisms
    is central, `adjoint y ∘ y` is a scalar multiple of the identity.
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
  replace this := (Subalgebra.mem_center_iff (R := 𝕜)).mpr fun _ ↦ this _
  simp only [Algebra.IsCentral.center_eq_bot] at this
  obtain ⟨α, hα⟩ := this
  simp only [AlgHom.toRingHom_eq_coe, Algebra.toRingHom_ofId, Algebra.algebraMap_eq_smul_one] at hα
  have hunit : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
    isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
      simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
        ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
  have hα_re : α = RCLike.re α := by
    have h := by simpa [IsSelfAdjoint, ← hα, one_def, star_eq_adjoint] using
      (IsSelfAdjoint.one (W →L[𝕜] W)).adjoint_conj y.toContinuousLinearMap
    rwa [← one_def, (smul_left_injective 𝕜 one_ne_zero).eq_iff, RCLike.conj_eq_iff_re,
      eq_comm] at h
  have hα_ne : α ≠ 0 := fun h ↦ by simp [h, ← hα] at hunit
  have hα_pos : 0 ≤ α := by
    have h := hα_re.symm ▸ (nonneg_iff_isPositive _ |>.mpr
      (hα_re ▸ hα ▸ isPositive_adjoint_comp_self y.toContinuousLinearMap))
    rw [← LinearMap.isPositive_one.isPositive_smul_iff (E := V) (one_ne_zero' (V →ₗ[𝕜] V))]
    exact (nonneg_iff_isPositive _).mp h
  replace hα_pos := RCLike.ofReal_pos.mp <| hα_re ▸ (lt_of_le_of_ne' hα_pos hα_ne)
  have hy_adj : y.toContinuousLinearMap ∘L adjoint y.toContinuousLinearMap =
      α • ContinuousLinearMap.id 𝕜 _ := by
    ext x
    simpa using congr(y (($hα ∘L y.symm.toContinuousLinearMap) x)).symm
  set αa := (((√(RCLike.re α))⁻¹ : ℝ) : 𝕜)
  have hαa : αa * αa = α⁻¹ := by
    rw [hα_re]
    simp [αa, ← RCLike.ofReal_mul, ← mul_inv, Real.mul_self_sqrt hα_pos.le]
  set U := auxIsometry y hα_ne hαa hα.symm hy_adj (by simp [αa])
  refine ⟨U, ext fun A ↦ ContinuousLinearMap.ext fun w ↦ ?_⟩
  obtain ⟨v, rfl⟩ := U.surjective w
  rw [LinearIsometryEquiv.conjStarAlgEquiv_apply_apply, U.symm_apply_apply,
    show f A = _ from congr_fun hy A]
  simp [U]
