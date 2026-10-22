# Decision context: ⋆-algebra isomorphisms between operator algebras on Hilbert spaces

Twelve sources, numbered S1–S12. Each is given in full at its first use. Where a source also bears
on a later decision, it is referred to there by number, with one sentence on what it bears on.
All paths are at the base commit.

## 1. Which isomorphisms (b) and (c) cover: every ⋆-algebra isomorphism, or only those with a continuity hypothesis, and in what form

**S1** · `library_example` · `Mathlib/Analysis/CStarAlgebra/Spectrum.lean:279-292`
```
namespace StarAlgEquiv

variable {F A B : Type*} [NonUnitalCStarAlgebra A] [NonUnitalCStarAlgebra B] [EquivLike F A B]
variable [NonUnitalAlgEquivClass F ℂ A B] [StarHomClass F A B]

lemma nnnorm_map (φ : F) (a : A) : ‖φ a‖₊ = ‖a‖₊ :=
  le_antisymm (NonUnitalStarAlgHom.nnnorm_apply_le φ a) <| by
    simpa using NonUnitalStarAlgHom.nnnorm_apply_le (symm (φ : A ≃⋆ₐ[ℂ] B)) ((φ : A ≃⋆ₐ[ℂ] B) a)

lemma norm_map (φ : F) (a : A) : ‖φ a‖ = ‖a‖ :=
  congr_arg NNReal.toReal (nnnorm_map φ a)

lemma isometry (φ : F) : Isometry φ :=
  AddMonoidHomClass.isometry_of_norm φ (norm_map φ)
```
Shows that, between *complex* C⋆-algebras, any ⋆-algebra equivalence is already isometric, and so
continuous, with no hypothesis. Lines 262–275 of the same file register non-unital
⋆-homomorphisms of complex C⋆-algebras as `ContinuousLinearMapClass`, as a scoped instance under
`CStarAlgebra`. Nothing comparable was found for real scalars or for a general `RCLike 𝕜`.

**S2** · `earlier_decision` · Zulip `#mathlib4`, topic "RFC: bicontinuous maps shouldn't be called
`ContinuousEquiv`", Jireh Loreaux (maintainer), 2025-01-04
```
In other words, I think the canonical way to refer to a linear equivalence which is also continuous
in the forward direction should be either `(f : E →L[𝕜] F) (hf : Function.Bijective f)` or
`(f : E ≃ₗ[𝕜] F) (hf : Continuous f)` depending on whether it is the continuity or the
computability of the inverse which is more important.
```
A stated preference, with its reason, for writing continuity as an unbundled hypothesis on an
algebraic equivalence rather than as a new bundled type. It concerns maps that are continuous in
one direction only.

**S3** · `library_example` · `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:15-33`
```
This file shows that continuous algebra equivalences between continuous endomorphisms are inner.
See `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean` for the non-continuous version.
The proof follows the same idea as the non-continuous version.

# TODO:
- when `V = W`, we can state that the group homomorphism
  `(V →L[𝕜] V)ˣ →* ((V →L[𝕜] V) ≃A[𝕜] (V →L[𝕜] V))` is surjective,
  see `Module.End.mulSemiringActionToAlgEquiv_conjAct_surjective` for the non-continuous
  version of this.
-/

open ContinuousLinearMap ContinuousLinearEquiv

/-- This is the continuous version of `AlgEquiv.eq_linearEquivConjAlgEquiv`. -/
public theorem ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv {𝕜 V W : Type*}
    [NontriviallyNormedField 𝕜] [SeminormedAddCommGroup V] [SeminormedAddCommGroup W]
    [NormedSpace 𝕜 V] [NormedSpace 𝕜 W] [SeparatingDual 𝕜 V] [SeparatingDual 𝕜 W]
    (f : (V →L[𝕜] V) ≃A[𝕜] (W →L[𝕜] W)) :
    ∃ U : V ≃L[𝕜] W, f = U.conjContinuousAlgEquiv := by
```
The nearest counterpart. It expresses continuity through the bundled type `≃A[𝕜]`, a competing
pattern to S2's unbundled hypothesis.

At base no bundled continuous ⋆-algebra equivalence exists: a search for `ContinuousStarAlgEquiv`
or a `≃⋆A[` notation found nothing. Bundled continuity would therefore need a new type, or `≃A[𝕜]`
together with a separate star condition.

