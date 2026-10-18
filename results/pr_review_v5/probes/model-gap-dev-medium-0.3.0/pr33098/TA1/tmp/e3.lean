theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber ε A ≤ packingNumber ε A := by
  by_cases h_top : packingNumber ε A = ⊤
  · simp [h_top]
  rw [← card_maximalSeparatedSet h_top]
  exact (isCover_maximalSeparatedSet h_top).coveringNumber_le_encard maximalSeparatedSet_subset
