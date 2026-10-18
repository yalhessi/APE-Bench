lemma finite_minimalCover : (minimalCover ε A).Finite := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.1
  · simp [minimalCover, h]
