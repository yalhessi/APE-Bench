theorem upperBounds_eq_of_subset_of_subset_closure {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {s t : Set α} (hst : s ⊆ t) (hts : t ⊆ closure s) :
    upperBounds s = upperBounds t :=
  (upperBounds_closure s ▸ upperBounds_mono_set hts).antisymm (upperBounds_mono_set hst)

namespace Dense

variable {α : Type*} [TopologicalSpace α] [TopologicalSpace γ] {f : γ → α} {S : Set γ}

/-- If `f` is continuous and `S` is dense, then `f '' S` has the same upper bounds as
`range f`. -/
theorem upperBounds_image [Preorder α] [ClosedIicTopology α] (hS : Dense S)
    (hf : Continuous f) : upperBounds (f '' S) = upperBounds (range f) :=
  upperBounds_eq_of_subset_of_subset_closure (image_subset_range f S)
    (hf.range_subset_closure_image_dense hS)

/-- If `f` is continuous and `S` is dense, then `f '' S` has the same lower bounds as
`range f`. -/
theorem lowerBounds_image [Preorder α] [ClosedIciTopology α] (hS : Dense S)
    (hf : Continuous f) : lowerBounds (f '' S) = lowerBounds (range f) :=
  hS.upperBounds_image (α := αᵒᵈ) hf

/-- If `f` is continuous and bounded above and `S` is dense, then the supremum of `f` over `S`
equals the supremum of `f`. -/
theorem ciSup_eq_ciSup_subtype_of_bddAbove [ConditionallyCompleteLattice α]
    [ClosedIicTopology α] (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s := by
  rw [← sSup_range, ← sSup_range]
  obtain (_ | _) := isEmpty_or_nonempty γ
  · simp [range_eq_empty]
  exact (isLUB_csSup (range_nonempty f) h).unique <| (isLUB_congr (hS.upperBounds_image hf)).mp <|
    isLUB_ciSup_set (h.mono (image_subset_range f S)) hS.nonempty

/-- If `f` is continuous and bounded below and `S` is dense, then the infimum of `f` over `S`
equals the infimum of `f`. -/
theorem ciInf_eq_ciInf_subtype_of_bddBelow [ConditionallyCompleteLattice α]
    [ClosedIciTopology α] (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup_eq_ciSup_subtype_of_bddAbove (α := αᵒᵈ) hf h

/-- In a conditionally complete linear order, the supremum of a continuous function `f` over a
dense set `S` equals the supremum of `f`; if `f` is not bounded above, both sides are `sSup ∅`. -/
theorem ciSup_eq_ciSup_subtype [ConditionallyCompleteLinearOrder α] [ClosedIicTopology α]
    (hS : Dense S) (hf : Continuous f) : ⨆ i, f i = ⨆ s : S, f s := by
  by_cases h : BddAbove (range f)
  · exact hS.ciSup_eq_ciSup_subtype_of_bddAbove hf h
  have h' : ¬BddAbove (f '' S) := by rwa [BddAbove, hS.upperBounds_image hf]
  rw [ciSup_of_not_bddAbove h, ciSup_of_not_bddAbove (by rwa [← image_eq_range])]

/-- In a conditionally complete linear order, the infimum of a continuous function `f` over a
dense set `S` equals the infimum of `f`; if `f` is not bounded below, both sides are `sInf ∅`. -/
theorem ciInf_eq_ciInf_subtype [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α]
    (hS : Dense S) (hf : Continuous f) : ⨅ i, f i = ⨅ s : S, f s :=
  hS.ciSup_eq_ciSup_subtype (α := αᵒᵈ) hf

end Dense
