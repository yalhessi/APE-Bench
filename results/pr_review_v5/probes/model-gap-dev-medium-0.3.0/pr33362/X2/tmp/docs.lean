/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and a positive radius
`R₁` to a closed ball with center `f c` and radius `R₂`, then the norm of the derivative of
`f` at `c` is at most the ratio `R₂ / R₁`. -/
theorem norm_deriv_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (h₀ : 0 < R₁) :
    ‖deriv f c‖ ≤ R₂ / R₁ := by
  simpa only [dslope_same] using norm_dslope_le_div_of_mapsTo_ball hd h_maps (mem_ball_self h₀)

/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and radius `R₁` to a
closed ball with center `f c` and radius `R₂`, then for any `z` in the former disk we have
`dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`. -/
theorem dist_le_div_mul_dist_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (hz : z ∈ ball c R₁) :
    dist (f z) (f c) ≤ R₂ / R₁ * dist z c := by
  rcases eq_or_ne z c with (rfl | hne)
  · simp only [dist_self, mul_zero, le_rfl]
  simpa only [dslope_of_ne _ hne, slope_def_module, norm_smul, norm_inv, ← div_eq_inv_mul, ←
    dist_eq_norm, div_le_iff₀ (dist_pos.2 hne)] using norm_dslope_le_div_of_mapsTo_ball hd h_maps hz

/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and positive radius
`R` to the closed ball with center `f c` and the same radius, then the norm of the derivative of
`f` at `c` is at most `1`. -/
theorem norm_deriv_le_one_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (closedBall (f c) R)) (h₀ : 0 < R) : ‖deriv f c‖ ≤ 1 :=
  (norm_deriv_le_div_of_mapsTo_ball hd h_maps h₀).trans_eq (div_self h₀.ne')

/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and radius `R` to the
closed ball with center `f c` and the same radius, then for any point `z` of this disk we have
`dist (f z) (f c) ≤ dist z c`. -/
theorem dist_le_dist_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (closedBall (f c) R)) (hz : z ∈ ball c R) :
    dist (f z) (f c) ≤ dist z c := by
  simpa [(nonempty_ball.1 ⟨z, hz⟩).ne'] using dist_le_div_mul_dist_of_mapsTo_ball hd h_maps hz
