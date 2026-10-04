# The PR model for #28649 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: doc(Probability): miscellaneous typo fixes
- description: (not recoverable at review start)
- changed files: Mathlib/Probability/Distributions/Gaussian/Real.lean, Mathlib/Probability/Kernel/Composition/CompNotation.lean, Mathlib/Probability/Kernel/Composition/IntegralCompProd.lean, Mathlib/Probability/Martingale/Convergence.lean, Mathlib/Probability/Martingale/Upcrossing.lean, Mathlib/Probability/Moments/Basic.lean, Mathlib/Probability/Moments/Variance.lean

## Objects

### `doc_comment in Real.lean` (command, modified) [116aa158d0]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- The gaussian pdf is nonnegative. -/
```
- as the PR leaves it:
```lean
/-- The Gaussian pdf is nonnegative. -/
```

### `doc_comment in Real.lean` (command, modified) [339b5d03f5]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- The gaussian pdf is positive when the variance is not zero. -/
```
- as the PR leaves it:
```lean
/-- The Gaussian pdf is positive when the variance is not zero. -/
```

### `doc_comment in Real.lean` (command, modified) [ab932f53ef]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- The gaussian pdf is measurable. -/
```
- as the PR leaves it:
```lean
/-- The Gaussian pdf is measurable. -/
```

### `doc_comment in Real.lean` (command, modified) [b698353b96]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- Probability density function of the gaussian distribution with mean `μ` and variance `v`. -/
```
- as the PR leaves it:
```lean
/-- Probability density function of the Gaussian distribution with mean `μ` and variance `v`. -/
```

### `doc_comment in Real.lean` (command, modified) [bca6922f8b]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- The gaussian distribution pdf integrates to 1 when the variance is not zero. -/
```
- as the PR leaves it:
```lean
/-- The Gaussian distribution pdf integrates to 1 when the variance is not zero. -/
```

### `doc_comment in Real.lean` (command, modified) [ec9bcfcbf3]
- file: `Mathlib/Probability/Distributions/Gaussian/Real.lean`; changed: documentation:modified
- before the PR:
```lean
/-- The gaussian pdf is strongly measurable. -/
```
- as the PR leaves it:
```lean
/-- The Gaussian pdf is strongly measurable. -/
```

### `module_doc in CompNotation.lean` (module_doc, modified) [02171fd1be]
- file: `Mathlib/Probability/Kernel/Composition/CompNotation.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Notation for the compostition of a measure and a kernel

This operation, for which we introduce the notation `∘ₘ`, takes `μ : Measure α` and
`κ : Kernel α β` and creates `κ ∘ₘ μ : Measure β`. The integral of a function against `κ ∘ₘ μ` is
`∫⁻ x, f x ∂(κ ∘ₘ μ) = ∫⁻ a, ∫⁻ b, f b ∂(κ a) ∂μ`.

This file does not define composition but only introduces notation for
`MeasureTheory.Measure.bind μ κ`.

## Notations

* `κ ∘ₘ μ = MeasureTheory.Measure.bind μ κ`, for `κ` a kernel.
-/

/- This file is only for lemmas that are direct specializations of `Measure.bind` to kernels,
anything more involved should go elsewhere (for example the `MeasureComp` file). -/
assert_not_exists ProbabilityTheory.Kernel.compProd
```
- as the PR leaves it:
```lean
/-!
# Notation for the composition of a measure and a kernel

This operation, for which we introduce the notation `∘ₘ`, takes `μ : Measure α` and
`κ : Kernel α β` and creates `κ ∘ₘ μ : Measure β`. The integral of a function against `κ ∘ₘ μ` is
`∫⁻ x, f x ∂(κ ∘ₘ μ) = ∫⁻ a, ∫⁻ b, f b ∂(κ a) ∂μ`.

This file does not define composition but only introduces notation for
`MeasureTheory.Measure.bind μ κ`.

## Notations

* `κ ∘ₘ μ = MeasureTheory.Measure.bind μ κ`, for `κ` a kernel.
-/

/- This file is only for lemmas that are direct specializations of `Measure.bind` to kernels,
anything more involved should go elsewhere (for example the `MeasureComp` file). -/
assert_not_exists ProbabilityTheory.Kernel.compProd
```

### `module_doc in IntegralCompProd.lean` (module_doc, modified) [84e5808d7a]
- file: `Mathlib/Probability/Kernel/Composition/IntegralCompProd.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Bochner integral of a function against the composition and the composition-products of two kernels

We prove properties of the composition and the composition-product of two kernels.

