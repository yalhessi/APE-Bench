lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  intro x hxA
  by_contra! h_dist
  have hx_not_mem : x ∉ maximalSeparatedSet ε A := by
    intro hx_mem
    specialize h_dist x hx_mem
    simp at h_dist
  let C := {x} ∪ maximalSeparatedSet ε A
  have hC_subset : C ⊆ A := by
    simp [C, hxA, maximalSeparatedSet_subset, insert_subset]
  have hC_separated : IsSeparated ε C := by
    intro a ha b hb hab
    by_cases hax : a = x
    · subst hax
      have hb' : b ∈ maximalSeparatedSet ε A := by simpa [C, hab.symm] using hb
      simpa using h_dist b hb'
    by_cases hbx : b = x
    · subst hbx
      have ha' : a ∈ maximalSeparatedSet ε A := by simpa [C, hab] using ha
      have h := h_dist a ha'
      simp only [mem_setOf_eq, not_le] at h
      rwa [edist_comm] at h
    simp only [singleton_union, mem_insert_iff, hax, false_or, hbx, C] at ha hb
    exact isSeparated_maximalSeparatedSet ha hb hab
  refine absurd (card_le_of_isSeparated hC_subset hC_separated h) ?_
  simp only [singleton_union, not_le, C]
  rw [encard_insert_of_notMem hx_not_mem, ENat.lt_add_one_iff]
  rwa [card_maximalSeparatedSet h]
