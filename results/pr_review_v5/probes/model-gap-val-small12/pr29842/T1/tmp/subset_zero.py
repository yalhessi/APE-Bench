import json
L=open("tmp/file.lean").read().split("\n")
# 1-indexed: lines 146..312 replaced
moved = L[295:312]  # lines 296..312
print("\n".join(moved), file=open("tmp/moved.txt","w"))
moved_txt = "\n".join(moved).replace(
 "theorem tangentConeAt_subset_zero (hx", "theorem tangentConeAt_subset_zero [T2Space E] (hx").replace(
 "theorem UniqueDiffWithinAt.accPt [Nontrivial E]", "theorem UniqueDiffWithinAt.accPt [T2Space E] [Nontrivial E]")
middle = L[145:295]  # lines 146..295
rep = "\n" + moved_txt + "\n" + "\n".join(middle)
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","line_start":146,"line_end":312,"replacement":rep}))
