lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  refine .of_maximal_isSeparated ⟨⟨maximalSeparatedSet_subset, isSeparated_maximalSeparatedSet⟩,
    fun N hN hle ↦ ?_⟩
  have hfin : (maximalSeparatedSet ε A).Finite :=
    encard_ne_top_iff.mp ((card_maximalSeparatedSet h).trans_ne h)
  refine (hfin.eq_of_subset_of_encard_le hle ?_).ge
  exact (hN.2.encard_le_packingNumber hN.1).trans_eq (card_maximalSeparatedSet h).symm
