# The PR model for #33362 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: weaken assumptions in Schwarz lemma
- description: Assume that `f` maps an open ball to a closed ball.
Also, generalize the "same radius" versions to any codomain.
- changed files: Mathlib/Analysis/Complex/Schwarz.lean

## Objects

### `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` (theorem, removed) [0ad6d80723]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div [CompleteSpace E] [StrictConvexSpace ℝ E]
    (hd : DifferentiableOn ℂ f (ball c R₁)) (h_maps : Set.MapsTo f (ball c R₁) (ball (f c) R₂))
    (h_z₀ : z₀ ∈ ball c R₁) (h_eq : ‖dslope f c z₀‖ = R₂ / R₁) :
    Set.EqOn f (fun z => f c + (z - c) • dslope f c z₀) (ball c R₁) := by
  set g := dslope f c
  rintro z hz
  by_cases h : z = c; · simp [h]
  have h_R₁ : 0 < R₁ := nonempty_ball.mp ⟨_, h_z₀⟩
  have g_le_div : ∀ z ∈ ball c R₁, ‖g z‖ ≤ R₂ / R₁ := fun z hz =>
    norm_dslope_le_div_of_mapsTo_ball hd h_maps hz
  have g_max : IsMaxOn (norm ∘ g) (ball c R₁) z₀ :=
    isMaxOn_iff.mpr fun z hz => by simpa [h_eq] using g_le_div z hz
  have g_diff : DifferentiableOn ℂ g (ball c R₁) :=
    (differentiableOn_dslope (isOpen_ball.mem_nhds (mem_ball_self h_R₁))).mpr hd
  have : g z = g z₀ := eqOn_of_isPreconnected_of_isMaxOn_norm (convex_ball c R₁).isPreconnected
    isOpen_ball g_diff h_z₀ g_max hz
  simp only [g] at this
  simp [g, ← this]
```

### `section in Schwarz.lean` (command, removed) [0bf1665454]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: namespace:removed
- before the PR:
```lean
end Space
```

### `Complex.schwarz_aux` (theorem, modified) [26e35f26fa]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: attributes:added, name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem schwarz_aux {f : ℂ → ℂ} (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (hz : z ∈ ball c R₁) :
    ‖dslope f c z‖ ≤ R₂ / R₁ := by
  have hR₁ : 0 < R₁ := nonempty_ball.1 ⟨z, hz⟩
  suffices ∀ᶠ r in 𝓝[<] R₁, ‖dslope f c z‖ ≤ R₂ / r by
    refine ge_of_tendsto ?_ this
    exact (tendsto_const_nhds.div tendsto_id hR₁.ne').mono_left nhdsWithin_le_nhds
  rw [mem_ball] at hz
  filter_upwards [Ioo_mem_nhdsLT hz] with r hr
  have hr₀ : 0 < r := dist_nonneg.trans_lt hr.1
  replace hd : DiffContOnCl ℂ (dslope f c) (ball c r) := by
    refine DifferentiableOn.diffContOnCl ?_
    rw [closure_ball c hr₀.ne']
    exact ((differentiableOn_dslope <| ball_mem_nhds _ hR₁).mpr hd).mono
      (closedBall_subset_ball hr.2)
  refine norm_le_of_forall_mem_frontier_norm_le isBounded_ball hd ?_ ?_
  · rw [frontier_ball c hr₀.ne']
    intro z hz
    have hz' : z ≠ c := ne_of_mem_sphere hz hr₀.ne'
    rw [dslope_of_ne _ hz', slope_def_module, norm_smul, norm_inv, mem_sphere_iff_norm.1 hz, ←
      div_eq_inv_mul, div_le_div_iff_of_pos_right hr₀, ← dist_eq_norm]
    exact le_of_lt (h_maps (mem_ball.2 (by rw [mem_sphere.1 hz]; exact hr.2)))
  · rw [closure_ball c hr₀.ne', mem_closedBall]
    exact hr.1.le
```
- as the PR leaves it:
```lean
private theorem Complex.schwarz_aux {f : ℂ → ℂ} (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (hz : z ∈ ball c R₁) :
    ‖dslope f c z‖ ≤ R₂ / R₁ := by
  have hR₁ : 0 < R₁ := nonempty_ball.1 ⟨z, hz⟩
  suffices ∀ᶠ r in 𝓝[<] R₁, ‖dslope f c z‖ ≤ R₂ / r by
    refine ge_of_tendsto ?_ this
    exact (tendsto_const_nhds.div tendsto_id hR₁.ne').mono_left nhdsWithin_le_nhds
  rw [mem_ball] at hz
  filter_upwards [Ioo_mem_nhdsLT hz] with r hr
  have hr₀ : 0 < r := dist_nonneg.trans_lt hr.1
  replace hd : DiffContOnCl ℂ (dslope f c) (ball c r) := by
    refine DifferentiableOn.diffContOnCl ?_
    rw [closure_ball c hr₀.ne']
    exact ((differentiableOn_dslope <| ball_mem_nhds _ hR₁).mpr hd).mono
      (closedBall_subset_ball hr.2)
  refine norm_le_of_forall_mem_frontier_norm_le isBounded_ball hd ?_ ?_
  · rw [frontier_ball c hr₀.ne']
    intro z hz
    have hz' : z ≠ c := ne_of_mem_sphere hz hr₀.ne'
    rw [dslope_of_ne _ hz', slope_def_module, norm_smul, norm_inv, mem_sphere_iff_norm.1 hz, ←
      div_eq_inv_mul, div_le_div_iff_of_pos_right hr₀, ← mem_closedBall_iff_norm]
    exact h_maps <| mem_ball.2 <| by rw [mem_sphere.1 hz]; exact hr.2
  · rw [closure_ball c hr₀.ne', mem_closedBall]
    exact hr.1.le
```

