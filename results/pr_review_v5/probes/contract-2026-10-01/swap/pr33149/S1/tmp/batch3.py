import json, sys
P = "Mathlib/Analysis/ODE/GalerkinRegularity.lean"
edits = {
"bkm_coordinate_invariance": '''lemma bkm_coordinate_invariance (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (ω Ω : ℝ → ℝ) (hω_cont : Continuous ω) (h_relation : ∀ τ, Ω τ = ω (L.φ τ))
    (T : ℝ) (τ_T : ℝ) (hτ : L.φ τ_T = T) :
    bkmPhysical ω T = bkmLifted Ω L.φ τ_T := by
  have := intervalIntegral.integral_comp_mul_deriv (a := 0) (b := τ_T)
    (fun x _ => (L.φ_diff x).hasDerivAt) L.φ_deriv_cont.continuousOn hω_cont
  rw [L.φ_zero, hτ] at this
  simp only [bkmPhysical, bkmLifted, h_relation]
  exact this.symm
''',
}
name = sys.argv[1]
print(json.dumps({"path":P,"declaration_name":name,"new_declaration":edits[name]}))
