import json, sys
D = sys.argv[1]
F = []
def add(target, claim, change, sev, ev):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev, "evidence": ev})

FILE = "Mathlib/Analysis/ODE/GalerkinRegularity.lean"
B1 = ("lean_verify_edit (lines 467-469 replaced by a block of examples) returned outcome=compiled, "
      "success=true, 0 errors, 0 new warnings")

# ---- PR level -------------------------------------------------------------
add("PR #33149 (as a whole)",
    "The PR presents a proof of global regularity for 3D Navier-Stokes (a Clay Millennium problem), but the file is unrevised generated scaffolding. "
    "The argument rests on 19 `axiom`s, one of which proves `False`. The notions in the statement are placeholders: `fourierDecay := True`, "
    "`spectralNSResidual := 0`, `GalerkinProjection` constant in time, and `BKMFinite` true for every function. Debugging commands "
    "(`#check`, `#print axioms`) and working headings (\"Axioms (after definitions they reference)\") are left in.",
    "Close the PR rather than review it line by line. Any further contribution should be a small, axiom-free change the author can explain and revise, "
    "for example new API about Fourier series on `UnitAddTorus`, written to Mathlib's standards.",
    "blocking",
    "Convention: LLM-generated code the submitter cannot revise is closed (and the AI-cleanup convention). " + B1 + " for: "
    "`example : False` from `bkm_implies_regularity (fun _ t _ => |t|) 0 ⟨_, le_rfl⟩` plus `not_differentiableAt_abs_zero`; "
    "`BKMFinite ω T := ⟨_, le_rfl⟩`; `SmoothInitial u := fun _ ↦ ⟨0, fun _ _ ↦ trivial⟩`; `SolvesNavierStokes ν u p := fun _ _ _ _ ↦ rfl`; "
    "and the main statement proved for arbitrary `ν u₀` with no hypotheses. Zulip (Yury Kudryashov, maintainer, 2025-05-03): "
    "\"As for axioms, we will definitely decline a PR with an `axiom` command.\"")

add("PR #33149 description",
    "The description does not say whether or how AI was used. The file has the marks of generated text: a section headed "
    "\"Axioms (after definitions they reference)\", placeholder definitions (`True`, `0`), `#check`/`#print axioms` left at the end, and a "
    "docstring claiming a Millennium-problem result.",
    "Add a statement to the PR description, as the Mathlib AI-use policy requires, of whether AI tools were used to write this PR and how.",
    "blocking",
    "Convention: AI-assisted PRs disclose this and how in the description. pr.md has only the two-sentence description and no disclosure. diff.patch lines 186 and 467-469.")

add("PR #33149 title and description",
    "The title \"Galerkin regularity for Navier-Stokes on T³\" and the description (\"global existence and smoothness for Galerkin approximations\", "
    "main result `GalerkinLimit.smooth`) do not describe the change. No Galerkin approximation or limit is constructed: `GalerkinProjection N u₀` "
    "is `u₀` held constant in time, whatever `N` is. Nothing about Navier-Stokes is proved, because `SolvesNavierStokes` is true for every `u`.",
    "Retitle and rewrite the description to state what the file actually contains: placeholder definitions plus axioms. Better, close the PR (see the PR-level finding).",
    "advisory",
    "Convention: the PR title and description say precisely what the change is. " + B1 + " for `GalerkinProjection N u₀ x t = GalerkinProjection M u₀ x s := rfl` and the main statement proved with no hypotheses.")

# ---- axioms ----------------------------------------------------------------
add(FILE,
    "The file adds 19 `axiom` declarations: cMoser, cGronwall, cSobolev, cMoser_pos, cGronwall_pos, cSobolev_pos, fourier_ortho_integral, "
    "fubini_torus3, fourier_inversion, parseval_orthonormal, bkm_implies_regularity, fourierCoeff_summable, integral_le_const_mul_length, "
    "vorticity_integrable, moser_estimate, hs_gronwall_bound, sobolev_embedding, vorticity_hs_bound and smooth_initial_hs_finite. Mathlib does not accept axioms.",
    "Remove every `axiom`. Results already in the library should be used directly (see the per-axiom findings). Genuine analytic inputs "
    "(Sobolev embedding, Moser and Gronwall estimates) should either be proved or become explicit hypotheses of the lemmas that use them; "
    "an unproved target statement may be recorded with `proof_wanted`.",
    "blocking",
    "grep '^axiom' on the diff gives 19 lines (50-256). Zulip (Yury Kudryashov, maintainer): \"we will definitely decline a PR with an `axiom` command.\" "
    "At least three of the axioms are false or inconsistent (separate findings).")

add("bkm_implies_regularity",
    "The axiom `bkm_implies_regularity` is inconsistent. `BKMFinite ω T` (`∃ M, ∫ t in 0..T, ω t ≤ M`) holds for every `ω`, so the axiom says every "
    "`u : T3 → ℝ → Fin 3 → ℝ` is `SmoothSpacetime`, and in particular that `t ↦ |t|` is `ContDiff ℝ ⊤`. That gives a proof of `False`, "
    "and from it every downstream theorem, including `GalerkinLimit.smooth`.",
    "Delete `bkm_implies_regularity`. The Beale-Kato-Majda criterion cannot be postulated; it must be proved, or taken as an explicit hypothesis with a correctly defined `BKMFinite`.",
    "blocking",
    B1 + " for:\n`example : False := by\n  have h := bkm_implies_regularity (fun _ t _ => |t|) 0 ⟨_, le_rfl⟩\n  have hc : ContDiff ℝ ⊤ (fun t : ℝ => |t|) := h.2 0 0\n  exact not_differentiableAt_abs_zero (hc.differentiable le_top 0)`")

