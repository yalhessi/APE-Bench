theorem probe_ortho (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n
  rw [fourierLp, fourierLp, MeasureTheory.ContinuousMap.inner_toLp] at h
  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]
  simp_rw [mul_comm (fourier n _)]
  convert h using 1
  simp [eq_comm]

theorem probe_vort_int (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T := intervalIntegrable_const enorm_ne_top

theorem probe_fourier3D_orthogonal (k k' : Fin 3 → ℤ) :
    ∫ x : T3, fourier3D k x * star (fourier3D k' x) = if k = k' then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (UnitAddTorus.orthonormal_mFourier (d := Fin 3)) k' k
  exact h
