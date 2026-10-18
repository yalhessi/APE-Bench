# Review notes: PR #33362 "feat: weaken assumptions in Schwarz lemma"

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Tools used through `./ptool`: `describe`,
`file_search`, `file_read` (whole PR file at `target/Mathlib/Analysis/Complex/Schwarz.lean`),
`content_search` (uses of every changed lemma across `target/Mathlib`; `conj` and `Set.` in the file),
`declaration_search` (the two `abs_deriv_*` names in the module doc), `naming_norm`,
`precedent_search` (nothing relevant came back), and `lean_verify_edit` (9 edits, listed below). Scratch
files are in `tmp/`. `tmp/Schwarz_revised.lean` is the whole file with every compilable finding applied;
it compiled as one edit (`tmp/z_all.json`: `compiled`, no errors, no warnings).

Downstream impact: `content_search` finds no use of any changed lemma outside `Schwarz.lean`, so
neither the switch from `ball` to `closedBall` nor the dropped `hc : f c = c` breaks anything else in
Mathlib.

## Object by object

- **Module docstring.** Filed four findings:
  - Bullets 25-31 still describe `f : ℂ → ℂ`, `f c = c` and `dist (f z) c` (blocking).
  - Bullet 33-34 for `norm_le_norm_of_mapsTo_ball_self` was never updated (blocking).
  - Two names do not exist: `abs_deriv_le_div_of_mapsTo_ball` and `abs_deriv_le_one_of_mapsTo_ball`
    (`declaration_search`: none in the base or the PR).
  - The TODO was deleted, but the doc lists neither `norm_dslope_le_div_of_mapsTo_ball` nor the
    equality-case `affine_*` lemmas.

  A fifth finding is a nit: "closed disk" on line 22 is the wrong word for a ball in `E`. The
  "Implementation notes" ("some versions ... for `f : ℂ → E`") are still true, so nothing filed there.
- **`open scoped Topology ComplexConjugate`.** `ComplexConjugate` is unused (no `conj` in the file).
  Removing it compiles. Filed.
- **The `variable` line.** Adding `R` to `{R R₁ R₂ : ℝ}` replaces the old second `variable` block.
  Nothing wrong.
- **`Complex.schwarz_aux`.**
  - The hypothesis change and the `← mem_closedBall_iff_norm` rewrite are correct.
  - Filed:
    - the `Complex.` prefix outside the namespace. Moving the namespace and the public section was
      unnecessary: the original layout with `private` added compiles.
    - the placeholder name. A descriptive rename compiles.
    - no deprecation for the public name that disappears (advisory, phrased as a question).
    - golfing the rewritten line 79 into `(mem_sphere.mp hz).trans_lt hr.2`, which removes the `;`
      and the `.1`/`.2`. It compiles.
  - Inlining it is an alternative, but at 24 lines it would make the single calc step unreadable, so
    I asked for the rename.
- **`@[expose] public section`.** No definitions in the file, so `@[expose]` has no effect. Plain
  `public section` compiles. Filed.
- **`norm_dslope_le_div_of_mapsTo_ball`.**
  - Correct:
    - `hR₂ : 0 ≤ R₂` via `nonempty_closedBall.mp`;
    - dropping `hg₀`, which `mapsTo_closedBall` does not need;
    - `g.lipschitz.mapsTo_closedBall (f c) R₂`.
  - Filed the changed `rw ...; exact ...` line: one tactic per line.
  - Docstring "Two cases ... merged together" is fine.
- **`affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div`.**
  - Removing `by_cases h : z = c; · simp [h]` is right: the step is unneeded and the PR compiles
    without it. That matches the "remove unneeded steps" convention, so I did not file it as scope
    churn.
  - Tested dropping `[CompleteSpace E]`: it fails (`differentiableOn_dslope` needs it), so no
    generalization to ask for.
  - Filed `Set.MapsTo`/`Set.EqOn` while `Set` is open. Without the prefix the binders fit on one
    97-char line, so the PR's split is no longer needed.
- **`affine_of_mapsTo_ball_of_exists_norm_dslope_eq_div'`.** The only change is `h_maps`, which is
  fine apart from the `Set.` prefix, covered by the finding above. It has no docstring, but it did not
  have one before either and theorems are not docBlame-linted. Not filed.
- **`norm_deriv_le_div_of_mapsTo_ball`.** The statement and proof are fine, and the new line break is
  needed (the joined line is over 100). The docstring still says "open ball": filed, blocking.
  `h₀ : 0 < R₁` is needed, since the conclusion fails for an empty ball.