## 2. The scalar field

**S4** · `written_guidance` · `Mathlib/Analysis/CStarAlgebra/ContinuousLinearMap.lean:11-21`
```
/-! # `E →L[ℂ] E` as a C⋆-algebra

We place this here because, for reasons related to the import hierarchy, it should not be placed
in earlier files.
-/

@[expose] public section

noncomputable
instance {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℂ E] [CompleteSpace E] :
    CStarAlgebra (E →L[ℂ] E) where
```
`E →L[𝕜] E` is a `CStarAlgebra` only for `𝕜 = ℂ`. That is the setting in which S1's automatic
isometry applies. `Adjoint.lean` itself states its star structure and `CStarRing` for any `RCLike 𝕜`.

**S5** · `written_guidance` · `Mathlib/Analysis/InnerProductSpace/StarOrder.lean:15-19` and `56-60`, `78-80`
```
In this file we show that the continuous linear maps on a complex Hilbert space form a
`StarOrderedRing`.  Note that they are already equipped with the Loewner partial order. We also
prove that, with respect to this partial order, a map is positive if every element of the
real spectrum is nonnegative. Consequently, when `H` is a Hilbert space, then `H →L[ℂ] H` is
equipped with all the usual instances of the continuous functional calculus.
```
```
/-- Because this takes `ContinuousFunctionalCalculus ℝ (H →L[𝕜] H) IsSelfAdjoint` as an argument,
and for the moment we only have this for `𝕜 := ℂ`, this is not registered as an instance. -/
lemma instStarOrderedRingRCLike
    [ContinuousFunctionalCalculus ℝ (H →L[𝕜] H) IsSelfAdjoint] :
    StarOrderedRing (H →L[𝕜] H) where
```
```
instance instStarOrderedRing {H : Type*} [NormedAddCommGroup H]
    [InnerProductSpace ℂ H] [CompleteSpace H] : StarOrderedRing (H →L[ℂ] H) :=
  instStarOrderedRingRCLike
```
States that the ordered-star structure exists as an instance only over ℂ. For a general
`RCLike 𝕜` it is available only as a lemma, under an extra hypothesis. The Loewner order itself is
defined for every `RCLike 𝕜`.

Also relevant: S1 is stated over ℂ only.

## 3. How the unitary from V onto W and the conjugation in (a) are expressed

**S6** · `library_example` · `Mathlib/Algebra/Star/UnitaryStarAlgAut.lean:21-31` and `41-42`
```
namespace Unitary
variable {S R : Type*} [Semiring R] [StarMul R]
  [SMul S R] [IsScalarTower S R R] [SMulCommClass S R R]

variable (S R) in
/-- Each unitary element `u` defines a ⋆-algebra automorphism such that
`x ↦ u * x * star u`.

This is the ⋆-algebra automorphism version of a specialized version of
`MulSemiringAction.toAlgAut`. -/
def conjStarAlgAut : unitary R →* (R ≃⋆ₐ[S] R) where
```
```
@[simp] theorem conjStarAlgAut_apply (u : unitary R) (x : R) :
    conjStarAlgAut S R u x = u * x * (star u : R) := rfl
```
An existing unitary conjugation, phrased with a unitary *element* of one star ring, so V = W only.
It is bundled as a monoid hom into ⋆-automorphisms.

**S7** · `library_example` · `Mathlib/Analysis/InnerProductSpace/Positive.lean:192-193`
```
theorem isPositive_linearIsometryEquiv_conj_iff {T : E →ₗ[𝕜] E} (f : E ≃ₗᵢ[𝕜] F) :
    IsPositive (f.toLinearMap ∘ₗ T ∘ₗ f.symm.toLinearMap) ↔ IsPositive T := by
```
A competing form. Here a unitary between two different spaces is a `LinearIsometryEquiv`, and the
conjugation is written out as a composite, with no bundled map.

Also relevant: S8, where a maintainer gives his reason why unitary conjugation is a natural
concept for C⋆-algebras.

## 4. Names and their relation to neighbours

