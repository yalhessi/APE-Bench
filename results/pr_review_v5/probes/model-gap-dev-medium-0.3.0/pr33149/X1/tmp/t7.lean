theorem probe_axioms_inconsistent : False := by
  have hB : BKMFinite (fun t => linftyNorm (fun x => Vorticity (fun _ t _ => |t|) x t)) 1 :=
    ⟨_, le_rfl⟩
  have h : ContDiff ℝ ⊤ (fun t : ℝ => |t|) :=
    (bkm_implies_regularity (fun _ t _ => |t|) 1 hB).2 0 0
  exact not_differentiableAt_abs_zero (h.differentiable (by simp) 0)

theorem probe_bkmFinite_trivial (ω : ℝ → ℝ) (T : ℝ) : BKMFinite ω T := ⟨_, le_rfl⟩

theorem probe_smoothInitial_trivial (u : T3 → Fin 3 → ℝ) : SmoothInitial u :=
  fun _ => ⟨0, fun _ _ => trivial⟩

theorem probe_solvesNS_trivial (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ) :
    SolvesNavierStokes ν u p := fun _ _ _ _ => rfl

theorem probe_galerkin_indep (N M : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) :
    GalerkinAt N u₀ t = GalerkinAt M u₀ 0 := rfl
