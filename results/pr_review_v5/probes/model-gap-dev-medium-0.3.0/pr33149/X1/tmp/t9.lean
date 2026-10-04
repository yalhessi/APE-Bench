lemma tau_interval_finite (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (T : ℝ) (hT : 0 < T) :
    ∃ τ_T : ℝ, L.φ τ_T = T ∧ τ_T ≤ T / Φ.φ_min := by
  obtain ⟨τ_T, hτ_T⟩ := L.φ_surj T hT.le
  refine ⟨τ_T, hτ_T, ?_⟩
  rcases le_or_gt τ_T 0 with hτ | hτ
  · exact hτ.trans (div_pos hT Φ.hmin_pos).le
  · have key := mul_sub_le_image_sub_of_le_deriv L.φ_diff L.φ_deriv_pos hτ.le
    rw [L.φ_zero, hτ_T, sub_zero, sub_zero] at key
    rw [le_div_iff₀ Φ.hmin_pos]
    linarith
