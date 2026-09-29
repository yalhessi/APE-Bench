lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  refine .of_maximal_isSeparated ⟨⟨maximalSeparatedSet_subset, isSeparated_maximalSeparatedSet⟩,
    fun N hN hsub ↦ ?_⟩
  have hfin : (maximalSeparatedSet ε A).Finite :=
    encard_ne_top_iff.mp (by rwa [card_maximalSeparatedSet h])
  exact (hfin.eq_of_subset_of_encard_le hsub (card_le_of_isSeparated hN.1 hN.2 h)).ge
