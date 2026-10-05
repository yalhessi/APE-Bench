# Notes: PR #29842, feat(TangentCone): generalize some lemmas to TVS

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. I read the whole of
`target/Mathlib/Analysis/Calculus/TangentCone.lean` as the PR leaves it, with
`file_read` and `omit_details=false`. I checked edits with `lean_verify_edit`; every check
compiled the whole file with no pre-existing errors. I also ran `precedent_search` on the
new `lim_zero` proof and on the TVS `variable` block, `declaration_search` and
`content_search` for the lemmas involved, and one `zulip_search`, which returned nothing
relevant.

## Object by object

- **`variable [ContinuousSMul 𝕜 E]` / `variable [ContinuousAdd E]` in the TangentCone TVS section.**
  `lim_zero` needs only `ContinuousSMul`, through `Tendsto.smul`. `tangentConeAt_mono_nhds`
  and its consequences also need continuity of translation, through
  `tendsto_const_nhds.add`. Asking for something weaker than `ContinuousAdd` (for example
  `ContinuousConstVAdd`) would be unidiomatic, so I made no request.
  - Spelling: `[ContinuousAdd E] [ContinuousSMul 𝕜 E]` is the weaker form and standard for
    modules over a field, where negation is `(-1) • ·`. I see no reason to ask for
    `IsTopologicalAddGroup`.
- **`tangentConeAt.lim_zero` (proof rewritten, statement moved to TVS).** The new proof is
  correct and shorter than the normed one. It can be shortened further: finding 2, checked
  in two variants. Both compiled.
  - Not a departure:
    - `fun n hn ↦` is the preferred arrow in new code.
    - `Tendsto.congr'` has an unprimed sibling, `Tendsto.congr`.
    - `tendsto_inv₀_cobounded` adds no imports, and the statement now lives in a TVS
      setting, where the old norm argument would not apply.
    - The proof is not over-compressed.
- **`tangentConeAt_mono_nhds`, `tangentConeAt_congr`, `tangentConeAt_inter_nhds`** (moved
  into TVS, unchanged otherwise). These are fine, and the deprecated aliases moved with
  them.
- **`tangentConeAt_closure` (moved into the Normed section, unchanged).** The sibling item
  asked whether it should be generalized too. It cannot be done for free. The
  sequence-based definition needs a countable neighbourhood basis to approximate points of
  the closure: the proof uses `Metric.mem_closure_iff` and `exists_seq_strictAnti_tendsto`.
  So it needs at least first countability. Keeping it in Normed is reasonable for this PR;
  no request.
- **`uniqueDiffWithinAt_closure`, `UniqueDiffWithinAt.of_closure/closure` aliases,
  `UniqueDiffWithinAt.mono_closure` (moved into the UniqueDiff Normed section).** These
  depend on `tangentConeAt_closure`, so they stay normed. The move is consistent; no
  request.
- **`variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` in the UniqueDiff TVS section, and
  `UniqueDiffWithinAt.mono_nhds` through `IsOpen.uniqueDiffOn`.**
  - `mono_nhds`, `congr`, `inter`, `inter'`, `of_mem_nhds`, `IsOpen.*` and
    `UniqueDiffOn.inter` really need both classes, through `tangentConeAt_mono_nhds`.
  - `UniqueDiffWithinAt.mono` (s ⊆ t) needs neither. Moved above the variable line and
    proved directly from `tangentConeAt_mono` and `closure_mono`, the whole file compiles,
    and an `example` with no topological-algebra classes uses it. This is finding 1.
- **Moved `section Normed` / `variable` blocks (blank-line item).** These lines are moved
  verbatim. The file stacks consecutive `variable` lines right after `section` throughout
  (for example `section TVS` at lines 83-85), and Mathlib does not require blank lines
  between consecutive `variable` commands. I dropped this item.
- **Module docstring.** It describes the predicates and the file's role, not a list of
  lemmas or their setting. No main declaration was added or removed, so I made no request.
- **Sibling lemmas left normed but not touched by the PR.**
  - `mem_tangentConeAt_of_openSegment_subset` and `mem_tangentConeAt_of_segment_subset`
    only use `mem_tangentConeAt_of_pow_smul`, so they look generalizable.
  - `tangentConeAt_subset_zero` would need `T2Space`.
  - These are untouched code and out of scope for this PR. They are follow-up material, not
    requests.

## Findings written

2, both advisory: finding 1 is a generalization (`UniqueDiffWithinAt.mono`) and finding 2
is a proof golf (`tangentConeAt.lim_zero`).
