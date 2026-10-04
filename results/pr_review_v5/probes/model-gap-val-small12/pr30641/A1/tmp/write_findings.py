import json, sys
D = sys.argv[1]
F = []
def add(target, claim, change, sev, ev):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev, "evidence": ev})

add("Real.posLog_pow",
    "The docstring of `Real.posLog_pow` says that `log⁺` \"commutes with taking powers\", which would mean `log⁺ (a ^ n) = (log⁺ a) ^ n`; the lemma actually states `log⁺ (a ^ n) = n * log⁺ a`, so the docstring misdescribes the result.",
    "Replace the docstring with one that states the result, e.g. `/-- The positive part of the logarithm of a power `a ^ n` is `n` times `log⁺ a`. -/`.",
    "blocking",
    "Read the statement at PosLog.lean:101-103 (`log⁺ (a ^ n) = n * log⁺ a`). lean_verify_edit on lines 101-110 with the new docstring (together with the header/proof changes below) returned outcome `compiled`, no errors.")

add("Real.posLog_pow",
    "The 7-line case-split proof of `Real.posLog_pow` (cases `n = 0`, `|a| ≤ 1`, then `rw [not_le] at h₂a` and two `posLog_eq_log` rewrites) redoes by hand what `Real.log_pow` (simp, holds for all real `x`) and `mul_max_of_nonneg` give directly from `posLog_def`: `max 0 (n * log a) = n * max 0 (log a)` because `0 ≤ (n : ℝ)`.",
    "Replace the proof with `simp [posLog_def, mul_max_of_nonneg _ _ n.cast_nonneg]`.",
    "advisory",
    "declaration_search: `Real.log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x` is `@[simp]` in Mathlib/Analysis/SpecialFunctions/Log/Basic.lean:266-267; `mul_max_of_nonneg (b c) (ha : 0 ≤ a) : a * max b c = max (a * b) (a * c)` at Mathlib/Algebra/Order/Ring/Unbundled/Basic.lean:525. lean_verify_edit replacing `Real.posLog_pow` by `lemma posLog_pow (n : ℕ) (a : ℝ) : log⁺ (a ^ n) = n * log⁺ a := by simp [posLog_def, mul_max_of_nonneg _ _ n.cast_nonneg]` returned outcome `compiled`, no errors (whole file).")

add("Real.posLog_pow",
    "`Real.posLog_pow` takes `{n : ℕ} {a : ℝ}` as implicit binders although the lemma has no explicit argument or hypothesis from which they could be inferred; the analogue `Real.log_pow (x : ℝ) (n : ℕ)` and the file's own `posLog_neg (x : ℝ)` / `posLog_abs (x : ℝ)` take them explicitly, so `posLog_pow` cannot be instantiated as `posLog_pow n a` in a rewrite.",
    "Make the binders explicit: `@[simp] lemma posLog_pow (n : ℕ) (a : ℝ) : log⁺ (a ^ n) = n * log⁺ a`.",
    "advisory",
    "Read Real.log_pow (Log/Basic.lean:267, explicit `(x : ℝ) (n : ℕ)`) and PosLog.lean:64,67 (`posLog_neg (x : ℝ)`, `posLog_abs (x : ℝ)`). No use of `posLog_pow` elsewhere in Mathlib (content_search over target/Mathlib found only its declaration). lean_verify_edit with explicit binders compiled with no errors.")

add("Real.posLog_pow",
    "The header of `Real.posLog_pow` is broken over two lines (`@[simp] lemma posLog_pow {n : ℕ} {a : ℝ} :` / `log⁺ (a ^ n) = n * log⁺ a := by`) although it fits in 74 characters, and the break leaves an inline `@[simp]` in front of a multi-line header.",
    "Put the header on one line: `@[simp] lemma posLog_pow (n : ℕ) (a : ℝ) : log⁺ (a ^ n) = n * log⁺ a := by` (with the explicit binders requested above); this also keeps the inline `@[simp]` on a one-line header, like `posLog_neg`/`posLog_abs`.",
    "advisory",
    "Measured the joined line: 74 characters (< 100). lean_verify_edit on lines 101-110 with the one-line header compiled with no errors.")

add("Real.posLog_norm_sum_le",
    "`Real.posLog_norm_sum_le` assumes `[NormedAddCommGroup E]`, but the only fact about `E` it uses is the triangle inequality `norm_sum_le`, which holds for `SeminormedAddCommGroup`; the lemma is stated in less generality than its proof gives.",
    "Weaken the instance to `[SeminormedAddCommGroup E]` (e.g. `lemma posLog_norm_sum_le {E : Type*} [SeminormedAddCommGroup E] {α : Type*} (s : Finset α)` / `    (f : α → E) : ...`).",
    "advisory",
    "declaration_search/file_read: `norm_sum_le {E} [SeminormedAddCommGroup E] (s : Finset ι) (f : ι → E)` at Mathlib/Analysis/Normed/Group/Basic.lean:1167. lean_verify_edit with `[SeminormedAddCommGroup E]` and the PR's calc proof (side goals inlined) compiled with no errors; a term-mode version with the same instance also compiled.")

