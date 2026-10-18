# 47 asks

## d0019  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:171  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α]
```
```
@@ -166,6 +166,100 @@ theorem Dense.isGLB_inter_iff {α : Type*} [TopologicalSpace α] [Preorder α] [
     IsGLB (t ∩ s) x ↔ IsGLB t x :=
   hs.isLUB_inter_iff (α := αᵒᵈ) ht
 
+/-- The upper bounds of the image of a continuous function on a dense set is equal to the upper
+bounds of the range of the universe. -/
+theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
```

## d0032  PR 33149 (human) — feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
None:None  kind=review  by grunweg  family=F12 PR level
**ASK:** Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) Please make this abundantly clear in the PR description, so we can review it properly.

Sadly, this PR shows some common weaknesses of AI-generated code (no matter how you generated it). Introducing additional axioms is a no go. Your code introduces lots of new definitions without supporting lemmas (that is not maintainable; please add basic lemmas about them when adding them).

Please address these issues; only then can we consider this PR for merging.
```

```

## d0012  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:324  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
lemma encard_le_of_isSeparated (h_subset : C ⊆ A)
```
```
Set ε A : Set X) := by
+  by_cases h : packingNumber ε A ≠ ⊤
+  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.1
+  · simp only [maximalSeparatedSet, h, dite_false, IsSeparated.empty]
+
+lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
+    (maximalSeparatedSet ε A).encard = packingNumber ε A := by
+  simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+  exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.2
+
+lemma card_le_of_isSeparated (h_subset : C ⊆ A)
```

## d0047  PR 33362 (human) — [Merged by Bors] - feat: weaken assumptions in Schwarz lemma
Mathlib/Analysis/Complex/Schwarz.lean:58  kind=review_comment  by vihdzp  family=F9 formatting
**ASK:** Why not move these a few lines below so that it's on the `Complex` namespace?
```
oped Topology
-
-namespace Complex
-
-section Space
+open scoped Topology ComplexConjugate
 
-variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℂ E] {R₁ R₂ : ℝ} {f : ℂ → E}
+variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℂ E] {R R₁ R₂ : ℝ} {f : ℂ → E}
   {c z z₀ : ℂ}
 
 /-- An auxiliary lemma for `Complex.norm_dslope_le_div_of_mapsTo_ball`. -/
-theorem schwarz_aux {f : ℂ → ℂ} (hd : DifferentiableOn ℂ f (ball c R₁))
-    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (hz : z ∈ ball c R₁) :
+private theorem Complex.schwarz_aux {f : ℂ → ℂ} (hd : DifferentiableOn ℂ f (ball c R₁))
```

## d0044  PR 33321 (human) — [Merged by Bors] - feat: linear independence of indecomposable roots of a root s
Mathlib/LinearAlgebra/RootSystem/BaseExists.lean:19  kind=review_comment  by jcommelin  family=F10 documentation
**ASK:** ```suggestion
The proof needs a set of ordered coefficients, even though the ultimate existence statement does
```
```
ghts reserved.
+Released under Apache 2.0 license as described in the file LICENSE.
+Authors: Oliver Nash
+-/
+module
+
+public import Mathlib.Algebra.Group.Irreducible.Indecomposable
+public import Mathlib.Algebra.Module.Submodule.Union
+public import Mathlib.LinearAlgebra.Dimension.OrzechProperty
+public import Mathlib.LinearAlgebra.QuadraticForm.Dual
+public import Mathlib.LinearAlgebra.RootSystem.Base
+
+/-!
+# Existence of bases for crystallographic root systems
+
+## Implementation details
+
+The proof needs a set of ordered coefficients, even though the existence ultimate statement does
```

## d0029  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
None:None  kind=review  by j-loreaux  family=F6 statement and API design
**ASK:** I suggest turning the declarations involving `iSup` and `iInf` around so that they read:
```lean
    ⨆ s : S, f s = ⨆ i, f i := by
```
instead.
```

```

## d0039  PR 33294 (human) — [Merged by Bors] - refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`
Mathlib/SetTheory/Ordinal/Topology.lean:186  kind=review_comment  by YaelDillies  family=F1 proof
**ASK:** ```suggestion
    rw [h.map_iSup (bddAbove_of_small _)]
```
no?

```
@@ -178,12 +178,12 @@ theorem enumOrd_isNormal_iff_isClosed (hs : ¬ BddAbove s) :
   have Hs := enumOrd_strictMono hs
   refine
     ⟨fun h => isClosed_iff_iSup.2 fun {ι} hι f hf => ?_, fun h =>
-      (isNormal_iff_strictMono_limit _).2 ⟨Hs, fun a ha o H => ?_⟩⟩
+      isNormal_iff.2 ⟨Hs, fun a ha o H => ?_⟩⟩
   · let g : ι → Ordinal.{u} := fun i => (enumOrdOrderIso s hs).symm ⟨_, hf i⟩
     suffices enumOrd s (⨆ i, g i) = ⨆ i, f i by
       rw [← this]
       exact enumOrd_mem hs _
-    rw [IsNormal.map_iSup h g]
+    rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]
```

## d0024  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:217  kind=review_comment  by j-loreaux  family=F4 derive, don't restate
**ASK:** ```suggestion
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup (α := αᵒᵈ) hf h
```
```
set is equal to the infimum on
+the universe. -/
+theorem Dense.continuous_inf {α : Type*} [TopologicalSpace α]
+    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
+    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
+    ⨅ i, f i = ⨅ s : S, f s := by
+  rw [← sInf_range, ← sInf_range]
+  obtain (_ | _) := isEmpty_or_nonempty γ
+  · simp [Set.range_eq_empty]
+  refine (isGLB_csInf (range_nonempty f) h).unique ?_
+  refine (isGLB_congr (hS.continuous_lowerBounds hf)).mp (isGLB_ciInf_set ?_ hS.nonempty)
+  exact h.mono (by grind)
```

## d0013  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:310  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`.
```lean
  intro x hxA
  by_contra! h_dist
  let C := {x} ∪ maximalSeparatedSet ε A
  have hx_not_mem : x ∉ maximalSeparatedSet ε A := by simpa using h_dist x
  suffices C ⊆ A ∧ IsSeparated ε C by
    refine absurd (encard_le_of_isSeparated this.1 this.2 h) ?_
    simp [C, encard_insert_of_notMem hx_not_mem,
      ENat.lt_add_one_iff (encard_maximalSeparatedSet h ▸ h)]
  constructor
  · simp [C, hxA, maximalSeparatedSet_subset, Set.insert_subset]
  · exact isSeparated_insert_of_notMem hx_not_mem |>.mpr
      ⟨isSeparated_maximalSeparatedSet, by simpa using h_dist⟩
```
```
ε A := by
+  simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+  exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.2
+
+lemma card_le_of_isSeparated (h_subset : C ⊆ A)
+    (h_sep : IsSeparated ε C) (h : packingNumber ε A ≠ ⊤) :
+    C.encard ≤ (maximalSeparatedSet ε A).encard := by
+  rw [card_maximalSeparatedSet h]
+  exact le_iSup_of_le C <| le_iSup_of_le h_subset <| le_iSup_of_le h_sep (by simp)
+
+/-- The maximal separated set is a cover. -/
+lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
+    IsCover ε A (maximalSeparatedSet ε A) := by
```

## d0021  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:191  kind=review_comment  by j-loreaux  family=F4 derive, don't restate
**ASK:** There's a trick you can use for this kind of thing by using the `OrderDual`.
```suggestion
    lowerBounds (f '' S) = lowerBounds (range f) :=
  hS.continuous_upperBounds (α := αᵒᵈ) hf
```
```
lower
+bounds of the range of the universe. -/
+theorem Dense.continuous_lowerBounds {α : Type*} [TopologicalSpace α] [Preorder α]
+    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
+    (hf : Continuous f) :
+    lowerBounds (f '' S) = lowerBounds (range f) := by
+  refine subset_antisymm ?_ fun _ => lowerBounds_mono (Set.image_subset_range f S) le_rfl
+  refine subset_trans ?_ fun _ => lowerBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl
+  intro x hx i hi
+  rw [mem_closure_iff_frequently] at hi
+  exact (hi.mono hx).mem_of_closed isClosed_Ici
```

## d0051  PR 33421 (human) — [Merged by Bors] - chore(Algebra/Order/Floor): review API about `round`
Mathlib/Algebra/Order/Floor/Ring.lean:277  kind=review_comment  by eric-wieser  family=F7 generality
**ASK:** Better I think as
```suggestion
theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :
    k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by
  rw [fract, mul_sub, sub_eq_iff_eq_add']
  refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩
  rintro ⟨n, hn⟩
  convert hn
  have hk0 : 0 < (k : R) := zero_le_one.trans_lt hk
  rw [floor_eq_iff, ← mul_le_mul_iff_right₀ hk0, ← mul_lt_mul_iff_right₀ hk0, hn]
  simp [mul_add, hk]
```
```
@@ -267,6 +267,15 @@ theorem mul_cast_floor_div_cancel_of_pos {n : ℤ} (hn : 0 < n) (a : R) : ⌊a *
 theorem mul_natCast_floor_div_cancel {n : ℕ} (hn : n ≠ 0) (a : R) : ⌊a * n⌋ / n = ⌊a⌋ := by
   simpa using mul_cast_floor_div_cancel_of_pos (n := n) (by positivity) a
 
+theorem two_mul_fract_eq_one_iff_exists_int {x : R} :
+    2 * fract x = 1 ↔ ∃ n : ℤ, 2 * x = 2 * n + 1 := by
+  rw [fract, mul_sub, sub_eq_iff_eq_add']
+  refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩
+  rintro ⟨n, hn⟩
+  convert hn
+  rw [floor_eq_iff, ← mul_le_mul_iff_right₀ two_pos, ← mul_lt_mul_iff_right₀ two_pos, hn]
+  simp [mul_add]
```

## d0026  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:239  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** It's easier if you case split on whether the range of the function from the subtype is bounded above or not.
```suggestion
  by_cases h : BddAbove (range (fun x : S ↦ f x))
  · refine hS.ciSup hf <| h.closure.mono ?_
    simpa [← Function.comp_def, range_comp] using hf.range_subset_closure_image_dense hS
  · suffices ¬ BddAbove (range f) by simp [ciSup_of_not_bddAbove, this, h]
    contrapose h
    exact h.mono fun _ ↦ by aesop
```
```
 (range f)
+  · refine (isLUB_csSup (range_nonempty f) h1).unique ?_
+    refine (isLUB_congr (hS.continuous_upperBounds hf)).mp (isLUB_ciSup_set ?_ hS.nonempty)
+    exact h1.mono (by grind)
+  · have h2 : ¬ BddAbove (range (fun s : S => f (Subtype.val s))) := by
+      intro h
+      have := range_comp' f (Subtype.val : S → γ)
+      simp_all only [Subtype.range_coe_subtype, setOf_mem_eq]
+      have := h.closure.mono (image_closure_subset_closure_image hf)
+      simp only [hS.closure_eq, image_univ] at this
+      exact h1 this
+    simp [csSup_of_not_bddAbove h1, csSup_of_not_bddAbove h2]
```

## d0048  PR 33421 (human) — [Merged by Bors] - chore(Algebra/Order/Floor): review API about `round`
Mathlib/Algebra/Order/Round.lean:51  kind=review_comment  by Ruben-VandeVelde  family=F8 naming
**ASK:** How about `round_eq_div`?
```
@@ -45,6 +45,26 @@ variable [Ring α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 def round (x : α) : ℤ :=
   if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
 
+/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.
+
+TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
+theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
```

## d0036  PR 33285 (human) — [Merged by Bors] - chore(*): golf, add missing lemmas
Mathlib/RingTheory/Ideal/Cotangent.lean:158  kind=review_comment  by themathqueen  family=F1 proof
**ASK:** or
```lean
  simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]
```
or
```lean
  exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)
```
```
ib4/pull/8386 had to specify `(R₂ := R)` because `I.toCotangent` suggested `R ⧸ I^2` instead
-    I.cotangentEquivIdeal.symm ⟨(I ^ 2).mkQ x,
-      -- timeout (200000 heartbeats) without `by exact`
-      by exact Submodule.mem_map_of_mem (F := R →ₗ[R] R ⧸ I ^ 2) (f := (I ^ 2).mkQ) hx⟩ =
-      I.toCotangent (R := R) ⟨x, hx⟩ := by
-  apply I.cotangentEquivIdeal.injective
-  rw [I.cotangentEquivIdeal.apply_symm_apply]
+    I.cotangentEquivIdeal.symm ⟨(I ^ 2).mkQ x, Submodule.mem_map_of_mem hx⟩ =
+      I.toCotangent ⟨x, hx⟩ := by
+  rw [I.cotangentEquivIdeal.symm_apply_eq]
   ext
-  rfl
+  simp
```

## d0046  PR 33337 (human) — [Merged by Bors] - chore(Analysis/InnerProductSpace/Projection/Submodule): renam
Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean:209  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] :
```
```
pl
+  LinearMap.ext <| orthogonalProjection_apply_eq_linearProjOfIsCompl
 
 @[deprecated (since := "2025-07-11")] alias orthogonalProjection_coe_linearMap_eq_linearProj :=
