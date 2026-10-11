-- A. the axiom `bkm_implies_regularity` proves `False`
example : False := by
  have h := bkm_implies_regularity (fun _ t _ => |t|) 0 ⟨_, le_rfl⟩
  have hc : ContDiff ℝ ⊤ (fun t : ℝ => |t|) := h.2 0 0
  exact not_differentiableAt_abs_zero (hc.differentiable le_top 0)

-- B. BKMFinite is vacuous
example (ω : ℝ → ℝ) (T : ℝ) : BKMFinite ω T := ⟨_, le_rfl⟩

-- C. SmoothInitial is vacuous
example (u : T3 → Fin 3 → ℝ) : SmoothInitial u := fun _ ↦ ⟨0, fun _ _ ↦ trivial⟩

-- D. SolvesNavierStokes is vacuous
example (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ) : SolvesNavierStokes ν u p :=
  fun _ _ _ _ ↦ rfl

-- E. smoothInTime is analyticity
open scoped ContDiff in
example (f : ℝ → ℝ) : smoothInTime f ↔ ContDiff ℝ ω f := Iff.rfl

-- F. `% 3` is a no-op on `Fin 3`
example : ∀ j : Fin 3, (j + 1) % 3 = j + 1 ∧ (j + 2) % 3 = j + 2 := by decide

-- G. fubini_torus3 is a library lemma
example (f : Fin 3 → UnitAddCircle → ℂ) :
    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y :=
  MeasureTheory.integral_fintype_prod_volume_eq_prod f

-- I. tau_interval_finite golfed, with `0 ≤ T`
lemma tau_interval_finite' (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (T : ℝ) (hT : 0 ≤ T) :
    ∃ τ_T : ℝ, L.φ τ_T = T ∧ τ_T ≤ T / Φ.φ_min := by
  obtain ⟨τ_T, hτ_T⟩ := L.φ_surj T hT
  refine ⟨τ_T, hτ_T, (le_div_iff₀ Φ.hmin_pos).2 ?_⟩
  rcases le_or_gt τ_T 0 with h | h
  · nlinarith [Φ.hmin_pos]
  · have := mul_sub_le_image_sub_of_le_deriv L.φ_diff L.φ_deriv_pos h.le
    rw [sub_zero, L.φ_zero, sub_zero, hτ_T] at this
    linarith

-- J. bkm_finite_anyT golfed (original route)
lemma bkm_finite_anyT' (u₀ : T3 → Fin 3 → ℝ)
    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀)
    (T : ℝ) (hT : 0 < T) (N : ℕ) :
    BKMFinite (fun t ↦ linftyNorm (fun x ↦ Vorticity (GalerkinProjection N u₀) x t)) T := by
  obtain ⟨C, hC⟩ := uniform_vorticity_bound u₀ h_smooth h_divfree T hT
  refine ⟨C * T, ?_⟩
  calc _ ≤ ∫ _ in (0)..T, C :=
        intervalIntegral.integral_mono_on hT.le (vorticity_integrable N u₀ T)
          intervalIntegrable_const fun t ht ↦ hC N t ht
    _ = C * T := by simp [mul_comm]

-- K. galerkin_energy_bound by le_rfl
example (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) : l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ := le_rfl

-- L. GalerkinProjection ignores N and t
example (N M : ℕ) (u₀ : T3 → Fin 3 → ℝ) (x : T3) (t s : ℝ) :
    GalerkinProjection N u₀ x t = GalerkinProjection M u₀ x s := rfl

-- M. main theorem needs none of its hypotheses
theorem regularity' (ν : ℝ) (u₀ : T3 → Fin 3 → ℝ) :
    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
      SmoothSpacetime u ∧ SolvesNavierStokes ν u p ∧ (∀ x, u x 0 = u₀ x) :=
  ⟨GalerkinProjection 1 u₀, fun _ _ ↦ 0, bkm_implies_regularity _ 1 ⟨_, le_rfl⟩,
    fun _ _ _ _ ↦ rfl, fun _ ↦ rfl⟩

-- O. bkm_coordinate_invariance is integral_comp_mul_deriv, for any C¹ φ
lemma bkm_coordinate_invariance' (φ : ℝ → ℝ) (hφ : Differentiable ℝ φ)
    (hφ' : Continuous (deriv φ)) (hφ0 : φ 0 = 0) (ω : ℝ → ℝ) (hω : Continuous ω) (τ_T : ℝ) :
    bkmPhysical ω (φ τ_T) = bkmLifted (ω ∘ φ) φ τ_T := by
  rw [bkmPhysical, bkmLifted, intervalIntegral.integral_comp_mul_deriv
    (fun x _ ↦ (hφ x).hasDerivAt) hφ'.continuousOn hω, hφ0]

-- P. fourier3D is UnitAddTorus.mFourier
example (k : Fin 3 → ℤ) (x : T3) : fourier3D k x = UnitAddTorus.mFourier k x := rfl

-- S. structure literal
example : VorticityResponse := ⟨1, 2, one_pos, one_le_two⟩
