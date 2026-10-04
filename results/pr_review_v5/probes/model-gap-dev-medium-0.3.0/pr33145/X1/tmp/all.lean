theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    upperBounds (f '' S) = upperBounds (range f) :=
  (upperBounds_closure (f '' S) ▸
    upperBounds_mono_set (hf.range_subset_closure_image_dense hS)).antisymm <|
    upperBounds_mono_set (image_subset_range f S)

theorem Dense.continuous_lowerBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    lowerBounds (f '' S) = lowerBounds (range f) :=
  hS.continuous_upperBounds (α := αᵒᵈ) hf

theorem Dense.continuous_sup {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s := by
  cases isEmpty_or_nonempty γ
  · simp [iSup_of_empty']
  exact (isLUB_ciSup h).unique <| (isLUB_congr (hS.continuous_upperBounds hf)).mp <|
    isLUB_ciSup_set (h.mono (image_subset_range f S)) hS.nonempty

theorem Dense.continuous_inf {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.continuous_sup (α := αᵒᵈ) hf h

theorem Dense.continuous_sup' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨆ i, f i = ⨆ s : S, f s := by
  by_cases h : BddAbove (range f)
  · exact hS.continuous_sup hf h
  have h' : ¬BddAbove (range fun s : S ↦ f s) := by
    rwa [← image_eq_range, BddAbove, hS.continuous_upperBounds hf]
  rw [ciSup_of_not_bddAbove h, ciSup_of_not_bddAbove h']

theorem Dense.continuous_inf' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.continuous_sup' (α := αᵒᵈ) hf
