import json
rep = r'''
@[deprecated (since := "2025-12-22")]
alias Submonoid.closure_image_one_lt_and_isMulIndecomposable :=
  Submonoid.closure_image_isMulIndecomposable_baseOf

@[deprecated (since := "2025-12-22")]
alias AddSubmonoid.closure_image_pos_and_isAddIndecomposable :=
  AddSubmonoid.closure_image_isAddIndecomposable_baseOf
'''
print(json.dumps({"path":"Mathlib/Algebra/Group/Irreducible/Indecomposable.lean","line_start":114,"line_end":114,"replacement":rep}))