add("fourier_inversion",
    "The axiom `fourier_inversion` is false. It asserts pointwise inversion `f x = ∑' k, fourierCoeff3D f k * fourier3D k x` for every continuous `f`. "
    "In `ℂ`, `tsum` of a non-summable family is `0`, and `‖fourierCoeff3D f k * fourier3D k x‖ = ‖fourierCoeff3D f k‖`. So for a continuous `f` "
    "whose coefficients are not absolutely summable (which exist), the axiom forces `f x = 0` at every `x`.",
    "Delete the axiom. Use `UnitAddTorus.hasSum_mFourier_series_apply_of_summable`, which carries the hypothesis `Summable (mFourierCoeff f)`, "
    "and add that hypothesis wherever inversion is needed.",
    "blocking",
    "declaration_search: `UnitAddTorus.hasSum_mFourier_series_apply_of_summable` is at Mathlib/Analysis/Fourier/AddCircleMulti.lean:267 (base). "
    "file_read shows it takes `(h : Summable (mFourierCoeff f))`. The falsity argument is mathematical; it was not compiled.")

add("parseval_orthonormal",
    "The axiom `parseval_orthonormal` is false. It assumes only `Summable (‖c k‖^2)`, but `∑' k, c k * fourier3D k x` is not summable at any `x` "
    "when `c ∈ ℓ² \\ ℓ¹`, because `‖fourier3D k x‖ = 1`. Then the left side is `∫ ‖0‖^2 = 0`, while the right side is positive. "
    "An example is `c k = 1 / (1 + ‖k‖²)` on `ℤ³`.",
    "Delete the axiom. State Parseval with the library's L² machinery: `UnitAddTorus.hasSum_sq_mFourierCoeff (f : L²(UnitAddTorus d))`.",
    "blocking",
    "declaration_search: `UnitAddTorus.hasSum_sq_mFourierCoeff` is at AddCircleMulti.lean:239 (base), with statement `HasSum (fun i ↦ ‖mFourierCoeff f i‖ ^ 2) (∫ t, ‖f t‖ ^ 2)`. "
    "The counterexample is mathematical; it was not compiled.")

add("fubini_torus3",
    "The axiom `fubini_torus3` is an existing library theorem: `MeasureTheory.integral_fintype_prod_volume_eq_prod` states the same thing, with no integrability hypothesis.",
    "Delete `fubini_torus3` and use `MeasureTheory.integral_fintype_prod_volume_eq_prod f` at its use site in `fourier3D_orthogonal`.",
    "blocking",
    B1 + " for `example (f : Fin 3 → UnitAddCircle → ℂ) : ∫ x : T3, ∏ i, f i (x i) = ∏ i, ∫ y : UnitAddCircle, f i y := "
    "MeasureTheory.integral_fintype_prod_volume_eq_prod f`. Signature read at Mathlib/MeasureTheory/Integral/Pi.lean:114.")

add("fourier_ortho_integral",
    "The axiom `fourier_ortho_integral` restates `orthonormal_fourier` for `T = 1` and is provable in four lines.",
    "Replace the axiom by this theorem, or by direct use of `orthonormal_fourier`:\n"
    "`theorem fourier_ortho_integral (n m : ℤ) : ∫ x : UnitAddCircle, fourier n x * star (fourier m x) = if n = m then 1 else 0 := by\n"
    "  have h := orthonormal_iff_ite.mp (orthonormal_fourier (T := 1)) m n\n"
    "  rw [MeasureTheory.ContinuousMap.inner_toLp] at h\n"
    "  rw [AddCircle.volume_eq_smul_haarAddCircle, ENNReal.ofReal_one, one_smul]\n"
    "  simpa [mul_comm, eq_comm] using h`",
    "blocking",
    "lean_verify_edit (appended example) compiled this proof with no error at its lines. The run's single reported error was in a separate first variant, using `convert`, which was discarded.")

add("integral_le_const_mul_length",
    "The axiom `integral_le_const_mul_length` is never used. It is also a consequence of library lemmas: `bkm_finite_anyT` already proves the same "
    "bound with `intervalIntegral.integral_mono_on` and `intervalIntegral.integral_const`.",
    "Delete `integral_le_const_mul_length`.",
    "blocking",
    "Its name appears in the diff only at its declaration (line 201). bkm_finite_anyT (lines 407-425) proves the bound from library lemmas.")

add("moser_estimate",
    "Several axioms are declared and never used: `moser_estimate`, `cMoser`, `cMoser_pos`, `cGronwall_pos` and `smooth_initial_hs_finite`. Nothing in the file refers to them.",
    "Remove these unused declarations, together with all the other axioms.",
    "blocking",
    "Convention: a lemma added by a PR is used, tagged or part of its API, or else removed. Searching the diff, each name occurs only at its own declaration "
    "(cMoser also inside moser_estimate). Line numbers: 50, 58, 59, 240, 256.")

