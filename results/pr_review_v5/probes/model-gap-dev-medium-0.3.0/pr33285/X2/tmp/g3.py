import json,sys
nd = '''def submoduleMap (e : M ≃SL[σ₁₂] M₂) (p : Submodule R M) :
    p ≃SL[σ₁₂] Submodule.map e p where
  toLinearEquiv := e.toLinearEquiv.submoduleMap p
  continuous_toFun := (e.continuous.comp continuous_subtype_val).subtype_mk _
  continuous_invFun := (e.symm.continuous.comp continuous_subtype_val).subtype_mk _'''
print(json.dumps({"path": "Mathlib/Topology/Algebra/Module/Equiv.lean", "declaration_name": "ContinuousLinearEquiv.submoduleMap", "new_declaration": nd}))
