import json
rep = '''@[deprecated LinearIsometry.isComplete_image_iff (since := "2025-12-25")]
theorem isComplete_image_iff' (f : LinearIsometry σ₁₂ E E₂) {s : Set E} :
    IsComplete (f '' s) ↔ IsComplete s :=
  LinearIsometry.isComplete_image_iff _

example (g : E →ₛₗᵢ[σ₁₂] E₂) {s : Set E} : IsComplete (g '' s) ↔ IsComplete s := by simp
example (g : E →ₛₗᵢ[σ₁₂] E₂) {s : Set E} (h : IsComplete s) : IsComplete (g '' s) := by simpa
example [SemilinearIsometryClass 𝓕 σ₁₂ E E₂] (g : 𝓕) (x : E) : ‖g x‖₊ = ‖x‖₊ := by
  simp only [SemilinearIsometryClass.nnnorm_map]'''
print(json.dumps({"path": "Mathlib/Analysis/Normed/Operator/LinearIsometry.lean", "line_start": 218, "line_end": 221, "replacement": rep}))
