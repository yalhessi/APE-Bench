
theorem DenseRange.upperBounds_range_comp {α β : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] [TopologicalSpace γ] {f : γ → α} {g : β → γ} (hg : DenseRange g)
    (hf : Continuous f) :
    upperBounds (range (f ∘ g)) = upperBounds (range f) := by
  rw [range_comp]
  exact Dense.continuous_upperBounds hg hf

theorem DenseRange.ciSup_comp {α β : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] [TopologicalSpace γ] {f : γ → α}
    {g : β → γ} (hg : DenseRange g) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ b, f (g b) = ⨆ i, f i := by
  cases isEmpty_or_nonempty γ
  · have : IsEmpty β := ⟨fun b ↦ isEmptyElim (g b)⟩
    simp [iSup_of_empty']
  have : Nonempty β := hg.nonempty
  exact (isLUB_ciSup (h.mono (range_comp_subset_range g f))).unique <|
    (isLUB_congr (hg.upperBounds_range_comp hf)).mpr (isLUB_ciSup h)

example {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddAbove (range f)) :
    ⨆ i, f i = ⨆ s : S, f s :=
  (hS.denseRange_val.ciSup_comp hf h).symm

