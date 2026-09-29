# Pass 3 notes: PR #32875 (chore: golf using `grind` and `simp`)

The PR changes proofs only. No statement is added, removed, renamed or modified, and the change
graph finds no families. So this pass asks whether the unchanged statements of the eight touched
declarations serve their consumers. The only way this PR can bear on that is through what the new
proofs reveal. I grouped each touched declaration with its siblings in the file into a family (the
two `setLIntegral_condKernel_eq_measure_prod` declarations form one family of two). The
constructions are c1–c62 in `constructions.json`.

A caveat: when a request here predates the PR, it is advisory ("while you are here"). The PR's
remit is proofs.

## Finset.mem_map_equiv (Data/Finset/Image.lean)
- Usage (c1, c2): `simp [ha]` proves `e a ∈ s.map e.toEmbedding` from `a ∈ s`, and the term-mode
  `.2` works. Both implicit binders are inferred.
- Generalisation (c3): there is no hypothesis or typeclass argument to drop. An `EquivLike`
  restatement is not more general in use.
- Automation (c4–c9): simp with the lemma removed leaves `(∃ a ∈ s, e a = b) ↔ e.symm b ∈ s`, so
  `simp 1100` is load-bearing. Bare `grind` proves neither the lemma nor a client goal, while
  `grind [mem_map_equiv]` proves the client goal. The file grind-registers only the four basic
  `mem_*` characterisations; the specialisations `mem_map'`, `mem_map_mk` and `mem_map_equiv` are
  simp-only. Leaving it out of grind therefore follows the file's convention. No request.
- Closure (c10): the image-side twins `Finset.mem_image_equiv` and `Set.mem_image_equiv` exist.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean)
- Usage (c11, c12): the ℤ-cast form `((a : ℚ)⁻¹.den : ℤ) = a` needs one `omega` to reach the
  `natAbs` or `toNat` form a client may want.
- Generalisation (c13–c15): the PR's proof also proves the `a ≠ 0` / `a.natAbs` statement. `0 ≤ a`
  and no hypothesis both fail (grind finds a = 0), so `0 < a` is the weakest hypothesis for RHS `a`.
  The general content is already `inv_intCast_den` and `den_inv_of_ne_zero`.
- Closure (c16): the lemma is a two-step corollary of `inv_intCast_den`
  (`rw [inv_intCast_den, if_neg ha0.ne']; omega`).
- Automation (c17–c21): `simp [ha0]` fails and `simp [ha0.ne']; omega` works. Bare grind fails and
  `grind [den_inv, num_intCast]` works. None of the eight inverse num/den siblings is registered,
  and the binders match the other `_of_pos` members. No request.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean)
- Usage (c22, c23): the lemma rewrites fine with probability measures. It also gives the full
  `MeasurePreserving` statement in one line.
- Generalisation (c24): SigmaFinite is required by `pi_eq`.
- Closure (c27–c29): the statement is exactly `(measurePreserving_piCongrLeft μ e).map_eq` (same
  file, line 720, same hypotheses), and each one derives from the other in one line. The sibling's
  3-line `rw` proof also compiles at line 446. The file therefore proves the same equation twice.
  **Finding 1** (advisory).
- Binders (c25, c26): `[hι' : Fintype ι']` is named, but the name is unused. The anonymous version
  is `rfl`-identical, and this is the only named `Fintype` binder in the directory (vs 13
  anonymous). **Finding 3** (advisory, predates the PR).
- Automation (c30): no `pi_map_*` sibling is registered.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (MeasureTheory/Measure/Portmanteau.lean)
- Usage (c31, c32): the lemma applies directly to `ℕ`-indexed sequences. A hypothesis written with
  the `ℝ≥0` coercion cast to `ℝ` is accepted by defeq.
- Generalisation (c33, c34): `[L.IsCountablyGenerated]` and `[OpensMeasurableSpace Ω]` are both
  needed by the new proof.
- Binders (c35, c36): the lemma re-binds `{L : Filter ι} [L.IsCountablyGenerated]`, which section
  Closed already declares. Without them the type is `rfl`-identical, and it is the only member of
  the section that re-binds them. **Finding 2** (advisory, predates the PR).
- Twin (c37, c38): there is no open-set/liminf `Measure.real` twin. One derives with the PR's
  two-line pattern (`NNReal.toReal_liminf` + `tendsto_of_forall_isOpen_le_liminf`). The open side of
  the file has never had a real-valued member, and the closed real version exists for its single
  consumer (line 679, c39). So the pattern does not demand the twin, and adding it is not this
  golf PR's job. Not filed.
- Automation (c40): nothing in the file is registered.

## limsup_finset_sup' (Order/LiminfLimsup.lean)
- Usage (c41, c42): in a complete linear order the autoparams discharge both bounds, and otherwise
  they are passed positionally.
- Generalisation (c43, c44): weakening `h₁` to the existential the first half uses fails, because
  the other half needs per-index coboundedness. `ConditionallyCompleteLattice` fails because
  linearity is needed.
- Closure and binders (c45, c46): `liminf_finset_inf'` (derived by `βᵒᵈ`), `limsup_finset_sup`,
  `liminf_finset_inf` and `limsup_max`/`liminf_min` are all present, with uniform autoparam binders.
  No request.

## setLIntegral_condKernel_eq_measure_prod (ProbabilityTheory and Measure; Probability/Kernel/Disintegration/Integral.lean)
- Usage (c47–c49): marginal computations (`t = univ`) and bounds work for both members.
- Generalisation (c50, c51): the proof's one step `compProd_apply_prod` consumes both `hs` and `ht`,
  so the hypotheses are exactly those of that lemma.
- Closure (c52–c54): each member is `setLIntegral_condKernel` at `f = 1`. That makes them named
  special cases, as the file's `_univ_left/_univ_right` corollaries are. The Measure member is not a
  simp-level specialisation of the Kernel member (via `Kernel.const`), so keeping the pair mirrors
  the rest of the file.
- Binders (c55): the two members' binders mirror each other and their siblings. No request.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean)
- Usage (c56, c57): the destructuring use (as in CircleTransform.lean) works, and a raw
  `dist x y < ε` hypothesis is accepted.
- Generalisation (c58, c59): the hypothesis is necessary (the conclusion implies it). The iff form
  and a `0 < ε'`-strengthened form are one-liners, so the statement loses nothing.
- Twin (c60, c61): `EMetric.exists_lt_mem_ball_of_mem_ball` does not exist; `declaration_search`'s
  hit was a false positive, and the census finds 2 files. The PR's new proof `exists_between' h`
  proves the EMetric twin verbatim. The twin was absent before the PR too, and the PR does not touch
  EMetric, so it is recorded as a follow-up opportunity, not filed.
- Automation (c62): existential lemmas in this block are unregistered, as expected.

## Environment notes
- `file_search` returns nothing in this workspace, but `file_read` and `content_search` work with
  the `target/Mathlib/...` prefix.
- `Topology/MetricSpace/Pseudo/Defs.lean` has 12 errors in the unedited file in this environment (a
  private `dist_nonneg'` under the module system). I checked only errors introduced by my edits.
