/-
Copyright (c) 2022 Rémy Degenne. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Rémy Degenne
-/
import Mathlib.Probability.IdentDistrib

/-!
# Moments and moment generating function

## Main definitions

* `ProbabilityTheory.moment X p μ`: `p`th moment of a real random variable `X` with respect to
  measure `μ`, `μ[X^p]`
* `ProbabilityTheory.centralMoment X p μ`:`p`th central moment of `X` with respect to measure `μ`,
  `μ[(X - μ[X])^p]`
* `ProbabilityTheory.mgf X μ t`: moment generating function of `X` with respect to measure `μ`,
  `μ[exp(t*X)]`
* `ProbabilityTheory.cgf X μ t`: cumulant generating function, logarithm of the moment generating
  function

## Main results

* `ProbabilityTheory.IndepFun.mgf_add`: if two real random variables `X` and `Y` are independent
  and their MGFs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
* `ProbabilityTheory.IndepFun.cgf_add`: if two real random variables `X` and `Y` are independent
  and their CGFs are defined at `t`, then `cgf (X + Y) μ t = cgf X μ t + cgf Y μ t`
* `ProbabilityTheory.measure_ge_le_exp_cgf` and `ProbabilityTheory.measure_le_le_exp_cgf`:
  Chernoff bound on the upper (resp. lower) tail of a random variable. For `t` nonnegative such that
  the cgf exists, `ℙ(ε ≤ X) ≤ exp(- t*ε + cgf X ℙ t)`. See also
  `ProbabilityTheory.measure_ge_le_exp_mul_mgf` and
  `ProbabilityTheory.measure_le_le_exp_mul_mgf` for versions of these results using `mgf` instead
  of `cgf`.
-/


open MeasureTheory Filter Finset Real

noncomputable section

open scoped MeasureTheory ProbabilityTheory ENNReal NNReal

namespace ProbabilityTheory

variable {Ω ι : Type*} {m : MeasurableSpace Ω} {X : Ω → ℝ} {p : ℕ} {μ : Measure Ω}

/-- Moment of a real random variable, `μ[X ^ p]`. -/
def moment (X : Ω → ℝ) (p : ℕ) (μ : Measure Ω) : ℝ :=
  μ[X ^ p]

/-- Central moment of a real random variable, `μ[(X - μ[X]) ^ p]`. -/
def centralMoment (X : Ω → ℝ) (p : ℕ) (μ : Measure Ω) : ℝ := by
  have m := fun (x : Ω) => μ[X] -- Porting note: Lean deems `μ[(X - fun x => μ[X]) ^ p]` ambiguous
  exact μ[(X - m) ^ p]

@[simp]
theorem moment_zero (hp : p ≠ 0) : moment 0 p μ = 0 := by
  simp only [moment, hp, zero_pow, Ne, not_false_iff, Pi.zero_apply, integral_const,
    smul_eq_mul, mul_zero]

@[simp]
lemma moment_zero_measure : moment X p (0 : Measure Ω) = 0 := by simp [moment]

@[simp]
theorem centralMoment_zero (hp : p ≠ 0) : centralMoment 0 p μ = 0 := by
  simp only [centralMoment, hp, Pi.zero_apply, integral_const, smul_eq_mul,
    mul_zero, zero_sub, Pi.pow_apply, Pi.neg_apply, neg_zero, zero_pow, Ne, not_false_iff]

@[simp]
lemma centralMoment_zero_measure : centralMoment X p (0 : Measure Ω) = 0 := by
  simp [centralMoment]

theorem centralMoment_one' [IsFiniteMeasure μ] (h_int : Integrable X μ) :
    centralMoment X 1 μ = (1 - μ.real Set.univ) * μ[X] := by
  simp only [centralMoment, Pi.sub_apply, pow_one]
  rw [integral_sub h_int (integrable_const _)]
  simp only [sub_mul, integral_const, smul_eq_mul, one_mul]

@[simp]
theorem centralMoment_one [IsZeroOrProbabilityMeasure μ] : centralMoment X 1 μ = 0 := by
  rcases eq_zero_or_isProbabilityMeasure μ with rfl | h
  · simp [centralMoment]
  by_cases h_int : Integrable X μ
  · rw [centralMoment_one' h_int]
    simp
  · simp only [centralMoment, Pi.sub_apply, pow_one]
    have : ¬Integrable (fun x => X x - integral μ X) μ := by
      refine fun h_sub => h_int ?_
      have h_add : X = (fun x => X x - integral μ X) + fun _ => integral μ X := by ext1 x; simp
      rw [h_add]
      fun_prop
    rw [integral_undef this]

lemma centralMoment_two_eq_variance (hX : AEMeasurable X μ) : centralMoment X 2 μ = variance X μ :=
  (variance_eq_integral hX).symm

section MomentGeneratingFunction

variable {t : ℝ}

/-- Moment generating function of a real random variable `X`: `fun t => μ[exp(t*X)]`. -/
def mgf (X : Ω → ℝ) (μ : Measure Ω) (t : ℝ) : ℝ :=
  μ[fun ω => exp (t * X ω)]

/-- Cumulant generating function of a real random variable `X`: `fun t => log μ[exp(t*X)]`. -/
def cgf (X : Ω → ℝ) (μ : Measure Ω) (t : ℝ) : ℝ :=
  log (mgf X μ t)

@[simp]
theorem mgf_zero_fun : mgf 0 μ t = μ.real Set.univ := by
  simp only [mgf, Pi.zero_apply, mul_zero, exp_zero, integral_const, smul_eq_mul, mul_one]

@[simp]
theorem cgf_zero_fun : cgf 0 μ t = log (μ.real Set.univ) := by simp only [cgf, mgf_zero_fun]

@[simp]
theorem mgf_zero_measure : mgf X (0 : Measure Ω) = 0 := by ext; simp [mgf]

@[simp]
theorem cgf_zero_measure : cgf X (0 : Measure Ω) = 0 := by ext; simp [cgf]

@[simp]
theorem mgf_const' (c : ℝ) : mgf (fun _ => c) μ t = μ.real Set.univ * exp (t * c) := by
  simp only [mgf, integral_const, smul_eq_mul]

theorem mgf_const (c : ℝ) [IsProbabilityMeasure μ] : mgf (fun _ => c) μ t = exp (t * c) := by
  simp

@[simp]
theorem cgf_const' [IsFiniteMeasure μ] (hμ : μ ≠ 0) (c : ℝ) :
    cgf (fun _ => c) μ t = log (μ.real Set.univ) + t * c := by
  simp only [cgf, mgf_const']
  rw [log_mul _ (exp_pos _).ne']
  · rw [log_exp _]
  · rw [Ne, measureReal_eq_zero_iff, Measure.measure_univ_eq_zero]
    simp only [hμ, not_false_iff]

@[simp]
theorem cgf_const [IsProbabilityMeasure μ] (c : ℝ) : cgf (fun _ => c) μ t = t * c := by
