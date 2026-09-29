/-
Copyright (c) 2022 Kexing Ying. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Kexing Ying
-/
import Mathlib.MeasureTheory.Constructions.Polish.Basic
import Mathlib.MeasureTheory.Function.UniformIntegrable
import Mathlib.Probability.Martingale.Upcrossing

/-!

# Martingale convergence theorems

The martingale convergence theorems are a collection of theorems characterizing the convergence
of a martingale provided it satisfies some boundedness conditions. This file contains the
almost everywhere martingale convergence theorem which provides an almost everywhere limit to
an L¹ bounded submartingale. It also contains the L¹ martingale convergence theorem which provides
an L¹ limit to a uniformly integrable submartingale. Finally, it also contains the Lévy upwards
theorems.

## Main results

* `MeasureTheory.Submartingale.ae_tendsto_limitProcess`: the almost everywhere martingale
  convergence theorem: an L¹-bounded submartingale adapted to the filtration `ℱ` converges almost
  everywhere to its limit process.
* `MeasureTheory.Submartingale.memLp_limitProcess`: the limit process of an Lᵖ-bounded
  submartingale is Lᵖ.
* `MeasureTheory.Submartingale.tendsto_eLpNorm_one_limitProcess`: part a of the L¹ martingale
  convergence theorem: a uniformly integrable submartingale adapted to the filtration `ℱ` converges
  almost everywhere and in L¹ to an integrable function which is measurable with respect to
  the σ-algebra `⨆ n, ℱ n`.
* `MeasureTheory.Martingale.ae_eq_condExp_limitProcess`: part b the L¹ martingale convergence
  theorem: if `f` is a uniformly integrable martingale adapted to the filtration `ℱ`, then
  `f n` equals `𝔼[g | ℱ n]` almost everywhere where `g` is the limiting process of `f`.
* `MeasureTheory.Integrable.tendsto_ae_condExp`: part c the L¹ martingale convergence theorem:
  given a `⨆ n, ℱ n`-measurable function `g` where `ℱ` is a filtration, `𝔼[g | ℱ n]` converges
  almost everywhere to `g`.
* `MeasureTheory.Integrable.tendsto_eLpNorm_condExp`: part c the L¹ martingale convergence theorem:
  given a `⨆ n, ℱ n`-measurable function `g` where `ℱ` is a filtration, `𝔼[g | ℱ n]` converges in
  L¹ to `g`.

-/


open TopologicalSpace Filter MeasureTheory.Filtration

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology

namespace MeasureTheory

variable {Ω : Type*} {m0 : MeasurableSpace Ω} {μ : Measure Ω} {ℱ : Filtration ℕ m0}
variable {a b : ℝ} {f : ℕ → Ω → ℝ} {ω : Ω} {R : ℝ≥0}

section AeConvergence

/-!

### Almost everywhere martingale convergence theorem

We will now prove the almost everywhere martingale convergence theorem.

The a.e. martingale convergence theorem states: if `f` is an L¹-bounded `ℱ`-submartingale, then
it converges almost everywhere to an integrable function which is measurable with respect to
the σ-algebra `ℱ∞ := ⨆ n, ℱ n`.

Mathematically, we proceed by first noting that a real sequence $(x_n)$ converges if
(a) $\limsup_{n \to \infty} |x_n| < \infty$, (b) for all $a < b \in \mathbb{Q}$ we have the
number of upcrossings of $(x_n)$ from below $a$ to above $b$ is finite.
Thus, for all $\omega$ satisfying $\limsup_{n \to \infty} |f_n(\omega)| < \infty$ and the number of
upcrossings of $(f_n(\omega))$ from below $a$ to above $b$ is finite for all $a < b \in \mathbb{Q}$,
we have $(f_n(\omega))$ is convergent.

Hence, assuming $(f_n)$ is L¹-bounded, using Fatou's lemma, we have
$$
  \mathbb{E} \limsup_{n \to \infty} |f_n| \le \limsup_{n \to \infty} \mathbb{E}|f_n| < \infty
$$
implying $\limsup_{n \to \infty} |f_n| < \infty$ a.e. Furthermore, by the upcrossing estimate,
the number of upcrossings is finite almost everywhere implying $f$ converges pointwise almost
everywhere.

