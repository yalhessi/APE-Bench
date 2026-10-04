theorem probe_mFourier_orthogonal (k k' : Fin 3 → ℤ) :
    ∫ x : UnitAddTorus (Fin 3), UnitAddTorus.mFourier k x * star (UnitAddTorus.mFourier k' x) =
      if k = k' then 1 else 0 := by
  have h := orthonormal_iff_ite.mp (UnitAddTorus.orthonormal_mFourier (d := Fin 3)) k' k
  rw [UnitAddTorus.mFourierLp, UnitAddTorus.mFourierLp,
    MeasureTheory.ContinuousMap.inner_toLp] at h
  simpa [eq_comm] using h

theorem probe_energy (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) :
    l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ := le_rfl