-  orthogonalProjection_coe_eq_linearProjOfIsCompl
+  coe_orthogonalProjection_eq_linearProjOfIsCompl
+@[deprecated (since := "2025-12-26")] alias orthogonalProjection_coe_eq_linearProjOfIsCompl :=
+  coe_orthogonalProjection_eq_linearProjOfIsCompl
 
 open Submodule in
-theorem starProjection_coe_eq_isCompl_projection [K.HasOrthogonalProjection] :
+theorem coe_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] :
```

## d0002  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Topology/Algebra/Algebra/Equiv.lean:307  kind=review_comment  by j-loreaux  family=F5 redundancy
**ASK:** This is just the pre-existing constructor for `ContinuousAlgEquiv`:
```
ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]
  [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra R A] [Algebra R B] (toAlgEquiv : A ≃ₐ[R] B)
  (continuous_toFun : Continuous toAlgEquiv.toFun := by fun_prop)
  (continuous_invFun : Continuous toAlgEquiv.invFun := by fun_prop) : A ≃A[R]
```
(up to some defeqs involving `toAlgEquiv.invFun`, `AlgEquiv.symm` and `DFunLike.coe`). So I think you can remove all this and use `mk` instead.
```
@@ -302,6 +302,25 @@ theorem _root_.AlgEquiv.isUniformEmbedding {E₁ E₂ : Type*} [UniformSpace E
     continuous_toFun := h₁
     continuous_invFun := by dsimp; fun_prop }
 
