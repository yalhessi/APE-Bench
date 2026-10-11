lemma exists_set_encard_eq_packingNumber (h : packingNumber ε A ≠ ⊤) :
    ∃ C, C ⊆ A ∧ C.Finite ∧ IsSeparated ε C ∧ C.encard = packingNumber ε A := by
  have : Nonempty {s : Set X // s ⊆ A ∧ IsSeparated ε s} := ⟨⟨∅, empty_subset A, .empty⟩⟩
  let h_exists := ENat.exists_eq_iSup_of_lt_top
    (f := fun C : { s : Set X // s ⊆ A ∧ IsSeparated ε s } ↦ (C : Set X).encard)
  simp_rw [packingNumber] at h ⊢
  simp_rw [iSup_subtype, iSup_and] at h_exists
  specialize h_exists h.lt_top
  obtain ⟨C, hC⟩ := h_exists
  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
  · refine encard_ne_top_iff.mp ?_
    rwa [hC]
  · rw [hC]
