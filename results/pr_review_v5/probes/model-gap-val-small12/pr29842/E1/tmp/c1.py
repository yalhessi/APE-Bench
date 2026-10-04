import json
decl = '''theorem mem_tangentConeAt_of_openSegment_subset {G : Type*} [AddCommGroup G] [Module ℝ G]
    [TopologicalSpace G] {s : Set G} {x y : G} (h : openSegment ℝ x y ⊆ s) :
    y - x ∈ tangentConeAt ℝ s x := by
  refine mem_tangentConeAt_of_pow_smul one_half_pos.ne' (by norm_num) ?_
  refine (eventually_ne_atTop 0).mono fun n hn ↦ (h ?_)
  rw [openSegment_eq_image]
  refine ⟨(1 / 2) ^ n, ⟨?_, ?_⟩, ?_⟩
  · exact pow_pos one_half_pos _
  · exact pow_lt_one₀ one_half_pos.le one_half_lt_one hn
  · simp only [sub_smul, one_smul, smul_sub]; abel

#check @mem_tangentConeAt_of_openSegment_subset'''
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","declaration_name":"mem_tangentConeAt_of_openSegment_subset","new_declaration":decl}))
