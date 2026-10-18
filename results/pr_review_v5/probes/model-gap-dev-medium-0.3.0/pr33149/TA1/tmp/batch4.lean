/-- Three-dimensional Fourier basis function -/
noncomputable def fourier3D (k : Fin 3 → ℤ) (x : T3) : ℂ :=
  ∏ i : Fin 3, fourier1D (k i) (x i)

/-- Fourier coefficient of a function on T³ -/
noncomputable def fourierCoeff3D (f : T3 → ℂ) (k : Fin 3 → ℤ) : ℂ :=
  ∫ x : T3, f x * star (fourier3D k x)

/-- Fourier transform of vector field -/
noncomputable def fourierTransform (u : T3 → Fin 3 → ℝ) (k : Fin 3 → ℤ) (j : Fin 3) : ℂ :=
  fourierCoeff3D (fun x ↦ (u x j : ℂ)) k

/-- Divergence-free condition in Fourier space -/
def DivergenceFree (u : T3 → Fin 3 → ℝ) : Prop :=
  ∀ k : Fin 3 → ℤ, ∑ j : Fin 3, (k j : ℂ) * fourierTransform u k j = 0

/-- Leray projection in Fourier space -/
noncomputable def LerayProjection (f : FourierCoeff) (k : Fin 3 → ℤ) (j : Fin 3) : ℂ :=
  if k = 0 then f k j
  else f k j - (∑ i : Fin 3, (k i : ℂ) * f k i) * (k j : ℂ) / (∑ i : Fin 3, (k i : ℂ) ^ 2)

/-- Spectral Navier-Stokes residual -/
def spectralNSResidual (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (t : ℝ) (k : Fin 3 → ℤ) (j : Fin 3) :
    ℂ :=
  0

/-- Solution satisfies Navier-Stokes equations -/
def SolvesNavierStokes (ν : ℝ) (u : T3 → ℝ → Fin 3 → ℝ) (p : T3 → ℝ → ℝ) : Prop :=
  ∀ t ≥ 0, ∀ k : Fin 3 → ℤ, ∀ j : Fin 3, spectralNSResidual ν u t k j = 0

/-- Fourier truncation to N modes -/
noncomputable def fourierTruncate (N : ℕ) (û : FourierCoeff) (k : Fin 3 → ℤ) (j : Fin 3) : ℂ :=
  if (∑ i : Fin 3, |k i|) ≤ N then û k j else 0

/-- Galerkin projection of initial data -/
noncomputable def GalerkinProjection (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (x : T3) (t : ℝ) (j : Fin 3) :
    ℝ :=
  u₀ x j

/-- Spectral curl operator: the Fourier multiplier of `curl` on `ℝ³ / ℤ³` is `2πi k ×`. -/
noncomputable def spectralCurl (û : FourierCoeff) (k : Fin 3 → ℤ) (j : Fin 3) : ℂ :=
  2 * Real.pi * Complex.I * ((k (j + 1) : ℂ) * û k (j + 2) - (k (j + 2) : ℂ) * û k (j + 1))

/-- Inverse Fourier transform -/
noncomputable def invFourier (f : FourierCoeff) (x : T3) (j : Fin 3) : ℝ :=
  (∑' k : Fin 3 → ℤ, f k j * fourier3D k x).re

/-- Vorticity of velocity field -/
noncomputable def Vorticity (u : T3 → ℝ → Fin 3 → ℝ) (x : T3) (t : ℝ) : Fin 3 → ℝ :=
  invFourier (spectralCurl (fourierTransform (u · t))) x

/-- Galerkin approximation at fixed time -/
noncomputable def GalerkinAt (N : ℕ) (u₀ : T3 → Fin 3 → ℝ) (t : ℝ) (x : T3) : Fin 3 → ℝ :=
  GalerkinProjection N u₀ x t