+/-- Interpret an algebra equivalence as a continuous algebra equivalence when it is continuous. -/
+def ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) : A ≃A[R] B :=
+  { e with continuous_toFun := he, continuous_invFun := he' }
```

## d0035  PR 33285 (human) — [Merged by Bors] - chore(*): golf, add missing lemmas
Mathlib/Algebra/Module/Submodule/Map.lean:597  kind=review_comment  by themathqueen  family=F1 proof
**ASK:** here's an even better golf
```suggestion
    comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=
  fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2
```
```
@@ -597,9 +597,8 @@ theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂) :
     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q := by
```

## d0010  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:273  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) :
```
```

+  · simp [minimalCover, h]
+
+lemma finite_minimalCover :
+    (minimalCover ε A).Finite := by
+  by_cases h : coveringNumber ε A ≠ ⊤
+  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.1
+  · simp [minimalCover, h]
+
+lemma isCover_minimalCover (h : coveringNumber ε A ≠ ⊤) :
+    IsCover ε A (minimalCover ε A) := by
+  simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+  exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.2.1
+
+lemma card_minimalCover (h : coveringNumber ε A ≠ ⊤) :
```

## d0018  PR 33117 (human) — [Merged by Bors] - feat: introduce predicate `Meromorphic`
Mathlib/Analysis/Meromorphic/Basic.lean:730  kind=review_comment  by jcommelin  family=F4 derive, don't restate
**ASK:** There is some new metaprogramming that can help here: the `to_fun` attribute.
To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).

