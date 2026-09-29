# Review notes: PR #33149 (Galerkin regularity for Navier-Stokes on T³)

## Process

I read `brief.md`, `pr.md`, `model.md` (all objects, families, relations) and `diff.patch`, then
rebuilt the new file into `tmp/file.lean` to get line numbers. The workspace file tools
(`file_read`, `content_search`, `file_search`) could not see any Mathlib path from this
workspace. So I checked library facts with `declaration_search` and with `lean_verify_edit`
probes. Each probe either replaced the trailing `#check` and `#print axioms` lines
(467-469) with test declarations, or replaced one declaration. To print a lemma's type I forced
a type-mismatch error in an `example : False`. Every probe's arguments and output are in `tmp/`
(`t1`..`t11`, `.lean` / `.json` / `.out`).

As the PR leaves it, the file compiles (`as_is_compile_check`: compiles=true) with 17
unused-variable warnings. Those warnings pinpoint the vacuous definitions.

## Overall assessment

A maintainer would not merge this PR, and would most likely close it. The file has 19 `axiom`s,
one of them inconsistent (`False` is provable). The core definitions are placeholders:
`fourierDecay := True`, `spectralNSResidual := 0`, and `GalerkinProjection` ignores N and t. The
advertised main theorem is provable with no axioms by a one-line term. The module doc claims a
solution of 3D Navier-Stokes regularity. The findings list the concrete asks one target at a
time. Most are blocking.

## Object by object

