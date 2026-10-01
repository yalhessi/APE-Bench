import json
P = "Mathlib/Analysis/ODE/GalerkinRegularity.lean"
F = []
def f(line, sev, claim, fix):
    F.append({"path": P, "line_start": line, "claim": claim, "suggested_fix": fix, "severity": sev})

# ---- inconsistent / false axioms and the no-axiom policy ----
f(193, "blocking",
  "`bkm_implies_regularity` is an inconsistent axiom. Its hypothesis `BKMFinite (...) T` holds for every `u` and `T` (take `M` to be the integral itself), so the axiom says `SmoothSpacetime u` for every `u : T3 → ℝ → Fin 3 → ℝ`. With `u x t j = |t|` the second conjunct gives `ContDiff ℝ ⊤ (fun t => |t|)`, which contradicts `not_differentiableAt_abs_zero`. Checked in this file: `have h : ContDiff ℝ ⊤ (fun t : ℝ => |t|) := (bkm_implies_regularity (fun _ t _ => |t|) 0 ⟨_, le_rfl⟩).2 0 0; exact not_differentiableAt_abs_zero (h.differentiable le_top 0)` proves `False`. Every result that depends on it, `GalerkinLimit.smooth` included, carries no information.",
  "Delete the axiom `bkm_implies_regularity`. Mathlib accepts no `axiom` declarations. The Beale-Kato-Majda criterion can only come in as a proved theorem about fields that actually solve the Navier-Stokes system, with that as a hypothesis.")
f(201, "blocking",
  "`integral_le_const_mul_length` is a false axiom that proves `False`. It has no integrability hypothesis, and the interval integral of a non-integrable function is `0`. Take `f t = -1 - t⁻¹`, `C = -1`, `T = 1`: the bound holds on `Icc 0 1`, `intervalIntegral.integral_undef` with `intervalIntegrable_inv_iff` makes the integral `0`, and the axiom then gives `0 ≤ -1`. This derivation compiles in this file. The axiom is also unused, since `bkm_finite_anyT` uses `intervalIntegral.integral_mono_on`.",
  "Delete `integral_le_const_mul_length`. Where a bound of this kind is needed, use `intervalIntegral.integral_mono_on` with an `IntervalIntegrable` hypothesis, followed by `intervalIntegral.integral_const`, as `bkm_finite_anyT` already does.")
f(50, "blocking",
  "`cMoser`, `cGronwall`, `cSobolev` and `cMoser_pos`, `cGronwall_pos`, `cSobolev_pos` are declared with `axiom`, like the analytic estimates that use them. Mathlib does not accept `axiom` declarations: an axiom extends the trusted base with no proof. The file's own `#print axioms GalerkinLimit.smooth` lists these next to `propext`, `Classical.choice` and `Quot.sound`.",
  "Remove every `axiom` from the file. Drop the opaque constant functions and quantify the constant inside each estimate, proved as a theorem: `∃ C > 0, ∀ u, ... ≤ C * ...`. An estimate that cannot be proved yet should not be in the PR.")
f(187, "blocking",
  "`fourier_inversion` is false. A `tsum` in `ℂ` is unconditional and `‖fourier3D k x‖ = 1`, so `∑' k, fourierCoeff3D f k * fourier3D k x` is summable only when `∑ ‖fourierCoeff3D f k‖ < ∞`; otherwise its value is `0`. Some continuous functions have Fourier coefficients that are not absolutely summable, for example `f x = g (x 0)` with `g t = ∑ sin (2πnt) / (n log n)`. For such an `f` the axiom gives `f x = 0` at every `x`. Mathlib's correct version, `UnitAddTorus.hasSum_mFourier_series_apply_of_summable`, assumes `Summable (mFourierCoeff f)`.",
  "Delete the axiom. Where pointwise Fourier inversion is needed, use `UnitAddTorus.hasSum_mFourier_series_apply_of_summable` together with its summability hypothesis.")
f(190, "blocking",
  "`parseval_orthonormal` is false. Take `c` square-summable but not summable, for example `c (n, 0, 0) = 1 / (|n| + 1)` and `0` elsewhere. Then `∑' k, c k * fourier3D k x` is not summable at any `x`, so the left side is `∫ x, ‖0‖ ^ 2 = 0` while the right side `∑' k, ‖c k‖ ^ 2` is positive. Parseval holds for the L²-convergent series, not for the pointwise `tsum`.",
  "Delete the axiom. Parseval on the torus is `UnitAddTorus.hasSum_sq_mFourierCoeff`, and the L² convergence of the series is `UnitAddTorus.hasSum_mFourier_series_L2`.")
