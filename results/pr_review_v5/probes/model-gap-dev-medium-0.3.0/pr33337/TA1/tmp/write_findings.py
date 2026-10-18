import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33337/TA1"
findings = [
 {
  "target": "Submodule.coe_starProjection_eq_isComplProjection",
  "claim": "The new name `coe_starProjection_eq_isComplProjection` spells the right-hand side `IsCompl.projection` (declared as `Submodule.IsCompl.projection`) as the re-tokenised `isComplProjection`, which names no declaration. Mathlib spells this term `isCompl_projection` everywhere it appears in a name (`Submodule.linearProjOfIsCompl_isCompl_projection`, `IsIdempotentElem.eq_isCompl_projection`, `isIdempotentElem_iff_eq_isCompl_projection_range_ker`), and the old name `starProjection_coe_eq_isCompl_projection` already had that spelling, so the rename introduces an inconsistency the PR did not need.",
  "requested_change": "Rename the theorem to `coe_starProjection_eq_isCompl_projection` (only the `coe_` move is needed), point the deprecated alias at it: `@[deprecated (since := \"2025-12-26\")] alias starProjection_coe_eq_isCompl_projection := coe_starProjection_eq_isCompl_projection`, and update the two uses in `Mathlib/Analysis/InnerProductSpace/Positive.lean` (`LinearMap.IsSymmetricProjection.le_iff_range_le_range` and `Submodule.starProjection_le_starProjection_iff`).",
  "severity": "blocking",
  "evidence": "content_search for `isComplProjection|isCompl_projection` over target/Mathlib: the only `isComplProjection` occurrences are this PR's new name and its two call sites; `isCompl_projection` appears in Mathlib/LinearAlgebra/Projection.lean:224,604,612 and Symmetric.lean:299. declaration_search: `Submodule.IsCompl.projection` is declared at Mathlib/LinearAlgebra/Projection.lean:154 (namespace `IsCompl`, field-style name `projection`). lean_verify_edit on Submodule.lean replacing lines 209-214 with the renamed theorem and the retargeted alias: outcome `compiled`, no errors or warnings."
 },
 {
  "target": "Submodule.coe_starProjection_eq_isComplProjection",
  "claim": "The statement reaches the linear map through the raw projection `K.starProjection.toLinearMap`, while the lemma is now named `coe_starProjection_...` and its sibling `coe_orthogonalProjection_eq_linearProjOfIsCompl` (and `LinearMap.isSymmetricProjection_iff_eq_coe_starProjection`) write the registered coercion `(K.orthogonalProjection : E →ₗ[𝕜] K)` / `↑K.starProjection`.",
  "requested_change": "State the left-hand side through the coercion, matching the sibling and the `coe_` name: `theorem coe_starProjection_eq_isCompl_projection [K.HasOrthogonalProjection] :\n    (K.starProjection : E →ₗ[𝕜] E) =\n      K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by\n  simp [starProjection, coe_orthogonalProjection_eq_linearProjOfIsCompl, IsCompl.projection]` (the line must be broken after `=` to stay under 100 characters).",
  "severity": "advisory",
  "evidence": "lean_verify_edit with this statement (lines 209-214 replaced, `open Submodule in` kept): outcome `compiled`, no warnings. A first attempt on one line compiled but raised the 100-character longLine warning, hence the break. The same call checked `example [K.HasOrthogonalProjection] : K.starProjection.toLinearMap = (K.starProjection : E →ₗ[𝕜] E) := by with_reducible rfl`, which compiled, so the coerced statement is the same term and existing `simp_rw`/`simpa` uses are unaffected. naming_norm on the declaration: subject `toLinearMap` (the `.toLinearMap` spelling), verdict `emerging` for a `toLinearMap_` prefix (21 vs `coe_` 7) -- i.e. as currently spelled the statement and the `coe_` name disagree; the area's siblings (Projection/Basic.lean:664,675; Submodule.lean:198) resolve that toward the coercion."
 },
 {
  "target": "Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl",
  "claim": "Inside `namespace Submodule` the renamed theorem still writes the namespace prefix the enclosing namespace supplies: `Submodule.isCompl_orthogonal_of_hasOrthogonalProjection` twice (statement and `have`) and `Submodule.coe_mem _` in the final `rw`.",
  "requested_change": "Drop the redundant prefixes: write `K.linearProjOfIsCompl _ isCompl_orthogonal_of_hasOrthogonalProjection x` in the statement, `have : IsCompl K Kᗮ := isCompl_orthogonal_of_hasOrthogonalProjection`, and `orthogonalProjection_mem_subspace_orthogonalComplement_eq_zero (coe_mem _)`.",
  "severity": "advisory",
  "evidence": "file_read of Submodule.lean: `namespace Submodule` at line 32, `end Submodule` at 216; the prefixed names are at lines 186, 187 and 191. lean_verify_edit replacing lines 184-201 with the unprefixed versions of this theorem and of `coe_orthogonalProjection_eq_linearProjOfIsCompl` (deprecated aliases unchanged): outcome `compiled`, no errors, no warnings."
 },
 {
  "target": "Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl",
  "claim": "Inside `namespace Submodule` the renamed theorem's statement writes `Submodule.isCompl_orthogonal_of_hasOrthogonalProjection`, a prefix the enclosing namespace already supplies.",
  "requested_change": "Write the right-hand side as `K.linearProjOfIsCompl _ isCompl_orthogonal_of_hasOrthogonalProjection`.",
  "severity": "advisory",
  "evidence": "Line 200 of Submodule.lean, within `namespace Submodule` (lines 32-216). Checked in the same lean_verify_edit as the previous finding (lines 184-201 replaced): outcome `compiled`, no errors, no warnings."
 },
 {
  "target": "PR #33337",
  "claim": "The title `chore(Analysis/InnerProductSpace/Projection/Submodule): rename lemmas` does not say which lemmas are renamed or to what, and the description is not available at review time, so the PR record does not state the three renames it makes.",
  "requested_change": "Question to the author: please list the renames in the PR description -- `orthogonalProjection_eq_linearProjOfIsCompl` -> `orthogonalProjection_apply_eq_linearProjOfIsCompl`, `orthogonalProjection_coe_eq_linearProjOfIsCompl` -> `coe_orthogonalProjection_eq_linearProjOfIsCompl`, `starProjection_coe_eq_isCompl_projection` -> `coe_starProjection_eq_isCompl_projection` -- and make the title name them, e.g. `chore(Analysis/InnerProductSpace/Projection/Submodule): rename lemmas relating orthogonal/star projections to linearProjOfIsCompl`.",
  "severity": "advisory",
  "evidence": "pr.md: title as quoted; description `(not recoverable at review start)`. The diff makes exactly three renames (model.md objects 19b24c6c42, d2466bcc94, 4da0a29709) plus two call-site updates in Positive.lean."
 }
]
json.dump(findings, open(f"{D}/findings.json", "w"), indent=1, ensure_ascii=False)
print(len(json.load(open(f"{D}/findings.json"))))
