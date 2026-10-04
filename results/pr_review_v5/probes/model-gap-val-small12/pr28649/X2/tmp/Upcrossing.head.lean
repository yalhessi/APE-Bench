/-
Copyright (c) 2022 Kexing Ying. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Kexing Ying
-/
import Mathlib.Order.Interval.Set.Monotone
import Mathlib.Probability.Process.HittingTime
import Mathlib.Probability.Martingale.Basic
import Mathlib.Tactic.AdaptationNote

/-!

# Doob's upcrossing estimate

Given a discrete real-valued submartingale $(f_n)_{n \in \mathbb{N}}$, denoting by $U_N(a, b)$ the
number of times $f_n$ crossed from below $a$ to above $b$ before time $N$, Doob's upcrossing
estimate (also known as Doob's inequality) states that
$$(b - a) \mathbb{E}[U_N(a, b)] \le \mathbb{E}[(f_N - a)^+].$$
Doob's upcrossing estimate is an important inequality and is central in proving the martingale
convergence theorems.

## Main definitions

* `MeasureTheory.upperCrossingTime a b f N n`: is the stopping time corresponding to `f`
  crossing above `b` the `n`-th time before time `N` (if this does not occur then the value is
  taken to be `N`).
* `MeasureTheory.lowerCrossingTime a b f N n`: is the stopping time corresponding to `f`
  crossing below `a` the `n`-th time before time `N` (if this does not occur then the value is
  taken to be `N`).
* `MeasureTheory.upcrossingStrat a b f N`: is the predictable process which is 1 if `n` is
  between a consecutive pair of lower and upper crossings and is 0 otherwise. Intuitively
  one might think of the `upcrossingStrat` as the strategy of buying 1 share whenever the process
  crosses below `a` for the first time after selling and selling 1 share whenever the process
  crosses above `b` for the first time after buying.
* `MeasureTheory.upcrossingsBefore a b f N`: is the number of times `f` crosses from below `a` to
  above `b` before time `N`.
* `MeasureTheory.upcrossings a b f`: is the number of times `f` crosses from below `a` to above
  `b`. This takes value in `ℝ≥0∞` and so is allowed to be `∞`.

## Main results

* `MeasureTheory.Adapted.isStoppingTime_upperCrossingTime`: `upperCrossingTime` is a
  stopping time whenever the process it is associated to is adapted.
* `MeasureTheory.Adapted.isStoppingTime_lowerCrossingTime`: `lowerCrossingTime` is a
  stopping time whenever the process it is associated to is adapted.
* `MeasureTheory.Submartingale.mul_integral_upcrossingsBefore_le_integral_pos_part`: Doob's
  upcrossing estimate.
* `MeasureTheory.Submartingale.mul_lintegral_upcrossings_le_lintegral_pos_part`: the inequality
  obtained by taking the supremum on both sides of Doob's upcrossing estimate.

### References

We mostly follow the proof from [Kallenberg, *Foundations of modern probability*][kallenberg2021]

-/


open TopologicalSpace Filter

open scoped NNReal ENNReal MeasureTheory ProbabilityTheory Topology

namespace MeasureTheory

variable {Ω ι : Type*} {m0 : MeasurableSpace Ω} {μ : Measure Ω}

/-!

## Proof outline

In this section, we will denote by $U_N(a, b)$ the number of upcrossings of $(f_n)$ from below $a$
to above $b$ before time $N$.

To define $U_N(a, b)$, we will construct two stopping times corresponding to when $(f_n)$ crosses
below $a$ and above $b$. Namely, we define
$$
  \sigma_n := \inf \{n \ge \tau_n \mid f_n \le a\} \wedge N;
$$
$$
  \tau_{n + 1} := \inf \{n \ge \sigma_n \mid f_n \ge b\} \wedge N.
$$
These are `lowerCrossingTime` and `upperCrossingTime` in our formalization which are defined
using `MeasureTheory.hitting` allowing us to specify a starting and ending time.
Then, we may simply define $U_N(a, b) := \sup \{n \mid \tau_n < N\}$.

Fixing $a < b \in \mathbb{R}$, we will first prove the theorem in the special case that
$0 \le f_0$ and $a \le f_N$. In particular, we will show
$$
  (b - a) \mathbb{E}[U_N(a, b)] \le \mathbb{E}[f_N].
$$
This is `MeasureTheory.integral_mul_upcrossingsBefore_le_integral` in our formalization.

To prove this, we use the fact that given a non-negative, bounded, predictable process $(C_n)$
(i.e. $(C_{n + 1})$ is adapted), $(C \bullet f)_n := \sum_{k \le n} C_{k + 1}(f_{k + 1} - f_k)$ is
a submartingale if $(f_n)$ is.

Define $C_n := \sum_{k \le n} \mathbf{1}_{[\sigma_k, \tau_{k + 1})}(n)$. It is easy to see that
$(1 - C_n)$ is non-negative, bounded and predictable, and hence, given a submartingale $(f_n)$,
$(1 - C) \bullet f$ is also a submartingale. Thus, by the submartingale property,
$0 \le \mathbb{E}[((1 - C) \bullet f)_0] \le \mathbb{E}[((1 - C) \bullet f)_N]$ implying
$$
  \mathbb{E}[(C \bullet f)_N] \le \mathbb{E}[(1 \bullet f)_N] = \mathbb{E}[f_N] - \mathbb{E}[f_0].
$$

Furthermore,
\begin{align}
    (C \bullet f)_N & =
      \sum_{n \le N} \sum_{k \le N} \mathbf{1}_{[\sigma_k, \tau_{k + 1})}(n)(f_{n + 1} - f_n)\\
    & = \sum_{k \le N} \sum_{n \le N} \mathbf{1}_{[\sigma_k, \tau_{k + 1})}(n)(f_{n + 1} - f_n)\\
    & = \sum_{k \le N} (f_{\sigma_k + 1} - f_{\sigma_k} + f_{\sigma_k + 2} - f_{\sigma_k + 1}
      + \cdots + f_{\tau_{k + 1}} - f_{\tau_{k + 1} - 1})\\
    & = \sum_{k \le N} (f_{\tau_{k + 1}} - f_{\sigma_k})
      \ge \sum_{k < U_N(a, b)} (b - a) = (b - a) U_N(a, b)
\end{align}
where the inequality follows since for all $k < U_N(a, b)$,
$f_{\tau_{k + 1}} - f_{\sigma_k} \ge b - a$ while for all $k > U_N(a, b)$,
$f_{\tau_{k + 1}} = f_{\sigma_k} = f_N$ and
$f_{\tau_{U_N(a, b) + 1}} - f_{\sigma_{U_N(a, b)}} = f_N - a \ge 0$. Hence, we have
$$
  (b - a) \mathbb{E}[U_N(a, b)] \le \mathbb{E}[(C \bullet f)_N]
  \le \mathbb{E}[f_N] - \mathbb{E}[f_0] \le \mathbb{E}[f_N],
$$
as required.

To obtain the general case, we simply apply the above to $((f_n - a)^+)_n$.

-/


/-- `lowerCrossingTimeAux a f c N` is the first time `f` reached below `a` after time `c` before
time `N`. -/
noncomputable def lowerCrossingTimeAux [Preorder ι] [InfSet ι] (a : ℝ) (f : ι → Ω → ℝ) (c N : ι) :
    Ω → ι :=
  hitting f (Set.Iic a) c N

/-- `upperCrossingTime a b f N n` is the first time before time `N`, `f` reaches
above `b` after `f` reached below `a` for the `n - 1`-th time. -/
noncomputable def upperCrossingTime [Preorder ι] [OrderBot ι] [InfSet ι] (a b : ℝ) (f : ι → Ω → ℝ)
    (N : ι) : ℕ → Ω → ι
  | 0 => ⊥