f(249, "blocking",
  "`sobolev_embedding` is false, because `hsNorm` takes the junk value `0` when its series diverges. Let `f x = (v (x 0), 0, 0)` where the step function `v` is `1` on half the circle and `-1` on the other half. Its Fourier coefficients have size `~1/n` along one axis, so for `s - 1 > 3/2` the H^{s-1} series diverges and `hsNorm (s - 1) f = 0`, yet `linftyNorm f = 1`.",
  "Delete the axiom. A Sobolev embedding has to assume that the H^{s-1} series is summable (or use an `ℝ≥0∞`-valued norm), and it has to be proved.")
f(252, "blocking",
  "`vorticity_hs_bound` is false even for trigonometric polynomials, because `hsNorm` weights by `‖(fun i => (k i : ℝ))‖`, which is the sup norm on `Fin 3 → ℝ`. Take `u x = 2 cos (2π (x₀ + x₁ + x₂)) • (1, -1, 0)`, with modes `±(1, 1, 1)` of sup norm `1`. The squared `hsNorm (s - 1)` of its curl is `12 · 2^(s-1)`, but the squared `hsNorm s u` is `8 · 2^(s-1)`. The bound also fails whenever the H^s series of `u` diverges (so the right side is `0`) while that of its curl converges.",
  "Delete the axiom. If an estimate of this form is kept, give it the Euclidean weight `1 + ∑ i, (k i : ℝ) ^ 2`, add the summability hypotheses, and prove it.")
f(240, "blocking",
  "`moser_estimate` is false, and nothing uses it. Take `u x = (v (x 0), 0, 0)` with `v` a `±1` step function. Then `fun x j => ∑ i, u x i * u x j` is the constant field `(1, 0, 0)`, whose `hsNorm s` is `1`. But the H^s series of `u` diverges for `s > 3/2`, so `hsNorm s u = 0` and the right side is `0`.",
  "Delete `moser_estimate`, and with it `cMoser` and `cMoser_pos`.")

# ---- axioms that are Mathlib theorems / provable ----
f(69, "blocking",
  "`fubini_torus3` is declared as an axiom, but it is a special case of a Mathlib theorem. `MeasureTheory.integral_fintype_prod_volume_eq_prod f` proves exactly this statement, and the replacement compiles in this file.",
  "Replace the axiom with `theorem fubini_torus3 (f : Fin 3 → UnitAddCircle → ℂ) : ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y := MeasureTheory.integral_fintype_prod_volume_eq_prod f`, or call that lemma directly at its single use in `fourier3D_orthogonal`.")
f(66, "blocking",
  "`fourier_ortho_integral` is declared as an axiom, but it is Mathlib's `orthonormal_fourier` written as an integral. This proof compiles in this file: `have h := (orthonormal_iff_ite.mp (orthonormal_fourier (T := 1))) m n; rw [MeasureTheory.ContinuousMap.inner_toLp] at h; rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]; simpa [mul_comm, eq_comm] using h`.",
  "Make `fourier_ortho_integral` a `theorem` with that proof, or derive the needed orthogonality from `orthonormal_fourier` at the use site.")
f(198, "blocking",
  "`fourierCoeff_summable` is an axiom, but it is Bessel's inequality, which Mathlib already proves: for continuous `f` it is `(UnitAddTorus.hasSum_sq_mFourierCoeff (f.toLp 2 volume ℂ)).summable`, rewritten with `UnitAddTorus.mFourierCoeff_toLp`.",
  "Delete the axiom and get summability from `UnitAddTorus.hasSum_sq_mFourierCoeff` (and `mFourierCoeff_toLp`), with `mFourierCoeff` in place of `fourierCoeff3D`.")
f(256, "blocking",
  "`smooth_initial_hs_finite` is an axiom with a trivial proof: take `M := hsNorm s u₀`, and the norm is a `Real.sqrt`. `⟨_, le_rfl, Real.sqrt_nonneg _⟩` proves it in this file, and the hypothesis `h` then comes up as unused. No declaration uses it.",
  "Delete `smooth_initial_hs_finite`.")
