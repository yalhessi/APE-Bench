import json
nd = r'''instance unitInterval.instTietzeExtension : TietzeExtension unitInterval :=
  .of_retract ⟨Subtype.val, continuous_subtype_val⟩
    ⟨Set.projIcc 0 1 zero_le_one, continuous_projIcc⟩ <| by ext; simp'''
print(json.dumps({"path":"Mathlib/Analysis/Complex/Tietze.lean","declaration_name":"unitInterval.instTietzeExtension","new_declaration":nd}))
