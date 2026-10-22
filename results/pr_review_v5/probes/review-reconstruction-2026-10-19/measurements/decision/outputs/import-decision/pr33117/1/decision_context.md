# Decision context: a whole-space meromorphy predicate

Sources are from the base commit of Mathlib unless dated otherwise. They are numbered [1]–[12] across
the whole packet; a decision may refer back to a source listed under another. Line numbers in
`Mathlib/Analysis/Meromorphic/Basic.lean` match the copy in `base/`.

## 1. Defining form, and which form is preferred when both appear

**[1] `library_example`** — `Mathlib/Analysis/Calculus/FDeriv/Defs.lean:159-167`

```lean
/-- `DifferentiableOn 𝕜 f s` means that `f` is differentiable within `s` at any point of `s`. -/
@[fun_prop]
def DifferentiableOn (f : E → F) (s : Set E) :=
  ∀ x ∈ s, DifferentiableWithinAt 𝕜 f s x

/-- `Differentiable 𝕜 f` means that `f` is differentiable at any point. -/
@[fun_prop]
def Differentiable (f : E → F) :=
  ∀ x, DifferentiableAt 𝕜 f x
```

Bears on the defining form: here the whole-space predicate is defined pointwise from the `At`
predicate, not as the set-wise predicate on `univ`, and sits next to the set-wise definition.

**[2] `library_example`** — `Mathlib/Analysis/Calculus/FDeriv/Basic.lean:511-517`

```lean
theorem differentiableOn_univ : DifferentiableOn 𝕜 f univ ↔ Differentiable 𝕜 f := by
  simp only [DifferentiableOn, Differentiable, differentiableWithinAt_univ, mem_univ,
    forall_true_left]

@[fun_prop]
theorem Differentiable.differentiableOn (h : Differentiable 𝕜 f) : DifferentiableOn 𝕜 f s :=
  (differentiableOn_univ.2 h).mono (subset_univ _)
```

Bears on the agreement statement (a): the equivalence is named `<setwise>_univ`, has the set-wise form
on the left, and is not tagged `simp`; a separate transition lemma passes from the global to any set.

**[3] `library_example`** — `Mathlib/Analysis/Calculus/ContDiff/Defs.lean:1031-1049`

```lean
/-- A function is continuously differentiable up to `n` if it admits derivatives up to
order `n`, which are continuous. Contrary to the case of definitions in domains (where derivatives
might not be unique) we do not need to localize the definition in space or time.
-/
@[fun_prop]
def ContDiff (n : WithTop ℕ∞) (f : E → F) : Prop :=
  match n with
  | ω => ∃ p : E → FormalMultilinearSeries 𝕜 E F, HasFTaylorSeriesUpTo ⊤ f p
      ∧ ∀ i, AnalyticOnNhd 𝕜 (fun x ↦ p x i) univ
  | (n : ℕ∞) => ∃ p : E → FormalMultilinearSeries 𝕜 E F, HasFTaylorSeriesUpTo n f p

/-- If `f` has a Taylor series up to `n`, then it is `C^n`. -/
theorem HasFTaylorSeriesUpTo.contDiff {n : ℕ∞} {f' : E → FormalMultilinearSeries 𝕜 E F}
    (hf : HasFTaylorSeriesUpTo n f f') : ContDiff 𝕜 n f :=
  ⟨f', hf⟩

@[simp, fun_prop] theorem contDiffOn_empty : ContDiffOn 𝕜 n f ∅ := fun _x hx ↦ hx.elim

theorem contDiffOn_univ : ContDiffOn 𝕜 n f univ ↔ ContDiff 𝕜 n f := by
```

Bears on the defining form: a third option, where the global predicate has its own definition (neither
the set-wise one on `univ` nor a pointwise quantifier) and the equivalence is proved afterwards, again
without `simp`.

**[4] `library_example`** — `Mathlib/Topology/ContinuousOn.lean:47-50`

```lean
@[simp]
theorem continuousOn_univ {f : α → β} : ContinuousOn f univ ↔ Continuous f := by
  simp [continuous_iff_continuousAt, ContinuousOn, ContinuousAt, ContinuousWithinAt,
    nhdsWithin_univ]
```

Bears on which form is preferred when both appear: unlike [2] and [3], this equivalence is a `simp`
lemma, so `simp` rewrites the set-wise form on `univ` into the global predicate.

**[5] `counterexample`** — `Mathlib/Analysis/Analytic/Basic.lean:443-445`

```lean
@[simp] lemma analyticOn_univ {f : E → F} :
    AnalyticOn 𝕜 f univ ↔ AnalyticOnNhd 𝕜 f univ := by
  simp only [AnalyticOn, analyticWithinAt_univ, AnalyticOnNhd]
```

Bears on whether a separate whole-space predicate is the library's only pattern: for analyticity, the
`simp` normal form on all of the domain is the set-wise `AnalyticOnNhd 𝕜 f univ` (also used inside
[3]); a search for an `analyticOnNhd_univ` equivalence to a global predicate found none.

## 2. Name and relation to neighbours