f(205, "blocking",
  "`vorticity_integrable` is an axiom with a trivial proof. `GalerkinProjection` ignores `t`, so the integrand does not depend on `t`, and `intervalIntegrable_const (c := linftyNorm fun x => Vorticity (GalerkinProjection N u₀) x 0)` proves it in this file.",
  "Replace the axiom with that one-line proof (keeping it as a `theorem`). Once `GalerkinProjection` really evolves in time, prove integrability from continuity in `t` instead.")
f(244, "blocking",
  "`hs_gronwall_bound` is an axiom, but with the placeholder `GalerkinAt` it follows from the definitions alone. `fun _ _ => le_mul_of_one_le_right (Real.sqrt_nonneg _) <| Real.one_le_exp <| mul_nonneg (mul_nonneg (cGronwall_pos s).le hT.le) (Real.sqrt_nonneg _)` proves it in this file, and leaves `hs` and `hu₀` unused. So it carries no Gronwall content.",
  "Delete the axiom. A real H^s Gronwall bound has to be proved for a Galerkin system that actually evolves.")

# ---- vacuous definitions ----
f(180, "blocking",
  "`BKMFinite ω T := ∃ M, ∫ t in 0..T, ω t ≤ M` holds for every `ω` and `T`: the Bochner integral is always a real number (`0` when `ω` is not integrable), so `M` can be the integral itself. `⟨_, le_rfl⟩ : BKMFinite ω T` compiles. It does not say that the Beale-Kato-Majda integral is finite.",
  "Define finiteness so that it can fail, e.g. `IntervalIntegrable ω volume 0 T` or `∫⁻ t in Set.Ioc 0 T, ‖ω t‖ₑ < ∞`.")
f(137, "blocking",
  "`spectralNSResidual` is the constant `0`; the linter reports all five of its arguments as unused. So `SolvesNavierStokes ν u p` holds for every `ν`, `u`, `p` (`fun _ _ _ _ => rfl` proves it in this file). `SolvesNavierStokes` also never uses the pressure `p` (another unused-variable warning). The PR's conclusion that the field solves Navier-Stokes is vacuous.",
  "Define the residual as the real equation, e.g. in Fourier variables `∂ₜ û k + ν (2π)² ‖k‖² û k + LerayProjection (transform of (u · ∇) u) k`, with a time-differentiability requirement. Make `SolvesNavierStokes` use `p`, or state it in Leray form and drop `p`.")
f(92, "blocking",
  "`fourierDecay` is defined as `True`, and the linter reports all five arguments as unused. So `SmoothInitial u` holds for every `u` (`fun _ => ⟨0, fun _ _ => trivial⟩` proves it in this file). The main theorem's hypothesis `h_smooth` and the first conjunct of `SmoothSpacetime` are therefore vacuous.",
  "Give the decay condition its real content, e.g. `‖fourierTransform u k j‖ ≤ C * (1 + ‖k‖) ^ (-(n : ℝ))`. Better still, define smoothness directly as `ContDiff ℝ ∞` of the periodic lift, and delete `fourierDecay`.")
f(150, "blocking",
  "`GalerkinProjection N u₀ := fun x t j => u₀ x j` ignores both `N` and `t` (both are flagged as unused). It is neither a Fourier truncation nor a time evolution, just `u₀` frozen in time. `VorticityResponse.regularity` uses `GalerkinProjection 1 u₀` as its \"solution\", and `galerkin_energy_bound`, `vorticity_integrable` and `hs_gronwall_bound` hold only because of this. Meanwhile `fourierTruncate` and `LerayProjection` are defined and never used.",
  "Define the Galerkin approximation as the solution of the truncated system `d/dt û = fourierTruncate N (LerayProjection (...))` with initial data `fourierTruncate N (fourierTransform u₀)`. Otherwise delete `GalerkinProjection` and `GalerkinAt` together with the unused `fourierTruncate` and `LerayProjection`.")
f(100, "blocking",
  "`smoothInTime f := ContDiff ℝ ⊤ f` asks for analyticity, not smoothness. `ContDiff` takes `n : WithTop ℕ∞`, and there `⊤` is `ω` (`scoped[ContDiff] notation3 \"ω\" => (⊤ : WithTop ℕ∞)` in `FTaylorSeries.lean`). The docstring \"Smooth function of time\" is therefore wrong.",
  "Write `ContDiff ℝ ∞ f` under `open scoped ContDiff`. The spelled-out form `ContDiff ℝ ((⊤ : ℕ∞) : WithTop ℕ∞) f` compiles here.")
