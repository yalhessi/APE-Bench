# Review notes: PR #32875 "chore: golf using `grind` and `simp`"

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then checked each declaration through `ptool`:
`declaration_search`, `file_read`, `content_search`, `precedent_search`, `zulip_search`, and
`lean_verify_edit` for every edit proposed. For timing I wrapped a proof in
`set_option profiler true in`. Each timing comes from a single run and the summed profiler lines may
double-count, so the timings only give orders of magnitude.

All seven changed files compile as the PR leaves them, except `Topology/MetricSpace/Pseudo/Defs.lean`.
That file has 12 errors of its own when checked standalone: a private `dist_nonneg'` at line 127, and
errors that follow from it. None is in the changed declaration, so they are not attributed to the PR.

## Object by object

- **`Finset.mem_map_equiv`** (finding). `simp only [mem_map, Equiv.coe_toEmbedding]; grind`.
  `simp [mem_map, Equiv.apply_eq_iff_eq_symm_apply]` closes it in one call (compiled), and
  `grind [mem_map, Equiv.coe_toEmbedding]` alone fails.
  - The PR's own trace says this declaration got slower (<10 → 25 ms).
  - My profile: grind version ~22 ms, single simp ~12 ms, original ~3 ms. The simp-attribute
    application itself measured 14-25 ms.
  - Precedent: on PR #30313 eric-wieser preferred the previous explicit proof over a `grind` golf.
- **`Rat.inv_intCast_den_of_pos`** (finding). `simp only [den_inv, num_intCast]; grind`.
  `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles and takes ~4 ms, against ~28 ms for the
  grind version (7.8 ms of that is kernel checking). `lia` also replaces `grind`; `omega` does not,
  because it cannot split the `if`. The sibling `inv_intCast_num_of_pos` is `simp [*]`.
- **`MeasureTheory.Measure.pi_map_piCongrLeft`** (two findings).
  - Main: `Equiv.piCongrLeft_preimage_univ_pi` and `Equiv.prod_comp` give the whole computation.
    The same file's `measurePreserving_piCongrLeft` (line 720) already proves the same `map_eq` with
    that chain. The 2-line replacement compiled, ~5 ms against ~55 ms.
  - Minor: `congrFun rfl` should be `fun _ ↦ rfl` with `e` explicit, and `simp only [pi_pi, this]`
    should be `rw [this, pi_pi]` (compiled).
  - Not filed: making `pi_map_piCongrLeft` a corollary of `measurePreserving_piCongrLeft`. The
    latter comes ~270 lines later and `pi_map_piCongrLeft` is used in Probability/ProductMeasure.lean;
    moving it is a reorganisation outside a golf PR.
- **`MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'`** (finding).
  - The new proof is a real improvement (268 ms → <10 ms per the PR).
  - But `trace_state` shows `h` ends as an `ℝ` inequality between coercions, and `exact` feeds it
    where an `ℝ≥0` `≤` is expected, so it relies on `rfl`. `NNReal.toReal_limsup` is a cast lemma
    named by hand.
  - `simp only [measureReal_eq_coe_coeFn] at h; exact ... fun F hF ↦ mod_cast h F hF` compiled.
  - Not filed: the redundant `{L : Filter ι} [L.IsCountablyGenerated]` binders shadowing the section
    variables (line 606). The PR does not touch them.
- **`limsup_finset_sup'`** (finding). The new `simp only ... at hb ⊢` plus `eventually_all_finset`
  is a good use of the filter API: it replaces the manual `eventually_iff_exists_mem` /
  `⋂ i ∈ s` construction. Only `gt_iff_lt` is unneeded (compiled without it). The unchanged first
  bullet (`h₃`) was left alone as out of scope.
- **`MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod`** and
  **`ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod`** (one finding each). The `have` +
  `simp only [this]` + `exact (compProd_apply_prod ..).symm` collapses to
  `rw [← compProd_apply_prod hs ht, ρ.disintegrate]` (and the `Kernel.` / `κ` analogue). Both
  compiled, as did the sibling `conv_rhs => rw [← _.disintegrate _]` form.
- **`Metric.exists_lt_mem_ball_of_mem_ball`** (finding, advisory). `exists_between' h` is a nice use
  of the `to_dual` lemma, but it crosses the `Metric.ball` definition by `rfl` on both the hypothesis
  and the goal. Keeping `simp only [mem_ball] at h ⊢` with `exact exists_between' h` introduces no
  errors. The term sits on its own line, as required: statement plus proof would pass 100 columns.
- **PR title and description** (two findings).
  - Title: only 2 of 8 golfs use `grind`; most use existing lemmas.
  - Description: the batching-guidelines paragraph is boilerplate about the author's process, and
    the PR (7 files) does not meet its own ~5-file guideline.

## Conventions: where filed, where left

1. *Finishing tactic instead of hand-written term*: no place; no goal here is closed by a manual
   rewrite chain that a single finisher would close.
2. *Derive from existing library API*: filed at `pi_map_piCongrLeft`
   (`Equiv.piCongrLeft_preimage_univ_pi`, `Equiv.prod_comp`) and at both
   `setLIntegral_condKernel_eq_measure_prod` (`compProd_apply_prod` with `disintegrate`).
