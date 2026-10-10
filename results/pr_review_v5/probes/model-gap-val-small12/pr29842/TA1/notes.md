# Review notes: PR #29842, feat(TangentCone): generalize some lemmas to TVS

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then read the whole of
  `Mathlib/Analysis/Calculus/TangentCone.lean` as the PR leaves it, via `ptool file_read`
  (workspace path `target/...`).
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors and no
  warnings.
- Checked every proposed edit with `lean_verify_edit`; the arguments are in `tmp/a*.json`. Ran
  `precedent_search` on the `lim_zero` block, on the UniqueDiff TVS block and on the Normed section
  header, `zulip_search` for tangent cone / TVS context, and `content_search` for
  `tendsto_inv₀_cobounded`, to look for a duplicate lemma.

## Object by object

- **`tangentConeAt.lim_zero`** (proof rewritten; it moves into TVS under `[ContinuousSMul 𝕜 E]`).
  The new proof is correct and compiles. The assumption is the right one: `Tendsto.smul` needs
  `ContinuousSMul`. Filed three findings:
  - inline the single-use `have`;
  - merge `apply Tendsto.congr' this` / `rw … at hc` / `simpa` into one `simpa` (the same shape
    ADedecker suggested on this lemma in #21065);
  - `fun n =>` → `fun n ↦` in the statement.

  No duplicate lemma found: `tendsto_inv₀_cobounded` is used in only 4 other places, none of them
  this statement.
- **`variable [ContinuousSMul 𝕜 E]` (L109) and `variable [ContinuousAdd E]` (L122).** They are
  correctly separate. Merging them would pull `ContinuousAdd` into `lim_zero`, which does not use it.
  Blank lines surround both. Nothing filed.
- **`tangentConeAt_mono_nhds` / `_congr` / `_inter_nhds`** (moved into TVS). They genuinely need
  `ContinuousAdd` (through `tendsto_const_nhds.add`) and `ContinuousSMul` (through `lim_zero`).
  Their deprecated aliases moved with them. Nothing filed.
- **`end TVS` / `section Normed` (L147-153) and `tangentConeAt_closure`** (moved, unchanged).
  - The `@[simp]` is kept.
  - The proof uses `Metric.mem_closure_iff` and `dist_smul₀`. A TVS version would need first
    countability, so I asked for nothing on it.
  - Filed a blank line after `section Normed`.
- **UniqueDiff TVS block** (`variable [ContinuousAdd E] [ContinuousSMul 𝕜 E]` at L433, then
  `mono_nhds`, `mono`, `uniqueDiffWithinAt_congr`, `_inter`, `.inter`, `_inter'`, `.inter'`,
  `_of_mem_nhds`, `IsOpen.uniqueDiffWithinAt`, `UniqueDiffOn.inter`, `IsOpen.uniqueDiffOn`).
  - Everything except `UniqueDiffWithinAt.mono` really goes through `mono_nhds`, so it needs the
    continuity assumptions.
  - **`UniqueDiffWithinAt.mono` does not.** It follows from `tangentConeAt_mono` and
    `closure_mono`, and that version compiled. Filed.
- **UniqueDiff `section Normed` (L479-495): `uniqueDiffWithinAt_closure`, the
  `of_closure`/`closure` alias and `mono_closure`** (moved, unchanged). Attributes are kept
  (`@[simp]`, `protected`). They still depend on the normed `tangentConeAt_closure`. Nothing filed
  beyond the blank-line finding.
- **Further lemmas the PR leaves normed but which hold in a TVS** (all verified to compile):
  - the segment and open-segment lemmas: any topological real module, no continuity;
  - `uniqueDiffWithinAt_convex` and `uniqueDiffOn_convex`: a real TVS, with
    `IsTopologicalAddGroup` and `ContinuousSMul ℝ`; this works only together with the segment
    lemmas;
  - the three `mono_field` lemmas: a topological module with a scalar tower, no continuity. Their
    docstrings also say "normed", "Given `x ∈ s`" and "larger field `𝕜`";
  - `tangentConeAt_subset_zero` and `UniqueDiffWithinAt.accPt`: a Hausdorff TVS.

  Filed as four advisory findings.
- **The repeated `variable {x y : E} {s t : Set E}`.** It can be declared once at file level; that
  compiled. Filed as advisory.
- **PR title and description.** "some lemmas" names none of them. Filed as advisory.
- **Left alone:**
  - `subset_tangentConeAt_prod_left`/`_right`, `mapsTo_tangentConeAt_pi`, `zero_mem_tangentCone`,
    `tangentConeAt_nonempty_of_properSpace` and `tangentConeAt_eq_univ`: genuinely normed proofs,
    untouched by the PR;
  - the `.prod`/`.pi` UniqueDiff lemmas: they depend on those;
  - the Real interval lemmas.
- No naming changes: the PR adds or renames no declaration.

## Conventions: what I filed and what I left

1. **Reuse existing variables.** Filed: hoist `variable {x y : E} {s t : Set E}` (L85/153/414/483)
   to L76. No new declaration in the PR adds binders that duplicate a variable.
2. **Drop unneeded hypotheses.** Filed: `UniqueDiffWithinAt.mono` (continuity is not needed).
   Left `lim_zero` and `tangentConeAt_mono_nhds`: removing either assumption breaks the proof
   (`Tendsto.smul`, `tendsto_const_nhds.add`).
3. **Blank line around section/end/variable.** Filed: `section Normed` at L149 and L479. Left
   L109, L122, L147, L433 and L477: the lines either side of each are blank.
4. **Inline a short `have`.** Filed: `lim_zero`'s `have`. No other changed proof has one.
5. **Merge consecutive tactic calls.** Filed: `lim_zero` (`apply …congr'`, `rw … at hc`, `simpa`).
6. **Automation vs explicit proof.** Left: the changed proof's only automation is `simpa using`
   (L120), which closes a one-step `zero_smul` goal.
7. **Module docstring in step.** Left: L14-22 still describe `tangentConeAt`, `UniqueDiffWithinAt`
   and `UniqueDiffOn`, which are the file's definitions. The PR adds no main result and the
   docstring states no normed-space restriction.
8. **`fun` with `↦`.** Filed: the `lim_zero` statement (`fun n =>`). The new proof (L117) and the
   moved `tangentConeAt_closure` (L169-170, `fun _ ↦`) already conform.
9. **Shared arguments as `variable`.** Left: the PR adds its new assumptions as `variable` lines
   (L109, L122, L433). No changed signature repeats a shared argument.
10. **State for the abstract property, not a concrete object.** Filed four:
    - segment lemmas: any topological real module;
    - convex lemmas: a real TVS;
    - `mono_field` family: a topological module;
    - `tangentConeAt_subset_zero` and `accPt`: a Hausdorff TVS.
11. **Keep attributes on moved declarations.** Left: `@[simp]` on `tangentConeAt_closure` (L155)
    and `uniqueDiffWithinAt_closure` (L485), and `protected alias` (L490), are kept as before.
    `mono_closure` had no attribute before and has none now.
12. **Title and description precise.** Filed: the PR-level finding.
13. **Filter API.** Left: `lim_zero` uses `.mono` (L117) and `tangentConeAt_closure` uses
    `filter_upwards` (L163). Nothing is unpacked by hand.
14. **No dense one-liners.** Left: the new `lim_zero` proof is four short steps. My merge
    suggestion keeps it at two readable lines.
15. **Every section closed.** Left: all of them are closed (`end TVS` L147/477, `end Normed`
    L401/588, `end TangentCone` L403, `end RealNormed` L615, `end Real` L683, `end UniqueDiff`
    L685).
16. **No heavier machinery than needed.** Left: the new `lim_zero` proof uses
    `tendsto_inv₀_cobounded` from `Analysis/Normed/Field/Lemmas`, already reachable; no new import.
17. **Docstring terminology matches generality.** Filed as part of the `mono_field` finding. The
    changed `lim_zero` docstring ("under the assumptions defining the tangent cone") is accurate.
18. **Group declarations about one notion.** Left: the moves are forced by the TVS/Normed split,
    and `tangentConeAt_closure` and the `*_closure` lemmas sit at the head of their Normed
    sections.
19. **Change only what the purpose requires.** Left: the only proof rewrite is `lim_zero`, whose
    old proof used `‖d n‖` and so had to change for TVS. Nothing is renamed.
20. **No `omit` sections.** Left: there is no `omit` in the file.
21. **Not over-general.** Left: the new assumptions are the minimal standard ones.
22. **Library spelling of hypotheses.** Left: `lim_zero`'s `hc` matches the `tangentConeAt`
    definition's `Tendsto (fun n => ‖c n‖) atTop atTop` (L49).
23. **`variable` only for widely shared arguments.** Covered by the `mono_field` finding, whose
    𝕜' variables serve only those three lemmas. Left L109/L122: each serves 3-4 lemmas, and they
    have to stay separate (see above).
24. **`simpa using` rather than backward rewriting.** Left: `lim_zero` already ends in
    `simpa using …` (L120).
25. **PR title format `type(Area): description`.** Left: `feat(TangentCone): …` has that form.
