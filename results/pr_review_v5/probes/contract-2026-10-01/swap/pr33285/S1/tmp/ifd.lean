def implicitFunctionData (h : IsContDiffImplicitAt n f f' a) :
    ImplicitFunctionData 𝕜 (E × F) E G where
  leftFun := Prod.fst
  leftDeriv := ContinuousLinearMap.fst 𝕜 E F
  rightFun := f
  rightDeriv := f'
  pt := a
  hasStrictFDerivAt_leftFun := by fun_prop
  hasStrictFDerivAt_rightFun := h.contDiffAt.hasStrictFDerivAt' h.hasFDerivAt h.ne_zero
  range_leftDeriv := LinearMap.range_eq_top_of_surjective _ fun x ↦ ⟨(x, 0), rfl⟩
  range_rightDeriv := by
    apply top_unique
    rw [← LinearMap.range_eq_top_of_surjective _ h.bijective.surjective]
    exact LinearMap.range_comp_le_range _ _
  isCompl_ker := by
    apply IsCompl.of_eq
    · ext ⟨x, y⟩
      rw [Submodule.mem_inf, Submodule.mem_bot, LinearMap.mem_ker, ContinuousLinearMap.coe_fst',
        LinearMap.mem_ker, Prod.ext_iff, ← h.bijective.injective.eq_iff]
      simp +contextual
    · ext x
      simp only [Submodule.mem_sup, Submodule.mem_top, iff_true]
      obtain ⟨y, hy⟩ := h.bijective.surjective (f' x)
      exact ⟨(0, y), by simp, x - (0, y), by simp [map_sub, ← hy], by abel⟩
