# Review notes: PR #29842, feat(TangentCone): generalize some lemmas to TVS

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`.
- The reviewed file lives at `target/Mathlib/Analysis/Calculus/TangentCone.lean` in the tool
  workspace. I read all of it with `file_read`.
- Ran `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors or
  warnings.
- Ran `zulip_search` for tangent cone / TVS / UniqueDiffWithinAt. Nothing relevant came back.
- Ran `precedent_search` on the new `lim_zero` proof. The nearest hit is ADedecker's suggestion on
  PR #21065 for this same lemma: `filter_upwards [hc.eventually_ne_cobounded 0] ...`. Ran it again
  on the UniqueDiff TVS block; nothing relevant.
- Ran `content_search` for `@`-applications of the moved lemmas in `target/Mathlib`. There are
  none, so the changed instance arguments break no caller.

## What the PR does

- It moves `tangentConeAt.lim_zero` into the TVS section under `[ContinuousSMul 𝕜 E]`, with a new
  proof via `tendsto_inv₀_cobounded`.
- It moves `tangentConeAt_mono_nhds`, `tangentConeAt_congr` and `tangentConeAt_inter_nhds` into TVS
  under `[ContinuousAdd E]` as well.
- In the UniqueDiff part, it moves `mono_nhds`, `mono`, `uniqueDiffWithinAt_congr`,
  `inter`/`inter'`, `of_mem_nhds`, `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter` and
  `IsOpen.uniqueDiffOn` into TVS under `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`.
- `tangentConeAt_closure`, `uniqueDiffWithinAt_closure`, the `of_closure`/`closure` alias and
  `mono_closure` only move down, into the Normed sections that now start later. Their text is
  unchanged.

## Object by object

- **Section / variable commands** (the `end TVS` / `section Normed` blocks, `variable
  [ContinuousSMul 𝕜 E]`, `variable [ContinuousAdd E]`, `variable [ContinuousAdd E] [ContinuousSMul
  𝕜 E]`, and the re-created Normed variable blocks):
  - Each moved lemma really needs the instances it gets. `lim_zero` needs `ContinuousSMul` for
    `Tendsto.smul`. `mono_nhds` needs `ContinuousAdd` for `tendsto_const_nhds.add`. The congr,
    inter, of_mem_nhds and IsOpen lemmas all go through `mono_nhds`.
  - `ContinuousAdd` is weaker than `IsTopologicalAddGroup`, so it is the right minimal choice.
  - The re-created Normed variable blocks match the old ones exactly.
  - The one exception is `UniqueDiffWithinAt.mono`, which is finding 1.
- **`tangentConeAt.lim_zero`** (proof modified):
  - The statement is unchanged and the new proof is correct: it compiles.
  - I verified a shorter three-line version that rewrites `hc` to `cobounded` first and uses
    `filter_upwards [hc.eventually_ne_cobounded 0]`. The precedent above suggests this shape. This
    is finding 2 (advisory golf).
  - The name was not introduced here and I raise no naming issue.
- **`tangentConeAt_mono_nhds`, `tangentConeAt_congr`, `tangentConeAt_inter_nhds`** (moved, text
  unchanged): they need both continuity instances. Nothing to request.
- **`tangentConeAt_closure`** (removed and re-added below):
  - The text is identical; only its position changed.
  - Generalizing it to TVS would need a countable neighbourhood basis, because the proof builds a
    sequence using `Metric.mem_closure_iff`. Keeping it in Normed is right for this PR.
  - `@[simp]` is preserved.
- **`uniqueDiffWithinAt_closure`, the `UniqueDiffWithinAt.of_closure`/`.closure` alias,
  `UniqueDiffWithinAt.mono_closure`** (removed and re-added below):
  - Identical text. They depend on `tangentConeAt_closure`, so Normed is right.
  - The Normed variable block with `𝕜'` is preserved for the later `mono_field` lemmas.
- **UniqueDiff TVS block**:
  - `UniqueDiffWithinAt.mono` now takes `[ContinuousAdd E] [ContinuousSMul 𝕜 E]`, but it does
    not need them.
  - I verified a direct proof placed before the variable line:
    `⟨h.1.mono <| Submodule.span_mono <| tangentConeAt_mono st, closure_mono st h.2⟩`.
    This is finding 1.
  - The other lemmas in the block need the instances.
- **Remaining Normed lemmas the PR did not generalize**:
  - `mem_tangentConeAt_of_openSegment_subset` and `mem_tangentConeAt_of_segment_subset` compile
    unchanged over `[AddCommGroup G] [Module ℝ G] [TopologicalSpace G]` (verified). This is
    finding 3, advisory, since it widens the PR's scope.
  - `tangentConeAt_subset_zero` also compiles in the TVS section with `[T2Space E]`. I did not
    file it: it adds a new separation assumption, and `UniqueDiffWithinAt.accPt` would need the
    same, so it is follow-up work rather than a request on this PR.
  - `zero_mem_tangentCone`, the prod/pi lemmas, `tangentConeAt_nonempty_of_properSpace` and
    `tangentConeAt_eq_univ` depend on metric or norm structure. I did not pursue them.
- **Documentation**:
  - The module docstring and the `lim_zero` docstring are still accurate.
  - The moved lemmas carry the same docstrings as before. Nothing to request.
- **Naming**: the PR adds and renames no names, so there was nothing to check with `naming_norm`.
- **Correctness**: the file compiles, and there are no explicit `@` callers whose argument
  positions shift.

## Result

3 findings, all advisory, each checked with `lean_verify_edit` (success).
