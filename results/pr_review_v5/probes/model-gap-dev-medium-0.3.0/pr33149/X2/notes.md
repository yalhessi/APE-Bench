# Review notes: PR #33149, `Mathlib/Analysis/ODE/GalerkinRegularity.lean`

## What I did

I read `brief.md`, `pr.md`, `model.md` (80+ objects, 4 families, the change graph) and `diff.patch`
(one new file, 469 lines). Then I used the tools:

- **As-is compile** (`lean_verify_edit`, no edit): the file compiles. It emits 17 `unusedVariables`
  warnings, which fail Mathlib CI, where warnings are errors.
- **Consistency probes** (`lean_verify_edit`, line mode, replacing the trailing `#check` / `#print axioms`):
  - Proved `False` from `bkm_implies_regularity`: `BKMFinite` is trivially true, and `u x t j = |t|`
    contradicts `not_differentiableAt_abs_zero`.
  - Proved `False` from `integral_le_const_mul_length`, using `f t = -t⁻¹ - 1`,
    `intervalIntegrable_inv_iff` and `integral_undef`.
  - Proved `SolvesNavierStokes ν u p` for all ν, u, p by `rfl`.
  - Proved `SmoothInitial u` for all u by `trivial`.
  - Proved `BKMFinite ω T` for all ω, T by `⟨_, le_rfl⟩`.
  - Proved `smoothInTime f ↔ ContDiff ℝ ω f` by `Iff.rfl`, so it means analytic, not C^∞.
  - Proved `T3 = UnitAddTorus (Fin 3)`, `fourier3D k x = UnitAddTorus.mFourier k x` and
    `fourier1D n = fourier n`, each by `rfl`.
- **Declaration-mode edits:**
  - `fubini_torus3` as a theorem `:= MeasureTheory.integral_fintype_prod_volume_eq_prod f`: success.
  - `tau_interval_finite` golfed through `mul_sub_le_image_sub_of_le_deriv`: success.
  - `bkm_finite_anyT` proved by `⟨_, le_rfl⟩`: no Lean errors. The harness flagged "Forbidden axioms
    used: bkm_implies_regularity" from the file's own `#print axioms GalerkinLimit.smooth`, which after
    this change lists only `bkm_implies_regularity` beyond the standard three.
  - A shorter `bkm_coordinate_invariance` failed: the `rw` did not match the `(ω ∘ L.φ)` form. I did not
    pursue it, and that finding asks only to drop the unused `hT`.
- **Commented out `set_option linter.style.commandStart false`** (set it to `true`): the linter reports
  `^2` → ` ^ 2`, `3/2` → `3 / 2`, `5/2` → `5 / 2`, and the `#print axioms` column.
- **Library lookups** (declaration_search, file_read, content_search):
  - `Mathlib/Analysis/Fourier/AddCircleMulti.lean` already has `UnitAddTorus`, `mFourier`,
    `mFourierCoeff`, `orthonormal_mFourier`, `hasSum_sq_mFourierCoeff` and
    `hasSum_mFourier_series_apply_of_summable`.
  - `Mathlib/MeasureTheory/Integral/Pi.lean` has `integral_fintype_prod_volume_eq_prod`.
  - `hasDerivAt_fourier` gives the 2π factor.
  - Sibling headers (`Gronwall.lean`, `AddCircleMulti.lean`) use `module` / `public import` /
    `@[expose] public section` and `Authors:`.
  - `Mathlib.lean` is a module and lists only Gronwall and PicardLindelof under `Analysis.ODE`.
- **Search tools that found nothing:**
  - `naming_norm` on five lemma names: subject unresolved or no population, so there was no naming
    census to cite.
  - `zulip_search` and `precedent_search` returned nothing that bears on this code.

## Object by object

**File-level**
- `import Mathlib` / no `module`: finding (blocking).
- Not in `Mathlib.lean`: finding (blocking).
- `#check` / `#print axioms`: finding (blocking).
- `set_option linter.style.commandStart false`: finding (blocking).
- `Author:` should be `Authors:`: finding (advisory).
- 19 axioms: finding (blocking).
- `open scoped InnerProductSpace` is unused, but it is harmless and moot once the imports are trimmed,
  so no finding.
- The file sits in `Analysis/ODE` although its content is PDE. I left this out as moot, since the
  content should not land at all.

**Module docs**
- Main module doc claims NS global regularity and a temporal-lifting proof: finding (blocking).
- Section headers (`## Axioms (after definitions they reference)` and others) need no separate
  finding; they go with the axioms.

