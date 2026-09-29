import json
nd = '''theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂) :
    comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=
  fun _ h ↦ add_mem h.1 h.2'''
print(json.dumps({"path": "Mathlib/Algebra/Module/Submodule/Map.lean", "declaration_name": "Submodule.inf_comap_le_comap_add", "new_declaration": nd}))
