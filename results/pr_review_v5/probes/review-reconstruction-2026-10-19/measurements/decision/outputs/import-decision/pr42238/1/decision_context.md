# Decision context: scoping the fourth-ring variables of `LinearIsometry.lean`

Sources are from the base commit, from Mathlib Zulip before the contribution, or from earlier PR
reviews. Line numbers are at the base commit. Twelve sources in all, numbered S1 to S12.

## 1. How the fourth-ring data is brought into scope (mechanism and placement)

The options seen at base are: binders written on the theorem itself, a `variable` block kept for a
whole section, a `variable` introduced partway through a section just before its users, and
`variable ... in` for a single declaration. The file already uses some of these patterns.

**S1** · `library_example` · `Mathlib/Algebra/Module/LinearMap/Defs.lean:518-524`
```lean
theorem comp_assoc
    {R₄ M₄ : Type*} [Semiring R₄] [AddCommMonoid M₄] [Module R₄ M₄]
    {σ₃₄ : R₃ →+* R₄} {σ₂₄ : R₂ →+* R₄} {σ₁₄ : R₁ →+* R₄}
    [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄] [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄] [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄]
    (f : M₁ →ₛₗ[σ₁₂] M₂) (g : M₂ →ₛₗ[σ₂₃] M₃) (h : M₃ →ₛₗ[σ₃₄] M₄) :
    ((h.comp g : M₂ →ₛₗ[σ₂₄] M₄).comp f : M₁ →ₛₗ[σ₁₄] M₄) = h.comp (g.comp f : M₁ →ₛₗ[σ₁₃] M₃) :=
  rfl
```
Shows that the semilinear-map version of the same associativity lemma declares its fourth ring,
module and three compatibility triples as binders on the theorem, not in a file-wide `variable`.

**S2** · `library_example` · `Mathlib/Topology/Algebra/Module/ContinuousLinearMap/Basic.lean:554-558`
```lean
theorem comp_assoc {R₄ : Type*} [Semiring R₄] [Module R₄ M₄] {σ₁₄ : R₁ →+* R₄} {σ₂₄ : R₂ →+* R₄}
    {σ₃₄ : R₃ →+* R₄} [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄] [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄]
    [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄] (h : M₃ →SL[σ₃₄] M₄) (g : M₂ →SL[σ₂₃] M₃) (f : M₁ →SL[σ₁₂] M₂) :
    (h ∘SL g) ∘SL f = h ∘SL (g ∘SL f) :=
  rfl
```
A second example of theorem-local fourth-ring binders. Here the fourth module `M₄` itself still
comes from the file's `variable`s. Only `R₄`, its module structure and the σ's are local.

**S3** · `counterexample` · `Mathlib/Algebra/Module/Equiv/Defs.lean:288-298` and `:411-412` (the
enclosing `section` runs from line 191 to line 562)
```lean
variable {σ₁₄ : R₁ →+* R₄} {σ₄₁ : R₄ →+* R₁} [RingHomInvPair σ₁₄ σ₄₁] [RingHomInvPair σ₄₁ σ₁₄]
variable {σ₂₃ : R₂ →+* R₃} {σ₃₂ : R₃ →+* R₂}
variable {σ₂₄ : R₂ →+* R₄} {σ₄₂ : R₄ →+* R₂} [RingHomInvPair σ₂₄ σ₄₂] [RingHomInvPair σ₄₂ σ₂₄]
variable {σ₃₄ : R₃ →+* R₄} {σ₄₃ : R₄ →+* R₃} [RingHomInvPair σ₃₄ σ₄₃] [RingHomInvPair σ₄₃ σ₃₄]
variable {re₁₂ : RingHomInvPair σ₁₂ σ₂₁} {re₂₁ : RingHomInvPair σ₂₁ σ₁₂}
variable {re₂₃ : RingHomInvPair σ₂₃ σ₃₂} {re₃₂ : RingHomInvPair σ₃₂ σ₂₃}
variable [RingHomCompTriple σ₁₂ σ₂₃ σ₁₃] [RingHomCompTriple σ₃₂ σ₂₁ σ₃₁]
variable [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄] [RingHomCompTriple σ₄₂ σ₂₁ σ₄₁]
variable [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄] [RingHomCompTriple σ₄₃ σ₃₁ σ₄₁]
variable [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄] [RingHomCompTriple σ₄₃ σ₃₂ σ₄₂]
variable (e₁₂ : M₁ ≃ₛₗ[σ₁₂] M₂) (e₂₃ : M₂ ≃ₛₗ[σ₂₃] M₃)
```
```lean
lemma trans_assoc (e₁₂ : M₁ ≃ₛₗ[σ₁₂] M₂) (e₂₃ : M₂ ≃ₛₗ[σ₂₃] M₃) (e₃₄ : M₃ ≃ₛₗ[σ₃₄] M₄) :
    (e₁₂.trans e₂₃).trans e₃₄ = e₁₂.trans (e₂₃.trans e₃₄) := rfl
```
`LinearEquiv.trans_assoc`, the closest analogue of `LinearIsometryEquiv.trans_assoc`, takes its
fourth-ring data from a `variable` block covering a section of more than 270 lines. This is the same
arrangement as the base file's, so the library does it both ways. Some of the
inverse pairs here are implicit binders `{re₁₂ : …}` rather than instance binders `[…]`.

