import json
rep = '''theorem integral_le_const_mul_length_inconsistent : False := by
  have hni : ¬ IntervalIntegrable (fun t : ℝ => -1 - t⁻¹) MeasureTheory.volume 0 1 := by
    intro h
    have h2 : IntervalIntegrable (fun t : ℝ => t⁻¹) MeasureTheory.volume 0 1 := by
      simpa using (intervalIntegrable_const (c := (-1 : ℝ))).sub h
    rw [intervalIntegrable_inv_iff] at h2
    simp at h2
  have h0 : ∫ t in (0 : ℝ)..1, (-1 - t⁻¹) = 0 := intervalIntegral.integral_undef hni
  have := integral_le_const_mul_length (fun t => -1 - t⁻¹) (-1) 1 one_pos (by
    intro t ht
    have : 0 ≤ t⁻¹ := inv_nonneg.mpr ht.1
    linarith)
  rw [h0] at this
  norm_num at this
'''
print(json.dumps({"path":"Mathlib/Analysis/ODE/GalerkinRegularity.lean","line_start":467,"line_end":469,"replacement":rep}))
