theorem Dense.continuous_upperBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIicTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    upperBounds (f '' S) = upperBounds (range f) := by
  refine subset_antisymm (fun x hx ↦ ?_) fun _ ↦ upperBounds_mono (image_subset_range f S) le_rfl
  refine upperBounds_mono (hf.range_subset_closure_image_dense hS) le_rfl fun i hi ↦ ?_
  rw [mem_closure_iff_frequently] at hi
  exact (hi.mono hx).mem_of_closed isClosed_Iic
