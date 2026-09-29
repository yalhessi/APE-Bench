# Review notes: PR #41314 (reviewer X1)

## Setup
- Read `pr.md`, `model.md`, `diff.patch`, then `ptool describe`.
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it (no errors, no warnings).
- The workspace files are under the `target/` prefix for `file_read` / `content_search`
  (a bare `Mathlib/...` path returned "File not found").
- Read `target/Mathlib/Geometry/Euclidean/Angle/Sphere.lean` lines 1-260 and the `IsDiameter`
  API in `target/Mathlib/Geometry/Euclidean/Sphere/Basic.lean` (lines 255-352, 580-622).

## `EuclideanGeometry.Sphere.angle_center_eq_pi_iff_isDiameter`
- Correctness: sound. The forward direction needs both memberships (`Sbtw p₁ c p₂` with only
  `p₁ ∈ s` does not force `p₂ ∈ s`); the reverse needs `hr` (radius 0 makes the angle π/2).
  `hr : s.radius ≠ 0` matches `IsDiameter.sbtw`.
- Duplication: `content_search` for `∠ … s.center … = π/0` over `Mathlib/Geometry/Euclidean`
  found nothing but the PR's own lemmas; `declaration_search` confirmed that the lemmas the proof
  uses (`angle_eq_pi_iff_sbtw`, `isDiameter_iff_mem_and_mem_and_wbtw`, `IsDiameter.sbtw`) are
  pre-existing.
- Generalization (finding 2): the reverse direction needs only `IsDiameter` + `hr`; the iff forces
  redundant `hp₁ hp₂`. A lemma `IsDiameter.angle_center_eq_pi := (h.sbtw hr).angle₁₂₃_eq_pi` was
  verified with `lean_verify_edit` (success).
- Proof: `rw [angle_eq_pi_iff_sbtw]; exact ⟨…⟩` is already short; a `.trans` term form exists
  but is not worth a separate ask.
- Naming: `naming_norm` could not resolve a subject (unmeasured). `_iff_isDiameter` matches
  siblings (`center_mem_affineSpan_pair_iff_isDiameter`). No ask.
- Docstring: accurate. No ask.
- Placement: `Sphere/Basic.lean` does not import unoriented angles, so `Angle/Sphere.lean` is the
  right file; the lemmas sit in the unoriented `Sphere` section next to the Thales lemmas. No ask.

## `EuclideanGeometry.Sphere.angle_center_eq_zero_iff_eq`
- Correctness: sound. Forward: equal norms plus angle 0 give equal vectors; reverse needs
  `p₁ ≠ s.center`, obtained from `hr` via `center_mem_iff`.
- Proof-golf (finding 1): `(by simpa [angle] using h)` can be just `h` (definitional unfolding).
  Both a minimal edit and a full term proof were verified with `lean_verify_edit` (success).
- Generalization, considered and not raised: the forward direction does not need `hr`, so a
  separate `eq_of_angle_center_eq_zero` without `hr` would be possible. I judged this less likely
  to be asked than the `IsDiameter` form.
- Duplication: no point-level `eq_of_angle_eq_zero_of_dist_eq` exists (only the vector lemmas
  `eq_of_angle_eq_zero_of_norm_eq` and `eq_of_angle_eq_zero`). No ask.
- Naming: `_eq_zero_iff_eq` is rare in Mathlib (only `smul_eq_zero_iff_eq`), and `dist_eq_zero`
  style omits the suffix. But `_iff_eq` is descriptive and parallel to the sibling
  `_iff_isDiameter`, and `naming_norm` was unmeasured. No ask.
- Docstring: accurate. No ask.

## The two doc comments
- Both are accurate and describe the hypotheses ("On a sphere of nonzero radius"). No ask.

## File `Mathlib/Geometry/Euclidean/Angle/Sphere.lean`
- Style (finding 3): the new code uses `fun h =>` three times; the file already uses `fun h ↦`,
  and the style guide slightly prefers `↦` (zulip_search: the style-guide quote).
- Module docstring ("results about angles in circles and spheres") still covers the additions.

## Tools used
`describe`, `lean_verify_edit` (as-is, 3 edits, all successful), `file_read`, `file_search`,
`content_search`, `declaration_search`, `naming_norm` (both unresolved), `precedent_search`,
`zulip_search`.
