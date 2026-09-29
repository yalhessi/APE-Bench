theorem probe_axioms_inconsistent : False := by
  have hB : BKMFinite (fun t => linftyNorm (fun x => Vorticity (fun _ t _ => |t|) x t)) 1 :=
    ⟨_, le_rfl⟩
  have h : ContDiff ℝ ⊤ (fun t : ℝ => |t|) :=
    (bkm_implies_regularity (fun _ t _ => |t|) 1 hB).2 0 0
  exact not_differentiableAt_abs_zero (h.differentiable (by simp) 0)

theorem probe_galerkin_smooth_axiom_free (ν : ℝ) (u₀ : T3 → Fin 3 → ℝ) :
    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
      SmoothSpacetime u ∧ SolvesNavierStokes ν u p ∧ (∀ x, u x 0 = u₀ x) :=
  ⟨fun x _ => u₀ x, fun _ _ => 0,
    ⟨fun _ _ _ => ⟨0, fun _ _ => trivial⟩, fun _ _ => contDiff_const⟩,
    fun _ _ _ _ => rfl, fun _ => rfl⟩

theorem probe_fubini_a (f : Fin 3 → UnitAddCircle → ℂ) :
    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y :=
  MeasureTheory.integral_fintype_prod_eq_prod _ f

theorem probe_fubini_b (f : Fin 3 → UnitAddCircle → ℂ) :
    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y :=
  MeasureTheory.integral_fintype_prod_eq_prod (ι := Fin 3) f

example : False := by
  have := @MeasureTheory.integral_fintype_prod_eq_prod
  exact this

example : False := by
  have := @UnitAddTorus.orthonormal_mFourier
  exact this

example : False := by
  have := @UnitAddTorus.mFourier
  exact this

example : False := by
  have := @UnitAddTorus.mFourierCoeff
  exact this

example : False := by
  have := @UnitAddTorus
  exact this

example : (⊤ : WithTop ℕ∞) = ω := rfl
