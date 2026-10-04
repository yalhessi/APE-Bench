theorem GalerkinLimit.smooth (ν : ℝ) (hν : 0 < ν) (u₀ : T3 → Fin 3 → ℝ)
    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀) :
    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
      SmoothSpacetime u ∧
      SolvesNavierStokes ν u p ∧
      (∀ x, u x 0 = u₀ x) := by
  let Φ : VorticityResponse := {
    φ_min := 1
    φ_max := 2
    hmin_pos := one_pos
    hbounds := le_of_lt one_lt_two
  }
  exact VorticityResponse.regularity Φ ν hν u₀ h_smooth h_divfree
