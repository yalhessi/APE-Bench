# Review notes: PR #32875, "chore: golf using `grind` and `simp`"

## Method
- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`. All eight changed declarations are proof-only
  changes: no statement, name, attribute or docstring changed.
- `file_read` and `content_search` cannot reach the Mathlib tree from this workspace; they return
  "File not found". I read statements with `#check` inside `lean_verify_edit` splices instead, and
  checked every proposed edit with `lean_verify_edit`. For speed comparisons I used
  `set_option profiler true` with `profiler.threshold 1`, in line mode.
- Other tools used: `declaration_search`, `precedent_search` (nothing applicable) and
  `zulip_search`. Zulip turned up only general grind-regression threads; nothing applied
  directly.

## Object by object

### `Finset.mem_map_equiv` (Data/Finset/Image.lean)
- The file compiles as the PR leaves it.
- The PR's own table shows a slowdown (<10 ms before, 25 ms after). Profiling confirms it: the
  grind version takes about 12 ms of tactic time, against about 4 ms for the original and about
  5 ms for a single `simp only [mem_map, Equiv.coe_toEmbedding, Equiv.apply_eq_iff_eq_symm_apply,
  exists_eq_right]`. `simp [Equiv.apply_eq_iff_eq_symm_apply]` also works.
- Filed an advisory proof-golf finding.
- Side check: dropping `@[simp 1100]` breaks a later proof in the file (a `map e'.toEmbedding (map e.toEmbedding s)`
  lemma), which confirms the attribute is load-bearing. The PR keeps it.

### `Rat.inv_intCast_den_of_pos` (Data/Rat/Lemmas.lean)
- The PR proof is `simp only [den_inv, num_intCast]; grind`. It profiles at about 25-50 ms,
  including 7-10 ms of kernel type checking of the grind term.
- `rw [den_inv, num_intCast, if_neg ha0.ne', Int.natAbs_of_nonneg ha0.le]` is one line and takes
  about 2 ms (profiled twice). Filed an advisory finding.
- Noted, not filed: `Rat.inv_intCast_den` (`(↑a)⁻¹.den = if a = 0 then 1 else a.natAbs`) sits later
  in the same file and subsumes this lemma. Reordering is outside a golf PR.

### `MeasureTheory.Measure.pi_map_piCongrLeft` (MeasureTheory/Constructions/Pi.lean)
- The new tail `simp only [pi_pi, this]; exact Fintype.prod_equiv _ _ _ (congrFun rfl)` compiles.
- `congrFun rfl` stands in for `fun _ ↦ rfl`, and `e.prod_comp fun i ↦ μ i (s i)` states the
  reindexing directly. Both variants verified. Filed an advisory style finding.
- The untouched `have` block re-proves `Equiv.piCongrLeft_preimage_univ_pi`, which exists in
  Data/Set/Prod.lean. A three-line proof using it plus `MeasurableEquiv.coe_piCongrLeft` verified,
  and profiled faster. Filed an advisory duplication finding. If it is applied, it subsumes the
  style finding.

### `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'` (MeasureTheory/Measure/Portmanteau.lean)
- The new two-line proof is correct and much faster than the old one.
- The final `exact` only closes by defeq, because `h` is left as `↑x ≤ ↑y` in ℝ while the lemma
  wants `x ≤ y` in ℝ≥0. Adding `NNReal.coe_le_coe` to the `simp only` verified, and the linter
  confirmed the lemma is used. Filed an advisory finding.
- No issue with calling the unprimed ℝ≥0 lemma instead of the primed ENNReal one.

### `limsup_finset_sup'` (Order/LiminfLimsup.lean)
- The changed part, `simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢` followed by
  `exact fun i i_s ↦ eventually_lt_of_limsup_lt (hb i i_s) (h₂ i i_s)`, is clean and replaces a
  manual `⋂`-set argument.
- Nothing to request on the changed lines.
- Not filed, because those lines are unchanged: the `h₃` construction and the second bullet
  (`simp only [le_sup'_iff]; use i, i_s`) could be golfed further, but asking for that goes
  beyond a golf PR's diff.

### `MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod` and `ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod` (Probability/Kernel/Disintegration/Integral.lean)
- Both new proofs keep a `have` (via `congr; exact (….disintegrate _).symm`), then `simp only [this]`
  and `exact (compProd_apply_prod hs ht).symm`.
- Each collapses to one `rw [← (Kernel.)compProd_apply_prod hs ht, ….disintegrate]`, verified for
  both. Filed one advisory finding per declaration and asked that the two stay parallel.

### `Metric.exists_lt_mem_ball_of_mem_ball` (Topology/MetricSpace/Pseudo/Defs.lean)
- `exists_between' : a₂ < a₁ → ∃ a < a₁, a₂ < a` applied to `h` works through the standard
  `mem_ball` defeq (`Metric.ball x ε = {y | dist y x < ε}`), which Mathlib routinely relies on.
- The docstring still matches the statement. No finding.

## Checked across all families with nothing to file
- Naming: no declarations were added or renamed.
- Documentation: no docstring changed, and the existing ones still match.
- Generalization: no statement changed.
- Scope: this is a pure proof-golf batch of 7 files and 8 declarations, within the stated
  batching guidelines.
- Correctness:
  - Image.lean and LiminfLimsup.lean compile as the PR leaves them (as-is check).
  - Rat/Lemmas, Pi, Portmanteau and Disintegration/Integral compile, as shown by successful
    whole-file verified edits.
  - Topology/MetricSpace/Pseudo/Defs.lean fails the as-is check. The errors are all at untouched
    lines (127, 168, 1061-1125): a private `dist_nonneg'` is referenced from a public
    `edist := …` default, and errors cascade from there. This looks like a standalone-check or
    module-visibility artifact of the base file, not something this PR introduced.
  - No error is reported at `exists_lt_mem_ball_of_mem_ball`, so the PR's term
    `exists_between' h` elaborates. No finding filed.
