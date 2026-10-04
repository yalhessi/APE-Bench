theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    upperBounds (f '' S) = upperBounds (range f) :=
  (upperBounds_closure (f '' S) ▸
    upperBounds_mono_set (hf.range_subset_closure_image_dense hS)).antisymm <|
    upperBounds_mono_set (image_subset_range f S)

theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    lowerBounds (f '' S) = lowerBounds (range f) :=
  hS.upperBounds_image (α := αᵒᵈ) hf

theorem Dense.ciSup_eq_ciSup_subtype {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s := by
  cases isEmpty_or_nonempty γ
  · simp [iSup_of_empty']
  exact (isLUB_ciSup h).unique <| (isLUB_congr (hS.upperBounds_image hf)).mp <|
    isLUB_ciSup_set (h.mono (image_subset_range f S)) hS.nonempty

theorem Dense.ciInf_eq_ciInf_subtype {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup_eq_ciSup_subtype (α := αᵒᵈ) hf h

theorem Dense.ciSup_eq_ciSup_subtype' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨆ i, f i = ⨆ s : S, f s := by
  by_cases h : BddAbove (range f)
  · exact hS.ciSup_eq_ciSup_subtype hf h
  have h' : ¬BddAbove (range fun s : S ↦ f s) := by
    rwa [← image_eq_range, BddAbove, hS.upperBounds_image hf]
  rw [ciSup_of_not_bddAbove h, ciSup_of_not_bddAbove h']

theorem Dense.ciInf_eq_ciInf_subtype' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup_eq_ciSup_subtype' (α := αᵒᵈ) hf
