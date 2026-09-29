import json
rep = """/-!
# Peano curve

This file proves the existence of a Peano curve: a continuous surjective map from the interval
`[0, 1]` onto the square `[0, 1] × [0, 1]`.

## Main results

* `PeanoCurve.exists_peano_curve`: there is a continuous surjection `I → I × I`.
-/

open scoped unitInterval

namespace PeanoCurve

/-- There is a continuous function on `ℝ` that maps the Cantor set onto the square. -/
lemma exists_long_peano_curve :
    ∃ f : C(ℝ, I × I), Set.SurjOn f cantorSet Set.univ := by
  -- Take a continuous surjection from the Cantor set to the square
  obtain ⟨g, hg, hg'⟩ := exists_nat_bool_continuous_surjective_of_compact (I × I)
  -- Extend it to whole `ℝ`
  obtain ⟨f, hf⟩ := ContinuousMap.exists_restrict_eq isClosed_cantorSet
    ⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩
  refine ⟨f, Set.surjOn_iff_surjective.mpr ?_⟩
  change Function.Surjective (f.restrict cantorSet)
  rw [hf]
  exact hg'.comp cantorSetHomeomorphNatToBool.surjective

/-- There is a continuous surjection from the interval to the square. -/
theorem exists_peano_curve :
    ∃ f : C(I, I × I), Function.Surjective f :=
  let ⟨f, hf⟩ := exists_long_peano_curve
  ⟨f.restrict I, Set.surjOn_iff_surjective.mp (hf.mono cantorSet_subset_unitInterval subset_rfl)⟩

end PeanoCurve"""
print(json.dumps({"path":"Counterexamples/PeanoCurve.lean","line_start":9,"line_end":38,"replacement":rep}))