# ---- duplicated Fourier API -------------------------------------------------
add("T3",
    "`abbrev T3 := Fin 3 → UnitAddCircle` duplicates Mathlib's `UnitAddTorus (Fin 3)` (`abbrev UnitAddTorus (d : Type*) := d → UnitAddCircle`). "
    "The name `T3` is also ambiguous with the T₃ separation axiom `T3Space`, and it is a root-level declaration.",
    "Delete `T3` and write `UnitAddTorus (Fin 3)` throughout, importing `Mathlib.Analysis.Fourier.AddCircleMulti`.",
    "blocking",
    "declaration_search: `UnitAddTorus` is at Mathlib/Analysis/Fourier/AddCircleMulti.lean:43 (base) and `T3Space` at Mathlib/Topology/Separation/Regular.lean:398. "
    "Conventions: no new definition that the library already has; no name with a different established meaning.")

add("fourier3D",
    "`fourier3D` re-implements `UnitAddTorus.mFourier`; the two agree definitionally.",
    "Delete `fourier3D` and use `UnitAddTorus.mFourier k` (a bundled `C(UnitAddTorus d, ℂ)`) everywhere.",
    "blocking",
    B1 + " for `example (k : Fin 3 → ℤ) (x : T3) : fourier3D k x = UnitAddTorus.mFourier k x := rfl`.")

add("fourier1D",
    "`fourier1D n := fourier n` is a bare alias of the library's `fourier n`. It adds nothing, and `fourier3D_orthogonal` has to `unfold` it again.",
    "Delete `fourier1D` and use `fourier` directly.",
    "blocking",
    "diff lines 112-113: the body is `fourier n`. Convention: no new definition when an existing library declaration already expresses it.")

add("fourierCoeff3D",
    "`fourierCoeff3D f k = ∫ x, f x * star (fourier3D k x)` duplicates `UnitAddTorus.mFourierCoeff f n = ∫ t, mFourier (-n) t • f t`, "
    "which also comes with Parseval and inversion theorems.",
    "Delete `fourierCoeff3D` and use `UnitAddTorus.mFourierCoeff`, rewriting `fourierTransform`, `DivergenceFree` and `hsNorm` against it.",
    "blocking",
    "file_read of AddCircleMulti.lean:193 gives `def mFourierCoeff (f : UnitAddTorus d → E) (n : d → ℤ) : E := ∫ t, mFourier (-n) t • f t`, and line 60 gives `mFourier_neg`.")

add("fourier3D_orthogonal",
    "`fourier3D_orthogonal` restates `UnitAddTorus.orthonormal_mFourier` and is proved from two axioms (`fourier_ortho_integral`, `fubini_torus3`). "
    "The proof also carries a redundant `have ortho1D := fourier_ortho_integral`, a `have : ∃ i, … ; obtain` detour, and a `have h1 : ∀ x, … := by intro x`.",
    "Delete the lemma in favour of `UnitAddTorus.orthonormal_mFourier`. If an integral form is wanted, prove it from library lemmas with binder-style `have`s:\n"
    "`  have h1 (x : T3) : fourier3D k x * star (fourier3D k' x) = ∏ i : Fin 3, (fourier (k i) (x i) * star (fourier (k' i) (x i))) := by\n"
    "    rw [fourier3D, fourier3D, star_prod, ← Finset.prod_mul_distrib]; rfl\n"
    "  simp_rw [h1, MeasureTheory.integral_fintype_prod_volume_eq_prod (fun i y ↦ fourier (k i) y * star (fourier (k' i) y)), fourier_ortho_integral]\n"
    "  by_cases h : k = k'\n  · simp [h]\n  · obtain ⟨i, hi⟩ := Function.ne_iff.mp h\n    rw [if_neg h]\n    exact Finset.prod_eq_zero (Finset.mem_univ i) (if_neg hi)`",
    "blocking",
    "lean_verify_edit compiled this proof (as `fourier3D_orthogonal'`, appended) with no errors or warnings at its lines. "
    "declaration_search: `UnitAddTorus.orthonormal_mFourier` is at AddCircleMulti.lean:172.")

add("parseval3D",
    "`parseval3D` duplicates `UnitAddTorus.hasSum_sq_mFourierCoeff`, and its proof rests on the false axioms `fourier_inversion` and `parseval_orthonormal`.",
    "Delete `parseval3D`. Obtain Parseval for continuous `f` from `UnitAddTorus.hasSum_sq_mFourierCoeff (f.toLp 2 volume ℂ)` and `UnitAddTorus.mFourierCoeff_toLp`.",
    "blocking",
    "file_read of AddCircleMulti.lean:239-251 shows `hasSum_sq_mFourierCoeff` and `mFourierCoeff_toLp`. diff lines 293-300 show parseval3D's proof using both axioms.")

