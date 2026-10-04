# 46 asks

## v0066  PR 30641 (human) — feat: elementary lemmas aiding computations with `log⁺`
Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean:109  kind=review_comment  by grunweg  family=F1 proof
**ASK:** Can you prove the \leq version here directly?
```
@@ -91,9 +98,21 @@ theorem monotoneOn_posLog : MonotoneOn log⁺ (Set.Ici 0) := by
     simp only [this, and_true, ge_iff_le]
     linarith
 
+/-- The function `log⁺` commutes with taking powers. -/
+@[simp] lemma posLog_pow {n : ℕ} {a : ℝ} :
+    log⁺ (a ^ n) = n * log⁺ a := by
+  by_cases hn : n = 0
+  · simp_all
+  by_cases h₂a : |a| ≤ 1
+  · simp_all [pow_le_one₀, (posLog_eq_zero_iff _).2]
+  rw [not_le] at h₂a
+  have : 1 < |a ^ n| := by simp [one_lt_pow₀ h₂a hn]
```

## p0004  PR 42814 (AI) — [Merged by Bors] - feat(NumberTheory/FundamentalDiscriminant): fundamental discr
Mathlib/Data/Nat/Prime/Basic.lean:110  kind=review_comment  by riccardobrasca  family=F6 statement and API design
**ASK:** Can you add an alias for the right to left implication? Or maybe even removing the other one (I don't see any reasonable application).
```
@@ -106,6 +106,14 @@ theorem Prime.odd_of_ne_two {p : ℕ} (hp : p.Prime) (h_two : p ≠ 2) : Odd p :
 theorem Prime.even_sub_one {p : ℕ} (hp : p.Prime) (h2 : p ≠ 2) : Even (p - 1) :=
   let ⟨n, hn⟩ := hp.odd_of_ne_two h2; ⟨n, by rw [hn, Nat.add_sub_cancel, two_mul]⟩
 
+/-- To prove a property of all primes, it is enough to prove it for `2` and for the odd primes. -/
+theorem forall_prime_iff_two_and_odd {P : ℕ → Prop} :
```

## v0067  PR 30641 (human) — feat: elementary lemmas aiding computations with `log⁺`
Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean:194  kind=review_comment  by grunweg  family=F1 proof
**ASK:** Can `positivity` do this (untested)?
```
e for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving
-multiple summands. -/
+/--
+Variant of `posLog_sum` for norms of elements in normed additive commutative
+groups, using monotonicity of `log⁺` and the triangle inequality.
+-/
+lemma posLog_norm_sum_le {E : Type*} [NormedAddCommGroup E]
+    {α : Type*} (s : Finset α) (f : α → E) :
+    log⁺ ‖∑ t ∈ s, f t‖ ≤ log s.card + ∑ t ∈ s, log⁺ ‖f t‖ := by
+  calc log⁺ ‖∑ t ∈ s, f t‖
+  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by
+    apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)
+    simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]
```

## v0016  PR 26755 (human) — [Merged by Bors] - chore: remove `noncomputable` from Set/Finset Monoid instance
Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean:1  kind=review_comment  by b-mehta  family=F12 PR level
**ASK:** How many `noncomputable`s from this file are still necessary? `coeMonoidHom` looks like it can be computable too?
```

```

## p0005  PR 42814 (AI) — [Merged by Bors] - feat(NumberTheory/FundamentalDiscriminant): fundamental discr
Mathlib/Data/Nat/Squarefree.lean:395  kind=review_comment  by riccardobrasca  family=F7 generality
**ASK:** Do we have the same theorem in any UFD (I see that here the pint is Nat vs Int, but it is worth to check). Even better, maybe there is a uniform way of stating this in any normalization monoid something.
```
@@ -387,6 +387,19 @@ theorem prod_primeFactors_sdiff_of_squarefree {n : ℕ} (hn : Squarefree n) {t :
 
 end Nat
 
+namespace Int
+
+/-- An integer is squarefree iff no prime square divides it. -/
+theorem squarefree_iff_prime_sq_not_dvd {n : ℤ} :
```

## v0105  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:86  kind=review_comment  by ocfnash  family=F1 proof
**ASK:** Surely this is a one-liner using `infinite_pigeonhole_card_lt`?
```
 exists_infinite_fiber {β α : Type u} (f : β → α) (w : #α < #β) (w' : Infinite α) :
+theorem exists_infinite_fiber {β α : Type u} (f : β → α) (h : #α < #β) (hβ : Infinite β) :
     ∃ a : α, Infinite (f ⁻¹' {a}) := by
-  simp_rw [Cardinal.infinite_iff] at w' ⊢
-  obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f w w'
-  exact ⟨a, w'.trans ha.le⟩
+  simp_rw [Cardinal.infinite_iff] at hβ ⊢
+  rcases lt_or_ge #α ℵ₀ with hα | hα
+  · exact infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])
+  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ
+    exact ⟨a, hα.trans ha.le⟩
```

## p0016  PR 43192 (human) — [Merged by Bors] - feat(Algebra/Category/ModuleCat): add abbrevs for Presheaves 
Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean:60  kind=review_comment  by joelriou  family=F8 naming
**ASK:** I would prefer the name `homMk` (overall, there is an hesitation in mathlib about `mkHom` or `homMk`). In the `PresheafOfModules` namespace, there is a `homMk` (with different parameters though).
```
 over a presheaf of commutative rings at an object. -/
+abbrev obj (F : PresheafOfModulesOfCommRing.{v} R) (X : Cᵒᵖ) : ModuleCat.{v} (R.obj X) :=
+  PresheafOfModules.obj F X
+
+/-- The restriction map of a presheaf of modules over a presheaf of commutative rings. -/
+abbrev map (F : PresheafOfModulesOfCommRing.{v} R) {X Y : Cᵒᵖ} (f : X ⟶ Y) :
+    F.obj X ⟶ (ModuleCat.restrictScalars (R.map f).hom).obj (F.obj Y) :=
+  PresheafOfModules.map _ _
+
+/-- Construct a morphism of presheaves of modules over a presheaf of commutative rings. -/
+abbrev mkHom {M₁ M₂ : PresheafOfModulesOfCommRing.{v} R}
```

## p0007  PR 42814 (AI) — [Merged by Bors] - feat(NumberTheory/FundamentalDiscriminant): fundamental discr
Mathlib/NumberTheory/FundamentalDiscriminant.lean:43  kind=review_comment  by riccardobrasca  family=F2 interface
**ASK:** ```suggestion
variable {D : ℤ}

theorem isFundamentalDiscr_def :
```
then you can remove `{D : ℤ}` in various declarations.
```
 if and only if
+  it is squarefree.
+* `Int.isFundamentalDiscr_four_mul`: `4m` is a fundamental discriminant if and only if `m` is
+  squarefree and `m ≡ 2, 3 mod 4`.
+-/
+
+@[expose] public section
+
+namespace Int
+
+/-- `D` is a fundamental discriminant: it is a discriminant (`D ≡ 0, 1 mod 4`) and primitive,
+i.e. `D / 4 ≢ 0, 1 mod 4` when `4 ∣ D`, and no odd prime square divides `D`. -/
+def IsFundamentalDiscr (D : ℤ) : Prop :=
+  (D % 4 = 0 ∨ D % 4 = 1) ∧ (∀ x, D = 4 * x → ¬ 4 ∣ x ∧ x % 4 ≠ 1) ∧
+    ∀ p : ℕ, p.Prime → Odd p → ¬ (p : ℤ) ^ 2 ∣ D
+
+theorem isFundamentalDiscr_def {D : ℤ} :
```

## p0013  PR 43192 (human) — [Merged by Bors] - feat(Algebra/Category/ModuleCat): add abbrevs for Presheaves 
Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean:11  kind=review_comment  by joelriou  family=F10 documentation
**ASK:** ```suggestion
# Modules over presheaves of commutative rings
```
```
@@ -0,0 +1,120 @@
+/-
+Copyright (c) 2026 Brian Nugent. All rights reserved.
+Released under Apache 2.0 license as described in the file LICENSE.
+Authors: Brian Nugent
+-/
+module
+
+public import Mathlib.Algebra.Category.ModuleCat.Presheaf.Pullback
+
+/-!
+# Modules over presheaves commutative rings
```

## v0109  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:67  kind=review_comment  by ocfnash  family=F10 documentation
**ASK:** ```suggestion
/-- A function whose domain's cardinality is infinite and strictly greater than its codomain's
```
```
@@ -64,33 +64,51 @@ theorem infinite_pigeonhole_set {β α : Type u} {s : Set β} (f : s → α) (θ
     rfl
   rintro x ⟨_, hx'⟩; exact hx'
 
-/-- A function whose codomain's cardinality is infinite but strictly smaller than its domain's
+/-- A function whose domain's cardinality is infinite but strictly greater than its domain's
```

## v0063  PR 30458 (AI) — chore(Algebra): misc. generalizations
Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean:1260  kind=review_comment  by themathqueen  family=F1 proof
**ASK:** same here, does the old proof not work?
```
ncel
 
-@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) :=
-  have ⟨_, ha⟩ := hs; card_le_card_image₂_left _ ha div_right_injective
+section RightCancel
+variable [DivisionMonoid α] [IsRightCancelMul α] [DecidableEq α] {s t : Finset α}
 
-@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) :=
-  have ⟨_, ha⟩ := ht; card_le_card_image₂_right _ ha div_left_injective
+@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by
+  obtain ⟨b, hb⟩ := ht
+  exact card_le_card_image₂_right _ hb (div_left_injective (b := b))
```

## p0012  PR 43167 (human) — [Merged by Bors] - feat(GroupTheory/Commutator/Basic): prove `⁅H ⊔ K, N⁆ = ⁅H, N
Mathlib/GroupTheory/Commutator/Basic.lean:326  kind=review_comment  by kim-em  family=F8 naming
**ASK:** `commutator_sup_left_of_normal` (or `_right_` after the swap) rather than a prime.
```
@@ -311,6 +323,40 @@ theorem commutator_le_map_commutator {f : G →* G'} {K₁ K₂ : Subgroup G'} (
 
 variable (H₁ H₂)
 
+private theorem commutator_sup_left' (H K N : Subgroup G) [(⁅H, N⁆ ⊔ ⁅K, N⁆).Normal] :
```

## p0015  PR 43192 (human) — [Merged by Bors] - feat(Algebra/Category/ModuleCat): add abbrevs for Presheaves 
Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean:43  kind=review_comment  by joelriou  family=F2 interface
> (in reply to) Could you add `by cat_disch` as default tactics?
**ASK:** (This may apply to other definitions below.)
```
rev mk (obj : ∀ (X : Cᵒᵖ), ModuleCat.{v} (R.obj X)) (map : ∀ {X Y : Cᵒᵖ} (f : X ⟶ Y),
+      obj X ⟶ (ModuleCat.restrictScalars (R.map f).hom).obj (obj Y))
+    (map_id : ∀ (X : Cᵒᵖ), map (𝟙 X) = (ModuleCat.restrictScalarsId' (R.map (𝟙 X)).hom
+      (congrArg CommRingCat.Hom.hom (R.map_id X))).inv.app _)
+    (map_comp : ∀ {X Y Z : Cᵒᵖ} (f : X ⟶ Y) (g : Y ⟶ Z),
+      map (f ≫ g) = map f ≫ (ModuleCat.restrictScalars _).map (map g) ≫
+        (ModuleCat.restrictScalarsComp' (R.map f).hom (R.map g).hom (R.map (f ≫ g)).hom
+          (congrArg CommRingCat.Hom.hom <| R.map_comp f g)).inv.app _) :
```

## v0065  PR 30641 (human) — feat: elementary lemmas aiding computations with `log⁺`
Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean:106  kind=review_comment  by grunweg  family=F8 naming
**ASK:** There's no `ha` in scope, so this could be `ha`, right?
```
@@ -91,9 +98,21 @@ theorem monotoneOn_posLog : MonotoneOn log⁺ (Set.Ici 0) := by
     simp only [this, and_true, ge_iff_le]
     linarith
 
+/-- The function `log⁺` commutes with taking powers. -/
+@[simp] lemma posLog_pow {n : ℕ} {a : ℝ} :
+    log⁺ (a ^ n) = n * log⁺ a := by
+  by_cases hn : n = 0
+  · simp_all
+  by_cases h₂a : |a| ≤ 1
```

## v0093  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/MeasureTheory/Measure/Portmanteau.lean:650  kind=review_comment  by artie2000  family=F1 proof
**ASK:** ````suggestion
Tendsto μs L (𝓝 μ) :=
  tendsto_of_forall_isClosed_limsup_le (by simpa using h)
````
```
ndsto_of_forall_isClosed_limsup_le' fun F hF ↦ ?_
-  rcases L.eq_or_neBot with rfl | hne
-  · simp
-  specialize h F hF
-  simp only [Measure.real_def] at h
-  rwa [ENNReal.limsup_toReal_eq (b := 1) (by simp) (.of_forall fun i ↦ prob_le_one),
-    ENNReal.toReal_le_toReal _ (by finiteness)] at h
-  refine ne_top_of_le_ne_top (b := 1) (by simp) ?_
-  refine limsup_le_of_le ?_ (.of_forall fun i ↦ prob_le_one)
-  exact isCoboundedUnder_le_of_le L (x := 0) (by simp)
+  simp only [ProbabilityMeasure.measureReal_eq_coe_coeFn, NNReal.toReal_limsup] at h
+  exact tendsto_of_forall_isClosed_limsup_le h
```

## v0061  PR 30458 (AI) — chore(Algebra): misc. generalizations
Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean:1258  kind=review_comment  by themathqueen  family=F2 interface
**ASK:** following the above suggestion:
```suggestion
variable [IsRightCancel α] in
@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by
```
```
 ha⟩ := hs
+  exact card_le_card_image₂_left _ ha (div_right_injective (b := a))
+
+end LeftCancel
 
-@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) :=
-  have ⟨_, ha⟩ := hs; card_le_card_image₂_left _ ha div_right_injective
+section RightCancel
+variable [DivisionMonoid α] [IsRightCancelMul α] [DecidableEq α] {s t : Finset α}
 
-@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) :=
-  have ⟨_, ha⟩ := ht; card_le_card_image₂_right _ ha div_left_injective
+@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by
```

## v0068  PR 30641 (human) — feat: elementary lemmas aiding computations with `log⁺`
Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean:193  kind=review_comment  by grunweg  family=F1 proof
**ASK:** Can `gcongr` do this (or do you need to provide the side condition manually)?
```
gle_le_sum (fun _ _ ↦ posLog_nonneg) ht_max.1
 
-/-- Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving
-multiple summands. -/
+/--
+Variant of `posLog_sum` for norms of elements in normed additive commutative
+groups, using monotonicity of `log⁺` and the triangle inequality.
+-/
+lemma posLog_norm_sum_le {E : Type*} [NormedAddCommGroup E]
+    {α : Type*} (s : Finset α) (f : α → E) :
+    log⁺ ‖∑ t ∈ s, f t‖ ≤ log s.card + ∑ t ∈ s, log⁺ ‖f t‖ := by
+  calc log⁺ ‖∑ t ∈ s, f t‖
+  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by
+    apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)
```

## v0110  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:67  kind=review_comment  by ocfnash  family=F10 documentation
> (in reply to) ```suggestion
/-- A function whose domain's cardinality is infinite and strictly greater than its codomain's
```
**ASK:** Similarly in comments below
```
@@ -64,33 +64,51 @@ theorem infinite_pigeonhole_set {β α : Type u} {s : Set β} (f : s → α) (θ
     rfl
   rintro x ⟨_, hx'⟩; exact hx'
 
-/-- A function whose codomain's cardinality is infinite but strictly smaller than its domain's
+/-- A function whose domain's cardinality is infinite but strictly greater than its domain's
```

## p0006  PR 42814 (AI) — [Merged by Bors] - feat(NumberTheory/FundamentalDiscriminant): fundamental discr
Mathlib/NumberTheory/FundamentalDiscriminant.lean:43  kind=review_comment  by riccardobrasca  family=F4 derive, don't restate
**ASK:** Can this be generated by `mk_iff`?
```
 if and only if
+  it is squarefree.
+* `Int.isFundamentalDiscr_four_mul`: `4m` is a fundamental discriminant if and only if `m` is
+  squarefree and `m ≡ 2, 3 mod 4`.
+-/
+
+@[expose] public section
+
+namespace Int
+
+/-- `D` is a fundamental discriminant: it is a discriminant (`D ≡ 0, 1 mod 4`) and primitive,
+i.e. `D / 4 ≢ 0, 1 mod 4` when `4 ∣ D`, and no odd prime square divides `D`. -/
+def IsFundamentalDiscr (D : ℤ) : Prop :=
+  (D % 4 = 0 ∨ D % 4 = 1) ∧ (∀ x, D = 4 * x → ¬ 4 ∣ x ∧ x % 4 ≠ 1) ∧
+    ∀ p : ℕ, p.Prime → Odd p → ¬ (p : ℤ) ^ 2 ∣ D
+
+theorem isFundamentalDiscr_def {D : ℤ} :
```

## v0132  PR 36822 (human) — [Merged by Bors] - feat(Order/Interval/Set/Disjoint): use `to_dual`
Mathlib/Order/Interval/Set/Disjoint.lean:82  kind=review_comment  by vihdzp  family=F3 registration
**ASK:** simp?
```
theorem Ioc_disjoint_Ioi_same : Disjoint (Ioc a b) (Ioi b) :=
   Ioc_disjoint_Ioi le_rfl
 
+@[to_dual Iio_disjoint_Ioi_of_not_lt]
 theorem Ioi_disjoint_Iio_of_not_lt (h : ¬a < b) : Disjoint (Ioi a) (Iio b) :=
   disjoint_left.mpr fun _ hx hy ↦ h (hx.trans hy)
 
+@[to_dual Iio_disjoint_Ioi_of_le]
 theorem Ioi_disjoint_Iio_of_le (h : a ≤ b) : Disjoint (Ioi b) (Iio a) :=
   Ioi_disjoint_Iio_of_not_lt (not_lt_of_ge h)
 
-@[simp]
+@[to_dual Iio_disjoint_Ioi_same]
 theorem Ioi_disjoint_Iio_same : Disjoint (Ioi a) (Iio a) :=
   Ioi_disjoint_Iio_of_le le_rfl
 
-@[simp]
+@[to_dual Iio_disjoint_Ioi_iff]
```

## v0108  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:89  kind=review_comment  by ocfnash  family=F2 interface
**ASK:** ```suggestion
theorem exists_infinite_fiber' {β α : Type u} (f : β → α) (h : #α < #β) [Infinite α] :
```
```
 α, Infinite (f ⁻¹' {a}) := by
-  simp_rw [Cardinal.infinite_iff] at w' ⊢
-  obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f w w'
-  exact ⟨a, w'.trans ha.le⟩
+  simp_rw [Cardinal.infinite_iff] at hβ ⊢
+  rcases lt_or_ge #α ℵ₀ with hα | hα
+  · exact infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])
+  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ
+    exact ⟨a, hα.trans ha.le⟩
+
+/-- A weaker version of `exists_infinite_fiber` that requires codomain to be infinite. -/
+theorem exists_infinite_fiber' {β α : Type u} (f : β → α) (h : #α < #β) (hα : Infinite α) :
```

## p0008  PR 43024 (human) — [Merged by Bors] - feat: `isMulCommutative_anti` for subobjects
Mathlib/Algebra/Group/Subsemigroup/Defs.lean:352  kind=review_comment  by SnirBroshi  family=F8 naming
**ASK:** ```suggestion
lemma isMulCommutative_anti {S M : Type*} [SetLike S M] [Mul M] [MulMemClass S M]
```
```
@@ -346,3 +346,11 @@ lemma setLike_mul_comm {S M : Type*} [SetLike S M] [Mul M] [MulMemClass S M]
     {s : S} [IsMulCommutative s] ⦃a b : M⦄ (ha : a ∈ s) (hb : b ∈ s) :
     a * b = b * a :=
   isMulCommutative_iff_of_setLike.mp ‹_› a ha b hb
+
+/-- Commutativity of multiplication passes to smaller subobjects. -/
+@[to_additive /-- Commutativity of addition passes to smaller subobjects. -/ ]
+lemma isMulCommutative_mono {S M : Type*} [SetLike S M] [Mul M] [MulMemClass S M]
```

## v0031  PR 28649 (human) — [Merged by Bors] - doc(Probability): miscellaneous typo fixes
Mathlib/Probability/Moments/Variance.lean:452  kind=review_comment  by grunweg  family=F10 documentation
**ASK:** I'm not sure about this one
```
@@ -449,7 +449,7 @@ lemma variance_le_sub_mul_sub [IsProbabilityMeasure μ] {a b : ℝ} {X : Ω →
       linarith
     _ = (b - μ[X]) * (μ[X] - a) := by ring
 
-/-- **Popoviciu's inequality on variance**
+/-- **Popoviciu's inequality on variances**
```

## v0107  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:97  kind=review_comment  by ocfnash  family=F2 interface
**ASK:** ```suggestion
theorem exists_uncountable_fiber {β α : Type u} (f : β → α) (h : #α < #β) [Uncountable β] :
```
```
hole_card_lt f h hβ
+    exact ⟨a, hα.trans ha.le⟩
+
+/-- A weaker version of `exists_infinite_fiber` that requires codomain to be infinite. -/
+theorem exists_infinite_fiber' {β α : Type u} (f : β → α) (h : #α < #β) (hα : Infinite α) :
+    ∃ a : α, Infinite (f ⁻¹' {a}) :=
+  exists_infinite_fiber f h (by
+    rw [Cardinal.infinite_iff] at hα ⊢
+    exact hα.trans h.le)
+
+/-- A function whose domain's cardinality is uncountable but strictly greater than its domain's
+has an uncountable fiber. -/
+theorem exists_uncountable_fiber {β α : Type u} (f : β → α) (h : #α < #β) (hβ : Uncountable β) :
```

## v0056  PR 29842 (human) — [Merged by Bors] - feat(TangentCone): generalize some lemmas to TVS
None:None  kind=issue_comment  by eric-wieser  family=F12 PR level
**ASK:** > but if I fail, then I would prefer to have one of the "generalize lemmas" PRs merged so that we can generalize downstream proofs here and there before generalizing the definition.

I'm fine with this, please just write something to this effect in the PR description.
```

```

## v0106  PR 34091 (AI) — [Merged by Bors] - feat(SetTheory/Cardinal): generalize infinite pigeonhole prin
Mathlib/SetTheory/Cardinal/Pigeonhole.lean:80  kind=review_comment  by ocfnash  family=F2 interface
**ASK:** ```suggestion
theorem exists_infinite_fiber {β α : Type u} (f : β → α) (h : #α < #β) [Infinite β] :
```
```
cof_eq])
+    exact ⟨a, ha.trans' (succ_le_of_lt hα)⟩
+  · exact infinite_pigeonhole_card f (succ #α) (succ_le_of_lt h) (hα.trans (le_succ _))
+      ((lt_succ _).trans_le (isRegular_succ hα).2.ge)
 
-/-- A function whose codomain's cardinality is infinite but strictly smaller than its domain's
+/-- A function whose domain's cardinality is infinite but strictly greater than its domain's
 has an infinite fiber. -/
-theorem exists_infinite_fiber {β α : Type u} (f : β → α) (w : #α < #β) (w' : Infinite α) :
+theorem exists_infinite_fiber {β α : Type u} (f : β → α) (h : #α < #β) (hβ : Infinite β) :
```

## v0131  PR 36822 (human) — [Merged by Bors] - feat(Order/Interval/Set/Disjoint): use `to_dual`
Mathlib/Order/Interval/Set/Disjoint.lean:78  kind=review_comment  by vihdzp  family=F3 registration
**ASK:** simp?
```
p]
 theorem Ioc_disjoint_Ioi (h : b ≤ c) : Disjoint (Ioc a b) (Ioi c) :=
   disjoint_left.mpr (fun _ hx hy ↦ (hx.2.trans h).not_gt hy)
 
 theorem Ioc_disjoint_Ioi_same : Disjoint (Ioc a b) (Ioi b) :=
   Ioc_disjoint_Ioi le_rfl
 
+@[to_dual Iio_disjoint_Ioi_of_not_lt]
 theorem Ioi_disjoint_Iio_of_not_lt (h : ¬a < b) : Disjoint (Ioi a) (Iio b) :=
   disjoint_left.mpr fun _ hx hy ↦ h (hx.trans hy)
 
+@[to_dual Iio_disjoint_Ioi_of_le]
 theorem Ioi_disjoint_Iio_of_le (h : a ≤ b) : Disjoint (Ioi b) (Iio a) :=
   Ioi_disjoint_Iio_of_not_lt (not_lt_of_ge h)
 
-@[simp]
+@[to_dual Iio_disjoint_Ioi_same]
```

## v0030  PR 28649 (human) — [Merged by Bors] - doc(Probability): miscellaneous typo fixes
Mathlib/Probability/Moments/Basic.lean:25  kind=review_comment  by grunweg  family=F10 documentation
**ASK:** spell out `mgf` instead?
```
@@ -22,9 +22,9 @@ import Mathlib.Probability.IdentDistrib
 ## Main results
 
 * `ProbabilityTheory.IndepFun.mgf_add`: if two real random variables `X` and `Y` are independent
-  and their mgfs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
+  and their MGFs are defined at `t`, then `mgf (X + Y) μ t = mgf X μ t * mgf Y μ t`
```

## v0091  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/Data/Rat/Lemmas.lean:303  kind=review_comment  by vihdzp  family=F3 registration
**ASK:** Same here.
```
@@ -300,10 +300,8 @@ theorem inv_natCast_num_of_pos {a : ℕ} (ha0 : 0 < a) : (a : ℚ)⁻¹.num = 1
   inv_intCast_num_of_pos (mod_cast ha0 : 0 < (a : ℤ))
 
 theorem inv_intCast_den_of_pos {a : ℤ} (ha0 : 0 < a) : ((a : ℚ)⁻¹.den : ℤ) = a := by
-  rw [← ofInt_eq_cast, ofInt, mk_eq_divInt, Rat.inv_divInt, divInt_eq_div, Nat.cast_one]
-  apply den_div_eq_of_coprime ha0
-  rw [Int.natAbs_one]
-  exact Nat.coprime_one_left _
+  simp only [den_inv, num_intCast]
```

## p0002  PR 42184 (human) — [Merged by Bors] - feat(Topology/InfiniteSum): non-negativity of tprod
Mathlib/Topology/Algebra/InfiniteSum/Order.lean:243  kind=review_comment  by CoolRmal  family=F7 generality
**ASK:** It seems like that at this step you can use `by_cases : L.NeBot` to remove the typeclass `L.NeBot` (and to do this, you probably need to generalize the typeclasses used in [finprod_nonneg](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/BigOperators/Finprod.html#finprod_nonneg) first)
```
@@ -234,6 +234,17 @@ protected theorem Multipliable.one_lt_tprod [L.LeAtTop] [L.NeBot] (hsum : Multip
 
 end OrderedCommGroup
 
+section WithZero
+
+theorem tprod_nonneg [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
+    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} (hf : ∀ i, 0 ≤ f i) :
+    0 ≤ ∏'[L] x, f x := by
+  by_cases h : Multipliable f L
+  · exact ge_of_tendsto' h.hasProd fun s ↦ s.prod_nonneg fun i _ ↦ hf i
```

## p0014  PR 43192 (human) — [Merged by Bors] - feat(Algebra/Category/ModuleCat): add abbrevs for Presheaves 
Mathlib/Algebra/Category/ModuleCat/Presheaf/OfCommRing.lean:43  kind=review_comment  by joelriou  family=F2 interface
**ASK:** Could you add `by cat_disch` as default tactics?
```
rev mk (obj : ∀ (X : Cᵒᵖ), ModuleCat.{v} (R.obj X)) (map : ∀ {X Y : Cᵒᵖ} (f : X ⟶ Y),
+      obj X ⟶ (ModuleCat.restrictScalars (R.map f).hom).obj (obj Y))
+    (map_id : ∀ (X : Cᵒᵖ), map (𝟙 X) = (ModuleCat.restrictScalarsId' (R.map (𝟙 X)).hom
+      (congrArg CommRingCat.Hom.hom (R.map_id X))).inv.app _)
+    (map_comp : ∀ {X Y Z : Cᵒᵖ} (f : X ⟶ Y) (g : Y ⟶ Z),
+      map (f ≫ g) = map f ≫ (ModuleCat.restrictScalars _).map (map g) ≫
+        (ModuleCat.restrictScalarsComp' (R.map f).hom (R.map g).hom (R.map (f ≫ g)).hom
+          (congrArg CommRingCat.Hom.hom <| R.map_comp f g)).inv.app _) :
```

## p0000  PR 41930 (human) — [Merged by Bors] - fix(GroupTheory/Coprod): fix recursor argument name
None:None  kind=issue_comment  by ocfnash  family=F12 PR level
**ASK:** Can you explain why the old names are bad / wrong?
```

```

## v0055  PR 29842 (human) — [Merged by Bors] - feat(TangentCone): generalize some lemmas to TVS
Mathlib/Analysis/Calculus/TangentCone.lean:120  kind=review_comment  by themathqueen  family=F1 proof
**ASK:** if you want, you can make it more compact:
```suggestion
  rw [tendsto_norm_atTop_iff_cobounded] at hc
  simpa using Tendsto.congr' this <| (tendsto_inv₀_cobounded.comp hc).smul hd
```
```
 n in l, ‖c n‖⁻¹ * ‖c n • d n‖ = ‖d n‖ := by
-    refine (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn => ?_
-    rw [norm_smul, ← mul_assoc, inv_mul_cancel₀, one_mul]
-    rwa [Ne, norm_eq_zero]
-  have D : Tendsto (fun n => ‖d n‖) l (𝓝 0) := Tendsto.congr' this C
-  rw [tendsto_zero_iff_norm_tendsto_zero]
-  exact D
+  have : ∀ᶠ n in l, (c n)⁻¹ • c n • d n = d n :=
+    (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn ↦ inv_smul_smul₀ hn (d n)
+  apply Tendsto.congr' this
+  rw [tendsto_norm_atTop_iff_cobounded] at hc
+  simpa using (tendsto_inv₀_cobounded.comp hc).smul hd
```

## p0011  PR 43167 (human) — [Merged by Bors] - feat(GroupTheory/Commutator/Basic): prove `⁅H ⊔ K, N⁆ = ⁅H, N
Mathlib/GroupTheory/Commutator/Basic.lean:337  kind=review_comment  by kim-em  family=F4 derive, don't restate
**ASK:** Missing `@[to_additive]` here, on line 357, and on the private lemma
```
(H K N : Subgroup G) [(⁅H, N⁆ ⊔ ⁅K, N⁆).Normal] :
+    ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
+  refine le_antisymm ?_
+    (sup_le (commutator_mono_left le_sup_left) (commutator_mono_left le_sup_right))
+  have hH : ⁅H, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_left
+  have hK : ⁅K, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_right
+  rw [← QuotientGroup.ker_mk' (⁅H, N⁆ ⊔ ⁅K, N⁆), ← Subgroup.map_eq_bot_iff,
+    map_commutator, Subgroup.commutator_eq_bot_iff_le_centralizer] at hH hK ⊢
+  rw [map_sup]
+  exact sup_le hH hK
+
+theorem commutator_sup_left (H K N : Subgroup G) [N.Normal] : ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
```

## v0064  PR 30641 (human) — feat: elementary lemmas aiding computations with `log⁺`
Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean:103  kind=review_comment  by grunweg  family=F8 naming
**ASK:** I think `x` might be more conventional for a real number --- though this file uses a mix of different conventions (sometimes `x`, sometimes `a` and `b`, sometimes `r`). In other words, consider my suggestion optional.
```suggestion
@[simp]
lemma posLog_pow {n : ℕ} {x : ℝ} : log⁺ (x ^ n) = n * log⁺ x := by
```
```
@@ -91,9 +98,21 @@ theorem monotoneOn_posLog : MonotoneOn log⁺ (Set.Ici 0) := by
     simp only [this, and_true, ge_iff_le]
     linarith
 
+/-- The function `log⁺` commutes with taking powers. -/
+@[simp] lemma posLog_pow {n : ℕ} {a : ℝ} :
+    log⁺ (a ^ n) = n * log⁺ a := by
```

## p0009  PR 43167 (human) — [Merged by Bors] - feat(GroupTheory/Commutator/Basic): prove `⁅H ⊔ K, N⁆ = ⁅H, N
Mathlib/Algebra/Group/Subgroup/Pointwise.lean:13  kind=review_comment  by kim-em  family=F9 formatting
**ASK:** ```suggestion
```
```
@@ -10,6 +10,7 @@ public import Mathlib.Algebra.Group.Pointwise.Set.Lattice
 public import Mathlib.Algebra.Group.Subgroup.MulOppositeLemmas
 public import Mathlib.Algebra.Group.Subgroup.ZPowers.Basic
 public import Mathlib.Algebra.Group.Submonoid.Pointwise
+public import Mathlib.GroupTheory.Commutator.Basic
```

## v0060  PR 30458 (AI) — chore(Algebra): misc. generalizations
Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean:1249  kind=review_comment  by themathqueen  family=F2 interface
**ASK:** you don't need to section these off
just keep things the same as before, collect the common variables, and then add variables as needed
so, in this case, instead of `variable [Group α]` at the start, change it to `[DivisionMonoid α]`, and keep the rest the same, and before this lemma add:
```suggestion
variable [IsLeftCancelMul α] in
@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by
```
```
@@ -1241,19 +1241,33 @@ lemma card_le_card_pow (hn : n ≠ 0) : #s ≤ #(s ^ n) := by
 
 end CancelMonoid
 
-section Group
-variable [Group α] [DecidableEq α] {s t : Finset α}
+section DivisionMonoid
+
+section LeftCancel
+variable [DivisionMonoid α] [IsLeftCancelMul α] [DecidableEq α] {s t : Finset α}
+
+@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by
```

## p0010  PR 43167 (human) — [Merged by Bors] - feat(GroupTheory/Commutator/Basic): prove `⁅H ⊔ K, N⁆ = ⁅H, N
Mathlib/GroupTheory/Commutator/Basic.lean:337  kind=review_comment  by kim-em  family=F8 naming
**ASK:** :robot: says: `left`/`right` look swapped: `inf_sup_left : a ⊓ (b ⊔ c)`, `Submodule.mul_sup : M * (N ⊔ P)`, `sup_le_sup_left (h) (c) : c ⊔ a ≤ c ⊔ b` all put the sup in the *second* argument for `_left`. So `⁅H ⊔ K, N⁆` would be `commutator_sup_right`, and `⁅N, H ⊔ K⁆` at line 357 `commutator_sup_left`.
```
(H K N : Subgroup G) [(⁅H, N⁆ ⊔ ⁅K, N⁆).Normal] :
+    ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
+  refine le_antisymm ?_
+    (sup_le (commutator_mono_left le_sup_left) (commutator_mono_left le_sup_right))
+  have hH : ⁅H, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_left
+  have hK : ⁅K, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_right
+  rw [← QuotientGroup.ker_mk' (⁅H, N⁆ ⊔ ⁅K, N⁆), ← Subgroup.map_eq_bot_iff,
+    map_commutator, Subgroup.commutator_eq_bot_iff_le_centralizer] at hH hK ⊢
+  rw [map_sup]
+  exact sup_le hH hK
+
+theorem commutator_sup_left (H K N : Subgroup G) [N.Normal] : ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
```

## v0029  PR 28649 (human) — [Merged by Bors] - doc(Probability): miscellaneous typo fixes
Mathlib/Probability/Martingale/Upcrossing.lean:698  kind=review_comment  by grunweg  family=F10 documentation
**ASK:** I disagree with this one, please revert.
```
@@ -695,7 +695,7 @@ This inequality is central for the martingale convergence theorem as it provides
 for the upcrossings.
 
 We note that on top of taking the supremum on both sides of the inequality, we had also used
-the monotone convergence theorem on the left hand side to take the supremum outside of the
+the monotone convergence theorem on the left-hand side to take the supremum outside of the
```

## v0053  PR 29842 (human) — [Merged by Bors] - feat(TangentCone): generalize some lemmas to TVS
None:None  kind=issue_comment  by eric-wieser  family=F12 PR level
**ASK:** How does this interact with #24163? When I tried something similar to this 8 months ago in #21065, I thought the consensus was to change the definition.

If you've changed your mind, could you explain why in the PR description?
```

```

## v0094  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/Probability/Kernel/Disintegration/Integral.lean:55  kind=review_comment  by artie2000  family=F1 proof
**ASK:** ````suggestion
simpa [this] using (Kernel.compProd_apply_prod hs ht).symm
````
```
 β} (hs : Measur
     ∫⁻ b in s, Kernel.condKernel κ (a, b) t ∂(Kernel.fst κ a) = κ a (s ×ˢ t) := by
   have : κ a (s ×ˢ t) = (Kernel.fst κ ⊗ₖ Kernel.condKernel κ) a (s ×ˢ t) := by
     congr; exact (κ.disintegrate _).symm
-  rw [this, Kernel.compProd_apply (hs.prod ht)]
-  classical
-  have : ∀ b, Kernel.condKernel κ (a, b) {c | (b, c) ∈ s ×ˢ t}
-      = s.indicator (fun b ↦ Kernel.condKernel κ (a, b) t) b := by
-    intro b
-    by_cases hb : b ∈ s <;> simp [hb]
-  simp_rw [Set.preimage, this]
-  rw [lintegral_indicator hs]
+  simp only [this]
+  exact (Kernel.compProd_apply_prod hs ht).symm
```

## v0090  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/Data/Finset/Image.lean:75  kind=review_comment  by vihdzp  family=F3 registration
**ASK:** Both of these should probably be tagged with `grind`.
```
@@ -72,11 +72,8 @@ theorem mem_map {b : β} : b ∈ s.map f ↔ ∃ a ∈ s, f a = b :=
 -- Higher priority to apply before `mem_map`.
 @[simp 1100]
 theorem mem_map_equiv {f : α ≃ β} {b : β} : b ∈ s.map f.toEmbedding ↔ f.symm b ∈ s := by
-  rw [mem_map]
-  exact
-    ⟨by
-      rintro ⟨a, H, rfl⟩
-      simpa, fun h => ⟨_, h, by simp⟩⟩
+  simp only [mem_map, Equiv.coe_toEmbedding]
```

## v0092  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/MeasureTheory/Constructions/Pi.lean:462  kind=review_comment  by artie2000  family=F1 proof
**ASK:** `simpa using`?
```
@@ -458,12 +458,8 @@ lemma pi_map_piCongrLeft [hι' : Fintype ι'] (e : ι ≃ ι') {β : ι' → Typ
     refine (e.forall_congr ?_).symm
     intro i
     rw [MeasurableEquiv.piCongrLeft_apply_apply e x i]
-  rw [this, pi_pi, Finset.prod_equiv e.symm]
-  · simp only [Finset.mem_univ, implies_true]
-  intro i _
-  simp only [s']
-  congr
-  all_goals rw [e.apply_symm_apply]
+  simp only [pi_pi, this]
+  exact Fintype.prod_equiv _ _ _ (congrFun rfl)
```

## v0095  PR 32875 (human) — [Merged by Bors] - chore: golf using `grind` and `simp`
Mathlib/Probability/Kernel/Disintegration/Integral.lean:147  kind=review_comment  by artie2000  family=F1 proof
**ASK:** simpa
```
@@ -149,14 +143,8 @@ lemma setLIntegral_condKernel_eq_measure_prod {s : Set β} (hs : MeasurableSet s
     ∫⁻ b in s, ρ.condKernel b t ∂ρ.fst = ρ (s ×ˢ t) := by
   have : ρ (s ×ˢ t) = (ρ.fst ⊗ₘ ρ.condKernel) (s ×ˢ t) := by
     congr; exact (ρ.disintegrate _).symm
-  rw [this, compProd_apply (hs.prod ht)]
-  classical
-  have : ∀ b, ρ.condKernel b (Prod.mk b ⁻¹' s ×ˢ t)
-      = s.indicator (fun b ↦ ρ.condKernel b t) b := by
-    intro b
-    by_cases hb : b ∈ s <;> simp [hb]
-  simp_rw [this]
-  rw [lintegral_indicator hs]
+  simp only [this]
+  exact (compProd_apply_prod hs ht).symm
```

## p0003  PR 42184 (human) — [Merged by Bors] - feat(Topology/InfiniteSum): non-negativity of tprod
Mathlib/Topology/Algebra/InfiniteSum/Order.lean:243  kind=review_comment  by CoolRmal  family=F6 statement and API design
> (in reply to) It seems like that at this step you can use `by_cases : L.NeBot` to remove the typeclass `L.NeBot` (and to do this, you probably need to generalize the typeclasses used in [finprod_nonneg](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Algebra/BigOperators/Finprod.html#finprod_nonneg) first)
**ASK:** and maybe you can provide a HasProd version of this lemma (as this seems to be the convention in this file)
```
@@ -234,6 +234,17 @@ protected theorem Multipliable.one_lt_tprod [L.LeAtTop] [L.NeBot] (hsum : Multip
 
 end OrderedCommGroup
 
+section WithZero
+
+theorem tprod_nonneg [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
+    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} (hf : ∀ i, 0 ≤ f i) :
+    0 ≤ ∏'[L] x, f x := by
+  by_cases h : Multipliable f L
+  · exact ge_of_tendsto' h.hasProd fun s ↦ s.prod_nonneg fun i _ ↦ hf i
```

## v0062  PR 30458 (AI) — chore(Algebra): misc. generalizations
Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean:1251  kind=review_comment  by themathqueen  family=F1 proof
**ASK:** does the old proof not work?
```
@@ -1241,19 +1241,33 @@ lemma card_le_card_pow (hn : n ≠ 0) : #s ≤ #(s ^ n) := by
 
 end CancelMonoid
 
-section Group
-variable [Group α] [DecidableEq α] {s t : Finset α}
+section DivisionMonoid
+
+section LeftCancel
+variable [DivisionMonoid α] [IsLeftCancelMul α] [DecidableEq α] {s t : Finset α}
+
+@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by
+  obtain ⟨a, ha⟩ := hs
+  exact card_le_card_image₂_left _ ha (div_right_injective (b := a))
```
