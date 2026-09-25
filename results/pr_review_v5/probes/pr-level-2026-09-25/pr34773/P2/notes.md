# PR #34773 — PR-level review notes (reviewer P2)

**1. Wanted / worth having?** Searched for existing entropy definitions. Mathlib has only `Real.binEntropy` and `Real.qaryEntropy` (BinaryEntropy.lean) plus topological entropy, so Shannon entropy of a distribution is new and wanted. Its form clashes with its sibling `klDiv` (KullbackLeibler/Basic.lean:57): `klDiv` is defined on `Measure` and is `ℝ≥0∞`-valued, while this definition is on `PMF`, is `ℝ`-valued, and uses `tsum`, which returns 0 when the sum diverges. It also takes the generic name `InformationTheory.entropy` → finding (advisory). None of the new public declarations is so trivial that it should be inlined. `entropy_pos_of_not_pure` is a normal API corollary.

**2. Every hunk an improvement?** Three hunks: the Mathlib.lean import, the new `negMulLog_pos_of_pos_lt_one` in NegMulLog.lean (used twice in `entropy_eq_zero_iff`; no strict-positivity lemma for negMulLog existed), and the new file. None is purely stylistic or unrelated. No finding.

**3. One thing?** Yes. The NegMulLog lemma is a direct prerequisite, and the scope matches the title. No finding.

**4. Description?** It is empty: no motivation, no design rationale (PMF vs Measure, ℝ + junk 0 vs `klDiv`'s ℝ≥0∞), and no Zulip or downstream links → blocking. It also has no AI disclosure despite clear signs of generated text (meta-comments, curly quotes, step-narration comments, duplicated helper proofs) → blocking.

**5. Finishes the job?** The PR gives a binEntropy bridge but no qaryEntropy bridge. Mathlib has no q-ary PMF, so that is not a gap to hold against this PR. There is no automation to test. Four sanity `example`s sit in the library file. Mathlib/InformationTheory has zero examples, and tests belong in MathlibTest → finding (advisory).

**6. Right place?** `InformationTheory/` is a reasonable directory. Two things are in the wrong place: `nat_mul_negMulLog_inv_eq_log` is a public real-analysis helper in the `InformationTheory` namespace and belongs in NegMulLog.lean or should be private → finding. The private helpers re-prove a missing general PMF fact (`p a = 1 → p = pure a`, twice) and re-derive `(p a).toReal ≤ 1` three times; these belong as public lemmas in ProbabilityMassFunction/{Monad,Basic}.lean → finding. The file name `Entropy.lean` for a PMF-only notion is covered by the question-1 finding.
