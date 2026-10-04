# Review notes: PR #29842, "feat(TangentCone): generalize some lemmas to TVS"

## What I did
- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then the whole of
  `target/Mathlib/Analysis/Calculus/TangentCone.lean` as the PR leaves it, through `file_read`.
- Ran lean_verify_edit with no edit: the file compiles with no errors and no warnings.
- Ran zulip_search ("tangentConeAt topological vector space ...", "tangent cone tangentConeAt"): nothing on
  this generalization.
- Ran precedent_search on `lim_zero` and on the TVS/Normed section split. It found PR #20859 and PR #21065,
  earlier attempts at the same generalization. On #21065 ADedecker suggested a three-line `lim_zero` proof
  through `cobounded` and raised the countability problem for lemmas that need closure approximation.

## Object by object
- **`tangentConeAt.lim_zero`** (proof modified, now under `[ContinuousSMul 𝕜 E]`). Joint continuity of the
  smul is genuinely needed, because both `(c n)⁻¹` and `c n • d n` vary. The statement is unchanged and the
  docstring still fits. The proof is correct, but a shorter form compiles (finding 3, advisory).
- **`variable [ContinuousSMul 𝕜 E]` / `variable [ContinuousAdd E]`** in the TangentCone TVS section.
  `tangentConeAt_mono_nhds` needs `ContinuousAdd` (`tendsto_const_nhds.add`) and `ContinuousSMul` (via
  `lim_zero`). `tangentConeAt_congr` and `tangentConeAt_inter_nhds` go through it. The as-is compile shows
  no unused-section-variable warning. Nothing to ask.
- **`tangentConeAt_closure`** (moved below `end TVS`). It correctly stays normed: the proof picks, for each n,
  a point at distance `u n / ‖c n‖`, which needs a countable neighbourhood basis. In a non-first-countable
  TVS (e.g. ℝ^I with I uncountable, s the finitely supported vectors) the statement fails. A
  `[FirstCountableTopology E]` version would be a separate PR. No ask.
- **Normed-section `variable` lines (E, F, G, `{x y}`, `{s t}`), re-added after the move.** Same content as
  before. Nothing to ask.
- **UniqueDiff TVS section, `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]`.** `mono_nhds`, `congr`,
  `inter`, `inter'`, `of_mem_nhds`, `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter` and
  `IsOpen.uniqueDiffOn` all need both, through `tangentConeAt_mono_nhds`. `UniqueDiffWithinAt.mono` does not
  need either: the direct proof via `tangentConeAt_mono` and `closure_mono` compiles above the variable line
  (finding 1, advisory).
- **`uniqueDiffWithinAt_closure`, the `of_closure`/`closure` alias and `UniqueDiffWithinAt.mono_closure`**
  (moved into the Normed section). They depend on `tangentConeAt_closure`, so they must stay normed. The
  bodies are unchanged and no deprecations are needed, because these are moves, not renames. No ask.
- **Ordering nit.** The TangentCone TVS section adds `ContinuousSMul` before `ContinuousAdd`; the UniqueDiff
  TVS section adds them the other way round. This is cosmetic and I would not ask for it.

## Generalizations I checked but did not report (untouched lemmas, likely follow-up)
- `tangentConeAt_subset_zero` and `UniqueDiffWithinAt.accPt` compile in the TVS section with `[T2Space E]`.
  I did report this one (finding 2, advisory), because it is the same argument as `tangentConeAt_mono_nhds`.
- `mem_tangentConeAt_of_openSegment_subset` compiles for `[AddCommGroup G] [Module ℝ G] [TopologicalSpace G]`
  with no norm at all, as a primed copy spliced into the TVS section.
- `tangentConeAt_mono_field` compiles in the UniqueDiff TVS section with `[Module 𝕜' E] [IsScalarTower 𝕜 𝕜' E]`
  and no `ContinuousAdd`/`ContinuousSMul`: the linter reports both as unused. `UniqueDiffWithinAt.mono_field`
  should therefore follow.
  These two lemmas are far from the PR's hunks, and an author would reasonably defer them. I record them
  here rather than as findings.
- `zero_mem_tangentCone`, `subset_tangentConeAt_prod_left/right`, `mapsTo_tangentConeAt_pi` and the
  `UniqueDiffWithinAt.prod/pi` family need closure approximation by sequences, so they need first
  countability (the same obstruction ADedecker raised on #21065). Correctly left normed.

## Tool calls that validated edits
- `UniqueDiffWithinAt.mono` moved above the variable line with a direct proof: compiled, no warnings.
- `tangentConeAt_subset_zero'` and `UniqueDiffWithinAt.accPt'` in TVS with `[T2Space E]`: compiled, no warnings.
- `tangentConeAt.lim_zero` three-line proof: compiled, no warnings.
- `mem_tangentConeAt_of_openSegment_subset'` in a topological ℝ-module: compiled.
- `tangentConeAt_mono_field'` in the TVS section: compiled, with only an unused-section-variable warning.