f(104, "blocking",
  "`SmoothSpacetime u` does not express space-time smoothness. Its first conjunct is `SmoothInitial`, which is vacuous because `fourierDecay` is `True`. Its second only asks that `t ↦ u x t j` be smooth for each fixed `x`, separately; it says nothing about joint regularity in `(x, t)` or about spatial derivatives.",
  "Require joint smoothness, e.g. `ContDiff ℝ ∞ (fun p : (Fin 3 → ℝ) × ℝ => u (fun i => (p.1 i : UnitAddCircle)) p.2)` on the periodic lift, restricted to `t ≥ 0` if needed.")
f(453, "blocking",
  "`GalerkinLimit.smooth` neither states nor proves regularity for Navier-Stokes. `SolvesNavierStokes` and `SmoothInitial` are true for all inputs, the witness is `u₀` frozen in time, and `SmoothSpacetime u` comes from the inconsistent axiom `bkm_implies_regularity`. Yet its docstring and the PR description present it as global existence and smoothness for Navier-Stokes on T³.",
  "Remove `GalerkinLimit.smooth`, and `VorticityResponse.regularity` with it. A statement like this can only be proposed once `SolvesNavierStokes`, `SmoothInitial` and the Galerkin scheme are the real notions and the proof uses no axioms.")

# ---- file-level policy ----
f(6, "blocking",
  "The file imports `Mathlib`. A Mathlib file cannot import the root `Mathlib` module: that module must import every file, this one included, so registering this file would create an import cycle. The PR does not add the file to `Mathlib.lean` either, as the `mk_all` check requires. It also lacks the `module` header and `public import` form that its siblings `Gronwall.lean` and `PicardLindelof.lean` use.",
  "Start the file with `module`. Replace `import Mathlib` by `public import`s of just the modules the file uses (e.g. `Mathlib.Analysis.Fourier.AddCircleMulti`; find the rest with `#min_imports`), wrap the declarations in `@[expose] public section`, and add `public import Mathlib.Analysis.ODE.GalerkinRegularity` to `Mathlib.lean`.")
f(467, "blocking",
  "`#check GalerkinLimit.smooth` and `#print axioms GalerkinLimit.smooth` are left at the end of the file. `#`-commands are development aids: they print on every build, and Mathlib's `linter.hashCommand` flags them when warnings are errors, as in CI.",
  "Delete both lines.")
f(37, "blocking",
  "`set_option linter.style.commandStart false` turns off a Mathlib style linter for the whole file, which hides formatting errors. With the linter on, it flags `‖c k‖^2` in `parseval_orthonormal`, and `3/2` or `5/2` in `moser_estimate`, `hs_gronwall_bound` and `sobolev_embedding`.",
  "Delete the `set_option` and fix the spacing it hides: `‖c k‖ ^ 2`, `3 / 2`, `5 / 2`, and likewise `^ 2` in `l2Norm`, `hsNorm`, `fourierCoeff_summable`, `parseval3D` and `LerayProjection`.")
f(4, "blocking",
  "The copyright header says `Author: Jeffrey Camlin`. Mathlib's header linter requires that line to begin with `Authors: `.",
  "Change the line to `Authors: Jeffrey Camlin`.")
f(8, "blocking",
  "The module docstring says that \"This file proves global existence and smoothness of solutions to the incompressible Navier-Stokes equations on T³\", which would settle a Millennium Prize problem. The file proves nothing of the kind: its definitions are placeholders and its proofs rest on axioms. The \"Main results\" list also counts structures as results, and the references are not given as `docs/references.bib` keys.",
  "Rewrite the module docstring to describe only what the file actually formalises, with no claim of Navier-Stokes regularity, and cite references by `docs/references.bib` keys.")

# ---- unused hypotheses (warnings are errors in Mathlib CI) / golf ----
f(306, "blocking",
  "`galerkin_energy_bound` has an unused hypothesis `ht : 0 ≤ t` (a linter warning, which Mathlib CI treats as an error). Its proof `unfold GalerkinAt GalerkinProjection; rfl` shows it is just `le_refl`: the lemma holds only because `GalerkinProjection` ignores time.",
  "Remove `ht` and make the proof `le_rfl`; this compiles.")
