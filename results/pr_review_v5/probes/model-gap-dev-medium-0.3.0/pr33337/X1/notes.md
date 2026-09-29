# Review notes: PR #33337 (rename lemmas in InnerProductSpace/Projection/Submodule)

Inputs read: brief.md, pr.md, model.md, diff.patch. The file as the PR leaves it came from
`file_read` on target/Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean, lines 1-240.

## Objects

### `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` (renamed from `orthogonalProjection_eq_linearProjOfIsCompl`)
- The statement is pointwise, `K.orthogonalProjection x = K.linearProjOfIsCompl _ _ x`. Adding
  `_apply_` separates it from the function-level `coe_` lemma, which fits the usual `foo` / `foo_apply` split.
- naming_norm: `insufficient_evidence` (subject `K`, no dominant prefix). No finding.
- Proof: unchanged. Golfing it is out of scope for a rename PR. No finding.

### `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` (renamed from `orthogonalProjection_coe_eq_linearProjOfIsCompl`)
- Stated with a coercion ascription `(K.orthogonalProjection : E →ₗ[𝕜] K)`. naming_norm: `coe_` 48 vs
  `toLinearMap_` 9 over 124, so `coe_` is the plurality and the prefix is fine. The proof now uses the
  renamed pointwise lemma. No finding.

### `Submodule.coe_starProjection_eq_isComplProjection` (renamed from `starProjection_coe_eq_isCompl_projection`)
- Finding 1 (blocking): `isComplProjection` is a new spelling. Every existing lemma name writes
  `IsCompl.projection` as `isCompl_projection` (3 declarations in LinearAlgebra/Projection.lean), and
  so did the old name. Renaming to `coe_starProjection_eq_isCompl_projection` compiled under lean_verify_edit.
- Finding 2 (advisory): the `coe_` prefix sits on a statement written with `.toLinearMap`. The census
  gives `toLinearMap_` 21 vs `coe_` 7, verdict emerging. Two edits compiled: renaming to `toLinearMap_...`,
  and keeping `coe_` with the ascription `(K.starProjection : E →ₗ[𝕜] E)`.
- I considered dropping `open Submodule in` as redundant inside `namespace Submodule`. lean_verify_edit
  showed it is required: without it, dot notation cannot resolve `IsCompl.projection`. So no finding.
- Proof: pre-existing `simp`, only the lemma name inside it changed. No finding.

### Removed `Submodule.starProjection_coe_eq_isCompl_projection`
- A deprecated alias (2025-12-26) replaces it. That is correct.

### Deprecated-alias commands (4 changed or added)
- The old 2025-07-11 aliases (`orthogonalProjection_eq_linear_proj`,
  `orthogonalProjection_coe_linearMap_eq_linearProj`) now point straight at the new names, so no alias
  points at another deprecated alias. That is correct.
- The new aliases have date 2025-12-26, which matches the Zulip cutoff of 2025-12-27. That is plausible.
- content_search over the whole target tree finds no remaining use of any old name outside the alias
  lines, so there are no deprecation warnings downstream. No finding.

### `LinearMap.IsSymmetricProjection.le_iff_range_le_range`, `Submodule.starProjection_le_starProjection_iff` (Positive.lean)
- The only change at each is the updated lemma name at the use site. Each would need a further update
  if finding 1 or 2 is adopted. That is recorded in the findings, not as separate findings.

## Tools used
describe, file_search, file_read, declaration_search (IsCompl.projection, Submodule.linearProjOfIsCompl),
content_search (spelling censuses, leftover old names, toLinearMap siblings), naming_norm (3 renamed
lemmas), zulip_search (3 queries), precedent_search (1), lean_verify_edit (4 edits: 3 succeeded; 1 failed,
which showed `open Submodule in` is needed).
