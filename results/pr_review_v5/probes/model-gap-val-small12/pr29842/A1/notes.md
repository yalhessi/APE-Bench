# Notes: PR #29842, feat(TangentCone): generalize some lemmas to TVS

Inputs read: brief.md, pr.md, model.md, diff.patch. With `file_read`, I read the whole of
`target/Mathlib/Analysis/Calculus/TangentCone.lean` as the PR leaves it (1-685). Other tools
used: `content_search`, `precedent_search`, `zulip_search` and `lean_verify_edit` (3 compiles).

## What the PR does
- In the TangentCone section, the `end TVS` / `section Normed` boundary moves down. As a result,
  `tangentConeAt.lim_zero` (under `[ContinuousSMul 𝕜 E]`) and then `tangentConeAt_mono_nhds`,
  `tangentConeAt_congr` and `tangentConeAt_inter_nhds` (under `[ContinuousAdd E]` as well) become
  TVS lemmas. `tangentConeAt_closure` stays normed and moves below the boundary unchanged.
- In the UniqueDiff section, `mono_nhds`, `mono`, `congr`, `inter`, `inter'`, `of_mem_nhds`,
  `IsOpen.*` and `UniqueDiffOn.inter` become TVS lemmas under
  `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`. `uniqueDiffWithinAt_closure`, the
  `of_closure`/`closure` aliases and `mono_closure` stay normed and move below the boundary unchanged.
- The proof of `tangentConeAt.lim_zero` is rewritten without norms:
  `inv_smul_smul₀` + `tendsto_inv₀_cobounded.smul`.

## Object by object
- `tangentConeAt.lim_zero` (proof modified): it genuinely needs `ContinuousSMul 𝕜 E` (joint
  continuity, since both `c n` and `d n` vary) and needs nothing else.
  - `#check` confirms the signature carries only `[ContinuousSMul 𝕜 E]`.
  - Proof: 4 readable lines. A merge of `rw … at hc` into the `simpa` term compiled (tested one
    variant), but every variant either runs past 100 columns or reads no better.
  - `precedent_search` shows a maintainer (ADedecker, PR #21065) suggesting this same shape,
    `rw [tendsto_norm_atTop_iff_cobounded] at hc` then `simpa`, for this lemma. So no golf is
    requested.
  - The `fun n =>` in the statement is untouched context, not changed by the PR, so I did not ask
    for `↦` there.
  - No existing library lemma does this step: `content_search` for cobounded/smul patterns found none.
- `tangentConeAt_mono_nhds` / `congr` / `inter_nhds` (moved into TVS): they need `lim_zero` plus
  continuity of `x + ·`. The assumptions are minimal in the usual Mathlib spelling, so there is
  nothing to request.
- `tangentConeAt_closure` (moved, unchanged, keeps `@[simp]`): the proof uses the metric
  (`Metric.mem_closure_iff`, `dist_smul₀`), and a TVS version would need at least first
  countability. Leaving it normed is reasonable, so there is nothing to request.
- `uniqueDiffWithinAt_closure`, `UniqueDiffWithinAt.of_closure`/`.closure` (alias),
  `UniqueDiffWithinAt.mono_closure` (moved, unchanged): they depend on `tangentConeAt_closure`, so
  they rightly stay normed. Attributes (`@[simp]`, `protected alias`) are preserved. Nothing to
  request.
- `UniqueDiffWithinAt.mono` is **finding 1**. It is placed after the `variable` line, so it
  inherits `[ContinuousAdd E] [ContinuousSMul 𝕜 E]` (confirmed by `#check`), although
  `tangentConeAt_mono` + `closure_mono` prove it with no continuity. I verified that moving it
  above the `variable` line with a direct term proof compiles and leaves the rest of the file
  compiling.
- `UniqueDiffWithinAt.mono_nhds`, `uniqueDiffWithinAt_congr`, `inter`/`inter'`, `of_mem_nhds`,
  `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter`, `IsOpen.uniqueDiffOn`: they need
  `tangentConeAt_mono_nhds`, so the assumptions are needed. Nothing to request.
- `section`/`variable` commands: the `variable [ContinuousSMul 𝕜 E]` → `variable [ContinuousAdd E]`
  layering is the standard incremental pattern, with no `omit`. The relocated `section Normed`
  blocks have no blank line after `section Normed`. This is **finding 2**, advisory: it is
  carried-over file style, raised only because the conventions list names it.
- Module docstring: still accurate (it describes `tangentConeAt`/`UniqueDiffWithinAt`
  generically). Nothing to request.
- PR title: `feat(TangentCone): …` fits `type(Area): description`. The description was not
  recoverable, so I cannot judge it.

## Considered and not raised
- Generalizing further lemmas that are not changed here: `tangentConeAt_subset_zero` and
  `UniqueDiffWithinAt.accPt` look generalizable to TVS with `[T2Space E]`, since they use only
  `lim_zero`, `ContinuousAdd` and limit uniqueness. The PR scopes itself to "some lemmas", so I
  left this out as outside the PR's scope. Not compile-tested.
- `IsTopologicalAddGroup` vs `ContinuousAdd`: with `ContinuousSMul 𝕜 E` they are equivalent, and
  `ContinuousAdd` is the weaker-looking hypothesis, so I did not raise it.
- `zulip_search` turned up no prior discussion relevant to this change.