No new source. A search of `Mathlib/` at base for the bare word `Meromorphic` finds only prose
(module headers and docstrings), no declaration. The neighbouring families in [1]–[4] pair a global
name with an `On` name (`Differentiable`/`DifferentiableOn`, `ContDiff`/`ContDiffOn`,
`Continuous`/`ContinuousOn`) and name the equivalence `<setwise>_univ`. The base file's
`MeromorphicOn` (line 420) quantifies `∀ x ∈ U, MeromorphicAt f x`, the shape of `AnalyticOnNhd`
rather than `AnalyticOn` [5]; the base lemma name `AnalyticOnNhd.meromorphicOn` (line 422) records that
correspondence. No dated earlier decision on the name was found.

## 3. Codomain of products, quotients and powers

**[6] `library_example`** — `Mathlib/Analysis/Meromorphic/Basic.lean:110-113`

```lean
@[fun_prop]
lemma mul {f g : 𝕜 → 𝕜} (hf : MeromorphicAt f x) (hg : MeromorphicAt g x) :
    MeromorphicAt (f * g) x :=
  hf.smul hg
```

Bears on the codomain: the existing pointwise multiplicative API is stated for `𝕜`-valued functions
(likewise `inv`, `div`, `pow`, `zpow`, `prod`, lines 257-330 and 122-140), and `smul` (line 94) takes a
`𝕜`-valued scalar function and an `E`-valued one. A search of `Mathlib/Analysis/Meromorphic/` for
`NormedRing` or `NormedAlgebra` returns nothing.

**[7] `counterexample`** — `Mathlib/Analysis/Analytic/Constructions.lean:38`, `:645-649`, `:1236`

```lean
variable {A : Type*} [NormedRing A] [NormedAlgebra 𝕜 A]
```
```lean
/-- Multiplication of analytic functions (valued in a normed `𝕜`-algebra) is analytic. -/
@[fun_prop]
lemma AnalyticAt.mul {f g : E → A} {z : E} (hf : AnalyticAt 𝕜 f z) (hg : AnalyticAt 𝕜 g z) :
    AnalyticAt 𝕜 (f * g) z :=
  hf.fun_mul hg
```
```lean
theorem Finset.analyticOnNhd_fun_prod {A : Type*} [NormedCommRing A] [NormedAlgebra 𝕜 A]
```

Bears on the codomain: the analytic counterpart states multiplication for a normed `𝕜`-algebra and
finite products for a commutative one, so the `𝕜`-only pattern in [6] is not the only one in this
area.

## 4. Hypotheses of the derivative results

**[8] `written_guidance`** — `Mathlib/Analysis/Meromorphic/Basic.lean:346-350`

```lean
/-- In a complete space, a function which is meromorphic at a point is analytic at all nearby
points. The completeness assumption can be dispensed with if one assumes that `f` is meromorphic
on a set around `x`, see `MeromorphicOn.eventually_analyticAt`. -/
theorem eventually_analyticAt [CompleteSpace E] {f : 𝕜 → E}
    (h : MeromorphicAt f x) : ∀ᶠ y in 𝓝[≠] x, AnalyticAt 𝕜 f y := by
```

Bears on whether completeness is needed: it states that meromorphy on a surrounding set can replace
completeness for one of the facts the pointwise theory uses. The existing `MeromorphicAt.deriv` (line
378) and `MeromorphicOn.deriv`/`iterated_deriv` (lines 562-582) all carry `[CompleteSpace E]`.

**[9] `library_example`** — `Mathlib/Analysis/Meromorphic/Order.lean:715-719`

```lean
/-- If a function is meromorphic on a set `U`, then for each point in `U`, it is analytic at nearby
points in `U`. When the target space is complete, this can be strengthened to analyticity at all
nearby points, see `MeromorphicAt.eventually_analyticAt`. -/
theorem eventually_analyticAt (h : MeromorphicOn f U) (hx : x ∈ U) :
    ∀ᶠ y in 𝓝[U \ {x}] x, AnalyticAt 𝕜 f y := by
```

Bears on whether completeness is needed: the set-wise version holds with no completeness hypothesis
(`Order.lean` contains no `CompleteSpace` at base); with `U` the whole space, the filter
`𝓝[U \ {x}] x` is the punctured neighbourhood filter `𝓝[≠] x` of [8]. Whether the derivative proof can use it is not shown by any source found.

## 5. Form of the closure statements (finite sums and products)

**[10] `earlier_decision`** — review of PR #30587, `Mathlib/Analysis/Meromorphic/Basic.lean`,
eric-wieser, 2025-10-19

~~~
```suggestion
theorem prod (h : ∀ σ ∈ s, MeromorphicAt (F σ) x) :
```
would be a stronger result
~~~

Bears on the hypothesis of finite sums and products: a reviewer argued for quantifying only over
`σ ∈ s`, for strength. The base file still states `prod`, `fun_prod`, `sum`, `fun_sum` with
`h : ∀ σ, …` (lines 124, 137, 144, 157, 510, 516, 521, 527), so the suggestion and the library
disagree.

