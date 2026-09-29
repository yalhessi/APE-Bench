# Reviewer X4 notes, PR #32875 ("chore: golf using `grind` and `simp`")

Inputs read: brief.md, pr.md, model.md, diff.patch. All tool calls went through `./ptool`. Workspace
files are under the `target/` prefix (for example `target/Mathlib/Data/Finset/Image.lean`).
`lean_verify_edit` takes the bare `Mathlib/...` path.

Procedural note: while working out that prefix, I once ran `cat` on the tool's own `toolbox.log`, a
log of tool-call startup lines in the scratchpad work directory. It is outside my working
directory. It contained no PR or review content, and I read nothing else outside the directory.

Timing method: in `lean_verify_edit` line mode I prefixed each declaration with
`set_option profiler true in set_option profiler.threshold 0 in`, then summed every reported
"took X ms" line. The totals overlap across categories, so they are for relative comparison only.
Each variant ran twice.

## Finset.mem_map_equiv (Data/Finset/Image.lean) -> finding 1
- Bare `grind` fails. `mem_map` is `grind =`, but grind never rewrites `f.toEmbedding w = b` into a
  statement about `f.symm b`.
- `simp [Equiv.apply_eq_iff_eq_symm_apply]` compiles, as does the fully `simp only` version with
  `exists_eq_right`.
- Profile: PR about 42 ms, simp one-liner about 23 ms, original about 17 ms. This confirms the
  PR's own report that this golf is a slowdown. Advisory: use the simp one-liner.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean) -> finding 2
- After `simp only [den_inv, num_intCast]` the goal is `↑(if a = 0 then 1 else a.natAbs) = a`.
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles and takes about 7 ms, against about 40 ms
  for the PR's version and about 10 ms for the original. `simp only; lia` is no faster than
  `grind`: its profile shows grind machinery.
- `abs_of_pos` is not imported in this file.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean) -> finding 3
- `measurePreserving_piCongrLeft` (line 720) proves the same equation in its `map_eq` field, with a
  single rewrite chain through `Equiv.piCongrLeft_preimage_univ_pi`.
- Transplanted here, that chain compiles. Profile: about 21 ms, against about 64 ms for the PR's
  version.
- `congrFun rfl` in the PR's proof is just `fun _ ↦ rfl`. The rewrite chain removes it together
  with the `let`s and the preimage `have`.
- Not requested: making the two lemmas share one proof. It would mean reordering the file, which
  is beyond a golf PR.
- The `hι'` binder name is unused, but it predates this PR; not raised.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (Measure/Portmanteau.lean) -> no finding
- The new proof reduces the lemma to the NNReal version `tendsto_of_forall_isClosed_limsup_le`
  through `measureReal_eq_coe_coeFn` and `NNReal.toReal_limsup` (simp, norm_cast). This is a good
  golf: 268 ms down to under 10 ms.
- The final `exact` relies on `(↑a : ℝ) ≤ ↑b` being defeq to `a ≤ b` in `ℝ≥0`. Adding
  `NNReal.coe_le_coe` to the simp set also compiles. That defeq is `Iff.rfl`-level, so I would not
  ask for it.
- `[L.IsCountablyGenerated]` is still needed by the lemma it calls. The shadowing of the section
  variables `{L} [L.IsCountablyGenerated]` and the missing docstring both predate this PR; not
  raised.

## limsup_finset_sup' (Order/LiminfLimsup.lean) -> finding 6 (advisory, lower confidence)
- The PR's change to the first branch (`simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset]
  at hb ⊢` plus `eventually_lt_of_limsup_lt`) is fine. `gt_iff_lt` is needed because `hb` is
  stated with `>`.
- The untouched second bullet proves `le_sup'` by hand. The replacement compiles.
- Replacing `h₃` with a `let ⟨i, hi⟩ := hs; ...` term also compiles. I mention it only as optional,
  because it rewrites lines the PR does not touch.
- `liminf_finset_inf'` is derived by `OrderDual`, so it needs no parallel change.

## ProbabilityTheory. / MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod (Probability/Kernel/Disintegration/Integral.lean) -> findings 4, 5
- Both are the same pattern, and both reduce to `rw [← (Kernel.)compProd_apply_prod hs ht,
  _.disintegrate]`. Also verified: the file's own `conv_rhs => rw [← _.disintegrate _.condKernel]`
  idiom.
- Profile: kernel version about 31 ms down to about 14 ms; measure version about 37 ms down to
  about 27 ms.
- `simp only [this]` used as a one-shot rewrite is the main style smell. I filed one finding per
  declaration; they are one decision.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean) -> no finding
- `exists_between'` is the `to_dual` of `exists_between` (Order/Basic.lean:1113):
  `a₁ < a₂ → ∃ a, a < a₂ ∧ a₁ < a`. It matches `∃ ε' < ε, x ∈ ball y ε'` through the definitional
  `mem_ball`, which is standard in this file. The docstring is unchanged and still accurate.

## Checked across the whole PR, nothing to request
- No statements, names, attributes or docstrings change, so naming, documentation and correctness
  have nothing to act on.
- Scope fits the batching guideline (7 files, 8 declarations).
- `grind` use: Data/Finset/Image.lean already used `grind` elsewhere. In Data/Rat/Lemmas.lean
  this PR adds the only use (checked with content_search). Finding 2 would remove it.