f(315, "blocking",
  "`uniform_vorticity_bound` never uses `h_divfree : DivergenceFree u₀`, which triggers an unused-variable warning. The bound comes entirely from the axioms `sobolev_embedding`, `vorticity_hs_bound` and `hs_gronwall_bound`.",
  "Remove the `h_divfree` hypothesis from `uniform_vorticity_bound` and from its call in `bkm_finite_anyT`.")
f(407, "blocking",
  "`bkm_finite_anyT` takes `Φ : VorticityResponse` and never uses it (unused-variable warning). The intermediate `bound` only restates `hC N`. Because `BKMFinite` is vacuous, the whole lemma is `⟨_, le_rfl⟩`.",
  "Drop the `Φ` argument, also at its call in `VorticityResponse.regularity`, and use `hC N t` directly instead of the `bound` step.")
f(353, "blocking",
  "`bkm_coordinate_invariance` has an unused hypothesis `hT : 0 ≤ T` (unused-variable warning). The lemma itself is `intervalIntegral.integral_comp_mul_deriv` specialised to `L.φ`, and its proof re-derives that in two `have`s.",
  "Drop `hT` and shorten the proof to `have := intervalIntegral.integral_comp_mul_deriv (a := 0) (b := τ_T) (fun x _ => (L.φ_diff x).hasDerivAt) L.φ_deriv_cont.continuousOn hω_cont; rw [L.φ_zero, hτ] at this; simp only [bkmPhysical, bkmLifted, h_relation]; exact this.symm`, which compiles.")
f(371, "advisory",
  "In `tau_interval_finite`, the last step is a five-line `calc` (`τ_T * 1`, `div_self`, two `ring` steps, `div_le_div_of_nonneg_right`) plus the auxiliary `hne`, all to turn `Φ.φ_min * τ_T ≤ T` into `τ_T ≤ T / Φ.φ_min`.",
  "Replace the `hne` line and the `calc` with `rw [le_div_iff₀ Φ.hmin_pos]; linarith`; this compiles.")
f(432, "advisory",
  "`VorticityResponse.regularity` has exactly the conclusion of `GalerkinLimit.smooth`. Its argument `Φ` is only passed on to `bkm_finite_anyT`, which ignores it, and `ν`/`_hν` are unused (silenced with `_`). The result is two theorems with one statement, one of them taking an argument that does nothing.",
  "Keep one theorem: delete `VorticityResponse.regularity`, and drop the `Φ` and `hν` arguments from whatever remains.")

# ---- duplication of Mathlib's torus Fourier API ----
f(41, "advisory",
  "`T3 := Fin 3 → UnitAddCircle` duplicates Mathlib's `UnitAddTorus (Fin 3)` (`Mathlib/Analysis/Fourier/AddCircleMulti.lean`). A root-level name `T3` also reads like the separation axiom `T3Space`.",
  "Use `UnitAddTorus (Fin 3)` throughout and delete `T3`.")
f(112, "advisory",
  "`fourier1D n` is `fourier n` under another name; the proof of `fourier3D_orthogonal` has to unfold it again.",
  "Delete `fourier1D` and write `fourier` directly.")
f(116, "advisory",
  "`fourier3D k` duplicates `UnitAddTorus.mFourier k`, which is the same product `∏ i, fourier (k i) (x i)` bundled as a continuous map, with `mFourier_add`, `mFourier_neg`, `mFourier_norm` already proved.",
  "Delete `fourier3D` and use `UnitAddTorus.mFourier`.")
f(120, "advisory",
  "`fourierCoeff3D` duplicates `UnitAddTorus.mFourierCoeff` (`∫ t, mFourier (-n) t • f t`, which equals the PR's integrand by `mFourier_neg`).",
  "Delete `fourierCoeff3D` and use `UnitAddTorus.mFourierCoeff`.")
f(263, "advisory",
  "`fourier3D_orthogonal` restates `UnitAddTorus.orthonormal_mFourier` as an integral, and proves it through two axioms (`fourier_ortho_integral`, `fubini_torus3`) that Mathlib already proves. Its `ortho1D` `have` merely repeats `fourier_ortho_integral`.",
  "Delete the lemma and use `UnitAddTorus.orthonormal_mFourier`, via `MeasureTheory.ContinuousMap.inner_toLp` if the integral form is needed.")
