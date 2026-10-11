theorem Dense.continuous_sup' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨆ i, f i = ⨆ s : S, f s := by
  rw [← sSup_range, ← sSup_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [range_eq_empty]
  by_cases h1 : BddAbove (range f)
  · refine (isLUB_csSup (range_nonempty f) h1).unique ?_
    exact (isLUB_congr (hS.continuous_upperBounds hf)).mp
      (isLUB_ciSup_set (h1.mono (image_subset_range f S)) hS.nonempty)
  · have h2 : ¬ BddAbove (f '' S) := by
      intro h
      have h3 : range f ⊆ closure (f '' S) := by
        simpa [hS.closure_eq] using image_closure_subset_closure_image (s := S) hf
      exact h1 (h.closure.mono h3)
    simp [csSup_of_not_bddAbove h1, ← image_eq_range, csSup_of_not_bddAbove h2]
