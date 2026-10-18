lemma exists_set_encard_eq_coveringNumber (h : coveringNumber ε A ≠ ⊤) :
    ∃ C ⊆ A, C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A := by
  have : Nonempty {s : Set X // s ⊆ A ∧ IsCover ε A s} := ⟨⟨A, subset_rfl, .rfl⟩⟩
  obtain ⟨C, hC⟩ :=
    ENat.exists_eq_iInf (fun C : {s : Set X // s ⊆ A ∧ IsCover ε A s} ↦ (C : Set X).encard)
  have hC' : (C : Set X).encard = coveringNumber ε A := by
    rw [hC]
    simp_rw [iInf_subtype, iInf_and]
    rfl
  exact ⟨C, C.2.1, encard_ne_top_iff.mp (hC' ▸ h), C.2.2, hC'⟩