```suggestion
@[to_fun (attr := fun_prop)]
lemma neg (hf : Meromorphic f) : Meromorphic (-f) := fun x ↦ (hf x).neg

@[to_fun (attr := fun_prop)]
lemma add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f + g) := fun x ↦ (hf x).add (hg x)

@[to_fun (attr := fun_prop)]
theorem sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)

@[to_fun (attr := fun_prop)]
lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)

@[to_fun (attr := fun_prop)]
lemma mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f * g) := fun x ↦ (hf x).mul (hg x)

@[to_fun (attr := fun_prop)]
theorem prod (h : ∀ σ, Meromorphic (F σ)) :
    Meromorphic (∏ n ∈ s, F n) := fun x ↦ MeromorphicAt.prod (h · x)

@[to_fun (attr := fun_prop)]
lemma div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f / g) := fun x ↦ (hf x).div (hg x)

@[to_fun (attr := fun_prop)]
lemma pow {f : 𝕜 → 𝕜} {n : ℕ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n

@[to_fun (attr := fun_prop)]
lemma zpow {f : 𝕜 → 𝕜} {n : ℤ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n

@[to_fun (attr := fun_prop)]
lemma deriv [CompleteSpace E] (hf : Meromorphic f) : Meromo
```
Meromorphic (fun x ↦ f x ^ n) := hf.zpow
+
+@[fun_prop]
+lemma deriv [CompleteSpace E] (hf : Meromorphic f) : Meromorphic (deriv f) := fun x ↦ (hf x).deriv
+
+@[fun_prop]
+lemma fun_deriv [CompleteSpace E] (hf : Meromorphic f) :
+    Meromorphic (fun x ↦ _root_.deriv f x) := hf.deriv
+
+@[fun_prop]
+lemma iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
+    Meromorphic (_root_.deriv^[n] f) := fun x ↦ (hf x).iterated_deriv
+
+@[fun_prop]
+lemma fun_iterated_deriv [CompleteSpace E] {n : ℕ} (hf : Meromorphic f) :
+    Meromorphic (fun x ↦ _root_.deriv^[n] f x) := hf.iterated_deriv
```

## d0015  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:405  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** ```suggestion
  rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)
  · simp
```
```
Set X) :
+    coveringNumber ε A ≤ packingNumber ε A := by
+  by_cases h_top : packingNumber ε A ≠ ⊤
+  · rw [← card_maximalSeparatedSet h_top]
+    refine (iInf_le _ (maximalSeparatedSet ε A)).trans (le_of_eq ?_)
+    simp [maximalSeparatedSet_subset, iInf_pos, isCover_maximalSeparatedSet h_top]
+  · simp only [ne_eq, Decidable.not_not] at h_top
+    simp [h_top]
+
+theorem coveringNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set X) :
+    coveringNumber (2 * ε) A ≤ externalCoveringNumber ε A := by
+  rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)
+  · simp [h_empty]
```

## d0045  PR 33337 (human) — [Merged by Bors] - chore(Analysis/InnerProductSpace/Projection/Submodule): renam
Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean:198  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] :
```
```
thogonalProjection_mem_subspace_orthogonalComplement_eq_zero (Submodule.coe_mem _), add_zero]
 
 @[deprecated (since := "2025-07-11")] alias orthogonalProjection_eq_linear_proj :=
-  orthogonalProjection_eq_linearProjOfIsCompl
+  orthogonalProjection_apply_eq_linearProjOfIsCompl
+@[deprecated (since := "2025-12-26")] alias orthogonalProjection_eq_linearProjOfIsCompl :=
+  orthogonalProjection_apply_eq_linearProjOfIsCompl
 
-theorem orthogonalProjection_coe_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] :
+theorem coe_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] :
```

