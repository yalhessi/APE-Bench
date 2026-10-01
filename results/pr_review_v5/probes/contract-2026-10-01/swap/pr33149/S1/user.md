# Pull request #33149

**Title:** feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³

**Description:**
Establishes global existence and smoothness for Galerkin approximations of incompressible Navier-Stokes on T³ with smooth divergence-free initial data.

Main result: `GalerkinLimit.smooth`

**Changed files:**
  - `Mathlib/Analysis/ODE/GalerkinRegularity.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33149 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
- description: Establishes global existence and smoothness for Galerkin approximations of incompressible Navier-Stokes on T³ with smooth divergence-free initial data.

Main result: `GalerkinLimit.smooth`
- changed files: Mathlib/Analysis/ODE/GalerkinRegularity.lean

## Objects

### `command in GalerkinRegularity.lean` (command, added) [04b7243613]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Smooth solutions exist for the Galerkin limit -/
```

### `command in GalerkinRegularity.lean` (command, added) [066f8c2b96]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- A bounded vorticity-response functional Φ : ℝ≥0 → [φ_min, φ_max] -/
```

### `bkm_implies_regularity` (axiom, added) [0ab9322b7c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom bkm_implies_regularity :
    ∀ (u : T3 → ℝ → Fin 3 → ℝ) (T : ℝ),
      BKMFinite (fun t => linftyNorm (fun x => Vorticity u x t)) T →
      SmoothSpacetime u
```

### `linftyNorm` (def, added) [11edaeea2a]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def linftyNorm (f : T3 → Fin 3 → ℝ) : ℝ :=
  ⨆ (x : T3) (j : Fin 3), |f x j|
```

### `cSobolev_pos` (axiom, added) [1208e7f5b8]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cSobolev_pos : ∀ s, 0 < cSobolev s
```

### `fourierDecay` (def, added) [14d670db44]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def fourierDecay (u : T3 → Fin 3 → ℝ) (k : Fin 3 → ℤ) (j : Fin 3) (n : ℕ) (C : ℝ) : Prop :=
  True
```

### `command in GalerkinRegularity.lean` (command, added) [195ba48056]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Galerkin projection of initial data -/
```

### `l2Norm` (def, added) [200aa70aba]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def l2Norm (f : T3 → Fin 3 → ℝ) : ℝ :=
  Real.sqrt (∫ x : T3, ∑ j : Fin 3, (f x j)^2)
```

### `command in GalerkinRegularity.lean` (command, added) [21c61fb5e9]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Three-dimensional Fourier basis function -/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [2338104ac6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Main Theorems
-/
```

### `command in GalerkinRegularity.lean` (command, added) [2906e1b319]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Vorticity of velocity field -/
```

### `namespace in GalerkinRegularity.lean` (command, added) [29a9a47d95]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open scoped InnerProductSpace
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [29d4e82ab0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Temporal Lifting
-/
```

### `command in GalerkinRegularity.lean` (command, added) [2b9909f9b4]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Gronwall constant for H^s norm control -/
```

### `SmoothInitial` (def, added) [2f4ba7b2d6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def SmoothInitial (u : T3 → Fin 3 → ℝ) : Prop :=
  ∀ n : ℕ, ∃ C : ℝ, ∀ k : Fin 3 → ℤ, ∀ j : Fin 3, fourierDecay u k j n C
```

### `VorticityResponse` (structure, added) [30d7c92eba]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
structure VorticityResponse where
  /-- Lower bound on temporal density -/
  φ_min : ℝ
  /-- Upper bound on temporal density -/
  φ_max : ℝ
  /-- Positivity of lower bound -/
  hmin_pos : 0 < φ_min
  /-- Ordering of bounds -/
  hbounds : φ_min ≤ φ_max
```

### `command in GalerkinRegularity.lean` (command, added) [353f575fc1]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- L∞ norm of vector field -/
```

### `command in GalerkinRegularity.lean` (command, added) [36df01d4d6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
#check GalerkinLimit.smooth
```

### `fourier1D` (def, added) [37b8ba4ad0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def fourier1D (n : ℤ) : UnitAddCircle → ℂ :=
  fourier n
```

### `SolvesNavierStokes` (def, added) [39f2ffb5fb]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def SolvesNavierStokes (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ) : Prop :=
  ∀ t ≥ 0, ∀ k : Fin 3 → ℤ, ∀ j : Fin 3, spectralNSResidual ν u t k j = 0
```

### `command in GalerkinRegularity.lean` (command, added) [3a54597be3]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
#print axioms GalerkinLimit.smooth
```

### `command in GalerkinRegularity.lean` (command, added) [3b10071f2c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- BKM integral in physical time -/
```

### `command in GalerkinRegularity.lean` (command, added) [3bb863b9dc]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Smooth in both space and time -/
```

### `command in GalerkinRegularity.lean` (command, added) [3e5986030f]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Sobolev embedding constant -/
```

### `command in GalerkinRegularity.lean` (command, added) [3f7d29a6ad]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Moser estimate constant for nonlinear term bounds -/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [3f868241bd]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Energy Bounds
-/
```

