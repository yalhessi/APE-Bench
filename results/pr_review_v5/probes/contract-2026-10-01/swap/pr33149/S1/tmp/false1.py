import json
rep = '''theorem bkm_implies_regularity_inconsistent : False := by
  have h : ContDiff ℝ ⊤ (fun t : ℝ => |t|) :=
    (bkm_implies_regularity (fun _ t _ => |t|) 0 ⟨_, le_rfl⟩).2 0 0
  exact not_differentiableAt_abs_zero (h.differentiable le_top 0)
'''
print(json.dumps({"path":"Mathlib/Analysis/ODE/GalerkinRegularity.lean","line_start":467,"line_end":469,"replacement":rep}))
