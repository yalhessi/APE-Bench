# PR #34773: reviewer P1 (the PR as a change)

**Q1. Is the change wanted?** Mathlib has no Shannon entropy of a distribution. The searches found only `Real.binEntropy`/`qaryEntropy` and topological entropy, and no "entropy" anywhere in Probability, InformationTheory or MeasureTheory. So the addition is wanted. The form is the problem. It is a PMF-only, ℝ-valued `tsum` (junk 0 when the sum diverges) under the generic name `InformationTheory.entropy`. Next to it, `klDiv` is built on `Measure` and takes values in ℝ≥0∞, and PMF is used nowhere in InformationTheory, Kernel, Independence or Moments. Filed as blocking: agree the design first. The new NegMulLog lemma has no existing duplicate.

**Q2. Is every hunk an improvement?** Every hunk is new material, and none is a purely stylistic edit to existing code. The one hunk that adds nothing is the closing Examples section, which only restates lemmas the file just proved. It is filed under Q6, as a location question.

**Q3. Is it one thing?** Yes. The one change outside the new file is the NegMulLog lemma, which `entropy_eq_zero_iff` uses, plus the `Mathlib.lean` import (in alphabetical order). The scope matches the title. Nothing to split.

**Q4. Does the description do its job?** The description is empty. It has no motivation, no design rationale (PMF vs Measure, codomain, name), no linked discussion or downstream work, no mention of the NegMulLog addition, and no AI disclosure. The file shows signs of machine assistance: curly quotes, running "goal is now" comments, and a proof block pasted twice. Filed as blocking.

**Q5. Does it finish the job?** The PR adds no automation or meta code, so there are no tests to check. The analogous-places question was checked. NegMulLog pairs `mul_log_nonpos` with `negMulLog_nonneg`, and the strict `mul_log` counterpart is missing too. `binEntropy_pos` proves its positivity inline. Neither seemed worth requesting. The API gap that matters, `PMF.eq_pure_iff`, is filed under Q6.

**Q6. Is it in the right place?** Three findings, all advisory:
- The general PMF fact `p a = 1 → p = pure a` is proved privately, twice. It belongs in `ProbabilityMassFunction/Monad.lean`, where no such lemma exists.
- `nat_mul_negMulLog_inv_eq_log` is a public real-analysis lemma in the `InformationTheory` namespace. It should be private, or moved to NegMulLog.lean as `x * negMulLog x⁻¹ = log x`.
- The Examples section should be deleted or moved to MathlibTest.

Where the file sits (`InformationTheory/Entropy.lean`) is folded into the Q1 design finding.
