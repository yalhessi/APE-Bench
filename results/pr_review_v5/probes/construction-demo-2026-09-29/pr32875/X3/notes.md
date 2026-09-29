# Reviewer notes: PR #32875 (X3)

This PR golfs proofs only. No statement, name, attribute or docstring changes. I read `pr.md`,
`model.md` and `diff.patch`, then used `ptool` to read files (the workspace root is `target/`),
search content and declarations, check Zulip and precedents, and compile edits with
`lean_verify_edit`. For timing, I spliced copies of the declarations wrapped in
`set_option profiler true in` / `set_option profiler.threshold 1 in` (line mode), because
`count_heartbeats` is not imported in these files.

Precedent search on the `simp only [...]; grind` shape returned nothing relevant. Zulip had general
maintainer comments that golfs should not make proofs slower (Eric Wieser on profiling
"`grind` works in place of `tac; grind`, but is 50% slower"). There was also a thread on fragile
`simp only` + `grind` combinations. Neither decides anything for this PR on its own.

## Finset.mem_map_equiv (Data/Finset/Image.lean) -- finding (advisory)
- The PR proof `simp only [mem_map, Equiv.coe_toEmbedding]; grind` compiles. The PR's own trace
  says it got slower (<10 ms to 25 ms).
- `grind` alone and `grind [Equiv.coe_toEmbedding]` fail, so the `simp only` exists only to feed
  `grind`.
- `simp [Equiv.apply_eq_iff_eq_symm_apply]` compiles as a one-liner. Profiled in place: PR ≈ 11 ms
  of tactic time, simp ≈ 5 ms, original ≈ 3 ms. I asked for the one-line simp, or keeping the
  original.
- Sibling `mem_map_equiv` lemmas for Subgroup, Submonoid, Subring and others are term proofs via
  `Set.mem_image_equiv`. `Finset.coe_map` is not in scope under that name here, so I did not push
  a term-mode proof.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean) -- finding (advisory)
- The PR proof `simp only [den_inv, num_intCast]; grind` compiles, but profiles at about 24 ms of
  tactic time plus 7 ms of type checking. The original rw proof and
  `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` both take about 3 ms. The PR trace also reports a
  slowdown (<10 ms to 17 ms).
- The sibling `inv_intCast_num_of_pos` is `by simp [*]`. `simp [*]` and `simp [ha0.ne', ha0.le]`
  leave `natAbs` goals, so the `Int.natAbs_of_nonneg` fact is needed.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean) -- finding (advisory)
- Only the tail changed. `Fintype.prod_equiv _ _ _ (congrFun rfl)` is an obscure spelling of
  `fun _ ↦ rfl`, with the equivalence left to unification. `Equiv.prod_comp` is the lemma the
  `Fintype.prod_equiv` docstring recommends when no `h` is needed.
- `rw [this, pi_pi]; exact e.prod_comp fun i ↦ μ i (s i)` compiles. `e.prod_comp _` does not:
  the CommMonoid metavariable gets stuck.
- The earlier part of the proof (`e_meas`, `s'`, `this`) is untouched by the PR. No request there.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (Measure/Portmanteau.lean) -- no finding
- The new proof reduces to the NNReal version `tendsto_of_forall_isClosed_limsup_le` via the simp
  lemmas `ProbabilityMeasure.measureReal_eq_coe_coeFn` (ProbabilityMeasure.lean:156) and
  `NNReal.toReal_limsup` (Order/Filter/ENNReal.lean:137). Both exist at the base. It is a clear
  improvement (268 ms to <10 ms) and it is idiomatic.
- The lemma repeats the section's `{L : Filter ι} [L.IsCountablyGenerated]` binders and has no
  docstring, but both are pre-existing and outside this golf. I did not raise them.

## limsup_finset_sup' (Order/LiminfLimsup.lean) -- no finding
- The new `simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢` followed by
  `exact fun i i_s ↦ eventually_lt_of_limsup_lt (hb i i_s) (h₂ i i_s)` is a sound, clearly shorter
  replacement for the manual `⋂` construction. `eventually_all_finset` exists (Order/Filter/Finite.lean:246).
- The untouched `h₃` block could be golfed too, but that is outside the PR's change. No request.
- The dual `liminf_finset_inf'` is derived from it via `βᵒᵈ` and is unaffected.

## ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod and MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod (Probability/Kernel/Disintegration/Integral.lean) -- two findings (advisory)
- Both keep a `have ... := by congr; exact (_.disintegrate _).symm`, then `simp only [this]` with a
  single local equation, then a `.symm` term.
- `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` and
  `rw [← compProd_apply_prod hs ht, ρ.disintegrate]` each compile as the whole proof. The variants
  following the file's own `conv_rhs => rw [← _.disintegrate _.condKernel]` idiom compile too.
  I recorded one finding per declaration.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean) -- no finding
- `exists_between' h` is the `to_dual` of `exists_between` (Order/Basic.lean:1113) with type
  `a₁ < a₂ → ∃ a, a < a₂ ∧ a₁ < a`. It matches `∃ ε' < ε, x ∈ ball y ε'` through the definitional
  `mem_ball`, which Mathlib routinely uses. The docstring is unchanged and still accurate.

## Across the PR
- Naming, documentation, scope and correctness: no declaration is renamed, added or removed. No
  docstring is affected. The file count fits the stated batching guideline for a golf PR. I found
  no semantic change, since the statements are unchanged and the PR proofs compile.
