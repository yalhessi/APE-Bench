import json
rep = r'''/-- For every nonempty compact metric space `X` with the Tietze extension property, there is a
continuous function on `ℝ` that maps the Cantor set onto `X`. -/
lemma exists_long_peano_curve (X : Type*) [MetricSpace X] [CompactSpace X] [Nonempty X]
    [TietzeExtension.{0} X] :
    ∃ f : C(ℝ, X), Set.SurjOn f cantorSet Set.univ := by
  -- Take a continuous surjection from the Cantor set to `X`
  obtain ⟨g, hg1, hg2⟩ := exists_nat_bool_continuous_surjective_of_compact X
  let g' : C(cantorSet, X) := ⟨g ∘ cantorSetHomeomorphNatToBool, by fun_prop⟩
  have hg' : Function.Surjective g' := by
    simp only [ContinuousMap.coe_mk, EquivLike.surjective_comp, g', hg2]
  -- Extend it to whole `ℝ`
  obtain ⟨f, hf⟩ := ContinuousMap.exists_restrict_eq isClosed_cantorSet g'
  use f
  simp only [Set.surjOn_iff_surjective, ← ContinuousMap.coe_restrict, hf, hg']

/-- For every nonempty compact metric space `X` with the Tietze extension property, there is a
continuous surjection from the unit interval onto `X`. -/
theorem exists_continuous_surjective_of_tietzeExtension (X : Type*) [MetricSpace X]
    [CompactSpace X] [Nonempty X] [TietzeExtension.{0} X] :
    ∃ f : C(I, X), Function.Surjective f := by
  obtain ⟨f, hf⟩ := exists_long_peano_curve X
  -- Restrict the map from `exists_long_peano_curve` to the interval
  use ContinuousMap.restrict I f
  rw [ContinuousMap.coe_restrict, ← Set.surjOn_iff_surjective]
  exact Set.SurjOn.mono cantorSet_subset_unitInterval subset_rfl hf

/-- There is a continuous surjection from the interval to the square. -/
theorem exists_peano_curve :
    ∃ f : C(I, I × I), Function.Surjective f :=
  exists_continuous_surjective_of_tietzeExtension (I × I)

/-- There is a continuous surjection from the interval onto the Hilbert cube. -/
example : ∃ f : C(I, ℕ → I), Function.Surjective f :=
  exists_continuous_surjective_of_tietzeExtension (ℕ → I)'''
print(json.dumps({"path":"Counterexamples/PeanoCurve.lean","line_start":17,"line_end":38,"replacement":rep}))
