lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  by_cases h : packingNumber ε A = ⊤
  · simp [maximalSeparatedSet, h]
  simpa [maximalSeparatedSet, h] using (exists_set_encard_eq_packingNumber h).choose_spec.1
