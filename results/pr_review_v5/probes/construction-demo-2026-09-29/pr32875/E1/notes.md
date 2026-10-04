# PR #32875 review notes (chore: golf using `grind` and `simp`)

I read pr.md, model.md and diff.patch. I read each changed declaration in context with
`file_read` (workspace paths are under `target/`). I compiled each candidate edit with
`lean_verify_edit`. I also compiled LiminfLimsup, Portmanteau and Rat/Lemmas as the PR leaves
them: all three compile with no warnings, so every `simp only` argument in them is used.
`proof_profile` was unavailable: there is no declaration table for the base commit.

## Finset.mem_map_equiv (Data/Finset/Image.lean)
- The PR's proof is `simp only [mem_map, Equiv.coe_toEmbedding]` then `grind`. The PR's own
  profile reports it slower: <10 ms before, 25 ms after.
- `simp [Equiv.apply_eq_iff_eq_symm_apply]` proves it in one call (compiled), so I made finding 1.
- A single `grind [Equiv.coe_toEmbedding]` fails: grind never turns `f.toEmbedding w` into `f w`.
  The sibling `mem_map` is `@[simp, grind =]`; this `iff` lemma is not tagged `grind =`.
  `@[simp 1100, grind =]` compiles, so I made finding 2, following the `grind =` convention.
- Zulip has a Dec 2025 maintainer thread, "`simp only` + `grind` failure", on the fragility of
  the `simp only; grind` pattern.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean)
- The PR's proof is `simp only [den_inv, num_intCast]` then `grind`, and it got slower
  (<10 ms → 17 ms).
- `grind [den_inv, num_intCast]` compiles, merging the two calls into one, so I made finding 3.
  `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` also compiles; it matches the sibling
  `inv_intCast_num_of_pos := by simp [*]`.
- `grind [den_inv]` and `simp [ha0.ne', ha0.le]` do not close the goal.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean)
- The new ending is `simp only [pi_pi, this]` + `exact Fintype.prod_equiv _ _ _ (congrFun rfl)`.
  `congrFun rfl` stands for `fun _ ↦ rfl`, and `Fintype.prod_equiv`'s docstring points to
  `Equiv.prod_comp` for exactly this case.
- `rw [this, pi_pi, e.prod_comp fun i ↦ μ i (s i)]` compiles as one call, so I made finding 4.
  `exact e.prod_comp _` fails because the `CommMonoid` instance is stuck, so the function has to
  be given.
- The unchanged first part (the `e_meas` / `s'` / `this` setup) I left alone; it is not in scope.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (MeasureTheory/Measure/Portmanteau.lean)
- The new proof is `simp only [measureReal_eq_coe_coeFn, NNReal.toReal_limsup] at h` + `exact
  tendsto_of_forall_isClosed_limsup_le h`. It is a large speed-up (268 ms → <10 ms) and reduces
  to the NNReal version, which is the right dependency.
- `NNReal.toReal_limsup` is `@[simp, norm_cast]`, and `tendsto_of_forall_isClosed_limsup_le (by
  simpa using h)` also compiles as a term. That is a matter of taste, not an ask, so no finding.
  `mod_cast h F hF` does not work.
- The `[L.IsCountablyGenerated]` instance is still needed by the lemma it calls, so the
  unused-arguments linter has nothing to flag.
- Pre-existing and untouched by the PR: the lemma re-binds `{L : Filter ι}
  [L.IsCountablyGenerated]`, which the section `variable` already declares, and it has no
  docstring. Both are out of scope for a golf PR, so no finding.

## limsup_finset_sup' (Order/LiminfLimsup.lean)
- The new two lines (`simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢`;
  `exact fun i i_s ↦ eventually_lt_of_limsup_lt (hb i i_s) (h₂ i i_s)`) are clean. The file
  compiles without unused-simp-arg warnings, so `gt_iff_lt` is needed. No finding.
- The surrounding unchanged code (the `h₃` block, the second bullet's `simp only [le_sup'_iff];
  use i, i_s`) could be golfed further but is outside this PR's diff. Not reported.

## setLIntegral_condKernel_eq_measure_prod, kernel and measure versions (Probability/Kernel/Disintegration/Integral.lean)
- Both new proofs are `have : ... := by congr; exact (_.disintegrate _).symm`, then
  `simp only [this]`, then `exact (compProd_apply_prod hs ht).symm`.
- A one-line `rw [← compProd_apply_prod hs ht, ρ.disintegrate]` and its kernel analogue
  `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` both compile, so I made findings 5
  and 6. The sibling-style `conv_rhs => rw [← _.disintegrate _.condKernel]; rw [...]` also
  compiles. `simpa [ρ.disintegrate ρ.condKernel] using (compProd_apply_prod (μ := ρ.fst)
  (κ := ρ.condKernel) hs ht).symm` compiles too, but a plain `simpa` fails because
  `disintegrate` is not simp. `rw [← ρ.disintegrate ρ.condKernel, ...]` fails with a "motive is
  not type correct" error, which is why siblings use `conv_rhs`.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean)
- The new term proof `exists_between' h` uses the `to_dual` of `exists_between`
  (`Mathlib/Order/Basic.lean:1113`, `@[to_dual exists_between']`) and relies on `mem_ball` being
  definitional. It is idiomatic and much faster (81 ms → <10 ms). The docstring is unchanged and
  still accurate. No finding.

## Conventions checked
- Merging consecutive calls: findings 1, 3, 4, 5, 6.
- Short block written as a term: applied to exists_lt_mem_ball_of_mem_ball (already a term) and
  to the Portmanteau lemma (it would need a nested `by`, so no ask).
- `@[grind =]` on characterisation lemmas: finding 2 (mem_map_equiv). `inv_intCast_den_of_pos`
  is a conditional equation with a positivity hypothesis, so I made no ask.
- `simpa using` over backwards `←` simp rewriting: no changed proof rewrites the goal backwards
  with `←` simp lemmas. The closest is the `have`/`simp only [this]`/`exact` pattern in the
  condKernel lemmas, covered by findings 5 and 6.
