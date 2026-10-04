import json
decl = '''theorem mem_tangentConeAt_of_segment_subset {G : Type*} [AddCommGroup G] [Module ℝ G]
    [TopologicalSpace G] {s : Set G} {x y : G} (h : segment ℝ x y ⊆ s) :
    y - x ∈ tangentConeAt ℝ s x :=
  mem_tangentConeAt_of_openSegment_subset ((openSegment_subset_segment ℝ x y).trans h)'''
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","declaration_name":"mem_tangentConeAt_of_segment_subset","new_declaration":decl}))
