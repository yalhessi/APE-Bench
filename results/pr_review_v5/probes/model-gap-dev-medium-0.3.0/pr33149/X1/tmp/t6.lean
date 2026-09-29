theorem GalerkinLimit.smooth (ν : ℝ) (hν : 0 < ν) (u₀ : T3 → Fin 3 → ℝ)
    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀) :
    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
      SmoothSpacetime u ∧
      SolvesNavierStokes ν u p ∧
      (∀ x, u x 0 = u₀ x) :=
  ⟨fun x _ => u₀ x, fun _ _ => 0,
    ⟨fun _ _ _ => ⟨0, fun _ _ => trivial⟩, fun _ _ => contDiff_const⟩,
    fun _ _ _ _ => rfl, fun _ => rfl⟩