**S4** · `counterexample` · `Mathlib/Topology/Algebra/Module/Equiv.lean:689-691` (the `variable`
holds until `end AddCommMonoid` at line 798)
```lean
variable {M₁} {R₄ : Type*} [Semiring R₄] [Module R₄ M₄] {σ₃₄ : R₃ →+* R₄} {σ₄₃ : R₄ →+* R₃}
  [RingHomInvPair σ₃₄ σ₄₃] [RingHomInvPair σ₄₃ σ₃₄] {σ₂₄ : R₂ →+* R₄} {σ₁₄ : R₁ →+* R₄}
  [RingHomCompTriple σ₂₁ σ₁₄ σ₂₄] [RingHomCompTriple σ₂₄ σ₄₃ σ₂₃] [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄]
```
A third pattern: `ContinuousLinearEquiv` brings in the fourth ring with a `variable` partway down
the file, just before the declarations that use it (`arrowCongr…`), and does not close it with a
section.

**S5** · `library_example` · `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean:980-983` and
`:1051-1056`
```lean
variable (R) in
/-- The negation operation on a normed space `E`, considered as a linear isometry equivalence. -/
def neg : E ≃ₗᵢ[R] E :=
  { LinearEquiv.neg R with norm_map' := norm_neg }
```
```lean
section submoduleMap

variable {R R₁ R₂ M M₂ : Type*}
variable [Ring R] [Ring R₂] [SeminormedAddCommGroup M] [SeminormedAddCommGroup M₂]
variable [Module R M] [Module R₂ M₂] {σ₁₂ : R →+* R₂} {σ₂₁ : R₂ →+* R}
variable {re₁₂ : RingHomInvPair σ₁₂ σ₂₁} {re₂₁ : RingHomInvPair σ₂₁ σ₁₂}
```
The target file already uses both `variable … in` for one declaration and a named `section` with its
own ring and module variables. The second is also in `LinearIsometry`'s namespace at lines 366-381.

**S6** · `earlier_decision` · Zulip `#mathlib4` › "style proposal: avoid `variable {X} ... variable (X)`",
Kim Morrison (maintainer), 2025-02-27
````
A proposal for the style guide. Let's avoid  ```Lean4 variable (X)  def foo := ...  variable {X} ```  in favour of  ```Lean4 variable (X) in def foo := ... ```
````
This prefers `variable … in` for a change that applies to a single declaration. The thread is about
binder updates, not adding new variables. Damiano Testa reported that a prototype linter flagged
218 exceptions (2025-02-28).

**S7** · `earlier_decision` · same thread, Eric Wieser (maintainer), 2025-02-27
````
I assume we are still fine with  ```Lean4 variable {X}  ...  section variable (X)  ...  end  ... ```  for when a whole group of declarations want explicit arguments?
````
The competing view in the same thread: when a group of declarations shares a change, a `section`
remains acceptable. The two users of the fourth ring are about 440 lines apart, in different
namespaces (lines 338 and 774).

**S8** · `earlier_decision` · review of PR #31219, `Mathlib/RingTheory/Flat/IsBaseChange.lean`,
2025-11-16, urkud
```
IMHO, it's more readable if you repeat the explicit arguments in each lemma.
```
A reviewer preferring arguments on each lemma over shared `variable`s, for readability. This
concerned explicit arguments, not instance arguments.

**S9** · `earlier_decision` · review of PR #25178, `Mathlib/Algebra/Module/Equiv/Defs.lean`,
2025-05-26, eric-wieser
```
How horrible!
```
The comment was left on the hunk that wrote S3's long fourth-ring `variable` block. It is a reaction
to that block, but no reason is given and the block was kept. Its target and weight are unclear.

