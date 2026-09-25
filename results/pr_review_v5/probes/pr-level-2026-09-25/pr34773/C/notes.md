# PR 34773 — reasoning notes

- `Mathlib.lean`: the import line is in the correct alphabetical position. No request.
- `NegMulLog.lean` / `negMulLog_pos_of_pos_lt_one`: searched; no strict-positivity lemma for negMulLog or `mul_log_neg` exists, so the lemma is new and belongs in this file. Its sibling `negMulLog_nonneg` sets the naming convention, so I asked for `negMulLog_pos`.
- `entropy` (def): the docstring formula has lost its minus sign (blocking doc fix). `klDiv` is measure-based in the same namespace, so a PMF-only `InformationTheory.entropy` is a design mismatch (advisory generalization).
- `entropy_pure`: the proof is a bit manual but acceptable; no request.
- `entropy_nonneg`: correct. Suggested a positivity extension, since `@[simp]` alone does not help `positivity`.
- `support_nontrivial_of_not_pure` / `toReal_lt_one_of_mem_support_of_not_pure`: both contain the same "p a = 1 → p = pure a" block, and Monad.lean has no `eq_pure_iff`, so I asked to extract it as public PMF API. `hx` is unused in the second lemma.
- `negMulLog_ite_nonneg` / `entropy_tsum_ite_ge`: exist only for the ite-splitting route; `Summable.tsum_pos` (Order.lean:228) with one positive term makes them unnecessary. Folded into the `entropy_eq_zero_iff` restructuring finding.
- `entropy_eq_zero_iff`: needs only one support point with 0 < p < 1; the statement continuation is indented 2 spaces; `Finite` is used only for summability (generalization).
- `entropy_pos_of_not_pure`: a one-term proof exists; `(α := α)` is redundant.
- `entropy_bernoulli_eq_binEntropy`: unfolds `ENNReal.toReal` inside `simp_all` (fragile); the name is inconsistent with `entropy_pure` / `entropy_uniformOf*`.
- `nat_mul_negMulLog_inv_eq_log`: `log_inv` holds for all reals and log 0 = 0, so `x * negMulLog x⁻¹ = log x` holds with no hypothesis. It should live in NegMulLog.lean with a short proof, not as a public InformationTheory lemma phrased through ENNReal.
- `entropy_uniformOfFintype`: `uniformOfFintype` is definitionally `uniformOfFinset univ`, so it is a corollary of `entropy_uniformOfFinset`.
- `entropy_uniformOfFinset`: unfolds the `uniformOfFinset` definition although `_apply_of_mem` / `_apply_of_notMem` exist; the calc and `set`s can go.
- Examples: they belong in MathlibTest, and the `Fin n` docstring mis-states the range.
- Imports: NegMulLog is imported redundantly (BinaryEntropy publicly imports it). Too minor to report.
