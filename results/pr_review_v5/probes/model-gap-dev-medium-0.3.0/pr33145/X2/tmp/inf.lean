theorem Dense.continuous_inf {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLattice α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) (h : BddBelow (range f)) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.continuous_sup (α := αᵒᵈ) hf h
