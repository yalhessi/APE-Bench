import json,sys
v = sys.argv[1]
bodies = {
 "a": "arctan_eq_of_tan_eq (by rw [tan_pi_div_six, one_div]) <| by constructor <;> linarith [pi_pos]",
 "b": "arctan_eq_of_tan_eq (tan_pi_div_six.trans (one_div _)) <| by constructor <;> linarith [pi_pos]",
 "c": "arctan_eq_of_tan_eq (by simp) <| by constructor <;> linarith [pi_pos]",
}
print(json.dumps({"path":"Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean","declaration_name":"Real.arctan_inv_sqrt_three","new_declaration":"@[simp]\ntheorem arctan_inv_sqrt_three : arctan (√3)⁻¹ = π / 6 :=\n  " + bodies[v]}))
