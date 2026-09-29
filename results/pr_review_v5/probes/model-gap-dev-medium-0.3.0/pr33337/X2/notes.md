# Review notes: PR #33337 (rename lemmas in Projection/Submodule)

What I read: pr.md, model.md and diff.patch. Through ptool I also read Projection/Submodule.lean
(lines 1-225), Projection/Basic.lean (lines 655-700) and LinearAlgebra/Projection.lean
(lines 145-245).

Tools used: naming_norm on all three renamed lemmas; content_search for sibling spellings and for
any remaining uses of the old names; zulip_search (naming of `IsCompl.projection`,
`coe_` vs `toLinearMap_`, maintainers only); precedent_search on both renamed hunks;
lean_verify_edit (two edits and one as-is check).

## Objects

- `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` (was `orthogonalProjection_eq_linearProjOfIsCompl`).
  The statement is applied (`K.orthogonalProjection x = ...`), so adding `_apply` is accurate.
  naming_norm: insufficient_evidence (the subject is `K`, and prefix counts are scattered). Siblings
  such as `orthogonalProjection_eq_zero_iff` leave out `_apply`, but that does not make `_apply` wrong. The deprecated
  alias is dated 2025-12-26, and the older 2025-07-11 alias `orthogonalProjection_eq_linear_proj` now points at
  the new name, so there is no chain of deprecated aliases. No finding.
- `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` (was `orthogonalProjection_coe_eq_linearProjOfIsCompl`).
  Moving `coe` to the front matches the maintainer line on Zulip ("`coe` should be a prefix",
  Dillies 2025-06-17) and the local sibling `LinearMap.isSymmetricProjection_iff_eq_coe_starProjection`.
  naming_norm: `coe_` is the plurality (48 of 124), so there is no case for a rename. Both old names have deprecated
  aliases, and the older one is retargeted. No finding.
- `Submodule.coe_starProjection_eq_isComplProjection` (was `starProjection_coe_eq_isCompl_projection`).
  - Naming (finding 1): `isComplProjection` differs from the `isCompl_projection` spelling that
    three LinearAlgebra/Projection.lean lemmas use for the same definition. The rename back to
    `isCompl_projection` compiles (lean_verify_edit, success).
  - Prefix: naming_norm calls `toLinearMap_` *emerging* (21 vs 7), because the statement spells out
    `.toLinearMap`, and the PR author uses `toLinearMap_` names in PR #32927. But the paired lemma
    `coe_orthogonalProjection_...` and the local `..._eq_coe_starProjection` both use `coe_`, and the
    verdict is advisory at most, so I did not request it.
  - `open Submodule in` before the theorem looked redundant inside `namespace Submodule`. It is not:
    lean_verify_edit without it fails with "Invalid field `projection`: The environment does not
    contain `IsCompl.projection`", because the def is `Submodule.IsCompl.projection`. No finding.
  - Proof: only the rewritten lemma reference changes. A golf would be out of scope for a
    rename PR, and nothing clearly shorter is available, because `orthogonalProjection` and
    `linearProjOfIsCompl` are not definitionally equal. No finding.
- The deprecated aliases (three new, two retargeted) cover every old name. content_search over
  target/ finds no remaining use of the old names outside the aliases, so no deprecation warnings
  appear elsewhere. No finding.
- `LinearMap.IsSymmetricProjection.le_iff_range_le_range` and
  `Submodule.starProjection_le_starProjection_iff` (Positive.lean): only the lemma name inside the
  `simpa`/`simp_rw` lists changes. The file compiles as the PR leaves it (as-is check). No finding.
- Documentation: none of the three renamed theorems has a docstring, before or after the PR. The
  PR changes no statement, so I made no documentation request.
- Scope and correctness: the PR does only the renames, deprecations and call-site updates it
  describes, and nothing looks out of place.

Findings written: 1.

Process note: early on, while working out the workspace path prefix (`target/`), I ran one `cat` on
the ptool wrapper's own stderr log directory for this reviewer (`.ape/probe_scratch/.../raw/pr33337/X2/*.err`),
which is outside the working directory. It printed nothing, and I read no other path outside this directory.
