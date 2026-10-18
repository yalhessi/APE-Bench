import json
L=open("tmp/file.lean").read().split("\n")
field = "\n".join(L[547:586])  # lines 548..586
middle = "\n".join(L[432:547])  # lines 433..547
sec = """section Field
variable {𝕜' : Type*} [NontriviallyNormedField 𝕜'] [NormedAlgebra 𝕜 𝕜'] [Module 𝕜' E]
  [IsScalarTower 𝕜 𝕜' E]

""" + field + """

end Field

"""
rep = sec + middle
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","line_start":433,"line_end":586,"replacement":rep}))