# ---- vacuous / wrong definitions ---------------------------------------------
add("fourierDecay",
    "`fourierDecay u k j n C` is defined as `True`, so `SmoothInitial u` holds for every `u`, and every \"smooth initial data\" hypothesis in the file is empty. "
    "The unused-variable linter flags all five arguments, and Mathlib CI treats those warnings as errors.",
    "Define the decay condition the docstring promises, e.g. `‖fourierTransform u k j‖ * (1 + ‖k‖) ^ n ≤ C`, or delete `fourierDecay` and `SmoothInitial`.",
    "blocking",
    B1 + " for `example (u : T3 → Fin 3 → ℝ) : SmoothInitial u := fun _ ↦ ⟨0, fun _ _ ↦ trivial⟩`. The as-is compile reports unused variables `u k j n C` at line 92.")

add("spectralNSResidual",
    "`spectralNSResidual` is the constant `0`, so `SolvesNavierStokes ν u p` holds for every `ν`, `u` and `p`; the theorem's Navier-Stokes conclusion says nothing. "
    "The linter flags all five arguments of `spectralNSResidual` as unused, and `p` as unused in `SolvesNavierStokes`.",
    "Define the actual spectral residual of the incompressible Navier-Stokes system (time derivative, `ν‖k‖²` dissipation, Leray-projected nonlinearity, pressure). "
    "Otherwise delete `spectralNSResidual` and `SolvesNavierStokes`.",
    "blocking",
    B1 + " for `example (ν) (u) (p) : SolvesNavierStokes ν u p := fun _ _ _ _ ↦ rfl`. The as-is compile warns about unused `ν u t k j` (line 137) and `p` (line 142).")

add("GalerkinProjection",
    "`GalerkinProjection N u₀ := fun x t j => u₀ x j` ignores both the truncation level `N` and the time `t`, so it is not a Galerkin approximation. "
    "`fourierTruncate` and `LerayProjection`, which a Galerkin scheme would use, are defined and never used. "
    "Because of this, `galerkin_energy_bound` is `le_rfl`, and the main theorem's \"solution\" is `u₀` held constant in time.",
    "Define the Galerkin approximation as the solution of the `fourierTruncate N`-projected, Leray-projected ODE system with initial data `fourierTruncate N (fourierTransform u₀)`. "
    "Otherwise remove `GalerkinProjection`, `GalerkinAt`, `fourierTruncate` and `LerayProjection`, and the Galerkin terminology.",
    "blocking",
    B1 + " for `GalerkinProjection N u₀ x t = GalerkinProjection M u₀ x s := rfl`. The as-is compile warns about unused `N` (line 150) and `t` (line 151). "
    "The names `fourierTruncate` and `LerayProjection` occur only at their own declarations.")

add("BKMFinite",
    "`BKMFinite ω T := ∃ M : ℝ, ∫ t in (0)..T, ω t ≤ M` is true for every `ω` and `T`: take `M` to be the integral. "
    "It does not express finiteness of the Beale-Kato-Majda integral.",
    "Define it as integrability, e.g. `IntervalIntegrable ω volume 0 T`, or `∫⁻ t in Set.Ioc 0 T, ‖ω t‖ₑ < ∞`.",
    "blocking",
    B1 + " for `example (ω : ℝ → ℝ) (T : ℝ) : BKMFinite ω T := ⟨_, le_rfl⟩`.")

add("smoothInTime",
    "`smoothInTime f := ContDiff ℝ ⊤ f` asks for analyticity, not smoothness. In current Mathlib `ContDiff 𝕜 n` takes `n : WithTop ℕ∞`, and `⊤` is `ω` (analytic), "
    "while smooth is `∞`. The docstring \"Smooth function of time\" and `SmoothSpacetime` therefore mean the wrong thing.",
    "Write `ContDiff ℝ ∞ f` with `open scoped ContDiff`.",
    "blocking",
    B1 + " for `open scoped ContDiff in example (f : ℝ → ℝ) : smoothInTime f ↔ ContDiff ℝ ω f := Iff.rfl`.")

add("spectralCurl",
    "`spectralCurl` is not the Fourier symbol of the curl on `UnitAddCircle`. With `fourier n x = exp (2πi n x)` (`fourier_coe_apply`, `T = 1`), "
    "`∂ⱼ` corresponds to `2πi kⱼ`, so the factor `2π` is missing. Separately, `(j + 1) % 3` and `(j + 2) % 3` on `Fin 3` reduce modulo `(3 : Fin 3) = 0`: "
    "they are no-ops, and only look like modular arithmetic.",
    "Rewrite as `noncomputable def spectralCurl (û : FourierCoeff) (k : Fin 3 → ℤ) (j : Fin 3) : ℂ :=\n"
    "  2 * Real.pi * Complex.I * ((k (j + 1) : ℂ) * û k (j + 2) - (k (j + 2) : ℂ) * û k (j + 1))`.",
    "blocking",
    B1 + " for `example : ∀ j : Fin 3, (j + 1) % 3 = j + 1 ∧ (j + 2) % 3 = j + 2 := by decide`. The rewritten definition compiled in context, with the rest of the file unchanged "
    "(lean_verify_edit lines 115-169: compiled, 0 new warnings). `fourier_coe_apply` (Mathlib/Analysis/Fourier/AddCircle.lean:132) gives `exp (2 * π * I * n * x / T)`.")

