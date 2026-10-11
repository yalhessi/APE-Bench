-- Q. fourier3D_orthogonal with binder-style `have` and no `have this`/`obtain` detour
lemma fourier3D_orthogonal' (k k' : Fin 3 → ℤ) :
    ∫ x : T3, fourier3D k x * star (fourier3D k' x) = if k = k' then 1 else 0 := by
  have h1 (x : T3) : fourier3D k x * star (fourier3D k' x) =
      ∏ i : Fin 3, (fourier (k i) (x i) * star (fourier (k' i) (x i))) := by
    rw [fourier3D, fourier3D, star_prod, ← Finset.prod_mul_distrib]
    rfl
  simp_rw [h1, MeasureTheory.integral_fintype_prod_volume_eq_prod (fun i y ↦
    fourier (k i) y * star (fourier (k' i) y)), fourier_ortho_integral]
  by_cases h : k = k'
  · simp [h]
  · obtain ⟨i, hi⟩ := Function.ne_iff.mp h
    rw [if_neg h]
    exact Finset.prod_eq_zero (Finset.mem_univ i) (if_neg hi)

-- R. uniform_vorticity_bound without `h_divfree`
lemma uniform_vorticity_bound' (u₀ : T3 → Fin 3 → ℝ) (h_smooth : SmoothInitial u₀)
    (T : ℝ) (hT : 0 < T) :
    ∃ C : ℝ, ∀ N : ℕ, ∀ t ∈ Set.Icc 0 T,
      linftyNorm (Vorticity (GalerkinProjection N u₀) · t) ≤ C := by
  refine ⟨cSobolev 3 * (hsNorm 3 u₀ * Real.exp (cGronwall 3 * T * hsNorm 3 u₀)),
    fun N t ht ↦ ?_⟩
  have hs : (3 : ℝ) > 5 / 2 := by norm_num
  calc linftyNorm (Vorticity (GalerkinProjection N u₀) · t)
      ≤ cSobolev 3 * hsNorm (3 - 1) (fun x ↦
          invFourier (spectralCurl (fourierTransform (GalerkinAt N u₀ t))) x) :=
        sobolev_embedding 3 hs _
    _ ≤ cSobolev 3 * hsNorm 3 (GalerkinAt N u₀ t) := by
        gcongr
        · exact (cSobolev_pos 3).le
        · exact vorticity_hs_bound 3 _
    _ ≤ _ := by
        gcongr
        · exact (cSobolev_pos 3).le
        · exact hs_gronwall_bound 3 hs u₀ h_smooth N T hT t ht

-- H1. fourier_ortho_integral from `orthonormal_fourier`
example (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n
  rw [ContinuousMap.inner_toLp] at h
  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]
  simp_rw [mul_comm (fourier n _)]
  convert h using 2
  exact propext eq_comm