3. *Terminal simp / simp feeding a flexible finisher not squeezed*: filed at `mem_map_equiv` and
   `inv_intCast_den_of_pos` (squeezed `simp only` feeding `grind`), folded into the single-`simp`
   requests. Left the other `simp only`s because each feeds an `exact` that depends on its exact
   output:
   - `limsup_finset_sup'`: `simp only [...] at hb ⊢` then `exact fun i i_s ↦ ...`;
   - Portmanteau: `simp only [...] at h` then `exact ... h`;
   - `pi_map_piCongrLeft`: `simp only [pi_pi, this]` then `exact`.
4. *Merge consecutive calls*: filed at `mem_map_equiv` and `inv_intCast_den_of_pos` (two calls → one
   `simp`), and at both disintegration lemmas (`have`/`simp only`/`exact` → one `rw`).
5. *Automation only when not markedly slower*: filed at `mem_map_equiv` (PR trace <10 → 25 ms) and
   `inv_intCast_den_of_pos` (<10 → 17 ms; my profile ~28 ms against ~4 ms for `simp`).
6. *Short tactic block as a term*: left everywhere. Every changed `by` block that remains has two or
   more steps that are not a single application; the one single-application proof,
   `exists_lt_mem_ball_of_mem_ball`, is already the term `exists_between' h`.
7. *Direct lemma, not a converted one*: filed at `pi_map_piCongrLeft` (`congrFun rfl` →
   `fun _ ↦ rfl`).
8. *Rewrite, not `rfl` across a definitional equality*: filed at
   `tendsto_of_forall_isClosed_limsup_real_le'` (the coerced `ℝ` inequality passed as an `ℝ≥0` one)
   and at `exists_lt_mem_ball_of_mem_ball` (membership in `ball` unfolded by `rfl`).
9. *Inferable arguments not passed*: left. The new code passes only needed arguments: `hs ht` to
   `compProd_apply_prod`, and `(hb i i_s) (h₂ i i_s)` to `eventually_lt_of_limsup_lt`. In
   `pi_map_piCongrLeft` the explicit arguments are already `_`.
10. *Remove unneeded steps or lemmas*: filed at `limsup_finset_sup'` (`gt_iff_lt`, checked
    unneeded). The unneeded `e_meas`/`s'`/`have` in `pi_map_piCongrLeft` are covered by its main
    finding.
11. *Simp consumed by another tactic is squeezed*: left. Every non-terminal simp in the diff is
    already `simp only [...]`: `at hb ⊢` in LiminfLimsup, `at h` in Portmanteau, `[pi_pi, this]` in
    Pi.
12. *Cut the PR at natural seams*: left. The eight golfs are independent and small (61 lines), well
    under the size where splitting helps. Dropping the two slower `grind` hunks is requested per
    declaration instead.
13. *Cleanup leaves out hunks that cost readability*: covered by the `mem_map_equiv` and
    `inv_intCast_den_of_pos` findings, which offer dropping the hunk.
14. *Marginal changes not made*: left at PR level. The trace shows real speedups (268 → <10 ms,
    81 → <10 ms, 69 → 17 ms), so the PR is not of marginal benefit.
15. *Benchmark accompanies a method-replacing PR*: left. The description already reports per-lemma
    trace profiling.
16. *Title and description precise*: filed (title).
17. *Filter API instead of unpacking `∀ᶠ` by hand*: left. The new `limsup_finset_sup'` uses
    `eventually_all_finset` and `eventually_lt_of_limsup_lt`, which removed the old manual
    `eventually_iff_exists_mem` / `⋂ i ∈ s` unpacking.
18. *No dense one-liners*: left. No new line packs an intricate argument: the longest is
    `exact fun i i_s ↦ eventually_lt_of_limsup_lt (hb i i_s) (h₂ i i_s)`.
19. *Lighter tactic than `grind`/`aesop`*: filed at `mem_map_equiv` (`simp` closes it) and
    `inv_intCast_den_of_pos` (`simp` closes it; `lia` also replaces `grind`).
20. *Concise description, no boilerplate*: filed (batching-guidelines paragraph).
21. *Title follows `type(Area): description`*: left. The title "chore: golf using `grind` and `simp`"
    has the type prefix, and the scope is optional for a PR spanning five areas.
22. *Proof term on the statement line only if both fit*: left. `exists_lt_mem_ball_of_mem_ball ... :=`
    is followed by `exists_between' h` on its own line, and together they would exceed 100 columns.
23. *Cast tactics instead of hand-listed cast lemmas*: filed at
    `tendsto_of_forall_isClosed_limsup_real_le'` (`NNReal.toReal_limsup` → `mod_cast`, compiled).
24. *Change only what the purpose needs*: left. Every hunk is a proof golf of the kind the title
    announces; no statement or name changes.
25. *`simpa using` the lemma instead of backward simp rewriting*: left. No changed proof rewrites a
    goal backwards with `←` simp lemmas; the disintegration `rw [← compProd_apply_prod ...]` proposed
    rewrites with an equation, not simp lemmas.