add("linftyNorm",
    "`linftyNorm f := ⨆ (x : T3) (j : Fin 3), |f x j|` is a pointwise supremum in `ℝ`, which is `0` for unbounded `f` (`Real.iSup_of_not_bddAbove`), and is not an essential supremum. "
    "The axioms `sobolev_embedding` and `bkm_implies_regularity` are stated about this junk value. "
    "`l2Norm` likewise re-implements an `L²` norm.",
    "Use the library seminorms: `MeasureTheory.eLpNorm f ∞ volume` and `MeasureTheory.eLpNorm f 2 volume` (or the `Lp` norms), instead of `linftyNorm` and `l2Norm`.",
    "advisory",
    "declaration_search: `Real.iSup_of_not_bddAbove` is at Mathlib/Data/Real/Archimedean.lean:191 and `MeasureTheory.eLpNorm` at Mathlib/MeasureTheory/Function/LpSeminorm/Defs.lean:86.")

# ---- theorems ------------------------------------------------------------------
add("VorticityResponse.regularity",
    "`VorticityResponse.regularity` needs none of its hypotheses: its conclusion holds for every `ν` and `u₀`, without `Φ`, `0 < ν`, `SmoothInitial u₀` or `DivergenceFree u₀`. "
    "Its proof also unfolds by hand (`intro t _ k j; simp [spectralNSResidual]`, `intro x; ext j; rfl`) what are `rfl` terms.",
    "Delete the theorem, since its statement is vacuous with the current definitions. If the definitions are repaired, drop every hypothesis the proof does not use, "
    "and write the witnesses as a term, e.g. `⟨GalerkinProjection 1 u₀, fun _ _ ↦ 0, …, fun _ _ _ _ ↦ rfl, fun _ ↦ rfl⟩`.",
    "blocking",
    "lean_verify_edit compiled `theorem regularity' (ν : ℝ) (u₀ : T3 → Fin 3 → ℝ) : ∃ u p, SmoothSpacetime u ∧ SolvesNavierStokes ν u p ∧ (∀ x, u x 0 = u₀ x) := "
    "⟨GalerkinProjection 1 u₀, fun _ _ ↦ 0, bkm_implies_regularity _ 1 ⟨_, le_rfl⟩, fun _ _ _ _ ↦ rfl, fun _ ↦ rfl⟩` with no errors.")

add("GalerkinLimit.smooth",
    "`GalerkinLimit.smooth` has exactly the statement of `VorticityResponse.regularity`, which already quantifies over an arbitrary `Φ`; it only instantiates `Φ` with `⟨1, 2, …⟩`. "
    "It sits in a namespace `GalerkinLimit` that names no definition, and no Galerkin limit is taken.",
    "Keep at most one of the two theorems, named after what it proves. Do not put it in the made-up namespace `GalerkinLimit`. "
    "If a `VorticityResponse` literal is needed, write `⟨1, 2, one_pos, one_le_two⟩`.",
    "blocking",
    "diff lines 432-465: the two statements are identical. lean_verify_edit compiled `example : VorticityResponse := ⟨1, 2, one_pos, one_le_two⟩`.")

add("uniform_vorticity_bound",
    "`uniform_vorticity_bound` takes `h_divfree : DivergenceFree u₀` and never uses it. The linter warns about it, which fails Mathlib CI.",
    "Drop `h_divfree` from `uniform_vorticity_bound` and from its call in `bkm_finite_anyT`. Optionally inline `C` and use `gcongr` with `(cSobolev_pos 3).le` for the two `mul_le_mul_of_nonneg_left` steps.",
    "blocking",
    "The as-is compile warns: unused variable `h_divfree` (line 316). lean_verify_edit compiled `uniform_vorticity_bound'` without `h_divfree` (gcongr version) with no errors or warnings.")

add("bkm_finite_anyT",
    "`bkm_finite_anyT` takes `Φ : VorticityResponse` and never uses it. The linter warns, which fails CI.",
    "Remove the `Φ` argument and update the call in `VorticityResponse.regularity`.",
    "blocking",
    "The as-is compile warns: unused variable `Φ` (line 407). lean_verify_edit compiled `bkm_finite_anyT'` without `Φ`.")

add("bkm_finite_anyT",
    "The proof of `bkm_finite_anyT` restates `hC N` as a separate `have bound` with `intro`. It rebuilds `t ∈ Set.Icc 0 T` as `Set.mem_Icc.mpr ⟨ht.1, ht.2⟩` from the very hypothesis `ht` of that type, "
    "and rewrites `integral_const` by hand.",
    "Golf to:\n`  obtain ⟨C, hC⟩ := uniform_vorticity_bound u₀ h_smooth h_divfree T hT\n  refine ⟨C * T, ?_⟩\n"
    "  calc _ ≤ ∫ _ in (0)..T, C :=\n        intervalIntegral.integral_mono_on hT.le (vorticity_integrable N u₀ T)\n          intervalIntegrable_const fun t ht ↦ hC N t ht\n"
    "    _ = C * T := by simp [mul_comm]`",
    "advisory",
    "lean_verify_edit compiled this proof (as `bkm_finite_anyT'`) with no errors or warnings.")

