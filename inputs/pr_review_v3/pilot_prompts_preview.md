# Pilot prompt preview — raw sites (leak-fixed), no-retrieval battery, apply_all_v2

worklist: worklist_v3_raw_nr_by_pr.jsonl | window size 8 | rendered with real PR context



==========================================================================================
## PR 33065 — window 1/1 — prompt 5,389 chars
==========================================================================================

## PR #33065 — feat: a function is always continuous at an isolated point

## Description

This PR adds a lemma `ContinuousWithinAt.of_not_accPt`, which says that a function is continuous at a point `x` within a set `s` if `x` is not an accumulated point of `s`.

Zulip discussion: [#Is there code for X? > Continuity at isolated points](https://leanprover.zulipchat.com/#narrow/channel/217875-Is-there-code-for-X.3F/topic/Continuity.20at.20isolated.20points/with/562319753)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Topology/ContinuousOn.lean b/Mathlib/Topology/ContinuousOn.lean
--- a/Mathlib/Topology/ContinuousOn.lean
+++ b/Mathlib/Topology/ContinuousOn.lean
@@ -296,11 +296,22 @@ theorem continuousWithinAt_diff_self :
     ContinuousWithinAt f (s \ {x}) x ↔ ContinuousWithinAt f s x :=
   continuousWithinAt_singleton.diff_iff
 
+/-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulated point of
+`s`. -/
+lemma ContinuousWithinAt.of_not_accPt (h : ¬AccPt x (𝓟 s)) : ContinuousWithinAt f s x := by
+  rw [← continuousWithinAt_diff_self]
+  simp_all [ContinuousWithinAt, AccPt, ← nhdsWithin_inter', Set.diff_eq, Set.inter_comm]
+
 @[simp]
 theorem continuousWithinAt_compl_self :
     ContinuousWithinAt f {x}ᶜ x ↔ ContinuousAt f x := by
   rw [compl_eq_univ_diff, continuousWithinAt_diff_self, continuousWithinAt_univ]
 
+/-- A function is continuous at a point `x` if `x` is isolated. -/
+lemma ContinuousAt.of_not_accPt (h : ¬AccPt x (𝓟 {x}ᶜ)) : ContinuousAt f x := by
+  rw [← continuousWithinAt_compl_self]
+  exact ContinuousWithinAt.of_not_accPt h
+
 theorem ContinuousOn.mono (hf : ContinuousOn f s) (h : t ⊆ s) :
     ContinuousOn f t := fun x hx => (hf x (h hx)).mono_left (nhdsWithin_mono _ h)
 

```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 1 sites, 8 facet items

### Site 1: `Mathlib/Topology/ContinuousOn.lean` lines 296-317
```
ContinuousWithinAt f (s \ {x}) x ↔ ContinuousWithinAt f s x :=
   continuousWithinAt_singleton.diff_iff
 
/-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulated point of
`s`. -/
lemma ContinuousWithinAt.of_not_accPt (h : ¬AccPt x (𝓟 s)) : ContinuousWithinAt f s x := by
  rw [← continuousWithinAt_diff_self]
  simp_all [ContinuousWithinAt, AccPt, ← nhdsWithin_inter', Set.diff_eq, Set.inter_comm]

 @[simp]
 theorem continuousWithinAt_compl_self :
     ContinuousWithinAt f {x}ᶜ x ↔ ContinuousAt f x := by
   rw [compl_eq_univ_diff, continuousWithinAt_diff_self, continuousWithinAt_univ]
 
/-- A function is continuous at a point `x` if `x` is isolated. -/
lemma ContinuousAt.of_not_accPt (h : ¬AccPt x (𝓟 {x}ᶜ)) : ContinuousAt f x := by
  rw [← continuousWithinAt_compl_self]
  exact ContinuousWithinAt.of_not_accPt h

 theorem ContinuousOn.mono (hf : ContinuousOn f s) (h : t ⊆ s) :
     ContinuousOn f t := fun x hx => (hf x (h hx)).mono_left (nhdsWithin_mono _ h)
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 1/6 — prompt 21,890 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 1/6: sites 1-8 of 47)

### Site 1: `Mathlib/Algebra/AffineMonoid/Irreducible.lean` lines 26-33
```
/-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Algebra/AffineMonoid/Irreducible.lean` lines 36-51
```
/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Algebra/AffineMonoid/Irreducible.lean` lines 54-61
```
/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
/-- A finitely generated additive monoid with a single unit has finitely many irreducible
elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Algebra/AffineMonoid/Irreducible.lean` lines 67-74
```
/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
/-- A finitely generated cancellative additive monoid with a single unit is generated by its
(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Algebra/AffineMonoid/Irreducible.lean` lines 87-94
```
simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Algebra/Algebra/Basic.lean` lines 344-350
```
theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Algebra/DirectSum/Basic.lean` lines 266-280
```
/-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
    left_inv x :=
      DirectSum.induction_on x
        (by rw [map_zero, map_zero])
        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
        (fun x y ihx ihy => by grind)
    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/Algebra/Group/Action/End.lean` lines 199-205
```
rfl
 
 lemma MulAction.toPerm_one :
    (MulAction.toPerm (1 : G)) = (1 : Equiv.Perm α) := by
   aesop
 
 end Group
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 2/6 — prompt 20,572 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 2/6: sites 9-16 of 47)

### Site 1: `Mathlib/Algebra/Group/Action/End.lean` lines 217-223
```
rfl
 
 theorem AddAction.toPerm_zero :
    (AddAction.toPerm (0 : G)) = (1 : Equiv.Perm α) := by
   aesop
 
 end AddGroup
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Algebra/GroupWithZero/Associated.lean` lines 355-361
```
variable [Monoid M] [Subsingleton Mˣ]
 
 theorem associated_iff_eq {x y : M} : x ~ᵤ y ↔ x = y := by
  simp [Associated, Units.eq_one]
 
 theorem associated_eq_eq : (Associated : M → M → Prop) = Eq := by
   ext
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Algebra/Module/TransferInstance.lean` lines 42-49
```
Module R α :=
   letI := Equiv.addCommMonoid e
   { Equiv.distribMulAction R e with
    zero_smul := by simp [smul_def, zero_smul, zero_def]
    add_smul := by simp [add_def, smul_def, add_smul] }
 
 variable (R) in
 /-- An equivalence `e : α ≃ β` gives a linear equivalence `α ≃ₗ[R] β`
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Algebra/Polynomial/AlgebraMap.lean` lines 23-32
```
## Main definitions
 
 - `Polynomial.aeval`: given a valuation `x` of the variable in an `R`-algebra `A`, `aeval R A x` is
  the unique `R`-algebra homomorphism from `R[X]` to `A` sending `X` to `x`.
 
 - `Polynomial.mapAlgHom` : given `φ : S →ₐ[R] S'`, `mapAlgHom φ` applies `φ` on the
  coefficients of a polynomial in `S[X]`.
 
 -/
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Algebra/Polynomial/AlgebraMap.lean` lines 567-580
```
open LinearMap TensorProduct in
 lemma X_pow_smul_rTensor_monomial [CommSemiring S] [Algebra R S] {N : Type*}
     [AddCommMonoid N] [Module R N] (k : ℕ) (sn : S ⊗[R] N) :
    X (R := S) ^ k • (LinearMap.rTensor N ((monomial 0).restrictScalars R)) sn =
      (LinearMap.rTensor N ((monomial k).restrictScalars R)) sn := by
  induction sn using TensorProduct.induction_on with
  | zero => simp
  | add x y hx hy => simp [hx, hy]
  | tmul s n =>
    simp only [rTensor_tmul, coe_restrictScalars, monomial_zero_left]
    rw [smul_tmul', smul_eq_mul, mul_comm, C_mul_X_pow_eq_monomial]
 
 
 end CommSemiring
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Algebra/Polynomial/Degree/Operations.lean` lines 334-340
```
theorem leadingCoeff_mul' (h : leadingCoeff p * leadingCoeff q ≠ 0) :
     leadingCoeff (p * q) = leadingCoeff p * leadingCoeff q := by
  simp [← coeff_natDegree, natDegree_mul' h, coeff_mul_degree_add_degree]
 
 theorem leadingCoeff_pow' : leadingCoeff p ^ n ≠ 0 → leadingCoeff (p ^ n) = leadingCoeff p ^ n :=
   Nat.recOn n (by simp) fun n ih h => by
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Algebra/Polynomial/Factors.lean` lines 486-492
```
trans ((s ×ˢ g.roots).map fun ij ↦ (-1) * (ij.1 - ij.2)).prod
   · rw [← Multiset.map_swap_product, Multiset.map_map]; simp
   · rw [Multiset.prod_map_mul]; simp [map_sub_sprod_roots_eq_prod_map_eval _ _ hg hg']

 end CommRing
 
 section DivisionSemiring
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/AlgebraicGeometry/AffineTransitionLimit.lean` lines 1022-1028
```
obtain ⟨j, hj⟩ := Scheme.exists_isAffine_of_isLimit _ _ (isLimitOpensCone D c hc i U)
   refine ⟨_, _, hj, ?_⟩
   rw [← Scheme.Hom.comp_preimage, c.w]
  simp
 
 open TopologicalSpace in
 include hc in
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 3/6 — prompt 20,629 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 3/6: sites 17-24 of 47)

### Site 1: `Mathlib/AlgebraicGeometry/AffineTransitionLimit.lean` lines 1048-1054
```
refine ⟨k, s, fun x ↦ D.map (fkj ≫ fi x.1 x.2) ⁻¹ᵁ V _, ?_, fun k ↦ ⟨(hV k).preimage _, ?_⟩⟩
   · refine top_le_iff.mp (e.symm.trans_le ?_)
     simp_rw [Hom.preimage_iSup, ← Hom.comp_preimage, iSup_subtype, ← D.map_comp]
    simp
   · rw [← hVU, ← Hom.comp_preimage, c.w]
 
 end IsAffine
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/AlgebraicTopology/ModelCategory/Over.lean` lines 19-25
```
(resp. a fibration, a weak equivalence) if the
 underlying morphism `f.left : X.left ⟶ Y.left` is.
 (Apart from the existence of (finite) limits
from `Mathlib.CategoryTheory.Limits.Constructions.Over.Basic`, the verification
 of the axioms is straightforward.)
 
 ## TODO
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/AlgebraicTopology/ModelCategory/Over.lean` lines 49-55
```
lemma cofibrations_over_iff {X Y : Over S} (f : X ⟶ Y) :
     Cofibration f ↔ Cofibration f.left := by
  simp only [cofibration_iff, cofibrations_over_def, MorphismProperty.over_iff]
 
 instance {X Y : Over S} (f : X ⟶ Y) [Cofibration f] : Cofibration f.left := by
   rwa [← cofibrations_over_iff]
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/AlgebraicTopology/ModelCategory/Over.lean` lines 73-79
```
lemma fibrations_over_iff {X Y : Over S} (f : X ⟶ Y) :
     Fibration f ↔ Fibration f.left := by
  simp only [fibration_iff, fibrations_over_def, MorphismProperty.over_iff]
 
 instance {X Y : Over S} (f : X ⟶ Y) [Fibration f] : Fibration f.left := by
   rwa [← fibrations_over_iff]
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/AlgebraicTopology/ModelCategory/Over.lean` lines 97-103
```
lemma weakEquivalences_over_iff {X Y : Over S} (f : X ⟶ Y) :
     WeakEquivalence f ↔ WeakEquivalence f.left := by
  simp only [weakEquivalence_iff, weakEquivalences_over_def, MorphismProperty.over_iff]
 
 instance {X Y : Over S} (f : X ⟶ Y) [WeakEquivalence f] : WeakEquivalence f.left := by
   rwa [← weakEquivalences_over_iff]
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Analysis/AbsoluteValue/Equivalence.lean` lines 108-118
```
variable [IsStrictOrderedRing S]
 
 theorem isEquiv_iff_lt_one_iff :
     v.IsEquiv w ↔ ∀ x, v x < 1 ↔ w x < 1 := by
   refine ⟨fun h _ ↦ h.lt_one_iff, fun h x y ↦ ?_⟩
  rcases eq_or_ne (v x) 0 with (_ | hy₀)
  · simp_all
   rw [le_iff_le_iff_lt_iff_lt, ← one_mul (v x), ← mul_inv_lt_iff₀ (by simp_all), ← one_mul (w x),
     ← mul_inv_lt_iff₀ (by simp_all), ← map_inv₀, ← map_mul, ← map_inv₀, ← map_mul]
   exact h _
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Analysis/LocallyConvex/PointwiseConvergence.lean` lines 78-85
```
theorem tendsto_nhds_atTop [SemilatticeSup α] [Nonempty α] (u : α → E →SLₚₜ[σ] F)
     (y₀ : E →SLₚₜ[σ] F) :
    Tendsto u atTop (𝓝 y₀) ↔
      ∀ (x : E) (ε : ℝ), 0 < ε → ∃ (k₀ : α), ∀ (k : α), k₀ ≤ k → ‖u k x - y₀ x‖ < ε :=
   PointwiseConvergenceCLM.withSeminorms.tendsto_nhds_atTop _ _
 
 end Tendsto
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/Data/Set/Lattice.lean` lines 1365-1372
```
inf_iInf_nat_succ u
 
 theorem iUnion_le_nat : ⋃ n : ℕ, {i | i ≤ n} = Set.univ :=
  subset_antisymm (Set.subset_univ _)
    (fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr (le_refl _)))
 
 end Set
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 4/6 — prompt 21,020 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 4/6: sites 25-32 of 47)

### Site 1: `Mathlib/LinearAlgebra/PiTensorProduct.lean` lines 322-329
```
/-- Every element of `⨂[R] i, s i` has a lift in `FreeAddMonoid (R × Π i, s i)`.
 -/
 lemma nonempty_lifts (x : ⨂[R] i, s i) : Set.Nonempty (lifts x) := by
  existsi Quot.out x
  simp [lifts, ← AddCon.quot_mk_eq_coe]
 
 /-- The empty list lifts the element `0` of `⨂[R] i, s i`.
 -/
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/Integral/RieszMarkovKakutani/Real.lean` lines 478-489
```
exact Measure.exists_regular_eq_of_compactSpace μ'
   refine ⟨ν'.map Subtype.val, Measure.InnerRegular.map_of_continuous (by fun_prop),
     by infer_instance, fun g ↦ ?_⟩
  convert hν' (g.compContinuous ⟨Subtype.val, by fun_prop⟩)
  · simp only [BoundedContinuousFunction.compContinuous_apply, ContinuousMap.coe_mk]
     rw [← integral_map (φ := Subtype.val) (by fun_prop) (by fun_prop)]
    simp only [map_comap_subtype_coe hK.measurableSet, μ', Measure.restrict_eq_self_of_ae_mem h]
   · rw [integral_map (φ := Subtype.val) (by fun_prop) (by fun_prop)]
    simp
 
 end Compact
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/Measure/ProbabilityMeasure.lean` lines 237-243
```
refine ⟨fun ⟨ν, hν⟩ ↦ by simp [← hν], fun h ↦ ?_⟩
   refine ⟨⟨μ, isProbabilityMeasure_iff_real.2 (by simpa using h)⟩, ?_⟩
   ext s hs
  simp
 
 theorem toFiniteMeasure_nonzero (μ : ProbabilityMeasure Ω) : μ.toFiniteMeasure ≠ 0 := by
   simp [← FiniteMeasure.mass_nonzero_iff]
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/MeasureTheory/Measure/Stieltjes.lean` lines 112-118
```
/-- Bundled monotone right-continuous real functions, used to construct Stieltjes measures. -/
 structure StieltjesFunction where
  /-- The underlying function `R → ℝ`.
 
   Do NOT use directly. Use the coercion instead. -/
   toFun : R → ℝ
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Probability/Distributions/Gaussian/Basic.lean` lines 126-132
```
/-- The map of a Gaussian measure by a continuous linear map is Gaussian. -/
 instance isGaussian_map (L : E →L[ℝ] F) : IsGaussian (μ.map L) :=
  isGaussian_map_of_measurable (by fun_prop)
 
 instance isGaussian_map_equiv (L : E ≃L[ℝ] F) : IsGaussian (μ.map L) :=
   isGaussian_map (L : E →L[ℝ] F)
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/RingTheory/AdicCompletion/Basic.lean` lines 88-99
```
simp only [Submodule.toAddSubgroup_toAddSubmonoid, Submodule.smul_toAddSubmonoid,
       Submodule.top_toAddSubmonoid]
     rw [AddSubmonoid.smul_le]
    intro r hr m hm
     rw [← algebraMap_smul S r m]
    apply AddSubmonoid.smul_mem_smul ?_ hm
    have := Ideal.mem_map_of_mem (algebraMap R S) hr
    simp only [Ideal.map_pow] at this
    exact Ideal.pow_right_mono hIJ n this
   · exact h n
 
 variable (I) in
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/RingTheory/IntegralClosure/IntegrallyClosed.lean` lines 127-134
```
IsFractionRing.injective R K]
 
 instance : IsIntegrallyClosedIn (integralClosure R A) A :=
  isIntegrallyClosedIn_iff.mpr
    ⟨FaithfulSMul.algebraMap_injective _ _, fun h ↦ ⟨⟨_, isIntegral_trans _ h⟩, rfl⟩⟩
 
 instance : IsIntegrallyClosedIn (integralClosure R A).toSubring A :=
   inferInstanceAs (IsIntegrallyClosedIn (integralClosure R A) A)
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/RingTheory/IntegralClosure/IntegrallyClosed.lean` lines 139-145
```
protected theorem isIntegrallyClosedIn_iff :
     IsIntegrallyClosedIn S A ↔ ∀ ⦃x : A⦄, IsIntegral S x → x ∈ S := by
  rw [isIntegrallyClosedIn_iff, and_iff_right (FaithfulSMul.algebraMap_injective _ _)]
   exact congr(∀ _ _, _ ∈ $Subtype.range_val)
 
 protected theorem isIntegrallyClosed_iff [IsFractionRing S A] :
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 5/6 — prompt 21,323 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 5/6: sites 33-40 of 47)

### Site 1: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 189-198
```
| one => simp
   | add_two n ih1 ih2 =>
     have : (2 * X * T R (n + 1)).degree = ↑(n + 2) := by
      rw [mul_assoc, ← C_ofNat, degree_C_mul two_ne_zero, mul_comm, degree_mul_X, ih1]
      norm_cast
     rw [T_add_two, degree_sub_eq_left_of_degree_lt]
    · rw [this]; norm_cast
     · rw [ih2, this]; tauto
   | neg n ih => simp [ih]
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 213-220
```
rw [T_add_two, leadingCoeff_sub_of_degree_lt, leadingCoeff_mul, ih1,
       leadingCoeff_mul, leadingCoeff_X, this]
     · norm_cast; simp [pow_add, mul_comm]
    · rw [mul_assoc, ← C_ofNat, degree_C_mul two_ne_zero, mul_comm, degree_mul_X, degree_T,
        degree_T]
       tauto
   | neg n ih => simp [ih]
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 333-343
```
| zero => simp
   | one =>
     norm_cast
    rw [U_one, ← C_ofNat, degree_C_mul_X two_ne_zero]
   | more n ih1 ih2 =>
     push_cast; push_cast at ih2
    have : (2 * X * U R (n + 1)).degree = ↑(n + 2) := by
      rw [mul_assoc, ← C_ofNat, degree_C_mul two_ne_zero, mul_comm, degree_mul_X, ih2]
       norm_cast
     rw [U_add_two, degree_sub_eq_left_of_degree_lt]
     · rw [this]; norm_cast
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 377-383
```
theorem leadingCoeff_U_natCast [IsDomain R] [NeZero (2 : R)] (n : ℕ) :
     (U R n).leadingCoeff = 2 ^ n := by
   have : leadingCoeff (2 : R[X]) = 2 := by
    rw [← C_ofNat, leadingCoeff_C]
   induction n using Nat.twoStepInduction with
   | zero => simp
   | one => simp [this]
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 386-393
```
rw [U_add_two, leadingCoeff_sub_of_degree_lt, leadingCoeff_mul, ih2,
       leadingCoeff_mul, leadingCoeff_X, this]
     · norm_cast; rw [pow_add, pow_add]; ring_nf
    · norm_cast
      rw [mul_assoc, ← C_ofNat, degree_C_mul two_ne_zero, mul_comm, degree_mul_X,
         degree_U_natCast R n, degree_U_natCast R (n + 1)]
       norm_cast; omega
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 481-491
```
| add_two n ih1 ih2 =>
     have h₁ := C_add_two R n
     have h₂ := C_sub_two R (-n)
    linear_combination (norm := ring_nf) (X : R[X]) * ih1 - ih2 - h₁ + h₂
   | neg_add_one n ih1 ih2 =>
     have h₁ := C_add_one R n
     have h₂ := C_sub_one R (-n)
    linear_combination (norm := ring_nf) (X : R[X]) * ih1 - ih2 + h₁ - h₂
 
 theorem C_natAbs (n : ℤ) : C R n.natAbs = C R n := by
   obtain h | h := Int.natAbs_eq n <;> nth_rw 2 [h]; simp
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 593-603
```
| add_two n ih1 ih2 =>
     have h₁ := S_add_one R n
     have h₂ := S_sub_two R (-n - 1)
    linear_combination (norm := ring_nf) (X : R[X]) * ih1 - ih2 + h₁ + h₂
   | neg_add_one n ih1 ih2 =>
     have h₁ := S_eq R n
     have h₂ := S_sub_two R (-n)
    linear_combination (norm := ring_nf) (X : R[X]) * ih1 - ih2 + h₁ + h₂
 
 theorem S_neg (n : ℤ) : S R (-n) = -S R (n - 2) := by simpa [sub_sub] using S_neg_sub_one R (n - 1)
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 672-683
```
have h₁ := S_add_two R (n + 1)
     have h₂ := S_add_two R n
     have h₃ := C_add_two R (n + 1)
    linear_combination (norm := ring_nf) -h₃ - (X : R[X]) * h₂ + 2 * h₁ + (X : R[X]) * ih1 - ih2
   | neg_add_one n ih1 ih2 =>
     have h₁ := S_add_two R (-n - 1)
     have h₂ := S_add_two R (-n)
     have h₃ := C_add_two R (-n)
    linear_combination (norm := ring_nf) -h₃ + 2 * h₂ - (X : R[X]) * h₁ - ih2 + (X : R[X]) * ih1
 
 theorem C_eq_S_sub_X_mul_S (n : ℤ) : C R n = 2 * S R n - X * S R (n - 1) := by
   linear_combination (norm := ring_nf) - S_eq_X_mul_S_add_C R (n - 1)
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33081 — window 6/6 — prompt 19,727 chars
==========================================================================================

## PR #33081 — chore: tidy various files

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AffineMonoid/Irreducible.lean b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
--- a/Mathlib/Algebra/AffineMonoid/Irreducible.lean
+++ b/Mathlib/Algebra/AffineMonoid/Irreducible.lean
@@ -26,8 +26,8 @@ variable [CommMonoid M] [Subsingleton Mˣ] {S : Set M}
 
 /-- Any set `S` inside a monoid with a single unit contains the irreducible elements of the
 submonoid it generates. -/
-@[to_additive /-- Any set `S` inside a monoid with a single unit contains the irreducible elements
-of the submonoid it generates. -/]
+@[to_additive /-- Any set `S` inside an additive monoid with a single unit contains the irreducible
+elements of the submonoid it generates. -/]
 lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irreducible p} ⊆ S := by
   refine fun x hx ↦
       Submonoid.closure_induction (s := S) (motive := fun x _ ↦ (Irreducible x → x ∈ S))
@@ -36,16 +36,16 @@ lemma irreducible_mem_submonoidClosure_subset : {p ∈ Submonoid.closure S | Irr
 
 /-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/
 @[to_additive
-/-- In a monoid with a single unit, irreducible elements lie in all generating sets. -/]
+/-- In an additive monoid with a single unit, irreducible elements lie in all generating sets. -/]
 lemma irreducible_subset_of_submonoidClosure_eq_top (hS : Submonoid.closure S = ⊤) :
     {p | Irreducible p} ⊆ S := by
   simpa [hS] using irreducible_mem_submonoidClosure_subset (S := S)
 
 /-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
 elements. -/
 @[to_additive
-/-- A finitely generated submonoid of a monoid with a single unit has finitely many irreducible
-elements. -/]
+/-- A finitely generated submonoid of an additive monoid with a single unit has finitely many
+irreducible elements. -/]
 lemma Submonoid.FG.finite_irreducible_mem_submonoidClosure {S : Submonoid M} (hS : S.FG) :
     {p ∈ S | Irreducible p}.Finite := by
   obtain ⟨T, hT⟩ := hS; exact T.finite_toSet.subset <| hT ▸ irreducible_mem_submonoidClosure_subset
@@ -54,7 +54,8 @@ variable [Monoid.FG M]
 
 /-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/
 @[to_additive
-/-- A finitely generated monoid with a single unit has finitely many irreducible elements. -/]
+/-- A finitely generated additive monoid with a single unit has finitely many irreducible
+elements. -/]
 lemma finite_irreducible : {p : M | Irreducible p}.Finite := by
   simpa using Monoid.FG.fg_top.finite_irreducible_mem_submonoidClosure
 