- **`dist_le_div_mul_dist_of_mapsTo_ball`.** The statement change and the docstring update are both
  correct. Nothing filed.
- **`norm_deriv_le_one_of_mapsTo_ball`.** The generalization (any `E`, no fixed point) and the proof
  are correct. The docstring is stale: filed, blocking. `h₀ : 0 < R` is needed.
- **`dist_le_dist_of_mapsTo_ball_self`.** The generalization and the `simpa` proof are correct.
  - Filed the stale docstring (blocking) and `.1` → `.mp`, which compiles.
  - Filed the `_self` naming as an advisory question.
- **`norm_le_norm_of_mapsTo_ball_self`.** The statement, proof and docstring content are correct.
  Filed a reflow of the docstring's short lines. The reflowed first line is exactly 100 chars.
- **PR description.** It omits the dropped `hc` argument, the new conclusion, the privatisation and
  the TODO removal. Filed, advisory.

## Conventions: places filed and places left

- **namespace grouping / no redundant prefix.**
  - Filed: `Complex.schwarz_aux` (prefix outside the namespace); `Set.MapsTo`/`Set.EqOn` in the
    `affine_*` lemmas (`Set` is open).
  - Left: every other declaration sits inside `namespace Complex` with no prefix (lines 85-175).
- **drop unneeded hypothesis.** No place filed. `[CompleteSpace E]` was tested and is needed. `h₀`
  is needed in the derivative lemmas. The PR itself drops `hc`.
- **terminal `simp` not squeezed.** Left: the new `simpa [...]` calls on lines 165 and 173 are
  unsqueezed and terminal. The `simpa only` calls on 103, 140 and 150 are unchanged lines.
- **name built from the statement.** Filed `dist_le_dist_of_mapsTo_ball_self`'s `_self`, as a
  question. Left: the other names, which this PR does not rename (renaming them would be scope churn).
- **module doc covers the main results.** Filed the missing `norm_dslope` and `affine_*` bullets, plus
  the stale bullets and the wrong names.
- **unused / repeated `open`.** Filed `ComplexConjugate`. Left `open Metric Set Function Filter
  TopologicalSpace`: the PR does not change that line.
- **concrete → general.** No place: the PR generalizes the codomain itself.
- **deprecate removed declarations.** Filed `Complex.schwarz_aux`, made private. Nothing else was
  removed or renamed.
- **break lines only past 100.**
  - Filed the `norm_le_norm_of_mapsTo_ball_self` docstring, and the `affine_*` binder split as part of
    the `Set.` finding.
  - Left `norm_deriv_le_div_of_mapsTo_ball`, line 138-139: joined it would be over 100.
- **one tactic per line.** Filed line 94 (`rw ...; exact ...`) and line 79 (nested `by rw ...; exact`).
- **remove unneeded steps.** No place filed. The PR's own removals of `by_cases` and `hg₀` comply.
- **consistent spelling.** Filed "closed disk" vs "closed ball" in the module doc.
- **comments in step with the code.** Filed the three stale declaration docstrings and the stale
  module-doc bullets. The TODO removal is folded into the module-doc finding.
- **PR description precise.** Filed.
- **`.mp`/`.mpr` over `.1`/`.2`.** Filed lines 77/79 (in the `schwarz_aux` golf finding) and line 165.
  Left lines 61, 91 and 151: unchanged lines.
- **docstring terminology matches generality.** Covered by the "disk" vs "ball" finding and the
  `f : ℂ → ℂ` → `f : ℂ → E` docstring findings.
- **whole-file section.** Left: `public section` is the module-system idiom, not a removable section.
- **descriptive names, not `aux`.** Filed `schwarz_aux`.
- **inline single-use aux.** Folded into the `schwarz_aux` naming finding as the alternative.
- **minimal changes / scope.** Filed the namespace and public-section restructuring, folded into the
  `Complex.schwarz_aux` namespace finding.
- **private vs public API.** Left: `schwarz_aux` serves one proof, so `private` fits this convention.
  The deprecation of its old public name is filed separately.
- **module: mark instances public.** No instances or downstream-needed declarations outside the public
  section.
- **no `x = f y` hypotheses.** None in the file.
- **`≠` over `<` in hypotheses.** `h₀ : 0 < R₁` / `0 < R` cannot be weakened to `≠ 0` for real radii
  (a negative radius gives an empty ball). Left.
- **`@[expose]` on individual defs.** Filed: no definitions, so drop `@[expose]` from the section.

Findings written: 20 (5 blocking, 15 advisory).