add("bkm_finite_anyT",
    "The name `bkm_finite_anyT` mixes camelCase (`anyT`) into a snake_case theorem name. It also does not follow Mathlib's naming scheme, which names a lemma after its conclusion (`BKMFinite` of the Galerkin vorticity).",
    "Rename it after its conclusion, e.g. `bkmFinite_linftyNorm_vorticity`, with no `anyT` suffix.",
    "advisory",
    "Convention: names follow the case convention of their kind. naming_norm returned `subject_unresolved` (unmeasured), so this rests on the naming guide rather than a census.")

add("bkm_coordinate_invariance",
    "`bkm_coordinate_invariance` is `intervalIntegral.integral_comp_mul_deriv` specialised to a `TemporalLifting`. It needs none of `Φ`, the lifting's bounds, or `hT : 0 ≤ T`; "
    "the linter flags `hT` as unused. Its proof re-derives the substitution in three steps.",
    "Drop `hT`, and state the lemma for any `C¹` map `φ` with `φ 0 = 0`, or delete it and use `intervalIntegral.integral_comp_mul_deriv` directly:\n"
    "`lemma bkm_coordinate_invariance (φ : ℝ → ℝ) (hφ : Differentiable ℝ φ) (hφ' : Continuous (deriv φ)) (hφ0 : φ 0 = 0) (ω : ℝ → ℝ) (hω : Continuous ω) (τ_T : ℝ) :\n"
    "    bkmPhysical ω (φ τ_T) = bkmLifted (ω ∘ φ) φ τ_T := by\n"
    "  rw [bkmPhysical, bkmLifted, intervalIntegral.integral_comp_mul_deriv (fun x _ ↦ (hφ x).hasDerivAt) hφ'.continuousOn hω, hφ0]`",
    "blocking",
    "The as-is compile warns: unused variable `hT` (line 355). lean_verify_edit compiled the general version above with no errors or warnings.")

add("tau_interval_finite",
    "`tau_interval_finite` assumes `0 < T`, but the conclusion also holds for `T = 0`; only `0 ≤ T` is needed, which is what `φ_surj` takes.",
    "Weaken `hT : 0 < T` to `hT : 0 ≤ T`.",
    "advisory",
    "lean_verify_edit compiled `tau_interval_finite'` with `(hT : 0 ≤ T)` (proof in the next finding) with no errors.")

add("tau_interval_finite",
    "`tau_interval_finite` is proved by hand. It case-splits on the sign of `τ_T`, rebuilds the fundamental theorem of calculus to bound `φ τ_T - φ 0`, "
    "and ends with a five-line calc (`τ_T = τ_T * 1 = τ_T * (φ_min / φ_min) = …`). The library's mean value inequality and `le_div_iff₀` do the same in a few lines, "
    "and do not need `φ_deriv_cont`.",
    "Golf to:\n`  obtain ⟨τ_T, hτ_T⟩ := L.φ_surj T hT\n  refine ⟨τ_T, hτ_T, (le_div_iff₀ Φ.hmin_pos).2 ?_⟩\n  rcases le_or_gt τ_T 0 with h | h\n"
    "  · nlinarith [Φ.hmin_pos]\n  · have := mul_sub_le_image_sub_of_le_deriv L.φ_diff L.φ_deriv_pos h.le\n    rw [sub_zero, L.φ_zero, sub_zero, hτ_T] at this\n    linarith`",
    "advisory",
    "lean_verify_edit compiled this proof with no errors or warnings. `mul_sub_le_image_sub_of_le_deriv` was read at Mathlib/Analysis/Calculus/Deriv/MeanValue.lean:324.")

add("galerkin_energy_bound",
    "`galerkin_energy_bound` is never used. Its hypothesis `ht` is unused (a linter warning), and its content is `le_rfl`, because `GalerkinAt N u₀ t` is definitionally `u₀`. "
    "The proof `unfold GalerkinAt GalerkinProjection; rfl` hides this.",
    "Delete `galerkin_energy_bound`. If it is kept after `GalerkinProjection` is repaired, drop `ht` and do not prove it by `unfold`.",
    "blocking",
    "The as-is compile warns: unused variable `ht` (line 306). lean_verify_edit compiled `example … : l2Norm (GalerkinAt N u₀ t) ≤ l2Norm u₀ := le_rfl`. "
    "The name occurs nowhere else in the diff.")

# ---- documentation --------------------------------------------------------------
add("module docstring of Mathlib/Analysis/ODE/GalerkinRegularity.lean",
    "The module docstring is false and out of step with the code. The title \"Regularity for Navier-Stokes on T³ via Bounded Vorticity-Response Functionals\" "
    "and \"This file proves global existence and smoothness of solutions to the incompressible Navier-Stokes equations\" claim a Millennium-problem result. "
    "The file proves only statements made vacuous by its placeholder definitions and axioms. The \"Implementation notes\" describe a proof via temporal lifting and BKM coordinate invariance, "
    "but `GalerkinLimit.smooth` uses none of `TemporalLifting`, `bkm_coordinate_invariance` or `tau_interval_finite`. The only support offered is the author's own non-peer-reviewed DOI.",
    "Rewrite the title and summary to state exactly what the file defines and proves. Remove the Navier-Stokes regularity claim and the implementation notes for a route the proofs do not take.",
    "blocking",
    "Conventions: a module title states what the file proves; docs stay in step with the code; non-obvious claims need a reference. diff lines 8-35. "
    "The proof of VorticityResponse.regularity (lines 432-450) uses only bkm_finite_anyT and bkm_implies_regularity.")