@@ -66,8 +67,8 @@ variable [CancelCommMonoid M] [Subsingleton Mˣ]
 /-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
 irreducible elements. -/
 @[to_additive (attr := simp)
-/-- A finitely generated cancellative monoid with a single unit is generated by its (finitely many)
-irreducible elements. -/]
+/-- A finitely generated cancellative additive monoid with a single unit is generated by its
+(finitely many) irreducible elements. -/]
 lemma Submonoid.closure_irreducible [Monoid.FG M] :
     Submonoid.closure {p : M | Irreducible p} = ⊤ := by
   classical
@@ -86,8 +87,8 @@ lemma Submonoid.closure_irreducible [Monoid.FG M] :
   simp only [irreducible_iff, Set.mem_setOf_eq, not_and, not_forall, not_or] at hrirred
   obtain ⟨a, b, hr, ha, hb⟩ := hrirred <| by simpa
   -- Write `a = ∏ s ∈ S, s ^ m s`, `b = ∏ s ∈ S, s ^ n s` for some coefficients `m`, `n`.
-  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; trivial)
-  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; trivial)
+  obtain ⟨m, -, hm⟩ := Submonoid.mem_closure_finset (x := a).mp (by rw [hSgen]; exact mem_top _)
+  obtain ⟨n, -, hn⟩ := Submonoid.mem_closure_finset (x := b).mp (by rw [hSgen]; exact mem_top _)
   -- Single out the `r` term in the two products.
   replace hm : a = r ^ m r * ∏ s ∈ S \ {r}, s ^ m s := by
     rw [← hm, Finset.sdiff_singleton_eq_erase, ← Finset.mul_prod_erase _ _ hrS]
diff --git a/Mathlib/Algebra/Algebra/Basic.lean b/Mathlib/Algebra/Algebra/Basic.lean
--- a/Mathlib/Algebra/Algebra/Basic.lean
+++ b/Mathlib/Algebra/Algebra/Basic.lean
@@ -344,7 +344,7 @@ theorem coe_inj {a b : R} : (↑a : A) = ↑b ↔ a = b :=
 theorem coe_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   FaithfulSMul.algebraMap_eq_zero_iff _ _
 
-@[deprecated coe_eq_zero_iff (since := "29/09/2025")]
+@[deprecated coe_eq_zero_iff (since := "2025-10-21")]
 theorem lift_map_eq_zero_iff (a : R) : (↑a : A) = 0 ↔ a = 0 :=
   coe_eq_zero_iff _ _ _
 
diff --git a/Mathlib/Algebra/DirectSum/Basic.lean b/Mathlib/Algebra/DirectSum/Basic.lean
--- a/Mathlib/Algebra/DirectSum/Basic.lean
+++ b/Mathlib/Algebra/DirectSum/Basic.lean
@@ -266,16 +266,15 @@ instance uniqueOfIsEmpty [IsEmpty ι] : Unique (⨁ i, β i) :=
 /-- The natural equivalence between `⨁ _ : ι, M` and `M` when `Unique ι`. -/
 protected def id (M : Type v) (ι : Type* := PUnit) [AddCommMonoid M] [Unique ι] :
     (⨁ _ : ι, M) ≃+ M :=
-  {
-    DirectSum.toAddMonoid fun _ =>
-      AddMonoidHom.id
-        M with
+  { DirectSum.toAddMonoid fun _ => AddMonoidHom.id M with
     toFun := DirectSum.toAddMonoid fun _ => AddMonoidHom.id M
     invFun := of (fun _ => M) default
-    left_inv := fun x =>
-      DirectSum.induction_on x (by rw [map_zero, map_zero])
-        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of]; rfl) fun x y ihx ihy => by grind
-    right_inv := fun _ => toAddMonoid_of _ _ _ }
+    left_inv x :=
+      DirectSum.induction_on x
+        (by rw [map_zero, map_zero])
+        (fun p x => by rw [Unique.default_eq p, toAddMonoid_of, AddMonoidHom.id_apply])
+        (fun x y ihx ihy => by grind)
+    right_inv _ := toAddMonoid_of _ _ _ }
 
 section CongrLeft
 
diff --git a/Mathlib/Algebra/Group/Action/End.lean b/Mathlib/Algebra/Group/Action/End.lean
--- a/Mathlib/Algebra/Group/Action/End.lean
+++ b/Mathlib/Algebra/Group/Action/End.lean
@@ -199,7 +199,7
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 7 sites, 56 facet items (window 6/6: sites 41-47 of 47)

### Site 1: `Mathlib/RingTheory/Polynomial/Chebyshev.lean` lines 830-841
```
have h₁ := C_add_two R (m + k)
     have h₂ := C_sub_two R (m - k)
     have h₃ := C_add_two R k
    linear_combination (norm := ring_nf) C R m * h₃ - h₂ - h₁ - ih2 + (X : R[X]) * ih1
   | neg_add_one k ih1 ih2 =>
     have h₁ := C_add_two R (m + (-k - 1))
     have h₂ := C_sub_two R (m - (-k - 1))
     have h₃ := C_add_two R (-k - 1)
    linear_combination (norm := ring_nf) C R m * h₃ - h₂ - h₁ - ih2 + (X : R[X]) * ih1
 
 /-- The `(m * n)`-th Chebyshev `T` polynomial is the composition of the `m`-th and `n`-th. -/
 theorem T_mul (m n : ℤ) : T R (m * n) = (T R m).comp (T R n) := by
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/RingTheory/PolynomialLaw/Basic.lean` lines 388-397
```
have uFG : Subalgebra.FG (R := R) (φ R s).range := by
     rw [← Algebra.map_top]
     exact Subalgebra.FG.map _ Algebra.FiniteType.out
   set u' := rTensor M (φ R s').rangeRestrict.toLinearMap p' with hu'
   have u'FG : Subalgebra.FG (R := R) (φ R s').range := by
     rw [← Algebra.map_top]
     exact Subalgebra.FG.map _ Algebra.FiniteType.out
   have huu' : rTensor M (Subalgebra.val _).toLinearMap u =
     rTensor M (Subalgebra.val _).toLinearMap u' := by
     simp only [π] at h
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/RingTheory/PolynomialLaw/Basic.lean` lines 431-437
```
use p
     rw [← hu, ← Subalgebra.val_comp_inclusion hφ, comp_toLinearMap, rTensor_comp,
       LinearMap.comp_apply, ← hp, ← LinearMap.comp_apply, ← rTensor_comp, ← comp_toLinearMap]
    simp
   exact rTensor_surjective M (rangeRestrict_surjective φ)
 
 /-- Tensor products in `S ⊗[R] M` can be lifted to some
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Topology/LocalAtTarget.lean` lines 180-186
```
IsHomeomorph f ↔ ∀ i, IsHomeomorph ((U i).1.restrictPreimage f) := by
   simp_rw [isHomeomorph_iff_isEmbedding_surjective, forall_and,
     ← isEmbedding_iff_restrictPreimage hU h,
    surjective_iff_surjective_of_iUnion_eq_univ hU.iSup_set_eq_univ, Opens.carrier_eq_coe]
 
 omit [TopologicalSpace α] in
 theorem denseRange_iff_restrictPreimage :
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Topology/Metrizable/Basic.lean` lines 14-20
```
exists a metric space structure that generates the same topology.
 We define it without any reference to metric spaces in order to avoid importing the real numbers.
 For the proof that metrizable spaces admit a compatible metric,
see `Mathlib/Topology/Metrizable/Uniformity.lean`.
 -/
 
 -- don't import the real numbers
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Topology/Metrizable/Basic.lean` lines 31-37
```
/-- A topological space is *pseudometrizable* if there exists a pseudometric space structure
 compatible with the topology. To minimize imports, we implement this class in terms of the
existence of a countably generated uniformity inducing the topology, which is mathematically
 equivalent.
 To endow such a space with a compatible uniformity, use
 `letI : UniformSpace X := TopologicalSpace.pseudoMetrizableSpaceUniformity X`.
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Topology/Metrizable/Basic.lean` lines 109-115
```
/-- A topological space is metrizable if there exists a metric space structure compatible with the
 topology. To minimize imports, we implement this class in terms of the existence of a
countably generated uniformity inducing the topology, which is mathematically
 equivalent.
 To endow such a space with a compatible uniformity, use
 `letI : UniformSpace X := TopologicalSpace.pseudoMetrizableSpaceUniformity X`.
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33086 — window 1/1 — prompt 12,181 chars
==========================================================================================

## PR #33086 — feat(AlgebraicTopology): bifibrant objects

## Description

We introduce the full subcategories of cofibrant, fibrant and bifibrant objects (in model categories).

- [x] depends on: #33085

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib.lean b/Mathlib.lean
--- a/Mathlib.lean
+++ b/Mathlib.lean
@@ -1371,6 +1371,7 @@ public import Mathlib.AlgebraicTopology.FundamentalGroupoid.PUnit
 public import Mathlib.AlgebraicTopology.FundamentalGroupoid.Product
 public import Mathlib.AlgebraicTopology.FundamentalGroupoid.SimplyConnected
 public import Mathlib.AlgebraicTopology.ModelCategory.Basic
+public import Mathlib.AlgebraicTopology.ModelCategory.Bifibrant
 public import Mathlib.AlgebraicTopology.ModelCategory.BrownLemma
 public import Mathlib.AlgebraicTopology.ModelCategory.CategoryWithCofibrations
 public import Mathlib.AlgebraicTopology.ModelCategory.Cylinder
diff --git a/Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean b/Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean
--- /dev/null
+++ b/Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean
@@ -0,0 +1,206 @@
+/-
+Copyright (c) 2025 Joël Riou. All rights reserved.
+Released under Apache 2.0 license as described in the file LICENSE.
+Authors: Joël Riou
+-/
+module
+
+public import Mathlib.AlgebraicTopology.ModelCategory.IsCofibrant
+
+/-!
+# Bifibrant objects
+
+In this file, we introduce the full subcategories `CofibrantObject C`,
+`FibrantObject C` and `BifibrantObject C` of a model category `C` which
+respectively consist of cofibrant objects, fibrant objects,
+and bifibrant objects, where "bifibrant" means both cofibrant and fibrant.
+
+-/
+
+@[expose] public section
+
+universe v u
+
+open CategoryTheory Limits
+
+namespace HomotopicalAlgebra
+
+variable {C : Type u} [Category.{v} C]
+
+section Cofibrant
+
+variable [CategoryWithCofibrations C] [HasInitial C]
+
+variable (C) in
+/-- The property that is satisfied by cofibrant objects. -/
+def cofibrantObjects : ObjectProperty C := IsCofibrant
+
+variable (C) in
+/-- The full subcategory of cofibrant objects. -/
+abbrev CofibrantObject : Type u := (cofibrantObjects C).FullSubcategory
+
+namespace CofibrantObject
+
+/-- Constructor for `CofibrantObject C`. -/
+abbrev mk (X : C) [IsCofibrant X] : CofibrantObject C :=
+  ⟨X, by assumption⟩
+
+lemma mk_surjective (X : CofibrantObject C) :
+    ∃ (Y : C) (_ : IsCofibrant Y), X = mk Y := ⟨X.obj, X.property, rfl⟩
+
+/-- Constructor for morphisms in `CofibrantObject C`. -/
+abbrev homMk {X Y : C} [IsCofibrant X] [IsCofibrant Y] (f : X ⟶ Y) :
+    mk X ⟶ mk Y := ObjectProperty.homMk f
+
+lemma homMk_surjective {X Y : C} [IsCofibrant X] [IsCofibrant Y]
+    (f : mk X ⟶ mk Y) :
+    ∃ (g : X ⟶ Y), f = homMk g := ⟨f.hom, rfl⟩
+
+@[simp]
+lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}
+    [IsCofibrant X] [IsCofibrant Y] (f : X ⟶ Y) :
+    WeakEquivalence (homMk f) ↔ WeakEquivalence f := by
+  simp only [weakEquivalence_iff]
+  rfl
+
+@[simp]
+lemma homMk_id (X : C) [IsCofibrant X] : homMk (𝟙 X) = 𝟙 (mk X) := rfl
+
+@[reassoc (attr := simp)]
+lemma homMk_homMk {X Y Z : C} [IsCofibrant X] [IsCofibrant Y] [IsCofibrant Z]
+    (f : X ⟶ Y) (g : Y ⟶ Z) :
+    homMk f ≫ homMk g = homMk (f ≫ g) := rfl
+
+/-- The inclusion functor `CofibrantObject C ⥤ C`. -/
+abbrev ι : CofibrantObject C ⥤ C := (cofibrantObjects C).ι
+
+instance (X : CofibrantObject C) : IsCofibrant X.1 := X.2
+instance (X : CofibrantObject C) : IsCofibrant (CofibrantObject.ι.obj X) := X.2
+
+end CofibrantObject
+
+end Cofibrant
+
+section Fibrant
+
+variable [CategoryWithFibrations C] [HasTerminal C]
+
+variable (C) in
+/-- The property that is satisfied by fibrant objects. -/
+def fibrantObjects : ObjectProperty C := fun X ↦ IsFibrant X
+
+variable (C) in
+/-- The full subcategory of fibrant objects. -/
+abbrev FibrantObject : Type u := (fibrantObjects C).FullSubcategory
+
+namespace FibrantObject
+
+/-- Constructor for `FibrantObject C`. -/
+abbrev mk (X : C) [IsFibrant X] : FibrantObject C :=
+  ⟨X, by assumption⟩
+
+lemma mk_surjective (X : FibrantObject C) :
+    ∃ (Y : C) (_ : IsFibrant Y), X = mk Y := ⟨X.obj, X.property, rfl⟩
+
+/-- Constructor for morphisms in `FibrantObject C`. -/
+abbrev homMk {X Y : C} [IsFibrant X] [IsFibrant Y] (f : X ⟶ Y) :
+    mk X ⟶ mk Y := ObjectProperty.homMk f
+
+lemma homMk_surjective {X Y : C} [IsFibrant X] [IsFibrant Y]
+    (f : mk X ⟶ mk Y) :
+    ∃ (g : X ⟶ Y), f = homMk g := ⟨f.hom, rfl⟩
+
+@[simp]
+lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}
+    [IsFibrant X] [IsFibrant Y] (f : X ⟶ Y) :
+    WeakEquivalence (homMk f) ↔ WeakEquivalence f := by
+  simp only [weakEquivalence_iff]
+  rfl
+
+@[simp]
+lemma homMk_id (X : C) [IsFibrant X] : homMk (𝟙 X) = 𝟙 (mk X) := rfl
+
+@[reassoc (attr := simp)]
+lemma homMk_homMk {X Y Z : C} [IsFibrant X] [IsFibrant Y] [IsFibrant Z]
+    (f : X ⟶ Y) (g : Y ⟶ Z) :
+    homMk f ≫ homMk g = homMk (f ≫ g) := rfl
+
+/-- The inclusion functor `FibrantObject C ⥤ C`. -/
+abbrev ι : FibrantObject C ⥤ C := (fibrantObjects C).ι
+
+instance (X : FibrantObject C) : IsFibrant X.1 := X.2
+instance (X : FibrantObject C) : IsFibrant (FibrantObject.ι.obj X) := X.2
+
+end FibrantObject
+
+end Fibrant
+
+section Bifibrant
+
+variable [CategoryWithCofibrations C] [HasInitial C]
+  [CategoryWithFibrations C] [HasTerminal C]
+
+variable (C) in
+/-- The property that is satisfied by bifibrant objects, i.e. objects
+that are both cofibrant and fibrant. -/
+def bifibrantObjects : ObjectProperty C :=
+    cofibrantObjects C ⊓ fibrantObjects C
+
+variable (C) in
+lemma bifibrantObjects_le_cofibrantObject :
+    bifibrantObjects C ≤ cofibrantObjects C :=
+  fun _ h ↦ h.1
+
+variable (C) in
+lemma bifibrantObjects_le_fibrantObject :
+    bifibrantObjects C ≤ fibrantObjects C :=
+  fun _ h ↦ h.2
+
+variable (C) in
+/-- The full subcategory of bifibrant objects. -/
+abbrev BifibrantObject : Type u := (bifibrantObjects C).FullSubcategory
+
+namespace BifibrantObject
+
+/-- Constructor for `BifibrantObject C`. -/
+abbrev mk (X : C) [IsCofibrant X] [IsFibrant X] :
+    BifibrantObject C :=
+  ⟨X, by assumption, by assumption⟩
+
+lemma mk_surjective (X : BifibrantObject C) :
+    ∃ (Y : C) (_ :
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 2 sites, 16 facet items

### Site 1: `Mathlib.lean` lines 1371-1377
```
public import Mathlib.AlgebraicTopology.FundamentalGroupoid.Product
 public import Mathlib.AlgebraicTopology.FundamentalGroupoid.SimplyConnected
 public import Mathlib.AlgebraicTopology.ModelCategory.Basic
public import Mathlib.AlgebraicTopology.ModelCategory.Bifibrant
 public import Mathlib.AlgebraicTopology.ModelCategory.BrownLemma
 public import Mathlib.AlgebraicTopology.ModelCategory.CategoryWithCofibrations
 public import Mathlib.AlgebraicTopology.ModelCategory.Cylinder
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean` lines 1-206
```
/-
Copyright (c) 2025 Joël Riou. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Joël Riou
-/
module

public import Mathlib.AlgebraicTopology.ModelCategory.IsCofibrant

/-!
# Bifibrant objects

In this file, we introduce the full subcategories `CofibrantObject C`,
`FibrantObject C` and `BifibrantObject C` of a model category `C` which
respectively consist of cofibrant objects, fibrant objects,
and bifibrant objects, where "bifibrant" means both cofibrant and fibrant.

-/

@[expose] public section

universe v u

open CategoryTheory Limits

namespace HomotopicalAlgebra

variable {C : Type u} [Category.{v} C]

section Cofibrant

variable [CategoryWithCofibrations C] [HasInitial C]

variable (C) in
/-- The property that is satisfied by cofibrant objects. -/
def cofibrantObjects : ObjectProperty C := IsCofibrant

variable (C) in
/-- The full subcategory of cofibrant objects. -/
abbrev CofibrantObject : Type u := (cofibrantObjects C).FullSubcategory

namespace CofibrantObject

/-- Constructor for `CofibrantObject C`. -/
abbrev mk (X : C) [IsCofibrant X] : CofibrantObject C :=
  ⟨X, by assumption⟩

lemma mk_surjective (X : CofibrantObject C) :
    ∃ (Y : C) (_ : IsCofibrant Y), X = mk Y := ⟨X.obj, X.property, rfl⟩

/-- Constructor for morphisms in `CofibrantObject C`. -/
abbrev homMk {X Y : C} [IsCofibrant X] [IsCofibrant Y] (f : X ⟶ Y) :
    mk X ⟶ mk Y := ObjectProperty.homMk f

