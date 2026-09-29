theorem Dense.continuous_inf' {α : Type*} [TopologicalSpace α]
    [ConditionallyCompleteLinearOrder α] [ClosedIciTopology α] {f : γ → α} [TopologicalSpace γ]
    {S : Set γ} (hS : Dense S) (hf : Continuous f) :
    ⨅ i, f i = ⨅ s : S, f s :=
  hS.continuous_sup' (α := αᵒᵈ) hf
