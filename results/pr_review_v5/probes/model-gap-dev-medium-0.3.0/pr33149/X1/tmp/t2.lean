open scoped ContDiff in
example (f : ℝ → ℝ) : smoothInTime f ↔ ContDiff ℝ ω f := Iff.rfl

example (f : ℝ → ℝ) (h : smoothInTime f) : AnalyticAt ℝ f 0 := h.contDiffAt.analyticAt

example : T3 = UnitAddTorus (Fin 3) := rfl

example (k : Fin 3 → ℤ) (x : T3) : fourier3D k x = UnitAddTorus.mFourier k x := rfl

example : False := by
  have := @UnitAddTorus.orthonormal_mFourier (Fin 3) _
  exact this

example : False := by
  have := @UnitAddTorus.hasSum_sq_mFourierCoeff (Fin 3) _
  exact this

example : False := by
  have := @UnitAddTorus.hasSum_mFourier_series_of_summable (Fin 3) _
  exact this

example (f : T3 → ℂ) (k : Fin 3 → ℤ) : fourierCoeff3D f k = UnitAddTorus.mFourierCoeff f k := by
  rfl

theorem probe_ortho (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n
  rw [fourierLp, fourierLp, ContinuousMap.inner_toLp] at h
  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]
  simp_rw [mul_comm (fourier n _)]
  convert h using 1
  simp [eq_comm]

theorem probe_vort_int (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T := intervalIntegrable_const

theorem probe_hs_finite (s : ℝ) (u₀ : T3 → Fin 3 → ℝ) (h : SmoothInitial u₀) :
    ∃ M : ℝ, hsNorm s u₀ ≤ M ∧ 0 ≤ hsNorm s u₀ := ⟨_, le_rfl, Real.sqrt_nonneg _⟩
