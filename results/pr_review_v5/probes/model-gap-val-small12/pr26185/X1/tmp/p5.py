import json
nd = """@[simp]
theorem coe_restrict (f : C(α, β)) : ⇑(f.restrict s) = f ∘ ((↑) : s → α) :=
  rfl"""
print(json.dumps({"path":"Mathlib/Topology/ContinuousMap/Basic.lean","declaration_name":"ContinuousMap.coe_restrict","new_declaration":nd}))
