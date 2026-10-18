# Review notes: PR #29842, "feat(TangentCone): generalize some lemmas to TVS"

## What I did
- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Read the whole PR file through `ptool file_read`
  (`target/Mathlib/Analysis/Calculus/TangentCone.lean`).
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors or warnings.
- `zulip_search` turned up nothing on this generalization. `precedent_search` on `lim_zero` found
  ADedecker's suggestion on PR #21065, which has nearly the same shape as this PR's new proof. The
  precedent search on the UniqueDiff TVS block found nothing relevant.

## Object by object
- **Section restructuring (TangentCone part).** The PR moves `end TVS` / `section Normed` below
  `tangentConeAt_inter_nhds`. It adds `variable [ContinuousSMul 𝕜 E]` before `lim_zero` and
  `variable [ContinuousAdd E]` before `mono_nhds`. Each lemma gets only what it uses: `lim_zero` needs
  only `.smul`, and `mono_nhds` adds `.add`. No finding.
- **`tangentConeAt.lim_zero`.** Its new proof (cobounded form, `inv_smul_smul₀`, `Tendsto.smul`) is correct
  and short, and it matches what a maintainer suggested on an earlier PR. A `filter_upwards` plus
  `simpa only [← tendsto_congr' this]` variant would save about one line, which is not worth asking for.
  The name and docstring are not changed by this PR. No finding.
- **`tangentConeAt_mono_nhds`, `tangentConeAt_congr`, `tangentConeAt_inter_nhds`.** Moved to TVS with
  `ContinuousSMul` and `ContinuousAdd`. Both are used, through `lim_zero` and `.add`. `ContinuousAdd` is
  the weaker choice beside `IsTopologicalAddGroup`, so it is fine. No finding.
- **`tangentConeAt_closure`.** Moved unchanged into `Normed`. Its proof picks approximants along a
  sequence of shrinking radii. In a TVS that needs a countable neighbourhood basis
  (first-countability), so leaving it in `Normed` is reasonable for this PR. No finding.
- **UniqueDiff TVS block.** `mono_nhds`, `mono`, `congr`, `inter`, `inter'`, `of_mem_nhds`,
  `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter` and `IsOpen.uniqueDiffOn` move under
  `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]`. All except `UniqueDiffWithinAt.mono` genuinely need
  `mono_nhds`. **Finding 1:** `mono` follows from `tangentConeAt_mono` and `closure_mono`, so it can sit
  above the variable line with no continuity assumptions. Verified to compile.
- **`uniqueDiffWithinAt_closure`, `UniqueDiffWithinAt.of_closure`/`.closure`, `UniqueDiffWithinAt.mono_closure`.**
  These moved into `Normed` because they depend on `tangentConeAt_closure`. Their statements are
  unchanged. No finding.
- **Lemmas left in `Normed` that would generalize.** `tangentConeAt_subset_zero` and
  `UniqueDiffWithinAt.accPt` use only `lim_zero`, `.add` and `tendsto_nhds_unique`. **Finding 2:** move
  them to TVS with `[T2Space E]`. Verified to compile.
  - I also checked `tangentConeAt_mono_field`, `UniqueDiffWithinAt.mono_field` and
    `UniqueDiffOn.mono_field`. They move into the TVS section, in a `section Field` with
    `[Module 𝕜' E] [IsScalarTower 𝕜 𝕜' E]` placed before the continuity variables, and compile. I am not
    filing this: those lemmas are far from the diff and not tied to what the PR generalizes.
  - `zero_mem_tangentCone`, `tangentConeAt_nonempty_of_properSpace`, `tangentConeAt_eq_univ`, the
    product and pi lemmas, and the convex lemmas use metric or norm arguments. They are rightly left in
    `Normed`.
- **Instance order.** The TangentCone section adds `ContinuousSMul` then `ContinuousAdd`; the UniqueDiff
  section has `ContinuousAdd` then `ContinuousSMul`. This is harmless and not worth a request.
- **Naming, documentation, correctness.** No declaration is renamed or newly added; only moved, plus one
  proof rewrite. Deprecated aliases are untouched, and the new instance arguments are inferable for
  every normed space, so no call site breaks. Nothing to request.