## d0008  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:259  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add
```lean
attribute [grind .] finite_empty
```
but I think we should do that anyway.
```suggestion
lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  grind [minimalCover]
```
```
 rfl
+
+open Classical in
+/-- A finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
+It is defined as the empty set if no such finite cover exists. -/
+noncomputable
+def minimalCover (ε : ℝ≥0) (A : Set X) : Set X :=
+  if h : coveringNumber ε A ≠ ⊤ then (exists_set_encard_eq_coveringNumber h).choose else ∅
+
+lemma minimalCover_subset : minimalCover ε A ⊆ A := by
+  by_cases h : coveringNumber ε A ≠ ⊤
+  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_coveringNumber h).choose_spec.1
+  · simp [minimalCover, h]
```

## d0043  PR 33321 (human) — [Merged by Bors] - feat: linear independence of indecomposable roots of a root s
Mathlib/Algebra/Group/Irreducible/Indecomposable.lean:50  kind=review_comment  by jcommelin  family=F6 statement and API design
**ASK:** Isn't this abusing the defeq between predicates and sets?
```suggestion
def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  {j | IsMulIndecomposable v {i | 1 < f (v i)} j}
```
```
iv [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) :
     IsMulIndecomposable id univ x ↔ Irreducible x :=
   ⟨fun h ↦ ⟨by simpa, by simpa using h⟩, fun h ↦ by simpa using h.isUnit_or_isUnit⟩
 
+/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
+@[to_additive /-- The "base" of `v` relative to a morphism `f`.
+
+In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
+base of the root system associated to `f`. -/]
+def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
+  IsMulIndecomposable v {i | 1 < f (v i)}
```

## d0014  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:400  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley:
```suggestion
  by_cases! h_top : packingNumber ε A ≠ ⊤
  · rw [← encard_maximalSeparatedSet h_top]
    exact isCover_maximalSeparatedSet h_top |>.coveringNumber_le_encard maximalSeparatedSet_subset
  · simp [h_top]
```
```
@@ -243,4 +390,33 @@ theorem packingNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set
       · exact hf' x
       · simpa [edist_comm, hxy] using hf' y
 
+theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
+    coveringNumber ε A ≤ packingNumber ε A := by
+  by_cases h_top : packingNumber ε A ≠ ⊤
+  · rw [← card_maximalSeparatedSet h_top]
+    refine (iInf_le _ (maximalSeparatedSet ε A)).trans (le_of_eq ?_)
+    simp [maximalSeparatedSet_subset, iInf_pos, isCover_maximalSeparatedSet h_top]
+  · simp only [ne_eq, Decidable.not_not] at h_top
+    simp [h_top]
```

## d0004  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:162  kind=review_comment  by j-loreaux  family=F10 documentation
**ASK:** This is nice, but it would be even nicer if it were interspersed throughout the code.
```
f = y.conjAlgEquiv`.
+    Our goal will be to construct an isometry from `y`. We do this by first showing
+    `adjoint y ∘ y` is in the center of the endormorphisms, and as the algebra of endomorphisms
+    are central, `adjoint y ∘ y` is a scalar multiple of the identity.
+    Let `α : 𝕜` be that scalar, i.e., `adjoint y ∘ y = α • id`. This scalar is clearly real.
+    Also, it's easy to see that `adjoint y ∘ y` is invertible, so `α ≠ 0`.
+    As `adjoint y ∘ y` is positive, we get `0 < α`.
+    We also get `y ∘ adjoint y = α • id`.
+    Finally, we construct our isometry `1/√(re α) • y`. -/
```

## d0016  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:411  kind=review_comment  by j-loreaux  family=F9 formatting
**ASK:** otherwise style guidelines would require to indent all lines below the first `calc` line.
```suggestion
    coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc
  coveringNumber ε A
```
```
t, iInf_pos, isCover_maximalSeparatedSet h_top]
+  · simp only [ne_eq, Decidable.not_not] at h_top
+    simp [h_top]
+
+theorem coveringNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set X) :
+    coveringNumber (2 * ε) A ≤ externalCoveringNumber ε A := by
+  rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)
+  · simp [h_empty]
+  refine (coveringNumber_le_packingNumber _ A).trans ?_
+  exact packingNumber_two_mul_le_externalCoveringNumber ε A
+
+lemma coveringNumber_subset_le (h : A ⊆ B) :
+    coveringNumber ε A ≤ coveringNumber (ε / 2) B := by
+  calc coveringNumber ε A
```

## d0038  PR 33294 (human) — [Merged by Bors] - refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`
Mathlib/SetTheory/Cardinal/Cofinality.lean:535  kind=review_comment  by YaelDillies  family=F8 naming
**ASK:** ```suggestion
theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
```
```
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
```

## d0003  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:151  kind=review_comment  by j-loreaux  family=F6 statement and API design
**ASK:** You can still phrase this as:
```suggestion
    Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by
```
and I think Lean shouldn't need you to fill in the `_`.
```
ly (auxIsometry e hα hα2 he he' hαa).toContinuousLinearEquiv.injective
+  simp [smul_smul, inv_mul_cancel₀ (a := α') (by grind)]
+
+end auxiliaryDefs
+
+open ComplexOrder
+
+/-- The ⋆-algebra equivalence version of
+`ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv`.
+
+TODO: remove the hypothesis `Continuous f`, as star-algebra equivalences between endomorphisms are
+automatically continuous. -/
+public theorem StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
+    (f : (V →L[𝕜] V) ≃⋆ₐ[𝕜] (W →L[𝕜] W)) (hf : Continuous f) :
+    ∃ U : V ≃ₗᵢ[𝕜] W, f = U.conjStarAlgEquiv := by
```