### `Complex.dist_le_dist_of_mapsTo_ball_self` (theorem, modified) [2db82735e6]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem dist_le_dist_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (ball c R)) (hc : f c = c) (hz : z ∈ ball c R) :
    dist (f z) c ≤ dist z c := by
  have := dist_le_div_mul_dist_of_mapsTo_ball hd (by rwa [hc]) hz
  rwa [hc, div_self, one_mul] at this
  exact (nonempty_ball.1 ⟨z, hz⟩).ne'
```
- as the PR leaves it:
```lean
theorem dist_le_dist_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (closedBall (f c) R)) (hz : z ∈ ball c R) :
    dist (f z) (f c) ≤ dist z c := by
  simpa [(nonempty_ball.1 ⟨z, hz⟩).ne'] using dist_le_div_mul_dist_of_mapsTo_ball hd h_maps hz
```

### `namespace in Schwarz.lean` (command, added) [3d00fdc945]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: namespace:added
- as the PR leaves it:
```lean
namespace Complex
```

### `Complex.dist_le_div_mul_dist_of_mapsTo_ball` (theorem, modified) [41fbe3a2dc]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: statement_or_type:modified
- before the PR:
```lean
theorem dist_le_div_mul_dist_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (hz : z ∈ ball c R₁) :
    dist (f z) (f c) ≤ R₂ / R₁ * dist z c := by
  rcases eq_or_ne z c with (rfl | hne)
  · simp only [dist_self, mul_zero, le_rfl]
  simpa only [dslope_of_ne _ hne, slope_def_module, norm_smul, norm_inv, ← div_eq_inv_mul, ←
    dist_eq_norm, div_le_iff₀ (dist_pos.2 hne)] using norm_dslope_le_div_of_mapsTo_ball hd h_maps hz
```
- as the PR leaves it:
```lean
theorem dist_le_div_mul_dist_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (hz : z ∈ ball c R₁) :
    dist (f z) (f c) ≤ R₂ / R₁ * dist z c := by
  rcases eq_or_ne z c with (rfl | hne)
  · simp only [dist_self, mul_zero, le_rfl]
  simpa only [dslope_of_ne _ hne, slope_def_module, norm_smul, norm_inv, ← div_eq_inv_mul, ←
    dist_eq_norm, div_le_iff₀ (dist_pos.2 hne)] using norm_dslope_le_div_of_mapsTo_ball hd h_maps hz
```

### `module_doc in Schwarz.lean` (module_doc, removed) [52439b707a]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: documentation:removed
- before the PR:
```lean
/-!
# Schwarz lemma

In this file we prove several versions of the Schwarz lemma.

* `Complex.norm_deriv_le_div_of_mapsTo_ball`, `Complex.abs_deriv_le_div_of_mapsTo_ball`: if
  `f : ℂ → E` sends an open disk with center `c` and a positive radius `R₁` to an open ball with
  center `f c` and radius `R₂`, then the norm of the derivative of `f` at `c` is at most
  the ratio `R₂ / R₁`;

* `Complex.dist_le_div_mul_dist_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to an open disk with center `f c` and radius `R₂`, then for any `z` in the former
  disk we have `dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`;

* `Complex.abs_deriv_le_one_of_mapsTo_ball`: if `f : ℂ → ℂ` sends an open disk of positive radius
  to itself and the center of this disk to itself, then the norm of the derivative of `f`
  at the center of this disk is at most `1`;

* `Complex.dist_le_dist_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends an open disk to itself and the
  center `c` of this disk to itself, then for any point `z` of this disk we have
  `dist (f z) c ≤ dist z c`;

* `Complex.norm_le_norm_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends an open disk with center `0` to
  itself, then for any point `z` of this disk we have `abs (f z) ≤ abs z`.

## Implementation notes

We prove some versions of the Schwarz lemma for a map `f : ℂ → E` taking values in any normed space
over complex numbers.

## TODO

* Prove that these inequalities are strict unless `f` is an affine map.

* Prove that any diffeomorphism of the unit disk to itself is a Möbius map.

## Tags

Schwarz lemma
-/
```

### `Complex.norm_deriv_le_div_of_mapsTo_ball` (theorem, modified) [5a8f29f307]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: statement_or_type:modified
- before the PR:
```lean
theorem norm_deriv_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (h₀ : 0 < R₁) : ‖deriv f c‖ ≤ R₂ / R₁ := by
  simpa only [dslope_same] using norm_dslope_le_div_of_mapsTo_ball hd h_maps (mem_ball_self h₀)
```
- as the PR leaves it:
```lean
theorem norm_deriv_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (h₀ : 0 < R₁) :
    ‖deriv f c‖ ≤ R₂ / R₁ := by
  simpa only [dslope_same] using norm_dslope_le_div_of_mapsTo_ball hd h_maps (mem_ball_self h₀)
```

### `namespace in Schwarz.lean` (command, modified) [5c46f04559]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: namespace:modified
- before the PR:
```lean
open scoped Topology



namespace Complex



section Space
```
- as the PR leaves it:
```lean
open scoped Topology ComplexConjugate
```

### `Complex.norm_le_norm_of_mapsTo_ball_self` (theorem, modified) [5cd4da119c]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem norm_le_norm_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball 0 R))
    (h_maps : MapsTo f (ball 0 R) (ball 0 R)) (h₀ : f 0 = 0) (hz : ‖z‖ < R) :
    ‖f z‖ ≤ ‖z‖ := by
  replace hz : z ∈ ball (0 : ℂ) R := mem_ball_zero_iff.2 hz
  simpa only [dist_zero_right] using dist_le_dist_of_mapsTo_ball_self hd h_maps h₀ hz
```
- as the PR leaves it:
```lean
theorem norm_le_norm_of_mapsTo_ball_self (hd : DifferentiableOn ℂ f (ball 0 R))
    (h_maps : MapsTo f (ball 0 R) (closedBall 0 R)) (h₀ : f 0 = 0) (hz : ‖z‖ < R) :
    ‖f z‖ ≤ ‖z‖ := by
  simpa [h₀] using dist_le_dist_of_mapsTo_ball_self hd (by rwa [h₀]) (mem_ball_zero_iff.mpr hz)
```

### `module_doc in Schwarz.lean` (module_doc, modified) [6a3267fdab]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Schwarz lemma

In this file we prove several versions of the Schwarz lemma.

* `Complex.norm_deriv_le_div_of_mapsTo_ball`, `Complex.abs_deriv_le_div_of_mapsTo_ball`: if
  `f : ℂ → E` sends an open disk with center `c` and a positive radius `R₁` to an open ball with
  center `f c` and radius `R₂`, then the norm of the derivative of `f` at `c` is at most
  the ratio `R₂ / R₁`;

* `Complex.dist_le_div_mul_dist_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to an open disk with center `f c` and radius `R₂`, then for any `z` in the former
  disk we have `dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`;

* `Complex.abs_deriv_le_one_of_mapsTo_ball`: if `f : ℂ → ℂ` sends an open disk of positive radius
  to itself and the center of this disk to itself, then the norm of the derivative of `f`
  at the center of this disk is at most `1`;

* `Complex.dist_le_dist_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends an open disk to itself and the
  center `c` of this disk to itself, then for any point `z` of this disk we have
  `dist (f z) c ≤ dist z c`;

* `Complex.norm_le_norm_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends an open disk with center `0` to
  itself, then for any point `z` of this disk we have `abs (f z) ≤ abs z`.

## Implementation notes

We prove some versions of the Schwarz lemma for a map `f : ℂ → E` taking values in any normed space
over complex numbers.

## TODO

* Prove that these inequalities are strict unless `f` is an affine map.

* Prove that any diffeomorphism of the unit disk to itself is a Möbius map.

## Tags

Schwarz lemma
-/
```
- as the PR leaves it:
```lean
/-!
# Schwarz lemma

In this file we prove several versions of the Schwarz lemma.

* `Complex.norm_deriv_le_div_of_mapsTo_ball`, `Complex.abs_deriv_le_div_of_mapsTo_ball`: if
  `f : ℂ → E` sends an open disk with center `c` and a positive radius `R₁` to a closed ball with
  center `f c` and radius `R₂`, then the norm of the derivative of `f` at `c` is at most
  the ratio `R₂ / R₁`;

* `Complex.dist_le_div_mul_dist_of_mapsTo_ball`: if `f : ℂ → E` sends an open disk with center `c`
  and radius `R₁` to a closed disk with center `f c` and radius `R₂`, then for any `z` in the former
  disk we have `dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`;

* `Complex.abs_deriv_le_one_of_mapsTo_ball`: if `f : ℂ → ℂ` sends a point `c` to itself
  and it maps an open disk with center `c` to the closed disk with the same center and radius,
  then the norm of the derivative of `f` at the center of this disk is at most `1`;

* `Complex.dist_le_dist_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends a point `c` to itself
  and it maps an open disk with center `c` to the closed disk with the same center and radius,
  then for any point `z` of this disk we have `dist (f z) c ≤ dist z c`;

* `Complex.norm_le_norm_of_mapsTo_ball_self`: if `f : ℂ → ℂ` sends an open disk with center `0` to
  itself, then for any point `z` of this disk we have `abs (f z) ≤ abs z`.

## Implementation notes

We prove some versions of the Schwarz lemma for a map `f : ℂ → E` taking values in any normed space
over complex numbers.

## TODO

* Prove that any diffeomorphism of the unit disk to itself is a Möbius map.

## Tags

Schwarz lemma
-/
```

### `command in Schwarz.lean` (command, modified) [6b108ad444]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: value_or_body:modified
- before the PR:
```lean
/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and radius `R₁` to an
open ball with center `f c` and radius `R₂`, then for any `z` in the former disk we have
`dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`. -/
```
- as the PR leaves it:
```lean
/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `c` and radius `R₁` to a
closed ball with center `f c` and radius `R₂`, then for any `z` in the former disk we have
`dist (f z) (f c) ≤ (R₂ / R₁) * dist z c`. -/
```

### `command in Schwarz.lean` (command, modified) [702401487c]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: value_or_body:modified
- before the PR:
```lean
/-- The **Schwarz Lemma**: if `f : ℂ → ℂ` sends an open disk with center `0` to itself, then for any
point `z` of this disk we have `‖f z‖ ≤ ‖z‖`. -/
```
- as the PR leaves it:
```lean
/-- The **Schwarz Lemma**: if `f : ℂ → E` sends an open disk with center `0`
to the closed ball with center `0` of the same radius,
then for any point `z` of this disk we have `‖f z‖ ≤ ‖z‖`. -/
```

### `command in Schwarz.lean` (command, added) [744403789c]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
@[expose] public section
```

### `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` (theorem, modified) [9a4d29d269]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: statement_or_type:modified
- before the PR:
```lean
theorem affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div' [CompleteSpace E]
    [StrictConvexSpace ℝ E] (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : Set.MapsTo f (ball c R₁) (ball (f c) R₂))
    (h_z₀ : ∃ z₀ ∈ ball c R₁, ‖dslope f c z₀‖ = R₂ / R₁) :
    ∃ C : E, ‖C‖ = R₂ / R₁ ∧ Set.EqOn f (fun z => f c + (z - c) • C) (ball c R₁) :=
  let ⟨z₀, h_z₀, h_eq⟩ := h_z₀
  ⟨dslope f c z₀, h_eq, affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div hd h_maps h_z₀ h_eq⟩
```
- as the PR leaves it:
```lean
theorem affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div' [CompleteSpace E]
    [StrictConvexSpace ℝ E] (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : Set.MapsTo f (ball c R₁) (closedBall (f c) R₂))
    (h_z₀ : ∃ z₀ ∈ ball c R₁, ‖dslope f c z₀‖ = R₂ / R₁) :
    ∃ C : E, ‖C‖ = R₂ / R₁ ∧ Set.EqOn f (fun z => f c + (z - c) • C) (ball c R₁) :=
  let ⟨z₀, h_z₀, h_eq⟩ := h_z₀
  ⟨dslope f c z₀, h_eq, affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div hd h_maps h_z₀ h_eq⟩
```

### `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` (theorem, modified) [9c2fe9a38a]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div [CompleteSpace E] [StrictConvexSpace ℝ E]
    (hd : DifferentiableOn ℂ f (ball c R₁)) (h_maps : Set.MapsTo f (ball c R₁) (ball (f c) R₂))
    (h_z₀ : z₀ ∈ ball c R₁) (h_eq : ‖dslope f c z₀‖ = R₂ / R₁) :
    Set.EqOn f (fun z => f c + (z - c) • dslope f c z₀) (ball c R₁) := by
  set g := dslope f c
  rintro z hz
  by_cases h : z = c; · simp [h]
  have h_R₁ : 0 < R₁ := nonempty_ball.mp ⟨_, h_z₀⟩
  have g_le_div : ∀ z ∈ ball c R₁, ‖g z‖ ≤ R₂ / R₁ := fun z hz =>
    norm_dslope_le_div_of_mapsTo_ball hd h_maps hz
  have g_max : IsMaxOn (norm ∘ g) (ball c R₁) z₀ :=
    isMaxOn_iff.mpr fun z hz => by simpa [h_eq] using g_le_div z hz
  have g_diff : DifferentiableOn ℂ g (ball c R₁) :=
    (differentiableOn_dslope (isOpen_ball.mem_nhds (mem_ball_self h_R₁))).mpr hd
  have : g z = g z₀ := eqOn_of_isPreconnected_of_isMaxOn_norm (convex_ball c R₁).isPreconnected
    isOpen_ball g_diff h_z₀ g_max hz
  simp only [g] at this
  simp [g, ← this]
```
- as the PR leaves it:
```lean
theorem affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div [CompleteSpace E] [StrictConvexSpace ℝ E]
    (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : Set.MapsTo f (ball c R₁) (closedBall (f c) R₂))
    (h_z₀ : z₀ ∈ ball c R₁) (h_eq : ‖dslope f c z₀‖ = R₂ / R₁) :
    Set.EqOn f (fun z => f c + (z - c) • dslope f c z₀) (ball c R₁) := by
  set g := dslope f c
  rintro z hz
  have h_R₁ : 0 < R₁ := nonempty_ball.mp ⟨_, h_z₀⟩
  have g_le_div : ∀ z ∈ ball c R₁, ‖g z‖ ≤ R₂ / R₁ := fun z hz =>
    norm_dslope_le_div_of_mapsTo_ball hd h_maps hz
  have g_max : IsMaxOn (norm ∘ g) (ball c R₁) z₀ :=
    isMaxOn_iff.mpr fun z hz => by simpa [h_eq] using g_le_div z hz
  have g_diff : DifferentiableOn ℂ g (ball c R₁) :=
    (differentiableOn_dslope (isOpen_ball.mem_nhds (mem_ball_self h_R₁))).mpr hd
  have : g z = g z₀ := eqOn_of_isPreconnected_of_isMaxOn_norm (convex_ball c R₁).isPreconnected
    isOpen_ball g_diff h_z₀ g_max hz
  simp only [g] at this
  simp [g, ← this]
```

### `section in Schwarz.lean` (command, modified) [a5aadf83ae]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: namespace:modified
- before the PR:
```lean
variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℂ E] {R₁ R₂ : ℝ} {f : ℂ → E}
  {c z z₀ : ℂ}
```
- as the PR leaves it:
```lean
variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℂ E] {R R₁ R₂ : ℝ} {f : ℂ → E}
  {c z z₀ : ℂ}
```

### `Complex.norm_dslope_le_div_of_mapsTo_ball` (theorem, modified) [b7af217d85]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem norm_dslope_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (hz : z ∈ ball c R₁) :
    ‖dslope f c z‖ ≤ R₂ / R₁ := by
  have hR₁ : 0 < R₁ := nonempty_ball.1 ⟨z, hz⟩
  have hR₂ : 0 < R₂ := nonempty_ball.1 ⟨f z, h_maps hz⟩
  rcases eq_or_ne (dslope f c z) 0 with hc | hc
  · rw [hc, norm_zero]; exact div_nonneg hR₂.le hR₁.le
  rcases exists_dual_vector ℂ _ hc with ⟨g, hg, hgf⟩
  have hg' : ‖g‖₊ = 1 := NNReal.eq hg
  have hg₀ : ‖g‖₊ ≠ 0 := by simpa only [hg'] using one_ne_zero
  calc
    ‖dslope f c z‖ = ‖dslope (g ∘ f) c z‖ := by
      rw [g.dslope_comp, hgf, RCLike.norm_ofReal, abs_norm]
      exact fun _ => hd.differentiableAt (ball_mem_nhds _ hR₁)
    _ ≤ R₂ / R₁ := by
      refine schwarz_aux (g.differentiable.comp_differentiableOn hd) (MapsTo.comp ?_ h_maps) hz
      simpa only [hg', NNReal.coe_one, one_mul] using g.lipschitz.mapsTo_ball hg₀ (f c) R₂
```
- as the PR leaves it:
```lean
theorem norm_dslope_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (closedBall (f c) R₂)) (hz : z ∈ ball c R₁) :
    ‖dslope f c z‖ ≤ R₂ / R₁ := by
  have hR₁ : 0 < R₁ := nonempty_ball.1 ⟨z, hz⟩
  have hR₂ : 0 ≤ R₂ := nonempty_closedBall.mp ⟨f z, h_maps hz⟩
  rcases eq_or_ne (dslope f c z) 0 with hc | hc
  · rw [hc, norm_zero]; exact div_nonneg hR₂ hR₁.le
  rcases exists_dual_vector ℂ _ hc with ⟨g, hg, hgf⟩
  have hg' : ‖g‖₊ = 1 := NNReal.eq hg
  calc
    ‖dslope f c z‖ = ‖dslope (g ∘ f) c z‖ := by
      rw [g.dslope_comp, hgf, RCLike.norm_ofReal, abs_norm]
      exact fun _ => hd.differentiableAt (ball_mem_nhds _ hR₁)
    _ ≤ R₂ / R₁ := by
      refine schwarz_aux (g.differentiable.comp_differentiableOn hd) (MapsTo.comp ?_ h_maps) hz
      simpa only [hg', NNReal.coe_one, one_mul] using g.lipschitz.mapsTo_closedBall (f c) R₂
```

### `section in Schwarz.lean` (command, removed) [c0ba0edeab]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: namespace:removed
- before the PR:
```lean
variable {f : ℂ → ℂ} {c z : ℂ} {R R₁ R₂ : ℝ}
```

### `command in Schwarz.lean` (command, removed) [c5723657e8]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: value_or_body:removed
- before the PR:
```lean
@[expose] public section
```

### `Complex.norm_deriv_le_one_of_mapsTo_ball` (theorem, modified) [d45918c2b7]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem norm_deriv_le_one_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (ball c R)) (hc : f c = c) (h₀ : 0 < R) : ‖deriv f c‖ ≤ 1 :=
  (norm_deriv_le_div_of_mapsTo_ball hd (by rwa [hc]) h₀).trans_eq (div_self h₀.ne')
```
- as the PR leaves it:
```lean
theorem norm_deriv_le_one_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R))
    (h_maps : MapsTo f (ball c R) (closedBall (f c) R)) (h₀ : 0 < R) : ‖deriv f c‖ ≤ 1 :=
  (norm_deriv_le_div_of_mapsTo_ball hd h_maps h₀).trans_eq (div_self h₀.ne')
```

### `Complex.norm_dslope_le_div_of_mapsTo_ball` (theorem, removed) [e6d7733b14]
- file: `Mathlib/Analysis/Complex/Schwarz.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem norm_dslope_le_div_of_mapsTo_ball (hd : DifferentiableOn ℂ f (ball c R₁))
    (h_maps : MapsTo f (ball c R₁) (ball (f c) R₂)) (hz : z ∈ ball c R₁) :
    ‖dslope f c z‖ ≤ R₂ / R₁ := by
  have hR₁ : 0 < R₁ := nonempty_ball.1 ⟨z, hz⟩
  have hR₂ : 0 < R₂ := nonempty_ball.1 ⟨f z, h_maps hz⟩
  rcases eq_or_ne (dslope f c z) 0 with hc | hc
  · rw [hc, norm_zero]; exact div_nonneg hR₂.le hR₁.le
  rcases exists_dual_vector ℂ _ hc with ⟨g, hg, hgf⟩
  have hg' : ‖g‖₊ = 1 := NNReal.eq hg
  have hg₀ : ‖g‖₊ ≠ 0 := by simpa only [hg'] using one_ne_zero
  calc
    ‖dslope f c z‖ = ‖dslope (g ∘ f) c z‖ := by
      rw [g.dslope_comp, hgf, RCLike.norm_ofReal, abs_norm]
      exact fun _ => hd.differentiableAt (ball_mem_nhds _ hR₁)
    _ ≤ R₂ / R₁ := by
      refine schwarz_aux (g.differentiable.comp_differentiableOn hd) (MapsTo.comp ?_ h_maps) hz
      simpa only [hg', NNReal.coe_one, one_mul] using g.lipschitz.mapsTo_ball hg₀ (f c) R₂
```

## Removed or renamed

- `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`
- `section in Schwarz.lean`
- `module_doc in Schwarz.lean`
- `section in Schwarz.lean`
- `command in Schwarz.lean`
- `Complex.norm_dslope_le_div_of_mapsTo_ball`

## Families (declarations that may be one decision)

- [hypothesis] `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`, `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Complex.norm_deriv_le_div_of_mapsTo_ball`, `Complex.norm_deriv_le_one_of_mapsTo_ball`, `Complex.norm_dslope_le_div_of_mapsTo_ball`, `Complex.norm_le_norm_of_mapsTo_ball_self` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`, `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Complex.dist_le_dist_of_mapsTo_ball_self`, `Complex.dist_le_div_mul_dist_of_mapsTo_ball` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` -> `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'`
- changed_siblings [high]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` -> `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` -> `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`
- direct_use_of_changed_declaration [exact]: `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'` -> `Complex.affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`
- direct_use_of_changed_declaration [exact]: `Complex.dist_le_dist_of_mapsTo_ball_self` -> `Complex.dist_le_div_mul_dist_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.dist_le_div_mul_dist_of_mapsTo_ball` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.dist_le_div_mul_dist_of_mapsTo_ball` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.norm_deriv_le_div_of_mapsTo_ball` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.norm_deriv_le_div_of_mapsTo_ball` -> `Complex.norm_dslope_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.norm_deriv_le_one_of_mapsTo_ball` -> `Complex.norm_deriv_le_div_of_mapsTo_ball`
- direct_use_of_changed_declaration [exact]: `Complex.norm_dslope_le_div_of_mapsTo_ball` -> `Complex.schwarz_aux`
- direct_use_of_changed_declaration [exact]: `Complex.norm_dslope_le_div_of_mapsTo_ball` -> `Complex.schwarz_aux`
- direct_use_of_changed_declaration [exact]: `Complex.norm_le_norm_of_mapsTo_ball_self` -> `Complex.dist_le_dist_of_mapsTo_ball_self`
