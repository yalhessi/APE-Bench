theorem probe_vort_int_a (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T := by
  unfold Vorticity GalerkinProjection
  simp

theorem probe_vort_int_b (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T := by
  unfold Vorticity GalerkinProjection
  exact intervalIntegrable_const (E := ℝ) enorm_ne_top

theorem probe_tau_calc (a T t : ℝ) (ha : 0 < a) (key : a * t ≤ T) : t ≤ T / a := by
  rw [le_div_iff₀ ha]; linarith

example (f : ℝ → ℝ) (h : smoothInTime f) : AnalyticAt ℝ f 0 := h.contDiffAt.analyticAt
