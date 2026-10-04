theorem Dense.continuous_lowerBounds {α : Type*} [TopologicalSpace α] [Preorder α]
    [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ] {S : Set γ} (hS : Dense S)
    (hf : Continuous f) :
    lowerBounds (f '' S) = lowerBounds (range f) :=
  hS.continuous_upperBounds (α := αᵒᵈ) hf
