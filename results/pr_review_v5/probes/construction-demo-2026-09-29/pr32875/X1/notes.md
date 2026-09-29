# Review notes: PR #32875 "chore: golf using `grind` and `simp`"

I read `pr.md`, `model.md` and `diff.patch`, then used `ptool` for three kinds of check:
- reading each changed file in its reviewed state (`file_read` under `target/`);
- looking up the lemmas each new proof relies on (`declaration_search`, `content_search`);
- compiling every file as the PR leaves it, and every alternative I considered (`lean_verify_edit`).

I also ran `precedent_search` and `zulip_search`. Neither turned up a precedent that changed a finding. The Zulip hits did confirm that maintainers track `simp only [...]; grind` brittleness and golf timing.

The PR changes proofs only: no statements change, and nothing is added, removed or renamed. Naming, generalization and documentation asks therefore apply only to pre-existing code, and I raised none.

## Finset.mem_map_equiv (Data/Finset/Image.lean) -> finding 1
- The file as the PR leaves it compiles.
- The PR's own profile shows this proof got slower (<10 ms before, 25 ms after).
- Plain `grind` fails, as do `grind [Equiv.coe_toEmbedding]` and `grind [Equiv.apply_eq_iff_eq_symm_apply]`. The `simp only` preprocessing is therefore essential.
- `simp [Equiv.apply_eq_iff_eq_symm_apply]` compiles as a one-liner without grind, and so does a fully squeezed `simp only`. I asked for that, or for a revert.
- `grind` is already used widely in this file, so its use as such is not a problem.

## Rat.inv_intCast_den_of_pos (Data/Rat/Lemmas.lean) -> finding 2
- The file compiles.
- The profile shows it got slower (<10 ms before, 17 ms after).
- `simp [ha0.ne', Int.natAbs_of_nonneg ha0.le]` compiles and matches the sibling `inv_intCast_num_of_pos := by simp [*]`.
- `grind [den_inv, num_intCast]` also compiles, if grind is preferred.
- `abs_of_pos` is not available in this file, and `simp [ha0.ne', ha0.le]` leaves `↑a.natAbs = a`.

## MeasureTheory.Measure.pi_map_piCongrLeft (MeasureTheory/Constructions/Pi.lean) -> finding 3
- The file compiles, and the golf is sound.
- `congrFun rfl` with the equivalence left as `_` is an obscure spelling.
- `rw [this, pi_pi]; exact Fintype.prod_equiv e _ _ fun _ ↦ rfl` compiles. I asked for it.
- The `let s'` and the `have` block are unchanged by the PR and still needed.

## MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le' (MeasureTheory/Measure/Portmanteau.lean): no finding
- The file compiles.
- The new proof goes through the NNReal version using two `@[simp]` lemmas: `measureReal_eq_coe_coeFn`, and `NNReal.toReal_limsup`, which is also `norm_cast`. The final `exact` uses the defeq between the coerced `≤` and the NNReal `≤`, which is standard.
- `tendsto_of_forall_isClosed_limsup_le (by simpa using h)` also compiles. The PR's two lines are fine, so I did not ask for it.
- Pre-existing and not touched by the PR:
  - The lemma rebinds `{L : Filter ι} [L.IsCountablyGenerated]`, which the section `variable` already supplies. Removing the binders compiles.
  - It has no docstring.
  I left both out as out of scope for a proof-only golf PR.

## limsup_finset_sup' (Order/LiminfLimsup.lean): no finding
- The file compiles.
- The new branch rewrites to `∀ i ∈ s, ∀ᶠ ...` via `eventually_all_finset` and closes it with `eventually_lt_of_limsup_lt`. This is a clean improvement over the manual `⋂` construction.
- Dropping `gt_iff_lt` from the `simp only` also compiles. The linter did not flag it as unused, so I did not ask.
- The unchanged `h₃` block could be a term, `hs.imp fun i hi ↦ ⟨hi, h₁ i hi⟩`, which I verified. It is outside the diff, so I did not ask.

## ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod and MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod (Probability/Kernel/Disintegration/Integral.lean) -> findings 4 and 5
- The file compiles. The change is correct: `compProd_apply_prod` replaces the manual indicator computation.
- The kept `have ... := by congr; exact (_.disintegrate _).symm` plus `simp only [this]` is unnecessary.
- The sibling lemmas in the file use `conv_rhs => rw [← κ.disintegrate κ.condKernel]`. That pattern, followed by `rw [compProd_apply_prod hs ht]`, compiles for both lemmas, and so does the one-liner `rw [← compProd_apply_prod hs ht, _.disintegrate]`.
- These two are one decision (the same edit in the kernel and measure versions), filed as one finding per declaration.

## Metric.exists_lt_mem_ball_of_mem_ball (Topology/MetricSpace/Pseudo/Defs.lean): no finding
- `exists_between'` is the `to_dual` of `exists_between` (Order/Basic.lean:1113). Applied to `h : dist x y < ε`, it gives `∃ a < ε, dist x y < a`, which is the goal up to `mem_ball`, itself `Iff.rfl`.
- The neighbouring `pos_of_mem_ball` uses the same defeq, so this is consistent with the file.
- The as-is compile of this file reports 12 pre-existing errors, all far from the change. They are at lines 127, 163-168, 1061-1125: a private `dist_nonneg'` used in a structure default field, and the knock-on errors. None is at line 377 or caused by this PR; they look like the file not being checkable on its own in this workspace.

## Checked and not raised
- Scope: the batch (7 files, 8 declarations) is within the author's stated limits, so I did not ask to split it.
- Naming and documentation: nothing changed.
- Correctness: every changed declaration compiles, with no new warnings.