If `κ` is a kernel from `α` to `β` and `η` is a kernel from `β` to `γ`, we can form their
composition `η ∘ₖ κ : Kernel α γ`. We proved in `ProbabilityTheory.Kernel.lintegral_comp` that it
verifies `∫⁻ c, f c ∂((η ∘ₖ κ) a) = ∫⁻ b, ∫⁻ c, f c ∂(η b) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

If `κ` is an s-finite kernel from `α` to `β` and `η` is an s-finite kernel from `α × β` to `γ`,
we can form their composition-product `κ ⊗ₖ η : Kernel α (β × γ)`.
We proved in `ProbabilityTheory.Kernel.lintegral_compProd` that it
verifies `∫⁻ bc, f bc ∂((κ ⊗ₖ η) a) = ∫⁻ b, ∫⁻ c, f (b, c) ∂(η (a, b)) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

## Main statements

* `ProbabilityTheory.integral_compProd`: the integral against the composition-product is
  `∫ z, f z ∂((κ ⊗ₖ η) a) = ∫ x, ∫ y, f (x, y) ∂(η (a, x)) ∂(κ a)`.

* `ProbabilityTheory.integral_comp`: the integral against the composition is
  `∫⁻ z, f z ∂((η ∘ₖ κ) a) = ∫⁻ x, ∫⁻ y, f y ∂(η x) ∂(κ a)`.

## Implementation details

This file is to a large extent a copy of part of `Mathlib/MeasureTheory/Integral/Prod.lean`.
The product of two measures is a particular case of composition-product of kernels and
it turns out that once the measurablity of the Lebesgue integral of a kernel is proved,
almost all proofs about integrals against products of measures extend with minimal modifications
to the composition-product of two kernels.

The composition of kernels can also be expressed easily with the composition-product and therefore
the proofs about the composition are only simplified versions of the ones for the
composition-product. However it is necessary to do all the proofs once again because the
composition-product requires s-finiteness while the composition does not.
-/
```
- as the PR leaves it:
```lean
/-!
# Bochner integral of a function against the composition and the composition-products of two kernels

We prove properties of the composition and the composition-product of two kernels.

If `κ` is a kernel from `α` to `β` and `η` is a kernel from `β` to `γ`, we can form their
composition `η ∘ₖ κ : Kernel α γ`. We proved in `ProbabilityTheory.Kernel.lintegral_comp` that it
verifies `∫⁻ c, f c ∂((η ∘ₖ κ) a) = ∫⁻ b, ∫⁻ c, f c ∂(η b) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

If `κ` is an s-finite kernel from `α` to `β` and `η` is an s-finite kernel from `α × β` to `γ`,
we can form their composition-product `κ ⊗ₖ η : Kernel α (β × γ)`.
We proved in `ProbabilityTheory.Kernel.lintegral_compProd` that it
verifies `∫⁻ bc, f bc ∂((κ ⊗ₖ η) a) = ∫⁻ b, ∫⁻ c, f (b, c) ∂(η (a, b)) ∂(κ a)`. In this file, we
prove the same equality for the Bochner integral.

## Main statements

* `ProbabilityTheory.integral_compProd`: the integral against the composition-product is
  `∫ z, f z ∂((κ ⊗ₖ η) a) = ∫ x, ∫ y, f (x, y) ∂(η (a, x)) ∂(κ a)`.

* `ProbabilityTheory.integral_comp`: the integral against the composition is
  `∫⁻ z, f z ∂((η ∘ₖ κ) a) = ∫⁻ x, ∫⁻ y, f y ∂(η x) ∂(κ a)`.

## Implementation details

This file is to a large extent a copy of part of `Mathlib/MeasureTheory/Integral/Prod.lean`.
The product of two measures is a particular case of composition-product of kernels and
it turns out that once the measurability of the Lebesgue integral of a kernel is proved,
almost all proofs about integrals against products of measures extend with minimal modifications
to the composition-product of two kernels.

The composition of kernels can also be expressed easily with the composition-product and therefore
the proofs about the composition are only simplified versions of the ones for the
composition-product. However it is necessary to do all the proofs once again because the
composition-product requires s-finiteness while the composition does not.
-/
```

### `doc_comment in Convergence.lean` (command, modified) [3fc9d67eb3]
- file: `Mathlib/Probability/Martingale/Convergence.lean`; changed: documentation:modified
- before the PR:
```lean
/-- A realization of a stochastic process with bounded upcrossings and bounded liminfs is
convergent.

We use the spelling `< ∞` instead of the standard `≠ ∞` in the assumptions since it is not as easy
to change `<` to `≠` under binders. -/
```
- as the PR leaves it:
```lean
/-- A realization of a stochastic process with bounded upcrossings and bounded limit inferiors is
convergent.

We use the spelling `< ∞` instead of the standard `≠ ∞` in the assumptions since it is not as easy
to change `<` to `≠` under binders. -/
```

