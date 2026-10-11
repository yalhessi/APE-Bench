import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33315/T1"
findings = [
  {
    "target": "module_doc in Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean",
    "claim": "The rewritten implementation note still presents generalizing `Finset.Nat.antidiagonalTuple` to finitely supported functions as future work (\"In the future, we could consider generalizing ... as in `Finset.finsuppAntidiag`\"), but that generalization already exists: `Finset.finsuppAntidiag` is the finsupp-valued construction the old `cut` reference stood for, and `Finset.finAntidiagonal` / `Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean` already generalize `antidiagonalTuple`, with `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple` relating them. The note now reads as an open TODO that has been done.",
    "requested_change": "Replace the \"In the future, we could consider generalizing ...\" paragraph with a statement that the generalizations exist, e.g. \"`Finset.Nat.antidiagonalTuple` has since been generalized: `Finset.finAntidiagonal` and `Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean` work over any commutative monoid with antidiagonals (see `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple`), and `Finset.finsuppAntidiag` in `Mathlib/Algebra/Order/Antidiag/Finsupp.lean` is the version for finitely supported functions.\" Alternatively, drop the paragraph and leave the deduplication TODO in Pi.lean.",
    "severity": "advisory",
    "evidence": "declaration_search: `Finset.finsuppAntidiag` declared at Mathlib/Algebra/Order/Antidiag/Finsupp.lean:45 before this PR; `Finset.finAntidiagonal` at Mathlib/Algebra/Order/Antidiag/Pi.lean:65; `Finset.piAntidiag_univ_fin_eq_antidiagonalTuple` (piAntidiag univ n = Nat.antidiagonalTuple k n) at Pi.lean:211. Pi.lean's module doc already says under ## TODO: \"`Finset.finAntidiagonal` is strictly more general than `Finset.Nat.antidiagonalTuple`. Deduplicate.\" and under ## See also points to `Finset.finsuppAntidiag`. content_search for `antidiagonalTuple` across Mathlib finds only these two files. lean_verify_edit replacing NatAntidiagonal.lean lines 39-41 with the suggested paragraph (all lines <= 100 chars): outcome compiled, no errors, no warnings."
  },
  {
    "target": "module_doc in Mathlib/Data/Finset/Defs.lean",
    "claim": "The pointer for \"More information\" on big operators was moved to `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`, which only proves lemmas (its module doc is one line: \"In this file we prove theorems about products and sums indexed by a `Finset`\"). The content the old `Group/Finset.lean` reference pointed to, the definitions `Finset.prod`/`Finset.sum` and the full documentation of the `∑ i ∈ s, f i` / `∏ i ∈ s, f i` notation, now lives in `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean`.",
    "requested_change": "Point the reference at the definitions file: \"More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean`.\"",
    "severity": "advisory",
    "evidence": "file_read of Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean: module doc \"# Big operators / In this file we define products and sums indexed by finite sets\" with a ## Notation section listing `∏ x ∈ s, f x`, `∑ x ∈ s, f x`, filter and product binders. declaration_search: `Finset.prod` declared at Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean:67. file_read of .../Finset/Basic.lean: module doc only \"In this file we prove theorems about products and sums indexed by a `Finset`.\" The old path Mathlib/Algebra/BigOperators/Group/Finset.lean no longer exists. lean_verify_edit replacing Finset/Defs.lean line 34 with the suggested line: outcome compiled, no errors, no warnings."
  },
  {
    "target": "module_doc in Mathlib/Data/Finsupp/MonomialOrder.lean",
    "claim": "The sentence the PR edits, \"For the graded lexicographic ordering, see `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean`\", has no closing period and runs straight into the following bullet list, and it names only a file path, the kind of reference this PR shows goes stale, rather than the declaration it is about.",
    "requested_change": "End the sentence with a period and name the declaration alongside the path: \"For the graded lexicographic ordering `MonomialOrder.degLex`, see\\n`Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean`.\"",
    "severity": "advisory",
    "evidence": "file_read of MonomialOrder.lean lines 35-39 shows line 37 without a terminal period followed by a blank line and the `* MonomialOrder.lex` bullet. declaration_search: `MonomialOrder.degLex` declared at Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean:201 before this PR. lean_verify_edit replacing line 37 with the two-line suggestion: outcome compiled, no errors, no warnings."
  }
]
with open(f"{D}/findings.json", "w") as f:
    json.dump(findings, f, indent=2, ensure_ascii=False)
    f.write("\n")
json.load(open(f"{D}/findings.json"))
print(len(findings))
