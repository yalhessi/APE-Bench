lemma card_le_of_isSeparated (h_subset : C ⊆ A) (h_sep : IsSeparated ε C)
    (h : packingNumber ε A ≠ ⊤) : C.encard ≤ (maximalSeparatedSet ε A).encard :=
  (h_sep.encard_le_packingNumber h_subset).trans_eq (card_maximalSeparatedSet h).symm
