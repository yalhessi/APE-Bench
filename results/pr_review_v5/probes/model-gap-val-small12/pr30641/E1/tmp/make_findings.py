import json, sys
D = sys.argv[1]
findings = [
 {
  "target": "Real.posLog_pow",
  "claim": "`Real.posLog_pow` is proved by a seven-line double case split (`n = 0`, `|a| ≤ 1`) with `simp_all`, `one_lt_pow₀` and two uses of `posLog_eq_log`, although after unfolding `posLog` and rewriting with the simp lemma `log_pow` the goal is just `max 0 (n * log a) = n * max 0 (log a)`, which `mul_max_of_nonneg` closes.",
  "requested_change": "Replace the whole proof of `posLog_pow` with `by simp [posLog, mul_max_of_nonneg]`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Real.posLog_pow with the original binders `{n : ℕ} {a : ℝ}` and proof `simp [posLog, mul_max_of_nonneg]`: outcome compiled, no errors or warnings. It also compiles with explicit binders `(x : ℝ) (n : ℕ)`. declaration_search: `mul_max_of_nonneg (b c : R) (ha : 0 ≤ a) : a * max b c = max (a * b) (a * c)` exists in Mathlib/Algebra/Order/Ring/Unbundled/Basic.lean:525 at the base commit."
 },
 {
  "target": "Real.posLog_pow",
  "claim": "`Real.posLog_pow` is an unconditional equational `@[simp]` lemma, but it takes both variables as implicit binders `{n : ℕ} {a : ℝ}`. Its model `Real.log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x` takes them explicitly, as do the file's other unconditional equational simp lemmas `posLog_neg (x : ℝ)` and `posLog_abs (x : ℝ)`. So `rw [posLog_pow x 2]` cannot be written.",
  "requested_change": "Make the binders explicit and use the same variable and order as `Real.log_pow`: `@[simp] lemma posLog_pow (x : ℝ) (n : ℕ) : log⁺ (x ^ n) = n * log⁺ x`.",
  "severity": "advisory",
  "evidence": "file_read of Mathlib/Analysis/SpecialFunctions/Log/Basic.lean:266-267 shows `@[simp] theorem log_pow (x : ℝ) (n : ℕ) : log (x ^ n) = n * log x`. PosLog.lean:64 and :67 take `(x : ℝ)` explicitly in `posLog_neg` and `posLog_abs`. lean_verify_edit of `@[simp] lemma posLog_pow (x : ℝ) (n : ℕ) : log⁺ (x ^ n) = n * log⁺ x := by simp [posLog, mul_max_of_nonneg]`: compiled. No other declaration in the file uses `posLog_pow`."
 },
 {
  "target": "Real.posLog_pow",
  "claim": "The docstring of `Real.posLog_pow` says \"The function `log⁺` commutes with taking powers\", which is false. Commuting would mean `log⁺ (a ^ n) = (log⁺ a) ^ n`, but the lemma states `log⁺ (a ^ n) = n * log⁺ a`.",
  "requested_change": "Reword the docstring to state what the lemma says, e.g. `/-- The positive part of the logarithm of a natural power: `log⁺ (x ^ n) = n * log⁺ x`. -/`.",
  "severity": "advisory",
  "evidence": "Read the docstring at PosLog.lean:101 and the statement at :102-103 (file_read of the PR's file)."
 },
 {
  "target": "Real.posLog_norm_sum_le",
  "claim": "The first calc step of `Real.posLog_norm_sum_le` applies the named monotonicity lemma `monotoneOn_posLog` by hand (`apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)`) and leaves a nonnegativity side goal. The file has no `@[gcongr]` lemma for `log⁺`, so `gcongr` cannot do this step, and the same hand application recurs in `posLog_sum` and `posLog_norm_add_le`.",
  "requested_change": "Next to `monotoneOn_posLog`, add `@[gcongr] theorem posLog_le_posLog {x y : ℝ} (hx : 0 ≤ x) (hxy : x ≤ y) : log⁺ x ≤ log⁺ y := monotoneOn_posLog hx (hx.trans hxy) hxy`. Then write the first calc step of `posLog_norm_sum_le` as `_ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by gcongr; exact norm_sum_le s f`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit (line mode, lines 182-194) inserting the `@[gcongr] posLog_le_posLog` lemma above `posLog_norm_sum_le` and using `by gcongr; exact norm_sum_le s f` for the first step: compiled. The same calc step with `gcongr` but without the new lemma gives `gcongr did not make progress`. declaration_search `posLog_le_posLog`: absent at the base and in the PR."
 },
 {
  "target": "Real.posLog_norm_sum_le",
  "claim": "The proof of `Real.posLog_norm_sum_le` is a two-step tactic `calc`. Its first step uses `apply … _ …` to leave a placeholder goal and then closes that goal by passing a proof term to `simp` (`simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]`). The whole proof is a single `.trans` of two terms.",
  "requested_change": "Replace the proof with the term `(monotoneOn_posLog (norm_nonneg _) (Finset.sum_nonneg fun _ _ ↦ norm_nonneg _) (norm_sum_le s f)).trans (posLog_sum s (‖f ·‖))`, or with the `gcongr` step if a `@[gcongr]` lemma for `log⁺` is added.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Real.posLog_norm_sum_le with the term-mode proof `(monotoneOn_posLog (norm_nonneg _) (Finset.sum_nonneg fun _ _ ↦ norm_nonneg _)\\n    (norm_sum_le s f)).trans (posLog_sum s (‖f ·‖))`: compiled, no errors. `by positivity` for the middle argument fails (`not a positivity goal`, because the goal is `_ ∈ Set.Ici 0`), so the explicit `Finset.sum_nonneg` term is needed."
 },
 {
  "target": "Real.posLog_norm_sum_le",
  "claim": "`Real.posLog_norm_sum_le` assumes `[NormedAddCommGroup E]`, but its proof uses only `norm_nonneg` and the triangle inequality `norm_sum_le`, both of which hold for seminormed groups. The lemma is stated at a stronger typeclass than it needs.",
  "requested_change": "Weaken the hypothesis on `E` from `[NormedAddCommGroup E]` to `[SeminormedAddCommGroup E]` in `posLog_norm_sum_le`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Real.posLog_norm_sum_le with `[SeminormedAddCommGroup E]` and the PR's unchanged proof: compiled. The term-mode proof also compiles under `SeminormedAddCommGroup`."
 },
 {
  "target": "module_doc in Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean",
  "claim": "The sentence the PR adds to the module docstring capitalises a common noun mid-sentence: \"the presentation of `log⁺` as a Circle Average\".",
  "requested_change": "Write \"as a circle average\" in lower case in the new module-doc sentence.",
  "severity": "advisory",
  "evidence": "Read PosLog.lean:19-20 as the PR leaves it (file_read)."
 }
]
with open(f"{D}/findings.json", "w") as fh:
    json.dump(findings, fh, ensure_ascii=False, indent=1)
print(len(findings))
