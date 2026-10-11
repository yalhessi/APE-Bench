lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    (maximalSeparatedSet ε A).encard = packingNumber ε A := by
  simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
  exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.2

lemma IsSeparated.encard_le_encard_maximalSeparatedSet (h_subset : C ⊆ A)
    (h_sep : IsSeparated ε C) (h : packingNumber ε A ≠ ⊤) :
    C.encard ≤ (maximalSeparatedSet ε A).encard :=
  (h_sep.encard_le_packingNumber h_subset).trans_eq (encard_maximalSeparatedSet h).symm

/-- If the packing number is finite, the maximal separated set is a cover. -/
lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  refine .of_maximal_isSeparated ⟨⟨maximalSeparatedSet_subset, isSeparated_maximalSeparatedSet⟩,
    fun N ⟨hNA, hN⟩ hMN ↦ ?_⟩
  have h_fin : (maximalSeparatedSet ε A).Finite := by
    rw [← encard_ne_top_iff, encard_maximalSeparatedSet h]
    exact h
  exact (h_fin.eq_of_subset_of_encard_le hMN (hN.encard_le_encard_maximalSeparatedSet hNA h)).ge
