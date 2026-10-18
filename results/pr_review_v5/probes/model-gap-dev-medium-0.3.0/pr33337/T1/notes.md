# Review notes: PR #33337 (rename lemmas in Analysis/InnerProductSpace/Projection/Submodule)

## What I did
I read brief.md, pr.md, model.md and diff.patch, and ran `ptool describe`. I read the PR's version of
`Projection/Submodule.lean` (lines 1-230), `Positive.lean` (lines 490-515) and
`LinearAlgebra/Projection.lean` (lines 120-330 and 598-618).

Tools used:
- content_search: uses of old and new names, the `isCompl_projection` spelling, other
  `*Projection_coe*` names;
- declaration_search: `IsCompl.projection`, `Submodule.linearProjOfIsCompl`;
- naming_norm: all three renamed lemmas;
- zulip_search: IsCompl.projection naming, the lowerCamelCase foreign-name convention, the old name;
- precedent_search: the new starProjection lemma;
- lean_verify_edit: one edit, below.

## Object by object
- `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` (renamed from
  `orthogonalProjection_eq_linearProjOfIsCompl`). Adding `_apply` is right: the LHS is
  `K.orthogonalProjection x`. naming_norm is insufficient_evidence, so it gives no prefix ask. It has
  a deprecated alias. The older alias `orthogonalProjection_eq_linear_proj` (2025-07-11) is
  re-pointed straight at the new name, so it does not chain through a deprecated alias. That is
  correct. No finding.
- `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` (from
  `orthogonalProjection_coe_eq_linearProjOfIsCompl`). The LHS is the coercion ascription
  `(K.orthogonalProjection : E →ₗ[𝕜] K)`, so the `coe_` prefix fits. naming_norm gives `coe_` the
  plurality (48 of 124), verdict insufficient_evidence. It has a deprecated alias, and the older
  alias `orthogonalProjection_coe_linearMap_eq_linearProj` is re-pointed correctly. No finding.
- `Submodule.coe_starProjection_eq_isComplProjection` (from
  `starProjection_coe_eq_isCompl_projection`).
  - Prefix: naming_norm says `toLinearMap_` is the emerging prefix for this subject (21 to 7),
    advisory at most. The statement writes `.toLinearMap`, but that is the same coercion and
    displays as `↑`, and the sibling lemma above uses `coe_`. I did not raise it.
  - Middle component: `isCompl_projection` became `isComplProjection`. This follows the
    lowerCamelCase foreign-name convention found on Zulip. But three existing lemmas about the same
    definition keep `isCompl_projection`, so the PR leaves the spelling inconsistent. This is
    **finding 1** (advisory).
  - `open Submodule in`: I tested removing it, since it sits inside `namespace Submodule`.
    lean_verify_edit returned compile_errors: "Invalid field `projection`: The environment does not
    contain `IsCompl.projection`". Dot notation needs it, because the definition is
    `Submodule.IsCompl.projection`. Keeping it is correct, so no finding.
  - Proof: only the reference changed. No golf requested.
- `Submodule.starProjection_coe_eq_isCompl_projection` (removed). Replaced by a deprecated alias
  dated 2025-12-26, which is consistent with the Zulip as_of date of 2025-12-27. No finding.
- Deprecated-alias commands (4 entries in model.md). All point at the current names, with no chains
  through deprecated names. No finding.
- `LinearMap.IsSymmetricProjection.le_iff_range_le_range` and
  `Submodule.starProjection_le_starProjection_iff` (Positive.lean). These only change the reference
  to the new name. The file compiles as the PR leaves it: the lean_verify_edit run reported
  `errors_already_in_the_file: []` and 0 warnings for Submodule.lean. No finding.
- Completeness: content_search over the whole tree finds no remaining use of any old name outside
  the aliases. A deprecated use elsewhere would fail CI as a warning, and there is none. No other
  `*Projection_coe*` names are left in the area.
- Documentation: none of the renamed theorems has a docstring. They had none before, and Mathlib
  does not require docstrings on theorems. The module docstring is unaffected. No finding.
