# Review notes: PR #29842, "feat(TangentCone): generalize some lemmas to TVS"

Inputs read: `brief.md`, `pr.md` (description not recoverable), `model.md`, `diff.patch`. Using
`file_read`, I then read the whole of `target/Mathlib/Analysis/Calculus/TangentCone.lean` as the PR
leaves it. As-is compile check (`lean_verify_edit` with no edit): it compiles, with no errors or
warnings.

## What the PR does

- The `TVS` section of the tangent-cone part is extended past `tangentConeAt_mono`. First comes
  `variable [ContinuousSMul 𝕜 E]` and `tangentConeAt.lim_zero`, with a new proof. Then come
  `variable [ContinuousAdd E]` and `tangentConeAt_mono_nhds`, `tangentConeAt_congr` and
  `tangentConeAt_inter_nhds`. `tangentConeAt_closure` moves, unchanged, into the following
  `section Normed`.
- In the UniqueDiff part, `variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` is added to the TVS
  section. The section now runs from `UniqueDiffWithinAt.mono_nhds` to `IsOpen.uniqueDiffOn`. Three
  lemmas move, unchanged, into the next `section Normed`, because they depend on the metric proof of
  `tangentConeAt_closure`: `uniqueDiffWithinAt_closure`, the `of_closure`/`closure` alias and
  `UniqueDiffWithinAt.mono_closure`.
- The model lists removed+added pairs for `tangentConeAt_closure`, `uniqueDiffWithinAt_closure` and
  `UniqueDiffWithinAt.mono_closure`. They are pure moves: no rename, so no deprecation is needed.

## Object by object

- **`tangentConeAt.lim_zero`** (proof changed, now TVS + ContinuousSMul). ContinuousSMul is needed
  for `Tendsto.smul`, and ContinuousAdd is correctly not assumed. The proof is correct and much
  shorter than before. Applying the brief's merge-consecutive-tactics convention:
  `apply Tendsto.congr' this` can be folded into the closing `simpa` (`... .congr' this`). Verified
  to compile, as was a variant that also inlines the `rw ... at hc`. precedent_search found
  ADedecker suggesting exactly this shape on PR #21065, which touched this same proof. ->
  finding (advisory).
- **`tangentConeAt_mono_nhds` / `_congr` / `_inter_nhds`** (moved into TVS, proofs unchanged).
  These need ContinuousAdd, for `tendsto_const_nhds.add`, and ContinuousSMul, through `lim_zero`.
  ContinuousAdd is already weaker than `IsTopologicalAddGroup`. Nothing to request.
- **`tangentConeAt_closure`** (moved, unchanged, still Normed). The proof is metric
  (`Metric.mem_closure_iff`, `dist_smul₀`). A TVS version would need sequences approximating in
  every neighbourhood, so it is not a mechanical generalization. Keeping it normed is right. Nothing
  to request.
- **`UniqueDiffWithinAt.mono_nhds`, `uniqueDiffWithinAt_congr`, `_inter`, `.inter`, `_inter'`,
  `.inter'`, `uniqueDiffWithinAt_of_mem_nhds`, `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter`,
  `IsOpen.uniqueDiffOn`** (now TVS + ContinuousAdd + ContinuousSMul). All of them go through
  `tangentConeAt_mono_nhds`, so they need the assumptions. Nothing to request.
- **`UniqueDiffWithinAt.mono`** (now TVS + ContinuousAdd + ContinuousSMul). It does not need either
  continuity assumption. `tangentConeAt_mono` plus `closure_mono` prove it in a bare TVS. Verified
  by a line-mode edit placing it above the variable line, with a `#check` showing the reduced
  signature. -> finding (advisory).
- **`uniqueDiffWithinAt_closure`, `UniqueDiffWithinAt.of_closure`/`.closure`,
  `UniqueDiffWithinAt.mono_closure`** (moved into Normed). They are forced by
  `tangentConeAt_closure`. Nothing to request.
- **Section / variable commands** (the `section in TangentCone.lean` objects): the
  `end TVS`/`section Normed` boundaries and the variable lines are consistent, and the file compiles.
  The normed `G` variable line in the first `section Normed` exists only for the segment lemmas (see
  below).
- **Lemmas not changed by the PR that could also be generalized.** The brief does not ask for this,
  but it is in the PR's theme.
  - `mem_tangentConeAt_of_openSegment_subset` and `mem_tangentConeAt_of_segment_subset` use no norm
    on `G`. Both compile over `[AddCommGroup G] [Module ℝ G] [TopologicalSpace G]` with unchanged
    proofs, and `uniqueDiffWithinAt_convex` still compiles. They must move together: the segment
    lemma alone times out at isDefEq. -> finding (advisory).
  - `tangentConeAt_subset_zero` and `UniqueDiffWithinAt.accPt` also compile in a TVS with
    `[ContinuousAdd E] [ContinuousSMul 𝕜 E] [T2Space E]`; I verified this with explicit binders.
    I did not file it. It adds a new hypothesis (T2), which is a design choice, and it reads as
    follow-up scope rather than a request on this PR.
- **Naming:** no new names. **Documentation:** the existing docstrings remain accurate. The module
  docstring needs no TVS note, and the motivation convention does not apply, since this is a
  generalization rather than a new concept. **Correctness:** the file compiles. I cannot check
  downstream callers that pass instance arguments positionally, and nothing in the diff suggests
  any exist.

## Tool calls

- `lean_verify_edit`:
  - as-is: compiled.
  - `lim_zero` merged `simpa`: compiled.
  - `lim_zero` fully inlined: compiled.
  - `mono` without continuity: compiled.
  - open-segment lemma in a TVS: compiled.
  - segment lemma alone: timeout error.
  - both segment lemmas: compiled.
  - `subset_zero`/`accPt` in a T2 TVS: compiled.
- `precedent_search`: run twice, for the `lim_zero` proof and for the TVS variable block.
- `zulip_search`: TVS tangent cone. It found only a Kudryashov note that a TVS generalization of
  `tangentConeAt` was planned.