## 2. Form of the two theorems: argument order and hypotheses

The brief leaves open whether the order of implicit and instance arguments must stay as it is.

**S10** · `consumer` · `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean:338-340, 342-347` and
`:774-776, 778, 784`
```lean
theorem comp_assoc (f : E₃ →ₛₗᵢ[σ₃₄] E₄) (g : E₂ →ₛₗᵢ[σ₂₃] E₃) (h : E →ₛₗᵢ[σ₁₂] E₂) :
    (f.comp g).comp h = f.comp (g.comp h) :=
  rfl
instance instMonoid : Monoid (E →ₗᵢ[R] E) where
  one := id
  mul := comp
  mul_assoc := comp_assoc
  one_mul := id_comp
  mul_one := comp_id
```
```lean
theorem trans_assoc (eEE₂ : E ≃ₛₗᵢ[σ₁₂] E₂) (eE₂E₃ : E₂ ≃ₛₗᵢ[σ₂₃] E₃) (eE₃E₄ : E₃ ≃ₛₗᵢ[σ₃₄] E₄) :
    eEE₂.trans (eE₂E₃.trans eE₃E₄) = (eEE₂.trans eE₂E₃).trans eE₃E₄ :=
  rfl
instance instGroup : Group (E ≃ₗᵢ[R] E) where
  mul_assoc _ _ _ := trans_assoc _ _ _
```
The theorems' main users in the file are the `Monoid` and `Group` instances. They pass the three
explicit arguments positionally, or by unification, and never name an implicit.

**S11** · `consumer` · `Mathlib/Analysis/InnerProductSpace/PiL2.lean:906-912`
```lean
@[simp]
theorem Complex.map_isometryOfOrthonormal (v : OrthonormalBasis (Fin 2) ℝ F) (f : F ≃ₗᵢ[ℝ] F') :
    Complex.isometryOfOrthonormal (v.map f) = (Complex.isometryOfOrthonormal v).trans f := by
  simp only [isometryOfOrthonormal, OrthonormalBasis.map, LinearIsometryEquiv.symm_trans,
    LinearIsometryEquiv.symm_symm]
  -- Porting note: `LinearIsometryEquiv.trans_assoc` doesn't trigger in the `simp` above
  rw [LinearIsometryEquiv.trans_assoc]
```
This is the only use of either theorem by full name found at base, and it is a bare `rw`. A
search for `@LinearIsometry…`/`@LinearIsometryEquiv…` across `Mathlib/Analysis` found no
`@`-application of either theorem.

The order of implicits in comparable lemmas is shown in S1 and S2: the ring and module first, then
the σ's, then the compatibility triples, then the explicit maps. S1 and S3 list the explicit maps
inner map first; S2 lists them outer map first, as the base `LinearIsometry.comp_assoc` does. A Zulip search for guidance on whether
reordering implicit or instance arguments counts as a breaking change found nothing on point.

## 3. Scope of edits: other rarely used variables of the file-wide block

**S12** · `earlier_decision` · Zulip `#mathlib4` › "Removing / linting against unused `variable`
commands", Marcelo Lynch, 2026-07-29 (Thomas Murrills replied the same day: "I think we definitely
want this unused variables linter, btw. :)")
```
One new linter that this feature enables is one that looks for `variable` commands that declare binders that are then never used. One might end up with these after refactors / copy-pasting files, etc., or by just over-specifying variables…
```
A separate effort targets `variable` binders that are never used. The thread mentions a sweep, #42214. The
fourth-ring data here is used, by two declarations, so this bears on how far a variable cleanup in
this file should reach, not on the fourth ring itself.

At base, the other variables in the block are used more widely. `F` with `[NormedAddCommGroup F]
[Module R F]` is used at lines 138, 207, 234, 237, 951, 956, and the third ring by `comp`, `trans`
and their lemmas. Nothing was found that argues for or against scoping them in the same change.

## 4. Names

No decision is open: the brief fixes both names. Nothing further found.

## 5. Registration with automation

Neither theorem is tagged at base. S11 records a porting note that `trans_assoc` does not fire in
`simp`. No source bears on whether scoping should change any attribute.

## 6. Proof route

Both proofs are `rfl` at base (S10), and so are those of S1 to S3. Nothing found suggests another
route.

## 7. Performance premise

No base-commit comment or Zulip message was found that measures the cost of unused local
`RingHomInvPair`/`RingHomCompTriple` instances in a `variable` block. Searches for that turned up
only general typeclass-performance discussion, which is not cited.