### `module_doc in Convergence.lean` (module_doc, modified) [61c30db040]
- file: `Mathlib/Probability/Martingale/Convergence.lean`; changed: documentation:modified
- before the PR:
```lean
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

Implementationwise, we have `tendsto_of_no_upcrossings` which shows that
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
```
- as the PR leaves it:
```lean
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
```

### `module_doc in Upcrossing.lean` (module_doc, modified) [b362510186]
- file: `Mathlib/Probability/Martingale/Upcrossing.lean`; changed: documentation:modified
- before the PR:
```lean
/-!

### Variant of the upcrossing estimate

Now, we would like to prove a variant of the upcrossing estimate obtained by taking the supremum
over $N$ of the original upcrossing estimate. Namely, we want the inequality
$$
  (b - a) \sup_N \mathbb{E}[U_N(a, b)] \le \sup_N \mathbb{E}[f_N].
$$
This inequality is central for the martingale convergence theorem as it provides a uniform bound
for the upcrossings.

We note that on top of taking the supremum on both sides of the inequality, we had also used
the monotone convergence theorem on the left hand side to take the supremum outside of the
integral. To do this, we need to make sure $U_N(a, b)$ is measurable and integrable. Integrability
is easy to check as $U_N(a, b) ≤ N$ and so it suffices to show measurability. Indeed, by
noting that
$$
  U_N(a, b) = \sum_{i = 1}^N \mathbf{1}_{\{U_N(a, b) < N\}}
$$
$U_N(a, b)$ is measurable as $\{U_N(a, b) < N\}$ is a measurable set since $U_N(a, b)$ is a
stopping time.

-/
```
- as the PR leaves it:
```lean
/-!

### Variant of the upcrossing estimate

Now, we would like to prove a variant of the upcrossing estimate obtained by taking the supremum
over $N$ of the original upcrossing estimate. Namely, we want the inequality
$$
  (b - a) \sup_N \mathbb{E}[U_N(a, b)] \le \sup_N \mathbb{E}[f_N].
$$
This inequality is central for the martingale convergence theorem as it provides a uniform bound
for the upcrossings.

We note that on top of taking the supremum on both sides of the inequality, we had also used
the monotone convergence theorem on the left-hand side to take the supremum outside of the
integral. To do this, we need to make sure $U_N(a, b)$ is measurable and integrable. Integrability
is easy to check as $U_N(a, b) ≤ N$ and so it suffices to show measurability. Indeed, by
noting that
$$
  U_N(a, b) = \sum_{i = 1}^N \mathbf{1}_{\{U_N(a, b) < N\}}
$$
$U_N(a, b)$ is measurable as $\{U_N(a, b) < N\}$ is a measurable set since $U_N(a, b)$ is a
stopping time.

-/
```

### `module_doc in Basic.lean` (module_doc, modified) [dbc82350de]
- file: `Mathlib/Probability/Moments/Basic.lean`; changed: documentation:modified
- before the PR:
```lean
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
  and their mgfs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
* `ProbabilityTheory.IndepFun.cgf_add`: if two real random variables `X` and `Y` are independent
  and their cgfs are defined at `t`, then `cgf (X + Y) μ t = cgf X μ t + cgf Y μ t`
* `ProbabilityTheory.measure_ge_le_exp_cgf` and `ProbabilityTheory.measure_le_le_exp_cgf`:
  Chernoff bound on the upper (resp. lower) tail of a random variable. For `t` nonnegative such that
  the cgf exists, `ℙ(ε ≤ X) ≤ exp(- t*ε + cgf X ℙ t)`. See also
  `ProbabilityTheory.measure_ge_le_exp_mul_mgf` and
  `ProbabilityTheory.measure_le_le_exp_mul_mgf` for versions of these results using `mgf` instead
  of `cgf`.
-/
```
- as the PR leaves it:
```lean
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
```

### `doc_comment in Variance.lean` (command, modified) [0fd73d45e0]
- file: `Mathlib/Probability/Moments/Variance.lean`; changed: documentation:modified
- before the PR:
```lean
/-- **Popoviciu's inequality on variance**

The variance of a random variable `X` satisfying `a ≤ X ≤ b` almost everywhere is at most
`((b - a) / 2) ^ 2`. -/
```
- as the PR leaves it:
```lean
/-- **Popoviciu's inequality on variances**

The variance of a random variable `X` satisfying `a ≤ X ≤ b` almost everywhere is at most
`((b - a) / 2) ^ 2`. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none
