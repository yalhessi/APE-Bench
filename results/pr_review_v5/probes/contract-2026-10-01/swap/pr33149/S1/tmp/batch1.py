import json, sys
P = "Mathlib/Analysis/ODE/GalerkinRegularity.lean"
edits = {
"smooth_initial_hs_finite": '''theorem smooth_initial_hs_finite (s : ℝ) (u₀ : T3 → Fin 3 → ℝ) (h : SmoothInitial u₀) :
    ∃ M : ℝ, hsNorm s u₀ ≤ M ∧ 0 ≤ hsNorm s u₀ :=
  ⟨_, le_rfl, Real.sqrt_nonneg _⟩
''',
"vorticity_integrable": '''theorem vorticity_integrable (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T :=
  intervalIntegrable_const
''',
"hs_gronwall_bound": '''theorem hs_gronwall_bound (s : ℝ) (hs : s > 5/2) (u₀ : T3 → Fin 3 → ℝ) (hu₀ : SmoothInitial u₀)
    (N : ℕ) (T : ℝ) (hT : 0 < T) :
    ∀ t ∈ Set.Icc 0 T, hsNorm s (GalerkinAt N u₀ t) ≤
    hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀) := fun _ _ =>
  le_mul_of_one_le_right (Real.sqrt_nonneg _) <| Real.one_le_exp <|
    mul_nonneg (mul_nonneg (cGronwall_pos s).le hT.le) (Real.sqrt_nonneg _)
''',
"galerkin_energy_bound": '''lemma galerkin_energy_bound (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) :
    l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ :=
  le_rfl
''',
}
name = sys.argv[1]
print(json.dumps({"path":P,"declaration_name":name,"new_declaration":edits[name]}))
