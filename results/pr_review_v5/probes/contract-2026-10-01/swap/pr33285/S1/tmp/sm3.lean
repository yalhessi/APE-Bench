def submoduleMap (e : M ≃SL[σ₁₂] M₂) (p : Submodule R M) :
    p ≃SL[σ₁₂] Submodule.map e p where
  __ := LinearEquiv.submoduleMap e.toLinearEquiv p
  continuous_toFun := by dsimp [LinearEquiv.submoduleMap]; fun_prop
  continuous_invFun := by dsimp [LinearEquiv.submoduleMap]; fun_prop
