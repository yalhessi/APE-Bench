import json
rep = '''* `ProbabilityTheory.Kernel.integral_comp`: the integral against the composition is
  `∫ z, f z ∂((η ∘ₖ κ) a) = ∫ x, ∫ y, f y ∂(η x) ∂(κ a)`.'''
print(json.dumps({"path":"Mathlib/Probability/Kernel/Composition/IntegralCompProd.lean","line_start":30,"line_end":31,"replacement":rep}))
