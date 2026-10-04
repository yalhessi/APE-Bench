import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-nature/results/pr_review_v5/probes/model-gap-val-small12/pr28649/A1"
findings = [
 {
  "target": "Mathlib/Probability/Kernel/Composition/IntegralCompProd.lean (module docstring, Main statements)",
  "claim": "The module docstring this PR edits still misstates the second main result. It names `ProbabilityTheory.integral_comp`, which does not exist: the theorem is declared inside `namespace Kernel` as `ProbabilityTheory.Kernel.integral_comp`. Its formula is written with the Lebesgue integral `∫⁻`, but the theorem, like the whole file, is about the Bochner integral: `∫ z, f z ∂(η ∘ₖ κ) a = ∫ x, ∫ y, f y ∂η x ∂κ a`.",
  "requested_change": "Change the bullet on lines 30-31 to: \"* `ProbabilityTheory.Kernel.integral_comp`: the integral against the composition is\\n  `∫ z, f z ∂((η ∘ₖ κ) a) = ∫ x, ∫ y, f y ∂(η x) ∂(κ a)`.\"",
  "severity": "advisory",
  "evidence": "declaration_search `ProbabilityTheory.integral_comp`: no declaration at base or in the PR. declaration_search `ProbabilityTheory.Kernel.integral_comp`: declared at IntegralCompProd.lean:417. file_read shows `namespace Kernel` at line 359 and `theorem integral_comp ... ∫ z, f z ∂(η ∘ₖ κ) a = ∫ x, ∫ y, f y ∂η x ∂κ a` at lines 417-418. lean_verify_edit (line mode, lines 30-31) with the corrected bullet: outcome compiled, no errors."
 },
 {
  "target": "Mathlib/Probability/Moments/Basic.lean (module docstring, Main results)",
  "claim": "The PR changes `mgfs`/`cgfs` to `MGFs`/`CGFs` on lines 25 and 27, but line 30 of the same docstring still says `the cgf exists`, so the module docstring now spells the abbreviation two ways. The lowercase form was not a typo either: the other Moments files write `mgf` in prose (ComplexMGF.lean: \"The moment generating function (mgf)\", \"of definition of the mgf\"; MGFAnalytic.lean: \"the n-th derivative of the mgf\"; SubGaussian.lean: \"the mgf of a Gaussian\").",
  "requested_change": "Revert lines 25 and 27 to `and their mgfs are defined at `t`` and `and their cgfs are defined at `t``, which keeps the docstring consistent with `the cgf exists` on line 30 and with the rest of `Mathlib/Probability/Moments/`.",
  "severity": "advisory",
  "evidence": "file_read Basic.lean lines 1-45: line 25 `MGFs`, line 27 `CGFs`, line 30 `the cgf exists`. content_search over target/Mathlib/Probability/Moments/ for MGF/CGF in prose: every other prose occurrence is lowercase `mgf` (ComplexMGF.lean lines 18, 20, 21, 32; MGFAnalytic.lean line 20; SubGaussian.lean lines 32, 107, 110). zulip_search: maintainer Rémy Degenne, the file's author, writes `mgf` lowercase. lean_verify_edit (line mode, lines 24-27) with the reverted text: compiled."
 },
 {
  "target": "MeasureTheory.tendsto_of_uncrossing_lt_top",
  "claim": "The new wording \"bounded limit inferiors\" uses a nonstandard plural (the usual plural is \"limits inferior\") and is less clear than the `liminfs` it replaces. It also does not match the statement: hypothesis `hf₁ : liminf (fun n => (‖f n ω‖₊ : ℝ≥0∞)) atTop < ∞` is a single limit inferior, of the norm of one realization.",
  "requested_change": "Rewrite the first sentence of the docstring as: \"A realization of a stochastic process with bounded upcrossings and whose norm has a finite limit inferior is convergent.\"",
  "severity": "advisory",
  "evidence": "file_read Convergence.lean lines 133-140: the docstring and the statement with the single hypothesis `hf₁` on `liminf ‖f n ω‖₊`. lean_verify_edit (line mode, lines 133-134) with the rewritten sentence: outcome compiled, no errors."
 },
 {
  "target": "Mathlib/Probability/Martingale/Upcrossing.lean (module-level doc `### Variant of the upcrossing estimate`)",
  "claim": "The paragraph this PR edits gives a wrong formula and a wrong reason. In `U_N(a, b) = \\sum_{i = 1}^N \\mathbf{1}_{\\{U_N(a, b) < N\\}}` the summand does not depend on `i`. It also says that `U_N(a, b)` is a stopping time. The code (`upcrossingsBefore_eq_sum`, `Adapted.measurable_upcrossingsBefore`) sums `{n | upperCrossingTime a b f N n ω < N}.indicator 1 i`, and it gets measurability because each `upperCrossingTime a b f N i` is a stopping time.",
  "requested_change": "Replace lines 703-706 with: \"  U_N(a, b) = \\sum_{i = 1}^N \\mathbf{1}_{\\{\\tau_i < N\\}},\\n$$\\nwhere $\\tau_i$ is the $i$-th upper crossing time `upperCrossingTime a b f N i`, $U_N(a, b)$ is\\nmeasurable as each $\\{\\tau_i < N\\}$ is a measurable set since $\\tau_i$ is a stopping time.\"",
  "severity": "advisory",
  "evidence": "file_read Upcrossing.lean lines 685-745: the docstring formula on line 703 and the 'U_N(a, b) is a stopping time' claim on lines 705-706, against `upcrossingsBefore_eq_sum` (lines 711-712) and `Adapted.measurable_upcrossingsBefore`, which uses `hf.isStoppingTime_upperCrossingTime.measurableSet_lt_of_pred N` (line 744). lean_verify_edit (line mode, lines 703-706) with the corrected text: compiled."
 },
 {
  "target": "Mathlib/Probability/Moments/Variance.lean (module docstring, Main results)",
  "claim": "This typo-fix PR touches Variance.lean but leaves a typo of the same kind in its module docstring: line 34 reads \"is at most`((b - a) / 2) ^ 2`.\", with no space before the code span.",
  "requested_change": "Change line 34 to \"  `a ≤ X ≤ b` almost everywhere is at most `((b - a) / 2) ^ 2`.\"",
  "severity": "advisory",
  "evidence": "file_read Variance.lean lines 1-50: line 34 `almost everywhere is at most`((b - a) / 2) ^ 2`.`. The same bound is written with the space in the docstring of `variance_le_sq_of_bounded` (lines 454-455). lean_verify_edit (line mode, line 34): compiled."
 },
 {
  "target": "Mathlib/Probability/Moments/Basic.lean (module docstring, Main definitions)",
  "claim": "The module docstring this PR edits has a spacing typo ten lines above the hunk: line 15 reads \"`ProbabilityTheory.centralMoment X p μ`:`p`th central moment\", with no space after the colon, unlike every other item in the list.",
  "requested_change": "Change line 15 to \"* `ProbabilityTheory.centralMoment X p μ`: `p`th central moment of `X` with respect to measure `μ`,\".",
  "severity": "advisory",
  "evidence": "file_read Basic.lean lines 13-20: line 15 has `:`p`th` while lines 13, 17 and 19 have `: ` after the code span. lean_verify_edit (line mode, line 15): compiled."
 }
]
with open(f"{D}/findings.json", "w") as fh:
    json.dump(findings, fh, ensure_ascii=False, indent=1)
print(len(findings))
