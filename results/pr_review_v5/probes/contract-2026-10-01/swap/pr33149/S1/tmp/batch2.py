import json, sys
P = "Mathlib/Analysis/ODE/GalerkinRegularity.lean"
edits = {
"vorticity_integrable": '''theorem vorticity_integrable (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T :=
  intervalIntegrable_const (c := linftyNorm fun x => Vorticity (GalerkinProjection N u₀) x 0)
''',
"tau_interval_finite": '''lemma tau_interval_finite (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (T : ℝ) (hT : 0 < T) :
    ∃ τ_T : ℝ, L.φ τ_T = T ∧ τ_T ≤ T / Φ.φ_min := by
  obtain ⟨τ_T, hτ_T⟩ := L.φ_surj T (le_of_lt hT)
  refine ⟨τ_T, hτ_T, ?_⟩
  by_cases hτ_nonneg : τ_T ≤ 0
  · calc τ_T ≤ 0 := hτ_nonneg
         _ ≤ T / Φ.φ_min := le_of_lt (div_pos hT Φ.hmin_pos)
  · push_neg at hτ_nonneg
    have key : Φ.φ_min * τ_T ≤ T := by
      rw [← hτ_T]
      have ftc : L.φ τ_T - L.φ 0 = ∫ s in (0)..τ_T, deriv L.φ s := by
        symm
        apply intervalIntegral.integral_deriv_eq_sub
        · intro x _; exact L.φ_diff.differentiableAt
        · exact L.φ_deriv_cont.intervalIntegrable 0 τ_T
      rw [L.φ_zero, sub_zero] at ftc
      rw [ftc]
      have const_int : Φ.φ_min * τ_T = ∫ s in (0)..τ_T, Φ.φ_min := by
        simp [intervalIntegral.integral_const]; ring
      rw [const_int]
      apply intervalIntegral.integral_mono_on (le_of_lt hτ_nonneg)
      · exact intervalIntegrable_const
      · exact L.φ_deriv_cont.intervalIntegrable 0 τ_T
      · intro x _; exact L.φ_deriv_pos x
    rw [le_div_iff₀ Φ.hmin_pos]
    linarith
''',
"bkm_coordinate_invariance": '''lemma bkm_coordinate_invariance (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (ω Ω : ℝ → ℝ) (hω_cont : Continuous ω) (h_relation : ∀ τ, Ω τ = ω (L.φ τ))
    (T : ℝ) (τ_T : ℝ) (hτ : L.φ τ_T = T) :
    bkmPhysical ω T = bkmLifted Ω L.φ τ_T := by
  simp only [bkmPhysical, bkmLifted, h_relation]
  rw [intervalIntegral.integral_comp_mul_deriv (fun x _ => (L.φ_diff x).hasDerivAt)
    L.φ_deriv_cont.continuousOn hω_cont, L.φ_zero, hτ]
''',
}
name = sys.argv[1]
print(json.dumps({"path":P,"declaration_name":name,"new_declaration":edits[name]}))
