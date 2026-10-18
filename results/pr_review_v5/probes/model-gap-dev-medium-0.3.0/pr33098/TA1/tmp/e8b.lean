lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  by_cases h : packingNumber ε A ≠ ⊤
  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_packingNumber h).choose_spec.1
  · simp [maximalSeparatedSet, h]
