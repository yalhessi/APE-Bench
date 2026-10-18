
lemma finite_maximalSeparatedSet : (maximalSeparatedSet ε A).Finite := by
  by_cases h : packingNumber ε A ≠ ⊤
  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_packingNumber h).choose_spec.2.1
  · simp [maximalSeparatedSet, h]