Thus, denoting $g$ the a.e. limit of $(f_n)$, $g$ is $\mathcal{F}_\infty$-measurable as for all
$n$, $f_n$ is $\mathcal{F}_n$-measurable and $\mathcal{F}_n \le \mathcal{F}_\infty$. Finally, $g$
is integrable as $|g| \le \liminf_{n \to \infty} |f_n|$ so
$$
  \mathbb{E}|g| \le \mathbb{E} \limsup_{n \to \infty} |f_n| \le
    \limsup_{n \to \infty} \mathbb{E}|f_n| < \infty
$$
as required.

In terms of implementation, we have `tendsto_of_no_upcrossings` which shows that
a bounded sequence converges if it does not visit below $a$ and above $b$ infinitely often
for all $a, b ∈ s$ for some dense set $s$. So, we may skip the first step provided we can prove
that the realizations are bounded almost everywhere. Indeed, suppose $|f_n(\omega)|$ is not
bounded, then either $f_n(\omega) \to \pm \infty$ or one of $\limsup f_n(\omega)$ or
$\liminf f_n(\omega)$ equals $\pm \infty$ while the other is finite. But the first case
contradicts $\liminf |f_n(\omega)| < \infty$ while the second case contradicts finite upcrossings.

Furthermore, we introduce `Filtration.limitProcess` which chooses the limiting random variable
of a stochastic process if it exists, otherwise returning 0. Hence, instead of showing an
existence statement, we phrase the a.e. martingale convergence theorem by showing that a
submartingale converges to its `limitProcess` almost everywhere.

-/


/-- If a stochastic process has bounded upcrossing from below `a` to above `b`,
then it does not frequently visit both below `a` and above `b`. -/
theorem not_frequently_of_upcrossings_lt_top (hab : a < b) (hω : upcrossings a b f ω ≠ ∞) :
    ¬((∃ᶠ n in atTop, f n ω < a) ∧ ∃ᶠ n in atTop, b < f n ω) := by
  rw [← lt_top_iff_ne_top, upcrossings_lt_top_iff] at hω
  replace hω : ∃ k, ∀ N, upcrossingsBefore a b f N ω < k := by
    obtain ⟨k, hk⟩ := hω
    exact ⟨k + 1, fun N => lt_of_le_of_lt (hk N) k.lt_succ_self⟩
  rintro ⟨h₁, h₂⟩
  rw [frequently_atTop] at h₁ h₂
  refine Classical.not_not.2 hω ?_
  push_neg
  intro k
  induction k with
  | zero => simp only [zero_le, exists_const]
  | succ k ih =>
    obtain ⟨N, hN⟩ := ih
    obtain ⟨N₁, hN₁, hN₁'⟩ := h₁ N
    obtain ⟨N₂, hN₂, hN₂'⟩ := h₂ N₁
    exact ⟨N₂ + 1, Nat.succ_le_of_lt <|
      lt_of_le_of_lt hN (upcrossingsBefore_lt_of_exists_upcrossing hab hN₁ hN₁' hN₂ hN₂')⟩

/-- A stochastic process that frequently visits below `a` and above `b` has infinite upcrossings. -/
theorem upcrossings_eq_top_of_frequently_lt (hab : a < b) (h₁ : ∃ᶠ n in atTop, f n ω < a)
    (h₂ : ∃ᶠ n in atTop, b < f n ω) : upcrossings a b f ω = ∞ :=
  by_contradiction fun h => not_frequently_of_upcrossings_lt_top hab h ⟨h₁, h₂⟩

/-- A realization of a stochastic process with bounded upcrossings and bounded limit inferiors is
convergent.

We use the spelling `< ∞` instead of the standard `≠ ∞` in the assumptions since it is not as easy
to change `<` to `≠` under binders. -/
theorem tendsto_of_uncrossing_lt_top (hf₁ : liminf (fun n => (‖f n ω‖₊ : ℝ≥0∞)) atTop < ∞)
    (hf₂ : ∀ a b : ℚ, a < b → upcrossings a b f ω < ∞) :
