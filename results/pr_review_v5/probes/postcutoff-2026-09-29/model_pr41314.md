# The PR model for #41314 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Geometry/Euclidean/Angle/Sphere): central angle equals π iff diameter, 0 iff equal points
- description: Add two lemmas characterising the two degenerate values of the central angle
`∠ p₁ s.center p₂` on a sphere of nonzero radius:

* `EuclideanGeometry.Sphere.angle_center_eq_pi_iff_isDiameter`: the central angle
  is `π` iff `p₁` and `p₂` are the endpoints of a diameter (`s.IsDiameter p₁ p₂`).
* `EuclideanGeometry.Sphere.angle_center_eq_zero_iff_eq`: the central angle is `0`
  iff `p₁ = p₂`.
- changed files: Mathlib/Geometry/Euclidean/Angle/Sphere.lean

## Objects

### `EuclideanGeometry.Sphere.angle_center_eq_zero_iff_eq` (theorem, added) [30c743b971]
- file: `Mathlib/Geometry/Euclidean/Angle/Sphere.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem angle_center_eq_zero_iff_eq {s : Sphere P} {p₁ p₂ : P}
    (hp₁ : p₁ ∈ s) (hp₂ : p₂ ∈ s) (hr : s.radius ≠ 0) :
    ∠ p₁ s.center p₂ = 0 ↔ p₁ = p₂ := by
  constructor
  · intro h
    refine vsub_left_cancel (eq_of_angle_eq_zero_of_norm_eq (by simpa [angle] using h) ?_)
    rw [norm_vsub_center_eq_radius hp₁, norm_vsub_center_eq_radius hp₂]
  · rintro rfl
    exact angle_self_of_ne fun h => hr (center_mem_iff.mp (h ▸ hp₁))
```

### `doc_comment in Sphere.lean` (command, added) [4bdc75980d]
- file: `Mathlib/Geometry/Euclidean/Angle/Sphere.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- On a sphere of nonzero radius, the central angle `∠ p₁ s.center p₂` equals `π` iff
`p₁` and `p₂` are diametrically opposite. -/
```

### `EuclideanGeometry.Sphere.angle_center_eq_pi_iff_isDiameter` (theorem, added) [61083ee4c2]
- file: `Mathlib/Geometry/Euclidean/Angle/Sphere.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem angle_center_eq_pi_iff_isDiameter {s : Sphere P} {p₁ p₂ : P}
    (hp₁ : p₁ ∈ s) (hp₂ : p₂ ∈ s) (hr : s.radius ≠ 0) :
    ∠ p₁ s.center p₂ = π ↔ s.IsDiameter p₁ p₂ := by
  rw [angle_eq_pi_iff_sbtw]
  exact ⟨fun h => isDiameter_iff_mem_and_mem_and_wbtw.2 ⟨hp₁, hp₂, h.wbtw⟩, fun h => h.sbtw hr⟩
```

### `doc_comment in Sphere.lean` (command, added) [a388bdc930]
- file: `Mathlib/Geometry/Euclidean/Angle/Sphere.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- On a sphere of nonzero radius, the central angle `∠ p₁ s.center p₂` equals zero iff
`p₁ = p₂`. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `EuclideanGeometry.Sphere.angle_center_eq_pi_iff_isDiameter`, `EuclideanGeometry.Sphere.angle_center_eq_zero_iff_eq` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- none