Also visible in the base file: each operation comes as a pair, `add` on `f + g` and `fun_add` on
`fun z ↦ f z + g z`, with older primed names deprecated (e.g. line 91, `since := "2025-05-09"`);
`MeromorphicOn` repeats the pairs (lines 475-556). No other source found.

## 6. Registration with automation (`fun_prop`, `simp`)

**[11] `mechanism`** — `Mathlib/Tactic/FunProp.lean:61-71`

~~~
To set up `fun_prop` for a new function property, you have to:

1. Mark the function property with the `fun_prop` attribute when defining it:
```lean
@[fun_prop]
def Continuous (f : X → Y) := ...
```
or later on with:
```lean
attribute [fun_prop] Continuous
```
~~~

Bears on registration: a new predicate takes part in `fun_prop` only if marked, and the doc goes on
(lines 73 onward) to the identity, constant and composition lemmas it then needs.

At base, `MeromorphicAt` is `@[fun_prop]` (line 34) with `@[fun_prop]` closure lemmas, while
`MeromorphicOn` (line 420) and its lemmas carry no `fun_prop`. In the neighbours, `Differentiable`,
`DifferentiableOn` and `ContDiff` are `@[fun_prop]` at definition ([1], [3]), and the global-to-set
transition lemma is `@[fun_prop]` ([2]). On `simp`, see [2]–[5]: the `_univ` equivalences split between
untagged and `simp`.

## 7. Scope: further results, and restating existing statements

**[12] `consumer`** — search results at base (`MeromorphicOn … univ`, `Set.univ` or `⊤`)

```
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:70:lemma toClosedBall_divisor {r : ℝ} {f : ℂ → ℂ} (h : MeromorphicOn f univ) :
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:268:theorem logCounting_add_analyticOn (hf : MeromorphicOn f univ) (hg : AnalyticOn 𝕜 g univ) :
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:297:theorem logCounting_add_top_le {f₁ f₂ : 𝕜 → E} {r : ℝ} (h₁f₁ : MeromorphicOn f₁ Set.univ)
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:298:    (h₁f₂ : MeromorphicOn f₂ Set.univ) (hr : 1 ≤ r) :
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:319:    (h₁f : ∀ a, MeromorphicOn (f a) Set.univ) (hr : 1 ≤ r) :
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:360:    (h₁f₁ : MeromorphicOn f₁ Set.univ) (h₂f₁ : ∀ z, meromorphicOrderAt f₁ z ≠ ⊤)
Mathlib/Analysis/Complex/ValueDistribution/CountingFunction.lean:448:    {f : ℂ → ℂ} (h : MeromorphicOn f ⊤) (hR : R ≠ 0) :
Mathlib/Analysis/Complex/ValueDistribution/FirstMainTheorem.lean:47:lemma characteristic_sub_characteristic_inv (h : MeromorphicOn f ⊤) :
Mathlib/Analysis/Complex/ValueDistribution/FirstMainTheorem.lean:66:    (hf : MeromorphicOn f Set.univ) (hR : R ≠ 0) :
Mathlib/Analysis/Complex/ValueDistribution/ProximityFunction.lean:160:theorem proximity_mul_top_le {f₁ f₂ : ℂ → ℂ} (h₁f₁ : MeromorphicOn f₁ Set.univ)
Mathlib/Analysis/Meromorphic/Basic.lean:615:    (h : MeromorphicOn f Set.univ) :
Mathlib/Analysis/Meromorphic/Complex.lean:23:lemma MeromorphicOn.Gamma : MeromorphicOn Gamma univ :=
```

Bears on the scope of edits: a single-line search finds 51 such lines in six files (11 in
`CharacteristicFunction.lean`, 22 in `CountingFunction.lean`, 7 in `FirstMainTheorem.lean`, 8 in
`ProximityFunction.lean`, 2 in `Meromorphic/Basic.lean`, 1 in `Meromorphic/Complex.lean`), written
three ways (`univ`, `Set.univ`, `⊤`), often beside `∀ z, meromorphicOrderAt f z ≠ ⊤` and, at line 268,
beside the set-wise `AnalyticOn 𝕜 g univ`. These are the statements a restatement would touch, and
the hypotheses that further results on the new notion would meet in use.

On which further results belong: no source found that states what basic API a new whole-space
predicate must ship with. The neighbours in [1]–[4] show what those families have (the `_univ`
equivalence, the transition lemma), not what was required at their introduction.

## 8. Placement

No source beyond [1] and [3], in which the global predicate is defined in the same file as, and
next to, its set-wise counterpart. The base file defines `MeromorphicAt` (line 35) and `MeromorphicOn`
(line 420) in one file, with separate `namespace` blocks. No written guidance or earlier decision on
placement was found.

## 9. Proof route

No source found. In the base file every `MeromorphicOn` closure lemma is proved pointwise from the
`MeromorphicAt` lemma (e.g. line 476, `fun x hx ↦ (hf x hx).add (hg x hx)`), and [2] proves the
`_univ` equivalence by unfolding with `simp only`.
