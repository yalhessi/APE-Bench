import json
F = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
dep = """  exact hi₁ hjk

@[to_additive (attr := deprecated (since := "2025-12-22"))]
alias Submonoid.closure_image_one_lt_and_isMulIndecomposable :=
  Submonoid.closure_image_isMulIndecomposable_baseOf
"""
baseof_set = """/-- The "base" of a set of points of a monoid relative to a morphism `f`. -/
@[to_additive /-- The "base" of `v` relative to a morphism `f`.

In the case that `v` is the set of roots of a crystallogrphic root system, and `S = ℚ`, this is the
base of the root system associated to `f`. -/]
def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=
  {i | IsMulIndecomposable v {j | 1 < f (v j)} i}"""
memlemma = """
@[to_additive]
lemma IsMulIndecomposable.mem_baseOf_iff [Monoid S] {v : ι → M} {f : M →* S} {i : ι} :
    i ∈ IsMulIndecomposable.baseOf v f ↔ IsMulIndecomposable v {j | 1 < f (v j)} i :=
  Iff.rfl
"""
spec = [
 ("deprecated alias", {"path":F,"line_start":113,"line_end":113,"replacement":dep}),
 ("baseOf as setOf", {"path":F,"declaration_name":"IsMulIndecomposable.baseOf","new_declaration":baseof_set}),
 ("mem_baseOf_iff", {"path":F,"line_start":51,"line_end":51,"replacement":memlemma}),
 ("Submonoid let t := baseOf", {"path":F,"line_start":98,"line_end":98,"replacement":"  let t : Set ι := IsMulIndecomposable.baseOf v f"}),
 ("invMonoidHom ext", {"path":"Mathlib/Algebra/Group/Hom/Basic.lean","declaration_name":"invMonoidHom_comp_invMonoidHom","new_declaration":"@[to_additive (attr := simp)]\ntheorem invMonoidHom_comp_invMonoidHom : (invMonoidHom (α := α)).comp invMonoidHom = .id _ :=\n  MonoidHom.ext inv_inv"}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/ind3.json","w"))
