open ComplexOrder

/-- The ⋆-algebra equivalence version of
`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`.

TODO: remove the hypothesis `Continuous f`, as star-algebra equivalences between endomorphisms are
automatically continuous. -/
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
  have hα0 : α ≠ 0 := by
    have : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
      isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
        simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
          ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
    rintro rfl
    simp [← hα] at this
  have hpos : 0 ≤ α := by
    have := isPositive_adjoint_comp_self y.toContinuousLinearMap
    rw [← hα, ← isPositive_toLinearMap_iff] at this
    exact (LinearMap.isPositive_one.isPositive_smul_iff (one_ne_zero' (V →ₗ[𝕜] V))).mp this
  obtain ⟨r, hr, rfl⟩ := RCLike.pos_iff_exists_ofReal.mp (hpos.lt_of_ne' hα0)
  obtain ⟨s, hs, rfl⟩ : ∃ s : ℝ, 0 < s ∧ s * s = r :=
    ⟨√r, Real.sqrt_pos.2 hr, Real.mul_self_sqrt hr.le⟩
  have hs' : (s : 𝕜) ≠ 0 := RCLike.ofReal_ne_zero.mpr hs.ne'
  have key (a b : V) : inner 𝕜 (y a) (y b) = (s * s : ℝ) * inner 𝕜 a b := by
    rw [← ContinuousLinearEquiv.coe_coe, ← adjoint_inner_right, ← comp_apply, ← hα]
    simp [inner_smul_right]
  let U : V ≃ₗᵢ[𝕜] W :=
    (y.toLinearEquiv.trans (.smulOfNeZero 𝕜 W _ (inv_ne_zero hs'))).isometryOfInner fun a b ↦ by
      simp [inner_smul_left, inner_smul_right, key]
      field_simp
  refine ⟨U, StarAlgEquiv.ext fun x ↦ ContinuousLinearMap.ext fun w ↦ ?_⟩
  obtain ⟨v, rfl⟩ := U.surjective w
  have hfx : f x (y v) = y (x v) := by simpa using congr($(congr_fun hy x) (y v))
  rw [LinearIsometryEquiv.conjStarAlgEquiv_apply_apply, U.symm_apply_apply]
  simp [U, hfx]
