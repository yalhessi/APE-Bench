theorem Dense.continuous_sup' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨆ i, f i = ⨆ s : S, f s := by
  by_cases h : BddAbove (range f)
  · exact hS.continuous_sup hf h
  have h' : ¬BddAbove (f '' S) := by rwa [BddAbove, hS.continuous_upperBounds hf]
  rw [ciSup_of_not_bddAbove h, ciSup_of_not_bddAbove (by rwa [← image_eq_range])]
