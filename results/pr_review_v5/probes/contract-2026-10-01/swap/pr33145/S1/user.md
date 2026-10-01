# Pull request #33145

**Title:** feat: supremum of a continuous function on a dense set is equal to the supremum on the univ

**Description:**
This PR adds the following theorems:

1. `Dense.continuous_upperBounds` : If `α` is a preordered set with ClosedIicTopology, `f : γ → α` is a continuous functions, and `S` is a dense subset of `γ`. Then the upper bounds of `f '' S` is equal to the upper bounds of `range f`.
2. `Dense.continuous_sup` : If`α` is a conditionally complete lattice and `f` is bounded above, then `⨆ i, f i = ⨆ s : S, f s`.
3. `Dense.continuous_sup'`: If `α` is a conditionally complete linear order, then `⨆ i, f i = ⨆ s : S, f s`.

Some of the codes in this PR are created by @plp127 and @j-loreaux . See also the zulip discussion: [#Is there code for X? > Continuous function reaches its supremum on a dense set](https://leanprover.zulipchat.com/#narrow/channel/217875-Is-there-code-for-X.3F/topic/Continuous.20function.20reaches.20its.20supremum.20on.20a.20dense.20set/with/556965307).

**Changed files:**
  - `Mathlib/Topology/Order/IsLUB.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33145 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: supremum of a continuous function on a dense set is equal to the supremum on the univ
- description: This PR adds the following theorems:

1. `Dense.continuous_upperBounds` : If `α` is a preordered set with ClosedIicTopology, `f : γ → α` is a continuous functions, and `S` is a dense subset of `γ`. Then the upper bounds of `f '' S` is equal to the upper bounds of `range f`.
2. `Dense.continuous_sup` : If`α` is a conditionally complete lattice and `f` is bounded above, then `⨆ i, f i = ⨆ s : S, f s`.
3. `Dense.continuous_sup'`: If `α` is a conditionally complete linear order, then `⨆ i, f i = ⨆ s : S, f s`.

Some of the codes in this PR are created by @plp127 and @j-loreaux . See also the zulip discussion: [#Is there code for X? > Continuous function reaches its supremum on a dense set](https://leanprover.zulipchat.com/#narrow/channel/217875-Is-there-code-for-X.3F/topic/Continuous.20function.20reaches.20its.20supremum.20on.20a.20dense.20set/with/556965307).
- changed files: Mathlib/Topology/Order/IsLUB.lean

## Objects

### `Dense.continuous_sup'` (theorem, added) [026d50893c]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_sup' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨆ i, f i = ⨆ s : S, f s := by
  rw [← sSup_range, ← sSup_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [Set.range_eq_empty]
  by_cases h1 : BddAbove (range f)
  · refine (isLUB_csSup (range_nonempty f) h1).unique ?_
    refine (isLUB_congr (hS.continuous_upperBounds hf)).mp (isLUB_ciSup_set ?_ hS.nonempty)
    exact h1.mono (by grind)
  · have h2 : ¬ BddAbove (range (fun s : S => f (Subtype.val s))) := by
      intro h
      have := range_comp' f (Subtype.val : S → γ)
      simp_all only [Subtype.range_coe_subtype, setOf_mem_eq]
      have := h.closure.mono (image_closure_subset_closure_image hf)
      simp only [hS.closure_eq, image_univ] at this
      exact h1 this
    simp [csSup_of_not_bddAbove h1, csSup_of_not_bddAbove h2]
```

### `command in IsLUB.lean` (command, added) [0670c7587f]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The infimum of a bounded below, continuous function on a dense set is equal to the infimum on
the universe. -/
```

### `Dense.continuous_sup` (theorem, added) [0a93104e7b]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_sup {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s := by
  rw [← sSup_range, ← sSup_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [Set.range_eq_empty]
  refine (isLUB_csSup (range_nonempty f) h).unique ?_
  refine (isLUB_congr (hS.continuous_upperBounds hf)).mp (isLUB_ciSup_set ?_ hS.nonempty)
  exact h.mono (by grind)
```

### `command in IsLUB.lean` (command, added) [1b029851b6]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- This is an analogue of `Dense.continuous_inf` for functions taking values in a conditionally
complete linear order. The assumption of `BddBelow (range f)` is not needed in this theorem. -/
```

### `Dense.continuous_upperBounds` (theorem, added) [3181a0b2d7]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    upperBounds (f '' S) = upperBounds (range f) := by
  refine subset_antisymm ?_ fun _ => upperBounds_mono (Set.image_subset_range f S) le_rfl
  refine subset_trans ?_ fun _ => upperBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl
  intro x hx i hi
  rw [mem_closure_iff_frequently] at hi
  exact (hi.mono hx).mem_of_closed isClosed_Iic
```

### `Dense.continuous_lowerBounds` (theorem, added) [544299c815]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_lowerBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    lowerBounds (f '' S) = lowerBounds (range f) := by
  refine subset_antisymm ?_ fun _ => lowerBounds_mono (Set.image_subset_range f S) le_rfl
  refine subset_trans ?_ fun _ => lowerBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl
  intro x hx i hi
  rw [mem_closure_iff_frequently] at hi
  exact (hi.mono hx).mem_of_closed isClosed_Ici
```

### `Dense.continuous_inf` (theorem, added) [66216f7980]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_inf {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
    ⨅ i, f i = ⨅ s : S, f s := by
  rw [← sInf_range, ← sInf_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [Set.range_eq_empty]
  refine (isGLB_csInf (range_nonempty f) h).unique ?_
  refine (isGLB_congr (hS.continuous_lowerBounds hf)).mp (isGLB_ciInf_set ?_ hS.nonempty)
  exact h.mono (by grind)
```

### `command in IsLUB.lean` (command, added) [7833703a3d]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- This is an analogue of `Dense.continuous_sup` for functions taking values in a conditionally
complete linear order. The assumption of `BddAbove (range f)` is not needed in this theorem. -/
```

### `command in IsLUB.lean` (command, added) [8d23f90657]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The lower bounds of the image of a continuous function on a dense set is equal to the lower
bounds of the range of the universe. -/
```

### `Dense.continuous_inf'` (theorem, added) [d060e494ca]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem Dense.continuous_inf' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨅ i, f i = ⨅ s : S, f s := by
  rw [← sInf_range, ← sInf_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [Set.range_eq_empty]
  by_cases h1 : BddBelow (range f)
  · refine (isGLB_csInf (range_nonempty f) h1).unique ?_
    refine (isGLB_congr (hS.continuous_lowerBounds hf)).mp (isGLB_ciInf_set ?_ hS.nonempty)
    exact h1.mono (by grind)
  · have h2 : ¬ BddBelow (range (fun s : S => f (Subtype.val s))) := by
      intro h
      have := range_comp' f (Subtype.val : S → γ)
      simp_all only [Subtype.range_coe_subtype, setOf_mem_eq]
      have := h.closure.mono (image_closure_subset_closure_image hf)
      simp only [hS.closure_eq, image_univ] at this
      exact h1 this
    simp [csInf_of_not_bddBelow h1, csInf_of_not_bddBelow h2]
```

### `command in IsLUB.lean` (command, added) [f7388ef647]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The supremum of a bounded above, continuous function on a dense set is equal to the supremum on
the universe. -/
```

### `command in IsLUB.lean` (command, added) [fef41c862c]
- file: `Mathlib/Topology/Order/IsLUB.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The upper bounds of the image of a continuous function on a dense set is equal to the upper
bounds of the range of the universe. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `Dense.continuous_inf`, `Dense.continuous_inf'`, `Dense.continuous_lowerBounds`, `Dense.continuous_sup`, `Dense.continuous_sup'`, `Dense.continuous_upperBounds` -- 6 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `Dense.continuous_inf` -> `Dense.continuous_lowerBounds`
- direct_use_of_changed_declaration [exact]: `Dense.continuous_inf'` -> `Dense.continuous_lowerBounds`
- direct_use_of_changed_declaration [exact]: `Dense.continuous_sup` -> `Dense.continuous_upperBounds`
- direct_use_of_changed_declaration [exact]: `Dense.continuous_sup'` -> `Dense.continuous_upperBounds`

---

## The diff

```diff
diff --git a/Mathlib/Topology/Order/IsLUB.lean b/Mathlib/Topology/Order/IsLUB.lean
--- a/Mathlib/Topology/Order/IsLUB.lean
+++ b/Mathlib/Topology/Order/IsLUB.lean
@@ -166,6 +166,100 @@ theorem Dense.isGLB_inter_iff {α : Type*} [TopologicalSpace α] [Preorder α] [
     IsGLB (t ∩ s) x ↔ IsGLB t x :=
   hs.isLUB_inter_iff (α := αᵒᵈ) ht
 
+/-- The upper bounds of the image of a continuous function on a dense set is equal to the upper
+bounds of the range of the universe. -/
+theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
+    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
+    (hf : Continuous f) :
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
+    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
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
+    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
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
+    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
+    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
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
+    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
+    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
+    ⨆ i, f i = ⨆ s : S, f s := by
+  rw [← sSup_range, ← sSup_range]
+  obtain (_ | _) := isEmpty_or_nonempty γ
+  · simp [Set.range_eq_empty]
+  by_cases h1 : BddAbove (range f)
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
+
+/-- This is an analogue of `Dense.continuous_inf` for functions taking values in a conditionally
+complete linear order. The assumption of `BddBelow (range f)` is not needed in this theorem. -/
+theorem Dense.continuous_inf' {α : Type*} [TopologicalSpace α]
+    [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
+    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
+    ⨅ i, f i = ⨅ s : S, f s := by
+  rw [← sInf_range, ← sInf_range]
+  obtain (_ | _) := isEmpty_or_nonempty γ
+  · simp [Set.range_eq_empty]
+  by_cases h1 : BddBelow (range f)
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
+
 /-- A closed interval in a conditionally complete linear order is compact.
 Also see general API on `CompactIccSpace`. -/
 protected lemma ConditionallyCompleteLinearOrder.isCompact_Icc {α : Type*}

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.