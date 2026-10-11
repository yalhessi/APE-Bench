/-- The covering number of a set `A` for radius `ε` is at most its packing number for radius `ε`.

[R. Vershynin, *High Dimensional Probability*][vershynin2018high], 4.2.8. -/
theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber ε A ≤ packingNumber ε A := by
  obtain h_top | h_top := eq_or_ne (packingNumber ε A) ⊤
  · simp [h_top]
  rw [← card_maximalSeparatedSet h_top]
  exact (isCover_maximalSeparatedSet h_top).coveringNumber_le_encard maximalSeparatedSet_subset
