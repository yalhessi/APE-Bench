# Review notes: PR #33305, doc(GroupTheory): fix file refs

The PR changes documentation only: seven module docstrings, one stale file path each. I read
`pr.md`, `model.md` and `diff.patch`, then used `ptool` to check three things: that each new path
exists, that it is the right file for the sentence, and whether the edited docstrings carry other
stale references. I compiled all seven files as the PR leaves them (`lean_verify_edit` with no edit
arguments). Only `Submonoid/Inverses.lean` warns: longLine at line 23. I compiled every edit I
propose (line mode), and each one came back `compiled` with no warnings.

## Object by object

- **Abelianization/Defs.lean module doc.** `Mathlib/Algebra/Category/Grp/Adjunctions.lean` exists.
  Its module doc lists `abelianizeAdj` ("`GrpCat.abelianize` is left adjoint to the forgetful
  functor from abelian groups to groups"), so the reference is correct. The changed line is 78
  characters. No finding.
- **FreeAbelianGroup.lean module doc.** Same target file. It contains `AddCommGrpCat.free` and
  `AddCommGrpCat.adj`, the free-forgetful adjunction for abelian groups, so the reference is correct.
  No finding.
- **FreeGroup/Basic.lean module doc.** Same target file. It contains `GrpCat.free` and `GrpCat.adj`,
  so the reference is correct. The file's other cited path, `Mathlib/GroupTheory/FreeGroup/GeneratorEquiv.lean`,
  exists. The declarations named in the doc (`FreeGroup.Red`, `FreeGroup.Red.trans`,
  `FreeGroup.Red.church_rosser`, `FreeGroup.freeGroupUnitEquivInt`) all exist. No finding.
- **GroupAction/DomAct/ActionHom.lean module doc.** **Wrong target (blocking).**
  - `Mathlib/Algebra/Group/Action/Hom.lean` is "Homomorphisms and group actions" (`compHom` and
    friends). The notation `α →[N] β` and `A →+[N] B` is defined in
    `Mathlib/GroupTheory/GroupAction/Hom.lean`, lines 96 and 108, and this file imports that module
    on line 9.
  - The TODO is also partly done (advisory). The left actions `SMul R (X →ₑ[σ] Y)` and
    `MulAction R (X →ₑ[σ] Y)` and the instances after them already exist (Hom.lean, lines 427-482).
    Only the `SMulCommClass` instances against `Mᵈᵐᵃ` are missing.
- **GroupExtension/Defs.lean module doc.**
  - The `Mathlib/` prefix on the planned `Abelian.lean` is right: the file's other paths use it, and
    the file does not exist yet, so the TODO still applies.
  - **Missed stale reference (advisory).** Line 52, inside the PR's own hunk, still cites
    `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`. That is a `deprecated_module`
    stub since 2025-06-14. The live file is `Mathlib/RepresentationTheory/Homological/GroupCohomology/LowDegree.lean`,
    and it holds the H2 TODO at line 50.
  - The PR's added words "the planned file" are redundant (advisory). The wrapped line is 99
    characters, under the limit.
  - The paths on lines 93 and 153 (`GroupExtension/Basic.lean`) exist.
- **Perm/Sign.lean module doc.** `Mathlib/GroupTheory/Perm/Finite.lean` exists and is
  "Permutations on `Fintype`s"; no `Perm/Fintype.lean` remains. So the target is right. The changed
  sentence lacks a period, and the docstring has a blank line before `-/`; both advisory, both
  inside the hunk.
  - I did not file the "have been moved" wording. It is a historical note but still true, and
    rewording it would be a purely stylistic change.
- **Submonoid/Inverses.lean module doc.**
  - `Mathlib/Algebra/Group/Submonoid/Units.lean` exists and has an "Implementation details" section,
    so the target is right.
  - **The changed line is 101 characters (blocking).** The longLine linter fires on it (verified),
    and the proposed reflow compiles clean.
  - Line 16 still names `IsUnit.Submonoid`, which does not exist; the declaration is
    `IsUnit.submonoid`. Advisory, in line with the PR's purpose.
  - Not filed, pre-existing and not a reference: the doc writes `leftInvEquiv : S.leftInv ≃* S`
    with `S`, while the rest of the doc uses `N`.

I also checked for stale paths outside these files. Every `Mathlib/....lean` path cited in
GroupTheory docs exists (17 checked), except the LowDegree stub above. Two `GrpCat/` paths remain,
in `Algebra/Category/Grp/{Injective,EnoughInjectives}.lean`. They are outside this PR's GroupTheory
scope, so I did not file them.

No checklist item yields a finding for proof-golf, generalization, duplication or naming: the PR
changes no declarations.

## Conventions: where filed, where left

1. **`-/` follows the last line of text.**
   - Filed: Sign.lean (blank line 29, in the hunk).
   - Left as already conforming: ActionHom.lean (line 20 text, then `-/` on 21); GroupExtension/Defs
     (line 52, then `-/` on 53); FreeGroup/Basic (`free group, ... Church-Rosser theorem`, then `-/`);
     Inverses (line 30 `implementation.`, then `-/`).
   - Left, not conforming but outside the diff hunks: Abelianization/Defs line 23 and
     FreeAbelianGroup line 65 are blank lines before `-/`. The PR does not touch those lines, and
     the conventions that a PR changes existing code only where its purpose requires, and that
     purely stylistic changes to untouched prose are left to the author, govern there.
2. **A cleanup hunk is left out when it costs more readability than it gains.** Every ref fix
   improves accuracy. The only hunk with incidental rewording is "the planned file" in
   GroupExtension, filed under convention 9.
3. **Spacing.** No doubled or trailing spaces on the added lines (lint clean in all 7 files). The
   triple spaces in FreeGroup/Basic's `w * x * x⁻¹ * v   ~>   w * v` sit inside a code fragment and
   are untouched.
4. **A deprecation names its replacement.** Not applicable: nothing is deprecated.
5. **Break a line only past 100 characters.**
   - Filed: Inverses line 23 (101 characters).
   - The GroupExtension wrap is valid: the joined line would be 99 + 27 characters, so it must break.
   - Left: the untouched FreeAbelianGroup prose wrapped near 80 characters (e.g. line 58, "But").
     That is the author's taste on lines this PR does not change.
6. **Docstring sentences end in a period.**
   - Filed: Sign.lean line 28.
   - Conforming changed lines: Abelianization line 15, FreeAbelianGroup line 25, FreeGroup line 19,
     ActionHom line 20, GroupExtension line 50, Inverses line 24 (all end in `.`).
   - Left, untouched list items without periods: Abelianization lines 21-22, FreeAbelianGroup
     lines 29/41/43, GroupExtension lines 20/22/37/39/41. Same scope reason as convention 1.
7. **One spelling of a construct per file.** GroupExtension now cites every path as `Mathlib/...`;
   the PR removed the one exception. No finding.
8. **Marginal-benefit change not made.** The PR fixes real stale references, which is not marginal.
   No finding.
9. **Comments kept in step with the code.**
   - Filed: the ActionHom TODO, partly done, and the stale LowDegree reference.
   - The GroupExtension `Abelian.lean` TODO still applies, since the file does not exist; it is
     rightly kept.
   - Also filed under this heading: "the planned file", a stylistic rewording of the original
     author's prose (the "left to the author" convention).
10. **PR title and description are precise.** "Fix some stale documentation file refs" matches the
    diff. No finding.
11. **Purely stylistic change left to the original author.** Filed: GroupExtension "the planned
    file".
12. **List continuation lines indented two spaces.** The changed GroupExtension continuation lines
    49-50 use two spaces. Left: FreeAbelianGroup line 39, untouched, indented four spaces (scope
    reason as in convention 1).
13. **A concise PR description.** Conforms (one sentence).
14. **Cross-references by file path.** Every changed reference uses a file path; there are no
    dotted module names in the changed docs (content_search). No finding.
15. **Title format `type(Area): description`.** "doc(GroupTheory): fix file refs" conforms.
16. **Backticks and full names in docs.** Filed: `IsUnit.Submonoid`, which should be
    `IsUnit.submonoid`. The other names checked with declaration_search all exist.
17. **Duplicate PR.** I cannot see other open PRs with these tools. Nothing filed.
18. **Results and TODO in the module docstring.** All TODOs here are already in module docstrings.
19. **The `TODO` marker.** Used throughout; no `XXX`.
20. **Deferred work recorded as a TODO.** The `Abelian.lean` deferral is already under `## TODO`.
21. **Code fragments not split across lines.** The GroupExtension wrap breaks between fragments, as
    do my proposed wraps. Conforms.
22. **Change existing code only where the purpose requires.** This is what limited the
    untouched-line items above. The PR itself changes only reference lines, apart from the
    "the planned file" wording (filed).