f(293, "blocking",
  "`parseval3D` states a true identity, but its proof goes through the false axioms `fourier_inversion` and `parseval_orthonormal`. For continuous `f` the statement is Mathlib's Parseval, `UnitAddTorus.hasSum_sq_mFourierCoeff`, applied to `f.toLp 2 volume ℂ`.",
  "Delete `parseval3D`, or derive it from `UnitAddTorus.hasSum_sq_mFourierCoeff` applied to `f.toLp 2 volume ℂ` (via `HasSum.tsum_eq`, `mFourierCoeff_toLp` and `ContinuousMap.coeFn_toLp`), with `mFourierCoeff` in place of `fourierCoeff3D`. Either way, no axiom should be involved.")
f(176, "advisory",
  "`linftyNorm f := ⨆ x j, |f x j|` is `0` for every unbounded `f`, since an unbounded `iSup` in `ℝ` is `0`. It is also a pointwise supremum rather than an essential supremum. So it is not the L∞ norm its docstring names, and it duplicates Mathlib's `MeasureTheory.eLpNorm f ∞ volume`.",
  "Use `MeasureTheory.eLpNorm f ∞ volume`, or the sup norm on `C(UnitAddTorus (Fin 3), _)`, instead of a new definition.")
f(172, "advisory",
  "`l2Norm` re-implements the L² norm by hand as `Real.sqrt (∫ x, ∑ j, (f x j) ^ 2)`, and returns `0` for non-integrable fields. Mathlib already has this norm as `MeasureTheory.eLpNorm f 2 volume`, and as the `Lp` norm.",
  "Delete `l2Norm` and state energy bounds with `eLpNorm f 2 volume` on `EuclideanSpace ℝ (Fin 3)`-valued fields.")
f(211, "blocking",
  "`hsNorm` returns `0` whenever its series diverges (the junk value of `tsum`). So `hsNorm s f ≤ M` does not mean `f ∈ H^s`, and every rough field gets norm `0`; this is what makes `sobolev_embedding`, `moser_estimate` and `vorticity_hs_bound` false. It also weights by `‖(fun i => (k i : ℝ))‖`, the sup norm on `Fin 3 → ℝ`, instead of the Euclidean `|k|`.",
  "Make the norm `ℝ≥0∞`-valued (`(∑' k, (1 + ∑ i, (k i : ℝ) ^ 2) ^ s * ∑ j, ‖û k j‖ₑ ^ 2) ^ (1/2)`), or pair it with a `Summable` membership predicate, and use the Euclidean weight `∑ i, (k i : ℝ) ^ 2`.")

# ---- naming / namespace / docs / scope / style ----
f(164, "advisory",
  "`Vorticity`, `GalerkinProjection`, `GalerkinAt` and `LerayProjection` are UpperCamelCase, but they define functions, not `Prop`s or types. Mathlib names term-valued definitions in lowerCamelCase, as this file already does for `spectralCurl`, `invFourier` and `fourierTransform`.",
  "Rename them to `vorticity`, `galerkinProjection`, `galerkinAt` and `lerayProjection`.")
f(100, "advisory",
  "`smoothInTime` and `fourierDecay` are `Prop`-valued but lowerCamelCase. Mathlib names `Prop`-valued definitions in UpperCamelCase, as this file does for `SmoothInitial`, `DivergenceFree` and `BKMFinite`.",
  "Rename them to `SmoothInTime` and `FourierDecay`.")
f(109, "advisory",
  "All of the file's declarations sit in the root namespace under generic names (`T3`, `l2Norm`, `linftyNorm`, `hsNorm`, `Vorticity`, `fourierTransform`, `FourierCoeff`). `FourierCoeff` differs from Mathlib's root-level `fourierCoeff` only by capitalisation, and `fourierTransform` clashes with the `FourierTransform`/`𝓕` API.",
  "Put the declarations in a namespace (e.g. `NavierStokes`) and rename `FourierCoeff` to something that is not a case variant of `fourierCoeff` (e.g. `NavierStokes.SpectralField`).")
f(77, "advisory",
  "The docstring of `VorticityResponse` says \"A bounded vorticity-response functional Φ : ℝ≥0 → [φ_min, φ_max]\", but the structure holds no function: only two reals with `0 < φ_min ≤ φ_max`. `GalerkinLimit.smooth` instantiates it with `1` and `2`, and nothing depends on the values.",
  "Rewrite the docstring to say what the structure is, a pair of bounds `0 < φ_min ≤ φ_max` for the derivative of a time reparametrisation, or delete the structure along with the unused `TemporalLifting` part.")