**Axioms**
- `bkm_implies_regularity`: inconsistent, finding.
- `integral_le_const_mul_length`: inconsistent and unused, finding.
- `fubini_torus3`: an existing Mathlib lemma, verified, finding.
- `fourier_inversion`: stronger than the true theorem (no summability hypothesis), finding.
- `fourier_ortho_integral`, `parseval_orthonormal`, `fourierCoeff_summable`: covered by the
  file-level axiom finding and the `fourier3D_orthogonal` / `parseval3D` duplication findings.
- `cMoser`, `cGronwall`, `cSobolev`, their `_pos` facts, `moser_estimate`, `hs_gronwall_bound`,
  `sobolev_embedding`, `vorticity_hs_bound`, `smooth_initial_hs_finite`, `vorticity_integrable`:
  covered by the file-level axiom finding.
  - `cMoser`, `cMoser_pos`, `cGronwall_pos`, `moser_estimate` and `smooth_initial_hs_finite` are unused.
  - I did not try to derive `False` from `sobolev_embedding`. It looks false for bounded non-measurable
    fields, where the Fourier coefficients are junk 0, but I did not construct that case.

**Definitions**
- `T3`: duplicates `UnitAddTorus (Fin 3)`, finding.
- `fourier1D` / `fourier3D`: duplicate `fourier` / `mFourier`, one finding on `fourier3D`.
- `fourierCoeff3D`: duplicates `mFourierCoeff`, finding.
- `fourierTransform`: nothing separate. It becomes `mFourierCoeff` under the `fourierCoeff3D` finding.
- `FourierCoeff` abbrev: no finding.
- `fourierDecay`: `True`, finding (blocking), with the casing noted.
- `SmoothInitial`: vacuous through `fourierDecay`; covered there.
- `smoothInTime`: means analytic, finding.
- `SmoothSpacetime`: no separate finding; covered by `smoothInTime` and `fourierDecay`.
- `DivergenceFree`: checked the formula (∑ k_j û_j = 0) and it is fine up to the 2π convention. No
  finding.
- `LerayProjection`: formula checked (f − (k·f)k/|k|²), fine, but unused. Covered by the
  `GalerkinProjection` finding.
- `spectralNSResidual` / `SolvesNavierStokes`: `0`, finding (blocking).
- `fourierTruncate`: unused; covered by the `GalerkinProjection` finding.
- `GalerkinProjection` / `GalerkinAt`: constant `u₀`, finding (blocking), plus a casing finding.
- `spectralCurl`: 2π missing and a redundant `% 3`, finding.
- `invFourier`, `Vorticity`: no finding beyond casing. `invFourier` uses `tsum` junk values, but it only
  feeds axioms.
- `l2Norm` / `linftyNorm`: ad hoc norms with junk values, one finding on `linftyNorm`.
- `BKMFinite`: trivially true, finding (blocking).
- `hsNorm`: `tsum` with junk value 0 when not summable, as with `linftyNorm`. It is used only inside
  axioms, so I raised no separate finding.
- `bkmPhysical` / `bkmLifted`: part of the unused temporal-lifting block (the `TemporalLifting` finding).
- `VorticityResponse`: docstring describes a functional that is not there, finding.
  - Field names `hmin_pos` / `hbounds` are unidiomatic (they would be `φ_min_pos` / `φ_min_le_φ_max`),
    but too minor next to everything else, so no finding.
- `TemporalLifting`: unused by any result outside its own block, scope finding.

**Lemmas and theorems**
- `fourier3D_orthogonal`: duplicates `orthonormal_mFourier`, finding. Its `ortho1D` and
  `have …; obtain` steps could be golfed, which is moot.
- `parseval3D`: duplicates `hasSum_sq_mFourierCoeff`, finding.
- `galerkin_energy_bound`: `rfl` by construction, unused `ht`, finding.
- `uniform_vorticity_bound`: unused `h_divfree`, finding. The proof is otherwise a plain chaining of
  axioms; the `gcongr` / `.le` golf is mentioned in passing.
- `bkm_coordinate_invariance`: unused `hT`, finding. The proof is a correct use of
  `integral_comp_mul_deriv`.
- `tau_interval_finite`: verified golf, finding.
- `bkm_finite_anyT`: unused `Φ`; the proof reduces to `⟨_, le_rfl⟩`. Finding.
- `VorticityResponse.regularity`: same statement as the main theorem, with an ignored Φ, finding.
- `GalerkinLimit.smooth`: vacuous, and depends on an inconsistent axiom. Finding (blocking). The
  missing `GalerkinLimit` namespace type is mentioned inside it rather than as a separate rename,
  because the theorem should be removed.

## Summary

This PR claims to settle 3D Navier-Stokes global regularity. It does so by trivial definitions
(`True`, `0`, a time-constant "Galerkin" field) together with 19 axioms, at least two of which prove
`False`. The Fourier-analytic layer duplicates `Mathlib/Analysis/Fourier/AddCircleMulti.lean`.

I wrote 33 findings: 15 blocking, 18 advisory.
