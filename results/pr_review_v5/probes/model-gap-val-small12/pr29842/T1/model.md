# The PR model for #29842 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(TangentCone): generalize some lemmas to TVS
- description: (not recoverable at review start)
- changed files: Mathlib/Analysis/Calculus/TangentCone.lean

## Objects

### `section in TangentCone.lean` (command, modified) [0bb7c0dadc]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:modified
- before the PR:
```lean
end TVS



section Normed


variable {𝕜' : Type*} [NontriviallyNormedField 𝕜'] [NormedAlgebra 𝕜 𝕜']


variable [NormedAddCommGroup E] [NormedSpace 𝕜 E] [NormedSpace 𝕜' E] [IsScalarTower 𝕜 𝕜' E]


variable [NormedAddCommGroup F] [NormedSpace 𝕜 F]


variable {x y : E} {s t : Set E}



protected alias ⟨UniqueDiffWithinAt.of_closure, UniqueDiffWithinAt.closure⟩ :=
  uniqueDiffWithinAt_closure
```
- as the PR leaves it:
```lean
variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]
```

### `section in TangentCone.lean` (command, modified) [12d13f49e1]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:modified
- before the PR:
```lean
end TVS



section Normed


variable [NormedAddCommGroup E] [NormedSpace 𝕜 E]


variable [NormedAddCommGroup F] [NormedSpace 𝕜 F]


variable [NormedAddCommGroup G] [NormedSpace ℝ G]


variable {x y : E} {s t : Set E}
```
- as the PR leaves it:
```lean
variable [ContinuousSMul 𝕜 E]
```

### `section in TangentCone.lean` (command, added) [1720719d65]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {x y : E} {s t : Set E}
```

### `section in TangentCone.lean` (command, added) [24cb5398bc]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end TVS
```

### `section in TangentCone.lean` (command, added) [33d563ffdf]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Normed
```

### `uniqueDiffWithinAt_closure` (theorem, removed) [596fd4bfa5]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem uniqueDiffWithinAt_closure :
    UniqueDiffWithinAt 𝕜 (closure s) x ↔ UniqueDiffWithinAt 𝕜 s x := by
  simp [uniqueDiffWithinAt_iff]
```

### `section in TangentCone.lean` (command, added) [7539fcc12f]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [NormedAddCommGroup E] [NormedSpace 𝕜 E] [NormedSpace 𝕜' E] [IsScalarTower 𝕜 𝕜' E]
```

### `section in TangentCone.lean` (command, added) [7cc5f02619]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
variable [ContinuousAdd E]
```

### `tangentConeAt.lim_zero` (theorem, modified) [9605c98d68]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: proof:modified
- before the PR:
```lean
theorem tangentConeAt.lim_zero {α : Type*} (l : Filter α) {c : α → 𝕜} {d : α → E}
    (hc : Tendsto (fun n => ‖c n‖) l atTop) (hd : Tendsto (fun n => c n • d n) l (𝓝 y)) :
    Tendsto d l (𝓝 0) := by
  have A : Tendsto (fun n => ‖c n‖⁻¹) l (𝓝 0) := tendsto_inv_atTop_zero.comp hc
  have B : Tendsto (fun n => ‖c n • d n‖) l (𝓝 ‖y‖) := (continuous_norm.tendsto _).comp hd
  have C : Tendsto (fun n => ‖c n‖⁻¹ * ‖c n • d n‖) l (𝓝 (0 * ‖y‖)) := A.mul B
  rw [zero_mul] at C
  have : ∀ᶠ n in l, ‖c n‖⁻¹ * ‖c n • d n‖ = ‖d n‖ := by
    refine (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn => ?_
    rw [norm_smul, ← mul_assoc, inv_mul_cancel₀, one_mul]
    rwa [Ne, norm_eq_zero]
  have D : Tendsto (fun n => ‖d n‖) l (𝓝 0) := Tendsto.congr' this C
  rw [tendsto_zero_iff_norm_tendsto_zero]
  exact D
```
- as the PR leaves it:
```lean
theorem tangentConeAt.lim_zero {α : Type*} (l : Filter α) {c : α → 𝕜} {d : α → E}
    (hc : Tendsto (fun n => ‖c n‖) l atTop) (hd : Tendsto (fun n => c n • d n) l (𝓝 y)) :
    Tendsto d l (𝓝 0) := by
  have : ∀ᶠ n in l, (c n)⁻¹ • c n • d n = d n :=
    (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn ↦ inv_smul_smul₀ hn (d n)
  apply Tendsto.congr' this
  rw [tendsto_norm_atTop_iff_cobounded] at hc
  simpa using (tendsto_inv₀_cobounded.comp hc).smul hd
```

### `section in TangentCone.lean` (command, added) [a3e0d34262]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {𝕜' : Type*} [NontriviallyNormedField 𝕜'] [NormedAlgebra 𝕜 𝕜']
```

### `command in TangentCone.lean` (command, added) [a54404df91]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
protected alias ⟨UniqueDiffWithinAt.of_closure, UniqueDiffWithinAt.closure⟩ :=
  uniqueDiffWithinAt_closure
```

### `UniqueDiffWithinAt.mono_closure` (theorem, removed) [b1f8a5d021]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem UniqueDiffWithinAt.mono_closure (h : UniqueDiffWithinAt 𝕜 s x) (st : s ⊆ closure t) :
    UniqueDiffWithinAt 𝕜 t x :=
  (h.mono st).of_closure
