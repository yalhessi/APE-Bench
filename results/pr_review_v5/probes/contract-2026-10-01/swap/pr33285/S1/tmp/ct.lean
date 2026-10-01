theorem cotangentEquivIdeal_symm_apply (x : R) (hx : x ∈ I) :
    I.cotangentEquivIdeal.symm ⟨(I ^ 2).mkQ x, Submodule.mem_map_of_mem hx⟩ =
      I.toCotangent ⟨x, hx⟩ := by
  rw [I.cotangentEquivIdeal.symm_apply_eq]
  rfl
