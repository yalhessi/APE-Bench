# Sketch: ⋆-isomorphisms `B(V) ≃ B(W)` are implemented by unitaries

Setting (unchecked): `[RCLike 𝕜]`, `V W` with `[NormedAddCommGroup _] [InnerProductSpace 𝕜 _] [CompleteSpace _]`.

## 1. Which isomorphisms (b) covers
**Choice:** every `f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)`, no continuity hypothesis (reading (i)). The route in 6 uses only the algebra and star structure and yields an isometry, so continuity is a consequence.
**Alternatives:** unbundled `(hf : Continuous f)` (S2); `f : ≃A[𝕜]` plus a `map_star` hypothesis (S3's form; no bundled continuous ⋆-equivalence exists); ℂ only, continuity from `StarAlgEquiv.isometry` (S1).
**References:** S1–S3; `ContinuousAlgEquiv.lean:29-33`.
**What would decide it:** whether route 6 compiles; if so, a continuity hypothesis is unused.

## 2. Scalar field
**Choice:** `RCLike 𝕜`.
**Alternatives:** ℂ only, where S1/S11 give continuity and (c) for free.
**References:** `Adjoint.lean:51`, `:201-215` (star on `E →L[𝕜] E` for any `RCLike 𝕜`, given `CompleteSpace`, `:64`); S4, S5.
**What would decide it:** nothing in route 6 is ℂ-specific.

## 3. The unitary and the conjugation (a)
**Choice:** a unitary is `U : V ≃ₗᵢ[𝕜] W`;
```lean
-- unchecked
/-- A linear isometry equivalence induces the ⋆-algebra equivalence `A ↦ e ∘L A ∘L e.symm`. -/
def LinearIsometryEquiv.conjStarAlgEquiv (e : V ≃ₗᵢ[𝕜] W) :
    (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W) where
  __ := e.toContinuousLinearEquiv.conjContinuousAlgEquiv
  map_star' A := by ext; simp [star_eq_adjoint, conjContinuousAlgEquiv_apply]
```
**Alternatives:** a unitary element with `Unitary.conjStarAlgAut` (S6; V = W only); `U : V ≃L[𝕜] W` with `adjoint U = U.symm`; an unbundled composite (S7). Names `innerStarAlgEquiv`, `toStarAlgAut` (S8).
**References:** `Adjoint.lean:659-664` (`adjoint_eq_symm`, gives `map_star'`), `:696` (unitary elements ≃ `H ≃ₗᵢ H`); S9, S10 (`conj…` names).
**What would decide it:** V ≠ W excludes unitary elements; the name follows both neighbours.

## 4. API around (a)
**Choice:** hand-written as in S9: `conjStarAlgEquiv_apply` (`= e ∘L A ∘L e.symm`, rfl), `@[simp]` `conjStarAlgEquiv_apply_apply`, `symm_conjStarAlgEquiv`, `conjStarAlgEquiv_refl`; `conjStarAlgEquiv_trans`; for V = W, `Unitary.conjStarAlgAut 𝕜 _ u = (Unitary.linearIsometryEquiv u).conjStarAlgEquiv`.
**Alternatives:** `@[simps!]` (S10), whose `apply` lemma would go through the parent structure.
**References:** S9, S10, S6; `Adjoint.lean:696-726`.
**What would decide it:** the simp normal form; how much `trans`/bridge API is wanted now is open.

## 5. Statement and name of (b)
**Choice:**
```lean
-- unchecked
theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) : ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv
```
**Alternatives:** `∃ U, ∀ A, f A = U ∘L A ∘L U.symm`; a class-generic `f : F` (S1's style).
**References:** `ContinuousAlgEquiv.lean:29-33`, `AlgEquiv.lean:28-29` (direction, name pattern).
**What would decide it:** sitting beside the two neighbours, as the brief requires.

## 6. Proof route for (b)
**Choice:** direct rank-one construction with normalised vectors. Subsingleton cases as in `ContinuousAlgEquiv.lean:48-51`. Else take `‖u‖ = 1`, `p := toSpanSingleton 𝕜 u ∘L innerSL 𝕜 u`; `f p ≠ 0`, so normalise some `f p w` to `z` (`f p z = z`, `‖z‖ = 1`). Put `T x := f (toSpanSingleton 𝕜 x ∘L innerSL 𝕜 u) z`. Then `T (A x) = f A (T x)`; as `(|x⟩⟨u|)† ∘L |y⟩⟨u| = ⟪x, y⟫ • p` and `f` preserves star, `⟪T x, T y⟫ = ⟪x, y⟫`; `T` is onto via `f.symm (toSpanSingleton 𝕜 w ∘L innerSL 𝕜 z) u`. Conclude with `LinearIsometryEquiv.ofSurjective` (recalled).
**Alternatives:** apply S3 (needs both directions continuous, so reading (ii)), then show `U† ∘L U` commutes with every operator, hence is a positive scalar, and rescale; no centre-is-scalars lemma exists (S12).
**References:** `ContinuousAlgEquiv.lean:54-71`; `Adjoint.lean:254-264` (adjoints of `innerSL`, `toSpanSingleton`).
**What would decide it:** compiled length; the direct route also removes 1's hypothesis.

## 7. Order statement (c)
**Choice:** include it over `RCLike 𝕜` as an instance `OrderIsoClass ((V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) _ _`, from (b) and positivity under conjugation by a linear isometry, so `map_le_map_iff f` works for every `𝕜`.
**Alternatives:** a named lemma `f A ≤ f B ↔ A ≤ B`; omitting it, since over ℂ it already is `map_le_map_iff` (S11 with S5's instance).
**References:** S11, S5, S7; recalled CLM analogue `IsPositive.conj_adjoint`.
**What would decide it:** whether real Hilbert spaces matter; once `StarOrderedRing (H →L[𝕜] H)` is an instance for all `RCLike 𝕜` (S5), S11 covers it and (c) should go.

## 8. Placement
**Choice:** (a) and API in `Adjoint.lean`'s `Unitary` section after `:669`; (b), (c) in a new `Mathlib/Analysis/InnerProductSpace/` file importing `Positive`, with "see also" lines in the module docs of `ContinuousAlgEquiv.lean:12-17` and `AlgEquiv.lean:13-20`.
**Alternatives:** (b) appended to `ContinuousAlgEquiv.lean`, importing inner-product theory into `Analysis/Normed/Operator/`; (b) in `Adjoint.lean`.
**References:** S3's one-file-per-variant pattern; S4; `ContinuousAlgEquiv.lean:8-10`.
**What would decide it:** import cost and maintainer preference; open.

## 9. Scope
**Choice:** add the V = W corollary `Function.Surjective (Unitary.conjStarAlgAut 𝕜 (H →L[𝕜] H))`, the ⋆-analogue of `AlgEquiv.lean:54-59`. Leave `Topology/Algebra/Algebra/Equiv.lean` unchanged: route 6 needs no `≃A` constructor. Fix the stale `eq_linearEquivAlgConj` at `AlgEquiv.lean:53` only if that file is edited anyway.
**Alternatives:** no corollary; corollary and fix in a separate PR.
**References:** S8 ("unitarily inner"), S3's TODO (`ContinuousAlgEquiv.lean:19-23`), `Adjoint.lean:667`.
**What would decide it:** open.
