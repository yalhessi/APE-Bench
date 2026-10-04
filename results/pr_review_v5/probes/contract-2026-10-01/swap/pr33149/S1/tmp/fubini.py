import json
rep = '''theorem fubini_torus3 (f : Fin 3 → UnitAddCircle → ℂ) :
    ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y :=
  MeasureTheory.integral_fintype_prod_volume_eq_prod f
'''
print(json.dumps({"path":"Mathlib/Analysis/ODE/GalerkinRegularity.lean","declaration_name":"fubini_torus3","new_declaration":rep}))
