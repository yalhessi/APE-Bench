import json
rep = r'''/-- There is a continuous function on `ℝ` that maps the Cantor set onto the square. -/
lemma exists_long_peano_curve :
    ∃ f : C(ℝ, I × I), Set.SurjOn f cantorSet Set.univ := by
  -- Take a continuous surjection from the Cantor set to the square
  obtain ⟨g, hg1, hg2⟩ := exists_nat_bool_continuous_surjective_of_compact (I × I)
  let g' : C(cantorSet, I × I) := ⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩
  have hg' : Function.Surjective g' := by
    simp only [ContinuousMap.coe_mk, EquivLike.surjective_comp, g', hg2]
  -- Extend it to whole `ℝ`
  obtain ⟨f, hf⟩ := ContinuousMap.exists_restrict_eq isClosed_cantorSet g'
  refine ⟨f, Set.surjOn_iff_surjective.mpr ?_⟩
  exact (hf ▸ hg' : Function.Surjective (f.restrict cantorSet))

/-- There is a continuous surjection from the interval to the square. -/
theorem exists_peano_curve :
    ∃ f : C(I, I × I), Function.Surjective f := by
  obtain ⟨f, hf⟩ := exists_long_peano_curve
  -- Restrict the map from `exists_long_peano_curve` to the interval
  exact ⟨f.restrict I, Set.surjOn_iff_surjective.mp <| hf.mono cantorSet_subset_unitInterval subset_rfl⟩'''
print(json.dumps({"path":"Counterexamples/PeanoCurve.lean","line_start":17,"line_end":38,"replacement":rep}))
