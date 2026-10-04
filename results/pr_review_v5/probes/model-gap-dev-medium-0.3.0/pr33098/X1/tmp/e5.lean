section MinimalCover

lemma exists_set_encard_eq_coveringNumber (ε : ℝ≥0) (A : Set X) :
    ∃ C ⊆ A, IsCover ε A C ∧ C.encard = coveringNumber ε A := by
  have : Nonempty {s : Set X // s ⊆ A ∧ IsCover ε A s} := ⟨⟨A, subset_rfl, .rfl⟩⟩
  obtain ⟨C, hC⟩ :=
    ENat.exists_eq_iInf fun C : {s : Set X // s ⊆ A ∧ IsCover ε A s} ↦ (C : Set X).encard
  refine ⟨C, C.2.1, C.2.2, ?_⟩
  rw [hC, coveringNumber]
  simp_rw [iInf_subtype, iInf_and]

/-- An internal `ε`-cover of a set `A` by closed balls with minimal cardinality. -/
noncomputable
def minimalCover (ε : ℝ≥0) (A : Set X) : Set X :=
  (exists_set_encard_eq_coveringNumber ε A).choose

lemma minimalCover_subset : minimalCover ε A ⊆ A :=
  (exists_set_encard_eq_coveringNumber ε A).choose_spec.1

lemma isCover_minimalCover : IsCover ε A (minimalCover ε A) :=
  (exists_set_encard_eq_coveringNumber ε A).choose_spec.2.1

lemma card_minimalCover : (minimalCover ε A).encard = coveringNumber ε A :=
  (exists_set_encard_eq_coveringNumber ε A).choose_spec.2.2

lemma finite_minimalCover (h : coveringNumber ε A ≠ ⊤) : (minimalCover ε A).Finite :=
  encard_ne_top_iff.mp (card_minimalCover.trans_ne h)

end MinimalCover
