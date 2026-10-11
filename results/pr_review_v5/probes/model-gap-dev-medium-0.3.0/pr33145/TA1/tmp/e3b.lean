theorem Dense.continuous_sup {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s := by
  rw [← sSup_range, ← sSup_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [range_eq_empty]
  refine (isLUB_csSup (range_nonempty f) h).unique ?_
  exact (isLUB_congr (hS.continuous_upperBounds hf)).mp
    (isLUB_ciSup_set (h.mono (image_subset_range f S)) hS.nonempty)
