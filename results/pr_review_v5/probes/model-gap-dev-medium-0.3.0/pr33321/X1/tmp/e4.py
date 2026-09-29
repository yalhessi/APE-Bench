import json
rep = r'''
@[to_additive (attr := deprecated (since := "2025-12-22"))]
alias Submonoid.closure_image_one_lt_and_isMulIndecomposable :=
  Submonoid.closure_image_isMulIndecomposable_baseOf

example := @AddSubmonoid.closure_image_pos_and_isAddIndecomposable
'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":114,"line_end":114,"replacement":rep}))
