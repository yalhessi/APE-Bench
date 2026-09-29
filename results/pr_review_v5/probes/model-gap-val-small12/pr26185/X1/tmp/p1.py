import json
nd = """lemma exists_long_peano_curve :
    ∃ f : C(ℝ, I × I), Set.SurjOn f cantorSet Set.univ := by
  obtain ⟨g, hg, hg'⟩ := exists_nat_bool_continuous_surjective_of_compact (I × I)
  obtain ⟨f, hf⟩ := ContinuousMap.exists_restrict_eq isClosed_cantorSet
    ⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩
  refine ⟨f, Set.surjOn_iff_surjective.mpr ?_⟩
  change Function.Surjective (f.restrict cantorSet)
  rw [hf]
  exact hg'.comp cantorSetHomeomorphNatToBool.surjective"""
print(json.dumps({"path":"Counterexamples/PeanoCurve.lean","declaration_name":"exists_long_peano_curve","new_declaration":nd}))
