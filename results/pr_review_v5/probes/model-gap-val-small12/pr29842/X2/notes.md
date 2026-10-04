# Review notes: PR #29842, feat(TangentCone): generalize some lemmas to TVS

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`.
- Read the whole file `target/Mathlib/Analysis/Calculus/TangentCone.lean` as the PR leaves it, using
  `file_read`.
- Ran `lean_verify_edit` with no edit. The file compiles as the PR leaves it, with no errors and no
  warnings.
- Called `precedent_search` on the new `lim_zero` proof and on the moved `UniqueDiff` block, and
  `zulip_search` on tangent cones in TVS.
- Tested three edits with `lean_verify_edit`. The results are below.

## Object by object

### `tangentConeAt.lim_zero` (proof modified; now under `[ContinuousSMul 𝕜 E]`)
- The new proof goes through `inv_smul_smul₀`, `tendsto_norm_atTop_iff_cobounded` and
  `tendsto_inv₀_cobounded.comp hc |>.smul hd`. It needs only `ContinuousSMul 𝕜 E` and does not ask
  for `ContinuousAdd`, so the assumption is minimal.
- The closest precedent is a suggestion ADedecker made on PR #21065 for this same lemma. It has
  essentially the same shape as the PR's proof.
- I checked a one-line tighter variant: `simpa using ((tendsto_inv₀_cobounded.comp
  (tendsto_norm_atTop_iff_cobounded.1 hc)).smul hd).congr' this`, which drops the `apply` and the
  `rw ... at hc`. It compiles (success). The gain is one line on a proof that is already short, so I
  do not think a maintainer would ask for it. No finding.

### `variable [ContinuousSMul 𝕜 E]` and `variable [ContinuousAdd E]` (tangent-cone TVS section)
- `tangentConeAt_mono_nhds` needs `ContinuousAdd` for `tendsto_const_nhds.add` and `ContinuousSMul`
  through `lim_zero`. `tangentConeAt_congr` and `tangentConeAt_inter_nhds` inherit both, and their
  deprecated aliases move with them. The instances are placed correctly. No finding.

### `tangentConeAt_closure` (moved into the `Normed` section; body unchanged)
- The proof relies on `Metric.mem_closure_iff`, `dist_smul₀` and norms. Proving it in a TVS would
  need at least a countable basis at 0, because the tangent cone is defined with `ℕ`-indexed
  sequences. Keeping it in the normed section is right. No finding.

### `uniqueDiffWithinAt_closure`, the `of_closure`/`closure` alias, `UniqueDiffWithinAt.mono_closure` (moved to the second `Normed` section; unchanged)
- These depend on `tangentConeAt_closure`, so they stay in the normed section. The `𝕜'` variables
  in that section are there for `tangentConeAt_mono_field`/`mono_field` and existed before the PR.
  No finding.

### `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` (UniqueDiff TVS section)
- `mono_nhds`, `uniqueDiffWithinAt_congr`, `_inter`/`.inter`, `_inter'`/`.inter'`,
  `uniqueDiffWithinAt_of_mem_nhds`, `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter` and
  `IsOpen.uniqueDiffOn` all go through `tangentConeAt_mono_nhds`, so they need both instances.
- `UniqueDiffWithinAt.mono` does not need them. This is the **one finding**, advisory: move it
  above the `variable` line and prove it directly as
  `⟨h.1.mono <| Submodule.span_mono <| tangentConeAt_mono st, closure_mono st h.2⟩`.
  `lean_verify_edit` returned success for the whole file, including the later uses of `.mono` in
  `mono_closure`, `uniqueDiffWithinAt_Ici` and `uniqueDiffWithinAt_Iic`.

### Section and `end TVS` / `section Normed` commands (added, moved)
- The section structure is consistent and the file compiles. The variable lines copied into the
  new `Normed` sections are the same as before the PR. No finding.

## Families checked with nothing to report

- **Naming:** nothing is added or renamed. Every name is a pre-existing declaration that was moved.
- **Documentation:** no docstrings were added or changed. The docstring on `lim_zero` is still
  accurate.
- **Duplication:** nothing new is duplicated.
- **Correctness:** the file compiles. The moved lemmas keep their explicit argument order; only
  the order of implicit and instance arguments changes.

## Outside the changed targets (noted only, no finding)

- `tangentConeAt_subset_zero` is not touched by this PR, but it also generalizes to a TVS under
  `[ContinuousAdd E] [ContinuousSMul 𝕜 E] [T2Space E]`. A copy placed at the end of the tangent-cone
  TVS section compiled unchanged (probe, success). This is a natural follow-up. I did not submit it,
  because it would widen a PR that describes itself as "some lemmas".