lemma homMk_surjective {X Y : C} [IsCofibrant X] [IsC
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33098 — window 1/1 — prompt 15,640 chars
==========================================================================================

## PR #33098 — feat: minimal covers and maximal separated sets

## Description

Define a minimal cover of a set by closed balls, and a maximal separated set.
Use the maximal separated set to prove comparisons between covering and packing numbers.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Topology/MetricSpace/CoveringNumbers.lean b/Mathlib/Topology/MetricSpace/CoveringNumbers.lean
--- a/Mathlib/Topology/MetricSpace/CoveringNumbers.lean
+++ b/Mathlib/Topology/MetricSpace/CoveringNumbers.lean
@@ -29,12 +29,23 @@ We prove inequalities between these covering and packing numbers.
 * `packingNumber`: the packing number of a set `A` for radius `ε` is the maximal cardinality of
   an `ε`-separated set in `A`.
 
+We define sets achieving these minimal/maximal cardinalities when they exist:
+* `minimalCover`: a finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
+* `maximalSeparatedSet`: a finite `ε`-separated subset of a set `A` with maximal cardinality.
+
 ## Main statements
 
-* `externalCoveringNumber_le_coveringNumber`: the external covering number is less than or equal to
-  the covering number.
-* `packingNumber_two_mul_le_externalCoveringNumber`: the packing number with radius `2 * ε` is
-  less than or equal to the external covering number for `ε`.
+We have the following inequalities between covering and packing numbers:
+* `externalCoveringNumber_le_coveringNumber`: external covering number ≤ covering number.
+* `packingNumber_two_mul_le_externalCoveringNumber`: packing number for `2 * ε` ≤ external covering
+  number for `ε`.
+* `coveringNumber_le_packingNumber`: covering number ≤ packing number.
+* `coveringNumber_two_mul_le_externalCoveringNumber`: covering number for `2 * ε` ≤ external
+  covering number for `ε`.
+
+The covering number is not monotone for set inclusion (because the cover must be contained
+in the set), but we have the following inequality:
+* `coveringNumber_subset_le`: if `A ⊆ B`, then `coveringNumber ε A ≤ coveringNumber (ε / 2) B`.
 
 ## References
 
@@ -217,6 +228,142 @@ lemma packingNumber_singleton (ε : ℝ≥0) (x : X) : packingNumber ε {x} = 1
   le_antisymm ((packingNumber_le_encard_self {x}).trans_eq (by simp)) <|
     le_iSup_of_le {x} <| le_iSup_of_le (by simp) <| le_iSup_of_le (by simp) (by simp)
 
+section MinimalCover
+
+lemma exists_set_encard_eq_coveringNumber (h : coveringNumber ε A ≠ ⊤) :
+    ∃ C, C ⊆ A ∧ C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A := by
+  simp only [coveringNumber, ne_eq, iInf_eq_top, encard_eq_top_iff, not_forall, not_infinite] at h
+  obtain ⟨C', hC'_subset, hC'_cover, hC'_fin⟩ := h
+  have : Nonempty { s : Set X // s ⊆ A ∧ IsCover ε A s } := ⟨C', hC'_subset, hC'_cover⟩
+  let h := ENat.exists_eq_iInf (fun C : {s : Set X // s ⊆ A ∧ IsCover ε A s} ↦ (C : Set X).encard)
+  obtain ⟨C, hC⟩ := h
+  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
+  · refine Set.encard_lt_top_iff.mp ?_
+    simp only [hC, iInf_lt_top, encard_lt_top_iff, Subtype.exists, exists_prop]
+    exact ⟨C', ⟨hC'_subset, hC'_cover⟩, hC'_fin⟩
+  · rw [hC]
+    simp_rw [iInf_subtype, iInf_and]
+    rfl
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
+    (minimalCover ε A).encard = coveringNumber ε A := by
+  simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+  exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.2.2
+
+end MinimalCover
+
+section MaximalSeparatedSet
+
+lemma exists_set_encard_eq_packingNumber (h : packingNumber ε A ≠ ⊤) :
+    ∃ C, C ⊆ A ∧ C.Finite ∧ IsSeparated ε C ∧ C.encard = packingNumber ε A := by
+  rcases Set.eq_empty_or_nonempty A with hA | hA
+  · simp [hA, packingNumber]
+  have : Nonempty { s : Set X // s ⊆ A ∧ IsSeparated ε s } := by
+    obtain ⟨a, ha⟩ := hA
+    exact ⟨⟨{a}, by simp [ha], by simp⟩⟩
+  let h_exists := ENat.exists_eq_iSup_of_lt_top
+    (f := fun C : { s : Set X // s ⊆ A ∧ IsSeparated ε s } ↦ (C : Set X).encard)
+  simp_rw [packingNumber] at h ⊢
+  simp_rw [iSup_subtype, iSup_and] at h_exists
+  specialize h_exists h.lt_top
+  obtain ⟨C, hC⟩ := h_exists
+  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
+  · refine Set.encard_ne_top_iff.mp ?_
+    rwa [hC]
+  · rw [hC]
+
+/-- A finite `ε`-separated subset of a set `A` with maximal cardinality.
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
+
+lemma isSeparated_maximalSeparatedSet :
+    IsSeparated ε (maximalSeparatedSet ε A : Set X) := by
+  by_cases h : packingNumber ε A ≠ ⊤
+  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
+    exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.1
+  · simp only [maximalSeparatedSet, h, dite_false, IsSeparated.empty]
+
+lemma car
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 3 sites, 24 facet items

### Site 1: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean` lines 29-51
```
* `packingNumber`: the packing number of a set `A` for radius `ε` is the maximal cardinality of
   an `ε`-separated set in `A`.
 
We define sets achieving these minimal/maximal cardinalities when they exist:
* `minimalCover`: a finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
* `maximalSeparatedSet`: a finite `ε`-separated subset of a set `A` with maximal cardinality.

 ## Main statements
 
We have the following inequalities between covering and packing numbers:
* `externalCoveringNumber_le_coveringNumber`: external covering number ≤ covering number.
* `packingNumber_two_mul_le_externalCoveringNumber`: packing number for `2 * ε` ≤ external covering
  number for `ε`.
* `coveringNumber_le_packingNumber`: covering number ≤ packing number.
* `coveringNumber_two_mul_le_externalCoveringNumber`: covering number for `2 * ε` ≤ external
  covering number for `ε`.

The covering number is not monotone for set inclusion (because the cover must be contained
in the set), but we have the following inequality:
* `coveringNumber_subset_le`: if `A ⊆ B`, then `coveringNumber ε A ≤ coveringNumber (ε / 2) B`.
 
 ## References
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean` lines 228-369
```
le_antisymm ((packingNumber_le_encard_self {x}).trans_eq (by simp)) <|
     le_iSup_of_le {x} <| le_iSup_of_le (by simp) <| le_iSup_of_le (by simp) (by simp)
 
section MinimalCover

lemma exists_set_encard_eq_coveringNumber (h : coveringNumber ε A ≠ ⊤) :
    ∃ C, C ⊆ A ∧ C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A := by
  simp only [coveringNumber, ne_eq, iInf_eq_top, encard_eq_top_iff, not_forall, not_infinite] at h
  obtain ⟨C', hC'_subset, hC'_cover, hC'_fin⟩ := h
  have : Nonempty { s : Set X // s ⊆ A ∧ IsCover ε A s } := ⟨C', hC'_subset, hC'_cover⟩
  let h := ENat.exists_eq_iInf (fun C : {s : Set X // s ⊆ A ∧ IsCover ε A s} ↦ (C : Set X).encard)
  obtain ⟨C, hC⟩ := h
  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
  · refine Set.encard_lt_top_iff.mp ?_
    simp only [hC, iInf_lt_top, encard_lt_top_iff, Subtype.exists, exists_prop]
    exact ⟨C', ⟨hC'_subset, hC'_cover⟩, hC'_fin⟩
  · rw [hC]
    simp_rw [iInf_subtype, iInf_and]
    rfl

open Classical in
/-- A finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
It is defined as the empty set if no such finite cover exists. -/
noncomputable
def minimalCover (ε : ℝ≥0) (A : Set X) : Set X :=
  if h : coveringNumber ε A ≠ ⊤ then (exists_set_encard_eq_coveringNumber h).choose else ∅

lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h).choo
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean` lines 390-422
```
· exact hf' x
       · simpa [edist_comm, hxy] using hf' y
 
theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber ε A ≤ packingNumber ε A := by
  by_cases h_top : packingNumber ε A ≠ ⊤
  · rw [← card_maximalSeparatedSet h_top]
    refine (iInf_le _ (maximalSeparatedSet ε A)).trans (le_of_eq ?_)
    simp [maximalSeparatedSet_subset, iInf_pos, isCover_maximalSeparatedSet h_top]
  · simp only [ne_eq, Decidable.not_not] at h_top
    simp [h_top]

theorem coveringNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber (2 * ε) A ≤ externalCoveringNumber ε A := by
  rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)
  · simp [h_empty]
  refine (coveringNumber_le_packingNumber _ A).trans ?_
  exact packingNumber_two_mul_le_externalCoveringNumber ε A

lemma coveringNumber_subset_le (h : A ⊆ B) :
    coveringNumber ε A ≤ coveringNumber (ε / 2) B := by
  calc coveringNumber ε A
  _ ≤ packingNumber ε A := coveringNumber_le_packingNumber ε A
  _ = packingNumber (2 * (ε / 2)) A := by ring_nf
  _ ≤ externalCoveringNumber (ε / 2) A :=
    packingNumber_two_mul_le_externalCoveringNumber (ε / 2) A
  _ ≤ externalCoveringNumber (ε / 2) B := externalCoveringNumber_mono_set h
  _ ≤ coveringNumber (ε / 2) B :=
    externalCoveringNumber_le_coveringNumber (ε / 2) B

end Comparisons

 end Metric
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33117 — window 1/1 — prompt 8,176 chars
==========================================================================================

## PR #33117 — feat: introduce predicate `Meromorphic`

## Description

Following a discussion of Zulip, introduce the predicate `Meromorphic` as a shorthand for functions that are `MeromorphicOn … Set.univ`

[#mathlib4 > Introducing &#96;Meromorphic&#96; @ 💬](https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/Introducing.20.60Meromorphic.60/near/564522177)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Analysis/Meromorphic/Basic.lean b/Mathlib/Analysis/Meromorphic/Basic.lean
--- a/Mathlib/Analysis/Meromorphic/Basic.lean
+++ b/Mathlib/Analysis/Meromorphic/Basic.lean
@@ -631,3 +631,102 @@ theorem measurable [MeasurableSpace 𝕜] [SecondCountableTopology 𝕜] [BorelS
     (by simp [- mem_compl_iff]) h₃.restrict.measurable (measurable_of_countable _)
 
 end MeromorphicOn
+
+/-- Meromorphy of a function on all of 𝕜. -/
+@[fun_prop]
+def Meromorphic (f : 𝕜 → E) := ∀ x, MeromorphicAt f x
+
+/-- A function is meromorphic iff it is meromorphic on Set.univ. -/
+@[simp]
+lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f  := by tauto
+
+namespace Meromorphic
+
+variable
+  {ι : Type*} {s : Finset ι}
+  {f g : 𝕜 → E} {F : ι → 𝕜 → 𝕜} {G : ι → 𝕜 → E}
+
+@[fun_prop]
+lemma neg (hf : Meromorphic f) : Meromorphic (-f) := fun x ↦ (hf x).neg
+
+@[fun_prop]
+lemma fun_neg (hf : Meromorphic f) : Meromorphic (fun x ↦ -f x ) := hf.neg
+
+@[fun_prop]
+lemma add (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (f + g) := fun x ↦ (hf x).add (hg x)
+
+@[fun_prop]
+lemma fun_add (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (fun x ↦ f x + g x) := hf.add hg
+
+@[fun_prop]
+theorem sum (h : ∀ σ, Meromorphic (G σ)) :
+    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)
+
+@[fun_prop]
+theorem fun_sum (h : ∀ σ, Meromorphic (G σ)) :
+    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := by
+  simpa [← Finset.sum_apply] using (sum h)
+
+@[fun_prop]
+lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)
+
+@[fun_prop]
+lemma fun_sub (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (fun x ↦ f x - g x) := hf.sub hg
+
+@[fun_prop]
+lemma mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (f * g) := fun x ↦ (hf x).mul (hg x)
+
+@[fun_prop]
+lemma fun_mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (fun x ↦ f x * g x) := hf.mul hg
+
+@[fun_prop]
+theorem prod (h : ∀ σ, Meromorphic (F σ)) :
+    Meromorphic (∏ n ∈ s, F n) := fun x ↦ MeromorphicAt.prod (h · x)
+
+@[fun_prop]
+theorem fun_prod (h : ∀ σ, Meromorphic (F σ)) :
+    Meromorphic (fun x ↦ ∏ n ∈ s, F n x) := by
+  simpa [← Finset.prod_apply] using (prod h)
+
+@[fun_prop]
+lemma div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (f / g) := fun x ↦ (hf x).div (hg x)
+
+@[fun_prop]
+lemma fun_div {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :
+    Meromorphic (fun x ↦ f x / g x) := hf.div hg
+
+@[fun_prop]
+lemma pow {f : 𝕜 → 𝕜} {n : ℕ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).pow n
+
+@[fun_prop]
+lemma fun_pow {f : 𝕜 → 𝕜} {n : ℕ} (hf : Meromorphic f) : Meromorphic (fun x ↦ f x ^ n) := hf.pow
+
+@[fun_prop]
+lemma zpow {f : 𝕜 → 𝕜} {n : ℤ} (hf : Meromorphic f) : Meromorphic (f ^ n) := fun x ↦ (hf x).zpow n
+
+@[fun_prop]
+lemma fun_zpow {f : 𝕜 → 𝕜} {n : ℤ} (hf : Meromorphic f) : Meromorphic (fun x ↦ f x ^ n) := hf.zpow
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
+
+end Meromorphic

```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 1 sites, 8 facet items

### Site 1: `Mathlib/Analysis/Meromorphic/Basic.lean` lines 631-732
```
(by simp [- mem_compl_iff]) h₃.restrict.measurable (measurable_of_countable _)
 
 end MeromorphicOn

/-- Meromorphy of a function on all of 𝕜. -/
@[fun_prop]
def Meromorphic (f : 𝕜 → E) := ∀ x, MeromorphicAt f x

/-- A function is meromorphic iff it is meromorphic on Set.univ. -/
@[simp]
lemma meromorphicOn_univ {f : 𝕜 → E} : MeromorphicOn f Set.univ ↔ Meromorphic f  := by tauto

namespace Meromorphic

variable
  {ι : Type*} {s : Finset ι}
  {f g : 𝕜 → E} {F : ι → 𝕜 → 𝕜} {G : ι → 𝕜 → E}

@[fun_prop]
lemma neg (hf : Meromorphic f) : Meromorphic (-f) := fun x ↦ (hf x).neg

@[fun_prop]
lemma fun_neg (hf : Meromorphic f) : Meromorphic (fun x ↦ -f x ) := hf.neg

@[fun_prop]
lemma add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f + g) := fun x ↦ (hf x).add (hg x)

@[fun_prop]
lemma fun_add (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x + g x) := hf.add hg

@[fun_prop]
theorem sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (∑ n ∈ s, G n) := fun x ↦ MeromorphicAt.sum (h · x)

@[fun_prop]
theorem fun_sum (h : ∀ σ, Meromorphic (G σ)) :
    Meromorphic (fun x ↦ ∑ n ∈ s, G n x) := by
  simpa [← Finset.sum_apply] using (sum h)

@[fun_prop]
lemma sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (f - g) := fun x ↦ (hf x).sub (hg x)

@[fun_prop]
lemma fun_sub (hf : Meromorphic f) (hg : Meromorphic g) :
    Meromorphic (fun x ↦ f x - g x) := hf.sub hg

@[fun_prop]
lemma mul {f g : 𝕜 → 𝕜} (hf : Meromorphic f) (hg : Meromorphic g) :

```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33153 — window 1/5 — prompt 21,429 chars
==========================================================================================

## PR #33153 — doc(MeasureTheory): fix typos and inconsistencies

## Description

Typos found and fixed by Codex.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
--- a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
+++ b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
@@ -28,7 +28,7 @@ public import Mathlib.Topology.Instances.Rat
 * `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
-  is continuous, then `fun x => op (f x, g y)` is measurable;
+  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
diff --git a/Mathlib/MeasureTheory/Constructions/Cylinders.lean b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
--- a/Mathlib/MeasureTheory/Constructions/Cylinders.lean
+++ b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
@@ -55,7 +55,7 @@ section squareCylinders
 /-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
-`squareCylinders` is the set of all such `squareCylinders`. -/
+`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
 
diff --git a/Mathlib/MeasureTheory/Constructions/Pi.lean b/Mathlib/MeasureTheory/Constructions/Pi.lean
--- a/Mathlib/MeasureTheory/Constructions/Pi.lean
+++ b/Mathlib/MeasureTheory/Constructions/Pi.lean
@@ -38,7 +38,7 @@ For a collection of σ-finite measures `μ` and a collection of measurable sets
 `Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
-  `∀ ι, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
+  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
diff --git a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
--- a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
+++ b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
@@ -31,7 +31,7 @@ convergence in measure and other notions of convergence.
 * `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
-  which converges in measure to `g`, then `f` has a subsequence which convergence almost
+  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
diff --git a/Mathlib/MeasureTheory/Function/Jacobian.lean b/Mathlib/MeasureTheory/Function/Jacobian.lean
--- a/Mathlib/MeasureTheory/Function/Jacobian.lean
+++ b/Mathlib/MeasureTheory/Function/Jacobian.lean
@@ -51,7 +51,7 @@ For the next statements, `s` is a measurable set and `f` is differentiable on `s
 * `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
-  integrable on `f '' s` if and only if `|(f' x).det| • g (f x))` is integrable on `s`.
+  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
 
diff --git a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
--- a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
+++ b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
@@ -55,7 +55,7 @@ variable [MeasurableSpace α] [PseudoEMetricSpace α] [OpensMeasurableSpace α]
 
 /-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
-`nearestPtInd e N x` returns the least of their indexes. -/
+`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
diff --git a/Mathlib/MeasureTheory/Function/UnifTight.lean b/Mathlib/MeasureTheory/Function/UnifTight.lean
--- a/Mathlib/MeasureTheory/Function/UnifTight.lean
+++ b/Mathlib/MeasureTheory/Function/UnifTight.lean
@@ -49,7 +49,7 @@ variable {α β ι : Type*} {m : MeasurableSpace α} {μ : Measure α} [NormedAd
 section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
-from `Mathlib/MeasureTheory/Functions/UniformIntegrable.lean`. -/
+from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
 
diff --git a/Mathlib/MeasureTheory/Group/Arithmetic.lean b/Mathlib/MeasureTheory/Group/Arithmetic.lean
--- a/Mathlib/MeasureTheory/Group/Arithmetic.lean
+++ b/Mathlib/MeasureTheory/Group/Arithmetic.lean
@@ -30,7 +30,7 @@ For instances relating, e.g., `ContinuousMul` to `MeasurableMul` see file
 ## Implementation notes
 
 For the heuristic
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 1/5: sites 1-8 of 35)

### Site 1: `Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean` lines 28-34
```
* `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/Constructions/Cylinders.lean` lines 55-61
```
/-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/Constructions/Pi.lean` lines 38-44
```
`Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean` lines 31-37
```
* `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/MeasureTheory/Function/Jacobian.lean` lines 51-57
```
* `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/MeasureTheory/Function/SimpleFuncDense.lean` lines 55-61
```
/-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/MeasureTheory/Function/UnifTight.lean` lines 49-55
```
section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/MeasureTheory/Group/Arithmetic.lean` lines 30-36
```
## Implementation notes
 
 For the heuristics of `@[to_additive]` it is important that the type with a multiplication
(or another multiplicative operation) is the first (implicit) argument of all declarations.
 
 ## Tags
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33153 — window 2/5 — prompt 21,517 chars
==========================================================================================

## PR #33153 — doc(MeasureTheory): fix typos and inconsistencies

## Description

Typos found and fixed by Codex.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
--- a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
+++ b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
@@ -28,7 +28,7 @@ public import Mathlib.Topology.Instances.Rat
 * `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
-  is continuous, then `fun x => op (f x, g y)` is measurable;
+  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
diff --git a/Mathlib/MeasureTheory/Constructions/Cylinders.lean b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
--- a/Mathlib/MeasureTheory/Constructions/Cylinders.lean
+++ b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
@@ -55,7 +55,7 @@ section squareCylinders
 /-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
-`squareCylinders` is the set of all such `squareCylinders`. -/
+`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
 
diff --git a/Mathlib/MeasureTheory/Constructions/Pi.lean b/Mathlib/MeasureTheory/Constructions/Pi.lean
--- a/Mathlib/MeasureTheory/Constructions/Pi.lean
+++ b/Mathlib/MeasureTheory/Constructions/Pi.lean
@@ -38,7 +38,7 @@ For a collection of σ-finite measures `μ` and a collection of measurable sets
 `Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
-  `∀ ι, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
+  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
diff --git a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
--- a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
+++ b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
@@ -31,7 +31,7 @@ convergence in measure and other notions of convergence.
 * `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
-  which converges in measure to `g`, then `f` has a subsequence which convergence almost
+  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
diff --git a/Mathlib/MeasureTheory/Function/Jacobian.lean b/Mathlib/MeasureTheory/Function/Jacobian.lean
--- a/Mathlib/MeasureTheory/Function/Jacobian.lean
+++ b/Mathlib/MeasureTheory/Function/Jacobian.lean
@@ -51,7 +51,7 @@ For the next statements, `s` is a measurable set and `f` is differentiable on `s
 * `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
-  integrable on `f '' s` if and only if `|(f' x).det| • g (f x))` is integrable on `s`.
+  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
 
diff --git a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
--- a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
+++ b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
@@ -55,7 +55,7 @@ variable [MeasurableSpace α] [PseudoEMetricSpace α] [OpensMeasurableSpace α]
 
 /-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
-`nearestPtInd e N x` returns the least of their indexes. -/
+`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
diff --git a/Mathlib/MeasureTheory/Function/UnifTight.lean b/Mathlib/MeasureTheory/Function/UnifTight.lean
--- a/Mathlib/MeasureTheory/Function/UnifTight.lean
+++ b/Mathlib/MeasureTheory/Function/UnifTight.lean
@@ -49,7 +49,7 @@ variable {α β ι : Type*} {m : MeasurableSpace α} {μ : Measure α} [NormedAd
 section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
-from `Mathlib/MeasureTheory/Functions/UniformIntegrable.lean`. -/
+from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
 
diff --git a/Mathlib/MeasureTheory/Group/Arithmetic.lean b/Mathlib/MeasureTheory/Group/Arithmetic.lean
--- a/Mathlib/MeasureTheory/Group/Arithmetic.lean
+++ b/Mathlib/MeasureTheory/Group/Arithmetic.lean
@@ -30,7 +30,7 @@ For instances relating, e.g., `ContinuousMul` to `MeasurableMul` see file
 ## Implementation notes
 
 For the heuristic
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 2/5: sites 9-16 of 35)

### Site 1: `Mathlib/MeasureTheory/Group/FundamentalDomain.lean` lines 57-63
```
namespace MeasureTheory
 
 /-- A measurable set `s` is a *fundamental domain* for an additive action of an additive group `G`
on a measurable space `α` with respect to a measure `μ` if the sets `g +ᵥ s`, `g : G`, are pairwise
 a.e. disjoint and cover the whole space. -/
 structure IsAddFundamentalDomain (G : Type*) {α : Type*} [Zero G] [VAdd G α] [MeasurableSpace α]
     (s : Set α) (μ : Measure α := by volume_tac) : Prop where
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/Group/FundamentalDomain.lean` lines 66-72
```
protected aedisjoint : Pairwise <| (AEDisjoint μ on fun g : G => g +ᵥ s)
 
 /-- A measurable set `s` is a *fundamental domain* for an action of a group `G` on a measurable
space `α` with respect to a measure `μ` if the sets `g • s`, `g : G`, are pairwise a.e. disjoint and
 cover the whole space. -/
 @[to_additive IsAddFundamentalDomain]
 structure IsFundamentalDomain (G : Type*) {α : Type*} [One G] [SMul G α] [MeasurableSpace α]
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/Integral/Bochner/L1.lean` lines 42-48
```
* `α →₁[μ] E` : functions in L1 space, i.e., equivalence classes of integrable functions (defined in
                 `Mathlib/MeasureTheory/Function/LpSpace/Basic.lean`)
 * `α →₁ₛ[μ] E` : simple functions in L1 space, i.e., equivalence classes of integrable simple
                 functions (defined in `Mathlib/MeasureTheory/Function/SimpleFuncDenseLp.lean`)
 
 We also define notations for integral on a set, which are described in the file
 `Mathlib/MeasureTheory/Integral/SetIntegral.lean`.
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/MeasureTheory/Integral/Prod.lean` lines 26-32
```
Tonelli's theorem (see `MeasureTheory.lintegral_prod`). The lemma
   `MeasureTheory.Integrable.integral_prod_right` states that the inner integral of the right-hand
   side is integrable.
* `MeasureTheory.integral_integral_swap_of_hasCompactSupport`: a version of Fubini's theorem for
   continuous functions with compact support, which does not assume that the measures are σ-finite
   contrary to all the usual versions of Fubini.
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/MeasureTheory/MeasurableSpace/Invariants.lean` lines 12-18
```
In this file we define `MeasurableSpace.invariants (f : α → α)`
 to be the σ-algebra of sets `s : Set α` such that
 - `s` is measurable w.r.t. the canonical σ-algebra on `α`;
- and `f ⁻¹' s = s`.
 -/
 
 @[expose] public section
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/MeasureTheory/Measure/Complex.lean` lines 22-28
```
* `MeasureTheory.ComplexMeasure.im`: obtains a signed measure `s` from a complex measure `c`
   such that `s i = (c i).im` for all measurable sets `i`.
 * `MeasureTheory.SignedMeasure.toComplexMeasure`: given two signed measures `s` and `t`,
  `s.toComplexMeasure t` provides a complex measure of the form `s + it`.
 * `MeasureTheory.ComplexMeasure.equivSignedMeasure`: is the equivalence between the complex
   measures and the type of the product of the signed measures with itself.
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/MeasureTheory/Measure/Haar/Unique.lean` lines 32-38
```
* `isMulLeftInvariant_eq_smul_of_innerRegular`: two left invariant measures which are
   inner regular coincide up to a scalar.
* `isMulLeftInvariant_eq_smul_of_regular`: two left invariant measures which are
   regular coincide up to a scalar.
 * `isHaarMeasure_eq_smul`: in a second countable space, two Haar measures coincide up to a
   scalar.
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/MeasureTheory/Measure/HasOuterApproxClosedProd.lean` lines 17-23
```
`f : (i : ι) → X i → ℝ` and `g : (j : κ) → Y j → ℝ`
 any families of bounded continuous functions.
 
In particular, if `μ` and `ν` are two finite measures over `Π i, X i` and `Π j, Y j` respectively,
 then their product is the only finite measure `ξ` over `(Π i, X i) × (Π j, Y j)`
 such that for any two families bounded continuous functions
 `f : (i : ι) → X i → ℝ` and `g : (j : κ) → Y j → ℝ` we have
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33153 — window 3/5 — prompt 21,575 chars
==========================================================================================

## PR #33153 — doc(MeasureTheory): fix typos and inconsistencies

## Description

Typos found and fixed by Codex.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
--- a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
+++ b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
@@ -28,7 +28,7 @@ public import Mathlib.Topology.Instances.Rat
 * `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
-  is continuous, then `fun x => op (f x, g y)` is measurable;
+  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
diff --git a/Mathlib/MeasureTheory/Constructions/Cylinders.lean b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
--- a/Mathlib/MeasureTheory/Constructions/Cylinders.lean
+++ b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
@@ -55,7 +55,7 @@ section squareCylinders
 /-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
-`squareCylinders` is the set of all such `squareCylinders`. -/
+`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
 
diff --git a/Mathlib/MeasureTheory/Constructions/Pi.lean b/Mathlib/MeasureTheory/Constructions/Pi.lean
--- a/Mathlib/MeasureTheory/Constructions/Pi.lean
+++ b/Mathlib/MeasureTheory/Constructions/Pi.lean
@@ -38,7 +38,7 @@ For a collection of σ-finite measures `μ` and a collection of measurable sets
 `Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
-  `∀ ι, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
+  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
diff --git a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
--- a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
+++ b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
@@ -31,7 +31,7 @@ convergence in measure and other notions of convergence.
 * `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
-  which converges in measure to `g`, then `f` has a subsequence which convergence almost
+  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
diff --git a/Mathlib/MeasureTheory/Function/Jacobian.lean b/Mathlib/MeasureTheory/Function/Jacobian.lean
--- a/Mathlib/MeasureTheory/Function/Jacobian.lean
+++ b/Mathlib/MeasureTheory/Function/Jacobian.lean
@@ -51,7 +51,7 @@ For the next statements, `s` is a measurable set and `f` is differentiable on `s
 * `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
-  integrable on `f '' s` if and only if `|(f' x).det| • g (f x))` is integrable on `s`.
+  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
 
diff --git a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
--- a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
+++ b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
@@ -55,7 +55,7 @@ variable [MeasurableSpace α] [PseudoEMetricSpace α] [OpensMeasurableSpace α]
 
 /-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
-`nearestPtInd e N x` returns the least of their indexes. -/
+`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
diff --git a/Mathlib/MeasureTheory/Function/UnifTight.lean b/Mathlib/MeasureTheory/Function/UnifTight.lean
--- a/Mathlib/MeasureTheory/Function/UnifTight.lean
+++ b/Mathlib/MeasureTheory/Function/UnifTight.lean
@@ -49,7 +49,7 @@ variable {α β ι : Type*} {m : MeasurableSpace α} {μ : Measure α} [NormedAd
 section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
-from `Mathlib/MeasureTheory/Functions/UniformIntegrable.lean`. -/
+from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
 
diff --git a/Mathlib/MeasureTheory/Group/Arithmetic.lean b/Mathlib/MeasureTheory/Group/Arithmetic.lean
--- a/Mathlib/MeasureTheory/Group/Arithmetic.lean
+++ b/Mathlib/MeasureTheory/Group/Arithmetic.lean
@@ -30,7 +30,7 @@ For instances relating, e.g., `ContinuousMul` to `MeasurableMul` see file
 ## Implementation notes
 
 For the heuristic
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 3/5: sites 17-24 of 35)

### Site 1: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 17-23
```
In this file we define the `d`-dimensional Hausdorff measure on an (extended) metric space `X` and
 the Hausdorff dimension of a set in an (extended) metric space. Let `μ d δ` be the maximal outer
 measure such that `μ d δ s ≤ (EMetric.diam s) ^ d` for every set of diameter less than `δ`. Then
the Hausdorff measure `μH[d] s` of `s` is defined as `⨆ δ > 0, μ d δ s`. By Carathéodory theorem
 `MeasureTheory.OuterMeasure.IsMetric.borel_le_caratheodory`, this is a Borel measure on `X`.
 
 The value of `μH[d]`, `d > 0`, on a set `s` (measurable or not) is given by
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 40-46
```
We also define a predicate `MeasureTheory.OuterMeasure.IsMetric` which says that an outer measure
 is additive on metric separated pairs of sets: `μ (s ∪ t) = μ s + μ t` provided that
`⨅ (x ∈ s) (y ∈ t), edist x y ≠ 0`. This is the property required for the Carathéodory theorem
 `MeasureTheory.OuterMeasure.IsMetric.borel_le_caratheodory`, so we prove this theorem for any
 metric outer measure, then prove that outer measures constructed using `mkMetric'` are metric outer
 measures.
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 49-55
```
* `MeasureTheory.OuterMeasure.IsMetric`: an outer measure `μ` is called *metric* if
   `μ (s ∪ t) = μ s + μ t` for any two metric separated sets `s` and `t`. A metric outer measure in a
  Borel extended metric space is guaranteed to satisfy the Carathéodory condition, see
   `MeasureTheory.OuterMeasure.IsMetric.borel_le_caratheodory`.
 * `MeasureTheory.OuterMeasure.mkMetric'` and its particular case
   `MeasureTheory.OuterMeasure.mkMetric`: a construction of an outer measure that is guaranteed to
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 70-76
```
* `MeasureTheory.OuterMeasure.IsMetric.borel_le_caratheodory`: if `μ` is a metric outer measure
   on an extended metric space `X` (that is, it is additive on pairs of metric separated sets), then
  every Borel set is Carathéodory measurable (hence, `μ` defines an actual
   `MeasureTheory.Measure`). See also `MeasureTheory.Measure.mkMetric`.
 * `MeasureTheory.Measure.hausdorffMeasure_mono`: `μH[d] s` is an antitone function
   of `d`.
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 126-133
```
/-!
 ### Metric outer measures
 
In this section we define metric outer measures and prove Carathéodory theorem: a metric outer
measure has the Carathéodory property.
 -/
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/MeasureTheory/Measure/Hausdorff.lean` lines 154-161
```
Metric.AreSeparated.finset_iUnion_right fun j hj =>
         hI i (Or.inl rfl) j (Or.inr hj) (ne_of_mem_of_not_mem hj hiI).symm]
 
/-- Carathéodory theorem. If `m` is a metric outer measure, then every Borel measurable set `t` is
Carathéodory measurable: for any (not necessarily measurable) set `s` we have
 `μ (s ∩ t) + μ (s \ t) = μ s`. -/
 theorem borel_le_caratheodory (hm : IsMetric μ) : borel X ≤ μ.caratheodory := by
   rw [borel_eq_generateFrom_isClosed]
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/MeasureTheory/Measure/Map.lean` lines 41-47
```
namespace Measure
 
 /-- Lift a linear map between `OuterMeasure` spaces such that for each measure `μ` every measurable
set is Carathéodory-measurable w.r.t. `f μ` to a linear map between `Measure` spaces. -/
 noncomputable
 def liftLinear [MeasurableSpace β] (f : OuterMeasure α →ₗ[ℝ≥0∞] OuterMeasure β)
     (hf : ∀ μ : Measure α, ‹_› ≤ (f μ.toOuterMeasure).caratheodory) :
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/MeasureTheory/Measure/MeasureSpaceDef.lean` lines 37-43
```
We get countable subadditivity for all sets, but only countable additivity for measurable sets.
 
 See the documentation of `MeasureTheory.MeasureSpace` for ways to construct measures and proving
that two measures are equal.
 
 A `MeasureSpace` is a class that is a measurable space with a canonical measure.
 The measure is denoted `volume`.
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33153 — window 4/5 — prompt 20,977 chars
==========================================================================================

## PR #33153 — doc(MeasureTheory): fix typos and inconsistencies

## Description

Typos found and fixed by Codex.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
--- a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
+++ b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
@@ -28,7 +28,7 @@ public import Mathlib.Topology.Instances.Rat
 * `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
-  is continuous, then `fun x => op (f x, g y)` is measurable;
+  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
diff --git a/Mathlib/MeasureTheory/Constructions/Cylinders.lean b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
--- a/Mathlib/MeasureTheory/Constructions/Cylinders.lean
+++ b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
@@ -55,7 +55,7 @@ section squareCylinders
 /-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
-`squareCylinders` is the set of all such `squareCylinders`. -/
+`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
 
diff --git a/Mathlib/MeasureTheory/Constructions/Pi.lean b/Mathlib/MeasureTheory/Constructions/Pi.lean
--- a/Mathlib/MeasureTheory/Constructions/Pi.lean
+++ b/Mathlib/MeasureTheory/Constructions/Pi.lean
@@ -38,7 +38,7 @@ For a collection of σ-finite measures `μ` and a collection of measurable sets
 `Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
-  `∀ ι, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
+  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
diff --git a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
--- a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
+++ b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
@@ -31,7 +31,7 @@ convergence in measure and other notions of convergence.
 * `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
-  which converges in measure to `g`, then `f` has a subsequence which convergence almost
+  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
diff --git a/Mathlib/MeasureTheory/Function/Jacobian.lean b/Mathlib/MeasureTheory/Function/Jacobian.lean
--- a/Mathlib/MeasureTheory/Function/Jacobian.lean
+++ b/Mathlib/MeasureTheory/Function/Jacobian.lean
@@ -51,7 +51,7 @@ For the next statements, `s` is a measurable set and `f` is differentiable on `s
 * `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
-  integrable on `f '' s` if and only if `|(f' x).det| • g (f x))` is integrable on `s`.
+  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
 
diff --git a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
--- a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
+++ b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
@@ -55,7 +55,7 @@ variable [MeasurableSpace α] [PseudoEMetricSpace α] [OpensMeasurableSpace α]
 
 /-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
-`nearestPtInd e N x` returns the least of their indexes. -/
+`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
diff --git a/Mathlib/MeasureTheory/Function/UnifTight.lean b/Mathlib/MeasureTheory/Function/UnifTight.lean
--- a/Mathlib/MeasureTheory/Function/UnifTight.lean
+++ b/Mathlib/MeasureTheory/Function/UnifTight.lean
@@ -49,7 +49,7 @@ variable {α β ι : Type*} {m : MeasurableSpace α} {μ : Measure α} [NormedAd
 section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
-from `Mathlib/MeasureTheory/Functions/UniformIntegrable.lean`. -/
+from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
 
diff --git a/Mathlib/MeasureTheory/Group/Arithmetic.lean b/Mathlib/MeasureTheory/Group/Arithmetic.lean
--- a/Mathlib/MeasureTheory/Group/Arithmetic.lean
+++ b/Mathlib/MeasureTheory/Group/Arithmetic.lean
@@ -30,7 +30,7 @@ For instances relating, e.g., `ContinuousMul` to `MeasurableMul` see file
 ## Implementation notes
 
 For the heuristic
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 4/5: sites 25-32 of 35)

### Site 1: `Mathlib/MeasureTheory/Measure/Stieltjes.lean` lines 42-49
```
there, and not exported.
 
 Note that the theory of Stieltjes measures is not completely satisfactory when there is a bot
element `x`: any Stieltjes measure gives zero mass to `{x}` in this case, so the Dirac mass at `x`
is not representable as a Stieltjes measure.
 -/
 
 noncomputable section
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/Measure/Stieltjes.lean` lines 175-181
```
continuousWithinAt_id.leftLim_eq
 
 variable (R) in
/-- A constant function is a Stieltjes function. -/
 protected def const (c : ℝ) : StieltjesFunction R where
   toFun := fun _ ↦ c
   mono' _ _ := by simp
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/Measure/WithDensityFinite.lean` lines 53-59
```
if IsFiniteMeasure μ then μ else (exists_isFiniteMeasure_absolutelyContinuous μ).choose
 
 /-- A finite measure obtained from an s-finite measure `μ`, such that
`μ = μ.toFinite.withDensity (μ.rnDeriv μ.toFinite)`
 (see `MeasureTheory.Measure.withDensity_rnDeriv_eq` along with
 `MeasureTheory.absolutelyContinuous_toFinite`). If `μ` is non-zero, then `μ.toFinite` is a
 probability measure. -/
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/MeasureTheory/Order/UpperLower.lean` lines 57-64
```
/-- If we can fit a small ball inside a set `s` intersected with any neighborhood of `x`, then the
 density of `s` near `x` is not `0`.
 
Along with `aux₁`, this proves that `x` is not a Lebesgue point of `s`. This will be used to prove
that the frontier of an order-connected set is null. -/
 private lemma aux₀
     (h : ∀ δ, 0 < δ →
       ∃ y, closedBall y (δ / 4) ⊆ closedBall x δ ∧ closedBall y (δ / 4) ⊆ interior s) :
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/MeasureTheory/Order/UpperLower.lean` lines 86-93
```
/-- If we can fit a small ball inside a set `sᶜ` intersected with any neighborhood of `x`, then the
 density of `s` near `x` is not `1`.
 
Along with `aux₀`, this proves that `x` is not a Lebesgue point of `s`. This will be used to prove
that the frontier of an order-connected set is null. -/
 private lemma aux₁
     (h : ∀ δ, 0 < δ →
       ∃ y, closedBall y (δ / 4) ⊆ closedBall x δ ∧ closedBall y (δ / 4) ⊆ interior sᶜ) :
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/MeasureTheory/OuterMeasure/Caratheodory.lean` lines 9-15
```
public import Mathlib.MeasureTheory.PiSystem
 
 /-!
# The Carathéodory σ-algebra of an outer measure
 
 Given an outer measure `m`, the Carathéodory-measurable sets are the sets `s` such that
 for all sets `t` we have `m t = m (t ∩ s) + m (t \ s)`. This forms a measurable space.
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/MeasureTheory/VectorMeasure/Basic.lean` lines 22-28
```
## Main definitions
 
 * `MeasureTheory.VectorMeasure` is a vector-valued, σ-additive function that maps the empty
  and non-measurable sets to zero.
 * `MeasureTheory.VectorMeasure.map` is the pushforward of a vector measure along a function.
 * `MeasureTheory.VectorMeasure.restrict` is the restriction of a vector measure on some set.
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/MeasureTheory/VectorMeasure/Decomposition/Hahn.lean` lines 66-72
```
$i \setminus \bigcup_{k \le n} A_k$.
 
 This sequence of sets does not necessarily exist. However, if this sequence terminates; that is,
there does not exist any set satisfying the property, the last $A_n$ will be a negative subset
 of negative measure, hence proving our claim.
 
 In the case that the sequence does not terminate, it is easy to see that
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33153 — window 5/5 — prompt 12,729 chars
==========================================================================================

## PR #33153 — doc(MeasureTheory): fix typos and inconsistencies

## Description

Typos found and fixed by Codex.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
--- a/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
+++ b/Mathlib/MeasureTheory/Constructions/BorelSpace/Basic.lean
@@ -28,7 +28,7 @@ public import Mathlib.Topology.Instances.Rat
 * `IsOpen.measurableSet`, `IsClosed.measurableSet`: open and closed sets are measurable;
 * `Continuous.measurable` : a continuous function is measurable;
 * `Continuous.measurable2` : if `f : α → β` and `g : α → γ` are measurable and `op : β × γ → δ`
-  is continuous, then `fun x => op (f x, g y)` is measurable;
+  is continuous, then `fun x => op (f x, g x)` is measurable;
 * `Measurable.add` etc. : dot notation for arithmetic operations on `Measurable` predicates,
   and similarly for `dist` and `edist`;
 * `AEMeasurable.add` : similar dot notation for almost everywhere measurable functions;
diff --git a/Mathlib/MeasureTheory/Constructions/Cylinders.lean b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
--- a/Mathlib/MeasureTheory/Constructions/Cylinders.lean
+++ b/Mathlib/MeasureTheory/Constructions/Cylinders.lean
@@ -55,7 +55,7 @@ section squareCylinders
 /-- Given a finite set `s` of indices, a square cylinder is the product of a set `S` of
 `∀ i : s, α i` and of `univ` on the other indices. The set `S` is a product of sets `t i` such that
 for all `i : s`, `t i ∈ C i`.
-`squareCylinders` is the set of all such `squareCylinders`. -/
+`squareCylinders` is the set of all such square cylinders. -/
 def squareCylinders (C : ∀ i, Set (Set (α i))) : Set (Set (∀ i, α i)) :=
   {S | ∃ s : Finset ι, ∃ t ∈ univ.pi C, S = (s : Set ι).pi t}
 
diff --git a/Mathlib/MeasureTheory/Constructions/Pi.lean b/Mathlib/MeasureTheory/Constructions/Pi.lean
--- a/Mathlib/MeasureTheory/Constructions/Pi.lean
+++ b/Mathlib/MeasureTheory/Constructions/Pi.lean
@@ -38,7 +38,7 @@ For a collection of σ-finite measures `μ` and a collection of measurable sets
 `Measure.pi μ (pi univ s) = ∏ i, m i (s i)`. To do this, we follow the following steps:
 * We know that there is some ordering on `ι`, given by an element of `[Countable ι]`.
 * Using this, we have an equivalence `MeasurableEquiv.piMeasurableEquivTProd` between
-  `∀ ι, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
+  `∀ i, α i` and an iterated product of `α i`, called `List.tprod α l` for some list `l`.
 * On this iterated product we can easily define a product measure `MeasureTheory.Measure.tprod`
   by iterating `MeasureTheory.Measure.prod`
 * Using the previous two steps we construct `MeasureTheory.Measure.pi'` on `(i : ι) → α i` for
diff --git a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
--- a/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
+++ b/Mathlib/MeasureTheory/Function/ConvergenceInMeasure.lean
@@ -31,7 +31,7 @@ convergence in measure and other notions of convergence.
 * `MeasureTheory.tendstoInMeasure_of_tendsto_ae`: convergence almost everywhere in a finite
   measure space implies convergence in measure.
 * `MeasureTheory.TendstoInMeasure.exists_seq_tendsto_ae`: if `f` is a sequence of functions
-  which converges in measure to `g`, then `f` has a subsequence which convergence almost
+  which converges in measure to `g`, then `f` has a subsequence which converges almost
   everywhere to `g`.
 * `MeasureTheory.exists_seq_tendstoInMeasure_atTop_iff`: for a sequence of functions `f`,
   convergence in measure is equivalent to the fact that every subsequence has another subsequence
diff --git a/Mathlib/MeasureTheory/Function/Jacobian.lean b/Mathlib/MeasureTheory/Function/Jacobian.lean
--- a/Mathlib/MeasureTheory/Function/Jacobian.lean
+++ b/Mathlib/MeasureTheory/Function/Jacobian.lean
@@ -51,7 +51,7 @@ For the next statements, `s` is a measurable set and `f` is differentiable on `s
 * `integral_image_eq_integral_abs_det_fderiv_smul`: for `g : E → F`, one has
     `∫ x in f '' s, g x ∂μ = ∫ x in s, |(f' x).det| • g (f x) ∂μ`.
 * `integrableOn_image_iff_integrableOn_abs_det_fderiv_smul`: for `g : E → F`, the function `g` is
-  integrable on `f '' s` if and only if `|(f' x).det| • g (f x))` is integrable on `s`.
+  integrable on `f '' s` if and only if `|(f' x).det| • g (f x)` is integrable on `s`.
 
 ## Implementation
 
diff --git a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
--- a/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
+++ b/Mathlib/MeasureTheory/Function/SimpleFuncDense.lean
@@ -55,7 +55,7 @@ variable [MeasurableSpace α] [PseudoEMetricSpace α] [OpensMeasurableSpace α]
 
 /-- `nearestPtInd e N x` is the index `k` such that `e k` is the nearest point to `x` among the
 points `e 0`, ..., `e N`. If more than one point are at the same distance from `x`, then
-`nearestPtInd e N x` returns the least of their indexes. -/
+`nearestPtInd e N x` returns the least of their indices. -/
 noncomputable def nearestPtInd (e : ℕ → α) : ℕ → α →ₛ ℕ
   | 0 => const α 0
   | N + 1 =>
diff --git a/Mathlib/MeasureTheory/Function/UnifTight.lean b/Mathlib/MeasureTheory/Function/UnifTight.lean
--- a/Mathlib/MeasureTheory/Function/UnifTight.lean
+++ b/Mathlib/MeasureTheory/Function/UnifTight.lean
@@ -49,7 +49,7 @@ variable {α β ι : Type*} {m : MeasurableSpace α} {μ : Measure α} [NormedAd
 section UnifTight
 
 /- This follows closely the `UnifIntegrable` section
-from `Mathlib/MeasureTheory/Functions/UniformIntegrable.lean`. -/
+from `Mathlib/MeasureTheory/Function/UniformIntegrable.lean`. -/
 
 variable {f g : ι → α → β} {p : ℝ≥0∞}
 
diff --git a/Mathlib/MeasureTheory/Group/Arithmetic.lean b/Mathlib/MeasureTheory/Group/Arithmetic.lean
--- a/Mathlib/MeasureTheory/Group/Arithmetic.lean
+++ b/Mathlib/MeasureTheory/Group/Arithmetic.lean
@@ -30,7 +30,7 @@ For instances relating, e.g., `ContinuousMul` to `MeasurableMul` see file
 ## Implementation notes
 
 For the heuristic
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 3 sites, 24 facet items (window 5/5: sites 33-35 of 35)

### Site 1: `Mathlib/MeasureTheory/VectorMeasure/Decomposition/Hahn.lean` lines 86-92
```
`restrictNonposSeq s i (n + 1) = someExistsOneDivLT s (i \ ⋃ k ≤ n, restrictNonposSeq k)`.
   This definition represents the sequence $(A_n)$ in the proof as described above.
 
With these definitions, we are able to consider the case where the sequence terminates separately,
 allowing us to prove `exists_subset_restrict_nonpos`.
 -/
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/MeasureTheory/VectorMeasure/Decomposition/Lebesgue.lean` lines 20-28
```
## Main definitions
 
* `MeasureTheory.SignedMeasure.HaveLebesgueDecomposition` : A signed measure `s` is said to have
  Lebesgue decomposition with respect to a measure `μ` if both the positive part and negative part
  of `s` have Lebesgue decomposition with respect to `μ`.
 * `MeasureTheory.SignedMeasure.singularPart` : The singular part between a signed measure `s`
   and a measure `μ` is simply the singular part of the positive part of `s` with respect to `μ`
   minus the singular part of the negative part of `s` with respect to `μ`.
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/MeasureTheory/VectorMeasure/WithDensity.lean` lines 13-19
```
# Vector measure defined by an integral
 
 Given a measure `μ` and an integrable function `f : α → E`, we can define a vector measure `v` such
that for all measurable sets `s`, `v s = ∫ x in s, f x ∂μ`. This definition is useful for
 the Radon-Nikodym theorem for signed measures.
 
 ## Main definitions
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 1/7 — prompt 22,384 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 1/7: sites 1-8 of 51)

### Site 1: `Mathlib/Order/IsNormal.lean` lines 50-58
```
section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
  hf.strictMono.monotone

 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Cardinal/Aleph.lean` lines 158-164
```
enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Cardinal/Aleph.lean` lines 177-183
```
@[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Cardinal/Aleph.lean` lines 247-253
```
alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Cardinal/Cofinality.lean` lines 532-538
```
obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Cardinal/Cofinality.lean` lines 559-591
```
hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
@[deprecated (since := "2025-12-25")]
alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal

theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq

@[deprecated (since := "2025-12-25")]
alias IsNormal.cof_eq := cof_eq_of_isNormal
 
theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
  · rw [cof_eq_of_isNormal hf ha]

@[deprecated (since := "2025-12-25")]
alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Cardinal/Cofinality.lean` lines 608-618
```
theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/Arithmetic.lean` lines 29-47
```
* `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
Note that some basic functions and properties of ordinals have been generalized to other orders:
 
* `Order.succ o = o + 1` is the successor of `o`.
 * `Order.IsSuccLimit o`: an ordinal is a limit ordinal if it is neither `0` nor a successor.
* `Order.IsNormal`: a function `f : Ordinal → Ordinal` is normal if it is strictly increasing and
  order-continuous, i.e., the image `f o` of a limit ordinal `o` is the supremum of `f a`
  for `a < o`.
 
 Various other basic arithmetic results are given in `Principal.lean` instead.
 -/
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 2/7 — prompt 23,894 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 2/7: sites 9-16 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/Arithmetic.lean` lines 347-447
```
· simp
   · rwa [ho.ordinalPred_eq, eq_comm, pred_eq_iff_isSuccPrelimit, isSuccPrelimit_lift]
 
 /-- A normal ordinal function is a strictly increasing function which is
   order-continuous, i.e., the image `f o` of a limit ordinal `o` is the sup of `f a` for
  `a < o`. -/
@[deprecated Order.IsNormal (since := "2025-12-25")]
protected def IsNormal (f : Ordinal → Ordinal) : Prop :=
   Order.IsNormal f
 
set_option linter.deprecated false in
@[deprecated IsNormal.le_iff_forall_le (since := "2025-12-25")]
theorem IsNormal.limit_le {f} (H : Ordinal.IsNormal f) :
     ∀ {o}, IsSuccLimit o → ∀ {a}, f o ≤ a ↔ ∀ b < o, f b ≤ a :=
   H.le_iff_forall_le
 
set_option linter.deprecated false in
@[deprecated IsNormal.lt_iff_exists_lt (since := "2025-12-25")]
theorem IsNormal.limit_lt {f} (H : Ordinal.IsNormal f) {o} (h : IsSuccLimit o) {a} :
     a < f o ↔ ∃ b < o, a < f b :=
   H.lt_iff_exists_lt h
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
theorem IsNormal.strictMono {f} (H : Ordinal.IsNormal f) : StrictMono f :=
   Order.IsNormal.strictMono H
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.strictMono (since := "2025-12-25")]
theorem IsNormal.monotone {f} (H : Ordinal.IsNormal f) : Monotone f :=
   H.strictMono.monotone
 
set_option linter.deprecated false in
@[deprecated isNormal_iff (since := "2025-12-25")]
 theorem isNormal_iff_strictMono_limit (f : Ordinal → Ordinal) :
    Ordinal.IsNormal f ↔ StrictMon
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/Arithmetic.lean` lines 545-555
```
alias add_le_of_limit := add_le_iff_of_isSuccLimit
 
 theorem isNormal_add_right (a : Ordinal) : IsNormal (a + ·) := by
  rw [isNormal_iff]
   exact ⟨add_right_strictMono, fun _ l _ ↦ (add_le_iff_of_isSuccLimit l).2⟩
 
 theorem isSuccLimit_add (a : Ordinal) {b : Ordinal} : IsSuccLimit b → IsSuccLimit (a + b) :=
  (isNormal_add_right a).map_isSuccLimit
 
 @[deprecated (since := "2025-07-09")]
 alias isLimit_add := isSuccLimit_add
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/Arithmetic.lean` lines 728-734
```
alias mul_le_of_limit := mul_le_iff_of_isSuccLimit
 
 theorem isNormal_mul_right {a : Ordinal} (h : 0 < a) : IsNormal (a * ·) := by
  refine .of_succ_lt (fun b ↦ ?_) fun hb ↦ ?_
   · simpa [mul_succ] using (add_lt_add_iff_left (a * b)).2 h
   · simpa [IsLUB, IsLeast, upperBounds, lowerBounds, mul_le_iff_of_isSuccLimit hb] using
       fun c hc ↦ mul_le_mul_right hc.le a
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Ordinal/Arithmetic.lean` lines 772-778
```
mul_left_cancel_iff_of_pos a0
 
 theorem isSuccLimit_mul {a b : Ordinal} (a0 : 0 < a) : IsSuccLimit b → IsSuccLimit (a * b) :=
  (isNormal_mul_right a0).map_isSuccLimit
 
 @[deprecated (since := "2025-07-09")]
 alias isLimit_mul := isSuccLimit_mul
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Ordinal/Enum.lean` lines 128-134
```
See also `enumOrd_isNormal_iff_isClosed`. -/
 theorem isNormal_enumOrd (H : ∀ t ⊆ s, t.Nonempty → BddAbove t → sSup t ∈ s) (hs : ¬ BddAbove s) :
     IsNormal (enumOrd s) := by
  refine isNormal_iff.2 ⟨enumOrd_strictMono hs, fun o ho a ha ↦ ?_⟩
   trans ⨆ b : Iio o, enumOrd s b
   · refine enumOrd_le_of_forall_lt ?_ (fun b hb ↦ (enumOrd_strictMono hs (lt_succ b)).trans_le ?_)
     · have : Nonempty (Iio o) := ⟨0, ho.bot_lt⟩
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Ordinal/Exponential.lean` lines 7-14
```
public import Mathlib.SetTheory.Ordinal.Family
 
/-!
# Ordinal exponential
 
 In this file we define the power function and the logarithm function on ordinals. The two are
 related by the lemma `Ordinal.opow_le_iff_le_log : b ^ c ≤ x ↔ c ≤ log b x` for nontrivial inputs
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Ordinal/Exponential.lean` lines 119-144
```
| zero => rw [Nat.cast_zero, opow_zero, pow_zero]
   | succ n IH => rw [Nat.cast_succ, add_one_eq_succ, opow_succ, pow_succ, IH]
 
theorem isNormal_opow {a : Ordinal} (h : 1 < a) : IsNormal (a ^ · : Ordinal → Ordinal) := by
   have ha : 0 < a := zero_lt_one.trans h
   refine IsNormal.of_succ_lt ?_ fun hl ↦ ?_
   · simpa only [mul_one, opow_succ] using fun b ↦ mul_lt_mul_of_pos_left h (opow_pos b ha)
   · simp [IsLUB, IsLeast, upperBounds, lowerBounds, ← opow_le_of_isSuccLimit ha.ne' hl]
 
 @[simp]
 theorem opow_lt_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b < a ^ c ↔ b < c :=
  (isNormal_opow a1).strictMono.lt_iff_lt
 
 @[simp]
 theorem opow_le_opow_iff_right {a b c : Ordinal} (a1 : 1 < a) : a ^ b ≤ a ^ c ↔ b ≤ c :=
  (isNormal_opow a1).strictMono.le_iff_le
 
 @[simp]
 theorem opow_right_inj {a b c : Ordinal} (a1 : 1 < a) : a ^ b = a ^ c ↔ b = c :=
  (isNormal_opow a1).strictMono.injective.eq_iff
 
 theorem isSuccLimit_opow {a b : Ordinal} (a1 : 1 < a) : IsSuccLimit b → IsSuccLimit (a ^ b) :=
  (isNormal_opow a1).map_isSuccLimit
 
 @[deprecated (since := "2025-07-08")]
 alias isLimit_opow := isSuccLimit_opow
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/Exponential.lean` lines 189-216
```
rwa [opow_lt_opow_iff_right ha]
 
 theorem right_le_opow {a : Ordinal} (b : Ordinal) (a1 : 1 < a) : b ≤ a ^ b :=
  (isNormal_opow a1).strictMono.le_apply
 
 theorem opow_lt_opow_left_of_succ {a b c : Ordinal} (ab : a < b) : a ^ succ c < b ^ succ c := by
   rw [opow_succ, opow_succ]
   exact mul_lt_mul_of_le_of_lt_of_nonneg_of_pos (by gcongr) ab (zero_le _) (opow_pos _ ab.bot_lt)
 
 theorem opow_add (a b c : Ordinal) : a ^ (b + c) = a ^ b * a ^ c := by
  obtain rfl | ha := eq_zero_or_pos a
  · obtain rfl | hc := eq_zero_or_pos c; · simp
    have : b + c ≠ 0 := (hc.trans_le le_add_self).ne'
    rw [zero_opow hc.ne', zero_opow, mul_zero]
    exact (hc.trans_le le_add_self).ne'
  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha.ne').eq_or_lt; · simp
   induction c using limitRecOn with
   | zero => simp
  | succ c IH => rw [add_succ, opow_succ, IH, opow_succ, mul_assoc]
   | limit c l IH =>
    refine eq_of_forall_ge_iff fun d ↦
      (((isNormal_opow ha').comp (isNormal_add_right b)).le_iff_forall_le l).trans ?_
    simpa +contextual [IH] using
      (((isNormal_mul_right <| opow_pos b (pos_iff_ne_zero.2 ha.ne')).comp
        (isNormal_opow ha')).le_iff_forall_le l).symm
 
 theorem opow_one_add (a b : Ordinal) : a ^ (1 + b) = a * a ^ b := by rw [opow_add, opow_one]
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 3/7 — prompt 23,637 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 3/7: sites 17-24 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/Exponential.lean` lines 225-242
```
opow_dvd_opow _⟩
 
 theorem opow_mul (a b c : Ordinal) : a ^ (b * c) = (a ^ b) ^ c := by
  obtain rfl | hb := eq_zero_or_pos b; · simp
  obtain rfl | ha := eq_or_ne a 0
  · have := hb.ne'
    by_cases c = 0 <;> simp_all
  obtain rfl | ha' := (one_le_iff_ne_zero.2 ha).eq_or_lt; · simp
   induction c using limitRecOn with
  | zero => simp
  | succ c IH => rw [mul_succ, opow_add, IH, opow_succ]
   | limit c l IH =>
    refine eq_of_forall_ge_iff fun d ↦
      (((isNormal_opow ha').comp (isNormal_mul_right hb)).le_iff_forall_le l).trans ?_
    simpa +contextual [IH] using (opow_le_of_isSuccLimit (opow_ne_zero _ ha) l).symm
 
 theorem opow_mul_add_pos {b v : Ordinal} (hb : b ≠ 0) (u : Ordinal) (hv : v ≠ 0) (w : Ordinal) :
     0 < b ^ u * v + w :=
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/Exponential.lean` lines 517-533
```
| n + 1 => by
     rw [pow_succ, natCast_mul, natCast_opow m n, Nat.cast_succ, add_one_eq_succ, opow_succ]
 
theorem iSup_pow_natCast {o : Ordinal} (ho : 0 < o) : ⨆ n : ℕ, o ^ n = o ^ ω := by
   simp_rw [← opow_natCast]
   rcases (one_le_iff_pos.2 ho).lt_or_eq with ho₁ | rfl
  · exact apply_omega0_of_isNormal (isNormal_opow ho₁)
   · rw [one_opow]
     refine le_antisymm (Ordinal.iSup_le fun n => by rw [one_opow]) ?_
     exact_mod_cast Ordinal.le_iSup _ 0
 
@[deprecated (since := "2025-12-25")]
alias iSup_pow := iSup_pow_natCast

 end Ordinal
 
 -- Porting note (https://github.com/leanprover-community/mathlib4/issues/11215): TODO: Port this meta code.
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/Family.lean` lines 238-277
```
(Ordinal.iSup_le fun y => ((typein_lt_typein r).2 <| hx _ <| mem_range_self y).le)
       (typein_lt_type r x)
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
theorem IsNormal.map_iSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
     {ι : Type*} (g : ι → Ordinal.{u}) (hg : BddAbove (range g))
     [Nonempty ι] : f (⨆ i, g i) = ⨆ i, f (g i) :=
   Order.IsNormal.map_iSup H hg
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.map_iSup (since := "2025-12-25")]
theorem IsNormal.map_iSup {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
     {ι : Type w} (g : ι → Ordinal.{u}) [Small.{u} ι] [Nonempty ι] :
     f (⨆ i, g i) = ⨆ i, f (g i) :=
  Order.IsNormal.map_iSup H (bddAbove_of_small _)
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
theorem IsNormal.map_sSup_of_bddAbove {f : Ordinal.{u} → Ordinal.{v}} (H : Ordinal.IsNormal f)
    {s : Set Ordinal.{u}} (hs : BddAbove s) (hn : s.Nonempty) : f (sSup s) = sSup (f '' s) :=
  Order.IsNormal.map_sSup H hn hs
 
set_option linter.deprecated false in
@[deprecated Order.IsNormal.map_sSup (since := "2025-12-25")]
 theorem IsNormal.map_sSup {f : Ordinal.{u} → Ordinal.{v}} (H : IsNormal f)
     {s : Set Ordinal.{u}} (hn : s.Nonempty) [Small.{u} s] : f (sSup s) = sSup (f '' s) :=
  Order.IsNormal.map_sSup H hn (bddAbove_of_small _)
 
set_option linter.deprecated false in
@[deprecated Orde
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Ordinal/Family.lean` lines 380-387
```
∀ (g : ∀ a < o, Ordinal), o ≠ 0 → f (bsup o g) = bsup o fun a h => f (g a h) :=
   inductionOn o fun α r _ g h => by
     haveI := type_ne_zero_iff_nonempty.1 h
    rw [← iSup'_eq_bsup r, Order.IsNormal.map_iSup H (bddAbove_of_small _), ← iSup'_eq_bsup r] <;>
      rfl
 
 theorem lt_bsup_of_ne_bsup {o : Ordinal.{u}} {f : ∀ a < o, Ordinal.{max u v}} :
     (∀ i h, f i h ≠ bsup.{_, v} o f) ↔ ∀ i h, f i h < bsup.{_, v} o f :=
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Ordinal/Family.lean` lines 809-815
```
constructor <;> intro H o ho <;> have := H o ho <;>
     rwa [← bsup_eq_blsub_of_lt_succ_limit ho fun a _ => h a] at *
 
@[deprecated IsNormal.ext (since := "2025-12-25")]
 theorem IsNormal.eq_iff_zero_and_succ {f g : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     (hg : IsNormal g) : f = g ↔ f 0 = g 0 ∧ ∀ a, f a = g a → f (succ a) = g (succ a) :=
   Order.IsNormal.ext hf hg
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Ordinal/Family.lean` lines 862-889
```
theorem iSup_natCast : iSup Nat.cast = ω :=
   (Ordinal.iSup_le fun n => (nat_lt_omega0 n).le).antisymm <| omega0_le.2 <| Ordinal.le_iSup _
 
theorem apply_omega0_of_isNormal {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) :
    ⨆ n : ℕ, f n = f ω := by
  rw [← iSup_natCast, hf.map_iSup (bddAbove_of_small _)]

@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_omega0 := apply_omega0_of_isNormal
 
 @[simp]
theorem iSup_add_natCast (o : Ordinal) : ⨆ n : ℕ, o + n = o + ω :=
  apply_omega0_of_isNormal (isNormal_add_right o)

@[deprecated (since := "2025-12-25")]
alias iSup_add_nat := iSup_add_natCast
 
 @[simp]
theorem iSup_mul_natCast (o : Ordinal) : ⨆ n : ℕ, o * n = o * ω := by
   rcases eq_zero_or_pos o with (rfl | ho)
   · rw [zero_mul]
     exact iSup_eq_zero_iff.2 fun n => zero_mul (n : Ordinal)
  · exact apply_omega0_of_isNormal (isNormal_mul_right ho)

@[deprecated (since := "2025-12-25")]
alias iSup_mul_nat := iSup_mul_natCast
 
 end Ordinal
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 13-20
```
# Fixed points of normal functions
 
 We prove various statements about the fixed points of normal ordinal functions. We state them in
two forms: as statements about indexed families of normal functions, and as statements about a
single normal function.
 
 Moreover, we prove some lemmas about the fixed points of specific normal functions.
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 82-88
```
(∀ i, f i b < nfpFamily f a) ↔ b < nfpFamily f a := by
   refine ⟨fun h ↦ ?_, apply_lt_nfpFamily H⟩
   let ⟨l, hl⟩ := lt_nfpFamily_iff.1 (h (Classical.arbitrary ι))
  exact lt_nfpFamily_iff.2 <| ⟨l, (H _).strictMono.le_apply.trans_lt hl⟩
 
 theorem nfpFamily_le_apply [Nonempty ι] [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a b} :
     (∃ i, nfpFamily f a ≤ f i b) ↔ nfpFamily f a ≤ b := by
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 4/7 — prompt 22,852 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 4/7: sites 25-32 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 97-112
```
theorem nfpFamily_fp [Small.{u} ι] {i} (H : IsNormal (f i)) (a) :
     f i (nfpFamily f a) = nfpFamily f a := by
  rw [nfpFamily, H.map_iSup (bddAbove_of_small _)]
   apply le_antisymm <;> refine Ordinal.iSup_le fun l => ?_
   · exact Ordinal.le_iSup _ (i::l)
  · exact H.strictMono.le_apply.trans (Ordinal.le_iSup _ _)
 
 theorem apply_le_nfpFamily [Small.{u} ι] [hι : Nonempty ι] (H : ∀ i, IsNormal (f i)) {a b} :
     (∀ i, f i b ≤ nfpFamily f a) ↔ b ≤ nfpFamily f a := by
   refine ⟨fun h => ?_, fun h i => ?_⟩
   · obtain ⟨i⟩ := hι
    exact (H i).strictMono.le_apply.trans (h i)
   · rw [← nfpFamily_fp (H i)]
     exact (H i).monotone h
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 171-177
```
exact nfpFamily_fp H _
   | limit o l IH =>
     have := l.nonempty_Iio.to_subtype
    rw [derivFamily_limit _ l, H.map_iSup (bddAbove_of_small _)]
     refine eq_of_forall_ge_iff fun c => ?_
     rw [Ordinal.iSup_le_iff, Ordinal.iSup_le_iff]
     refine forall_congr' fun a ↦ ?_
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 181-187
```
(∀ i, f i a ≤ a) ↔ ∃ o, derivFamily f o = a :=
   ⟨fun ha => by
     suffices ∀ (o), a ≤ derivFamily f o → ∃ o, derivFamily f o = a from
      this a (isNormal_derivFamily _).strictMono.le_apply
     intro o
     induction o using limitRecOn with
     | zero =>
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 207-214
```
theorem fp_iff_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
     (∀ i, f i a = a) ↔ ∃ o, derivFamily f o = a :=
  Iff.trans ⟨fun h i => le_of_eq (h i), fun h i => (H i).strictMono.le_apply.ge_iff_eq'.1 (h i)⟩
    (le_iff_derivFamily H)
 
 theorem mem_range_derivFamily [Small.{u} ι] (H : ∀ i, IsNormal (f i)) {a} :
     a ∈ Set.range (derivFamily f) ↔ ∀ i, f i a = a :=
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 288-321
```
rw [← iterate_succ_apply]
   exact iterate_le_nfp ..
 
theorem apply_lt_nfp (H : IsNormal f) {a b} : f b < nfp f a ↔ b < nfp f a := by
   unfold nfp
   rw [← @apply_lt_nfpFamily_iff Unit (fun _ => f) _ _ (fun _ => H) a b]
   exact ⟨fun h _ => h, fun h => h Unit.unit⟩
 
@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_lt_nfp := apply_lt_nfp

theorem nfp_le_apply (H : IsNormal f) {a b} : nfp f a ≤ f b ↔ nfp f a ≤ b :=
  le_iff_le_iff_lt_iff_lt.2 (apply_lt_nfp H)

@[deprecated (since := "2025-12-25")]
alias IsNormal.nfp_le_apply := nfp_le_apply
 
 theorem nfp_le_fp (H : Monotone f) {a b} (ab : a ≤ b) (h : f b ≤ b) : nfp f a ≤ b :=
   nfpFamily_le_fp (fun _ => H) ab fun _ => h
 
theorem nfp_fp (H : IsNormal f) : ∀ a, f (nfp f a) = nfp f a :=
   @nfpFamily_fp Unit (fun _ => f) _ () H
 
@[deprecated (since := "2025-12-25")]
alias IsNormal.nfp_fp := nfp_fp

theorem apply_le_nfp (H : IsNormal f) {a b} : f b ≤ nfp f a ↔ b ≤ nfp f a :=
  ⟨H.strictMono.le_apply.trans, fun h => by simpa only [nfp_fp H] using H.monotone h⟩

@[deprecated (since := "2025-12-25")]
alias IsNormal.apply_le_nfp := apply_le_nfp
 
 theorem nfp_eq_self {a} (h : f a = a) : nfp f a = a :=
   nfpFamily_eq_self fun _ => h
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 353-386
```
derivFamily_strictMono _
 
 theorem deriv_eq_id_of_nfp_eq_id (h : nfp f = id) : deriv f = id :=
  ((isNormal_deriv _).ext .id).2 (by simp [h])
 
 @[deprecated (since := "2025-10-25")]
 alias deriv_id_of_nfp_id := deriv_eq_id_of_nfp_eq_id
 
theorem deriv_fp (H : IsNormal f) : ∀ o, f (deriv f o) = deriv f o :=
   derivFamily_fp (i := ⟨⟩) H
 
@[deprecated (since := "2025-10-25")]
alias IsNormal.deriv_fp := deriv_fp

theorem le_iff_deriv (H : IsNormal f) {a} : f a ≤ a ↔ ∃ o, deriv f o = a := by
   unfold deriv
   rw [← le_iff_derivFamily fun _ : Unit => H]
   exact ⟨fun h _ => h, fun h => h Unit.unit⟩
 
@[deprecated (since := "2025-10-25")]
alias IsNormal.le_iff_deriv := le_iff_deriv

theorem mem_range_deriv (H : IsNormal f) {a} : a ∈ Set.range (deriv f) ↔ f a = a := by
  rw [Set.mem_range, ← H.strictMono.le_apply.ge_iff_eq', le_iff_deriv H]

@[deprecated mem_range_deriv (since := "2025-10-25")]
theorem fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a :=
  (mem_range_deriv H).symm
 
@[deprecated mem_range_deriv (since := "2025-10-25")]
alias IsNormal.fp_iff_deriv := fp_iff_deriv
 
 /-- `Ordinal.deriv` enumerates the fixed points of a normal function. -/
 theorem deriv_eq_enumOrd (H : IsNormal f) : deriv f = enumOrd (Function.fixedPoints f) := by
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 414-420
```
@[simp]
 theorem nfp_add_zero (a) : nfp (a + ·) 0 = a * ω := by
  simp_rw [← iSup_iterate_eq_nfp, ← iSup_mul_natCast]
   congr; funext n
   induction n with
   | zero => rw [Nat.cast_zero, mul_zero, iterate_zero_apply]
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 429-435
```
theorem add_eq_right_iff_mul_omega0_le {a b : Ordinal} : a + b = b ↔ a * ω ≤ b := by
   refine ⟨fun h => ?_, fun h => ?_⟩
   · rw [← nfp_add_zero a, ← deriv_zero_right]
    obtain ⟨c, hc⟩ := (mem_range_deriv (isNormal_add_right a)).2 h
     rw [← hc]
     exact (isNormal_deriv _).monotone (zero_le _)
   · have := Ordinal.add_sub_cancel_of_le h
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 5/7 — prompt 21,155 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 5/7: sites 33-40 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 438-450
```
theorem add_le_right_iff_mul_omega0_le {a b : Ordinal} : a + b ≤ b ↔ a * ω ≤ b := by
   rw [← add_eq_right_iff_mul_omega0_le]
  exact (isNormal_add_right a).strictMono.le_apply.ge_iff_eq'
 
 theorem deriv_add_eq_mul_omega0_add (a b : Ordinal.{u}) : deriv (a + ·) b = a * ω + b := by
   revert b
  rw [← funext_iff, IsNormal.ext (isNormal_deriv _) (isNormal_add_right _)]
   refine ⟨?_, fun a h => ?_⟩
  · rw [bot_eq_zero, deriv_zero_right, add_zero]
     exact nfp_add_zero a
   · rw [deriv_succ, h, add_succ]
     exact nfp_eq_self (add_eq_right_iff_mul_omega0_le.2 (le_self_add.trans (le_succ _)))
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 453-459
```
@[simp]
 theorem nfp_mul_one {a : Ordinal} (ha : 0 < a) : nfp (a * ·) 1 = a ^ ω := by
  rw [← iSup_iterate_eq_nfp, ← iSup_pow_natCast ha]
   congr
   funext n
   induction n with
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 509-515
```
theorem mul_le_right_iff_opow_omega0_dvd {a b : Ordinal} (ha : 0 < a) :
     a * b ≤ b ↔ (a ^ ω) ∣ b := by
   rw [← mul_eq_right_iff_opow_omega0_dvd]
  exact (isNormal_mul_right ha).strictMono.le_apply.ge_iff_eq'
 
 theorem nfp_mul_opow_omega0_add {a c : Ordinal} (b) (ha : 0 < a) (hc : 0 < c)
     (hca : c ≤ a ^ ω) : nfp (a * ·) (a ^ ω * b + c) = a ^ ω * succ b := by
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 519-525
```
gcongr
     · dsimp only; rw [← mul_assoc, ← opow_one_add, one_add_omega0]
   · obtain ⟨d, hd⟩ :=
      mul_eq_right_iff_opow_omega0_dvd.1 (nfp_fp (isNormal_mul_right ha) (a ^ ω * b + c))
     rw [hd]
     apply mul_le_mul_right
     have := le_nfp (a * ·) (a ^ ω * b + c)
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Ordinal/FixedPoint.lean` lines 532-540
```
deriv (a * ·) b = a ^ ω * b := by
   revert b
   rw [← funext_iff,
    IsNormal.ext (isNormal_deriv _) (isNormal_mul_right (opow_pos ω ha))]
   refine ⟨?_, fun c h => ?_⟩
  · rw [bot_eq_zero, deriv_zero_right, nfp_mul_zero, mul_zero]
   · rw [deriv_succ, h]
     exact nfp_mul_opow_omega0_add c ha zero_lt_one (one_le_iff_pos.2 (opow_pos _ ha))
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Ordinal/Principal.lean` lines 90-96
```
theorem op_eq_self_of_principal (hao : a < o) (H : IsNormal (op a))
     (ho : Principal op o) (ho' : IsSuccLimit o) : op a o = o := by
  apply H.strictMono.le_apply.antisymm'
   rw [H.apply_of_isSuccLimit ho', Ordinal.iSup_le_iff]
   exact fun ⟨b, hbo⟩ ↦ (ho hao hbo).le
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Ordinal/Principal.lean` lines 202-208
```
grw [ax, opow_succ, ← mul_add, add_omega0 xo]
   | limit b l IH =>
     rcases (lt_opow_of_isSuccLimit omega0_ne_zero l).1 h with ⟨x, xb, ax⟩
    apply (((isNormal_add_right a).comp <| isNormal_opow one_lt_omega0).le_iff_forall_le l).2
     intro y yb
     calc a + ω ^ y ≤ a + ω ^ max x y := by gcongr; exacts [omega0_pos, le_max_right ..]
     _ ≤ ω ^ max x y :=
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/Principal.lean` lines 340-350
```
· exact (lt_irrefl _).elim c0
   · rw [opow_succ] at ha
     obtain ⟨n, hn, an⟩ :=
      ((isNormal_mul_right <| opow_pos _ omega0_pos).lt_iff_exists_lt isSuccLimit_omega0).1 ha
     grw [an, opow_succ, mul_assoc]
     gcongr
     exacts [opow_pos _ omega0_pos, principal_mul_omega0 hn hb]
  · rcases ((isNormal_opow one_lt_omega0).lt_iff_exists_lt l).1 ha with ⟨x, hx, ax⟩
     refine (mul_le_mul' (le_of_lt ax) (le_of_lt hb)).trans_lt ?_
     rw [← opow_succ, opow_lt_opow_iff_right one_lt_omega0]
     exact l.succ_lt hx
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 6/7 — prompt 20,836 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 6/7: sites 41-48 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/Topology.lean` lines 178-189
```
have Hs := enumOrd_strictMono hs
   refine
     ⟨fun h => isClosed_iff_iSup.2 fun {ι} hι f hf => ?_, fun h =>
      isNormal_iff.2 ⟨Hs, fun a ha o H => ?_⟩⟩
   · let g : ι → Ordinal.{u} := fun i => (enumOrdOrderIso s hs).symm ⟨_, hf i⟩
     suffices enumOrd s (⨆ i, g i) = ⨆ i, f i by
       rw [← this]
       exact enumOrd_mem hs _
    rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]
     congr
     ext x
     change (enumOrdOrderIso s hs _).val = f x
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 91-97
```
· rwa [veblenWith_zero]
   · exact isNormal_veblenWith' f h
 
@[deprecated (since := "2025-12-25")]
 protected alias IsNormal.veblenWith := isNormal_veblenWith
 
 theorem mem_range_veblenWith (h : o ≠ 0) :
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 117-123
```
simp
 
 theorem veblenWith_succ (o : Ordinal) : veblenWith f (succ o) = deriv (veblenWith f o) := by
  rw [deriv_eq_enumOrd (isNormal_veblenWith hf o), veblenWith_of_ne_zero f (succ_ne_zero _),
     derivFamily_eq_enumOrd]
   · apply congr_arg
     ext a
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 128-137
```
· rw [Function.mem_fixedPoints_iff, ha]
     · rw [← ha]
       exact veblenWith_veblenWith_of_lt hf hb _
  · exact fun o ↦ isNormal_veblenWith hf o.1
 
 theorem veblenWith_right_strictMono (o : Ordinal) : StrictMono (veblenWith f o) :=
  (isNormal_veblenWith hf o).strictMono
 
 @[simp]
 theorem veblenWith_lt_veblenWith_iff_right : veblenWith f o a < veblenWith f o b ↔ a < b :=
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 187-194
```
(veblenWith_zero_strictMono hf hp).le_apply.trans <|
     (veblenWith_right_strictMono hf _).monotone (zero_le _)
 
theorem isNormal_veblenWith_zero (hp : 0 < f 0) : IsNormal (veblenWith f · 0) := by
  rw [isNormal_iff]
   refine ⟨veblenWith_zero_strictMono hf hp, fun o ho a IH ↦ ?_⟩
   rw [veblenWith_of_ne_zero f ho.ne_bot, derivFamily_zero]
   apply nfpFamily_le fun l ↦ ?_
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 206-214
```
rw [lt_succ_iff]
     exact le_max_left _ b
 
@[deprecated (since := "2025-12-25")]
alias IsNormal.veblenWith_zero := isNormal_veblenWith_zero

 theorem veblenWith_veblenWith_eq_veblenWith_iff (h : o₂ ≤ o₁) :
     veblenWith f o₁ (veblenWith f o₂ a) = veblenWith f o₂ a ↔ veblenWith f o₁ a = a := by
   grind [veblenWith_inj, → veblenWith_eq_self_of_le]
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 292-298
```
veblenWith_of_ne_zero _ h
 
 theorem isNormal_veblen (o : Ordinal) : IsNormal (veblen o) :=
  isNormal_veblenWith (isNormal_opow one_lt_omega0) o
 
 theorem mem_range_veblen (h : o ≠ 0) : a ∈ range (veblen o) ↔ ∀ b < o, veblen b a = a :=
   mem_range_veblenWith (isNormal_opow one_lt_omega0) h
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 356-362
```
left_le_veblenWith (isNormal_opow one_lt_omega0) (by simp) o a
 
 theorem isNormal_veblen_zero : IsNormal (veblen · 0) :=
  isNormal_veblenWith_zero (isNormal_opow one_lt_omega0) (by simp)
 
 theorem veblen_veblen_eq_veblen_iff (h : o₂ ≤ o₁) :
     veblen o₁ (veblen o₂ a) = veblen o₂ a ↔ veblen o₁ a = a :=
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33294 — window 7/7 — prompt 12,161 chars
==========================================================================================

## PR #33294 — refactor: deprecate `Ordinal.IsNormal` for `Order.IsNormal`

## Description

See issue #17033.

Moved from #28743.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Order/IsNormal.lean b/Mathlib/Order/IsNormal.lean
--- a/Mathlib/Order/IsNormal.lean
+++ b/Mathlib/Order/IsNormal.lean
@@ -50,6 +50,9 @@ namespace IsNormal
 section LinearOrder
 variable [LinearOrder α] [LinearOrder β] [LinearOrder γ]
 
+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f :=
+  hf.strictMono.monotone
+
 theorem isLUB_image_Iio_of_isSuccLimit {f : α → β} (hf : IsNormal f) {a : α} (ha : IsSuccLimit a) :
     IsLUB (f '' Iio a) (f a) := by
   refine ⟨?_, hf.2 ha⟩
diff --git a/Mathlib/SetTheory/Cardinal/Aleph.lean b/Mathlib/SetTheory/Cardinal/Aleph.lean
--- a/Mathlib/SetTheory/Cardinal/Aleph.lean
+++ b/Mathlib/SetTheory/Cardinal/Aleph.lean
@@ -158,7 +158,7 @@ theorem preOmega_le_of_forall_lt {o a : Ordinal} (ha : IsInitial a) (H : ∀ b <
   enumOrd_le_of_forall_lt ha H
 
 theorem isNormal_preOmega : IsNormal preOmega := by
-  rw [isNormal_iff_strictMono_limit]
+  rw [isNormal_iff]
   refine ⟨preOmega_strictMono, fun o ho a ha ↦
     (preOmega_le_of_forall_lt (isInitial_ord _) fun b hb ↦ ?_).trans (ord_card_le a)⟩
   rw [← (isInitial_ord _).card_lt_card, card_ord]
@@ -177,7 +177,7 @@ alias ⟨_, IsInitial.mem_range_preOmega⟩ := mem_range_preOmega_iff
 
 @[simp]
 theorem preOmega_omega0 : preOmega ω = ω := by
-  simp_rw [← isNormal_preOmega.apply_omega0, preOmega_natCast, iSup_natCast]
+  simp_rw [← apply_omega0_of_isNormal isNormal_preOmega, preOmega_natCast, iSup_natCast]
 
 @[simp]
 theorem omega0_le_preOmega_iff {x : Ordinal} : ω ≤ preOmega x ↔ ω ≤ x := by
@@ -247,7 +247,7 @@ theorem omega0_lt_omega_one : ω < ω₁ := by
 alias omega0_lt_omega1 := omega0_lt_omega_one
 
 theorem isNormal_omega : IsNormal omega :=
-  isNormal_preOmega.trans (isNormal_add_right _)
+  isNormal_preOmega.comp (isNormal_add_right _)
 
 @[simp]
 theorem range_omega : range omega = {x | ω ≤ x ∧ IsInitial x} := by
diff --git a/Mathlib/SetTheory/Cardinal/Cofinality.lean b/Mathlib/SetTheory/Cardinal/Cofinality.lean
--- a/Mathlib/SetTheory/Cardinal/Cofinality.lean
+++ b/Mathlib/SetTheory/Cardinal/Cofinality.lean
@@ -532,7 +532,7 @@ theorem cof_cof (a : Ordinal.{u}) : cof (cof a).ord = cof a := by
   obtain ⟨g, hg⟩ := exists_fundamental_sequence a.cof.ord
   exact ord_injective (hf.trans hg).cof_eq.symm
 
-protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
+theorem isFundamentalSequence_of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f)
     {a o} (ha : IsSuccLimit a) {g} (hg : IsFundamentalSequence a o g) :
     IsFundamentalSequence (f a) o fun b hb => f (g b hb) := by
   refine ⟨?_, @fun i j _ _ h => hf.strictMono (hg.2.1 _ _ h), ?_⟩
@@ -559,24 +559,33 @@ protected theorem IsNormal.isFundamentalSequence {f : Ordinal.{u} → Ordinal.{u
         hg.2.2]
     exact IsNormal.blsub_eq.{u, u} hf ha
 
-theorem IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.isFundamentalSequence := isFundamentalSequence_of_isNormal
+
+theorem cof_eq_of_isNormal {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a :=
   let ⟨_, hg⟩ := exists_fundamental_sequence a
-  ord_injective (hf.isFundamentalSequence ha hg).cof_eq
+  ord_injective (isFundamentalSequence_of_isNormal hf ha hg).cof_eq
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_eq := cof_eq_of_isNormal
 
-theorem IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
+theorem cof_le_of_isNormal {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a) := by
   rcases zero_or_succ_or_isSuccLimit a with (rfl | ⟨b, rfl⟩ | ha)
   · rw [cof_zero]
     exact zero_le _
   · rw [cof_succ, Cardinal.one_le_iff_ne_zero, cof_ne_zero, ← pos_iff_ne_zero]
     exact (zero_le (f b)).trans_lt (hf.strictMono (lt_succ b))
-  · rw [hf.cof_eq ha]
+  · rw [cof_eq_of_isNormal hf ha]
+
+@[deprecated (since := "2025-12-25")]
+alias IsNormal.cof_le := cof_le_of_isNormal
 
 @[simp]
 theorem cof_add (a b : Ordinal) : b ≠ 0 → cof (a + b) = cof b := fun h => by
   rcases zero_or_succ_or_isSuccLimit b with (rfl | ⟨c, rfl⟩ | hb)
   · contradiction
   · rw [add_succ, cof_succ, cof_succ]
-  · exact (isNormal_add_right a).cof_eq hb
+  · exact cof_eq_of_isNormal (isNormal_add_right a) hb
 
 theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
   rcases zero_or_succ_or_isSuccLimit o with (rfl | ⟨o, rfl⟩ | l)
@@ -599,11 +608,11 @@ theorem aleph0_le_cof {o} : ℵ₀ ≤ cof o ↔ IsSuccLimit o := by
 theorem cof_preOmega {o : Ordinal} (ho : IsSuccPrelimit o) : (preOmega o).cof = o.cof := by
   by_cases h : IsMin o
   · simp [h.eq_bot]
-  · exact isNormal_preOmega.cof_eq ⟨h, ho⟩
+  · exact cof_eq_of_isNormal isNormal_preOmega ⟨h, ho⟩
 
 @[simp]
 theorem cof_omega {o : Ordinal} (ho : IsSuccLimit o) : (ω_ o).cof = o.cof :=
-  isNormal_omega.cof_eq ho
+  cof_eq_of_isNormal isNormal_omega ho
 
 @[simp]
 theorem cof_omega0 : cof ω = ℵ₀ :=
diff --git a/Mathlib/SetTheory/Ordinal/Arithmetic.lean b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
--- a/Mathlib/SetTheory/Ordinal/Arithmetic.lean
+++ b/Mathlib/SetTheory/Ordinal/Arithmetic.lean
@@ -29,20 +29,19 @@ successor ordinals and limit ordinals, in `limitRecOn`.
 * `o₁ * o₂` is the lexicographic order on `o₂ × o₁`.
 * `o₁ / o₂` is the ordinal `o` such that `o₁ = o₂ * o + o'` with `o' < o₂`. We also define the
   divisibility predicate, and a modulo operation.
-* `Order.succ o = o + 1` is the successor of `o`.
-* `pred o` if the predecessor of `o`. If `o` is not a successor, we set `pred o = o`.
+* `limitRecOn` is the main induction principle of ordinals: if one can prove a property by
+  induction at successor ordinals and at limit ordinals, then it holds for all ordinals.
 
 We discuss the properties of casts of natural numbers of and of `ω` with respect to these
 operations.
 
-Some properties of the operations are also used to discuss general tools on ordinals:
+Note that some basic functions and properties of ordinals have been generalized to other orders:
 
+
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 3 sites, 24 facet items (window 7/7: sites 49-51 of 51)

### Site 1: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 553-559
```
@[simp]
 theorem omega0_opow_epsilon (o : Ordinal) : ω ^ ε_ o = ε_ o := by
  rw [epsilon_eq_deriv, deriv_fp (isNormal_opow one_lt_omega0)]
 
 /-- `ε₀` is the limit of `0`, `ω ^ 0`, `ω ^ ω ^ 0`, … -/
 theorem lt_epsilon0 : o < ε₀ ↔ ∃ n : ℕ, o < (fun a ↦ ω ^ a)^[n] 0 := by
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 600-606
```
isNormal_deriv _
 
 theorem mem_range_gamma : o ∈ range Γ_ ↔ veblen o 0 = o :=
  mem_range_deriv isNormal_veblen_zero
 
 theorem strictMono_gamma : StrictMono gamma :=
   isNormal_gamma.strictMono
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/SetTheory/Ordinal/Veblen.lean` lines 622-628
```
@[simp]
 theorem veblen_gamma_zero (o : Ordinal) : veblen (Γ_ o) 0 = Γ_ o :=
  deriv_fp isNormal_veblen_zero o
 
 theorem gamma0_eq_nfp : Γ₀ = nfp (veblen · 0) 0 :=
   deriv_zero_right _
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33332 — window 1/1 — prompt 15,830 chars
==========================================================================================

## PR #33332 — chore: golf using `grind`. add `grind` annotations.

## Description

The goal of this golfing PR is to decrease the number of times lemmas are called explicitly (replacing calls to lemmas with calls to tactics). Any decrease in compilation time is a welcome side effect, although it is not a primary objective.

Trace profiling results (shown if ≥10 ms before or after):
* `SimpleGraph.adj_of_mem_walk_support`: 33 ms before, 46 ms after
* `Finset.mem_of_max`: 13 ms before, 88 ms after
* `Set.eq_of_notMem_uIoc_of_notMem_uIoc`: 59 ms before, 44 ms after  🎉

This golfing PR is batched under the following guidelines:
* Up to ~5 changed files per PR
* Up to ~25 changed declarations per PR
* Up to ~100 changed lines per PR

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean b/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean
--- a/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean
+++ b/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean
@@ -252,22 +252,7 @@ lemma adj_of_mem_walk_support {G : SimpleGraph V} {u v : V} (p : G.Walk u v) (hp
   | nil =>
     exact (hp Walk.Nil.nil).elim
   | @cons u v w h p ih =>
-    cases List.mem_cons.mp hx with
-    | inl hxu =>
-      rw [hxu]
-      exact ⟨v, ⟨((Walk.cons h p).mem_support_iff).mpr (Or.inr p.start_mem_support), h⟩⟩
-    | inr hxp =>
-      cases Decidable.em p.Nil with
-      | inl hnil =>
-        rw [Walk.nil_iff_support_eq.mp hnil] at hxp
-        rw [show (x = v) by simp_all]
-        exact ⟨u, ⟨(Walk.cons h p).start_mem_support, G.adj_symm h⟩⟩
-      | inr hnotnil =>
-        obtain ⟨y, hy⟩ := ih hnotnil hxp
-        refine ⟨y, ⟨?_, hy.right⟩⟩
-        rw [Walk.mem_support_iff]
-        simp only [Walk.support_cons, List.tail_cons]
-        exact Or.inr hy.left
+    grind [Walk.nil_iff_support_eq, Walk.support_eq_cons, adj_comm]
 
 lemma mem_support_of_mem_walk_support {G : SimpleGraph V} {u v : V} (p : G.Walk u v) (hp : ¬p.Nil)
     {w : V} (hw : w ∈ p.support) : w ∈ G.support := by
diff --git a/Mathlib/Combinatorics/SimpleGraph/Walks/Basic.lean b/Mathlib/Combinatorics/SimpleGraph/Walks/Basic.lean
--- a/Mathlib/Combinatorics/SimpleGraph/Walks/Basic.lean
+++ b/Mathlib/Combinatorics/SimpleGraph/Walks/Basic.lean
@@ -134,7 +134,7 @@ def edges {u v : V} (p : G.Walk u v) : List (Sym2 V) := p.darts.map Dart.edge
 @[simp]
 theorem support_nil {u : V} : (nil : G.Walk u u).support = [u] := rfl
 
-@[simp]
+@[simp, grind =]
 theorem support_cons {u v w : V} (h : G.Adj u v) (p : G.Walk v w) :
     (cons h p).support = u :: p.support := rfl
 
diff --git a/Mathlib/Data/Finset/Max.lean b/Mathlib/Data/Finset/Max.lean
--- a/Mathlib/Data/Finset/Max.lean
+++ b/Mathlib/Data/Finset/Max.lean
@@ -44,7 +44,7 @@ theorem max_eq_sup_withBot (s : Finset α) : s.max = sup s (↑) :=
 theorem max_empty : (∅ : Finset α).max = ⊥ :=
   rfl
 
-@[simp]
+@[simp, grind =]
 theorem max_insert {a : α} {s : Finset α} : (insert a s).max = max ↑a s.max :=
   fold_insert_idem
 
@@ -73,15 +73,7 @@ theorem max_eq_bot {s : Finset α} : s.max = ⊥ ↔ s = ∅ :=
 theorem mem_of_max {s : Finset α} : ∀ {a : α}, s.max = a → a ∈ s := by
   induction s using Finset.induction_on with
   | empty => intro _ H; cases H
-  | insert b s _ ih =>
-    intro a h
-    by_cases p : b = a
-    · induction p
-      exact mem_insert_self b s
-    · rcases max_choice (↑b) s.max with q | q <;> rw [max_insert, q] at h
-      · cases h
-        cases p rfl
-      · exact mem_insert_of_mem (ih h)
+  | insert b s _ ih => grind [WithBot.coe_eq_coe]
 
 theorem le_max {a : α} {s : Finset α} (as : a ∈ s) : ↑a ≤ s.max :=
   le_sup as
diff --git a/Mathlib/Order/Interval/Set/UnorderedInterval.lean b/Mathlib/Order/Interval/Set/UnorderedInterval.lean
--- a/Mathlib/Order/Interval/Set/UnorderedInterval.lean
+++ b/Mathlib/Order/Interval/Set/UnorderedInterval.lean
@@ -252,8 +252,8 @@ scoped[Interval] notation "Ι" => Set.uIoc
 
 open scoped Interval
 
-@[simp] lemma uIoc_of_le (h : a ≤ b) : Ι a b = Ioc a b := by simp [uIoc, h]
-@[simp] lemma uIoc_of_ge (h : b ≤ a) : Ι a b = Ioc b a := by simp [uIoc, h]
+@[simp, grind =] lemma uIoc_of_le (h : a ≤ b) : Ι a b = Ioc a b := by simp [uIoc, h]
+@[simp, grind =] lemma uIoc_of_ge (h : b ≤ a) : Ι a b = Ioc b a := by simp [uIoc, h]
 
 lemma uIoc_eq_union : Ι a b = Ioc a b ∪ Ioc b a := by
   cases le_total a b <;> simp [uIoc, *]
@@ -294,11 +294,7 @@ lemma eq_of_mem_uIoc_of_mem_uIoc' : b ∈ Ι a c → c ∈ Ι a b → b = c := b
 
 lemma eq_of_notMem_uIoc_of_notMem_uIoc (ha : a ≤ c) (hb : b ≤ c) :
     a ∉ Ι b c → b ∉ Ι a c → a = b := by
-  simp_rw [notMem_uIoc]
-  rintro (⟨_, _⟩ | ⟨_, _⟩) (⟨_, _⟩ | ⟨_, _⟩) <;>
-      apply le_antisymm <;>
-    first | assumption | exact le_of_lt ‹_› |
-    exact absurd hb (not_le_of_gt ‹c < b›) | exact absurd ha (not_le_of_gt ‹c < a›)
+  grind
 
 @[deprecated (since := "2025-05-23")]
 alias eq_of_not_mem_uIoc_of_not_mem_uIoc := eq_of_notMem_uIoc_of_notMem_uIoc

```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 6 sites, 48 facet items

### Site 1: `Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean` lines 252-258
```
| nil =>
     exact (hp Walk.Nil.nil).elim
   | @cons u v w h p ih =>
    grind [Walk.nil_iff_support_eq, Walk.support_eq_cons, adj_comm]
 
 lemma mem_support_of_mem_walk_support {G : SimpleGraph V} {u v : V} (p : G.Walk u v) (hp : ¬p.Nil)
     {w : V} (hw : w ∈ p.support) : w ∈ G.support := by
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Combinatorics/SimpleGraph/Walks/Basic.lean` lines 134-140
```
@[simp]
 theorem support_nil {u : V} : (nil : G.Walk u u).support = [u] := rfl
 
@[simp, grind =]
 theorem support_cons {u v w : V} (h : G.Adj u v) (p : G.Walk v w) :
     (cons h p).support = u :: p.support := rfl
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Data/Finset/Max.lean` lines 44-50
```
theorem max_empty : (∅ : Finset α).max = ⊥ :=
   rfl
 
@[simp, grind =]
 theorem max_insert {a : α} {s : Finset α} : (insert a s).max = max ↑a s.max :=
   fold_insert_idem
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Data/Finset/Max.lean` lines 73-79
```
theorem mem_of_max {s : Finset α} : ∀ {a : α}, s.max = a → a ∈ s := by
   induction s using Finset.induction_on with
   | empty => intro _ H; cases H
  | insert b s _ ih => grind [WithBot.coe_eq_coe]
 
 theorem le_max {a : α} {s : Finset α} (as : a ∈ s) : ↑a ≤ s.max :=
   le_sup as
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Order/Interval/Set/UnorderedInterval.lean` lines 252-259
```
open scoped Interval
 
@[simp, grind =] lemma uIoc_of_le (h : a ≤ b) : Ι a b = Ioc a b := by simp [uIoc, h]
@[simp, grind =] lemma uIoc_of_ge (h : b ≤ a) : Ι a b = Ioc b a := by simp [uIoc, h]
 
 lemma uIoc_eq_union : Ι a b = Ioc a b ∪ Ioc b a := by
   cases le_total a b <;> simp [uIoc, *]
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Order/Interval/Set/UnorderedInterval.lean` lines 294-300
```
lemma eq_of_notMem_uIoc_of_notMem_uIoc (ha : a ≤ c) (hb : b ≤ c) :
     a ∉ Ι b c → b ∉ Ι a c → a = b := by
  grind
 
 @[deprecated (since := "2025-05-23")]
 alias eq_of_not_mem_uIoc_of_not_mem_uIoc := eq_of_notMem_uIoc_of_notMem_uIoc
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33356 — window 1/1 — prompt 9,015 chars
==========================================================================================

## PR #33356 — feat: hasDetPlusMinusOne_iff_abs_det

## Description

This seems like a useful characterization.

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/Ring/Units.lean b/Mathlib/Algebra/Ring/Units.lean
--- a/Mathlib/Algebra/Ring/Units.lean
+++ b/Mathlib/Algebra/Ring/Units.lean
@@ -43,6 +43,10 @@ protected theorem val_neg (u : αˣ) : (↑(-u) : α) = -u :=
 protected theorem coe_neg_one : ((-1 : αˣ) : α) = -1 :=
   rfl
 
+@[simp, norm_cast]
+theorem val_eq_neg_one {a : αˣ} : (a : α) = -1 ↔ a = -1 := by
+  rw [← Units.coe_neg_one, val_inj]
+
 instance : HasDistribNeg αˣ := val_injective.hasDistribNeg _ Units.val_neg val_mul
 
 theorem neg_divp (a : α) (u : αˣ) : -(a /ₚ u) = -a /ₚ u := by simp only [divp, neg_mul]
diff --git a/Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean b/Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean
--- a/Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean
+++ b/Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean
@@ -43,6 +43,11 @@ lemma HasDetPlusMinusOne.abs_det [LinearOrder R] [IsOrderedRing R] [HasDetPlusMi
     {g} (hg : g ∈ Γ) : |g.det.val| = 1 := by
   rcases HasDetPlusMinusOne.det_eq hg with h | h <;> simp [h]
 
+lemma hasDetPlusMinusOne_iff_abs_det [LinearOrder R] [IsOrderedRing R] :
+    HasDetPlusMinusOne Γ ↔ ∀ {g}, g ∈ Γ → |g.det.val| = 1 := by
+  refine ⟨fun h {g} hg => h.abs_det hg, fun h => ⟨?_⟩⟩
+  simpa [-GeneralLinearGroup.val_det_apply, abs_eq zero_le_one] using @h
+
 /-- Typeclass saying that a subgroup of `GL(n, R)` is contained in `SL(n, R)`. Necessary so that
 the typeclass system can detect when the slash action is `ℂ`-linear. -/
 class HasDetOne : Prop where
@@ -102,8 +107,8 @@ instance IsArithmetic.finiteIndex_comap (𝒢 : Subgroup (GL (Fin 2) ℝ)) [IsAr
   ⟨𝒢.index_comap (mapGL (R := ℤ) ℝ) ▸ IsArithmetic.is_commensurable.1⟩
 
 instance {Γ : Subgroup (GL (Fin 2) ℝ)} [h : Γ.IsArithmetic] : HasDetPlusMinusOne Γ := by
-  refine ⟨fun {g} hg ↦ ?_⟩
-  suffices |g.det.val| = 1 by rcases abs_cases g.det.val <;> aesop
+  rw [hasDetPlusMinusOne_iff_abs_det]
+  intro g hg
   obtain ⟨n, hn, _, hgn⟩ := Subgroup.exists_pow_mem_of_relIndex_ne_zero
     Subgroup.IsArithmetic.is_commensurable.2 hg
   suffices |(g.det ^ n).val| = 1 by simpa [← abs_pow, abs_pow_eq_one _ (Nat.ne_zero_of_lt hn)]

```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 3 sites, 24 facet items

### Site 1: `Mathlib/Algebra/Ring/Units.lean` lines 43-52
```
protected theorem coe_neg_one : ((-1 : αˣ) : α) = -1 :=
   rfl
 
@[simp, norm_cast]
theorem val_eq_neg_one {a : αˣ} : (a : α) = -1 ↔ a = -1 := by
  rw [← Units.coe_neg_one, val_inj]

 instance : HasDistribNeg αˣ := val_injective.hasDistribNeg _ Units.val_neg val_mul
 
 theorem neg_divp (a : α) (u : αˣ) : -(a /ₚ u) = -a /ₚ u := by simp only [divp, neg_mul]
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean` lines 43-53
```
{g} (hg : g ∈ Γ) : |g.det.val| = 1 := by
   rcases HasDetPlusMinusOne.det_eq hg with h | h <;> simp [h]
 
lemma hasDetPlusMinusOne_iff_abs_det [LinearOrder R] [IsOrderedRing R] :
    HasDetPlusMinusOne Γ ↔ ∀ {g}, g ∈ Γ → |g.det.val| = 1 := by
  refine ⟨fun h {g} hg => h.abs_det hg, fun h => ⟨?_⟩⟩
  simpa [-GeneralLinearGroup.val_det_apply, abs_eq zero_le_one] using @h

 /-- Typeclass saying that a subgroup of `GL(n, R)` is contained in `SL(n, R)`. Necessary so that
 the typeclass system can detect when the slash action is `ℂ`-linear. -/
 class HasDetOne : Prop where
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean` lines 107-114
```
⟨𝒢.index_comap (mapGL (R := ℤ) ℝ) ▸ IsArithmetic.is_commensurable.1⟩
 
 instance {Γ : Subgroup (GL (Fin 2) ℝ)} [h : Γ.IsArithmetic] : HasDetPlusMinusOne Γ := by
  rw [hasDetPlusMinusOne_iff_abs_det]
  intro g hg
   obtain ⟨n, hn, _, hgn⟩ := Subgroup.exists_pow_mem_of_relIndex_ne_zero
     Subgroup.IsArithmetic.is_commensurable.2 hg
   suffices |(g.det ^ n).val| = 1 by simpa [← abs_pow, abs_pow_eq_one _ (Nat.ne_zero_of_lt hn)]
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33421 — window 1/3 — prompt 23,104 chars
==========================================================================================

## PR #33421 — chore(Algebra/Order/Floor): review API about `round`

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AddConstMap/Basic.lean b/Mathlib/Algebra/AddConstMap/Basic.lean
--- a/Mathlib/Algebra/AddConstMap/Basic.lean
+++ b/Mathlib/Algebra/AddConstMap/Basic.lean
@@ -9,6 +9,7 @@ public import Mathlib.Algebra.Group.Action.Pi
 public import Mathlib.Algebra.Group.End
 public import Mathlib.Algebra.Module.NatInt
 public import Mathlib.Algebra.Order.Archimedean.Basic
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Maps (semi)conjugating a shift to a shift
diff --git a/Mathlib/Algebra/Order/Archimedean/Basic.lean b/Mathlib/Algebra/Order/Archimedean/Basic.lean
--- a/Mathlib/Algebra/Order/Archimedean/Basic.lean
+++ b/Mathlib/Algebra/Order/Archimedean/Basic.lean
@@ -10,6 +10,7 @@ public import Mathlib.Algebra.Order.Monoid.Units
 public import Mathlib.Algebra.Order.Ring.Pow
 public import Mathlib.Data.Int.LeastGreatest
 public import Mathlib.Data.Rat.Floor
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Archimedean groups and fields.
diff --git a/Mathlib/Algebra/Order/Floor/Ring.lean b/Mathlib/Algebra/Order/Floor/Ring.lean
--- a/Mathlib/Algebra/Order/Floor/Ring.lean
+++ b/Mathlib/Algebra/Order/Floor/Ring.lean
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
+
 end LinearOrderedRing
 
 section LinearOrderedCommRing
@@ -627,19 +636,36 @@ theorem ceil_ofNat (n : ℕ) [n.AtLeastTwo] : ⌈(ofNat(n) : R)⌉ = ofNat(n) :=
 theorem ceil_add_intCast (a : R) (z : ℤ) : ⌈a + z⌉ = ⌈a⌉ + z := by
   rw [← neg_inj, neg_add', ← floor_neg, ← floor_neg, neg_add', floor_sub_intCast]
 
+@[simp]
+theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈z + a⌉ = z + ⌈a⌉ := by
+  rw [add_comm, ceil_add_intCast, add_comm]
+
 @[simp]
 theorem ceil_add_natCast (a : R) (n : ℕ) : ⌈a + n⌉ = ⌈a⌉ + n := by
   rw [← Int.cast_natCast, ceil_add_intCast]
 
+@[simp]
+theorem ceil_natCast_add (n : ℕ) (a : R) : ⌈n + a⌉ = n + ⌈a⌉ :=
+  mod_cast ceil_intCast_add n a
+
 @[simp]
 theorem ceil_add_one (a : R) : ⌈a + 1⌉ = ⌈a⌉ + 1 := by
   rw [← ceil_add_intCast a (1 : ℤ), cast_one]
 
+@[simp]
+theorem ceil_one_add (a : R) : ⌈1 + a⌉ = 1 + ⌈a⌉ :=
+  mod_cast ceil_natCast_add 1 a
+
 @[simp]
 theorem ceil_add_ofNat (a : R) (n : ℕ) [n.AtLeastTwo] :
     ⌈a + ofNat(n)⌉ = ⌈a⌉ + ofNat(n) :=
   ceil_add_natCast a n
 
+@[simp]
+theorem ceil_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
+    ⌈ofNat(n) + a⌉ = ofNat(n) + ⌈a⌉ :=
+  ceil_natCast_add n a
+
 @[simp]
 theorem ceil_sub_intCast (a : R) (z : ℤ) : ⌈a - z⌉ = ⌈a⌉ - z :=
   Eq.trans (by rw [Int.cast_neg, sub_eq_add_neg]) (ceil_add_intCast _ _)
diff --git a/Mathlib/Algebra/Order/Round.lean b/Mathlib/Algebra/Order/Round.lean
--- a/Mathlib/Algebra/Order/Round.lean
+++ b/Mathlib/Algebra/Order/Round.lean
@@ -6,7 +6,7 @@ Authors: Mario Carneiro, Kevin Kappelmann
 module
 
 public import Mathlib.Algebra.Order.Floor.Ring
-public import Mathlib.Algebra.Order.Interval.Set.Group
+import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Rounding
@@ -45,6 +45,26 @@ variable [Ring α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 def round (x : α) : ℤ :=
   if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
 
+/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.
+
+TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
+theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
+  rw [← floor_add_fract x, round, fract_intCast_add, fract_fract, floor_intCast_add, mul_add,
+    ← Int.cast_ofNat, ← Int.cast_mul, floor_intCast_add, ceil_intCast_add, add_assoc,
+    Int.mul_add_ediv_left _ _ two_ne_zero, Int.cast_ofNat]
+  split_ifs with h <;> congr 1
+  · rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr]
+    · simp
+    · simp [h]
+    · suffices fract x < 1 by simpa
+      refine lt_of_le_of_lt ?_ h
+      apply le_mul_of_one_le_left <;> simp
+  · have H : ⌊2 * fract x⌋ = 1 := by simpa [floor_eq_iff, ← two_mul, fract_lt_one] using h
+    suffices 0 < fract x by simp [this, H, ceil_eq_iff, (fract_lt_one _).le]
+    contrapose! h
+    grw [h]
+    simp
+
 @[simp]
 theorem round_zero : round (0 : α) = 0 := by simp [round]
 
@@ -61,6 +81,17 @@ theorem round_ofNat (n : ℕ) [n.AtLeastTwo] : round (ofNat(n) : α) = ofNat(n)
 @[simp]
 theorem round_intCast (n : ℤ) : round (n : α) = n := by simp [round]
 
+/-- Away from the points with fractional part `1 / 2`, `round x = ⌈2 * x⌉ / 2`. -/
+theorem round_eq_half_ceil_two_mul {x : α} (hx : 2 * fract x ≠ 1) : round x = ⌈2 * x⌉ / 2 := by
+  rcases em (2 * x ∈ range Int.cast) with ⟨m, hm⟩ | hx'
+  · rw [← hm, ceil_intCast]
+    rcases m.even_or_odd with ⟨m, rfl⟩ | ⟨m, rfl⟩
+    · obtain rfl : m = x := mul_left_cancel₀ two_ne_zero <| by simp [← hm, ← two_mul]
+      rw [round_intCast, ← two_mul, Int.mul_ediv_cancel_left _ two_ne_zero]
+    · refine absurd ?_ hx
+      exact two_mul_fract_eq_one_iff_exists_int.mpr ⟨m, mod_cast hm.symm⟩
+  · rw [round_eq', (ceil_eq_floor_add_one_iff_notMem _).mpr hx']
+
 @[simp]
 theorem round_add_intCast (x : α) (y : ℤ) : round (x + y) = round x + y := by
   rw [round, round, Int.fract_add_intCast, Int.floor_add_intCast, Int.ceil_add_intCast,
@@ -140,38 +171,21 @@ section LinearOrderedField
 variable [Field α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 
 theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
-  simp_rw [round, (by simp only [lt_div_iff₀', two_pos] : 2 * fract x < 1 ↔ fract x < 1 / 2)]
-  rcases lt_or_ge (fract x) (1 / 2) with hx | hx
-  · conv_rhs => rw [← fract_add_floor x, add_assoc, add_left_comm, fl
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 1/3: sites 1-8 of 23)

### Site 1: `Mathlib/Algebra/AddConstMap/Basic.lean` lines 9-15
```
public import Mathlib.Algebra.Group.End
 public import Mathlib.Algebra.Module.NatInt
 public import Mathlib.Algebra.Order.Archimedean.Basic
import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Maps (semi)conjugating a shift to a shift
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Algebra/Order/Archimedean/Basic.lean` lines 10-16
```
public import Mathlib.Algebra.Order.Ring.Pow
 public import Mathlib.Data.Int.LeastGreatest
 public import Mathlib.Data.Rat.Floor
import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Archimedean groups and fields.
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Algebra/Order/Floor/Ring.lean` lines 267-281
```
theorem mul_natCast_floor_div_cancel {n : ℕ} (hn : n ≠ 0) (a : R) : ⌊a * n⌋ / n = ⌊a⌋ := by
   simpa using mul_cast_floor_div_cancel_of_pos (n := n) (by positivity) a
 
theorem two_mul_fract_eq_one_iff_exists_int {x : R} :
    2 * fract x = 1 ↔ ∃ n : ℤ, 2 * x = 2 * n + 1 := by
  rw [fract, mul_sub, sub_eq_iff_eq_add']
  refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩
  rintro ⟨n, hn⟩
  convert hn
  rw [floor_eq_iff, ← mul_le_mul_iff_right₀ two_pos, ← mul_lt_mul_iff_right₀ two_pos, hn]
  simp [mul_add]

 end LinearOrderedRing
 
 section LinearOrderedCommRing
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Algebra/Order/Floor/Ring.lean` lines 636-671
```
theorem ceil_add_intCast (a : R) (z : ℤ) : ⌈a + z⌉ = ⌈a⌉ + z := by
   rw [← neg_inj, neg_add', ← floor_neg, ← floor_neg, neg_add', floor_sub_intCast]
 
@[simp]
theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈z + a⌉ = z + ⌈a⌉ := by
  rw [add_comm, ceil_add_intCast, add_comm]

 @[simp]
 theorem ceil_add_natCast (a : R) (n : ℕ) : ⌈a + n⌉ = ⌈a⌉ + n := by
   rw [← Int.cast_natCast, ceil_add_intCast]
 
@[simp]
theorem ceil_natCast_add (n : ℕ) (a : R) : ⌈n + a⌉ = n + ⌈a⌉ :=
  mod_cast ceil_intCast_add n a

 @[simp]
 theorem ceil_add_one (a : R) : ⌈a + 1⌉ = ⌈a⌉ + 1 := by
   rw [← ceil_add_intCast a (1 : ℤ), cast_one]
 
@[simp]
theorem ceil_one_add (a : R) : ⌈1 + a⌉ = 1 + ⌈a⌉ :=
  mod_cast ceil_natCast_add 1 a

 @[simp]
 theorem ceil_add_ofNat (a : R) (n : ℕ) [n.AtLeastTwo] :
     ⌈a + ofNat(n)⌉ = ⌈a⌉ + ofNat(n) :=
   ceil_add_natCast a n
 
@[simp]
theorem ceil_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
    ⌈ofNat(n) + a⌉ = ofNat(n) + ⌈a⌉ :=
  ceil_natCast_add n a

 @[simp]
 theorem ceil_sub_intCast (a : R) (z : ℤ) : ⌈a - z⌉ = ⌈a⌉ - z :=
   Eq.trans (by rw [Int.cast_neg, sub_eq_add_neg]) (ceil_add_intCast _ _)
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Algebra/Order/Round.lean` lines 6-12
```
module
 
 public import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Rounding
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Algebra/Order/Round.lean` lines 45-70
```
def round (x : α) : ℤ :=
   if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
 
/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.

TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
  rw [← floor_add_fract x, round, fract_intCast_add, fract_fract, floor_intCast_add, mul_add,
    ← Int.cast_ofNat, ← Int.cast_mul, floor_intCast_add, ceil_intCast_add, add_assoc,
    Int.mul_add_ediv_left _ _ two_ne_zero, Int.cast_ofNat]
  split_ifs with h <;> congr 1
  · rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr]
    · simp
    · simp [h]
    · suffices fract x < 1 by simpa
      refine lt_of_le_of_lt ?_ h
      apply le_mul_of_one_le_left <;> simp
  · have H : ⌊2 * fract x⌋ = 1 := by simpa [floor_eq_iff, ← two_mul, fract_lt_one] using h
    suffices 0 < fract x by simp [this, H, ceil_eq_iff, (fract_lt_one _).le]
    contrapose! h
    grw [h]
    simp

 @[simp]
 theorem round_zero : round (0 : α) = 0 := by simp [round]
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Algebra/Order/Round.lean` lines 81-97
```
@[simp]
 theorem round_intCast (n : ℤ) : round (n : α) = n := by simp [round]
 
/-- Away from the points with fractional part `1 / 2`, `round x = ⌈2 * x⌉ / 2`. -/
theorem round_eq_half_ceil_two_mul {x : α} (hx : 2 * fract x ≠ 1) : round x = ⌈2 * x⌉ / 2 := by
  rcases em (2 * x ∈ range Int.cast) with ⟨m, hm⟩ | hx'
  · rw [← hm, ceil_intCast]
    rcases m.even_or_odd with ⟨m, rfl⟩ | ⟨m, rfl⟩
    · obtain rfl : m = x := mul_left_cancel₀ two_ne_zero <| by simp [← hm, ← two_mul]
      rw [round_intCast, ← two_mul, Int.mul_ediv_cancel_left _ two_ne_zero]
    · refine absurd ?_ hx
      exact two_mul_fract_eq_one_iff_exists_int.mpr ⟨m, mod_cast hm.symm⟩
  · rw [round_eq', (ceil_eq_floor_add_one_iff_notMem _).mpr hx']

 @[simp]
 theorem round_add_intCast (x : α) (y : ℤ) : round (x + y) = round x + y := by
   rw [round, round, Int.fract_add_intCast, Int.floor_add_intCast, Int.ceil_add_intCast,
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/Algebra/Order/Round.lean` lines 171-191
```
variable [Field α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 
 theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
  rw [← cast_mul_floor_div_cancel_of_pos two_pos, round_eq']
  simp [mul_add]

theorem round_eq_iff {x : α} {n : ℤ} : round x = n ↔ x ∈ Ico (n - 1 / 2 : α) (n + 1 / 2) := by
  norm_num [round_eq, floor_eq_iff, ← lt_sub_iff_add_lt, add_sub_assoc]

@[simp]
theorem round_two_inv : round (2⁻¹ : α) = 1 := by norm_num [round_eq_iff]

@[simp]
theorem round_neg_two_inv : round (-2⁻¹ : α) = 0 := by norm_num [round_eq_iff]
 
 @[simp]
 theorem round_eq_zero_iff {x : α} : round x = 0 ↔ x ∈ Ico (-(1 / 2)) ((1 : α) / 2) := by
  simp [round_eq_iff]
 
 theorem abs_sub_round (x : α) : |x - round x| ≤ 1 / 2 := by
   rw [round_eq, abs_sub_le_iff]
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33421 — window 2/3 — prompt 20,219 chars
==========================================================================================

## PR #33421 — chore(Algebra/Order/Floor): review API about `round`

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AddConstMap/Basic.lean b/Mathlib/Algebra/AddConstMap/Basic.lean
--- a/Mathlib/Algebra/AddConstMap/Basic.lean
+++ b/Mathlib/Algebra/AddConstMap/Basic.lean
@@ -9,6 +9,7 @@ public import Mathlib.Algebra.Group.Action.Pi
 public import Mathlib.Algebra.Group.End
 public import Mathlib.Algebra.Module.NatInt
 public import Mathlib.Algebra.Order.Archimedean.Basic
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Maps (semi)conjugating a shift to a shift
diff --git a/Mathlib/Algebra/Order/Archimedean/Basic.lean b/Mathlib/Algebra/Order/Archimedean/Basic.lean
--- a/Mathlib/Algebra/Order/Archimedean/Basic.lean
+++ b/Mathlib/Algebra/Order/Archimedean/Basic.lean
@@ -10,6 +10,7 @@ public import Mathlib.Algebra.Order.Monoid.Units
 public import Mathlib.Algebra.Order.Ring.Pow
 public import Mathlib.Data.Int.LeastGreatest
 public import Mathlib.Data.Rat.Floor
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Archimedean groups and fields.
diff --git a/Mathlib/Algebra/Order/Floor/Ring.lean b/Mathlib/Algebra/Order/Floor/Ring.lean
--- a/Mathlib/Algebra/Order/Floor/Ring.lean
+++ b/Mathlib/Algebra/Order/Floor/Ring.lean
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
+
 end LinearOrderedRing
 
 section LinearOrderedCommRing
@@ -627,19 +636,36 @@ theorem ceil_ofNat (n : ℕ) [n.AtLeastTwo] : ⌈(ofNat(n) : R)⌉ = ofNat(n) :=
 theorem ceil_add_intCast (a : R) (z : ℤ) : ⌈a + z⌉ = ⌈a⌉ + z := by
   rw [← neg_inj, neg_add', ← floor_neg, ← floor_neg, neg_add', floor_sub_intCast]
 
+@[simp]
+theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈z + a⌉ = z + ⌈a⌉ := by
+  rw [add_comm, ceil_add_intCast, add_comm]
+
 @[simp]
 theorem ceil_add_natCast (a : R) (n : ℕ) : ⌈a + n⌉ = ⌈a⌉ + n := by
   rw [← Int.cast_natCast, ceil_add_intCast]
 
+@[simp]
+theorem ceil_natCast_add (n : ℕ) (a : R) : ⌈n + a⌉ = n + ⌈a⌉ :=
+  mod_cast ceil_intCast_add n a
+
 @[simp]
 theorem ceil_add_one (a : R) : ⌈a + 1⌉ = ⌈a⌉ + 1 := by
   rw [← ceil_add_intCast a (1 : ℤ), cast_one]
 
+@[simp]
+theorem ceil_one_add (a : R) : ⌈1 + a⌉ = 1 + ⌈a⌉ :=
+  mod_cast ceil_natCast_add 1 a
+
 @[simp]
 theorem ceil_add_ofNat (a : R) (n : ℕ) [n.AtLeastTwo] :
     ⌈a + ofNat(n)⌉ = ⌈a⌉ + ofNat(n) :=
   ceil_add_natCast a n
 
+@[simp]
+theorem ceil_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
+    ⌈ofNat(n) + a⌉ = ofNat(n) + ⌈a⌉ :=
+  ceil_natCast_add n a
+
 @[simp]
 theorem ceil_sub_intCast (a : R) (z : ℤ) : ⌈a - z⌉ = ⌈a⌉ - z :=
   Eq.trans (by rw [Int.cast_neg, sub_eq_add_neg]) (ceil_add_intCast _ _)
diff --git a/Mathlib/Algebra/Order/Round.lean b/Mathlib/Algebra/Order/Round.lean
--- a/Mathlib/Algebra/Order/Round.lean
+++ b/Mathlib/Algebra/Order/Round.lean
@@ -6,7 +6,7 @@ Authors: Mario Carneiro, Kevin Kappelmann
 module
 
 public import Mathlib.Algebra.Order.Floor.Ring
-public import Mathlib.Algebra.Order.Interval.Set.Group
+import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Rounding
@@ -45,6 +45,26 @@ variable [Ring α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 def round (x : α) : ℤ :=
   if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
 
+/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.
+
+TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
+theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
+  rw [← floor_add_fract x, round, fract_intCast_add, fract_fract, floor_intCast_add, mul_add,
+    ← Int.cast_ofNat, ← Int.cast_mul, floor_intCast_add, ceil_intCast_add, add_assoc,
+    Int.mul_add_ediv_left _ _ two_ne_zero, Int.cast_ofNat]
+  split_ifs with h <;> congr 1
+  · rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr]
+    · simp
+    · simp [h]
+    · suffices fract x < 1 by simpa
+      refine lt_of_le_of_lt ?_ h
+      apply le_mul_of_one_le_left <;> simp
+  · have H : ⌊2 * fract x⌋ = 1 := by simpa [floor_eq_iff, ← two_mul, fract_lt_one] using h
+    suffices 0 < fract x by simp [this, H, ceil_eq_iff, (fract_lt_one _).le]
+    contrapose! h
+    grw [h]
+    simp
+
 @[simp]
 theorem round_zero : round (0 : α) = 0 := by simp [round]
 
@@ -61,6 +81,17 @@ theorem round_ofNat (n : ℕ) [n.AtLeastTwo] : round (ofNat(n) : α) = ofNat(n)
 @[simp]
 theorem round_intCast (n : ℤ) : round (n : α) = n := by simp [round]
 
+/-- Away from the points with fractional part `1 / 2`, `round x = ⌈2 * x⌉ / 2`. -/
+theorem round_eq_half_ceil_two_mul {x : α} (hx : 2 * fract x ≠ 1) : round x = ⌈2 * x⌉ / 2 := by
+  rcases em (2 * x ∈ range Int.cast) with ⟨m, hm⟩ | hx'
+  · rw [← hm, ceil_intCast]
+    rcases m.even_or_odd with ⟨m, rfl⟩ | ⟨m, rfl⟩
+    · obtain rfl : m = x := mul_left_cancel₀ two_ne_zero <| by simp [← hm, ← two_mul]
+      rw [round_intCast, ← two_mul, Int.mul_ediv_cancel_left _ two_ne_zero]
+    · refine absurd ?_ hx
+      exact two_mul_fract_eq_one_iff_exists_int.mpr ⟨m, mod_cast hm.symm⟩
+  · rw [round_eq', (ceil_eq_floor_add_one_iff_notMem _).mpr hx']
+
 @[simp]
 theorem round_add_intCast (x : α) (y : ℤ) : round (x + y) = round x + y := by
   rw [round, round, Int.fract_add_intCast, Int.floor_add_intCast, Int.ceil_add_intCast,
@@ -140,38 +171,21 @@ section LinearOrderedField
 variable [Field α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 
 theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
-  simp_rw [round, (by simp only [lt_div_iff₀', two_pos] : 2 * fract x < 1 ↔ fract x < 1 / 2)]
-  rcases lt_or_ge (fract x) (1 / 2) with hx | hx
-  · conv_rhs => rw [← fract_add_floor x, add_assoc, add_left_comm, fl
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 8 sites, 64 facet items (window 2/3: sites 9-16 of 23)

### Site 1: `Mathlib/Algebra/Order/ToIntervalMod.lean` lines 10-16
```
public import Mathlib.Algebra.Ring.Periodic
 public import Mathlib.Data.Int.SuccPred
 public import Mathlib.Order.Circular
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Reducing to an interval modulo its length
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Analysis/CStarAlgebra/ApproximateUnit.lean` lines 9-15
```
public import Mathlib.Analysis.CStarAlgebra.SpecialFunctions.PosPart
 public import Mathlib.Analysis.SpecialFunctions.ContinuousFunctionalCalculus.Rpow.Basic
 public import Mathlib.Topology.ApproximateUnit
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-! # Nonnegative contractions in a C⋆-algebra form an approximate unit
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Analysis/SpecialFunctions/Complex/Arctan.lean` lines 6-12
```
module
 
 public import Mathlib.Analysis.SpecialFunctions.Complex.LogBounds
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Complex arctangent
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean` lines 9-15
```
public import Mathlib.Analysis.SpecialFunctions.Pow.Real
 public import Mathlib.Algebra.Order.ToIntervalMod
 public import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Akra-Bazzi theorem: the polynomial growth condition
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/GroupTheory/Archimedean.lean` lines 7-13
```
public import Mathlib.Algebra.Group.Subgroup.Order
 public import Mathlib.Algebra.Order.Archimedean.Basic
import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Archimedean groups
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/MeasureTheory/Integral/IntervalIntegral/Basic.lean` lines 8-14
```
public import Mathlib.MeasureTheory.Integral.Bochner.ContinuousLinearMap
 public import Mathlib.MeasureTheory.Measure.Lebesgue.Basic
 public import Mathlib.MeasureTheory.Topology
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Integral over an interval
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/MeasureTheory/Integral/IntervalIntegral/DerivIntegrable.lean` lines 8-14
```
public import Mathlib.Analysis.BoundedVariation
 public import Mathlib.MeasureTheory.Function.AbsolutelyContinuous
 public import Mathlib.MeasureTheory.Integral.IntervalIntegral.Slope
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # `f'` is interval integrable for certain classes of functions `f`
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 8: `Mathlib/NumberTheory/Transcendental/Liouville/Basic.lean` lines 10-16
```
public import Mathlib.Analysis.Calculus.Deriv.Polynomial
 public import Mathlib.NumberTheory.Real.Irrational
 public import Mathlib.Topology.Algebra.Polynomial
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
```
- Item 57 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 58 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 59 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 60 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 61 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 62 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 63 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 64 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?



==========================================================================================
## PR 33421 — window 3/3 — prompt 20,823 chars
==========================================================================================

## PR #33421 — chore(Algebra/Order/Floor): review API about `round`

## Description

(no description provided)

## Diff under review (against the merge base; line numbers refer to the reviewed state)

```diff
diff --git a/Mathlib/Algebra/AddConstMap/Basic.lean b/Mathlib/Algebra/AddConstMap/Basic.lean
--- a/Mathlib/Algebra/AddConstMap/Basic.lean
+++ b/Mathlib/Algebra/AddConstMap/Basic.lean
@@ -9,6 +9,7 @@ public import Mathlib.Algebra.Group.Action.Pi
 public import Mathlib.Algebra.Group.End
 public import Mathlib.Algebra.Module.NatInt
 public import Mathlib.Algebra.Order.Archimedean.Basic
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Maps (semi)conjugating a shift to a shift
diff --git a/Mathlib/Algebra/Order/Archimedean/Basic.lean b/Mathlib/Algebra/Order/Archimedean/Basic.lean
--- a/Mathlib/Algebra/Order/Archimedean/Basic.lean
+++ b/Mathlib/Algebra/Order/Archimedean/Basic.lean
@@ -10,6 +10,7 @@ public import Mathlib.Algebra.Order.Monoid.Units
 public import Mathlib.Algebra.Order.Ring.Pow
 public import Mathlib.Data.Int.LeastGreatest
 public import Mathlib.Data.Rat.Floor
+import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # Archimedean groups and fields.
diff --git a/Mathlib/Algebra/Order/Floor/Ring.lean b/Mathlib/Algebra/Order/Floor/Ring.lean
--- a/Mathlib/Algebra/Order/Floor/Ring.lean
+++ b/Mathlib/Algebra/Order/Floor/Ring.lean
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
+
 end LinearOrderedRing
 
 section LinearOrderedCommRing
@@ -627,19 +636,36 @@ theorem ceil_ofNat (n : ℕ) [n.AtLeastTwo] : ⌈(ofNat(n) : R)⌉ = ofNat(n) :=
 theorem ceil_add_intCast (a : R) (z : ℤ) : ⌈a + z⌉ = ⌈a⌉ + z := by
   rw [← neg_inj, neg_add', ← floor_neg, ← floor_neg, neg_add', floor_sub_intCast]
 
+@[simp]
+theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈z + a⌉ = z + ⌈a⌉ := by
+  rw [add_comm, ceil_add_intCast, add_comm]
+
 @[simp]
 theorem ceil_add_natCast (a : R) (n : ℕ) : ⌈a + n⌉ = ⌈a⌉ + n := by
   rw [← Int.cast_natCast, ceil_add_intCast]
 
+@[simp]
+theorem ceil_natCast_add (n : ℕ) (a : R) : ⌈n + a⌉ = n + ⌈a⌉ :=
+  mod_cast ceil_intCast_add n a
+
 @[simp]
 theorem ceil_add_one (a : R) : ⌈a + 1⌉ = ⌈a⌉ + 1 := by
   rw [← ceil_add_intCast a (1 : ℤ), cast_one]
 
+@[simp]
+theorem ceil_one_add (a : R) : ⌈1 + a⌉ = 1 + ⌈a⌉ :=
+  mod_cast ceil_natCast_add 1 a
+
 @[simp]
 theorem ceil_add_ofNat (a : R) (n : ℕ) [n.AtLeastTwo] :
     ⌈a + ofNat(n)⌉ = ⌈a⌉ + ofNat(n) :=
   ceil_add_natCast a n
 
+@[simp]
+theorem ceil_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
+    ⌈ofNat(n) + a⌉ = ofNat(n) + ⌈a⌉ :=
+  ceil_natCast_add n a
+
 @[simp]
 theorem ceil_sub_intCast (a : R) (z : ℤ) : ⌈a - z⌉ = ⌈a⌉ - z :=
   Eq.trans (by rw [Int.cast_neg, sub_eq_add_neg]) (ceil_add_intCast _ _)
diff --git a/Mathlib/Algebra/Order/Round.lean b/Mathlib/Algebra/Order/Round.lean
--- a/Mathlib/Algebra/Order/Round.lean
+++ b/Mathlib/Algebra/Order/Round.lean
@@ -6,7 +6,7 @@ Authors: Mario Carneiro, Kevin Kappelmann
 module
 
 public import Mathlib.Algebra.Order.Floor.Ring
-public import Mathlib.Algebra.Order.Interval.Set.Group
+import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # Rounding
@@ -45,6 +45,26 @@ variable [Ring α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 def round (x : α) : ℤ :=
   if 2 * fract x < 1 then ⌊x⌋ else ⌈x⌉
 
+/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.
+
+TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
+theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
+  rw [← floor_add_fract x, round, fract_intCast_add, fract_fract, floor_intCast_add, mul_add,
+    ← Int.cast_ofNat, ← Int.cast_mul, floor_intCast_add, ceil_intCast_add, add_assoc,
+    Int.mul_add_ediv_left _ _ two_ne_zero, Int.cast_ofNat]
+  split_ifs with h <;> congr 1
+  · rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr]
+    · simp
+    · simp [h]
+    · suffices fract x < 1 by simpa
+      refine lt_of_le_of_lt ?_ h
+      apply le_mul_of_one_le_left <;> simp
+  · have H : ⌊2 * fract x⌋ = 1 := by simpa [floor_eq_iff, ← two_mul, fract_lt_one] using h
+    suffices 0 < fract x by simp [this, H, ceil_eq_iff, (fract_lt_one _).le]
+    contrapose! h
+    grw [h]
+    simp
+
 @[simp]
 theorem round_zero : round (0 : α) = 0 := by simp [round]
 
@@ -61,6 +81,17 @@ theorem round_ofNat (n : ℕ) [n.AtLeastTwo] : round (ofNat(n) : α) = ofNat(n)
 @[simp]
 theorem round_intCast (n : ℤ) : round (n : α) = n := by simp [round]
 
+/-- Away from the points with fractional part `1 / 2`, `round x = ⌈2 * x⌉ / 2`. -/
+theorem round_eq_half_ceil_two_mul {x : α} (hx : 2 * fract x ≠ 1) : round x = ⌈2 * x⌉ / 2 := by
+  rcases em (2 * x ∈ range Int.cast) with ⟨m, hm⟩ | hx'
+  · rw [← hm, ceil_intCast]
+    rcases m.even_or_odd with ⟨m, rfl⟩ | ⟨m, rfl⟩
+    · obtain rfl : m = x := mul_left_cancel₀ two_ne_zero <| by simp [← hm, ← two_mul]
+      rw [round_intCast, ← two_mul, Int.mul_ediv_cancel_left _ two_ne_zero]
+    · refine absurd ?_ hx
+      exact two_mul_fract_eq_one_iff_exists_int.mpr ⟨m, mod_cast hm.symm⟩
+  · rw [round_eq', (ceil_eq_floor_add_one_iff_notMem _).mpr hx']
+
 @[simp]
 theorem round_add_intCast (x : α) (y : ℤ) : round (x + y) = round x + y := by
   rw [round, round, Int.fract_add_intCast, Int.floor_add_intCast, Int.ceil_add_intCast,
@@ -140,38 +171,21 @@ section LinearOrderedField
 variable [Field α] [LinearOrder α] [IsStrictOrderedRing α] [FloorRing α]
 
 theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
-  simp_rw [round, (by simp only [lt_div_iff₀', two_pos] : 2 * fract x < 1 ↔ fract x < 1 / 2)]
-  rcases lt_or_ge (fract x) (1 / 2) with hx | hx
-  · conv_rhs => rw [← fract_add_floor x, add_assoc, add_left_comm, fl
```

## Workspace

- `target/` holds the full repository at the reviewed state (read-only). Changed files:
  (none listed)
- Available tools: read files, grep the repo (content_search), compile/verify Lean code (lean_verify), inspect goals, navigate declarations (hover/goto/references)

## Your task

For EVERY site in the CHECKLIST below, write the 2-4 most plausible maintainer asks (counterfactual
— no verdicts, no "looks fine"), each anchored at the site with `path` + `line_start`/`line_end`,
with `severity`, `claim` (the concrete ask, naming real declarations), `suggested_fix`,
`confidence` (0.0-1.0: P(a maintainer would leave this comment)), and — where you verified an edit
— `declaration_name` + `new_declaration` or `line_start`/`line_end` + `replacement`.
At most 24 findings total; spend them on the highest-probability asks across sites.
Then call `mcp__submit_findings` exactly once. `merge_ready_as_is`: your overall judgment.

You MUST finish by calling `mcp__submit_findings` exactly once — even if you find nothing. If there is nothing to change, call it with an empty `findings` list and `merge_ready_as_is: true`. A text-only reply does not count and fails the task.

---
## CHECKLIST — 7 sites, 56 facet items (window 3/3: sites 17-23 of 23)

### Site 1: `Mathlib/Order/Filter/AtTopBot/Archimedean.lean` lines 9-15
```
public import Mathlib.Order.Filter.AtTopBot.Group
 public import Mathlib.Order.Filter.CountablyGenerated
 public import Mathlib.Tactic.GCongr
import Mathlib.Algebra.Order.Group.Basic
 
 /-!
 # `Filter.atTop` filter and archimedean (semi)rings/fields
```
- Item 1 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 2 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 3 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 4 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 5 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 6 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 7 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 8 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 2: `Mathlib/Topology/Algebra/Order/Floor.lean` lines 6-12
```
module
 
 public import Mathlib.Algebra.Order.Floor.Ring
public import Mathlib.Algebra.Order.Round
 public import Mathlib.Order.Filter.AtTopBot.Floor
 public import Mathlib.Topology.Algebra.Order.Group
```
- Item 9 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 10 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 11 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 12 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 13 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 14 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 15 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 16 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 3: `Mathlib/Topology/Algebra/Order/Floor.lean` lines 59-66
```
end FloorSemiring
 
section Ring

 variable {α β γ : Type*} [Ring α] [LinearOrder α] [FloorRing α]
 
 section
```
- Item 17 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 18 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 19 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 20 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 21 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 22 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 23 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 24 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 4: `Mathlib/Topology/Algebra/Order/Floor.lean` lines 86-130
```
variable [TopologicalSpace α]
 
 theorem continuousOn_floor (n : ℤ) :
    ContinuousOn (fun x => floor x : α → ℤ) (Ico n (n + 1) : Set α) :=
  (continuousOn_congr <| floor_eq_on_Ico n).mpr continuousOn_const
 
theorem continuousOn_ceil (n : ℤ) :
    ContinuousOn (fun x => ceil x : α → ℤ) (Ioc (n - 1) n : Set α) :=
  (continuousOn_congr <| ceil_eq_on_Ioc n).mpr continuousOn_const
 
 section OrderClosedTopology
 
variable [OrderClosedTopology α]

@[fun_prop]
theorem continuousAt_floor {x : α} (hx : x ≠ ⌊x⌋) : ContinuousAt floor x :=
  (continuousOn_floor ⌊x⌋).continuousAt <|
    Ico_mem_nhds ((floor_le x).lt_of_ne hx.symm) (lt_floor_add_one x)

@[fun_prop]
theorem continuousOn_floor_compl_range : ContinuousOn (floor : α → ℤ) (range Int.cast)ᶜ := by
  intro x hx
  refine (continuousAt_floor ?_).continuousWithinAt
  simp_all [eq_comm]
 
 theorem tendsto_floor_right_pure_floor (x : α) : Tendsto (floor : α → ℤ) (𝓝[≥] x) (pure ⌊x⌋) :=
   tendsto_pure.2 <| mem_of_superset (Ico_mem_nhdsGE <| lt_floor_add_one x) fun _y hy =>
     floor_eq_on_Ico _ _ ⟨(floor_le x).trans hy.1, hy.2⟩
 
variable [IsStrictOrderedRing α]

theorem continuousAt_ceil {x : α} (hx : x ≠ ⌊x⌋) : ContinuousAt ceil x :=
  (continuousOn_ceil ⌈x⌉).continuousAt <|
    Ioc_mem_nhds (sub_lt_iff_lt_add.mpr <| ceil_lt_add_one _) <| (le_ceil x).lt_of_ne fun h ↦
      hx <| by rw [h, floor_intCast]

@[fun_prop]
theorem continuousOn_ceil_compl_range : ContinuousOn (ceil : α → ℤ) (range Int.cast)ᶜ := by
  intro x hx
  refine (c
```
- Item 25 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 26 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 27 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 28 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 29 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 30 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 31 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 32 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 5: `Mathlib/Topology/Algebra/Order/Floor.lean` lines 195-239
```
theorem continuousOn_fract [IsTopologicalAddGroup α] (n : ℤ) :
     ContinuousOn (fract : α → α) (Ico n (n + 1) : Set α) :=
  continuousOn_id.sub (continuous_of_discreteTopology.comp_continuousOn (continuousOn_floor n))
 
 theorem continuousAt_fract [OrderClosedTopology α] [IsTopologicalAddGroup α]
     {x : α} (h : x ≠ ⌊x⌋) : ContinuousAt fract x :=
  continuousAt_id.sub <| continuous_of_discreteTopology.continuousAt.comp <|
    continuousAt_floor h

theorem tendsto_round_nhdsGE_pure [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]
    (x : α) : Tendsto round (𝓝[≥] x) (pure (round x)) := by
  rw [funext round_eq']
  have : Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_le_add ha ha
  exact (tendsto_pure_pure (fun n ↦ (n + 1) / 2) _).comp <|
    (tendsto_floor_right_pure_floor (2 * x)).comp this

theorem tendsto_round_nhdsLT_pure_half_ceil [IsStrictOrderedRing α] [OrderClosedTopology α]
    [ContinuousAdd α] (x : α) : Tendsto round (𝓝[<] x) (pure (⌈2 * x⌉ / 2)) := by
  rw [funext round_eq', tendsto_pure]
  have : Tendsto (2 * ·) (𝓝[<] x) (𝓝[<] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_lt_add ha ha
  filter_upwards [tendsto_pure.mp ((tendsto_floor_left_pure_ceil_sub_one (2 * x)).comp this)]
    using by simp +contextual

theorem continuou
```
- Item 33 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 34 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 35 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 36 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 37 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 38 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 39 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 40 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 6: `Mathlib/Topology/Algebra/Order/Floor.lean` lines 292-296
```
Continuous (f ∘ fract) :=
   ContinuousOn.comp_fract (h.comp continuousOn_snd fun _x hx => (mem_prod.mp hx).2) continuous_id
     fun _ => hf

end Ring
```
- Item 41 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 42 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 43 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 44 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 45 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 46 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 47 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 48 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?

### Site 7: `Mathlib/Topology/Instances/AddCircle/Defs.lean` lines 13-19
```
public import Mathlib.Topology.Algebra.Order.Field
 public import Mathlib.Topology.OpenPartialHomeomorph.Constructions
 public import Mathlib.Topology.Order.T5
import Mathlib.Algebra.Order.Interval.Set.Group
 
 /-!
 # The additive circle
```
- Item 49 | **proof-golf**: Is any proof here longer or more manual than the canonical tactic/lemma allows?
- Item 50 | **generalization**: Should any statement be stated more generally (weaker hypotheses, more general typeclass, arbitrary constant instead of a fixed one)?
- Item 51 | **duplication**: Does anything here restate or specialize material that already exists in Mathlib (or elsewhere in this PR)?
- Item 52 | **naming**: Does every new/renamed declaration follow the naming convention and match its siblings (dot-notation, prefixes, suffixes like _iff, capitalization)?
- Item 53 | **docs**: Is any docstring missing, stale, imprecise, or in the wrong form (capitalization, references to renamed declarations, module-doc conventions)?
- Item 54 | **style**: Any formatting/structure issue maintainers flag: line breaks, calc layout, binder style, attribute placement, explicit vs implicit arguments, redundant qualifiers?
- Item 55 | **scope**: Is anything in the wrong place (file, namespace, section), unnecessary for this PR, or better split out / made private-or-public differently?
- Item 56 | **correctness**: Does the PR violate a Mathlib policy (new axioms, sorry, disallowed imports) or contain a semantic error a maintainer would block on?
