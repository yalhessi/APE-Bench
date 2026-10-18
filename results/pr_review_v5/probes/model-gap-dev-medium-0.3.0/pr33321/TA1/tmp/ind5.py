import json, re
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp"
exec(open(D + "/ind4.py").read().split("spec =")[0])
def imports(xs): return "\n".join("public import " + x for x in xs)
spec = []
for name, xs in [("Lattice instead of Pointwise", ["Mathlib.Algebra.Group.Irreducible.Defs","Mathlib.Algebra.Group.Subgroup.Lattice","Mathlib.Algebra.Order.Group.Defs","Mathlib.Order.Preorder.Finite"]),
                 ("Subgroup.Basic only", ["Mathlib.Algebra.Group.Irreducible.Defs","Mathlib.Algebra.Group.Subgroup.Basic","Mathlib.Algebra.Order.Group.Defs","Mathlib.Order.Preorder.Finite"])]:
    rep = imports(xs) + "\n" + L(16, 56) + "\n" + tail
    spec.append((name, {"path":F, "line_start":8, "line_end":190, "replacement":rep}))
json.dump(spec, open(D + "/ind5.json", "w"))
