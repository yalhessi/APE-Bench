# PR #33305 review notes (doc(GroupTheory): fix file refs)

The PR has seven module-doc edits and no declaration changes. For each one I checked that the new
path exists, that it is the right file for the sentence it sits in, and that the edited lines fit
the 100-column limit. The `ptool file_search` directory listing returned nothing under `target/`,
so I confirmed files exist with `file_read` on `target/<path>` and with `declaration_search`.

## Abelianization/Defs.lean -- no finding
`GrpCat/Adjunctions.lean` -> `Grp/Adjunctions.lean`. `declaration_search` confirms
`GrpCat.abelianizeAdj` is in `Mathlib/Algebra/Category/Grp/Adjunctions.lean`, and the old `GrpCat/`
path does not exist. Line is 78 chars.

## FreeAbelianGroup.lean -- no finding
Same path fix. That file declares `AddCommGrpCat.free` and `AddCommGrpCat.adj`, which is the
adjunction statement the doc refers to. The rest of the module doc has a stale claim: the Finsupp
API is said to be "in the lean-liquid repo", but `Mathlib/Algebra/FreeAbelianGroup/Finsupp.lean`
exists. It is not a file reference and not part of this PR, so I did not raise it.

## FreeGroup/Basic.lean -- no finding
Same path fix; `GrpCat.free` and `GrpCat.adj` are in that file. The file's other reference,
`Mathlib/GroupTheory/FreeGroup/GeneratorEquiv.lean` (l.789), exists.

## GroupAction/DomAct/ActionHom.lean -- finding 1 (blocking)
The new target `Mathlib/Algebra/Group/Action/Hom.lean` is the wrong file. It has no
`MulActionHom`, `→[` or `→ₑ`. `α →[N] β` is defined in `Mathlib/GroupTheory/GroupAction/Hom.lean`,
which this file imports. That file already has the left actions `SMul R (X →ₑ[σ] Y)` and
`MulAction R (X →ₑ[σ] Y)`, so only the `SMulCommClass` part of the TODO is still open. I checked
that the corrected, reworded TODO compiles with the longLine linter on.

## GroupExtension/Defs.lean -- finding 3 (advisory)
The edited `Abelian.lean` bullet is correct as a planned file (it does not exist yet). It is 99
chars, within the limit. "the planned file ... to be added in a later PR" is slightly redundant,
but I would not ask for that. The next line, which the PR leaves alone, still cites
`Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`. That is now a
`deprecated_module (since := "2025-06-14")` stub; the real file is under `Homological/`. A search of
GroupTheory for the stale patterns found only this one. The rewrapped fix compiles clean with the
longLine linter on.

## Perm/Sign.lean -- no finding
`Perm/Fintype.lean` -> `Perm/Finite.lean`. The new file exists ("Permutations on `Fintype`s",
miscellaneous `Equiv.Perm` lemmas) and the old one does not. The line has no trailing period, which
is too minor to ask for.

## Submonoid/Inverses.lean -- finding 2 (blocking)
The path `Mathlib/Algebra/Group/Submonoid/Units.lean` is correct (the old `GroupTheory/Submonoid/`
path does not exist). But the edited line is 101 chars. A `lean_verify_edit` probe with
`set_option linter.style.longLine true` confirms the linter warns, and the rewrapped version is
clean. The target file's section is titled "Implementation details" rather than "notes", which is
too minor to raise. The Pointwise reference exists.

## Tools used
file_read, content_search, declaration_search, lean_verify_edit (1 as-is compile, 4 edit probes),
precedent_search and zulip_search (nothing directly applicable).