add("VorticityResponse",
    "`VorticityResponse` is documented as \"A bounded vorticity-response functional Φ : ℝ≥0 → [φ_min, φ_max]\", but it holds only two real numbers with `0 < φ_min ≤ φ_max`. "
    "It contains no functional and refers to no vorticity, so the name and docstring describe a structure the definition does not have.",
    "Either add the functional as a field (with its bounds), or rename the structure to describe what it is (a pair of positive bounds) and correct its docstring.",
    "advisory",
    "Convention: a new notion's name describes what it is. diff lines 76-86.")

add("VorticityResponse",
    "The proof fields of `VorticityResponse` are named `hmin_pos` and `hbounds`, hypothesis-style names, rather than after their statements.",
    "Rename them after their statements, e.g. `φ_min_pos : 0 < φ_min` and `φ_min_le_φ_max : φ_min ≤ φ_max`.",
    "advisory",
    "diff lines 83-86. Mathlib names a proof field after its statement in snake_case.")

add("TemporalLifting",
    "In `TemporalLifting`, the field `φ_deriv_pos` states `Φ.φ_min ≤ deriv φ τ`, a lower bound and not positivity. The docstring calls `φ` a \"diffeomorphism\", "
    "although the fields give only a `C¹` map with bounded derivative and surjectivity onto `[0, ∞)` (documented as \"Surjectivity (global coverage)\"). "
    "`φ_diff` together with `φ_deriv_cont` is `ContDiff ℝ 1 φ`.",
    "Rename `φ_deriv_pos` to `φ_min_le_deriv` (and `φ_deriv_bdd` to `deriv_le_φ_max`), fix the docstrings to say what the fields state, "
    "and consider bundling regularity as `ContDiff ℝ 1 φ`.",
    "advisory",
    "diff lines 220-235.")

# ---- file-level policy / style ------------------------------------------------------
add(FILE,
    "The file begins with `import Mathlib`. A Mathlib file must import only what it needs, and importing `Mathlib` creates an import cycle once the file is listed in `Mathlib.lean`.",
    "Replace `import Mathlib` with\n`import Mathlib.Analysis.Fourier.AddCircleMulti`\n`import Mathlib.MeasureTheory.Integral.IntervalIntegral.IntegrationByParts`.",
    "blocking",
    "lean_verify_edit replacing line 6 with these two imports: outcome=compiled, 0 errors, 0 new warnings.")

add(FILE,
    "The new file is not a `module`: it has no `module` keyword, uses plain `import`, and has no `@[expose] public section`. Its neighbours in the same directory "
    "(for example `Mathlib/Analysis/ODE/Gronwall.lean`) and its natural import `Mathlib/Analysis/Fourier/AddCircleMulti.lean` are all modules.",
    "Start the file with `module`, use `public import`, and put the content in `@[expose] public section`.",
    "blocking",
    "file_read of target/Mathlib/Analysis/ODE/Gronwall.lean lines 6-32 shows `module`, `public import` and `@[expose] public section`, and so does AddCircleMulti.lean lines 6-19.")

add("Mathlib.lean",
    "The new file `Mathlib/Analysis/ODE/GalerkinRegularity.lean` is not imported in `Mathlib.lean`, the only changed file is the new one, "
    "so CI does not build it as part of Mathlib and the `mk_all` check fails.",
    "Add `import Mathlib.Analysis.ODE.GalerkinRegularity` (or `public import` under the module system) to `Mathlib.lean`, after fixing `import Mathlib`.",
    "blocking",
    "pr.md lists one changed file, and the diff touches only GalerkinRegularity.lean.")

add(FILE,
    "The file ends with the debugging commands `#check GalerkinLimit.smooth` and `#print axioms GalerkinLimit.smooth`, which print output on every build. "
    "The heading \"## Axioms (after definitions they reference)\" is a note to oneself.",
    "Delete lines 467-469 (`#check` and `#print axioms`) and the working heading at line 186.",
    "blocking",
    "Compile results report infos=2 from these two commands (lean_verify_edit runs report `infos: 2`). Convention: scaffolding and working comments are removed before merging.")

add(FILE,
    "`set_option linter.style.commandStart false` disables a style linter for the whole file to hide four spacing warnings that are easy to fix in the source.",
    "Remove the `set_option` and fix the spacing: `‖c k‖^2` → `‖c k‖ ^ 2`, `3/2` → `3 / 2`, `5/2` → `5 / 2` (and the other `^2` occurrences).",
    "blocking",
    "lean_verify_edit deleting lines 37-38 reported 4 new warnings, all `missing space`: `parseval_orthonormal` (`k‖^2`), `moser_estimate` (`3/2`), "
    "`hs_gronwall_bound` and `sobolev_embedding` (`5/2`). Convention: no linter exemption for a warning that can be fixed at its source.")

add(FILE,
    "`open scoped InnerProductSpace` is not needed; the file uses no inner-product notation.",
    "Delete `open scoped InnerProductSpace` (line 38).",
    "advisory",
    "lean_verify_edit deleting lines 37-38 compiled with no errors. The only new warnings were the commandStart spacing ones.")

