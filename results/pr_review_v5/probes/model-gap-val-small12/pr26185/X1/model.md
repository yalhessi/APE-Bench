# The PR model for #26185 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Counterexamples): Peano curve
- description: Prove the existence of a continuous surjection from `unitInterval` onto `unitInterval × unitInterval`.

- [x] depends on: #26184
- changed files: Counterexamples.lean, Counterexamples/PeanoCurve.lean, Mathlib/Analysis/Complex/Tietze.lean, Mathlib/Topology/ContinuousMap/Basic.lean, Mathlib/Topology/UnitInterval.lean

## Objects

### `import in Counterexamples.lean` (import, modified) [d5988f4a00]
- file: `Counterexamples.lean`; changed: imports:added

### `exists_long_peano_curve` (lemma, added) [39e7f50bc9]
- file: `Counterexamples/PeanoCurve.lean`; changed: documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma exists_long_peano_curve :
    ∃ f : C(ℝ, I × I), Set.SurjOn f cantorSet Set.univ := by
  -- Take a continuous surjection from the Cantor set to the square
  obtain ⟨g, hg1, hg2⟩ := exists_nat_bool_continuous_surjective_of_compact (I × I)
  let g' : C(cantorSet, I × I) :=
    ⟨g ∘ cantorSetHomeomorphNatToBool, Continuous.comp hg1 (Homeomorph.continuous _)⟩
  have hg' : Function.Surjective g' := by
    simp only [ContinuousMap.coe_mk, EquivLike.surjective_comp, g', hg2]
  -- Extend it to whole `ℝ`
  obtain ⟨f, hf⟩ := ContinuousMap.exists_restrict_eq isClosed_cantorSet g'
  use f
  simp only [Set.surjOn_iff_surjective, ← ContinuousMap.coe_restrict, hf, hg']
```

### `doc_comment in PeanoCurve.lean` (command, added) [3b0fa67f4e]
- file: `Counterexamples/PeanoCurve.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- There is a continuous function on `ℝ` that maps the Cantor set to the square. -/
```

### `module_doc in PeanoCurve.lean` (module_doc, added) [3b644f5ded]
- file: `Counterexamples/PeanoCurve.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Peano curve
This file proves the existsence of a Peano curve -- continuous sujrective map from the interval
`[0, 1]` onto the square `[0, 1] × [0, 1]`.
-/
```

### `namespace in PeanoCurve.lean` (command, added) [3d9c7e245f]
- file: `Counterexamples/PeanoCurve.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open scoped unitInterval
```

### `exists_peano_curve` (theorem, added) [57860242fb]
- file: `Counterexamples/PeanoCurve.lean`; changed: documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem exists_peano_curve :
    ∃ f : C(I, I × I), Function.Surjective f := by
  obtain ⟨f, hf⟩ := exists_long_peano_curve
  -- Restrict the map from `exists_long_peano_curve` to the interval
  use ContinuousMap.restrict I f
  rw [ContinuousMap.coe_restrict, ← Set.surjOn_iff_surjective]
  exact Set.SurjOn.mono cantorSet_subset_unitInterval (by rfl) hf
```

### `doc_comment in PeanoCurve.lean` (command, added) [d564cb8332]
- file: `Counterexamples/PeanoCurve.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- There is a continuous surjection from the interval to the square. -/
```

### `unitInterval.instTietzeExtension` (instance, added) [b03f2d3d52]
- file: `Mathlib/Analysis/Complex/Tietze.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance unitInterval.instTietzeExtension : TietzeExtension unitInterval := by
  rw [unitInterval.eq_closedBall]
  exact Metric.instTietzeExtensionClosedBall ℝ _ (by norm_num)
```

### `ContinuousMap.coe_restrict` (theorem, modified) [8aa7eea3c3]
- file: `Mathlib/Topology/ContinuousMap/Basic.lean`; changed: statement_or_type:modified
- before the PR:
```lean
@[simp]
theorem coe_restrict (f : C(α, β)) : ⇑(f.restrict s) = f ∘ ((↑) : s → α) :=
  rfl
```
- as the PR leaves it:
```lean
@[simp]
theorem coe_restrict (f : C(α, β)) : ⇑(f.restrict s) = s.restrict f :=
  rfl
```

### `ContinuousMap.liftCover_restrict` (theorem, modified) [fff26894b8]
- file: `Mathlib/Topology/ContinuousMap/Basic.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem liftCover_restrict {i : ι} : (liftCover S φ hφ hS).restrict (S i) = φ i := by
  ext
  simp only [coe_restrict, Function.comp_apply, liftCover_coe]
```
- as the PR leaves it:
```lean
@[simp]
theorem liftCover_restrict {i : ι} : (liftCover S φ hφ hS).restrict (S i) = φ i := by
  ext
  simp only [restrict_apply, liftCover_coe]
```

### `unitInterval.eq_closedBall` (theorem, added) [f8db9d961a]
- file: `Mathlib/Topology/UnitInterval.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem eq_closedBall : I = Metric.closedBall 2⁻¹ 2⁻¹ := by
  norm_num [unitInterval, Real.Icc_eq_closedBall]
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `ContinuousMap.coe_restrict`, `ContinuousMap.liftCover_restrict` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `exists_long_peano_curve` -> `ContinuousMap.coe_restrict`
- direct_use_of_changed_declaration [exact]: `exists_peano_curve` -> `ContinuousMap.coe_restrict`
- direct_use_of_changed_declaration [exact]: `exists_peano_curve` -> `exists_long_peano_curve`
- direct_use_of_changed_declaration [exact]: `unitInterval.instTietzeExtension` -> `unitInterval.eq_closedBall`
- name_family [high]: `ContinuousMap.coe_restrict` -> `ContinuousMap.liftCover_restrict`
- name_family [high]: `ContinuousMap.liftCover_restrict` -> `ContinuousMap.coe_restrict`
