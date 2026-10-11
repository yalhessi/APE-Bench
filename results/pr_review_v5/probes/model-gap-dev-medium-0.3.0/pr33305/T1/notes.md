# Review notes: PR #33305 "doc(GroupTheory): fix file refs"

This PR changes only documentation: seven module docstrings, each with one file-path reference
updated. There are no declarations, so the proof-golf, generalization, duplication and naming
checks have nothing to apply to. For each changed path I checked that the new target exists and
holds what the prose says it holds. I also checked the edited lines against the 100-character
limit, and compiled each file as the PR leaves it (`lean_verify_edit` with no edit) to see the
linter output.

## Object by object

- **Abelianization/Defs.lean**: `GrpCat/Adjunctions` became `Grp/Adjunctions`.
  `Mathlib/Algebra/Category/Grp/Adjunctions.lean` exists and contains `GrpCat.abelianize` and
  `abelianizeAdj`. The line is 78 characters. The file compiles with no warnings. No finding.
- **FreeAbelianGroup.lean**: the same path change. The Adjunctions file defines
  `AddCommGrpCat.free` from `FreeAbelianGroup` with its adjunction. Compiles cleanly. No finding.
- **FreeGroup/Basic.lean**: the same path change. The Adjunctions file defines `GrpCat.free` from
  `FreeGroup` with its adjunction. Its other path reference,
  `Mathlib/GroupTheory/FreeGroup/GeneratorEquiv.lean` (line 789), exists. Compiles cleanly.
  No finding.
- **GroupAction/DomAct/ActionHom.lean**: the new path `Mathlib/Algebra/Group/Action/Hom.lean`
  is the wrong file. It holds `MulAction.compHom` and similar, and has no `→[N]` or
  `MulActionHom`. `MulActionHom` is declared in `Mathlib/GroupTheory/GroupAction/Hom.lean`,
  which this file imports. That is finding 2 (blocking). I also found that the left actions the
  TODO asks for already exist in that file: `SMul R (X →ₑ[σ] Y)` and `MulAction R ...` at
  lines 427-467, and `inferInstance` finds `MulAction M (α →[N] β)`. The `SMulCommClass Mᵈᵐᵃ R`
  instance is still missing, so the TODO should be reworded to that remaining part: finding 4
  (advisory). Both proposed edits compile with no warnings.
- **GroupExtension/Defs.lean**: the new text names the planned
  `Mathlib/GroupTheory/GroupExtension/Abelian.lean`, which does not exist yet; the prose says
  "planned", so that is accurate. The line is 99 characters. The neighbouring bullet still
  points at `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`, which is now a
  `deprecated_module` shim (since 2025-06-14); the TODO lives in
  `.../Homological/GroupCohomology/LowDegree.lean`. Searching all of Mathlib shows this is the
  only remaining reference to that path: finding 3 (advisory, in the paragraph the PR already
  edits). `Mathlib/GroupTheory/GroupExtension/Basic.lean`, referenced twice further down, exists.
  The rewrapped edit compiles cleanly.
- **Perm/Sign.lean**: `Perm/Fintype.lean` became `Perm/Finite.lean`. `Perm/Finite.lean` exists
  ("Permutations on `Fintype`s", miscellaneous `Equiv.Perm` lemmas), so it is the renamed
  file. No `Perm/Fintype` reference remains anywhere in Mathlib. The line has no final period,
  but that predates the PR, so I am not asking for it. Compiles cleanly. No finding.
- **Submonoid/Inverses.lean**: the new path `Mathlib/Algebra/Group/Submonoid/Units.lean` is
  correct; that file has the units-of-submonoid table and mentions `S.leftInv`. The edited line
  is now 101 characters, and the `longLine` linter warns on it in the as-is compile: finding 1
  (blocking). The rewrapped paragraph compiles with no warnings. (That file's section is titled
  "Implementation details", not "implementation notes"; too minor to request.)
  `Mathlib/Algebra/Group/Submonoid/Pointwise.lean` (line 20) exists.

## Completeness of the sweep

Searching all 7445 Mathlib files finds no remaining reference to `GrpCat/Adjunctions`,
`Algebra/Hom/GroupAction`, `Perm/Fintype` or `GroupTheory/Submonoid/Units`. So the PR covers
every occurrence of the paths it targets; the one stale path left is the LowDegree reference.

## Tools used

`file_search`, `file_read`, `content_search`, `declaration_search` (MulActionHom), and
`lean_verify_edit`: as-is compiles of all 7 files, plus verified edits for findings 1-4 and an
instance probe for finding 4.
