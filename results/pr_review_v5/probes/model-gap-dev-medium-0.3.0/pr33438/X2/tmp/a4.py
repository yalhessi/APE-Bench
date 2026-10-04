import json
print(json.dumps({"path":"Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean","line_start":217,"line_end":217,"replacement":"    norm_num\n\n#lint only simpNF simpComm simpVarHead\n\nexample : arctan (1 / √3) = π / 6 := by simp\nexample : arctan (-√3) = -(π / 3) := by simp\nexample : arctan (√3 / 3) = π / 6 := by simp\n"}))