```

### `tangentConeAt_closure` (theorem, added) [b51a7213bd]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem tangentConeAt_closure : tangentConeAt 𝕜 (closure s) x = tangentConeAt 𝕜 s x := by
  refine Subset.antisymm ?_ (tangentConeAt_mono subset_closure)
  rintro y ⟨c, d, ds, ctop, clim⟩
  obtain ⟨u, -, u_pos, u_lim⟩ :
      ∃ u, StrictAnti u ∧ (∀ (n : ℕ), 0 < u n) ∧ Tendsto u atTop (𝓝 (0 : ℝ)) :=
    exists_seq_strictAnti_tendsto (0 : ℝ)
  have : ∀ᶠ n in atTop, ∃ d', x + d' ∈ s ∧ dist (c n • d n) (c n • d') < u n := by
    filter_upwards [ctop.eventually_gt_atTop 0, ds] with n hn hns
    rcases Metric.mem_closure_iff.mp hns (u n / ‖c n‖) (div_pos (u_pos n) hn) with ⟨y, hys, hy⟩
    refine ⟨y - x, by simpa, ?_⟩
    rwa [dist_smul₀, ← dist_add_left x, add_sub_cancel, ← lt_div_iff₀' hn]
  simp only [Filter.skolem, eventually_and] at this
  rcases this with ⟨d', hd's, hd'⟩
  exact ⟨c, d', hd's, ctop, clim.congr_dist
    (squeeze_zero' (.of_forall fun _ ↦ dist_nonneg) (hd'.mono fun _ ↦ le_of_lt) u_lim)⟩
```

### `section in TangentCone.lean` (command, added) [c52e88a95d]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [NormedAddCommGroup G] [NormedSpace ℝ G]
```

### `section in TangentCone.lean` (command, added) [c58e422f84]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [NormedAddCommGroup F] [NormedSpace 𝕜 F]
```

### `uniqueDiffWithinAt_closure` (theorem, added) [d0abcaf087]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem uniqueDiffWithinAt_closure :
    UniqueDiffWithinAt 𝕜 (closure s) x ↔ UniqueDiffWithinAt 𝕜 s x := by
  simp [uniqueDiffWithinAt_iff]
```

### `tangentConeAt_closure` (theorem, removed) [ea6fc74ede]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem tangentConeAt_closure : tangentConeAt 𝕜 (closure s) x = tangentConeAt 𝕜 s x := by
  refine Subset.antisymm ?_ (tangentConeAt_mono subset_closure)
  rintro y ⟨c, d, ds, ctop, clim⟩
  obtain ⟨u, -, u_pos, u_lim⟩ :
      ∃ u, StrictAnti u ∧ (∀ (n : ℕ), 0 < u n) ∧ Tendsto u atTop (𝓝 (0 : ℝ)) :=
    exists_seq_strictAnti_tendsto (0 : ℝ)
  have : ∀ᶠ n in atTop, ∃ d', x + d' ∈ s ∧ dist (c n • d n) (c n • d') < u n := by
    filter_upwards [ctop.eventually_gt_atTop 0, ds] with n hn hns
    rcases Metric.mem_closure_iff.mp hns (u n / ‖c n‖) (div_pos (u_pos n) hn) with ⟨y, hys, hy⟩
    refine ⟨y - x, by simpa, ?_⟩
    rwa [dist_smul₀, ← dist_add_left x, add_sub_cancel, ← lt_div_iff₀' hn]
  simp only [Filter.skolem, eventually_and] at this
  rcases this with ⟨d', hd's, hd'⟩
  exact ⟨c, d', hd's, ctop, clim.congr_dist
    (squeeze_zero' (.of_forall fun _ ↦ dist_nonneg) (hd'.mono fun _ ↦ le_of_lt) u_lim)⟩
```

### `section in TangentCone.lean` (command, added) [ebfceb6cf1]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [NormedAddCommGroup E] [NormedSpace 𝕜 E]
```

### `UniqueDiffWithinAt.mono_closure` (theorem, added) [fcb0330926]
- file: `Mathlib/Analysis/Calculus/TangentCone.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem UniqueDiffWithinAt.mono_closure (h : UniqueDiffWithinAt 𝕜 s x) (st : s ⊆ closure t) :
    UniqueDiffWithinAt 𝕜 t x :=
  (h.mono st).of_closure
```

## Removed or renamed

- `uniqueDiffWithinAt_closure`
- `UniqueDiffWithinAt.mono_closure`
- `tangentConeAt_closure`

## Families (declarations that may be one decision)

- [exact] `UniqueDiffWithinAt.mono_closure` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `tangentConeAt_closure`, `uniqueDiffWithinAt_closure` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- name_family [high]: `UniqueDiffWithinAt.mono_closure` -> `UniqueDiffWithinAt.mono_closure`
- name_family [high]: `UniqueDiffWithinAt.mono_closure` -> `UniqueDiffWithinAt.mono_closure`
- name_family [high]: `tangentConeAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `tangentConeAt_closure` -> `tangentConeAt_closure`
- name_family [high]: `tangentConeAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `tangentConeAt_closure` -> `tangentConeAt_closure`
- name_family [high]: `tangentConeAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `tangentConeAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `tangentConeAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `tangentConeAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `tangentConeAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `uniqueDiffWithinAt_closure`
- name_family [high]: `uniqueDiffWithinAt_closure` -> `tangentConeAt_closure`
