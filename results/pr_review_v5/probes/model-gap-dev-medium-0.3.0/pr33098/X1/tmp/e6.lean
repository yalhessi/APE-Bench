lemma exists_set_encard_eq_packingNumber (h : packingNumber ε A ≠ ⊤) :
    ∃ C, C ⊆ A ∧ C.Finite ∧ IsSeparated ε C ∧ C.encard = packingNumber ε A := by
  have : Nonempty {s : Set X // s ⊆ A ∧ IsSeparated ε s} := ⟨⟨∅, empty_subset _, .empty⟩⟩
  have hsup : packingNumber ε A =
      ⨆ C : {s : Set X // s ⊆ A ∧ IsSeparated ε s}, (C : Set X).encard := by
    simp_rw [packingNumber, iSup_subtype, iSup_and]
  obtain ⟨C, hC⟩ := ENat.exists_eq_iSup_of_lt_top (hsup ▸ h.lt_top)
  rw [← hsup] at hC
  exact ⟨C, C.2.1, encard_ne_top_iff.mp (hC ▸ h), C.2.2, hC⟩
