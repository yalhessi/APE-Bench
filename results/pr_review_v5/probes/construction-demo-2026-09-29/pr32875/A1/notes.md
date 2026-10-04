# Review notes: PR #32875 "chore: golf using `grind` and `simp`"

I read brief.md, pr.md, model.md and diff.patch, then called `ptool describe`. Every edit I
propose was checked with `lean_verify_edit` against the PR's workspace, under the declaration's
real name and in place. To time proofs I put copies of the variants beside the declaration, with
`set_option profiler true in` (threshold 1 ms). Scratch argument files are in `tmp/`.

## Finset.mem_map_equiv (Data/Finset/Image.lean)
- The PR changes the proof to `simp only [mem_map, Equiv.coe_toEmbedding]; grind`. The author's
  own trace shows it got slower: <10 ms before, 25 ms after.
- What I tried:
  - Plain `simp` fails; the goal `(∃ a ∈ s, f a = b) ↔ f.symm b ∈ s` is left.
  - `grind [Equiv.coe_toEmbedding, Equiv.apply_eq_iff_eq_symm_apply]` fails.
  - `simp [Equiv.apply_eq_iff_eq_symm_apply]` compiles, both in place and as a variant placed
    before the declaration (so simp cannot use the lemma itself).
- Profile: PR version about 13-15 ms; original about 6 ms; one-call `simp` about 9 ms.
- Finding (advisory): use the single `simp`, or revert the hunk.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean)
- The PR changes the proof to `simp only [den_inv, num_intCast]; grind`. The author's trace:
  <10 ms before, 17 ms after.
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles in place. `simp [ha0.ne', ha0.le]` alone
  leaves `↑a.natAbs = a`.
- Profile: proposed simp about 2-3 ms; original rw chain about 3 ms; PR version grind 3-50 ms
  plus 7 ms type-checking the grind term.
- Finding (blocking): the golf makes a cheap lemma several times slower, and a one-call `simp` of
  the same length exists.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean)
- The PR ends with `simp only [pi_pi, this]; exact Fintype.prod_equiv _ _ _ (congrFun rfl)`.
- This is `Equiv.prod_comp` (Defs.lean:724) rebuilt by hand. The `e` is inferred only by
  unification through `congrFun rfl`, and `simp only` is used for a plain rewrite.
- These compile in place:
  - `rw [this, pi_pi]; exact e.prod_comp fun i ↦ μ i (s i)`;
  - the one-line `rw [..., e.prod_comp fun i ↦ μ i (s i)]`;
  - `Fintype.prod_equiv e _ _ fun _ ↦ rfl`.
- `e.prod_comp _` fails with a stuck CommMonoid instance.
- Finding (advisory).
- I did not ask for any change to the unchanged `have`/`s'` part, since this PR does not touch it.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (Measure/Portmanteau.lean)
- The PR reduces the proof to the NNReal version, `tendsto_of_forall_isClosed_limsup_le`. After
  `simp only [ProbabilityMeasure.measureReal_eq_coe_coeFn, NNReal.toReal_limsup] at h`, `h` reads
  `↑(limsup …) ≤ ↑(μ F)` in ℝ.
- `exact` accepts it through `NNReal.coe_le_coe`, which is `Iff.rfl`, so that defeq is benign.
  Adding `NNReal.coe_le_coe` also compiles but is not worth asking for.
- Alternatives I tried (`simpa … using h` as the argument, `exact_mod_cast`) compile but are slower
  (about 40-270 ms against the PR's about 4 ms).
- No finding.
- Not raised, because untouched by the PR: the lemma re-binds `{L : Filter ι}
  [L.IsCountablyGenerated]`, which the section `variable` already provides, and it has no docstring.

## limsup_finset_sup' (Order/LiminfLimsup.lean)
- The new `simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢` followed by `exact`
  is correctly squeezed, since a later step consumes its output. It uses the filter API
  (`eventually_all_finset`).
- `gt_iff_lt` is unnecessary: the proof compiles without it, with line 1155 replaced in place.
- Finding (advisory, minor).
- Not raised, because untouched by the PR: the `h₃` construction and the `le_sup'_iff; use` branch
  could be golfed further.

## ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod and MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod (Probability/Kernel/Disintegration/Integral.lean)
- Both keep a `have this : κ a (s ×ˢ t) = (fst ⊗ compProd) …`, then `simp only [this]` and
  `exact (compProd_apply_prod hs ht).symm`.
- `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` compiles in place, and so does
  `rw [← compProd_apply_prod hs ht, ρ.disintegrate]` for the measure version.
- The sibling-style `conv_rhs => rw [← κ.disintegrate κ.condKernel]; rw [...]` also compiles for
  both, matching `lintegral_condKernel` and `setLIntegral_condKernel` in the same file.
- Two advisory findings, one per declaration. They are twins and one decision.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean)
- The PR's term proof `exists_between' h` uses the `to_dual` companion of `exists_between`
  (Order/Basic.lean:1113). It relies on `x ∈ ball y ε` unfolding to `dist x y < ε`, which `mem_ball`
  states as `Iff.rfl`.
- This is standard in Mathlib and the docstring is unchanged.
- No finding.

## PR-level
- Description: the "batched under the following guidelines" section is boilerplate, and the PR
  (7 files) does not meet its "~5 files" line. Finding (advisory): drop it.
- Title: `chore: golf using grind and simp` has no single area to name across 7 directories, so
  `chore:` is the normal form. Only two hunks actually use `grind`; the rest golf through library
  lemmas. Not raised.
- The profiling table is useful and should stay. It is what shows that the two `grind` hunks
  regress.
- Scope: each hunk is an independent golf, so there is no seam that forces a split.
