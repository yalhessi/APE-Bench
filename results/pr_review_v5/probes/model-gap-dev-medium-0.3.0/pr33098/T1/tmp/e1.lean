lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  refine .of_maximal_isSeparated ⟨⟨maximalSeparatedSet_subset, isSeparated_maximalSeparatedSet⟩,
    fun N ⟨hNA, hN⟩ hMN ↦ ?_⟩
  have h_fin : (maximalSeparatedSet ε A).Finite := by
    rw [← encard_ne_top_iff, card_maximalSeparatedSet h]
    exact h
  exact (h_fin.eq_of_subset_of_encard_le hMN (card_le_of_isSeparated hNA hN h)).ge
