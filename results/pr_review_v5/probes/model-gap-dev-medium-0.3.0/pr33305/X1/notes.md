# Review notes: PR #33305, doc(GroupTheory): fix file refs

The PR changes seven module docs, each only in its file-path references. For every reference
the PR introduces, and every other `Mathlib/...lean` reference in the changed files, I checked
three things:
- does the file exist in the reviewed workspace? (`file_read` of `target/<path>`)
- is it a `deprecated_module` shim?
- does it contain what the sentence says it does?

I also measured the length of every added line in characters and tested it under
`linter.style.longLine`. The tool's plain compile does not enable Mathlib's own linters, so I
turned the linter on with a `set_option` line inserted before the module doc. That line was only
a probe and is not part of any request.

Workspace note: `file_search` returns nothing under `target/`, probably because it does not
follow the symlink. `file_read` and `content_search` on `target/...` work, so I used those.

## Object by object

### `Mathlib/GroupTheory/Abelianization/Defs.lean` (module doc)
- `GrpCat/Adjunctions.lean` becomes `Grp/Adjunctions.lean`. The new file exists and the old one
  does not.
- The new file contains `GrpCat.abelianize` and `abelianizeAdj`, the left adjoint to the
  forgetful functor from abelian groups to groups. The sentence is correct.
- Line length is 78. No finding.

### `Mathlib/GroupTheory/FreeAbelianGroup.lean` (module doc)
- Same path change. `Grp/Adjunctions.lean` contains `AddCommGrpCat.free` and
  `AddCommGrpCat.adj`, the free/forgetful adjunction for abelian groups, which is the statement
  the doc refers to.
- No finding.

### `Mathlib/GroupTheory/FreeGroup/Basic.lean` (module doc)
- Same path change. The file contains `GrpCat.free` and `GrpCat.adj`. Correct.
- The file's other reference, `Mathlib/GroupTheory/FreeGroup/GeneratorEquiv.lean` at line 789,
  exists.
- No finding.

### `Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean` (module doc): 2 findings
- The new path `Mathlib/Algebra/Group/Action/Hom.lean` exists, but it is the wrong file.
  - It covers `MulAction.compHom` and similar, and never mentions `MulActionHom` or `→[`.
  - `α →[N] β` is `MulActionHom`, declared in `Mathlib/GroupTheory/GroupAction/Hom.lean`, which
    is what this file imports.
  - The old `Mathlib/Algebra/Hom/GroupAction.lean` is the Mathlib 3 port name of that file.
  - **Finding 1 (blocking):** point the reference at `Mathlib/GroupTheory/GroupAction/Hom.lean`.
    Verified to compile, with no long-line warning.
- `Mathlib/GroupTheory/GroupAction/Hom.lean` already has the left actions `SMul R (X →ₑ[σ] Y)`
  and `MulAction R (X →ₑ[σ] Y)`. There is no left action on `A →+[N] B`, and no
  `SMulCommClass` between a left action and `Mᵈᵐᵃ`.
  - **Finding 4 (advisory):** reword the TODO to what is still open. Verified.

### `Mathlib/GroupTheory/GroupExtension/Defs.lean` (module doc): 1 finding
- The PR's change is fine.
  - It makes the not-yet-existing `Abelian.lean` path fully qualified and marks it as planned.
    The file indeed does not exist.
  - The new line is 99 characters, within the limit.
- The next bullet in the same TODO cites
  `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`.
  - That file is a `deprecated_module (since := "2025-06-14")` shim.
  - The cited TODO ("The relationship between `H2` and group extensions") is in
    `Mathlib/RepresentationTheory/Homological/GroupCohomology/LowDegree.lean`.
  - This is the only remaining reference to the deprecated path in Mathlib.
  - **Finding 3 (advisory):** update it, wrapped over two lines (a single line would be 112
    characters). Verified under the linter.
- The other references in the file (`Mathlib/GroupTheory/GroupExtension/Basic.lean` at lines 93
  and 153) exist.

### `Mathlib/GroupTheory/Perm/Sign.lean` (module doc)
- `Perm/Fintype.lean` becomes `Perm/Finite.lean`. The new file exists and the old one does not.
- `Finite.lean`'s header ("Permutations on `Fintype`s: miscellaneous lemmas about `Equiv.Perm`
  and `Equiv.swap`") matches the old `perm/fintype` file, and it holds lemmas such as
  `isConj_of_support_equiv`. So this rename is the right target.
- The sentence has no trailing period. That is too minor to ask for.
- No finding.

### `Mathlib/GroupTheory/Submonoid/Inverses.lean` (module doc): 1 finding
- `Mathlib/Algebra/Group/Submonoid/Units.lean` exists, and it has the implementation section
  with the table of related constructions. The old `GroupTheory/Submonoid/Units.lean` does not
  exist.
- The edited line is 101 characters.
  - `linter.style.longLine` fires on it (tool output quoted in the finding).
  - **Finding 2 (blocking):** rewrap the line. Verified: no warning after the rewrap.
- The file calls the section "implementation notes" while `Units.lean` titles it "Implementation
  details". Too minor to request.
- The unchanged `Mathlib/Algebra/Group/Submonoid/Pointwise.lean` reference exists.

## Wider checks
- I collected every backticked `Mathlib/...lean` reference in `Mathlib/GroupTheory` (17 unique
  paths) and checked each one:
  - all exist, except the planned `GroupExtension/Abelian.lean`;
  - one is deprecated: the LowDegree path of finding 3.
- No other copies of the old spellings (`GrpCat/Adjunctions`, `Algebra/Hom/GroupAction`,
  `Perm/Fintype.lean`, `GroupTheory/Submonoid/Units`) remain in Mathlib, so the PR is complete
  for the stale paths it chose.
- Zulip ("Broken file references", 2024-11): maintainers want module docs to use full path
  spelling. The PR follows that, including the `Abelian.lean` qualification.
- The proof-golf, generalization, duplication and naming checks do not apply: no declarations
  change.