- **File header / imports / options**: `import Mathlib` (blocking: import cycle, since
  `Mathlib.lean` must import the file). `set_option linter.style.commandStart false` (blocking;
  precedent #26644 queried a similar file-level linter disable). `#check` and `#print axioms` at
  the end (blocking). `Author:` should be `Authors:` (advisory). The file has no namespace, so
  every name lands in the root namespace (advisory, targeted at `T3`).
- **Module doc**: claims the file proves global existence and smoothness. That is false given
  the axioms and placeholders. Finding (documentation, blocking).
- **`T3`, `fourier1D`, `fourier3D`, `fourierCoeff3D`**: duplicate Mathlib's
  `UnitAddTorus`/`mFourier`/`mFourierCoeff`. `T3 = UnitAddTorus (Fin 3)` and
  `fourier3D k x = UnitAddTorus.mFourier k x` both close by `rfl`. `fourierCoeff3D` is not
  definitionally `mFourierCoeff` (different integrand form) but means the same thing. One
  finding targets `fourier3D`, one targets `T3` (namespace).
- **Constants `cMoser`, `cGronwall`, `cSobolev` and `_pos`**: axiomatised data, covered by
  the file-level "remove all axioms" finding. `cMoser`/`cMoser_pos` are used only by the
  unused `moser_estimate`.
- **`fourier_ortho_integral`**: proved from `orthonormal_fourier` (probe `probe_ortho_a`/`_b`
  compiled). Finding.
- **`fubini_torus3`**: equals `MeasureTheory.integral_fintype_prod_eq_prod (ι := Fin 3) f`
  (compiled). Finding.
- **`VorticityResponse`**: a structure with two reals and two facts. Nothing wrong in itself.
  The only uses are an unused argument of `bkm_finite_anyT` and the `TemporalLifting` parameter.
  Covered by the `bkm_finite_anyT` finding.
- **`fourierDecay` / `SmoothInitial`**: `True`, so `SmoothInitial u` is always true (compiled).
  Finding on `fourierDecay`.
- **`smoothInTime`**: `ContDiff ℝ ⊤` equals `ContDiff ℝ ω` by `Iff.rfl` and implies `AnalyticAt`
  (compiled), so it means analytic, not smooth. The fix `ContDiff ℝ (⊤ : ℕ∞)` recompiles the
  file. Finding. Its naming (Prop-valued, lowerCamelCase) is folded into the `Vorticity`
  naming finding.
- **`SmoothSpacetime`**: nothing separate. Its content collapses because of `fourierDecay` and
  `smoothInTime`.
- **`FourierCoeff`, `fourierTransform`, `DivergenceFree`, `spectralCurl`, `invFourier`**: I
  checked the formulas. `DivergenceFree` (k · û = 0) and `spectralCurl` (i k × û, with the
  index arithmetic in `Fin 3`) look right. `invFourier` uses a pointwise `∑'`, so it is junk (0)
  for non-ℓ¹ coefficients. That is the root of the `fourier_inversion`/`parseval_orthonormal`
  falsity, reported there. No separate finding.
- **`LerayProjection`, `fourierTruncate`**: never used. `fourierTruncate` is what
  `GalerkinProjection` should use, which is mentioned in that finding. `LerayProjection` gets
  only the naming comment. The formula is the standard one.
- **`spectralNSResidual` / `SolvesNavierStokes`**: the residual is `0`, so `SolvesNavierStokes`
  holds for all u, p (compiled). Finding.
- **`GalerkinProjection` / `GalerkinAt`**: ignore N and t. `GalerkinAt N u₀ t = GalerkinAt M u₀ 0`
  by `rfl` (compiled). Finding. Naming is covered in the `Vorticity` finding.
- **`l2Norm`, `linftyNorm`**: ad hoc, and `linftyNorm` is junk for unbounded fields. Suggest
  `eLpNorm` (advisory).
- **`BKMFinite`**: always true, `⟨_, le_rfl⟩` (compiled). Finding.
- **`fourier_inversion`, `parseval_orthonormal`**: false by the absolute-summability semantics
  of `∑'` in ℂ. The arguments are mathematical and I did not compile them. Mathlib's true
  versions are `hasSum_mFourier_series_of_summable` (with a summability hypothesis) and
  `hasSum_sq_mFourierCoeff`, whose types I printed. Two findings.
- **`bkm_implies_regularity`**: inconsistent. `probe_axioms_inconsistent : False` compiled,
  using `u x t j = |t|` and `not_differentiableAt_abs_zero`. Finding.
- **`fourierCoeff_summable`**: true mathematically (Bessel). Covered by the axioms finding and
  the `parseval3D` finding.
- **`integral_le_const_mul_length`**: unused, and false for non-integrable f with C < 0.
  Finding.
- **`vorticity_integrable`**: provable, but only because of the vacuous `GalerkinProjection`
  (`unfold Vorticity GalerkinProjection; simp` compiled). Mentioned as evidence in the axioms
  finding, not asked for separately, because once `GalerkinProjection` is fixed that proof no
  longer applies.
- **`hsNorm`**: a real-valued `∑'` inside `sqrt`, junk 0 off H^s. This makes `sobolev_embedding`
  (and `vorticity_hs_bound`) false. Finding on `sobolev_embedding`. The math argument was not
  compiled.
- **`moser_estimate`, `hs_gronwall_bound`, `vorticity_hs_bound`, `smooth_initial_hs_finite`**:
  covered by the axioms finding. `smooth_initial_hs_finite` is provable
  (`⟨_, le_rfl, Real.sqrt_nonneg _⟩` compiled). `hs_gronwall_bound` is also provable from the
  placeholder definitions (not compiled; not asked).
- **`TemporalLifting`**: a structure. `φ_deriv_cont` is needed only by the long proof of
  `tau_interval_finite`. `bkm_coordinate_invariance` still uses it via
  `integral_comp_mul_deriv`, so no removal is requested.
- **`fourier3D_orthogonal`**: should come from `UnitAddTorus.orthonormal_mFourier`. My
  integral-form derivation reduced to the goal but did not close, because the MeasureSpace
  instances on UnitAddCircle differ between the PR's context (`AddCircle.measureSpace 1`) and
  Mathlib's (`instMeasureSpaceUnitAddCircle`). The finding says so.
- **`parseval3D`**: duplicates `hasSum_sq_mFourierCoeff`. Finding.
- **`galerkin_energy_bound`**: `le_rfl` (compiled); `ht` is unused. Finding (advisory).
- **`uniform_vorticity_bound`**: `h_divfree` is unused (linter). Finding. The calc chain itself
  is fine given the axioms.
- **`bkmPhysical`, `bkmLifted`, `bkm_coordinate_invariance`**: the change-of-variables proof via
  `intervalIntegral.integral_comp_mul_deriv` is sound and uses no PR axiom. Only `hT` is unused
  (advisory finding). Nothing else.
- **`tau_interval_finite`**: correct but long. An 8-line proof via
  `mul_sub_le_image_sub_of_le_deriv` + `le_div_iff₀` compiled (declaration mode). Advisory golf.
- **`bkm_finite_anyT`**: `Φ` is unused (linter). Finding. The rest of the proof is fine, though
  the name `anyT` mixes camelCase into a snake_case name. I did not report that separately.
- **`VorticityResponse.regularity`, `GalerkinLimit.smooth`**: the main statement is provable with
  only the standard axioms (declaration-mode probe compiled, and the file's own `#print axioms`
  then showed propext/Quot.sound/Classical.choice). Finding on `GalerkinLimit.smooth`, which also
  asks to remove or restate `VorticityResponse.regularity`.

## Not reported

- File location (`Analysis/ODE` for a PDE result): moot given the rest.
- `DivergenceFree`, `spectralCurl`, `LerayProjection` formulas: checked, no error found.
- Tool reliability: `naming_norm` returned `subject_unresolved` for `Vorticity` and
  `bkm_finite_anyT`, so the naming finding rests on the stated Mathlib convention.
  `declaration_search` sometimes matches loosely (e.g. `FourierTransform.fourier`), so I did not
  claim a name clash for `fourierTransform`.
