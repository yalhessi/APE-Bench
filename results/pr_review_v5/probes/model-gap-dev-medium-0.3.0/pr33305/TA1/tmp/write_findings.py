import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33305/TA1/"
F = [
 {
  "target": "module_doc in Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean",
  "claim": "The TODO's new reference `Mathlib/Algebra/Group/Action/Hom.lean` points to the wrong file. That file (\"Homomorphisms and group actions\": `Function.Surjective.mulActionLeft`, `MulAction.compHom`, ...) does not define `α →[N] β` or `A →+[N] B`. Both are defined in `Mathlib/GroupTheory/GroupAction/Hom.lean`, which is where the stale `Mathlib/Algebra/Hom/GroupAction.lean` was moved to and which this very file imports. So the fix swaps one wrong reference for another.",
  "requested_change": "Replace `Mathlib/Algebra/Group/Action/Hom.lean` with `Mathlib/GroupTheory/GroupAction/Hom.lean` on line 19: `Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/GroupTheory/GroupAction/Hom.lean` and` (94 characters).",
  "severity": "blocking",
  "evidence": "file_read target/Mathlib/Algebra/Group/Action/Hom.lean lines 1-60: module doc is '# Homomorphisms and group actions', with contents `Function.Surjective.mulActionLeft` and `MulAction.compHom`, and no MulActionHom. content_search for the notation `\" →[\" M:25 \"] \"` finds it only at target/Mathlib/GroupTheory/GroupAction/Hom.lean:96 (MulActionHom) and :108 (AddActionHom). That file's module doc lists `MulActionHom`, `DistribMulActionHom` and the notations `X →[M] Y` and `A →+[M] B`. ActionHom.lean line 9 is `public import Mathlib.GroupTheory.GroupAction.Hom`. lean_verify_edit (line mode, lines 19-20, with the corrected path): outcome compiled, no errors, no warnings."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/GroupExtension/Defs.lean",
  "claim": "The PR leaves one stale file reference in the hunk it edits. Line 52 still cites `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`, which is now only a `deprecated_module (since := \"2025-06-14\")` stub re-exporting `Mathlib.RepresentationTheory.Homological.GroupCohomology.LowDegree`. The TODO this line refers to (\"The relationship between `H2` and group extensions\") lives in the Homological file.",
  "requested_change": "Point the reference at the live file and break the now over-long line between fragments:\n```\n- there is a bijection between equivalence classes of group extensions and `groupCohomology.H2`\n  (which is also stated as a TODO in\n  `Mathlib/RepresentationTheory/Homological/GroupCohomology/LowDegree.lean`).\n```",
  "severity": "advisory",
  "evidence": "file_read target/Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean: the whole file is `public import Mathlib.RepresentationTheory.Homological.GroupCohomology.LowDegree` plus `deprecated_module (since := \"2025-06-14\")`. In target/Mathlib/RepresentationTheory/Homological/GroupCohomology/LowDegree.lean, line 50 under `## TODO` reads '* The relationship between `H2` and group extensions'. A content_search over all of target/Mathlib/GroupTheory for paths of the stale kinds returns only this line; every other `Mathlib/....lean` path cited in GroupTheory docs exists. lean_verify_edit (line mode, lines 51-52, with the replacement above): compiled, no errors, no warnings. Line lengths are 95, 36 and 77."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/Submonoid/Inverses.lean",
  "claim": "The changed line 23 is 101 characters long. It goes over Mathlib's 100-character limit, and the `linter.style.longLine` linter warns on it, which fails the lint step in CI.",
  "requested_change": "Reflow the paragraph so that `details` moves to the next line:\n```\n`N.leftInv` is distinct from `N.units`, which is the subgroup of `Mˣ` containing all units that are\nin `N`. See the implementation notes of `Mathlib/Algebra/Group/Submonoid/Units.lean` for more\ndetails on related constructions.\n```",
  "severity": "blocking",
  "evidence": "Measured the added lines in diff.patch: this one is 101 characters. lean_verify_edit on Mathlib/GroupTheory/Submonoid/Inverses.lean with no edit args (as the PR leaves it): compiled, with warning 'This line exceeds the 100 character limit, please shorten it!' at line 23, code_line 'in `N`. See the implementation notes of `Mathlib/Algebra/Group/Submonoid/Units.lean` for more details'. lean_verify_edit (line mode, lines 22-24, with the reflow above): compiled, no errors, no warnings."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean",
  "claim": "The TODO whose reference this PR rewrites is partly done. Left actions on `α →[N] β` (for any `R` acting on the codomain with `[SMulCommClass N R Y]`) already exist in `Mathlib/GroupTheory/GroupAction/Hom.lean`: `SMul R (X →ₑ[σ] Y)`, `MulAction R (X →ₑ[σ] Y)`, `DistribMulAction` and `Module`. Only the `SMulCommClass` instances relating them to the `Mᵈᵐᵃ` action defined here are still missing. So the comment no longer matches the code.",
  "requested_change": "Reword the TODO to what remains. For example:\n```\nThe left actions of, e.g., `M` on `α →[N] β` are in `Mathlib/GroupTheory/GroupAction/Hom.lean`. Add\n`SMulCommClass` instances saying that they commute with the right actions defined here.\n```",
  "severity": "advisory",
  "evidence": "file_read target/Mathlib/GroupTheory/GroupAction/Hom.lean lines 405-470: line 427 is `instance [SMul M X] [SMul N Y] [SMul R Y] [SMulCommClass N R Y] : SMul R (X →ₑ[σ] Y)`, line 464 is `MulAction R (X →ₑ[σ] Y)`, and lines 469-482 are DistribSMul, DistribMulAction and Module. ActionHom.lean (lines 25-87) holds only the `Mᵈᵐᵃ` actions and `SMulCommClass Mᵈᵐᵃ M'ᵈᵐᵃ` instances, with no instance relating them to a left action. lean_verify_edit (line mode, lines 19-20, with the text above): compiled, no errors, no warnings. Line lengths are 99 and 87. Precedent: eric-wieser on PR #22132 asked, of a stale-path TODO edit, to 'work out what the updated version of this comment is rather than making it more confusing'."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/Perm/Sign.lean",
  "claim": "The sentence this PR edits, 'Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`', has no final period. Docstrings are written in full sentences ending in a period.",
  "requested_change": "Add the period: `Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`.`",
  "severity": "advisory",
  "evidence": "file_read target/Mathlib/GroupTheory/Perm/Sign.lean line 28: 'Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`' with no trailing period. lean_verify_edit (line mode, lines 28-30, replaced by the line with the period and `-/` directly after): compiled, no errors, no warnings."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/Perm/Sign.lean",
  "claim": "In the hunk this PR edits, the module docstring's closing `-/` comes after a blank line (line 29). It should follow the last line of text directly.",
  "requested_change": "Delete the blank line 29, so that `-/` comes directly after the line `Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`.`",
  "severity": "advisory",
  "evidence": "diff.patch hunk @@ -25,7 +25,7 @@ shows the changed line followed by a blank context line and then `-/`. The same lean_verify_edit as for the period finding (lines 28-30 replaced, with no blank line before `-/`): compiled, no errors, no warnings."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/Submonoid/Inverses.lean",
  "claim": "The PR is about stale documentation references, and the module docstring it edits still names a non-existent declaration on line 16: `IsUnit.Submonoid M`. The declaration is `IsUnit.submonoid`, so the reference neither renders as a link nor points anywhere.",
  "requested_change": "On line 16, replace `IsUnit.Submonoid M` with `IsUnit.submonoid M`.",
  "severity": "advisory",
  "evidence": "declaration_search 'IsUnit.Submonoid': 0 hits, before the PR or in it. declaration_search 'IsUnit.submonoid': declared in Mathlib/Algebra/Group/Submonoid/Basic.lean:359. The Inverses.lean code itself uses `IsUnit.submonoid M` (line 41: `noncomputable instance [Monoid M] : Group (IsUnit.submonoid M)`)."
 },
 {
  "target": "module_doc in Mathlib/GroupTheory/GroupExtension/Defs.lean",
  "claim": "The rewritten TODO line adds the words 'the planned file', which repeat 'to be added in a later PR'. That is a stylistic rewording of the original author's prose beyond the reference fix, which only needed the `Mathlib/` prefix.",
  "requested_change": "Drop 'the planned file' and keep only the path fix:\n```\n  (which will be available in `Mathlib/GroupTheory/GroupExtension/Abelian.lean`, to be added in a\n  later PR).\n```",
  "severity": "advisory",
  "evidence": "diff.patch: the old line was '(which will be available in `GroupTheory/GroupExtension/Abelian.lean` to be added in a later PR).' and the new one is '(which will be available in the planned file `Mathlib/GroupTheory/GroupExtension/Abelian.lean` to' / 'be added in a later PR).'. file_search shows only Basic.lean and Defs.lean in GroupTheory/GroupExtension, so 'to be added in a later PR' alone already says the file does not exist yet. lean_verify_edit (line mode, lines 49-50, with the text above): compiled, no errors, no warnings. The first line is 97 characters."
 }
]
json.dump(F, open(D + "findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
