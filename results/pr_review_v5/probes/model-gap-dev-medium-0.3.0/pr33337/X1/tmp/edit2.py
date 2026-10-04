import json, sys
name = sys.argv[1]
rep = f'''open Submodule in
theorem {name} [K.HasOrthogonalProjection] :
    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by
  simp [starProjection, coe_orthogonalProjection_eq_linearProjOfIsCompl, IsCompl.projection]

@[deprecated (since := "2025-12-26")] alias starProjection_coe_eq_isCompl_projection :=
  {name}'''
print(json.dumps({"path":"Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean","line_start":208,"line_end":214,"replacement":rep}))
