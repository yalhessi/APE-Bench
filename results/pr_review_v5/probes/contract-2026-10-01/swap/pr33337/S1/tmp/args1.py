import json
rep = '''theorem coe_starProjection_eq_isCompl_projection [K.HasOrthogonalProjection] :
    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by
  simp [starProjection, coe_orthogonalProjection_eq_linearProjOfIsCompl, IsCompl.projection]

@[deprecated (since := "2025-12-26")] alias starProjection_coe_eq_isCompl_projection :=
  coe_starProjection_eq_isCompl_projection'''
print(json.dumps({"path":"Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean","line_start":208,"line_end":214,"replacement":rep}))
