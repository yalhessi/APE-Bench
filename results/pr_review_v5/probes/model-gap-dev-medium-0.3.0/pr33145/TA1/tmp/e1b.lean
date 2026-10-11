theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    upperBounds (f '' S) = upperBounds (range f) :=
  subset_antisymm
    (upperBounds_closure (f '' S) ▸ upperBounds_mono_set (hf.range_subset_closure_image_dense hS))
    (upperBounds_mono_set (image_subset_range f S))
