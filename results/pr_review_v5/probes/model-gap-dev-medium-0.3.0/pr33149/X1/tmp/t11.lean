def smoothInTime (f : ℝ → ℝ) : Prop :=
  ContDiff ℝ (⊤ : ℕ∞) f
