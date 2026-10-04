
lemma finite_maximalSeparatedSet : (maximalSeparatedSet ε A).Finite := by
  unfold maximalSeparatedSet
  split_ifs with h
  exacts [(exists_set_encard_eq_packingNumber h).choose_spec.2.1, finite_empty]