add(FILE,
    "The copyright header says `Author: Jeffrey Camlin`; Mathlib's header format requires `Authors:`.",
    "Change line 4 to `Authors: Jeffrey Camlin`.",
    "advisory",
    "diff line 4. Every Mathlib file read (Gronwall.lean, AddCircleMulti.lean) uses `Authors:`.")

add(FILE,
    "Lambdas throughout are written `fun x => …` rather than Mathlib's `fun x ↦ …`. This occurs in 26 lines, for example in `fourier3D`, `fourierTransform`, `SmoothSpacetime`, `LerayProjection`, "
    "`fourierTruncate`, `GalerkinProjection`, `spectralCurl`, `invFourier`, `Vorticity`, `GalerkinAt`, `hsNorm`, `bkm_implies_regularity`, `vorticity_integrable`, "
    "`moser_estimate`, `vorticity_hs_bound`, `uniform_vorticity_bound`, `fourier3D_orthogonal`, `bkm_finite_anyT` and `VorticityResponse.regularity`.",
    "Replace every `=>` in a `fun` with `↦`.",
    "advisory",
    "`grep -c '=>'` on the reconstructed file gives 26 lines. The batch rewrite of lines 115-169 with `↦` compiled.")

add(FILE,
    "Nine function-valued definitions are written as `:= fun k j => …` or `:= fun x t => …` instead of taking their arguments as binders after the name: "
    "`fourier3D`, `fourierTransform`, `LerayProjection`, `fourierTruncate`, `GalerkinProjection`, `spectralCurl`, `invFourier`, `Vorticity` and `GalerkinAt`.",
    "Move the lambda arguments into binders, e.g. `noncomputable def fourier3D (k : Fin 3 → ℤ) (x : T3) : ℂ := ∏ i : Fin 3, fourier1D (k i) (x i)` "
    "and `noncomputable def Vorticity (u : T3 → ℝ → Fin 3 → ℝ) (x : T3) (t : ℝ) : Fin 3 → ℝ := invFourier (spectralCurl (fourierTransform (u · t))) x`.",
    "advisory",
    "lean_verify_edit replacing lines 115-169 with binder-style versions of all nine definitions: compiled, 0 errors, 0 new warnings; the rest of the file was unchanged and still compiled.")

add(FILE,
    "16 of the file's 24 definitions are marked `noncomputable def` one by one; the rest are `Prop`s.",
    "Open a single `noncomputable section` after the module docstring and drop the per-definition `noncomputable` markers.",
    "advisory",
    "`grep -c 'noncomputable def'` gives 16. Convention: a file most of whose definitions are noncomputable opens one `noncomputable section`.")

add(FILE,
    "Every declaration is placed in the root namespace, including generic names such as `fourierTransform`, `invFourier`, `DivergenceFree`, `Vorticity`, `hsNorm`, `l2Norm`, `T3` and `cMoser`. "
    "This pollutes the global namespace and collides conceptually with existing Fourier-transform API.",
    "Put the Fourier-series material in the `UnitAddTorus` namespace (where `mFourier` and `mFourierCoeff` live), and the fluid-dynamics definitions in a dedicated namespace such as `NavierStokes`.",
    "advisory",
    "The diff has no `namespace` command. Convention: declarations about a theory go in its established namespace. AddCircleMulti.lean uses `namespace UnitAddTorus`.")

add("GalerkinProjection",
    "`GalerkinProjection`, `LerayProjection`, `Vorticity` and `GalerkinAt` are definitions whose values are functions (terms), not types or propositions, but they are named in UpperCamelCase.",
    "Rename them `galerkinProjection`, `lerayProjection`, `vorticity` and `galerkinAt`.",
    "advisory",
    "Convention: lowerCamelCase for definitions producing terms. Their types are `… → T3 → ℝ → Fin 3 → ℝ` and `FourierCoeff` (diff lines 132, 150, 164, 168).")

add("smoothInTime",
    "`smoothInTime` and `fourierDecay` are `Prop`-valued definitions named in lowerCamelCase. Their siblings `SmoothInitial`, `SmoothSpacetime` and `DivergenceFree` are correctly in UpperCamelCase.",
    "Rename them `SmoothInTime` and `FourierDecay`.",
    "advisory",
    "Convention: Prop-valued definitions use UpperCamelCase. diff lines 92 and 100.")

add(FILE,
    "The file is placed in `Mathlib/Analysis/ODE/`, but Navier-Stokes is a PDE, and the reusable content (Fourier analysis on the 3-torus) belongs with `Mathlib/Analysis/Fourier/AddCircleMulti.lean`. "
    "The file name `GalerkinRegularity` names a method rather than the notion the file is about.",
    "Move any surviving Fourier-on-torus lemmas into `Mathlib/Analysis/Fourier/AddCircleMulti.lean`. Do not add a Navier-Stokes file under `Analysis/ODE`.",
    "advisory",
    "Convention: a new file is named for its notion and placed in that theory's directory. AddCircleMulti.lean already holds the torus Fourier API.")

json.dump(F, open(f"{D}/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
