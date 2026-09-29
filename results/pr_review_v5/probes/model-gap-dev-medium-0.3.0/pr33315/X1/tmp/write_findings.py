import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33315/X1"
findings = [
 {
  "target": "module_doc in Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean",
  "claim": "The rewritten implementation note still says that \"in the future, we could consider generalizing `Finset.Nat.antidiagonalTuple` further to support finitely-supported functions, as in `Finset.finsuppAntidiag`\". That generalization already exists. `Finset.finAntidiagonal` and `Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean` generalize `antidiagonalTuple`, `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple` states that they agree, and `Finset.finsuppAntidiag` is the finsupp-valued version. Swapping the dead archive reference for `finsuppAntidiag` leaves a stale TODO pointing at code that already does the thing.",
  "requested_change": "Replace lines 39-41 with a statement of the existing generalizations and move the remaining work to a TODO section, e.g.: \"`Finset.Nat.antidiagonalTuple` is generalized by `Finset.finAntidiagonal` and `Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean` (see `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple`), and to finitely-supported functions by `Finset.finsuppAntidiag` in `Mathlib/Algebra/Order/Antidiag/Finsupp.lean`.\" followed by \"## TODO\\n\\nDeduplicate `Finset.Nat.antidiagonalTuple` with `Finset.finAntidiagonal`.\"",
  "severity": "advisory",
  "evidence": "declaration_search: `Finset.finsuppAntidiag`, `Finset.piAntidiag`, `Finset.finAntidiagonal` and `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple` are all declared in the base tree (Mathlib/Algebra/Order/Antidiag/{Pi,Finsupp}.lean). file_read of Antidiag/Pi.lean: line 37 reads \"`Finset.finAntidiagonal` is strictly more general than `Finset.Nat.antidiagonalTuple`. Deduplicate.\", line 64 reads \"TODO: deduplicate with the less general `Finset.Nat.antidiagonalTuple`\", and lines 211-213 prove `piAntidiag univ n = Nat.antidiagonalTuple k n`. lean_verify_edit (line mode, lines 39-41 of Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean replaced with the proposed text) returned success, no errors and no warnings."
 },
 {
  "target": "module_doc in Mathlib/Data/Finset/Defs.lean",
  "claim": "The same paragraph the PR edits keeps a stale file reference. It says a `Fintype α` instance consists of a universal finset `univ` and points to `Mathlib/Data/Fintype/Basic.lean`, but `class Fintype` and `Finset.univ` are now defined in `Mathlib/Data/Fintype/Defs.lean`. `Fintype/Basic.lean` describes itself as \"a collection of basic `Fintype` instances for types such as `Fin`, `Prod` and pi types\".",
  "requested_change": "On line 38, change \"See `Mathlib/Data/Fintype/Basic.lean`.\" to \"See `Mathlib/Data/Fintype/Defs.lean`.\"",
  "severity": "advisory",
  "evidence": "content_search for `^class Fintype` over target/Mathlib/Data: only hit is Mathlib/Data/Fintype/Defs.lean:56. declaration_search `Finset.univ` lists Mathlib/Data/Fintype/Defs.lean. file_read of Mathlib/Data/Fintype/Basic.lean lines 16-20: module doc is \"# Instances for finite types / This file is a collection of basic `Fintype` instances ...\". lean_verify_edit on Mathlib/Data/Finset/Defs.lean (lines 34-55 replaced, including this change) returned success with no errors."
 },
 {
  "target": "module_doc in Mathlib/Data/Finset/Defs.lean",
  "claim": "The replacement for the deleted `Mathlib/Algebra/BigOperators/Group/Finset.lean` points to `.../Finset/Basic.lean`, whose module doc is only \"In this file we prove theorems about products and sums indexed by a `Finset`\". The sentence introduces what `∑ i ∈ s, f i` and `∏ i ∈ s, f i` are. Those operators are defined in `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean`, and that file's module doc documents the notation.",
  "requested_change": "On line 34, point to `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean` instead of `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`.",
  "severity": "advisory",
  "evidence": "file_read of Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean lines 14-43: \"In this file we define products and sums indexed by finite sets\" plus a full `## Notation` section for ∏/∑ binders. file_read of .../Finset/Basic.lean lines 12-16: \"In this file we prove theorems about products and sums indexed by a `Finset`.\" The directory has both files, plus Lemmas, Pi, Sigma and others. lean_verify_edit on Mathlib/Data/Finset/Defs.lean with this change returned success."
 },
 {
  "target": "module_doc in Mathlib/Data/Finset/Defs.lean",
  "claim": "The `## Main definitions` list of the module doc this PR edits for stale references still names two declarations that do not exist. `Finset.instMembershipFinset` is actually `Finset.instMembership`. `Finset.instCoeSortFinsetType` no longer exists, because the coercion of a finset to a type now comes through the `SetLike` instance.",
  "requested_change": "Rename `Finset.instMembershipFinset` to `Finset.instMembership` in the list. Delete the `Finset.instCoeSortFinsetType` bullet and fold it into the `Finset.instSetLike` bullet, e.g. \"* `Finset.instSetLike`: Provides a coercion `s : Finset α` to `s : Set α`, and through `SetLike` a coercion of `s : Finset α` to the type of all `x ∈ s`.\"",
  "severity": "advisory",
  "evidence": "lean_verify_edit (line splice after line 104 of Mathlib/Data/Finset/Defs.lean): `example {β : Type*} : Membership β (Finset β) := Finset.instMembership` compiled, and `example := @Finset.instMembershipFinset` failed with \"Unknown constant `Finset.instMembershipFinset`\". A second splice after the SetLike instance (line 130): `example := @Finset.instSetLike` and `example {β : Type*} (s : Finset β) : Type _ := s` compiled, and `example := @Finset.instCoeSortFinsetType` failed with \"Unknown constant `Finset.instCoeSortFinsetType`\". content_search for CoeSort in target/Mathlib/Data/Finset found only the doc line 55, so there is no CoeSort instance declaration. lean_verify_edit with the proposed doc text returned success."
 }
]
with open(f"{D}/findings.json", "w") as fh:
    json.dump(findings, fh, indent=1, ensure_ascii=False)
print(len(json.load(open(f"{D}/findings.json"))))
