# Review notes: PR #41314 (reviewer X2)

## Process
- I read brief.md, pr.md, model.md and diff.patch.
- `file_read` only resolves the reviewed tree under the `target/` prefix (`target/Mathlib/...`).
  I read the changed file `Angle/Sphere.lean` in full as the PR leaves it, and read
  `Sphere/Basic.lean` for the `IsDiameter` API: `IsDiameter.wbtw`, `IsDiameter.sbtw (hr : s.radius ≠ 0)`,
  `isDiameter_iff_mem_and_mem_and_wbtw`, `center_mem_iff`, `norm_vsub_center_eq_radius`.
- I ran `lean_verify_edit` with no edit: the file compiles, with no errors or warnings.
- `naming_norm` returned `subject_unresolved` for both lemmas, so naming is unmeasured and I judged it by hand.
- `proof_profile` was unavailable (no declaration table for the base commit).
- `precedent_search` on the zero lemma returned nothing directly applicable. The top hits were a Thales
  docstring comment, `ofDiameter` protection and a Triangle golf.

## `EuclideanGeometry.Sphere.angle_center_eq_pi_iff_isDiameter`
- Correctness and hypotheses: `hr` is needed only for (←). With radius 0 the endpoints coincide with the
  center and the angle is π/2, so the iff would be false without `hr`. `hp₁` and `hp₂` are needed for (→),
  because Sbtw alone does not put `p₂` on the sphere. `hr : s.radius ≠ 0` matches the form used by
  `IsDiameter.sbtw`. I see nothing to weaken.
- Duplication: I searched Geometry for central-angle π/0 statements and for `IsDiameter` together with
  angle. There are no existing equivalents. `angle_eq_pi_iff_sbtw` and `isDiameter_iff_mem_and_mem_and_wbtw`
  are reused correctly.
- Proof: two lines using the canonical API. A term-mode `.trans` would be only cosmetic, so I asked
  for no golf.
- Naming: `angle_center_eq_pi_iff_isDiameter` matches the file's `oangle_center_*` naming and the
  `isDiameter` spelling. Fine.
- Docstring: accurate. Placement: correct, next to the Thales lemmas in the unoriented `namespace Sphere`
  block.
- Style: uses `fun h =>`, reported in finding 2 (verified with `↦`).
- I considered and did not submit a dot-notation counterpart `IsDiameter.angle_center_eq_pi` for (←),
  which needs no membership hypotheses. It would be an addition rather than a fix, and I have no evidence
  that a maintainer would demand it.

## `EuclideanGeometry.Sphere.angle_center_eq_zero_iff_eq`
- Correctness: `hr` is needed for (←), since `angle_self_of_ne` requires `p₁ ≠ center`. `hp₂` is needed
  for (→). The statement is fine.
- Proof golf (finding 1): `by simpa [angle] using h` is redundant because `h` elaborates directly
  (verified). A full term-mode proof compiles (verified). An alternative via
  `dist_eq_abs_sub_dist_of_angle_eq_zero` also compiles.
- Naming: the `_iff_eq` suffix follows patterns such as `vsub_eq_zero_iff_eq`. Not worth a request.
- Generalization: the forward direction holds for any two points equidistant from a point, not only on a
  sphere. `EuclideanGeometry.eq_of_angle_eq_zero_of_dist_eq` does not exist at base. I did not submit a
  request to add a general `_of_dist_eq` version: it is plausible, but speculative for a two-lemma
  sphere PR.
- Docstring accurate. Placement fine.

## Doc comments (4bdc75980d, a388bdc930)
- Both docstrings correctly state the hypotheses (nonzero radius) and the conclusion. No change requested.

## File-level
- Style: both new lemmas use `fun h =>` where the surrounding code and mathlib style use `↦` (finding 2).
- The module docstring is generic ("results about angles in circles and spheres") and needs no update.
