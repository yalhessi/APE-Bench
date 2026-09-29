lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  unfold maximalSeparatedSet
  split_ifs with h
  exacts [(exists_set_encard_eq_packingNumber h).choose_spec.1, empty_subset _]