## d0034  PR 33149 (human) — feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
None:None  kind=issue_comment  by grunweg  family=CORR 
**ASK:** Dear Jeff,

I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about them. If yours is different, that is nice to hear; we definitely welcome high-quality contributions.)

To make this PR closer to mathlib standards, you should
- avoid any axioms: either fill them in (if they define data), deduce them from existing mathlib facts or state them as `sorry`. (This PR cannot be merged while it contains `sorry`'s, but this could indicate any missing gaps. I'm working towards the Sobolev embedding theorem, for example.)
- some definitions are simply shorter names for mathlib definitions (e.g. `fourier1D` or `smoothInTime`). In general, I would just inline those. (If you believe this is absolutely essential for readability, you can introduce an `abbrev`. This should be used sparingly.)
- note that the definitions of `fourierDecay` and `spectralNSResidual` (thus, by extension, `SolvesNavierStokes`), are vacuously true --- thus, very likely not what you intend. I haven't checked every definition in your PR; please do so carefully before submitting! The fact that this happened this should be a major red flag. (It certainly is one for me, and makes me *much* less inclined to take a careful look.)

In general, [this page](https://leanprover-community.github.io/did_you_prove_it.html) documents some common p
```

```

## d0031  PR 33149 (human) — feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
Mathlib/Analysis/ODE/GalerkinRegularity.lean:293  kind=review_comment  by grunweg  family=F5 redundancy
**ASK:** Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).
```
o x
+      unfold fourier3D fourier1D
+      rw [star_prod, ← Finset.prod_mul_distrib]
+    simp_rw [h1]
+    exact fubini_torus3 (fun i y => fourier (k i) y * star (fourier (k' i) y))
+  rw [fubini]
+  simp only [ortho1D]
+  by_cases h : k = k'
+  · subst h
+    simp
+  · have : ∃ i, k i ≠ k' i := Function.ne_iff.mp h
+    obtain ⟨i, hi⟩ := this
+    have hz : ∏ j : Fin 3, (if k j = k' j then (1 : ℂ) else 0) = 0 := by
+      apply Finset.prod_eq_zero (Finset.mem_univ i)
+      simp [hi]
+    simp [h, hz]
+
+/-!
+## Parseval Identity
+-/
+
+theorem parseval3D (f : T3 → ℂ) (hf : Continuous f) :
```

## d0030  PR 33149 (human) — feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
Mathlib/Analysis/ODE/GalerkinRegularity.lean:50  kind=review_comment  by grunweg  family=CORR 
**ASK:** Mathlib has a no-axioms policy. Please don't introduce any new axioms.
```
oth solutions
+- Sundman (1912): Mémoire sur le problème des trois corps
+- Camlin (2025): Global Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response
+  Functionals. DOI: 10.63968/post-bio-ai-epistemics.v1n2.012
+-/
+
+set_option linter.style.commandStart false
+open scoped InnerProductSpace
+
+/-- The three-dimensional torus T³ := (ℝ/ℤ)³ -/
+abbrev T3 := Fin 3 → UnitAddCircle
+
+/-!
+## Analysis Constants
+
+Standard constants from Moser estimates, Gronwall inequalities, and Sobolev embeddings.
+-/
+
+/-- Moser estimate constant for nonlinear term bounds -/
+axiom cMoser : ℝ → ℝ
```

## d0001  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Analysis/InnerProductSpace/Adjoint.lean:689  kind=review_comment  by j-loreaux  family=F10 documentation
**ASK:** ```suggestion
/-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of
```
```
@@ -682,6 +683,36 @@ theorem inner_map_map_of_mem_unitary {u : H →L[𝕜] H} (hu : u ∈ unitary (H
 
 end ContinuousLinearMap
 
+namespace LinearIsometryEquiv
+
+open ContinuousLinearMap ContinuousLinearEquiv in
+/-- An isometry linear equivalence of two Hilbert spaces induces an equivalence of
```

## d0011  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:319  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
```
```
t, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_packingNumber h).choose_spec.1
+  · simp only [maximalSeparatedSet, h, dite_false, Set.empty_subset]
+
+lemma isSeparated_maximalSeparatedSet :
+    IsSeparated ε (maximalSeparatedSet ε A : Set X) := by
+  by_cases h : packingNumber ε A ≠ ⊤
+  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.1
+  · simp only [maximalSeparatedSet, h, dite_false, IsSeparated.empty]
+
+lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
```

## d0022  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:195  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.ciSup {α : Type*} [TopologicalSpace α]
```
```
ace γ] {S : Set γ} (hS : Dense S)
+    (hf : Continuous f) :
+    lowerBounds (f '' S) = lowerBounds (range f) := by
+  refine subset_antisymm ?_ fun _ => lowerBounds_mono (Set.image_subset_range f S) le_rfl
+  refine subset_trans ?_ fun _ => lowerBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl
+  intro x hx i hi
+  rw [mem_closure_iff_frequently] at hi
+  exact (hi.mono hx).mem_of_closed isClosed_Ici
+
+/-- The supremum of a bounded above, continuous function on a dense set is equal to the supremum on
+the universe. -/
+theorem Dense.continuous_sup {α : Type*} [TopologicalSpace α]
```

