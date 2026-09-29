import json
rep = r'''def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  {i | IsMulIndecomposable v {j | 1 < f (v j)} i}'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":49,"line_end":50,"replacement":rep}))