**S8** · `earlier_decision` · Zulip `#PR-reviews`, topic "#29028 define unitary R →* StarAlgEquiv S R R",
2025-10-31 (the PR that added S6)
```
Monica Omar — 15:42: There are a lot of potential applications. Hmm I guess, the first thing to
come to mind is that this map is surjective when `R = Matrix n n \bbk`, i.e., any star-algebra
automorphism in `Matrix n n \bbk` is unitarily inner (equal to `Unitary.toStarAlgAut u` for some
unitary `u`).
Jireh Loreaux [maintainer] — 16:00: @Kenny Lau when `R` is a C⋆-algebra, these are exactly the
inner ⋆-automorphisms of the algebra, so it's a very natural concept. Note that since `u` is
unitary, `star u = u⁻¹`, so this is just `u * x * u⁻¹`.
Kenny Lau — 16:27: maybe we can call it `inner` or `innerStarAlgEquiv`?
Monica Omar — 16:30: Maybe. I called it `Unitary.toStarAlgAut` because of docs#MulSemiringAction.toAlgAut
```
Three naming options were argued for the same concept: `toStarAlgAut` (by analogy with
`MulSemiringAction.toAlgAut`), `inner`/`innerStarAlgEquiv`, and the merged `conjStarAlgAut`
(S6). The thread also names "unitarily inner" as the surjectivity statement for matrices.

Also relevant: S3. Its neighbour names follow the pattern `eq_<equivKind>Conj<algEquivKind>`
(`eq_linearEquivConjAlgEquiv`, `eq_continuousLinearEquivConjContinuousAlgEquiv`). The
conjugations are `LinearEquiv.conjAlgEquiv` and `ContinuousLinearEquiv.conjContinuousAlgEquiv`
(S9, S10).

## 5. The API around the conjugation in (a)

**S9** · `library_example` · `Mathlib/Topology/Algebra/Module/StrongTopology.lean:805-824`
```
/-- A continuous linear equivalence of two spaces induces a continuous equivalence of algebras of
their endomorphisms. -/
def conjContinuousAlgEquiv (e : G ≃L[𝕜] H) : (G →L[𝕜] G) ≃A[𝕜] (H →L[𝕜] H) :=
  { e.arrowCongr e with
    map_mul' _ _ := by ext; simp
    commutes' _ := by ext; simp }

@[simp] theorem conjContinuousAlgEquiv_apply_apply (e : G ≃L[𝕜] H) (f : G →L[𝕜] G) (x : H) :
    e.conjContinuousAlgEquiv f x = e (f (e.symm x)) := rfl

theorem symm_conjContinuousAlgEquiv_apply_apply (e : G ≃L[𝕜] H) (f : H →L[𝕜] H) (x : G) :
    e.conjContinuousAlgEquiv.symm f x = e.symm (f (e x)) := rfl

theorem conjContinuousAlgEquiv_apply (e : G ≃L[𝕜] H) (f : G →L[𝕜] G) :
    e.conjContinuousAlgEquiv f = e ∘L f ∘L e.symm := rfl

@[simp] theorem symm_conjContinuousAlgEquiv (e : G ≃L[𝕜] H) :
    e.conjContinuousAlgEquiv.symm = e.symm.conjContinuousAlgEquiv := rfl

@[simp] theorem conjContinuousAlgEquiv_refl : conjContinuousAlgEquiv (.refl 𝕜 G) = .refl 𝕜 _ := rfl
```
The API that accompanies the neighbouring conjugation: pointwise and composite `apply` forms,
`symm`, `refl`, and (at lines 826–829) `trans`. The definition is built on the existing `arrowCongr`
with the extra fields filled in.

## 6. Registration with automation (simp lemmas)

**S10** · `counterexample` · `Mathlib/Algebra/Algebra/Equiv.lean:858`
```
@[simps!] def conjAlgEquiv (e : M₁ ≃ₗ[S] M₂) : Module.End S M₁ ≃ₐ[R] Module.End S M₂ where
```
The non-continuous neighbour generates its simp lemmas with `@[simps!]`. S9 writes them by hand
and marks only some `@[simp]`. These are two patterns for the same purpose.

Also relevant: S11, an instance that would supply order lemmas through a class rather than
stating them.

## 7. The order statement (c): whether it is needed, and its form

