import json
rep = '''/-- If a subset of a real vector space contains an open segment, then the direction of this
segment belongs to the tangent cone at its endpoints. -/
theorem mem_tangentConeAt_of_openSegment_subset {G : Type*} [AddCommGroup G] [Module ℝ G]
    [TopologicalSpace G] {s : Set G} {x y : G} (h : openSegment ℝ x y ⊆ s) :
    y - x ∈ tangentConeAt ℝ s x := by
  refine mem_tangentConeAt_of_pow_smul one_half_pos.ne' (by norm_num) ?_
  refine (eventually_ne_atTop 0).mono fun n hn ↦ (h ?_)
  rw [openSegment_eq_image]
  refine ⟨(1 / 2) ^ n, ⟨?_, ?_⟩, ?_⟩
  · exact pow_pos one_half_pos _
  · exact pow_lt_one₀ one_half_pos.le one_half_lt_one hn
  · simp only [sub_smul, one_smul, smul_sub]; abel

@[deprecated (since := "2025-04-27")]
alias mem_tangentCone_of_openSegment_subset := mem_tangentConeAt_of_openSegment_subset

/-- If a subset of a real vector space contains a segment, then the direction of this
segment belongs to the tangent cone at its endpoints. -/
theorem mem_tangentConeAt_of_segment_subset {G : Type*} [AddCommGroup G] [Module ℝ G]
    [TopologicalSpace G] {s : Set G} {x y : G} (h : segment ℝ x y ⊆ s) :
    y - x ∈ tangentConeAt ℝ s x :=
  mem_tangentConeAt_of_openSegment_subset ((openSegment_subset_segment ℝ x y).trans h)'''
print(json.dumps({"path":"Mathlib/Analysis/Calculus/TangentCone.lean","line_start":240,"line_end":259,"replacement":rep}))