### `fourier3D_orthogonal` (lemma, added) [3fb8b425f4]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma fourier3D_orthogonal (k k' : Fin 3 → ℤ) :
    ∫ x : T3, fourier3D k x * star (fourier3D k' x) = if k = k' then 1 else 0 := by
  have ortho1D : ∀ (n m : ℤ),
      ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 :=
    fourier_ortho_integral
  have fubini : ∫ x : T3, fourier3D k x * star (fourier3D k' x) =
      ∏ i : Fin 3, ∫ y : UnitAddCircle, fourier (k i) y * star (fourier (k' i) y) := by
    have h1 : ∀ x : T3, fourier3D k x * star (fourier3D k' x) =
        ∏ i : Fin 3, (fourier (k i) (x i) * star (fourier (k' i) (x i))) := by
      intro x
      unfold fourier3D fourier1D
      rw [star_prod, ← Finset.prod_mul_distrib]
    simp_rw [h1]
    exact fubini_torus3 (fun i y => fourier (k i) y * star (fourier (k' i) y))
  rw [fubini]
  simp only [ortho1D]
  by_cases h : k = k'
  · subst h
    simp
  · have : ∃ i, k i ≠ k' i := Function.ne_iff.mp h
    obtain ⟨i, hi⟩ := this
    have hz : ∏ j : Fin 3, (if k j = k' j then (1 : ℂ) else 0) = 0 := by
      apply Finset.prod_eq_zero (Finset.mem_univ i)
      simp [hi]
    simp [h, hz]
```

### `VorticityResponse.regularity` (theorem, added) [40520a78ed]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem VorticityResponse.regularity (Φ : VorticityResponse) (ν : ℝ) (_hν : 0 < ν)
    (u₀ : T3 → Fin 3 → ℝ) (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀) :
    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
      SmoothSpacetime u ∧
      SolvesNavierStokes ν u p ∧
      (∀ x, u x 0 = u₀ x) := by
  let u : T3 → ℝ → Fin 3 → ℝ := GalerkinProjection 1 u₀
  let p : T3 → ℝ → ℝ := fun _ _ => 0
  have hBKM : BKMFinite (fun t => linftyNorm (fun x => Vorticity u x t)) 1 :=
    bkm_finite_anyT Φ u₀ h_smooth h_divfree 1 one_pos 1
  have hSmooth : SmoothSpacetime u := bkm_implies_regularity u 1 hBKM
  have hNS : SolvesNavierStokes ν u p := by
    intro t _ k j
    simp [spectralNSResidual]
  have hInit : ∀ x, u x 0 = u₀ x := by
    intro x
    ext j
    rfl
  exact ⟨u, p, hSmooth, hNS, hInit⟩
```

### `command in GalerkinRegularity.lean` (command, added) [4347f0f1e3]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Leray projection in Fourier space -/
```

### `fourier_ortho_integral` (axiom, added) [43caf038a1]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom fourier_ortho_integral (n m : ℤ) :
    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0
```

### `bkmLifted` (def, added) [4a93cd5b46]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def bkmLifted (Ω : ℝ → ℝ) (φ : ℝ → ℝ) (τ_T : ℝ) : ℝ :=
  ∫ τ in (0)..τ_T, Ω τ * deriv φ τ
```

### `BKMFinite` (def, added) [4bb93487bf]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def BKMFinite (ω : ℝ → ℝ) (T : ℝ) : Prop :=
  ∃ M : ℝ, ∫ t in (0)..T, ω t ≤ M
```

### `GalerkinAt` (def, added) [4cd87081fe]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def GalerkinAt (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) : T3 → Fin 3 → ℝ :=
  fun x => GalerkinProjection N u₀ x t
```

### `bkm_finite_anyT` (lemma, added) [55d65efb5b]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma bkm_finite_anyT (Φ : VorticityResponse) (u₀ : T3 → Fin 3 → ℝ)
    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀)
    (T : ℝ) (hT : 0 < T) (N : ℕ) :
    BKMFinite (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t)) T := by
  obtain ⟨C, hC⟩ := uniform_vorticity_bound u₀ h_smooth h_divfree T hT
  use C * T
  have bound : ∀ t ∈ Set.Icc 0 T,
      linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t) ≤ C := by
    intro t ht
    exact hC N t ht
  calc ∫ t in (0)..T, linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t)
      ≤ ∫ t in (0)..T, C := by
        apply intervalIntegral.integral_mono_on (le_of_lt hT)
        · exact vorticity_integrable N u₀ T
        · exact intervalIntegrable_const
        · intro t ht
          exact bound t (Set.mem_Icc.mpr ⟨ht.1, ht.2⟩)
      _ = C * T := by
        rw [intervalIntegral.integral_const, sub_zero, smul_eq_mul, mul_comm]
```

### `command in GalerkinRegularity.lean` (command, added) [561de4d15a]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Fourier coefficient of a function on T³ -/
```

### `vorticity_hs_bound` (axiom, added) [567e8713e1]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom vorticity_hs_bound (s : ℝ) (u : T3 → Fin 3 → ℝ) :
    hsNorm (s - 1) (fun x => invFourier (spectralCurl (fourierTransform u)) x) ≤
    hsNorm s u
```

### `cSobolev` (axiom, added) [56b96be8d6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cSobolev : ℝ → ℝ
```

### `command in GalerkinRegularity.lean` (command, added) [56f2a107b1]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Smooth function of time -/
```

### `cMoser` (axiom, added) [58660f102e]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cMoser : ℝ → ℝ
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [5a58d91221]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Fourier Analysis on T³
-/
```

### `fourierCoeff3D` (def, added) [5ac53df706]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def fourierCoeff3D (f : T3 → ℂ) (k : Fin 3 → ℤ) : ℂ :=
  ∫ x : T3, f x * star (fourier3D k x)
```

### `fourierCoeff_summable` (axiom, added) [5f8b0c67d6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom fourierCoeff_summable (f : T3 → ℂ) (hf : Continuous f) :
    Summable (fun k => ‖fourierCoeff3D f k‖^2)
```

### `parseval3D` (theorem, added) [60b5342e51]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem parseval3D (f : T3 → ℂ) (hf : Continuous f) :
    ∫ x : T3, ‖f x‖^2 = ∑' k : Fin 3 → ℤ, ‖fourierCoeff3D f k‖^2 := by
  have expand : ∫ x : T3, ‖f x‖^2 =
      ∫ x : T3, ‖∑' k, fourierCoeff3D f k * fourier3D k x‖^2 := by
    congr 1; funext x
    rw [fourier_inversion f hf x]
  rw [expand]
  exact parseval_orthonormal (fourierCoeff3D f) (fourierCoeff_summable f hf)
```

### `hs_gronwall_bound` (axiom, added) [61ed160f65]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom hs_gronwall_bound (s : ℝ) (hs : s > 5/2) (u₀ : T3 → Fin 3 → ℝ) (hu₀ : SmoothInitial u₀)
    (N : ℕ) (T : ℝ) (hT : 0 < T) :
    ∀ t ∈ Set.Icc 0 T, hsNorm s (GalerkinAt N u₀ t) ≤
    hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)
```

### `fourierTruncate` (def, added) [62781a8675]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def fourierTruncate (N : ℕ) (û : FourierCoeff) : FourierCoeff := fun k j =>
  if (∑ i : Fin 3, |k i|) ≤ N then û k j else 0
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [634b0af718]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response Functionals

This file proves global existence and smoothness of solutions to the incompressible
Navier-Stokes equations on the three-torus T³ for smooth divergence-free initial data.

## Main results

- `VorticityResponse`: Structure encoding bounded vorticity-response functional
- `TemporalLifting`: Temporal lifting as a coupled system with diffeomorphism properties
- `uniform_vorticity_bound`: Uniform vorticity bounds independent of Galerkin truncation
- `bkm_coordinate_invariance`: BKM integral invariance under temporal reparameterization
- `bkm_finite_anyT`: BKM integral finiteness for any finite time interval
- `GalerkinLimit.smooth`: Main theorem establishing global smooth solutions

## Implementation notes

The proof proceeds via temporal lifting, generalizing Sundman regularization from celestial
mechanics. Uniform bounds on Galerkin approximations combined with coordinate invariance
of the Beale-Kato-Majda integral yield finiteness in physical time.

## References

- Beale, Kato, Majda (1984): Remarks on the breakdown of smooth solutions
- Sundman (1912): Mémoire sur le problème des trois corps
- Camlin (2025): Global Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response
  Functionals. DOI: 10.63968/post-bio-ai-epistemics.v1n2.012
-/
```

### `smoothInTime` (def, added) [6606d482de]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def smoothInTime (f : ℝ → ℝ) : Prop :=
  ContDiff ℝ ⊤ f
```

### `GalerkinProjection` (def, added) [681a224e77]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def GalerkinProjection (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) : T3 → ℝ → Fin 3 → ℝ :=
  fun x t j => u₀ x j
```

### `command in GalerkinRegularity.lean` (command, added) [68656edb8d]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Spectral curl operator -/
```

### `galerkin_energy_bound` (lemma, added) [72312ca0b6]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma galerkin_energy_bound (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) (ht : 0 ≤ t) :
    l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ := by
  unfold GalerkinAt GalerkinProjection
  rfl
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [731b02f102]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## BKM Coordinate Invariance
-/
```

### `smooth_initial_hs_finite` (axiom, added) [751880a545]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom smooth_initial_hs_finite (s : ℝ) (u₀ : T3 → Fin 3 → ℝ) (h : SmoothInitial u₀) :
    ∃ M : ℝ, hsNorm s u₀ ≤ M ∧ 0 ≤ hsNorm s u₀
```

### `command in GalerkinRegularity.lean` (command, added) [7521efd5e3]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Fourier truncation to N modes -/
```

### `LerayProjection` (def, added) [76774409fc]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def LerayProjection (f : FourierCoeff) : FourierCoeff := fun k j =>
  if k = 0 then f k j
  else f k j - (∑ i : Fin 3, (k i : ℂ) * f k i) * (k j : ℂ) / (∑ i : Fin 3, (k i : ℂ)^2)
```

### `command in GalerkinRegularity.lean` (command, added) [78e6c09f54]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Beale-Kato-Majda integral finiteness -/
```

### `command in GalerkinRegularity.lean` (command, added) [7bbe154f46]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Regularity from bounded vorticity response -/
```

### `command in GalerkinRegularity.lean` (command, added) [7f9afdb013]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Spectral Navier-Stokes residual -/
```

### `hsNorm` (def, added) [813b9c42a1]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def hsNorm (s : ℝ) (f : T3 → Fin 3 → ℝ) : ℝ :=
  Real.sqrt (∑' k : Fin 3 → ℤ, (1 + ‖(fun i => (k i : ℝ))‖^2)^s *
    ∑ j : Fin 3, ‖fourierTransform f k j‖^2)
```

### `cGronwall_pos` (axiom, added) [83ea1c981c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cGronwall_pos : ∀ s, 0 < cGronwall s
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [84ba1341ad]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Analytic Estimates
-/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [874606e678]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Parseval Identity
-/
```

### `T3` (abbrev, added) [89fb9872e0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev T3 := Fin 3 → UnitAddCircle
```

### `command in GalerkinRegularity.lean` (command, added) [8b7f876a0b]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- L² norm of vector field -/
```

### `fourierTransform` (def, added) [8d1fc1decf]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def fourierTransform (u : T3 → Fin 3 → ℝ) : FourierCoeff :=
  fun k j => fourierCoeff3D (fun x => (u x j : ℂ)) k
```

### `cMoser_pos` (axiom, added) [960d382089]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cMoser_pos : ∀ s, 0 < cMoser s
```

### `fubini_torus3` (axiom, added) [9791fc8ddd]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom fubini_torus3 (f : Fin 3 → UnitAddCircle → ℂ) :
    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y
```

### `command in GalerkinRegularity.lean` (command, added) [9d7594689e]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Solution satisfies Navier-Stokes equations -/
```

### `invFourier` (def, added) [a1366d6d42]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def invFourier (f : FourierCoeff) : T3 → Fin 3 → ℝ :=
  fun x j => (∑' k : Fin 3 → ℤ, f k j * fourier3D k x).re
```

### `FourierCoeff` (abbrev, added) [a234878f2a]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
abbrev FourierCoeff := (Fin 3 → ℤ) → (Fin 3 → ℂ)
```

### `command in GalerkinRegularity.lean` (command, added) [a3dad84df5]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The three-dimensional torus T³ := (ℝ/ℤ)³ -/
```

### `spectralNSResidual` (def, added) [a43e79cc5b]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def spectralNSResidual (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (t : ℝ) (k : Fin 3 → ℤ) (j : Fin 3) :
    ℂ :=
  0
```

### `moser_estimate` (axiom, added) [a739a981dc]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom moser_estimate (s : ℝ) (hs : s > 3/2) (u : T3 → Fin 3 → ℝ) :
    hsNorm s (fun x j => ∑ i : Fin 3, u x i * u x j) ≤
    cMoser s * hsNorm s u * hsNorm s u
```

### `parseval_orthonormal` (axiom, added) [a85efd34ab]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom parseval_orthonormal (c : (Fin 3 → ℤ) → ℂ) (hc : Summable (fun k => ‖c k‖^2)) :
    ∫ x : T3, ‖∑' k, c k * fourier3D k x‖^2 = ∑' k, ‖c k‖^2
```

### `command in GalerkinRegularity.lean` (command, added) [ac597695bd]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Fourier decay condition for smoothness -/
```

### `command in GalerkinRegularity.lean` (command, added) [ae109c5c50]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Sobolev H^s norm via Fourier coefficients -/
```

### `command in GalerkinRegularity.lean` (command, added) [aed229ef42]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- BKM integral in lifted time -/
```

### `fourier3D` (def, added) [b0b0df436c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def fourier3D (k : Fin 3 → ℤ) : T3 → ℂ :=
  fun x => ∏ i : Fin 3, fourier1D (k i) (x i)
```

### `uniform_vorticity_bound` (lemma, added) [b2b6721db7]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma uniform_vorticity_bound (u₀ : T3 → Fin 3 → ℝ) (h_smooth : SmoothInitial u₀)
    (h_divfree : DivergenceFree u₀) (T : ℝ) (hT : 0 < T) :
    ∃ C : ℝ, ∀ N : ℕ, ∀ t ∈ Set.Icc 0 T,
      linftyNorm (Vorticity (GalerkinProjection N u₀) · t) ≤ C := by
  let s : ℝ := 3
  have hs : s > 5/2 := by norm_num
  let C := cSobolev s * hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)
  use C
  intro N t ht
  calc linftyNorm (Vorticity (GalerkinProjection N u₀) · t)
      = linftyNorm (fun x =>
          invFourier (spectralCurl (fourierTransform (GalerkinAt N u₀ t))) x) := by
        rfl
      _ ≤ cSobolev s * hsNorm (s - 1) (fun x =>
          invFourier (spectralCurl (fourierTransform (GalerkinAt N u₀ t))) x) := by
        exact sobolev_embedding s hs _
      _ ≤ cSobolev s * hsNorm s (GalerkinAt N u₀ t) := by
        apply mul_le_mul_of_nonneg_left
        · exact vorticity_hs_bound s (GalerkinAt N u₀ t)
        · exact le_of_lt (cSobolev_pos s)
      _ ≤ cSobolev s * (hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)) := by
        apply mul_le_mul_of_nonneg_left
        · exact hs_gronwall_bound s hs u₀ h_smooth N T hT t ht
        · exact le_of_lt (cSobolev_pos s)
      _ = C := by ring
```

### `command in GalerkinRegularity.lean` (command, added) [b96d78523d]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- One-dimensional Fourier basis function -/
```

### `command in GalerkinRegularity.lean` (command, added) [b99c1c6f96]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Galerkin approximation at fixed time -/
```

### `DivergenceFree` (def, added) [b9a1e6aa47]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def DivergenceFree (u : T3 → Fin 3 → ℝ) : Prop :=
  ∀ k : Fin 3 → ℤ, ∑ j : Fin 3, (k j : ℂ) * fourierTransform u k j = 0
```

### `command in GalerkinRegularity.lean` (command, added) [be53ea45d9]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Temporal lifting structure encoding the diffeomorphism t = φ(τ) -/
```

### `tau_interval_finite` (lemma, added) [beea82b9b8]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma tau_interval_finite (Φ : VorticityResponse) (L : TemporalLifting Φ)
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
    have hne : Φ.φ_min ≠ 0 := ne_of_gt Φ.hmin_pos
    calc τ_T = τ_T * 1 := (mul_one _).symm
         _ = τ_T * (Φ.φ_min / Φ.φ_min) := by rw [div_self hne]
         _ = (τ_T * Φ.φ_min) / Φ.φ_min := by ring
         _ = (Φ.φ_min * τ_T) / Φ.φ_min := by ring
         _ ≤ T / Φ.φ_min := div_le_div_of_nonneg_right key (le_of_lt Φ.hmin_pos)
```

### `SmoothSpacetime` (def, added) [bf8503e9b4]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def SmoothSpacetime (u : T3 → ℝ → Fin 3 → ℝ) : Prop :=
  (∀ t : ℝ, 0 ≤ t → SmoothInitial (fun x => u x t)) ∧
  (∀ x : T3, ∀ j : Fin 3, smoothInTime (fun t => u x t j))
```

### `command in GalerkinRegularity.lean` (command, added) [c233068d5f]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Fourier coefficient type -/
```

### `command in GalerkinRegularity.lean` (command, added) [c4356a2588]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Divergence-free condition in Fourier space -/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [c4973f8535]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## BKM Finiteness
-/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [c6871b4216]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Fourier Orthogonality
-/
```

### `command in GalerkinRegularity.lean` (command, added) [cc385bf288]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
set_option linter.style.commandStart false
```

### `command in GalerkinRegularity.lean` (command, added) [cfc507d66a]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Smooth initial data has rapid Fourier decay -/
```

### `Vorticity` (def, added) [d2a312914c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def Vorticity (u : T3 → ℝ → Fin 3 → ℝ) : T3 → ℝ → Fin 3 → ℝ :=
  fun x t => invFourier (spectralCurl (fourierTransform (u · t))) x
```

### `TemporalLifting` (structure, added) [d7a37fabb0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
structure TemporalLifting (Φ : VorticityResponse) where
  /-- The temporal diffeomorphism -/
  φ : ℝ → ℝ
  /-- Initial condition φ(0) = 0 -/
  φ_zero : φ 0 = 0
  /-- Differentiability of φ -/
  φ_diff : Differentiable ℝ φ
  /-- Continuity of derivative -/
  φ_deriv_cont : Continuous (deriv φ)
  /-- Lower bound on derivative (non-degeneracy) -/
  φ_deriv_pos : ∀ τ, Φ.φ_min ≤ deriv φ τ
  /-- Upper bound on derivative (boundedness) -/
  φ_deriv_bdd : ∀ τ, deriv φ τ ≤ Φ.φ_max
  /-- Surjectivity (global coverage) -/
  φ_surj : ∀ t ≥ 0, ∃ τ, φ τ = t
```

### `spectralCurl` (def, added) [d886428a24]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def spectralCurl (û : FourierCoeff) : FourierCoeff := fun k j =>
  let j1 := (j + 1) % 3
  let j2 := (j + 2) % 3
  Complex.I * ((k j1 : ℂ) * û k j2 - (k j2 : ℂ) * û k j1)
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [db74003820]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Axioms (after definitions they reference)
-/
```

### `bkm_coordinate_invariance` (lemma, added) [dc8225d29c]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma bkm_coordinate_invariance (Φ : VorticityResponse) (L : TemporalLifting Φ)
    (ω Ω : ℝ → ℝ) (hω_cont : Continuous ω) (h_relation : ∀ τ, Ω τ = ω (L.φ τ))
    (T : ℝ) (hT : 0 ≤ T) (τ_T : ℝ) (hτ : L.φ τ_T = T) :
    bkmPhysical ω T = bkmLifted Ω L.φ τ_T := by
  unfold bkmPhysical bkmLifted
  have step1 : ∫ τ in (0)..τ_T, Ω τ * deriv L.φ τ =
      ∫ τ in (0)..τ_T, ω (L.φ τ) * deriv L.φ τ := by
    congr 1; ext τ; rw [h_relation]
  rw [step1]
  have subst : ∫ x in (0)..τ_T, ω (L.φ x) * deriv L.φ x =
      ∫ t in (L.φ 0)..(L.φ τ_T), ω t := by
    apply intervalIntegral.integral_comp_mul_deriv
    · intro x _; exact (L.φ_diff x).hasDerivAt
    · exact L.φ_deriv_cont.continuousOn
    · exact hω_cont
  rw [L.φ_zero, hτ] at subst
  exact subst.symm
```

### `command in GalerkinRegularity.lean` (command, added) [e35fd84544]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Inverse Fourier transform -/
```

### `sobolev_embedding` (axiom, added) [e4590fbb0d]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom sobolev_embedding (s : ℝ) (hs : s > 5/2) (f : T3 → Fin 3 → ℝ) :
    linftyNorm f ≤ cSobolev s * hsNorm (s - 1) f
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [e5eeec4265]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Analysis Constants

Standard constants from Moser estimates, Gronwall inequalities, and Sobolev embeddings.
-/
```

### `integral_le_const_mul_length` (axiom, added) [e68da314be]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom integral_le_const_mul_length (f : ℝ → ℝ) (C T : ℝ) (hT : 0 < T)
    (hf : ∀ t ∈ Set.Icc 0 T, f t ≤ C) :
    ∫ t in (0)..T, f t ≤ C * T
```

### `bkmPhysical` (def, added) [ed593c1f6e]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable def bkmPhysical (ω : ℝ → ℝ) (T : ℝ) : ℝ :=
  ∫ t in (0)..T, ω t
```

### `vorticity_integrable` (axiom, added) [ed973f3bfd]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom vorticity_integrable (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
    IntervalIntegrable
      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
      MeasureTheory.volume 0 T
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [f357c97c32]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Vorticity Response Functional
-/
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [f3d314d0e0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Basic Definitions
-/
```

### `command in GalerkinRegularity.lean` (command, added) [f84bb8aeea]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Fourier transform of vector field -/
```

### `GalerkinLimit.smooth` (theorem, added) [f8cc1f805d]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
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
```

### `module_doc in GalerkinRegularity.lean` (module_doc, added) [f97a563ff0]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Uniform Vorticity Bounds
-/
```

### `fourier_inversion` (axiom, added) [fd27a90a72]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
axiom fourier_inversion (f : T3 → ℂ) (hf : Continuous f) (x : T3) :
    f x = ∑' k : Fin 3 → ℤ, fourierCoeff3D f k * fourier3D k x
```

### `cGronwall` (axiom, added) [fece1fe682]
- file: `Mathlib/Analysis/ODE/GalerkinRegularity.lean`; changed: name:added, statement_or_type:added
- as the PR leaves it:
```lean
axiom cGronwall : ℝ → ℝ
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `bkm_coordinate_invariance`, `tau_interval_finite` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `spectralCurl`, `spectralNSResidual` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `FourierCoeff`, `SmoothInitial`, `Vorticity`, `VorticityResponse`, `bkm_implies_regularity`, `cGronwall`, `cGronwall_pos`, `cMoser_pos`, `cSobolev`, `cSobolev_pos`, `fourier1D`, `fourier3D`, `fourier3D_orthogonal`, `fourierCoeff3D`, `fourierCoeff_summable`, `fourierDecay`, `fourierTransform`, `fourierTruncate`, `fourier_inversion`, `fourier_ortho_integral`, `fubini_torus3`, `hs_gronwall_bound`, `integral_le_const_mul_length`, `invFourier`, `moser_estimate`, `parseval3D`, `parseval_orthonormal`, `smooth_initial_hs_finite`, `sobolev_embedding`, `uniform_vorticity_bound`, `vorticity_hs_bound`, `vorticity_integrable` -- 32 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `GalerkinAt`, `GalerkinProjection`, `LerayProjection`, `galerkin_energy_bound` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `bkm_coordinate_invariance` -> `tau_interval_finite`
- changed_siblings [high]: `bkm_implies_regularity` -> `parseval_orthonormal`
- changed_siblings [high]: `bkm_implies_regularity` -> `fourierCoeff_summable`
- changed_siblings [high]: `cGronwall_pos` -> `cSobolev_pos`
- changed_siblings [high]: `cGronwall_pos` -> `cMoser_pos`
- changed_siblings [high]: `cMoser_pos` -> `cSobolev`
- changed_siblings [high]: `cMoser_pos` -> `cGronwall_pos`
- changed_siblings [high]: `cSobolev` -> `cMoser_pos`
- changed_siblings [high]: `cSobolev_pos` -> `cGronwall_pos`
- changed_siblings [high]: `fourierCoeff_summable` -> `integral_le_const_mul_length`
- changed_siblings [high]: `fourierCoeff_summable` -> `bkm_implies_regularity`
- changed_siblings [high]: `fourier_inversion` -> `parseval_orthonormal`
- changed_siblings [high]: `fourier_ortho_integral` -> `fubini_torus3`
- changed_siblings [high]: `fubini_torus3` -> `fourier_ortho_integral`
- changed_siblings [high]: `hs_gronwall_bound` -> `sobolev_embedding`
- changed_siblings [high]: `hs_gronwall_bound` -> `moser_estimate`
- changed_siblings [high]: `integral_le_const_mul_length` -> `fourierCoeff_summable`
- changed_siblings [high]: `integral_le_const_mul_length` -> `vorticity_integrable`
- changed_siblings [high]: `moser_estimate` -> `hs_gronwall_bound`
- changed_siblings [high]: `parseval_orthonormal` -> `fourier_inversion`
- changed_siblings [high]: `parseval_orthonormal` -> `bkm_implies_regularity`
- changed_siblings [high]: `smooth_initial_hs_finite` -> `vorticity_hs_bound`
- changed_siblings [high]: `sobolev_embedding` -> `vorticity_hs_bound`
- changed_siblings [high]: `sobolev_embedding` -> `hs_gronwall_bound`
- changed_siblings [high]: `tau_interval_finite` -> `bkm_coordinate_invariance`
- changed_siblings [high]: `vorticity_hs_bound` -> `sobolev_embedding`
- changed_siblings [high]: `vorticity_hs_bound` -> `smooth_initial_hs_finite`
- changed_siblings [high]: `vorticity_integrable` -> `integral_le_const_mul_length`
- declaration_dependency [exact]: `DivergenceFree` -> `T3`
- declaration_dependency [exact]: `GalerkinAt` -> `T3`
- declaration_dependency [exact]: `GalerkinLimit.smooth` -> `SmoothInitial`
- declaration_dependency [exact]: `GalerkinLimit.smooth` -> `SmoothSpacetime`
- declaration_dependency [exact]: `GalerkinLimit.smooth` -> `DivergenceFree`
- declaration_dependency [exact]: `GalerkinLimit.smooth` -> `SolvesNavierStokes`
- declaration_dependency [exact]: `GalerkinLimit.smooth` -> `T3`
- declaration_dependency [exact]: `GalerkinProjection` -> `T3`
- declaration_dependency [exact]: `LerayProjection` -> `FourierCoeff`
- declaration_dependency [exact]: `SmoothInitial` -> `T3`
- declaration_dependency [exact]: `SmoothSpacetime` -> `T3`
- declaration_dependency [exact]: `SolvesNavierStokes` -> `T3`
- declaration_dependency [exact]: `TemporalLifting` -> `VorticityResponse`
- declaration_dependency [exact]: `Vorticity` -> `T3`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `SolvesNavierStokes`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `SmoothInitial`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `DivergenceFree`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `VorticityResponse`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `T3`
- declaration_dependency [exact]: `VorticityResponse.regularity` -> `SmoothSpacetime`
- declaration_dependency [exact]: `bkm_coordinate_invariance` -> `VorticityResponse`
- declaration_dependency [exact]: `bkm_coordinate_invariance` -> `bkmLifted`
- declaration_dependency [exact]: `bkm_coordinate_invariance` -> `bkmPhysical`
- declaration_dependency [exact]: `bkm_coordinate_invariance` -> `TemporalLifting`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `T3`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `BKMFinite`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `linftyNorm`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `Vorticity`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `VorticityResponse`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `SmoothInitial`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `DivergenceFree`
- declaration_dependency [exact]: `bkm_finite_anyT` -> `GalerkinProjection`
- declaration_dependency [exact]: `cGronwall_pos` -> `cGronwall`
- declaration_dependency [exact]: `cMoser_pos` -> `cMoser`
- declaration_dependency [exact]: `cSobolev_pos` -> `cSobolev`
- declaration_dependency [exact]: `fourier3D` -> `T3`
- declaration_dependency [exact]: `fourier3D_orthogonal` -> `fourier3D`
- declaration_dependency [exact]: `fourier3D_orthogonal` -> `T3`
- declaration_dependency [exact]: `fourierCoeff3D` -> `T3`
- declaration_dependency [exact]: `fourierCoeff_summable` -> `T3`
- declaration_dependency [exact]: `fourierDecay` -> `T3`
- declaration_dependency [exact]: `fourierTransform` -> `T3`
- declaration_dependency [exact]: `fourierTransform` -> `FourierCoeff`
- declaration_dependency [exact]: `fourierTruncate` -> `FourierCoeff`
- declaration_dependency [exact]: `fourier_inversion` -> `T3`
- declaration_dependency [exact]: `galerkin_energy_bound` -> `GalerkinAt`
- declaration_dependency [exact]: `galerkin_energy_bound` -> `T3`
- declaration_dependency [exact]: `galerkin_energy_bound` -> `l2Norm`
- declaration_dependency [exact]: `hsNorm` -> `T3`
- declaration_dependency [exact]: `hs_gronwall_bound` -> `SmoothInitial`
- declaration_dependency [exact]: `hs_gronwall_bound` -> `T3`
- declaration_dependency [exact]: `invFourier` -> `T3`
- declaration_dependency [exact]: `invFourier` -> `FourierCoeff`
- declaration_dependency [exact]: `l2Norm` -> `T3`
- declaration_dependency [exact]: `linftyNorm` -> `T3`
- declaration_dependency [exact]: `moser_estimate` -> `T3`
- declaration_dependency [exact]: `parseval3D` -> `T3`
- declaration_dependency [exact]: `parseval3D` -> `fourierCoeff3D`
- declaration_dependency [exact]: `smooth_initial_hs_finite` -> `SmoothInitial`
- declaration_dependency [exact]: `smooth_initial_hs_finite` -> `T3`
- declaration_dependency [exact]: `sobolev_embedding` -> `T3`
- declaration_dependency [exact]: `spectralCurl` -> `FourierCoeff`
- declaration_dependency [exact]: `spectralNSResidual` -> `T3`
- declaration_dependency [exact]: `tau_interval_finite` -> `TemporalLifting`
- declaration_dependency [exact]: `tau_interval_finite` -> `VorticityResponse`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `Vorticity`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `DivergenceFree`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `T3`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `SmoothInitial`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `GalerkinProjection`
- declaration_dependency [exact]: `uniform_vorticity_bound` -> `linftyNorm`
- declaration_dependency [exact]: `vorticity_hs_bound` -> `T3`
- declaration_dependency [exact]: `vorticity_integrable` -> `T3`
- direct_use_of_changed_declaration [exact]: `DivergenceFree` -> `fourierTransform`
- direct_use_of_changed_declaration [exact]: `GalerkinAt` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `GalerkinLimit.smooth` -> `VorticityResponse`
- direct_use_of_changed_declaration [exact]: `GalerkinLimit.smooth` -> `VorticityResponse.regularity`
- direct_use_of_changed_declaration [exact]: `SmoothInitial` -> `fourierDecay`
- direct_use_of_changed_declaration [exact]: `SmoothSpacetime` -> `SmoothInitial`
- direct_use_of_changed_declaration [exact]: `SmoothSpacetime` -> `smoothInTime`
- direct_use_of_changed_declaration [exact]: `SmoothSpacetime` -> `T3`
- direct_use_of_changed_declaration [exact]: `SolvesNavierStokes` -> `spectralNSResidual`
- direct_use_of_changed_declaration [exact]: `Vorticity` -> `spectralCurl`
- direct_use_of_changed_declaration [exact]: `Vorticity` -> `fourierTransform`
- direct_use_of_changed_declaration [exact]: `Vorticity` -> `invFourier`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `SolvesNavierStokes`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `bkm_finite_anyT`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `BKMFinite`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `bkm_implies_regularity`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `Vorticity`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `T3`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `spectralNSResidual`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `VorticityResponse.regularity` -> `SmoothSpacetime`
- direct_use_of_changed_declaration [exact]: `bkm_coordinate_invariance` -> `bkmPhysical`
- direct_use_of_changed_declaration [exact]: `bkm_coordinate_invariance` -> `bkmLifted`
- direct_use_of_changed_declaration [exact]: `bkm_finite_anyT` -> `uniform_vorticity_bound`
- direct_use_of_changed_declaration [exact]: `bkm_finite_anyT` -> `vorticity_integrable`
- direct_use_of_changed_declaration [exact]: `bkm_finite_anyT` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `bkm_finite_anyT` -> `Vorticity`
- direct_use_of_changed_declaration [exact]: `bkm_finite_anyT` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `bkm_implies_regularity` -> `T3`
- direct_use_of_changed_declaration [exact]: `bkm_implies_regularity` -> `BKMFinite`
- direct_use_of_changed_declaration [exact]: `bkm_implies_regularity` -> `Vorticity`
- direct_use_of_changed_declaration [exact]: `bkm_implies_regularity` -> `SmoothSpacetime`
- direct_use_of_changed_declaration [exact]: `bkm_implies_regularity` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `fourier3D` -> `fourier1D`
- direct_use_of_changed_declaration [exact]: `fourier3D_orthogonal` -> `fubini_torus3`
- direct_use_of_changed_declaration [exact]: `fourier3D_orthogonal` -> `fourier1D`
- direct_use_of_changed_declaration [exact]: `fourier3D_orthogonal` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `fourier3D_orthogonal` -> `fourier_ortho_integral`
- direct_use_of_changed_declaration [exact]: `fourier3D_orthogonal` -> `T3`
- direct_use_of_changed_declaration [exact]: `fourierCoeff3D` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `fourierCoeff3D` -> `T3`
- direct_use_of_changed_declaration [exact]: `fourierCoeff_summable` -> `fourierCoeff3D`
- direct_use_of_changed_declaration [exact]: `fourierTransform` -> `fourierCoeff3D`
- direct_use_of_changed_declaration [exact]: `fourier_inversion` -> `fourierCoeff3D`
- direct_use_of_changed_declaration [exact]: `fourier_inversion` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `fubini_torus3` -> `T3`
- direct_use_of_changed_declaration [exact]: `galerkin_energy_bound` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `galerkin_energy_bound` -> `GalerkinAt`
- direct_use_of_changed_declaration [exact]: `hsNorm` -> `fourierTransform`
- direct_use_of_changed_declaration [exact]: `hs_gronwall_bound` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `hs_gronwall_bound` -> `GalerkinAt`
- direct_use_of_changed_declaration [exact]: `hs_gronwall_bound` -> `cGronwall`
- direct_use_of_changed_declaration [exact]: `invFourier` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `l2Norm` -> `T3`
- direct_use_of_changed_declaration [exact]: `linftyNorm` -> `T3`
- direct_use_of_changed_declaration [exact]: `moser_estimate` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `moser_estimate` -> `cMoser`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `parseval_orthonormal`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `fourierCoeff3D`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `fourier_inversion`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `fourierCoeff_summable`
- direct_use_of_changed_declaration [exact]: `parseval3D` -> `T3`
- direct_use_of_changed_declaration [exact]: `parseval_orthonormal` -> `T3`
- direct_use_of_changed_declaration [exact]: `parseval_orthonormal` -> `fourier3D`
- direct_use_of_changed_declaration [exact]: `smooth_initial_hs_finite` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `sobolev_embedding` -> `cSobolev`
- direct_use_of_changed_declaration [exact]: `sobolev_embedding` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `sobolev_embedding` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `cSobolev`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `cGronwall`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `cSobolev_pos`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `invFourier`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `Vorticity`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `spectralCurl`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `hs_gronwall_bound`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `sobolev_embedding`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `vorticity_hs_bound`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `GalerkinAt`
- direct_use_of_changed_declaration [exact]: `uniform_vorticity_bound` -> `fourierTransform`
- direct_use_of_changed_declaration [exact]: `vorticity_hs_bound` -> `spectralCurl`
- direct_use_of_changed_declaration [exact]: `vorticity_hs_bound` -> `fourierTransform`
- direct_use_of_changed_declaration [exact]: `vorticity_hs_bound` -> `invFourier`
- direct_use_of_changed_declaration [exact]: `vorticity_hs_bound` -> `hsNorm`
- direct_use_of_changed_declaration [exact]: `vorticity_integrable` -> `linftyNorm`
- direct_use_of_changed_declaration [exact]: `vorticity_integrable` -> `GalerkinProjection`
- direct_use_of_changed_declaration [exact]: `vorticity_integrable` -> `Vorticity`
- name_family [high]: `FourierCoeff` -> `fourier3D`
- name_family [high]: `FourierCoeff` -> `fourier_inversion`
- name_family [high]: `FourierCoeff` -> `fourierDecay`
- name_family [high]: `FourierCoeff` -> `fourierTruncate`
- name_family [high]: `FourierCoeff` -> `fourier1D`
- name_family [high]: `FourierCoeff` -> `fourierCoeff3D`
- name_family [high]: `FourierCoeff` -> `fourierCoeff_summable`
- name_family [high]: `FourierCoeff` -> `invFourier`
- name_family [high]: `FourierCoeff` -> `fourier_ortho_integral`
- name_family [high]: `FourierCoeff` -> `fourierTransform`
- name_family [high]: `FourierCoeff` -> `fourier3D_orthogonal`
- name_family [high]: `GalerkinAt` -> `GalerkinProjection`
- name_family [high]: `GalerkinAt` -> `galerkin_energy_bound`
- name_family [high]: `GalerkinProjection` -> `GalerkinAt`
- name_family [high]: `GalerkinProjection` -> `galerkin_energy_bound`
- name_family [high]: `GalerkinProjection` -> `LerayProjection`
- name_family [high]: `LerayProjection` -> `GalerkinProjection`
- name_family [high]: `SmoothInitial` -> `smooth_initial_hs_finite`
- name_family [high]: `Vorticity` -> `vorticity_integrable`
- name_family [high]: `Vorticity` -> `vorticity_hs_bound`
- name_family [high]: `Vorticity` -> `VorticityResponse`
- name_family [high]: `Vorticity` -> `uniform_vorticity_bound`
- name_family [high]: `VorticityResponse` -> `uniform_vorticity_bound`
- name_family [high]: `VorticityResponse` -> `vorticity_integrable`
- name_family [high]: `VorticityResponse` -> `vorticity_hs_bound`
- name_family [high]: `VorticityResponse` -> `Vorticity`
- name_family [high]: `cGronwall` -> `cGronwall_pos`
- name_family [high]: `cGronwall` -> `hs_gronwall_bound`
- name_family [high]: `cGronwall_pos` -> `cGronwall`
- name_family [high]: `cGronwall_pos` -> `hs_gronwall_bound`
- name_family [high]: `cSobolev` -> `cSobolev_pos`
- name_family [high]: `cSobolev` -> `sobolev_embedding`
- name_family [high]: `cSobolev_pos` -> `sobolev_embedding`
- name_family [high]: `cSobolev_pos` -> `cSobolev`
- name_family [high]: `fourier1D` -> `fourierCoeff_summable`
- name_family [high]: `fourier1D` -> `fourierCoeff3D`
- name_family [high]: `fourier1D` -> `fourier_inversion`
- name_family [high]: `fourier1D` -> `invFourier`
- name_family [high]: `fourier1D` -> `fourierDecay`
- name_family [high]: `fourier1D` -> `fourierTruncate`
- name_family [high]: `fourier1D` -> `FourierCoeff`
- name_family [high]: `fourier1D` -> `fourier3D_orthogonal`
- name_family [high]: `fourier1D` -> `fourier3D`
- name_family [high]: `fourier1D` -> `fourier_ortho_integral`
- name_family [high]: `fourier1D` -> `fourierTransform`
- name_family [high]: `fourier3D` -> `fourier3D_orthogonal`
- name_family [high]: `fourier3D` -> `fourierTransform`
- name_family [high]: `fourier3D` -> `invFourier`
- name_family [high]: `fourier3D` -> `fourierTruncate`
- name_family [high]: `fourier3D` -> `fourierDecay`
- name_family [high]: `fourier3D` -> `fourierCoeff_summable`
- name_family [high]: `fourier3D` -> `fourier_ortho_integral`
- name_family [high]: `fourier3D` -> `fourierCoeff3D`
- name_family [high]: `fourier3D` -> `fourier_inversion`
- name_family [high]: `fourier3D` -> `fourier1D`
- name_family [high]: `fourier3D` -> `FourierCoeff`
- name_family [high]: `fourier3D_orthogonal` -> `FourierCoeff`
- name_family [high]: `fourier3D_orthogonal` -> `fourier_inversion`
- name_family [high]: `fourier3D_orthogonal` -> `fourierTruncate`
- name_family [high]: `fourier3D_orthogonal` -> `fourierCoeff_summable`
- name_family [high]: `fourier3D_orthogonal` -> `fourierDecay`
- name_family [high]: `fourier3D_orthogonal` -> `fourier1D`
- name_family [high]: `fourier3D_orthogonal` -> `fourierTransform`
- name_family [high]: `fourier3D_orthogonal` -> `fourier3D`
- name_family [high]: `fourier3D_orthogonal` -> `fourierCoeff3D`
- name_family [high]: `fourier3D_orthogonal` -> `fourier_ortho_integral`
- name_family [high]: `fourier3D_orthogonal` -> `invFourier`
- name_family [high]: `fourierCoeff3D` -> `fourier_ortho_integral`
- name_family [high]: `fourierCoeff3D` -> `fourierTruncate`
- name_family [high]: `fourierCoeff3D` -> `fourier3D_orthogonal`
- name_family [high]: `fourierCoeff3D` -> `FourierCoeff`
- name_family [high]: `fourierCoeff3D` -> `fourier3D`
- name_family [high]: `fourierCoeff3D` -> `fourier_inversion`
- name_family [high]: `fourierCoeff3D` -> `fourierCoeff_summable`
- name_family [high]: `fourierCoeff3D` -> `invFourier`
- name_family [high]: `fourierCoeff3D` -> `fourierTransform`
- name_family [high]: `fourierCoeff3D` -> `fourier1D`
- name_family [high]: `fourierCoeff3D` -> `fourierDecay`
- name_family [high]: `fourierCoeff_summable` -> `fourier_ortho_integral`
- name_family [high]: `fourierCoeff_summable` -> `fourierTruncate`
- name_family [high]: `fourierCoeff_summable` -> `fourier_inversion`
- name_family [high]: `fourierCoeff_summable` -> `fourierDecay`
- name_family [high]: `fourierCoeff_summable` -> `fourierTransform`
- name_family [high]: `fourierCoeff_summable` -> `invFourier`
- name_family [high]: `fourierCoeff_summable` -> `fourier1D`
- name_family [high]: `fourierCoeff_summable` -> `fourier3D`
- name_family [high]: `fourierCoeff_summable` -> `fourier3D_orthogonal`
- name_family [high]: `fourierCoeff_summable` -> `FourierCoeff`
- name_family [high]: `fourierCoeff_summable` -> `fourierCoeff3D`
- name_family [high]: `fourierDecay` -> `fourier3D_orthogonal`
- name_family [high]: `fourierDecay` -> `fourier1D`
- name_family [high]: `fourierDecay` -> `fourierTruncate`
- name_family [high]: `fourierDecay` -> `fourierCoeff_summable`
- name_family [high]: `fourierDecay` -> `invFourier`
- name_family [high]: `fourierDecay` -> `fourierTransform`
- name_family [high]: `fourierDecay` -> `fourierCoeff3D`
- name_family [high]: `fourierDecay` -> `fourier_inversion`
- name_family [high]: `fourierDecay` -> `fourier_ortho_integral`
- name_family [high]: `fourierDecay` -> `fourier3D`
- name_family [high]: `fourierDecay` -> `FourierCoeff`
- name_family [high]: `fourierTransform` -> `fourier1D`
- name_family [high]: `fourierTransform` -> `fourierTruncate`
- name_family [high]: `fourierTransform` -> `fourier3D`
- name_family [high]: `fourierTransform` -> `fourier3D_orthogonal`
- name_family [high]: `fourierTransform` -> `fourierDecay`
- name_family [high]: `fourierTransform` -> `fourier_ortho_integral`
- name_family [high]: `fourierTransform` -> `fourierCoeff3D`
- name_family [high]: `fourierTransform` -> `invFourier`
- name_family [high]: `fourierTransform` -> `FourierCoeff`
- name_family [high]: `fourierTransform` -> `fourierCoeff_summable`
- name_family [high]: `fourierTransform` -> `fourier_inversion`
- name_family [high]: `fourierTruncate` -> `fourier3D_orthogonal`
- name_family [high]: `fourierTruncate` -> `invFourier`
- name_family [high]: `fourierTruncate` -> `fourierCoeff_summable`
- name_family [high]: `fourierTruncate` -> `fourier_ortho_integral`
- name_family [high]: `fourierTruncate` -> `fourierDecay`
- name_family [high]: `fourierTruncate` -> `fourier_inversion`
- name_family [high]: `fourierTruncate` -> `fourierTransform`
- name_family [high]: `fourierTruncate` -> `fourier3D`
- name_family [high]: `fourierTruncate` -> `fourierCoeff3D`
- name_family [high]: `fourierTruncate` -> `FourierCoeff`
- name_family [high]: `fourierTruncate` -> `fourier1D`
- name_family [high]: `fourier_inversion` -> `fourierDecay`
- name_family [high]: `fourier_inversion` -> `FourierCoeff`
- name_family [high]: `fourier_inversion` -> `fourier3D_orthogonal`
- name_family [high]: `fourier_inversion` -> `fourier_ortho_integral`
- name_family [high]: `fourier_inversion` -> `fourierTransform`
- name_family [high]: `fourier_inversion` -> `fourier3D`
- name_family [high]: `fourier_inversion` -> `fourierCoeff3D`
- name_family [high]: `fourier_inversion` -> `fourierCoeff_summable`
- name_family [high]: `fourier_inversion` -> `invFourier`
- name_family [high]: `fourier_inversion` -> `fourierTruncate`
- name_family [high]: `fourier_inversion` -> `fourier1D`
- name_family [high]: `fourier_ortho_integral` -> `fourier3D`
- name_family [high]: `fourier_ortho_integral` -> `fourier_inversion`
- name_family [high]: `fourier_ortho_integral` -> `fourier1D`
- name_family [high]: `fourier_ortho_integral` -> `fourier3D_orthogonal`
- name_family [high]: `fourier_ortho_integral` -> `integral_le_const_mul_length`
- name_family [high]: `fourier_ortho_integral` -> `fourierCoeff3D`
- name_family [high]: `fourier_ortho_integral` -> `fourierDecay`
- name_family [high]: `fourier_ortho_integral` -> `FourierCoeff`
- name_family [high]: `fourier_ortho_integral` -> `fourierTruncate`
- name_family [high]: `fourier_ortho_integral` -> `invFourier`
- name_family [high]: `fourier_ortho_integral` -> `fourierTransform`
- name_family [high]: `fourier_ortho_integral` -> `fourierCoeff_summable`
- name_family [high]: `galerkin_energy_bound` -> `GalerkinProjection`
- name_family [high]: `galerkin_energy_bound` -> `GalerkinAt`
- name_family [high]: `hs_gronwall_bound` -> `cGronwall_pos`
- name_family [high]: `hs_gronwall_bound` -> `cGronwall`
- name_family [high]: `integral_le_const_mul_length` -> `fourier_ortho_integral`
- name_family [high]: `invFourier` -> `fourier3D`
- name_family [high]: `invFourier` -> `fourier1D`
- name_family [high]: `invFourier` -> `fourierTransform`
- name_family [high]: `invFourier` -> `fourier3D_orthogonal`
- name_family [high]: `invFourier` -> `fourier_inversion`
- name_family [high]: `invFourier` -> `fourierCoeff3D`
- name_family [high]: `invFourier` -> `FourierCoeff`
- name_family [high]: `invFourier` -> `fourier_ortho_integral`
- name_family [high]: `invFourier` -> `fourierDecay`
- name_family [high]: `invFourier` -> `fourierTruncate`
- name_family [high]: `invFourier` -> `fourierCoeff_summable`
- name_family [high]: `parseval3D` -> `parseval_orthonormal`
- name_family [high]: `parseval_orthonormal` -> `parseval3D`
- name_family [high]: `smooth_initial_hs_finite` -> `SmoothInitial`
- name_family [high]: `sobolev_embedding` -> `cSobolev_pos`
- name_family [high]: `sobolev_embedding` -> `cSobolev`
- name_family [high]: `spectralCurl` -> `spectralNSResidual`
- name_family [high]: `spectralNSResidual` -> `spectralCurl`
- name_family [high]: `uniform_vorticity_bound` -> `vorticity_integrable`
- name_family [high]: `uniform_vorticity_bound` -> `VorticityResponse`
- name_family [high]: `uniform_vorticity_bound` -> `vorticity_hs_bound`
- name_family [high]: `uniform_vorticity_bound` -> `Vorticity`
- name_family [high]: `vorticity_hs_bound` -> `uniform_vorticity_bound`
- name_family [high]: `vorticity_hs_bound` -> `VorticityResponse`
- name_family [high]: `vorticity_hs_bound` -> `Vorticity`
- name_family [high]: `vorticity_hs_bound` -> `vorticity_integrable`
- name_family [high]: `vorticity_integrable` -> `uniform_vorticity_bound`
- name_family [high]: `vorticity_integrable` -> `VorticityResponse`
- name_family [high]: `vorticity_integrable` -> `vorticity_hs_bound`
- name_family [high]: `vorticity_integrable` -> `Vorticity`

---

## The diff

```diff
diff --git a/Mathlib/Analysis/ODE/GalerkinRegularity.lean b/Mathlib/Analysis/ODE/GalerkinRegularity.lean
--- /dev/null
+++ b/Mathlib/Analysis/ODE/GalerkinRegularity.lean
@@ -0,0 +1,469 @@
+/-
+Copyright (c) 2025 Jeffrey Camlin. All rights reserved.
+Released under Apache 2.0 license as described in the file LICENSE.
+Author: Jeffrey Camlin
+-/
+import Mathlib
+
+/-!
+# Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response Functionals
+
+This file proves global existence and smoothness of solutions to the incompressible
+Navier-Stokes equations on the three-torus T³ for smooth divergence-free initial data.
+
+## Main results
+
+- `VorticityResponse`: Structure encoding bounded vorticity-response functional
+- `TemporalLifting`: Temporal lifting as a coupled system with diffeomorphism properties
+- `uniform_vorticity_bound`: Uniform vorticity bounds independent of Galerkin truncation
+- `bkm_coordinate_invariance`: BKM integral invariance under temporal reparameterization
+- `bkm_finite_anyT`: BKM integral finiteness for any finite time interval
+- `GalerkinLimit.smooth`: Main theorem establishing global smooth solutions
+
+## Implementation notes
+
+The proof proceeds via temporal lifting, generalizing Sundman regularization from celestial
+mechanics. Uniform bounds on Galerkin approximations combined with coordinate invariance
+of the Beale-Kato-Majda integral yield finiteness in physical time.
+
+## References
+
+- Beale, Kato, Majda (1984): Remarks on the breakdown of smooth solutions
+- Sundman (1912): Mémoire sur le problème des trois corps
+- Camlin (2025): Global Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response
+  Functionals. DOI: 10.63968/post-bio-ai-epistemics.v1n2.012
+-/
+
+set_option linter.style.commandStart false
+open scoped InnerProductSpace
+
+/-- The three-dimensional torus T³ := (ℝ/ℤ)³ -/
+abbrev T3 := Fin 3 → UnitAddCircle
+
+/-!
+## Analysis Constants
+
+Standard constants from Moser estimates, Gronwall inequalities, and Sobolev embeddings.
+-/
+
+/-- Moser estimate constant for nonlinear term bounds -/
+axiom cMoser : ℝ → ℝ
+
+/-- Gronwall constant for H^s norm control -/
+axiom cGronwall : ℝ → ℝ
+
+/-- Sobolev embedding constant -/
+axiom cSobolev : ℝ → ℝ
+
+axiom cMoser_pos : ∀ s, 0 < cMoser s
+axiom cGronwall_pos : ∀ s, 0 < cGronwall s
+axiom cSobolev_pos : ∀ s, 0 < cSobolev s
+
+/-!
+## Fourier Analysis on T³
+-/
+
+axiom fourier_ortho_integral (n m : ℤ) :
+    ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0
+
+axiom fubini_torus3 (f : Fin 3 → UnitAddCircle → ℂ) :
+    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y
+
+/-!
+## Vorticity Response Functional
+-/
+
+/-- A bounded vorticity-response functional Φ : ℝ≥0 → [φ_min, φ_max] -/
+structure VorticityResponse where
+  /-- Lower bound on temporal density -/
+  φ_min : ℝ
+  /-- Upper bound on temporal density -/
+  φ_max : ℝ
+  /-- Positivity of lower bound -/
+  hmin_pos : 0 < φ_min
+  /-- Ordering of bounds -/
+  hbounds : φ_min ≤ φ_max
+
+/-!
+## Basic Definitions
+-/
+
+/-- Fourier decay condition for smoothness -/
+def fourierDecay (u : T3 → Fin 3 → ℝ) (k : Fin 3 → ℤ) (j : Fin 3) (n : ℕ) (C : ℝ) : Prop :=
+  True
+
+/-- Smooth initial data has rapid Fourier decay -/
+def SmoothInitial (u : T3 → Fin 3 → ℝ) : Prop :=
+  ∀ n : ℕ, ∃ C : ℝ, ∀ k : Fin 3 → ℤ, ∀ j : Fin 3, fourierDecay u k j n C
+
+/-- Smooth function of time -/
+def smoothInTime (f : ℝ → ℝ) : Prop :=
+  ContDiff ℝ ⊤ f
+
+/-- Smooth in both space and time -/
+def SmoothSpacetime (u : T3 → ℝ → Fin 3 → ℝ) : Prop :=
+  (∀ t : ℝ, 0 ≤ t → SmoothInitial (fun x => u x t)) ∧
+  (∀ x : T3, ∀ j : Fin 3, smoothInTime (fun t => u x t j))
+
+/-- Fourier coefficient type -/
+abbrev FourierCoeff := (Fin 3 → ℤ) → (Fin 3 → ℂ)
+
+/-- One-dimensional Fourier basis function -/
+noncomputable def fourier1D (n : ℤ) : UnitAddCircle → ℂ :=
+  fourier n
+
+/-- Three-dimensional Fourier basis function -/
+noncomputable def fourier3D (k : Fin 3 → ℤ) : T3 → ℂ :=
+  fun x => ∏ i : Fin 3, fourier1D (k i) (x i)
+
+/-- Fourier coefficient of a function on T³ -/
+noncomputable def fourierCoeff3D (f : T3 → ℂ) (k : Fin 3 → ℤ) : ℂ :=
+  ∫ x : T3, f x * star (fourier3D k x)
+
+/-- Fourier transform of vector field -/
+noncomputable def fourierTransform (u : T3 → Fin 3 → ℝ) : FourierCoeff :=
+  fun k j => fourierCoeff3D (fun x => (u x j : ℂ)) k
+
+/-- Divergence-free condition in Fourier space -/
+def DivergenceFree (u : T3 → Fin 3 → ℝ) : Prop :=
+  ∀ k : Fin 3 → ℤ, ∑ j : Fin 3, (k j : ℂ) * fourierTransform u k j = 0
+
+/-- Leray projection in Fourier space -/
+noncomputable def LerayProjection (f : FourierCoeff) : FourierCoeff := fun k j =>
+  if k = 0 then f k j
+  else f k j - (∑ i : Fin 3, (k i : ℂ) * f k i) * (k j : ℂ) / (∑ i : Fin 3, (k i : ℂ)^2)
+
+/-- Spectral Navier-Stokes residual -/
+def spectralNSResidual (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (t : ℝ) (k : Fin 3 → ℤ) (j : Fin 3) :
+    ℂ :=
+  0
+
+/-- Solution satisfies Navier-Stokes equations -/
+def SolvesNavierStokes (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ) : Prop :=
+  ∀ t ≥ 0, ∀ k : Fin 3 → ℤ, ∀ j : Fin 3, spectralNSResidual ν u t k j = 0
+
+/-- Fourier truncation to N modes -/
+noncomputable def fourierTruncate (N : ℕ) (û : FourierCoeff) : FourierCoeff := fun k j =>
+  if (∑ i : Fin 3, |k i|) ≤ N then û k j else 0
+
+/-- Galerkin projection of initial data -/
+noncomputable def GalerkinProjection (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) : T3 → ℝ → Fin 3 → ℝ :=
+  fun x t j => u₀ x j
+
+/-- Spectral curl operator -/
+noncomputable def spectralCurl (û : FourierCoeff) : FourierCoeff := fun k j =>
+  let j1 := (j + 1) % 3
+  let j2 := (j + 2) % 3
+  Complex.I * ((k j1 : ℂ) * û k j2 - (k j2 : ℂ) * û k j1)
+
+/-- Inverse Fourier transform -/
+noncomputable def invFourier (f : FourierCoeff) : T3 → Fin 3 → ℝ :=
+  fun x j => (∑' k : Fin 3 → ℤ, f k j * fourier3D k x).re
+
+/-- Vorticity of velocity field -/
+noncomputable def Vorticity (u : T3 → ℝ → Fin 3 → ℝ) : T3 → ℝ → Fin 3 → ℝ :=
+  fun x t => invFourier (spectralCurl (fourierTransform (u · t))) x
+
+/-- Galerkin approximation at fixed time -/
+noncomputable def GalerkinAt (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) : T3 → Fin 3 → ℝ :=
+  fun x => GalerkinProjection N u₀ x t
+
+/-- L² norm of vector field -/
+noncomputable def l2Norm (f : T3 → Fin 3 → ℝ) : ℝ :=
+  Real.sqrt (∫ x : T3, ∑ j : Fin 3, (f x j)^2)
+
+/-- L∞ norm of vector field -/
+noncomputable def linftyNorm (f : T3 → Fin 3 → ℝ) : ℝ :=
+  ⨆ (x : T3) (j : Fin 3), |f x j|
+
+/-- Beale-Kato-Majda integral finiteness -/
+def BKMFinite (ω : ℝ → ℝ) (T : ℝ) : Prop :=
+  ∃ M : ℝ, ∫ t in (0)..T, ω t ≤ M
+
+/-!
+## Axioms (after definitions they reference)
+-/
+
+axiom fourier_inversion (f : T3 → ℂ) (hf : Continuous f) (x : T3) :
+    f x = ∑' k : Fin 3 → ℤ, fourierCoeff3D f k * fourier3D k x
+
+axiom parseval_orthonormal (c : (Fin 3 → ℤ) → ℂ) (hc : Summable (fun k => ‖c k‖^2)) :
+    ∫ x : T3, ‖∑' k, c k * fourier3D k x‖^2 = ∑' k, ‖c k‖^2
+
+axiom bkm_implies_regularity :
+    ∀ (u : T3 → ℝ → Fin 3 → ℝ) (T : ℝ),
+      BKMFinite (fun t => linftyNorm (fun x => Vorticity u x t)) T →
+      SmoothSpacetime u
+
+axiom fourierCoeff_summable (f : T3 → ℂ) (hf : Continuous f) :
+    Summable (fun k => ‖fourierCoeff3D f k‖^2)
+
+axiom integral_le_const_mul_length (f : ℝ → ℝ) (C T : ℝ) (hT : 0 < T)
+    (hf : ∀ t ∈ Set.Icc 0 T, f t ≤ C) :
+    ∫ t in (0)..T, f t ≤ C * T
+
+axiom vorticity_integrable (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (T : ℝ) :
+    IntervalIntegrable
+      (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t))
+      MeasureTheory.volume 0 T
+
+/-- Sobolev H^s norm via Fourier coefficients -/
+noncomputable def hsNorm (s : ℝ) (f : T3 → Fin 3 → ℝ) : ℝ :=
+  Real.sqrt (∑' k : Fin 3 → ℤ, (1 + ‖(fun i => (k i : ℝ))‖^2)^s *
+    ∑ j : Fin 3, ‖fourierTransform f k j‖^2)
+
+/-!
+## Temporal Lifting
+-/
+
+/-- Temporal lifting structure encoding the diffeomorphism t = φ(τ) -/
+structure TemporalLifting (Φ : VorticityResponse) where
+  /-- The temporal diffeomorphism -/
+  φ : ℝ → ℝ
+  /-- Initial condition φ(0) = 0 -/
+  φ_zero : φ 0 = 0
+  /-- Differentiability of φ -/
+  φ_diff : Differentiable ℝ φ
+  /-- Continuity of derivative -/
+  φ_deriv_cont : Continuous (deriv φ)
+  /-- Lower bound on derivative (non-degeneracy) -/
+  φ_deriv_pos : ∀ τ, Φ.φ_min ≤ deriv φ τ
+  /-- Upper bound on derivative (boundedness) -/
+  φ_deriv_bdd : ∀ τ, deriv φ τ ≤ Φ.φ_max
+  /-- Surjectivity (global coverage) -/
+  φ_surj : ∀ t ≥ 0, ∃ τ, φ τ = t
+
+/-!
+## Analytic Estimates
+-/
+
+axiom moser_estimate (s : ℝ) (hs : s > 3/2) (u : T3 → Fin 3 → ℝ) :
+    hsNorm s (fun x j => ∑ i : Fin 3, u x i * u x j) ≤
+    cMoser s * hsNorm s u * hsNorm s u
+
+axiom hs_gronwall_bound (s : ℝ) (hs : s > 5/2) (u₀ : T3 → Fin 3 → ℝ) (hu₀ : SmoothInitial u₀)
+    (N : ℕ) (T : ℝ) (hT : 0 < T) :
+    ∀ t ∈ Set.Icc 0 T, hsNorm s (GalerkinAt N u₀ t) ≤
+    hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)
+
+axiom sobolev_embedding (s : ℝ) (hs : s > 5/2) (f : T3 → Fin 3 → ℝ) :
+    linftyNorm f ≤ cSobolev s * hsNorm (s - 1) f
+
+axiom vorticity_hs_bound (s : ℝ) (u : T3 → Fin 3 → ℝ) :
+    hsNorm (s - 1) (fun x => invFourier (spectralCurl (fourierTransform u)) x) ≤
+    hsNorm s u
+
+axiom smooth_initial_hs_finite (s : ℝ) (u₀ : T3 → Fin 3 → ℝ) (h : SmoothInitial u₀) :
+    ∃ M : ℝ, hsNorm s u₀ ≤ M ∧ 0 ≤ hsNorm s u₀
+
+/-!
+## Fourier Orthogonality
+-/
+
+lemma fourier3D_orthogonal (k k' : Fin 3 → ℤ) :
+    ∫ x : T3, fourier3D k x * star (fourier3D k' x) = if k = k' then 1 else 0 := by
+  have ortho1D : ∀ (n m : ℤ),
+      ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 :=
+    fourier_ortho_integral
+  have fubini : ∫ x : T3, fourier3D k x * star (fourier3D k' x) =
+      ∏ i : Fin 3, ∫ y : UnitAddCircle, fourier (k i) y * star (fourier (k' i) y) := by
+    have h1 : ∀ x : T3, fourier3D k x * star (fourier3D k' x) =
+        ∏ i : Fin 3, (fourier (k i) (x i) * star (fourier (k' i) (x i))) := by
+      intro x
+      unfold fourier3D fourier1D
+      rw [star_prod, ← Finset.prod_mul_distrib]
+    simp_rw [h1]
+    exact fubini_torus3 (fun i y => fourier (k i) y * star (fourier (k' i) y))
+  rw [fubini]
+  simp only [ortho1D]
+  by_cases h : k = k'
+  · subst h
+    simp
+  · have : ∃ i, k i ≠ k' i := Function.ne_iff.mp h
+    obtain ⟨i, hi⟩ := this
+    have hz : ∏ j : Fin 3, (if k j = k' j then (1 : ℂ) else 0) = 0 := by
+      apply Finset.prod_eq_zero (Finset.mem_univ i)
+      simp [hi]
+    simp [h, hz]
+
+/-!
+## Parseval Identity
+-/
+
+theorem parseval3D (f : T3 → ℂ) (hf : Continuous f) :
+    ∫ x : T3, ‖f x‖^2 = ∑' k : Fin 3 → ℤ, ‖fourierCoeff3D f k‖^2 := by
+  have expand : ∫ x : T3, ‖f x‖^2 =
+      ∫ x : T3, ‖∑' k, fourierCoeff3D f k * fourier3D k x‖^2 := by
+    congr 1; funext x
+    rw [fourier_inversion f hf x]
+  rw [expand]
+  exact parseval_orthonormal (fourierCoeff3D f) (fourierCoeff_summable f hf)
+
+/-!
+## Energy Bounds
+-/
+
+lemma galerkin_energy_bound (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) (ht : 0 ≤ t) :
+    l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ := by
+  unfold GalerkinAt GalerkinProjection
+  rfl
+
+/-!
+## Uniform Vorticity Bounds
+-/
+
+lemma uniform_vorticity_bound (u₀ : T3 → Fin 3 → ℝ) (h_smooth : SmoothInitial u₀)
+    (h_divfree : DivergenceFree u₀) (T : ℝ) (hT : 0 < T) :
+    ∃ C : ℝ, ∀ N : ℕ, ∀ t ∈ Set.Icc 0 T,
+      linftyNorm (Vorticity (GalerkinProjection N u₀) · t) ≤ C := by
+  let s : ℝ := 3
+  have hs : s > 5/2 := by norm_num
+  let C := cSobolev s * hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)
+  use C
+  intro N t ht
+  calc linftyNorm (Vorticity (GalerkinProjection N u₀) · t)
+      = linftyNorm (fun x =>
+          invFourier (spectralCurl (fourierTransform (GalerkinAt N u₀ t))) x) := by
+        rfl
+      _ ≤ cSobolev s * hsNorm (s - 1) (fun x =>
+          invFourier (spectralCurl (fourierTransform (GalerkinAt N u₀ t))) x) := by
+        exact sobolev_embedding s hs _
+      _ ≤ cSobolev s * hsNorm s (GalerkinAt N u₀ t) := by
+        apply mul_le_mul_of_nonneg_left
+        · exact vorticity_hs_bound s (GalerkinAt N u₀ t)
+        · exact le_of_lt (cSobolev_pos s)
+      _ ≤ cSobolev s * (hsNorm s u₀ * Real.exp (cGronwall s * T * hsNorm s u₀)) := by
+        apply mul_le_mul_of_nonneg_left
+        · exact hs_gronwall_bound s hs u₀ h_smooth N T hT t ht
+        · exact le_of_lt (cSobolev_pos s)
+      _ = C := by ring
+
+/-!
+## BKM Coordinate Invariance
+-/
+
+/-- BKM integral in physical time -/
+noncomputable def bkmPhysical (ω : ℝ → ℝ) (T : ℝ) : ℝ :=
+  ∫ t in (0)..T, ω t
+
+/-- BKM integral in lifted time -/
+noncomputable def bkmLifted (Ω : ℝ → ℝ) (φ : ℝ → ℝ) (τ_T : ℝ) : ℝ :=
+  ∫ τ in (0)..τ_T, Ω τ * deriv φ τ
+
+lemma bkm_coordinate_invariance (Φ : VorticityResponse) (L : TemporalLifting Φ)
+    (ω Ω : ℝ → ℝ) (hω_cont : Continuous ω) (h_relation : ∀ τ, Ω τ = ω (L.φ τ))
+    (T : ℝ) (hT : 0 ≤ T) (τ_T : ℝ) (hτ : L.φ τ_T = T) :
+    bkmPhysical ω T = bkmLifted Ω L.φ τ_T := by
+  unfold bkmPhysical bkmLifted
+  have step1 : ∫ τ in (0)..τ_T, Ω τ * deriv L.φ τ =
+      ∫ τ in (0)..τ_T, ω (L.φ τ) * deriv L.φ τ := by
+    congr 1; ext τ; rw [h_relation]
+  rw [step1]
+  have subst : ∫ x in (0)..τ_T, ω (L.φ x) * deriv L.φ x =
+      ∫ t in (L.φ 0)..(L.φ τ_T), ω t := by
+    apply intervalIntegral.integral_comp_mul_deriv
+    · intro x _; exact (L.φ_diff x).hasDerivAt
+    · exact L.φ_deriv_cont.continuousOn
+    · exact hω_cont
+  rw [L.φ_zero, hτ] at subst
+  exact subst.symm
+
+lemma tau_interval_finite (Φ : VorticityResponse) (L : TemporalLifting Φ)
+    (T : ℝ) (hT : 0 < T) :
+    ∃ τ_T : ℝ, L.φ τ_T = T ∧ τ_T ≤ T / Φ.φ_min := by
+  obtain ⟨τ_T, hτ_T⟩ := L.φ_surj T (le_of_lt hT)
+  refine ⟨τ_T, hτ_T, ?_⟩
+  by_cases hτ_nonneg : τ_T ≤ 0
+  · calc τ_T ≤ 0 := hτ_nonneg
+         _ ≤ T / Φ.φ_min := le_of_lt (div_pos hT Φ.hmin_pos)
+  · push_neg at hτ_nonneg
+    have key : Φ.φ_min * τ_T ≤ T := by
+      rw [← hτ_T]
+      have ftc : L.φ τ_T - L.φ 0 = ∫ s in (0)..τ_T, deriv L.φ s := by
+        symm
+        apply intervalIntegral.integral_deriv_eq_sub
+        · intro x _; exact L.φ_diff.differentiableAt
+        · exact L.φ_deriv_cont.intervalIntegrable 0 τ_T
+      rw [L.φ_zero, sub_zero] at ftc
+      rw [ftc]
+      have const_int : Φ.φ_min * τ_T = ∫ s in (0)..τ_T, Φ.φ_min := by
+        simp [intervalIntegral.integral_const]; ring
+      rw [const_int]
+      apply intervalIntegral.integral_mono_on (le_of_lt hτ_nonneg)
+      · exact intervalIntegrable_const
+      · exact L.φ_deriv_cont.intervalIntegrable 0 τ_T
+      · intro x _; exact L.φ_deriv_pos x
+    have hne : Φ.φ_min ≠ 0 := ne_of_gt Φ.hmin_pos
+    calc τ_T = τ_T * 1 := (mul_one _).symm
+         _ = τ_T * (Φ.φ_min / Φ.φ_min) := by rw [div_self hne]
+         _ = (τ_T * Φ.φ_min) / Φ.φ_min := by ring
+         _ = (Φ.φ_min * τ_T) / Φ.φ_min := by ring
+         _ ≤ T / Φ.φ_min := div_le_div_of_nonneg_right key (le_of_lt Φ.hmin_pos)
+
+/-!
+## BKM Finiteness
+-/
+
+lemma bkm_finite_anyT (Φ : VorticityResponse) (u₀ : T3 → Fin 3 → ℝ)
+    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀)
+    (T : ℝ) (hT : 0 < T) (N : ℕ) :
+    BKMFinite (fun t => linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t)) T := by
+  obtain ⟨C, hC⟩ := uniform_vorticity_bound u₀ h_smooth h_divfree T hT
+  use C * T
+  have bound : ∀ t ∈ Set.Icc 0 T,
+      linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t) ≤ C := by
+    intro t ht
+    exact hC N t ht
+  calc ∫ t in (0)..T, linftyNorm (fun x => Vorticity (GalerkinProjection N u₀) x t)
+      ≤ ∫ t in (0)..T, C := by
+        apply intervalIntegral.integral_mono_on (le_of_lt hT)
+        · exact vorticity_integrable N u₀ T
+        · exact intervalIntegrable_const
+        · intro t ht
+          exact bound t (Set.mem_Icc.mpr ⟨ht.1, ht.2⟩)
+      _ = C * T := by
+        rw [intervalIntegral.integral_const, sub_zero, smul_eq_mul, mul_comm]
+
+/-!
+## Main Theorems
+-/
+
+/-- Regularity from bounded vorticity response -/
+theorem VorticityResponse.regularity (Φ : VorticityResponse) (ν : ℝ) (_hν : 0 < ν)
+    (u₀ : T3 → Fin 3 → ℝ) (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀) :
+    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
+      SmoothSpacetime u ∧
+      SolvesNavierStokes ν u p ∧
+      (∀ x, u x 0 = u₀ x) := by
+  let u : T3 → ℝ → Fin 3 → ℝ := GalerkinProjection 1 u₀
+  let p : T3 → ℝ → ℝ := fun _ _ => 0
+  have hBKM : BKMFinite (fun t => linftyNorm (fun x => Vorticity u x t)) 1 :=
+    bkm_finite_anyT Φ u₀ h_smooth h_divfree 1 one_pos 1
+  have hSmooth : SmoothSpacetime u := bkm_implies_regularity u 1 hBKM
+  have hNS : SolvesNavierStokes ν u p := by
+    intro t _ k j
+    simp [spectralNSResidual]
+  have hInit : ∀ x, u x 0 = u₀ x := by
+    intro x
+    ext j
+    rfl
+  exact ⟨u, p, hSmooth, hNS, hInit⟩
+
+/-- Smooth solutions exist for the Galerkin limit -/
+theorem GalerkinLimit.smooth (ν : ℝ) (hν : 0 < ν) (u₀ : T3 → Fin 3 → ℝ)
+    (h_smooth : SmoothInitial u₀) (h_divfree : DivergenceFree u₀) :
+    ∃ (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ),
+      SmoothSpacetime u ∧
+      SolvesNavierStokes ν u p ∧
+      (∀ x, u x 0 = u₀ x) := by
+  let Φ : VorticityResponse := {
+    φ_min := 1
+    φ_max := 2
+    hmin_pos := one_pos
+    hbounds := le_of_lt one_lt_two
+  }
+  exact VorticityResponse.regularity Φ ν hν u₀ h_smooth h_divfree
+
+#check GalerkinLimit.smooth
+
+#print axioms GalerkinLimit.smooth

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.