# Sketch: a whole-space meromorphy predicate

`Basic.lean` means `base/Mathlib/Analysis/Meromorphic/Basic.lean`. Bracketed numbers are packet
sources (seen in `decision_context.md`, not in `base/`). All Lean is unchecked.

## 1. Defining form
**Choice:** pointwise, as `Differentiable` is:
```lean
/-- `Meromorphic f` means that `f` is meromorphic at every point of `𝕜`. -/
@[fun_prop]
def Meromorphic (f : 𝕜 → E) : Prop := ∀ x, MeromorphicAt f x
```
**Alternatives:** `def Meromorphic f := MeromorphicOn f univ` (the literal reading; (a) becomes
near-definitional); an `abbrev` of that; an independent characterisation as `ContDiff` has [3] (none
suggests itself here).
**References:** `Basic.lean:420` (`MeromorphicOn` is already `∀ x ∈ U, MeromorphicAt f x`);
`Differentiable` [1].
**What would decide it:** a stated maintainer preference for the literal abbreviation. Otherwise
the pointwise form gives one-line closure proofs and a direct `fun_prop` route to `MeromorphicAt`.

## 2. Name and signature
**Choice:** `Meromorphic f`, `𝕜` implicit, root namespace; its API in `namespace Meromorphic`.
**Alternatives:** `Meromorphic 𝕜 f` with `𝕜` explicit (as `Differentiable 𝕜 f`, where the field
is not determined by `f`'s type); `MeromorphicOnUniv`.
**References:** `Basic.lean:35`, `:420` (neither takes `𝕜` explicitly); global/`On` pairs
`Continuous`, `Differentiable`, `ContDiff` [1]–[4]; no existing declaration `Meromorphic` (§2).
**What would decide it:** the neighbouring pairs settle it.

## 3. Agreement and transition lemmas
**Choice:**
```lean
@[simp] theorem meromorphicOn_univ : MeromorphicOn f univ ↔ Meromorphic f := by
  simp [MeromorphicOn, Meromorphic]
@[fun_prop] lemma Meromorphic.meromorphicAt (hf : Meromorphic f) : MeromorphicAt f x := hf x
lemma Meromorphic.meromorphicOn (hf : Meromorphic f) : MeromorphicOn f U := fun x _ ↦ hf x
lemma AnalyticOnNhd.meromorphic (hf : AnalyticOnNhd 𝕜 f univ) : Meromorphic f :=
  fun x ↦ (hf x trivial).meromorphicAt
```
**Alternatives:** no `simp` tag, as `differentiableOn_univ` [2] and `contDiffOn_univ` [3]; the
sides swapped under a name like `meromorphic_iff_meromorphicOn_univ`.
**References:** `continuousOn_univ` [4] (`simp`, set-wise on the left); `Basic.lean:422`.
**What would decide it:** whether `Meromorphic f` is to be the normal form. With `simp`,
`simp at`/`simpa using` on the 51 `MeromorphicOn f univ` hypotheses [12] now produce `Meromorphic f`
and may break proofs there; building `Analysis/Complex/ValueDistribution/` decides. Untagged is the
fallback.

## 4. Closure API and proof route
**Choice:** mirror the `MeromorphicOn` block (`Basic.lean:465-582`) one for one, each as an
`op`/`fun_op` pair: `id`, `const`, `add`, `neg`, `sub`, `smul`, `mul`, `inv`, `div`, `pow`, `zpow`,
`sum`, `prod`, `deriv` (protected), `iterated_deriv`; plus `neg_iff`, `inv_iff`. Proofs pointwise,
e.g. `fun x ↦ (hf x).add (hg x)`. No deprecated aliases.
**Alternatives:** prove through `MeromorphicOn … univ` and `meromorphicOn_univ`; only `op` forms,
leaving the rest to `fun_prop`.
**References:** `Basic.lean:476`, `:91` (the `fun_` pairs and deprecated primes, 2025-05-09).
**What would decide it:** the pair convention is this file's; the route is internal.

## 5. Automation
**Choice:** `@[fun_prop]` on the definition and on every closure lemma, both forms, as for
`MeromorphicAt`; `@[simp]` where the pointwise layer has it (`const`, `neg_iff`, `inv_iff`).
**Alternatives:** unregistered, as `MeromorphicOn` is.
**References:** `Basic.lean:34`, `:66`, `:174`, `:289`, `:420`; `FunProp.lean:61-71` [11].
**What would decide it:** nothing contrary found; registering `MeromorphicOn` is a separate change.

## 6. Finite sums and products
**Choice:** `(h : ∀ σ, Meromorphic (F σ))`, matching both existing layers.
**Alternatives:** `∀ σ ∈ s`, stronger, as suggested in review of #30587 [10]; it needs the
`MeromorphicAt` versions restated first, or a direct `Finset.induction`.
**References:** `Basic.lean:124`, `:144`, `:510`, `:521`.
**What would decide it:** whether reviewers now want [10] applied; if so, to all three layers in one
change. Open.

## 7. Codomain of products, quotients, powers
**Choice:** `𝕜`-valued, with `smul` taking a `𝕜`-valued scalar, exactly as the pointwise lemmas.
**Alternatives:** a normed `𝕜`-algebra (commutative for `prod`), as `AnalyticAt.mul` [7].
**References:** `Basic.lean:94`, `:111`, `:258`, `:307`; [6], [7].
**What would decide it:** generalising requires `MeromorphicAt.mul`/`inv` generalised first (the
`inv` proof uses field arithmetic, `Basic.lean:281`); the derived layer should not outrun its source.

## 8. Completeness in the derivative results
**Choice:** keep `[CompleteSpace E]`.
**Alternatives:** drop it for the whole-space version, via `MeromorphicOn.eventually_analyticAt`,
which needs no completeness [9].
**References:** `Basic.lean:346-350`, `:378`, `:562-582`; [8], [9].
**What would decide it:** a completeness-free proof. The pointwise proof (`Basic.lean:380-391`)
differentiates the analytic factor `g`, and `AnalyticAt.deriv` needs completeness (recalled), so
[9] alone does not supply one. Open; not for this change.

## 9. Placement
**Choice:** `Basic.lean`, a new section after `end MeromorphicOn` (`Basic.lean:633`), so the
order runs `At`, `On`, global; a bullet in the module docstring (`:15-20`).
**Alternatives:** immediately after `Basic.lean:420`, next to the `On` definition as `Differentiable`
sits by `DifferentiableOn` [1]; a new file `Meromorphic/Global.lean`.
**What would decide it:** open; 633 lines do not force a split.

## 10. Scope
**Choice:** the definition and decisions 3–8 only. Leave the 51 `univ`/`Set.univ`/`⊤` statements
[12], including `Basic.lean:615`, `:623`, unchanged; restate them in a follow-up once decision 3's
normal form is settled.
**Alternatives:** add `Meromorphic.countable_compl_analyticAt` and `Meromorphic.measurable` now;
restate every consumer in this change.
**References:** [12]; `Basic.lean:614-631`.
**What would decide it:** reviewer appetite for diff size, and whether consumers build under the
`simp` lemma. Open.