add("Real.posLog_norm_sum_le",
    "In `Real.posLog_norm_sum_le` the first calc step uses `apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)` with an `_` hole and then closes the nonnegativity side goal in a separate `simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]` line; a short side goal should be discharged inline (and a term with holes is applied with `refine ?_`, not `apply _`).",
    "Discharge the side goal inline and write the step as a term: `_ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg]) (norm_sum_le s f)`; or drop the calc altogether: `(monotoneOn_posLog (norm_nonneg _) (s.sum_nonneg fun _ _ ↦ norm_nonneg _) (norm_sum_le s f)).trans (posLog_sum s _)`.",
    "advisory",
    "lean_verify_edit with the calc step `monotoneOn_posLog (by simp) (by simp [Finset.sum_nonneg]) (norm_sum_le s f)` compiled with no errors; lean_verify_edit with the term proof `(monotoneOn_posLog (norm_nonneg _) (s.sum_nonneg fun _ _ ↦ norm_nonneg _) (norm_sum_le s f)).trans (posLog_sum s _)` also compiled with no errors.")

add("Real.posLog_norm_sum_le",
    "The docstring of `Real.posLog_norm_sum_le` opens on the line after `/--` and closes with `-/` on its own line, describes the lemma only as a \"Variant of `posLog_sum`\" rather than saying what it bounds, cites `posLog_sum` without its full name `Real.posLog_sum`, and spends its second half on the proof method (\"using monotonicity of `log⁺` and the triangle inequality\"), which is not part of the statement.",
    "Rewrite it as a docstring that starts on the `/--` line, says what is estimated and ends with `-/` on the last text line, e.g. `/-- Estimate for `log⁺` of the norm of a sum. See `Real.posLog_norm_add_le` for a variant involving` / `just two summands. -/`.",
    "advisory",
    "Read PosLog.lean:182-185. The file's other docstrings cross-reference by full name (`Real.posLog_add`, `Real.posLog_sum`, `Real.posLog_mul`). lean_verify_edit replacing lines 182-185 with the suggested two-line docstring compiled with no errors; first line measures 99 characters.")

add("Real.posLog_sum",
    "The PR reflows the docstring of `Real.posLog_sum` from `/-- Estimate ... involving` / `just two summands. -/` into a form whose text starts on the line after `/--` and whose `-/` sits on a line of its own; this departs from the docstring layout used elsewhere in the file and is cosmetic churn on a declaration the PR does not otherwise change.",
    "Revert the docstring to the original layout: `/-- Estimate for `log⁺` of a sum. See `Real.posLog_add` for a variant involving` / `just two summands. -/`.",
    "advisory",
    "diff.patch hunk @@ -130,8 +149,10 @@ shows only the layout change, no change of wording. A one-line `/-- ... -/` would be 101 characters, so the original two-line form is the one that fits; the other docstrings in the file (e.g. `posLog_mul`, `posLog_prod`, lines 116-117, 135-136) start on the `/--` line and close on the last text line.")

add("Real.posLog_add",
    "The PR reflows the docstring of `Real.posLog_add` into a form whose text starts on the line after `/--` and whose `-/` sits on a line of its own; the wording is unchanged, so this is pure layout churn that departs from the file's `/-- text ... -/` docstring layout.",
    "Revert the docstring to the original layout: `/-- Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving` / `multiple summands. -/`.",
    "advisory",
    "diff.patch hunk @@ -158,8 +179,23 @@: the old docstring `/-- Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving` / `multiple summands. -/` is replaced by the same words in `/--` / text / `-/` form.")

add("Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean",
    "The new sentence in the module docstring refers to the other file by its dotted module name `Mathlib.Analysis.SpecialFunctions.Integrals.PosLogEqCircleAverage` rather than by its file path.",
    "Write the cross-reference as a file path: \"See `Mathlib/Analysis/SpecialFunctions/Integrals/PosLogEqCircleAverage.lean` for the presentation of `log⁺` as a circle average.\"",
    "advisory",
    "Read PosLog.lean:19-20; file_search confirms the target file is `Mathlib/Analysis/SpecialFunctions/Integrals/PosLogEqCircleAverage.lean` (its module doc is \"Representation of `log⁺` as a Circle Average\"). The replacement first line measures 100 characters.")

add("Real.posLog_zero",
    "`Real.posLog_zero` and `Real.posLog_one` are a parallel pair of one-line `@[simp]` evaluation lemmas, but the PR separates them with a blank line, which hides the parallel.",
    "Remove the blank line between `@[simp] lemma posLog_zero : log⁺ 0 = 0 := by simp [posLog]` and `@[simp] lemma posLog_one : log⁺ 1 = 0 := by simp [posLog]` so the two stand adjacent.",
    "advisory",
    "Read PosLog.lean:56-58. lean_verify_edit replacing lines 56-58 with the two adjacent lines compiled with no errors.")

add("Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean",
    "The PR inserts a blank line after the `## Elementary Properties`, `## Estimates for Products` and `## Estimates for Sums` section headers, but leaves the first header `## Definition, Notation and Reformulations` (lines 25-28) directly followed by the `posLog` docstring, so the file now lays out its section headers two different ways.",
    "Add the same blank line after the `## Definition, Notation and Reformulations` section header (between line 27 `-/` and line 28 `/-- Definition: ...`), so that every section header is laid out the same way.",
    "advisory",
    "Read PosLog.lean:25-28, 37-41, 112-116, 149-153 as the PR leaves the file; diff.patch adds `+` blank lines only after the latter three headers.")

with open(f"{D}/findings.json", "w") as fh:
    json.dump(F, fh, indent=1, ensure_ascii=False)
print(len(F))