## d0033  PR 33149 (human) — feat(Analysis/ODE): Galerkin regularity for Navier-Stokes on T³
None:None  kind=issue_comment  by grunweg  family=F12 PR level
**ASK:** Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open is useful. If you have addressed all the above comments, feel free to re-open this PR.
```

```

## d0028  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:261  kind=review_comment  by j-loreaux  family=F4 derive, don't restate
**ASK:** ```suggestion
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup' (α := αᵒᵈ) hf
```
```
 (range f)
+  · refine (isGLB_csInf (range_nonempty f) h1).unique ?_
+    refine (isGLB_congr (hS.continuous_lowerBounds hf)).mp (isGLB_ciInf_set ?_ hS.nonempty)
+    exact h1.mono (by grind)
+  · have h2 : ¬ BddBelow (range (fun s : S => f (Subtype.val s))) := by
+      intro h
+      have := range_comp' f (Subtype.val : S → γ)
+      simp_all only [Subtype.range_coe_subtype, setOf_mem_eq]
+      have := h.closure.mono (image_closure_subset_closure_image hf)
+      simp only [hS.closure_eq, image_univ] at this
+      exact h1 this
+    simp [csInf_of_not_bddBelow h1, csInf_of_not_bddBelow h2]
```

## d0042  PR 33321 (human) — [Merged by Bors] - feat: linear independence of indecomposable roots of a root s
Mathlib/Algebra/Group/Irreducible/Indecomposable.lean:47  kind=review_comment  by jcommelin  family=F10 documentation
**ASK:** ```suggestion
In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the
```
```
cted lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) :
+    {i | IsMulIndecomposable v s i} ⊆ s := by
+  aesop
+
 @[to_additive]
 lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) :
     IsMulIndecomposable id univ x ↔ Irreducible x :=
   ⟨fun h ↦ ⟨by simpa, by simpa using h⟩, fun h ↦ by simpa using h.isUnit_or_isUnit⟩
 
+/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
+@[to_additive /-- The "base" of `v` relative to a morphism `f`.
+
+In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
```

## d0027  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:243  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.ciInf' {α : Type*} [TopologicalSpace α]
```
```
 by
+      intro h
+      have := range_comp' f (Subtype.val : S → γ)
+      simp_all only [Subtype.range_coe_subtype, setOf_mem_eq]
+      have := h.closure.mono (image_closure_subset_closure_image hf)
+      simp only [hS.closure_eq, image_univ] at this
+      exact h1 this
+    simp [csSup_of_not_bddAbove h1, csSup_of_not_bddAbove h2]
+
+/-- This is an analogue of `Dense.continuous_inf` for functions taking values in a conditionally
+complete linear order. The assumption of `BddBelow (range f)` is not needed in this theorem. -/
+theorem Dense.continuous_inf' {α : Type*} [TopologicalSpace α]
```

## d0005  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:94  kind=review_comment  by j-loreaux  family=F9 formatting
**ASK:** ```suggestion
section auxiliaryDefs

variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)
```
```
@@ -79,3 +85,145 @@ public theorem ContinuousAlgEquiv.eq_continuousLinearEquivConjContinuousAlgEquiv
       suffices T'.toLinearMap = Tₗ.symm from this ▸ T'.continuous
       simp [LinearMap.ext_iff, ← Tₗ.injective.eq_iff, T', this, hT, hd, Tₗ] }
   exact ⟨TL, fun A ↦ (ContinuousLinearMap.ext <| this A).symm⟩
+
+variable {𝕜 V W : Type*} [RCLike 𝕜] [NormedAddCommGroup V] [InnerProductSpace 𝕜 V] [CompleteSpace V]
+  [NormedAddCommGroup W] [InnerProductSpace 𝕜 W] [CompleteSpace W]
+
+section auxiliaryDefs
+variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)
```

## d0020  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:183  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α]
```
```
hf : Continuous f) :
+    upperBounds (f '' S) = upperBounds (range f) := by
+  refine subset_antisymm ?_ fun _ => upperBounds_mono (Set.image_subset_range f S) le_rfl
+  refine subset_trans ?_ fun _ => upperBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl
+  intro x hx i hi
+  rw [mem_closure_iff_frequently] at hi
+  exact (hi.mono hx).mem_of_closed isClosed_Iic
+
+/-- The lower bounds of the image of a continuous function on a dense set is equal to the lower
+bounds of the range of the universe. -/
+theorem Dense.continuous_lowerBounds {α : Type*} [TopologicalSpace α] [Preorder α]
```

