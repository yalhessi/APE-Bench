# Review notes: PR #32875 (chore: golf using `grind` and `simp`)

All eight changed declarations change only their proofs. No statement, name or docstring changes,
so naming, documentation and generalization asks apply only where a proof now shows a statement
could change, and none did. I compiled every proposed edit with `lean_verify_edit`. Timings come
from adding `set_option trace.profiler true in` to the replacement declaration. For the
profiled calls the tool then also reported a spurious "unexpected token 'set_option'" splice
error, but the profiler output was still produced; I confirmed every proposal compiles in a run
without the profiler option.

## Finset.mem_map_equiv (Data/Finset/Image.lean)
- The PR's proof `simp only [mem_map, Equiv.coe_toEmbedding]; grind` takes 25 ms, of which grind
  is 20 ms. The old proof took about 11 ms. The PR description itself reports <10 → 25 ms.
- Bare `by grind` fails, and so does `grind [Equiv.coe_toEmbedding]`.
- `simp only [mem_map, Equiv.coe_toEmbedding, Equiv.apply_eq_iff_eq_symm_apply, exists_eq_right]`
  compiles and stays under the 10 ms reporting threshold. `simp [mem_map,
  Equiv.apply_eq_iff_eq_symm_apply]` also compiles. → advisory finding.
- `grind` is already used in this file (`forall_mem_map`, `coe_map`), so I make no style
  objection to grind as such.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean)
- The PR's proof takes 42 ms here; the old proof was under 10 ms. The PR description reports
  <10 → 17 ms.
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles and is under 10 ms, matching the
  sibling `inv_intCast_num_of_pos := by simp [*]`. `simp [ha0.ne']; lia` also compiles (26 ms).
- `inv_intCast_den` is declared later in the file, so it cannot be used here. → advisory finding.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean)
- The PR replaces only the tail. The hand-rolled preimage `have` stays, and the new tail uses
  `(congrFun rfl)` as an obfuscated `fun _ ↦ rfl`.
- `measurePreserving_piCongrLeft`, at line 720 of the same file, is the same statement with ι and
  ι' swapped, proved by
  `rw [MeasurableEquiv.map_apply, MeasurableEquiv.coe_piCongrLeft, Equiv.piCongrLeft_preimage_univ_pi, pi_pi, f.prod_comp …]`.
- Transplanting that chain compiles: 18 ms against 78 ms, and 2 tactic lines against 13. The
  minimal fallback (`rw [this, pi_pi]; exact Fintype.prod_equiv e _ _ fun _ ↦ rfl`) also compiles.
  → advisory finding.
- It is a possible scope point that the lemma could become `(measurePreserving_piCongrLeft μ e).map_eq`
  if reordered. That is out of scope for a golf PR, so I did not raise it.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (MeasureTheory/Measure/Portmanteau.lean)
- The new proof reduces to the unprimed NNReal version `tendsto_of_forall_isClosed_limsup_le`, a
  genuine simplification that removes the ⊥-filter case split. The file compiles as the PR leaves
  it, with no warnings.
- The lemma still has no docstring, and it rebinds `{L} [L.IsCountablyGenerated]`, which the
  section variables already provide. Both predate the PR, so I did not raise them on a golf PR.
  No finding.

## limsup_finset_sup' (Order/LiminfLimsup.lean)
- The new `simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢` plus `exact`
  compiles. Dropping `gt_iff_lt` also compiles, but that is too small a nit to request.
- The untouched parts (`h₃` and the second `le_antisymm` branch) can be golfed further:
  `hs.imp fun i i_s ↦ ⟨i_s, h₁ i i_s⟩` and `le_sup' (fun i ↦ F i a) i_s`. This compiles and
  saves about 25%. I did not raise it because those lines are outside the PR's diff. No finding.

## ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod and MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod (Probability/Kernel/Disintegration/Integral.lean)
- The PR keeps a `have … := by congr; exact (disintegrate _).symm`, uses it through
  `simp only [this]`, then ends with `exact (compProd_apply_prod hs ht).symm`.
- `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` and
  `rw [← compProd_apply_prod hs ht, ρ.disintegrate]` each compile as the whole proof. So does the
  file's own `conv_rhs => rw [← _.disintegrate _]` idiom, which the neighbouring lemmas use.
  → one advisory finding per declaration (they are one family).

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean)
- `exists_between' h` is the `to_dual` of `exists_between`, generated in Order/Basic.lean at line
  1113. It typechecks through the definitional unfolding of `mem_ball`, which is `Iff.rfl`, a
  normal idiom in this file.
- Compiling the file with no edit reports errors at lines 127, 168 and 1061+: private
  `dist_nonneg'` in a structure default and missing `edist`. These are artifacts of the review
  environment's module setup, are unrelated to line 378, and none touches the changed lemma.
  No finding.

## Other checks
- Zulip search found a late-2025 maintainer thread on `simp only` + `grind` failures and a remark
  by Eric Wieser that golfs to grind should come with profiling. Together they support asking
  for the slowed-down grind golfs to be replaced.
- precedent_search turned up nothing directly applicable. One jcommelin comment prefers a local
  `rw` over `simp`.
