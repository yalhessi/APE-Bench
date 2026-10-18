/-- The covering number of a set `A` for radius `ε` is at most its packing number for radius `ε`,
since a maximal `ε`-separated subset of `A` is an `ε`-cover of `A`. -/
theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber ε A ≤ packingNumber ε A := by
  by_cases h_top : packingNumber ε A ≠ ⊤
  · rw [← card_maximalSeparatedSet h_top]
    refine (iInf_le _ (maximalSeparatedSet ε A)).trans (le_of_eq ?_)
    simp [maximalSeparatedSet_subset, iInf_pos, isCover_maximalSeparatedSet h_top]
  · simp only [ne_eq, Decidable.not_not] at h_top
    simp [h_top]
