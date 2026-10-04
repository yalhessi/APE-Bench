# The PR model for #33066 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Analysis/Normed/Operator): star-algebra equivalences between continuous endomorphisms are isometrically inner
- description: This is the star-algebra equivalence version of [AlgEquiv.eq_linearEquivConjAlgEquiv](https://leanprover-community.github.io/mathlib4_docs/Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.html#AlgEquiv.eq_linearEquivConjAlgEquiv) and [ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.html#ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv). So we now have a characterization of algebra, continuous algebra, and star-algebra equivalences between endomorphisms.

The proof follows the same idea as the one in #28972.

The proof of this is much longer than the `ContinuousAlgEquiv` and the `AlgEquiv` versions. Please feel free to golf!

The proof has private auxiliary lemmas and definitions because otherwise the proof gets too long and slow.

- [x] depends on: #33017
- [x] depends on: #33022
- changed files: Mathlib/Analysis/InnerProductSpace/Adjoint.lean, Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean, Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean, Mathlib/Topology/Algebra/Algebra/Equiv.lean

## Objects

### `LinearIsometryEquiv.conjStarAlgEquiv_refl` (theorem, added) [23c93cea30]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem conjStarAlgEquiv_refl : conjStarAlgEquiv (.refl 𝕜 H) = .refl := rfl
```

### `command in Adjoint.lean` (command, added) [2d681d88de]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- An isometry linear equivalence of two Hilbert spaces induces an equivalence of
⋆-algebras of their endomorphisms. -/
```

### `section in Adjoint.lean` (command, modified) [3211e98038]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:modified
- before the PR:
```lean
namespace ContinuousLinearMap
```
- as the PR leaves it:
```lean
section linearIsometryEquiv
```

### `LinearIsometryEquiv.conjStarAlgEquiv_apply_apply` (lemma, added) [469008037d]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma conjStarAlgEquiv_apply_apply (e : H ≃ₗᵢ[𝕜] K) (x : H →L[𝕜] H) (y : K) :
    e.conjStarAlgEquiv x y = e (x (e.symm y)) := rfl
```

### `namespace in Adjoint.lean` (command, added) [4c9eedf07b]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace LinearIsometryEquiv
```

### `LinearIsometryEquiv.conjStarAlgEquiv_trans` (theorem, added) [58e02a18ba]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem conjStarAlgEquiv_trans {G : Type*} [NormedAddCommGroup G] [InnerProductSpace 𝕜 G]
    [CompleteSpace G] (e : H ≃ₗᵢ[𝕜] K) (f : K ≃ₗᵢ[𝕜] G) :
    (e.trans f).conjStarAlgEquiv = e.conjStarAlgEquiv.trans f.conjStarAlgEquiv := rfl
```

### `LinearIsometryEquiv.conjStarAlgEquiv_apply` (lemma, added) [5c4cdf3bbd]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma conjStarAlgEquiv_apply (e : H ≃ₗᵢ[𝕜] K) (x : H →L[𝕜] H) :
    e.conjStarAlgEquiv x = e ∘L x ∘L e.symm := rfl
```

### `section in Adjoint.lean` (command, added) [a84d81f049]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end linearIsometryEquiv
```

### `LinearIsometryEquiv.symm_conjStarAlgEquiv` (lemma, added) [d9f14a95fb]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma symm_conjStarAlgEquiv (e : H ≃ₗᵢ[𝕜] K) :
    e.conjStarAlgEquiv.symm = e.symm.conjStarAlgEquiv := rfl
```

### `namespace in Adjoint.lean` (command, added) [e13ec88882]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open ContinuousLinearMap ContinuousLinearEquiv in
```

### `namespace in Adjoint.lean` (command, added) [e9c65dfafb]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace ContinuousLinearMap
```

### `LinearIsometryEquiv.symm_conjStarAlgEquiv_apply_apply` (theorem, added) [e9def9763b]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem symm_conjStarAlgEquiv_apply_apply (e : H ≃ₗᵢ[𝕜] K) (f : K →L[𝕜] K) (x : H) :
    e.conjStarAlgEquiv.symm f x = e.symm (f (e x)) := rfl
```

### `LinearIsometryEquiv.conjStarAlgEquiv` (def, added) [f3b8394e85]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def conjStarAlgEquiv (e : H ≃ₗᵢ[𝕜] K) : (H →L[𝕜] H) ≃⋆ₐ[𝕜] (K →L[𝕜] K) :=
  .ofAlgEquiv e.toContinuousLinearEquiv.conjContinuousAlgEquiv fun x ↦ by
    simp [star_eq_adjoint, conjContinuousAlgEquiv_apply, ← toContinuousLinearEquiv_symm, comp_assoc]
```

### `section in Adjoint.lean` (command, added) [fcbd8b133b]
- file: `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end LinearIsometryEquiv
```

### `declaration in ContinuousAlgEquiv.lean` (instance, added) [037e6736ef]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
public instance (priority := 100) {F : Type*} [EquivLike F (V →L[𝕜] V) (W →L[𝕜] W)]
    [NonUnitalAlgEquivClass F 𝕜 _ _] [StarHomClass F _ _] [ContinuousMapClass F _ _] :
    OrderIsoClass F _ _ where
  map_le_map_iff f x y := by
    obtain ⟨U, hU⟩ := StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
      (StarAlgEquivClass.toStarAlgEquiv f : _ ≃⋆ₐ[𝕜] _) (map_continuous f)
    have this a : f a = U.conjStarAlgEquiv a := by simpa using congr($hU a)
    simp_rw [le_def, ← _root_.map_sub, ← isPositive_toLinearMap_iff, this]
    exact LinearMap.isPositive_linearIsometryEquiv_conj_iff U
```

### `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv` (theorem, added) [14e57552db]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
public theorem ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv {𝕜 V W : Type*}
    [NontriviallyNormedField 𝕜] [SeminormedAddCommGroup V] [SeminormedAddCommGroup W]
    [NormedSpace 𝕜 V] [NormedSpace 𝕜 W] [SeparatingDual 𝕜 V] [SeparatingDual 𝕜 W]
    (f : (V →L[𝕜] V) ≃A[𝕜] (W →L[𝕜] W)) :
    ∃ U : V ≃L[𝕜] W, f = U.conjContinuousAlgEquiv := by
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
  simp_rw [ContinuousAlgEquiv.ext_iff, funext_iff, conjContinuousAlgEquiv_apply, ← comp_assoc,
    eq_comp_toContinuousLinearMap_symm]
  obtain ⟨u, hu⟩ := exists_ne (0 : V)
  obtain ⟨v, huv⟩ := SeparatingDual.exists_ne_zero (R := 𝕜) hu
  obtain ⟨z, hz⟩ : ∃ z : W, ¬ f (smulRight v u) z = (0 : W →L[𝕜] W) z := by
    rw [← not_forall, ← ContinuousLinearMap.ext_iff, map_eq_zero_iff, ContinuousLinearMap.ext_iff]
    exact not_forall.mpr ⟨u, huv.isUnit.smul_eq_zero.not.mpr hu⟩
  set T := apply' _ (.id 𝕜) z ∘L f.toContinuousAlgHom.toContinuousLinearMap ∘L smulRightL 𝕜 _ _ v
  have hT x : T x = f (smulRight v x) z := rfl
  have this A x : T (A x) = f A (T x) := by
    simp only [hT, ← mul_apply, ← map_mul]
    congr; ext; simp
  have ⟨d, hd⟩ := SeparatingDual.exists_eq_one (R := 𝕜) hz
  have surj : Function.Surjective T := fun w ↦ ⟨f.symm (smulRight d w) u, by simp [T, this, hd]⟩
  have inj : Function.Injective T := fun x y hxy ↦ by
    have h_smul : smulRight v x = smulRight v y := by
      apply f.injective <| ContinuousLinearMap.ext fun z ↦ ?_
      obtain ⟨w, rfl⟩ := surj z
      simp [← this, hxy]
    simpa [huv.isUnit.smul_left_cancel] using congr((fun f ↦ f u) $h_smul)
  set Tₗ : V ≃ₗ[𝕜] W := .ofBijective T.toLinearMap ⟨inj, surj⟩
  set T' := apply' _ (.id 𝕜) u ∘L f.symm.toContinuousAlgHom.toContinuousLinearMap ∘L
    smulRightL 𝕜 _ _ d
  set TL : V ≃L[𝕜] W := { Tₗ with
    continuous_toFun := T.continuous
    continuous_invFun := by
      change Continuous Tₗ.symm.toLinearMap
      suffices T'.toLinearMap = Tₗ.symm from this ▸ T'.continuous
      simp [LinearMap.ext_iff, ← Tₗ.injective.eq_iff, T', this, hT, hd, Tₗ] }
  exact ⟨TL, fun A ↦ (ContinuousLinearMap.ext <| this A).symm⟩
```

### `import in ContinuousAlgEquiv.lean` (import, modified) [194a03c241]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: imports:added

### `auxIsometry` (abbrev, added) [2313fe513a]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    V ≃ₗᵢ[𝕜] W where
  __ := auxContinuousLinearEquiv e hα hα2 he he' |>.toLinearEquiv
  norm_map' := by
    rw [ContinuousLinearEquiv.coe_toLinearEquiv, ← ContinuousLinearEquiv.coe_coe,
      norm_map_iff_adjoint_comp_self, coe_auxContinuousLinearEquiv,
      MulActionSemiHomClass.map_smulₛₗ]
    simp only [hαa, comp_smulₛₗ, RingHom.id_apply, smul_comp, smul_smul, hα2]
    simp [he, smul_smul, hα, one_def]
```

### `module_doc in ContinuousAlgEquiv.lean` (module_doc, modified) [29e91d1e54]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Continuous algebra equivalences between continuous endomorphisms are inner

This file shows that continuous algebra equivalences between continuous endomorphisms are inner.
See `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean` for the non-continuous version.
The proof follows the same idea as the non-continuous version.

# TODO:
- when `V = W`, we can state that the group homomorphism
  `(V →L[𝕜] V)ˣ →* ((V →L[𝕜] V) ≃A[𝕜] (V →L[𝕜] V))` is surjective,
  see `Module.End.mulSemiringActionToAlgEquiv_conjAct_surjective` for the non-continuous
  version of this.
-/
```
- as the PR leaves it:
```lean
/-!
# Continuous (star-)algebra equivalences between continuous endomorphisms are (isometrically) inner

This file shows that continuous (star-)algebra equivalences between continuous endomorphisms are
(isometrically) inner.
See `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean` for the non-continuous version.
The proof follows the same idea as the non-continuous version.

### TODO:
- when `V = W`, we can state that the group homomorphism
  `(V →L[𝕜] V)ˣ →* ((V →L[𝕜] V) ≃A[𝕜] (V →L[𝕜] V))` is surjective,
  see `Module.End.mulSemiringActionToAlgEquiv_conjAct_surjective` for the non-continuous
  version of this.
-/
```

### `coe_auxContinuousLinearEquiv` (theorem, added) [2f8e8d3ec4]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem coe_auxContinuousLinearEquiv :
    (auxContinuousLinearEquiv e hα hα2 he he').toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl
```

### `command in ContinuousAlgEquiv.lean` (command, added) [317781a525]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The ⋆-algebra equivalence version of
`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`.

TODO: remove the hypothesis `Continuous f`, as star-algebra equivalences between endomorphisms are
automatically continuous. -/
```

### `command in ContinuousAlgEquiv.lean` (command, added) [38c7bd91de]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Scalar multiple of a continuous linear equivalence (given certain properties are satisfied). -/
```

### `auxContinuousLinearEquiv` (abbrev, added) [5b6f14fda1]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable abbrev auxContinuousLinearEquiv :
    V ≃L[𝕜] W where
  toLinearMap := (α' • e.toContinuousLinearMap).toLinearMap
  invFun := (α' • e.toContinuousLinearMap.adjoint).toLinearMap
  left_inv x := by
    have := by simpa using congr($he x)
    simp [smul_smul, hα2, this, hα, ← mul_assoc]
  right_inv x := by
    have := by simpa using congr($he' x)
    simp [smul_smul, hα2, this, hα, ← mul_assoc]
  continuous_toFun := (α' • e.toContinuousLinearMap).continuous
  continuous_invFun := (α' • e.toContinuousLinearMap.adjoint).continuous
```

### `command in ContinuousAlgEquiv.lean` (command, added) [728e654d3d]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Construct an isometry linear equivalence from a continuous linear equivalence
and that its adjoint is a real-scalar multiple of its inverse. -/
```

### `coe_symm_auxIsometry` (theorem, added) [72959f6fd2]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem coe_symm_auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.symm.toContinuousLinearMap =
      α'⁻¹ • e.symm.toContinuousLinearMap := by
  ext y
  apply (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.injective
  simp [smul_smul, inv_mul_cancel₀ (a := α') (by grind)]
```

### `section in ContinuousAlgEquiv.lean` (command, added) [883321af9b]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section auxiliaryDefs
```

### `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` (theorem, added) [b32ffcc769]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
public theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) (hf : Continuous f) :
    ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv := by
  /- Assume nontriviality of `V`.
    Then by `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`,
    we know there exists a continuous linear equivalence `y : V ≃L[𝕜] W` such that
    `f = y.conjAlgEquiv`.
    Our goal will be to construct an isometry from `y`. We do this by first showing
    `adjoint y ∘ y` is in the center of the endormorphisms, and as the algebra of endomorphisms
    are central, `adjoint y ∘ y` is a scalar multiple of the identity.
    Let `α : 𝕜` be that scalar, i.e., `adjoint y ∘ y = α • id`. This scalar is clearly real.
    Also, it's easy to see that `adjoint y ∘ y` is invertible, so `α ≠ 0`.
    As `adjoint y ∘ y` is positive, we get `0 < α`.
    We also get `y ∘ adjoint y = α • id`.
    Finally, we construct our isometry `1/√(re α) • y`. -/
  by_cases! hV : Subsingleton V
  · by_cases! hV : Subsingleton W
    · use { toLinearEquiv := 0, norm_map' _ := by simp [Subsingleton.eq_zero] }
      exact ext fun _ ↦ Subsingleton.allEq _ _
    simpa using congr(f $(Subsingleton.allEq 0 1))
  obtain ⟨y, hy⟩ := (ContinuousAlgEquiv.ofAlgEquiv f.toAlgEquiv hf
    (f.toAlgEquiv.toLinearEquiv.continuous_symm hf)).eq_continuousLinearEquivConjContinuousAlgEquiv
  have (x : V →L[𝕜] V) : adjoint (f x) = f (adjoint x) := map_star _ _ |>.symm
  rw [ContinuousAlgEquiv.ext_iff] at hy
  simp_rw [← StarAlgEquiv.coe_toAlgEquiv, ContinuousAlgEquiv.coe_ofAlgEquiv f.toAlgEquiv hf _ ▸ hy,
    conjContinuousAlgEquiv_apply,  adjoint_comp] at this
  replace this (x : V →L[𝕜] V) : adjoint y.toContinuousLinearMap ∘L y ∘L adjoint x ∘L y.symm =
      adjoint x ∘L adjoint y.toContinuousLinearMap := by
    simp_rw [← this x, ← comp_assoc, ← adjoint_comp]
    simp
  replace this (x : V →L[𝕜] V) : Commute x (adjoint y.toContinuousLinearMap ∘L y) := by
    simp_rw [commute_iff_eq, mul_def, ← comp_assoc, ← (adjoint_adjoint x ▸ this _), comp_assoc]
    simp
  replace this := (Subalgebra.mem_center_iff (R := 𝕜)).mpr fun _ ↦ this _
  simp only [Algebra.IsCentral.center_eq_bot] at this
  obtain ⟨α, hα⟩ := this
  simp only [AlgHom.toRingHom_eq_coe, Algebra.toRingHom_ofId, Algebra.algebraMap_eq_smul_one] at hα
  have this : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
    isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
      simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
        ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
  have thisα : α = RCLike.re α := by
    have this10 := by simpa [IsSelfAdjoint, ← hα, one_def, star_eq_adjoint] using
      (IsSelfAdjoint.one (W →L[𝕜] W)).adjoint_conj y.toContinuousLinearMap
    rwa [← one_def, (smul_left_injective 𝕜 one_ne_zero).eq_iff, RCLike.conj_eq_iff_re,
      eq_comm] at this10
  have thisα' : α ≠ 0 := fun h ↦ by simp [h, ← hα] at this
  have this2 : 0 ≤ α := by
    have this1 := thisα.symm ▸ (nonneg_iff_isPositive _ |>.mpr
      (thisα ▸ hα ▸ isPositive_adjoint_comp_self y.toContinuousLinearMap))
    rw [← LinearMap.isPositive_one.isPositive_smul_iff (E := V) (one_ne_zero' (V →ₗ[𝕜] V))]
    exact (nonneg_iff_isPositive _).mp this1
  replace this2 := RCLike.ofReal_pos.mp <| thisα ▸ (lt_of_le_of_ne' this2 thisα')
  have thisU : y.toContinuousLinearMap ∘L adjoint y.toContinuousLinearMap =
      α • ContinuousLinearMap.id 𝕜 _ := by
    ext x
    simpa using congr(y (($hα ∘L y.symm.toContinuousLinearMap) x)).symm
  set αa := (((RCLike.re α : ℝ) ^ (-(1 / 2 : ℝ)) : ℝ) : 𝕜)
  have αa2 : αa * αa = α⁻¹ := by
    rw [thisα]
    norm_num [αa, ← RCLike.ofReal_mul, ← Real.rpow_add this2, Real.rpow_neg_one]
  set U := auxIsometry y thisα' αa2 hα.symm thisU (by simp [αa])
  use U
  have la : αa⁻¹ * αa = 1 := by
    refine inv_mul_cancel₀ ?_
    simp only [αa, ne_eq, map_eq_zero]
    rw [Real.rpow_eq_zero this2.le (by simp)]
    exact ne_of_gt this2
  ext
  simp [U.conjStarAlgEquiv_apply, U, smul_smul, la, ← conjContinuousAlgEquiv_apply, ← hy]

/- TODO: Remove instance when we have `StarOrderedRing (V →L[𝕜] V)` since
this then becomes an instance from `StarRingEquivClass.instOrderIsoClass`. -/
```

### `section in ContinuousAlgEquiv.lean` (command, added) [cae67aad8f]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {𝕜 V W : Type*} [RCLike 𝕜] [NormedAddCommGroup V] [InnerProductSpace 𝕜 V] [CompleteSpace V]
  [NormedAddCommGroup W] [InnerProductSpace 𝕜 W] [CompleteSpace W]
```

### `section in ContinuousAlgEquiv.lean` (command, added) [e65283c63a]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)
  (hα2 : α' * α' = α⁻¹) (he : e.toContinuousLinearMap.adjoint ∘L e = α • .id 𝕜 V)
  (he' : e ∘L e.toContinuousLinearMap.adjoint = α • .id 𝕜 W)
include hα hα2 he he'
```

### `coe_auxIsometry` (theorem, added) [edaddf3030]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem coe_auxIsometry (hαa : starRingEnd 𝕜 α' = α') :
    (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.toContinuousLinearMap =
      α' • e.toContinuousLinearMap := rfl
```

### `section in ContinuousAlgEquiv.lean` (command, added) [f1f6e3e865]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end auxiliaryDefs
```

### `namespace in ContinuousAlgEquiv.lean` (command, added) [fa74711ad6]
- file: `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open ComplexOrder
```

### `module_doc in AlgEquiv.lean` (module_doc, added) [9cc3c5d48b]
- file: `Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Algebra automorphisms in `End K V` are inner

This file shows that given any algebra equivalence `f : End K V ≃ₐ[K] End K V`,
there exists a linear equivalence `T : V ≃ₗ[K] V` such that `f x = T ∘ₗ x ∘ₗ T.symm`.
In other words, the map `MulSemiringAction.toAlgEquiv` from `GeneralLinearGroup K V` to
`End K V ≃ₐ[K] End K V` is surjective.

For the continuous versions, see `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`.
-/
```

### `command in Equiv.lean` (command, added) [0d96f0973e]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Interpret an algebra equivalence as a continuous algebra equivalence when it is continuous. -/
```

### `ContinuousAlgEquiv.coe_ofAlgEquiv` (theorem, added) [21ec312bd6]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem coe_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') : ⇑(ofAlgEquiv e he he') = e := rfl
```

### `ContinuousAlgEquiv.symm_ofAlgEquiv` (theorem, added) [600f9856d9]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem symm_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') :
    (ofAlgEquiv e he he').symm = ofAlgEquiv e.symm he' he := rfl
```

### `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv` (theorem, added) [781597936a]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem toAlgEquiv_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') :
    (ofAlgEquiv e he he').toAlgEquiv = e := rfl
```

### `ContinuousAlgEquiv.ofAlgEquiv` (def, added) [798036c2ad]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) : A ≃A[R] B :=
  { e with continuous_toFun := he, continuous_invFun := he' }
```

### `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv` (theorem, added) [85656f2226]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem ofAlgEquiv_trans_ofAlgEquiv (f : A ≃ₐ[R] B) (g : B ≃ₐ[R] C) (hf hf' hg hg') :
    (ofAlgEquiv f hf hf').trans (ofAlgEquiv g hg hg') =
      ofAlgEquiv (f.trans g) (hg.comp hf) (hf'.comp hg') := rfl
```

### `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv` (theorem, added) [8f715d2513]
- file: `Mathlib/Topology/Algebra/Algebra/Equiv.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] theorem ofAlgEquiv_toAlgEquiv (e : A ≃A[R] B) :
    ofAlgEquiv e.toAlgEquiv e.continuous e.continuous_symm = e := rfl
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `LinearIsometryEquiv.symm_conjStarAlgEquiv`, `LinearIsometryEquiv.symm_conjStarAlgEquiv_apply_apply` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `LinearIsometryEquiv.conjStarAlgEquiv`, `LinearIsometryEquiv.conjStarAlgEquiv_apply`, `LinearIsometryEquiv.conjStarAlgEquiv_apply_apply`, `LinearIsometryEquiv.conjStarAlgEquiv_refl`, `LinearIsometryEquiv.conjStarAlgEquiv_trans` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `ContinuousAlgEquiv.ofAlgEquiv`, `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv`, `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `ContinuousAlgEquiv.coe_ofAlgEquiv`, `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv`, `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv`, `ContinuousAlgEquiv.symm_ofAlgEquiv`, `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `auxIsometry`, `coe_auxIsometry`, `coe_symm_auxIsometry` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `LinearIsometryEquiv.conjStarAlgEquiv_refl`, `LinearIsometryEquiv.conjStarAlgEquiv_trans` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `LinearIsometryEquiv.conjStarAlgEquiv_apply`, `LinearIsometryEquiv.symm_conjStarAlgEquiv` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `ContinuousAlgEquiv.coe_ofAlgEquiv` -> `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv` -> `ContinuousAlgEquiv.symm_ofAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv` -> `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv` -> `ContinuousAlgEquiv.symm_ofAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.symm_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.symm_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv`
- changed_siblings [high]: `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv` -> `ContinuousAlgEquiv.coe_ofAlgEquiv`
- changed_siblings [high]: `LinearIsometryEquiv.conjStarAlgEquiv_apply` -> `LinearIsometryEquiv.symm_conjStarAlgEquiv`
- changed_siblings [high]: `LinearIsometryEquiv.conjStarAlgEquiv_refl` -> `LinearIsometryEquiv.conjStarAlgEquiv_trans`
- changed_siblings [high]: `LinearIsometryEquiv.conjStarAlgEquiv_trans` -> `LinearIsometryEquiv.conjStarAlgEquiv_refl`
- changed_siblings [high]: `LinearIsometryEquiv.symm_conjStarAlgEquiv` -> `LinearIsometryEquiv.conjStarAlgEquiv_apply`
- changed_siblings [high]: `coe_auxIsometry` -> `coe_symm_auxIsometry`
- changed_siblings [high]: `coe_symm_auxIsometry` -> `coe_auxIsometry`
- declaration_dependency [exact]: `ContinuousAlgEquiv.coe_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- declaration_dependency [exact]: `ContinuousAlgEquiv.ofAlgEquiv_toAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- declaration_dependency [exact]: `ContinuousAlgEquiv.ofAlgEquiv_trans_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- declaration_dependency [exact]: `ContinuousAlgEquiv.symm_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- declaration_dependency [exact]: `ContinuousAlgEquiv.toAlgEquiv_ofAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.conjStarAlgEquiv_apply` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.conjStarAlgEquiv_apply_apply` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.conjStarAlgEquiv_refl` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.conjStarAlgEquiv_trans` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.symm_conjStarAlgEquiv` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `LinearIsometryEquiv.symm_conjStarAlgEquiv_apply_apply` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- declaration_dependency [exact]: `coe_auxContinuousLinearEquiv` -> `auxContinuousLinearEquiv`
- declaration_dependency [exact]: `coe_auxIsometry` -> `auxIsometry`
- declaration_dependency [exact]: `coe_symm_auxIsometry` -> `auxIsometry`
- direct_use_of_changed_declaration [exact]: `LinearIsometryEquiv.conjStarAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- direct_use_of_changed_declaration [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `LinearIsometryEquiv.conjStarAlgEquiv_apply`
- direct_use_of_changed_declaration [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`
- direct_use_of_changed_declaration [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `auxIsometry`
- direct_use_of_changed_declaration [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `ContinuousAlgEquiv.ofAlgEquiv`
- direct_use_of_changed_declaration [exact]: `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv` -> `ContinuousAlgEquiv.coe_ofAlgEquiv`
- direct_use_of_changed_declaration [exact]: `auxIsometry` -> `coe_auxContinuousLinearEquiv`
- direct_use_of_changed_declaration [exact]: `auxIsometry` -> `auxContinuousLinearEquiv`
- direct_use_of_changed_declaration [exact]: `coe_symm_auxIsometry` -> `auxIsometry`
- direct_use_of_changed_declaration [exact]: `declaration in ContinuousAlgEquiv.lean` -> `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`
- direct_use_of_changed_declaration [exact]: `declaration in ContinuousAlgEquiv.lean` -> `LinearIsometryEquiv.conjStarAlgEquiv`
- name_family [high]: `auxIsometry` -> `coe_auxIsometry`
- name_family [high]: `auxIsometry` -> `coe_symm_auxIsometry`
- name_family [high]: `coe_auxIsometry` -> `coe_symm_auxIsometry`
- name_family [high]: `coe_auxIsometry` -> `auxIsometry`
- name_family [high]: `coe_symm_auxIsometry` -> `auxIsometry`
- name_family [high]: `coe_symm_auxIsometry` -> `coe_auxIsometry`