## d0006  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean:189  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** The naming of your `have`s could use some work. Please improve them.
```
imp
+  replace this := (Subalgebra.mem_center_iff (R := 𝕜)).mpr fun _ ↦ this _
+  simp only [Algebra.IsCentral.center_eq_bot] at this
+  obtain ⟨α, hα⟩ := this
+  simp only [AlgHom.toRingHom_eq_coe, Algebra.toRingHom_ofId, Algebra.algebraMap_eq_smul_one] at hα
+  have this : IsUnit (adjoint y.toContinuousLinearMap ∘L y) :=
+    isUnit_iff_exists.mpr ⟨y.symm ∘L adjoint y.symm.toContinuousLinearMap, by
+      simp [mul_def, ← comp_assoc, comp_assoc _ _ (adjoint y.toContinuousLinearMap),
+        ← adjoint_comp, one_def, comp_assoc _ y.toContinuousLinearMap]⟩
+  have thisα : α = RCLike.re α := by
```

## d0041  PR 33305 (human) — [Merged by Bors] - doc(GroupTheory): fix file refs
None:None  kind=issue_comment  by bryangingechen  family=F9 formatting
**ASK:** bors r-
bors d+

There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36
```

```

## d0009  PR 33098 (human) — [Merged by Bors] - feat: minimal covers and maximal separated sets
Mathlib/Topology/MetricSpace/CoveringNumbers.lean:310  kind=review_comment  by j-loreaux  family=F1 proof
**ASK:** This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add
```lean
attribute [grind .] IsSeparated.empty
```
but I think we should do that anyway.

```suggestion
lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  by grind [maximalSeparatedSet]
```
```
 subset of a set `A` with maximal cardinality.
+It is defined as the empty set if no such finite subset exists. -/
+noncomputable
+def maximalSeparatedSet (ε : ℝ≥0) (A : Set X) : Set X :=
+  if h : packingNumber ε A ≠ ⊤ then (exists_set_encard_eq_packingNumber h).choose else ∅
+
+lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
+  by_cases h : packingNumber ε A ≠ ⊤
+  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_packingNumber h).choose_spec.1
+  · simp only [maximalSeparatedSet, h, dite_false, Set.empty_subset]
```

## d0049  PR 33421 (human) — [Merged by Bors] - chore(Algebra/Order/Floor): review API about `round`
Mathlib/Topology/Algebra/Order/Floor.lean:211  kind=review_comment  by Ruben-VandeVelde  family=F6 statement and API design
**ASK:** Is this not something very general that should exist as a lemma? Same in the next theorem
```
ontinuousOn_fract ⌊x⌋).continuousAt <|
-    Ico_mem_nhds ((floor_le _).lt_of_ne h.symm) (lt_floor_add_one _)
+  continuousAt_id.sub <| continuous_of_discreteTopology.continuousAt.comp <|
+    continuousAt_floor h
+
+theorem tendsto_round_nhdsGE_pure [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]
+    (x : α) : Tendsto round (𝓝[≥] x) (pure (round x)) := by
+  rw [funext round_eq']
+  have : Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x)) := by
+    simp only [two_mul]
+    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
+    exact fun a ha ↦ add_le_add ha ha
```

## d0023  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:208  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.ciInf {α : Type*} [TopologicalSpace α]
```
```
} [TopologicalSpace γ]
+    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
+    ⨆ i, f i = ⨆ s : S, f s := by
+  rw [← sSup_range, ← sSup_range]
+  obtain (_ | _) := isEmpty_or_nonempty γ
+  · simp [Set.range_eq_empty]
+  refine (isLUB_csSup (range_nonempty f) h).unique ?_
+  refine (isLUB_congr (hS.continuous_upperBounds hf)).mp (isLUB_ciSup_set ?_ hS.nonempty)
+  exact h.mono (by grind)
+
+/-- The infimum of a bounded below, continuous function on a dense set is equal to the infimum on
+the universe. -/
+theorem Dense.continuous_inf {α : Type*} [TopologicalSpace α]
```

## d0007  PR 33066 (human) — [Merged by Bors] - feat(Analysis/Normed/Operator): star-algebra equivalences bet
None:None  kind=issue_comment  by j-loreaux  family=F9 formatting
**ASK:** I guess your contention regarding imports is that because this file is a leaf, the import increase doesn't matter?
```

```

## d0025  PR 33145 (human) — [Merged by Bors] - feat: supremum of a continuous function on a dense set is equ
Mathlib/Topology/Order/IsLUB.lean:221  kind=review_comment  by j-loreaux  family=F8 naming
**ASK:** ```suggestion
theorem Dense.ciSup' {α : Type*} [TopologicalSpace α]
```
```
 BddBelow (range f)) :
+    ⨅ i, f i = ⨅ s : S, f s := by
+  rw [← sInf_range, ← sInf_range]
+  obtain (_ | _) := isEmpty_or_nonempty γ
+  · simp [Set.range_eq_empty]
+  refine (isGLB_csInf (range_nonempty f) h).unique ?_
+  refine (isGLB_congr (hS.continuous_lowerBounds hf)).mp (isGLB_ciInf_set ?_ hS.nonempty)
+  exact h.mono (by grind)
+
+/-- This is an analogue of `Dense.continuous_sup` for functions taking values in a conditionally
+complete linear order. The assumption of `BddAbove (range f)` is not needed in this theorem. -/
+theorem Dense.continuous_sup' {α : Type*} [TopologicalSpace α]
```
