lemma IsSeparated.encard_le_encard_maximalSeparatedSet (h_sep : IsSeparated ε C)
    (h_subset : C ⊆ A) (h : packingNumber ε A ≠ ⊤) :
    C.encard ≤ (maximalSeparatedSet ε A).encard :=
  (h_sep.encard_le_packingNumber h_subset).trans_eq (card_maximalSeparatedSet h).symm

/-- The maximal separated set is a cover. -/
lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  refine .of_maximal_isSeparated ⟨⟨maximalSeparatedSet_subset, isSeparated_maximalSeparatedSet⟩,
    fun N hN hsub ↦ ?_⟩
  have hfin : (maximalSeparatedSet ε A).Finite :=
    encard_ne_top_iff.mp (by rwa [card_maximalSeparatedSet h])
  exact (hfin.eq_of_subset_of_encard_le hsub
    (hN.2.encard_le_encard_maximalSeparatedSet hN.1 h)).ge
