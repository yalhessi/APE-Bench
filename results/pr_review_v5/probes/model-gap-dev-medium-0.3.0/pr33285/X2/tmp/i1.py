import json,sys
nd = '''@[simp]
theorem prodComm_symm : (prodComm R M M₂).symm = prodComm R M₂ M := rfl'''
print(json.dumps({"path": "Mathlib/LinearAlgebra/Prod.lean", "declaration_name": "LinearEquiv.symm_prodComm", "new_declaration": nd}))
