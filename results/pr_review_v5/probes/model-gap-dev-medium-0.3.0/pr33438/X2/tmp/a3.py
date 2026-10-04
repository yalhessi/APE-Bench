import json,sys
print(json.dumps({"path":"Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean","declaration_name":"Real.arctan_inv_sqrt_three","new_declaration":"@[simp]\ntheorem arctan_inv_sqrt_three : arctan (√3)⁻¹ = π / 6 := by\n  rw [arctan_inv_of_pos (by positivity), arctan_sqrt_three]\n  ring"}))
