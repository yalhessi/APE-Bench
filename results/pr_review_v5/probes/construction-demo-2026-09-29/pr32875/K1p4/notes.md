# Pass 4 (proofs) — PR #32875, "chore: golf using `grind` and `simp`"

## How the constructions were made
- Every construction was compiled with `lean_verify_edit` against the PR's workspace. Candidates
  replace the PR's declaration in place (line mode or `declaration_name`) unless the entry says
  "inserted after".
- Timings come from `set_option profiler true` with `profiler.threshold 1`, placed in front of the
  declaration. They are the sum of the entries of 1 ms or more, so each is a lower bound with roughly
  ±20% noise between runs. Where a finding rests on a timing, the numbers are 3 runs.
- The `profiler.threshold` line cannot follow a docstring, so the Metric timings came from runs that
  also reported a docstring parse error. The declarations themselves still elaborated. The Metric
  compile results were then rechecked in `declaration_name` mode, where the edit introduced no
  errors. Separately, the Metric file has 12 errors already present in this environment, all from
  the private `dist_nonneg'` at line 127.
- A deliberately wrong proof was compiled first. It was reported as an introduced error, so a clean
  result is informative.
- `file_read`/`content_search` need the `target/` prefix. `proof_profile` was unavailable: its
  declaration table was not built for this commit.

## Finset.mem_map_equiv (Data/Finset/Image.lean)
- Pre-PR proof (c1): compiles, ~5.5 ms. The PR's `simp only [mem_map, Equiv.coe_toEmbedding]; grind`
  takes 12.3–15.3 ms over 3 runs, which agrees with the PR's own "<10 → 25 ms".
- Idiom (c2): `simp [Equiv.apply_eq_iff_eq_symm_apply]` takes one line and ~7 ms. The squeezed
  `simp only [..., Equiv.apply_eq_iff_eq_symm_apply, exists_eq_right]` (c3) takes ~5 ms. A lone
  `grind [Equiv.coe_toEmbedding]` fails (c4), so the PR's pair cannot be merged into one grind call.
  A term-mode proof (c5) and the injectivity route (c6) also work but are no better. The sibling
  `mem_map'` is declared after this lemma (c7).
- Finding F1 (advisory): use the one-line simp, or drop the hunk.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean)
- The goal the PR hands to grind is `↑(if a = 0 then 1 else a.natAbs) = a` (c17).
- Pre-PR proof ~3 ms (c8). The PR's proof takes 24.5–28.7 ms.
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` (c9) takes 3–5 ms. The `rw` chain with `if_neg` and
  `Int.natAbs_of_nonneg` (c10) takes ~2 ms.
- Other closers are slower: `simp; omega` (c11) ~14 ms, `simp; lia` (c12) ~40 ms,
  `split_ifs <;> omega` (c13) ~63 ms, and `grind [den_inv, num_intCast]` (c16) ~75 ms.
- `simp [*]` (c14) and `simp [ha0.ne', ha0.le]` (c15) fail.
- Finding F2 (advisory).

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean)
- Pre-PR proof ~52 ms (c18). The PR's proof takes 41–48 ms: the PR removed only the `congr` step.
  The cost the PR keeps is in the preamble, where the `have` does four CoeT searches of ~4 ms each.
- If the structure is kept, the idiomatic tail is `rw [this, pi_pi]` with
  `Fintype.prod_equiv e _ _ fun _ ↦ rfl` (c19) or `e.prod_comp` (c20).
- Library tool: the six-line `have` is exactly `Equiv.piCongrLeft_preimage_univ_pi e s` (c21). The
  3-line proof of `measurePreserving_piCongrLeft` from the same file compiles here and takes 10–13 ms
  (c22).
- Derivation: with this lemma in place, `measurePreserving_piCongrLeft.map_eq := pi_map_piCongrLeft f μ`
  compiles (c23), so the equation need only be proved once.
- Finding F3 (advisory). Pass 3 recorded the duplicated statement; this finding is about which
  proof to keep.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (Portmanteau.lean)
- Pre-PR proof ~420 ms, 332 ms of it in `finiteness`/aesop (c24). The PR's proof takes ~9 ms, a real
  improvement.
- Derivation (c25): the PR derives the lemma from the ℝ≥0 member. After its `simp only`, h is an
  inequality in ℝ between ℝ≥0 casts, and `exact` accepts it only by unfolding the ℝ≥0 order.
  Adding `NNReal.coe_le_coe` (c26) makes that step a rewrite at the same cost. A term-mode
  `simpa` (c27) works but costs ~25 ms.
- Finding F7 (advisory, minor).

## limsup_finset_sup' (Order/LiminfLimsup.lean)
- Pre-PR proof ~57 ms, PR ~61 ms (c28), one run each. The PR's reported 64 → 51 ms is not visible at
  this resolution.
- The PR's middle step is already idiomatic: a `simpa using` variant (c29) is no better.
- A whole-proof rewrite in the style of the sibling `limsup_max` (c30), using `hs.imp` for `h₃` and a
  term `le_sup'` for the `≥` half, is 7 lines against 13 at the same cost.
- The dual `liminf_finset_inf'` and `limsup_finset_sup` still derive from this member (c31).
- Finding F6 (advisory; the change is outside the diff hunk but inside the proof the PR modifies).

## ProbabilityTheory / MeasureTheory.Measure .setLIntegral_condKernel_eq_measure_prod (Kernel/Disintegration/Integral.lean)
- Kernel member: pre-PR proof ~42 ms (c32). The PR's proof takes 13–16 ms.
  - The file's own idiom (`conv_rhs => rw [← κ.disintegrate κ.condKernel]; rw [Kernel.compProd_apply_prod hs ht]`),
    used by every sibling in the file, takes 5–6 ms (c33). The one-liner
    `rw [← Kernel.compProd_apply_prod hs ht, κ.disintegrate]` takes 5.5–8 ms (c34).
  - With the `have` kept, `simp only [this]; exact (...).symm` is just `rw [this, ...]` (c35).
  - The repeated `have` fragment is `rw [κ.disintegrate]` (c36), so it is not worth extracting.
  - At this position the `f = 1` specialisation of `setLIntegral_condKernel` is unavailable: that
    lemma is declared later (c37).
- Measure member: pre-PR proof ~57 ms (c38). The PR's proof takes ~27 ms. The conv form (c39) takes
  ~21 ms and the one-line rw (c40) ~31 ms. A 17–25 ms SFinite instance search dominates every
  variant, so here the gain is length and consistency, not time. The fragment is
  `rw [ρ.disintegrate]` (c41).
- Findings F4 and F5 (advisory). They are one decision for the pair.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean)
- Pre-PR proof ~42 ms, from two linarith calls (c42). The PR's `exists_between' h` takes ~3 ms.
- `exists_between'` is the `to_dual` of `exists_between`, with statement
  `a₂ < a₁ → ∃ a < a₁, a₂ < a` (c43). That is exactly the target's shape, and the proof uses the
  same `mem_ball` defeq as `pos_of_mem_ball` next to it.
- The form written before `to_dual`, `(exists_between h).imp fun _ ↦ And.symm` (c44), is longer and
  no cheaper. Unfolding with `mem_ball.1` (c45) gains nothing.
- No finding: this is the proof the library would write.
