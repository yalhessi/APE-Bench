import json,sys
rep = '''@[simp]
theorem nnnorm_map [SemilinearIsometryClass 𝓕 σ₁₂ E E₂] (f : 𝓕) (x : E) : ‖f x‖₊ = ‖x‖₊ :=
  NNReal.eq <| norm_map f x'''
print(json.dumps({"path": "Mathlib/Analysis/Normed/Operator/LinearIsometry.lean", "line_start": 99, "line_end": 101, "replacement": rep}))