f(220, "advisory",
  "`TemporalLifting`, `bkmPhysical`, `bkmLifted`, `bkm_coordinate_invariance` and `tau_interval_finite` are used by no other declaration. They are the \"temporal lifting\" half that the module docstring presents as the proof method, yet the main theorem never passes through them.",
  "Remove these declarations from the PR. As general change-of-variables facts they could go in a separate PR, if wanted.")
f(154, "advisory",
  "In `spectralCurl`, `(j + 1) % 3` and `(j + 2) % 3` reduce modulo `3 = 0` in `Fin 3`, so `% 3` does nothing: addition in `Fin 3` already wraps around.",
  "Write `let j1 := j + 1` and `let j2 := j + 2`.")
f(38, "advisory",
  "`open scoped InnerProductSpace` is unused: the file uses neither `⟪·, ·⟫` nor `inner`.",
  "Delete the line.")

notes = r"""
Overall: this PR adds a single new file that claims global regularity for 3D Navier-Stokes on the torus, which would settle a Millennium Prize problem. It is not mergeable. The file declares 22 `axiom`s, and two of them prove `False`; I checked both derivations with lean_verify_edit (bkm_implies_regularity via |t|; integral_le_const_mul_length via -1 - t⁻¹). The key predicates are placeholders (`fourierDecay := True`, `spectralNSResidual := 0`, `BKMFinite` trivially true; all three checked), and `GalerkinProjection` is `u₀` frozen in time. The main theorem therefore says nothing. A maintainer would close it. I list the concrete asks per declaration anyway. The file compiles as left (13 s), with 17 unused-variable warnings, which are errors under Mathlib CI.

Header / file (line 4 copyright, line 6 import, line 8 module doc, lines 37-38 options, lines 467/469 commands):
- `Author:` must be `Authors:` (header linter). Asked.
- `import Mathlib` cannot appear in a Mathlib file; the file also lacks the `module`/`public import` header its siblings in Analysis/ODE use, and it is not registered in `Mathlib.lean` (checked: only Gronwall and PicardLindelof are listed). Asked.
- The module doc claims a proof of NS regularity, which is false and misleading. Asked. Placement: there is no PDE directory, and an ODE folder is wrong for this; I left that unasked, because the content should not land at all.
- `set_option linter.style.commandStart false`: I re-enabled the linter in a test edit. It flags `^2` and `3/2`/`5/2` spacing. Asked.
- `open scoped InnerProductSpace`: unused (no ⟪⟫ or inner in the file). Asked.
- `#check` and `#print axioms`: remove. Asked.

Constant axioms cMoser/cGronwall/cSobolev and their _pos versions: policy, since Mathlib accepts no axioms; constants should be existential inside proved estimates. Asked once at cMoser, for the family.

Fourier family:
- `fourier_ortho_integral` (axiom): proved from `orthonormal_fourier` in 4 lines (verified). Asked.
- `fubini_torus3` (axiom): one line, `integral_fintype_prod_volume_eq_prod` (verified). Asked.
- `T3`: duplicate of `UnitAddTorus (Fin 3)`. Asked.
- `fourier1D`: is `fourier`. Asked.
- `fourier3D`: duplicate of `mFourier`. Asked.
- `fourierCoeff3D`: duplicate of `mFourierCoeff`. Asked.
- `fourierTransform` and `FourierCoeff`: root namespace, name clash with `fourierCoeff`/`FourierTransform`. Asked at FourierCoeff, together with the namespace ask.
- `invFourier`: `.re` of a pointwise tsum carries the same junk-value problem; it is covered by the hsNorm, fourier_inversion and parseval asks, so nothing separate.
- `fourier_inversion` (axiom): false (tsum in ℂ is unconditional; continuous functions with non-ℓ¹ coefficients exist); Mathlib's version needs `Summable`. Asked.
- `parseval_orthonormal` (axiom): false for ℓ²∖ℓ¹ coefficients. Asked.
- `fourierCoeff_summable` (axiom): true; it is Bessel via `hasSum_sq_mFourierCoeff`. Asked.
- `fourier3D_orthogonal`: duplicate of `orthonormal_mFourier`; proved via axioms. Asked. Golfing its proof is moot once it is replaced.
- `parseval3D`: the statement is true, but the proof uses false axioms; Mathlib has it. Asked.

Definitions:
- `fourierDecay`/`SmoothInitial`: vacuous (verified `SmoothInitial u` holds for every u). Asked at fourierDecay; the naming ask covers fourierDecay; SmoothInitial's name is fine.
- `smoothInTime`: `⊤` is ω, i.e. analytic (verified the notation in FTaylorSeries.lean, and that the `∞` version compiles). Asked; naming asked separately.
- `SmoothSpacetime`: no joint regularity, and its first conjunct is vacuous. Asked.
- `DivergenceFree`: the formula is fine (k·û = 0). It is unused in every proof (`h_divfree` is unused in uniform_vorticity_bound). Nothing beyond that ask.
- `LerayProjection`, `fourierTruncate`: correct-looking formulas, never used. Folded into the GalerkinProjection ask; LerayProjection is also in the naming ask.
- `spectralNSResidual`/`SolvesNavierStokes`: vacuous (verified), and `p` is unused. Asked at spectralNSResidual.
- `GalerkinProjection`/`GalerkinAt`: ignore N and t. Asked; naming asked at Vorticity.
- `spectralCurl`: the components are correct for i k×û; the `% 3` is redundant. Asked (advisory).
- `Vorticity`: the definition is fine given the other pieces; it is in the lowerCamelCase naming ask.
- `l2Norm`, `linftyNorm`: hand-rolled norms with junk values; Mathlib has `eLpNorm`. Asked.
- `hsNorm`: junk 0 when not summable; sup-norm weight. Asked.
- `BKMFinite`: vacuous (verified). Asked.
- `bkmPhysical`, `bkmLifted`: plain integrals; unused outside the lifting lemmas. Covered by the scope ask at TemporalLifting.
- `VorticityResponse`: the docstring does not match the fields. Asked. `TemporalLifting`: unused by the main result. Scope asked. Its fields could be bundled as `ContDiff ℝ 1 φ`; not asked, because the whole part should be removed.

Analytic axioms:
- `bkm_implies_regularity`: inconsistent (verified False). Asked.
- `integral_le_const_mul_length`: inconsistent (verified False), unused. Asked.
- `vorticity_integrable`: provable by `intervalIntegrable_const` (verified). Asked.
- `moser_estimate`: false (±1 step function), unused. Asked.
- `hs_gronwall_bound`: provable from the placeholder definitions (verified). Asked.
- `sobolev_embedding`: false because of the hsNorm junk value. Asked.
- `vorticity_hs_bound`: false (sup-norm weight; explicit trig counterexample, 12·2^(s-1) > 8·2^(s-1)). Asked.
- `smooth_initial_hs_finite`: trivially provable (verified), unused. Asked.

Lemmas:
- `galerkin_energy_bound`: unused `ht`; `le_rfl` works (verified). Asked.
- `uniform_vorticity_bound`: unused `h_divfree`. Asked. The first calc step by `rfl` is fine; the rest is a chain of axioms.
- `bkm_coordinate_invariance`: unused `hT`; a 4-line proof via `integral_comp_mul_deriv` compiles without hT (verified). Asked.
- `tau_interval_finite`: the closing calc golfs to `rw [le_div_iff₀ Φ.hmin_pos]; linarith` (verified). Asked, advisory. The FTC part is fine.
- `bkm_finite_anyT`: unused `Φ` (linter); `bound` is redundant. Asked. The name `anyT` is non-standard, but the lemma should go together with the vacuous BKMFinite, so I did not ask for a rename.
- `VorticityResponse.regularity`: duplicates the statement of GalerkinLimit.smooth; Φ and ν do nothing. Asked.
- `GalerkinLimit.smooth`: vacuous main theorem resting on an inconsistent axiom. Asked to remove it. The name (a `GalerkinLimit` namespace with no such object) is also poor; I did not ask for a rename, since the theorem should be removed.
"""

sub = {"notes": notes.strip(), "findings": F}
out = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/post-carryover-replan/results/pr_review_v5/probes/contract-2026-10-01/swap/pr33149/S1/submission.json"
with open(out, "w", encoding="utf-8") as fh:
    json.dump(sub, fh, ensure_ascii=False, indent=1)
print(len(F))
