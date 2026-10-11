import json
D="/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33305/TA1/tmp/"
edits = {
 "ge_lowdegree": {"path":"Mathlib/GroupTheory/GroupExtension/Defs.lean","line_start":51,"line_end":52,"replacement":
   "- there is a bijection between equivalence classes of group extensions and `groupCohomology.H2`\n  (which is also stated as a TODO in\n  `Mathlib/RepresentationTheory/Homological/GroupCohomology/LowDegree.lean`)."},
 "ge_planned": {"path":"Mathlib/GroupTheory/GroupExtension/Defs.lean","line_start":49,"line_end":50,"replacement":
   "  (which will be available in `Mathlib/GroupTheory/GroupExtension/Abelian.lean`, to be added in a\n  later PR)."},
 "ah_path": {"path":"Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean","line_start":19,"line_end":20,"replacement":
   "Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/GroupTheory/GroupAction/Hom.lean` and\n`SMulCommClass` instances saying that left and right actions commute."},
 "ah_todo": {"path":"Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean","line_start":19,"line_end":20,"replacement":
   "Add `SMulCommClass` instances saying that the left actions on `α →[N] β` defined in\n`Mathlib/GroupTheory/GroupAction/Hom.lean` commute with the action of `Mᵈᵐᵃ` defined here, and\nadd the corresponding left actions and instances on `A →+[N] B`."},
 "sign": {"path":"Mathlib/GroupTheory/Perm/Sign.lean","line_start":28,"line_end":30,"replacement":
   "Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`.\n-/"},
}
for k,v in edits.items():
    json.dump(v, open(D+k+".json","w"))
    for line in v["replacement"].split("\n"):
        print(k, len(line), line)
