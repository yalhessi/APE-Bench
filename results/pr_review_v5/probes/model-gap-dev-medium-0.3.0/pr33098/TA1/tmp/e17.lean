lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    (maximalSeparatedSet ε A).encard = packingNumber ε A := by
  simpa [maximalSeparatedSet, h] using (exists_set_encard_eq_packingNumber h).choose_spec.2.2.2
