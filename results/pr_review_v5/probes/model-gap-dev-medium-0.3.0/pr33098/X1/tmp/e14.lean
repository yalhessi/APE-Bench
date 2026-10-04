lemma isSeparated_maximalSeparatedSet : IsSeparated ε (maximalSeparatedSet ε A) := by
  unfold maximalSeparatedSet
  split_ifs with h
  exacts [(exists_set_encard_eq_packingNumber h).choose_spec.2.2.1, .empty]
