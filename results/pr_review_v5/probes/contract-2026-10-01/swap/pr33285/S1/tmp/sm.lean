def submoduleMap (e : M ≃SL[σ₁₂] M₂) (p : Submodule R M) :
    p ≃SL[σ₁₂] Submodule.map e p where
  __ := LinearEquiv.submoduleMap e.toLinearEquiv p
  continuous_toFun := map_continuous ((e.toContinuousLinearMap.comp p.subtypeL).codRestrict _ _)
  continuous_invFun := (map_continuous e.symm).restrict fun x hx ↦
    ((LinearEquiv.submoduleMap e.toLinearEquiv p).symm ⟨x, hx⟩).2
