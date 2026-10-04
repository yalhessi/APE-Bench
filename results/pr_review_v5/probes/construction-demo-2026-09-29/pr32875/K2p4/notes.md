# Pass 4 (proofs) — PR #32875, `chore: golf using grind and simp`

Every proof compiled with `lean_verify_edit` against the reviewed workspace. Timings come from
`set_option profiler true` / `profiler.threshold 1` in a line-mode edit. Each is **one run**, so it is
indicative only. I use them only where they agree in direction with the PR's own trace. No family
was found by the change graph. The two `setLIntegral_condKernel_eq_measure_prod` lemmas are
treated as one family (kernel / measure), and both proofs change the same way. `proof_profile` was
unavailable (no declaration table for the base commit), so the "library's way" below comes from the
files' own siblings, not from a corpus ranking.

## `Finset.mem_map_equiv` (c1-c3) — finding 1
- PR: `simp only [mem_map, Equiv.coe_toEmbedding]; grind`. The `simp only` is there only because
  `grind` cannot see `Equiv.toEmbedding_apply` (pass 3 c3/c6).
- Idiom: `simp [Equiv.apply_eq_iff_eq_symm_apply]` closes it in one terminal simp (c1), and was
  cheaper than the PR in the profiler run.
- Library as tool: `grind [Equiv.toEmbedding_apply]` is one call (c2). It is no faster than the PR.
- Pre-PR proof compiles (c3) and is cheapest in the run, in line with the PR's own trace
  (<10 → 25 ms).
- No derivation or repetition applies. `mem_map'`, which would give a derivation, is declared after it.

## `Rat.inv_intCast_den_of_pos` (c4-c11) — finding 2
- PR: `simp only [den_inv, num_intCast]; grind`, where `grind` closes `↑(if a = 0 then 1 else a.natAbs) = a`.
- `simp [ha0.ne', ha0.le]` and the `abs` route fail here: `abs_of_pos` and `Int.natCast_natAbs`
  are not in scope in this file (c4-c6).
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` (c7) and the `rw` chain
  `den_inv, num_intCast, if_neg ha0.ne', Int.natAbs_of_nonneg ha0.le` (c8) both compile. Each costs
  about 2-4 ms, against about 22 ms for the PR's proof (grind 10.8 ms plus 8.4 ms kernel type
  checking). c7 is in the siblings' form (`simp [*]`, `simp [den_inv, Int.natAbs_eq_iff]`).
- `omega` in place of `grind` (c9) is just as heavy. `simpa … using Int.natAbs_of_nonneg` works (c10).
- Pre-PR proof compiles (c11) at about 2 ms, in line with the PR's trace (<10 → 17 ms).
- Pass 3 c13 (special case of `inv_intCast_den`, l.322) would need reordering. c7 is that
  derivation inlined.

## `MeasureTheory.Measure.pi_map_piCongrLeft` (c12-c17) — findings 3, 4
- PR keeps the `let e_meas` / `let s'` / `ext` / `have` block and ends with
  `simp only [pi_pi, this]; exact Fintype.prod_equiv _ _ _ (congrFun rfl)`.
- The closing step is `e.prod_comp fun i ↦ μ i (s i)` (c13) or `Fintype.prod_equiv e _ _ fun _ ↦ rfl`
  (c12). `congrFun rfl` is a disguised `fun _ ↦ rfl`, and it leaves the equivalence to unification.
  A pure `rw` ending fails because of the `let s'` (c14).
- The whole proof is the two-step `pi_eq` plus a `rw` chain through
  `Equiv.piCongrLeft_preimage_univ_pi` and `Equiv.prod_comp` (c15). That is literally the proof of
  `measurePreserving_piCongrLeft.map_eq` at l.724-727, it compiles at l.446, and it is cheaper.
- Derivation (c17): with c15 in place, `measurePreserving_piCongrLeft` takes
  `map_eq := Measure.pi_map_piCongrLeft f μ`. The edit over l.446-727 compiles, and the fact is then
  proved once.
- Pre-PR proof compiles (c16).

## `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'` (c18-c20) — no finding
- PR: `simp only [measureReal_eq_coe_coeFn, NNReal.toReal_limsup] at h; exact tendsto_of_forall_isClosed_limsup_le h`.
  This is the library's way: it reduces to the NNReal portmanteau lemma just above.
- A bare `simpa using h` term form (c18) is shorter but much slower (DiscreteTopology/T1Space
  searches, 36 ms of simp). The PR's `simp only` is the right call. The `simpa only … using h` term
  form (c19) costs the same as the PR's, so there is nothing to ask.
- Pre-PR proof compiles (c20), dominated by `finiteness` (aesop 272 ms). The PR's 268 → <10 ms is real.

## `limsup_finset_sup'` (c21-c24) — no finding
- The PR's ≤ branch (`simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢; exact …`)
  is the library's route. `gt_iff_lt` can be dropped (c21), but the unused-simp-args linter does not
  flag it, so this is only a nit and not a request.
- The unchanged branches can also become terms (c22: `hs.imp …` for `h₃`, `le_sup'` for ≥). That
  is outside what the PR changed.
- Pre-PR proof compiles (c23).
- Derivation (c24): `limsup_max` follows from `limsup_finset_sup'` in three lines, even in a
  conditionally complete order with explicit bounds. But `limsup_max` is untouched and comes
  earlier in the file, so this is no request on this PR. The duals `liminf_finset_inf'` /
  `liminf_min` are already derived through `βᵒᵈ`.

## `setLIntegral_condKernel_eq_measure_prod`, kernel and measure (c25-c32) — finding 5
- PR: keeps `have : κ a (s ×ˢ t) = (fst κ ⊗ₖ condKernel κ) a (s ×ˢ t) := by congr; exact (κ.disintegrate _).symm`,
  then `simp only [this]; exact (Kernel.compProd_apply_prod hs ht).symm`, and the same for the
  measure version.
- The file's idiom, `conv_rhs => rw [← κ.disintegrate κ.condKernel]` then one `rw`, is used by
  all 10 siblings. It compiles for both (c25, c30).
- A one-line `rw [← compProd_apply_prod hs ht, disintegrate]` compiles for both (c27, c31).
- `simp only [this]` can simply be `rw [this, …]` (c26).
- Pre-PR proofs compile (c28, c32).
- Derivation from `setLIntegral_condKernel` with `f = 1` (c29, after l.79) works, but it needs
  reordering and is heavier. No request.
- Repetition: the fragment the two proofs share is exactly the `disintegrate` rewrite. The idiom
  already expresses it, so no lemma was extracted.

## `Metric.exists_lt_mem_ball_of_mem_ball` (c33-c34) — no finding
- PR: `exists_between' h` (the `to_dual` of `exists_between`). The file's siblings use
  definitional ball membership the same way (`pos_of_mem_ball`), so this is the library's proof.
- `exists_between' (mem_ball.1 h)` also works (c34) but is unnecessary.
- Pre-PR proof compiles (c33), with two `linarith` calls at about 40 ms in total.
- This file carries 12 errors already in this environment (private `dist_nonneg'`, l.127 onward).
  Every edit here was checked as "no errors introduced".
