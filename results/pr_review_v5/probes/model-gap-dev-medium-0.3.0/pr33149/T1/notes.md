# Review notes: PR #33149 (Galerkin regularity for Navier-Stokes on T³)

One new file, `Mathlib/Analysis/ODE/GalerkinRegularity.lean`, 469 lines. I read `pr.md`, `model.md` (every
object plus the families/relations) and `diff.patch`, then used the tools. Every Lean claim below was checked
with `lean_verify_edit` against the PR workspace. Args and outputs are in `tmp/*.json`.

## Whole-file checks
- As-is compile: it compiles, with 17 unused-variable warnings (fourierDecay ×5, spectralNSResidual ×5,
  SolvesNavierStokes `p`, GalerkinProjection `N`/`t`, galerkin_energy_bound `ht`, uniform_vorticity_bound
  `h_divfree`, bkm_coordinate_invariance `hT`, bkm_finite_anyT `Φ`). Mathlib CI fails on warnings.
- `#print axioms GalerkinLimit.smooth` (the file's own command) depends on 9 custom axioms.
- **Inconsistency (verified).** `BKMFinite` is trivially true, so `bkm_implies_regularity` makes every
  function `ContDiff ℝ ⊤`. A 3-line proof of `False` via `|t|` and `not_differentiableAt_abs_zero` compiled.
- Vacuity (verified): `BKMFinite ω T`, `SmoothInitial u` and `SolvesNavierStokes ν u p` hold for all arguments,
  and `GalerkinAt N u₀ t = u₀` by rfl. So the main theorem says nothing about Navier-Stokes.
- `smoothInTime` uses `ContDiff ℝ ⊤` = `ContDiff ℝ ω` (analytic). Proved by rfl; the `∞` version compiles.
- Imports: `#min_imports` gives `Mathlib.Analysis.CStarAlgebra.Classes` and `Mathlib.Analysis.Fourier.AddCircle`.
  Swapping them in for `import Mathlib` compiles.
- Module system: `Mathlib.lean` starts with `module`, and the file is not registered there. With `module` added,
  `#print axioms` is a hard error and the linter asks for `@[expose] public section`.
- Removing `set_option linter.style.commandStart false` together with `open scoped InnerProductSpace`
  compiles; the `open` is unused. The linter then flags 4 spacing issues (`^2`, `3/2`, `5/2` ×2).
- The header line reads `Author:`. Mathlib's header linter requires `Authors: `, but it only runs on files
  that `Mathlib.lean` imports, which is why the as-is compile shows no warning.
- Zulip: Kudryashov (maintainer) says a PR with an `axiom` command will be declined.

## Object by object
- Axioms (19): policy violation. Of these, `fubini_torus3` is `integral_fintype_prod_volume_eq_prod` and
  `fourier_ortho_integral` follows from `orthonormal_fourier` (both verified by compiling replacements).
  `fourier_inversion`, `parseval_orthonormal` and `integral_le_const_mul_length` are false as stated, because
  a non-summable tsum or a non-integrable integral takes the junk value 0. `smooth_initial_hs_finite` is
  provable without its hypothesis. `integral_le_const_mul_length`, `moser_estimate`, `cMoser`,
  `cMoser_pos` and `smooth_initial_hs_finite` are unused.
- `T3`, `fourier3D`, `fourierCoeff3D`, `fourier3D_orthogonal`, `parseval3D`: duplicate `UnitAddTorus`,
  `mFourier`, `mFourierCoeff`, `orthonormal_mFourier` and `hasSum_sq_mFourierCoeff` (AddCircleMulti.lean).
- `fourier1D`: a bare alias of `fourier`.
- `fourierDecay`, `spectralNSResidual`, `BKMFinite`, `GalerkinProjection`: vacuous or constant (findings).
  `fourierTruncate` and `LerayProjection` are never used.
- `SmoothInitial`, `SmoothSpacetime`, `SolvesNavierStokes`: vacuous through the definitions above. I filed no
  separate finding beyond the ones on their constituents.
- `DivergenceFree`, `fourierTransform`, `invFourier`, `hsNorm`, `FourierCoeff`: nothing separate to request.
  The definitions are plausible spectral encodings. `hsNorm` inherits the junk-tsum issue, which I covered
  under the axioms finding rather than filing it separately.
- `spectralCurl`: `% 3` on `Fin 3` is a no-op (verified by `decide`). Advisory.
- `l2Norm` / `linftyNorm`: reinvent `eLpNorm`, and `linftyNorm` is junk 0 for unbounded f. Advisory.
- `Vorticity`, `GalerkinAt`, `LerayProjection`, `GalerkinProjection`: data defs in UpperCamelCase.
  `fourierDecay` and `smoothInTime`: Props in lowerCamelCase. One naming finding.
- `VorticityResponse`: the docstring promises a functional, but there is no function field. Advisory.
- `TemporalLifting`: nothing separately requested. It is only used by `bkm_coordinate_invariance` and
  `tau_interval_finite`, and those are used by nothing.
- `fourier3D_orthogonal`: the proof is fine given its axioms; filed as a duplication finding.
- `parseval3D`: duplication of Mathlib's Parseval, built on false axioms.
- `galerkin_energy_bound`: `rfl` only because the projection is constant; `ht` unused.
- `uniform_vorticity_bound`: `h_divfree` unused. The calc itself is fine given the axioms. Small golfs
  (`(cSobolev_pos s).le`, `gcongr`) were not worth filing.
- `bkm_coordinate_invariance`: `hT` unused. Otherwise it is a correct use of `integral_comp_mul_deriv`.
- `tau_interval_finite`: the 30-line proof golfs to 9 lines via `mul_sub_le_image_sub_of_le_deriv` +
  `le_div_iff₀` (verified). This also removes the need for `φ_deriv_cont`.
- `bkm_finite_anyT`: `Φ` unused, so the temporal-lifting idea is decorative. Its last step
  (`rw [integral_const, ...]`) is fine.
- `VorticityResponse.regularity` / `GalerkinLimit.smooth`: rest on the inconsistent axiom and vacuous
  definitions; `_hν` is unused. These are covered by the findings above, with no separate request.
- Module docstring: claims a proof of global regularity, which is false. Filed.
- `#check` / `#print axioms`: must go. Filed.

29 findings in `findings.json`.