**S11** · `mechanism` · `Mathlib/Algebra/Order/Star/Basic.lean:452-465`
```
instance (priority := 100) StarRingHomClass.instOrderHomClass [FunLike F R S]
    [NonUnitalSemiring R] [StarRing R] [StarOrderedRing R] [NonUnitalSemiring S]
    [StarRing S] [StarOrderedRing S] [NonUnitalRingHomClass F R S]
    [NonUnitalStarRingHomClass F R S] : OrderHomClass F R S where
  map_rel f := (f : R →⋆ₙ+* S).map_le_map_of_map_star

instance (priority := 100) StarRingEquivClass.instOrderIsoClass [EquivLike F R S]
    [StarRingEquivClass F R S] : OrderIsoClass F R S where
  map_le_map_iff f x y := by
    refine ⟨fun h ↦ ?_, map_rel f⟩
    let f_inv : S →⋆ₙ+* R := (f : R ≃⋆+* S).symm
    have f_inv_f (r : R) : f_inv (f r) = r := EquivLike.inv_apply_apply f r
    rw [← f_inv_f x, ← f_inv_f y]
    exact NonUnitalStarRingHom.map_le_map_of_map_star f_inv h
```
Wherever both sides are `StarOrderedRing`, every star ring equivalence is already an
`OrderIsoClass`, so the iff `map_le_map_iff` comes from the class.

Also relevant:
- S5: `StarOrderedRing (H →L[𝕜] H)` is an instance only over ℂ, so S11 applies to operators
  directly only there.
- S7: an existing iff statement about positivity under conjugation by a `LinearIsometryEquiv`, on
  linear maps, valid for any `RCLike 𝕜`.

## 8. Placement

No source dedicated to this decision was found. The cross-references below are the only evidence
on placement.

Also relevant:
- S3: the existing pattern is one file per variant. The continuous version lives in
  `Analysis/Normed/Operator/` and points back to the algebraic version in
  `LinearAlgebra/GeneralLinearGroup/`.
- S4: a comment saying that operator C⋆-algebra material over ℂ sits late in the import hierarchy,
  for import reasons.
- S6: the unitary-element conjugation sits in `Algebra/Star/`.

## 9. The proof route

**S12** · `library_example` · `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:34-51`
```
  /- The proof goes as follows:
    We want to show the existence of a continuous linear equivalence `U : V ≃L[𝕜] W` such that
    `f A (U x) = U (A x)` for all `A : V →L[𝕜] V` and `x : V`.
    Assume nontriviality of `V`, and let `(u : V) ≠ 0`. Let `v` be a strong dual on `V` such that
    `v u ≠ 0` (exists since it has a separating dual).
    Let `z : W` such that `f (smulRight v u) z ≠ 0`.
    Then we construct a bijective continuous linear map `T : V →L[𝕜] W`
    given by `x ↦ f (smulRight v x) z` and so satisfies `T (A x) = f A (T x)` for all
    `A : V →L[𝕜] V` and `x : V`. So it remains to show that this map has a continuous inverse.
    Let `d` be a strong dual on `W` such that `d ((f (smulRight v u)) z) = 1` (exists since it has
    a separating dual).
    We then construct a right-inverse continuous linear map `T' : W →L[𝕜] V` given by
    `x ↦ f.symm (smulRight d x) u`.
    And so it follows that `T` is also a continuous linear equivalence. -/
  by_cases! hV : Subsingleton V
  · by_cases! hV : Subsingleton W
    · exact ⟨{ toLinearEquiv := 0 }, ext <| Subsingleton.allEq _ _⟩
    simpa using congr(f $(Subsingleton.allEq 0 1))
```
This is the route the neighbouring result takes: a rank-one construction. It handles the case
where V or W is the zero space separately, in its first lines, which bears on requirement 3.

Searches for base results stating that the centre of `V →L[𝕜] V`, or of `Module.End`, consists of
scalars found nothing. Such a result would let an operator that commutes with every operator be
rescaled to a scalar.

## 10. Scope of edits

No source dedicated to this decision was found, beyond the TODO below.

Also relevant: S3's TODO (lines 19–23). It asks for a surjectivity statement for the group
homomorphism from units when V = W, the continuous analogue of
`Module.End.mulSemiringActionToAlgEquiv_conjAct_surjective`. It is the one stated item of pending
work next to this result.
