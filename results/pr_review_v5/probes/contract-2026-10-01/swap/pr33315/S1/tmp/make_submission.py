import json
notes = """Doc-only PR updating stale file references in 11 files under Mathlib/Data. For every new path I read the target file at review time; every one exists, and every old path is gone (Data/Complex/Module, Algebra/BigOperators/Group/Finset.lean, Data/Finsupp/DegLex, Data/Finset/Colex, Data/Pi/Lex, Data/Matrix/ConjTranspose, Data/Array.lean, Data/Option.lean). No proofs, statements, names or attributes change, so proof-golf, generalization, duplication and naming do not apply to any target. I also checked the files for other stale references, which is the PR's stated scope.

- module_doc in Mathlib/Data/Array/Defs.lean: the heading `##` -> `#` is right, since a module doc needs a top-level title. Dropping the dead pointer to `Mathlib/Data/Array.lean` is right too: nothing in Mathlib proves anything about `Array.cyclicPermute!` or `Array.permute!` (their only other use is in Tactic/Translate/Core.lean), and `Data/Array/Extract.lean` is about `extract`, so there is nowhere to point. Nothing to ask.
- command in Mathlib/Data/Complex/Basic.lean (docstring of `Complex.SMul.instSMulRealComplex`): the new path `Mathlib/LinearAlgebra/Complex/Module.lean` exists and has `open scoped SMul`, so it does use the scoped instance. The docstring is now correct. But the same move is still cited, in the old form, by the comment at lines 281-283 (`Data.Complex.Module`). That gets a finding.
- module_doc in Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean: `Finset.finsuppAntidiag` is defined in `Mathlib/Algebra/Order/Antidiag/Finsupp.lean`, so the reference resolves. But the new sentence still calls the generalization something to do 'in the future', when `Finset.piAntidiag`/`Finset.finAntidiagonal` (Antidiag/Pi.lean, whose own TODO says `finAntidiagonal` is strictly more general than `Finset.Nat.antidiagonalTuple`) and `Finset.finsuppAntidiag` already provide it. That gets a finding. Separately, the implementation note above it names `Fintype.PiFinset`, which does not exist (the name is `Fintype.piFinset`, in Data/Fintype/Pi.lean). That gets a finding.
- module_doc in Mathlib/Data/Finset/Defs.lean: the new big-operators path exists, but it is the lemma file ('we prove theorems about products and sums'). `Finset.prod`/`Finset.sum` and the `∑ x ∈ s, f x` notation are defined and documented in `.../Group/Finset/Defs.lean`. That gets a finding. In the same block, `class Fintype` and `Finset.univ` are in `Mathlib/Data/Fintype/Defs.lean`, while the cited `Data/Fintype/Basic.lean` is now 'Instances for finite types'. That gets a finding. `Finset.card` in Data/Finset/Card.lean is correct. The Main definitions list names `Finset.instMembershipFinset` and `Finset.instCoeSortFinsetType`, and neither is declared anywhere. A compile check confirmed `Finset.instMembership` and `Finset.instSetLike` elaborate and that `CoeSort (Finset α) _` resolves to `SetLike.instCoeSortType`. That gets a finding.
- module_doc in Mathlib/Data/Finsupp/MonomialOrder.lean: `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean` exists. Nothing to ask (the missing full stop after the path predates the PR).
- module_doc in Mathlib/Data/List/Lex.lean: `Mathlib/Combinatorics/Colex.lean` is the colex order on `Finset`, and `Mathlib/Order/PiLex.lean` defines `Πₗ`. The unchanged entries (PSigma/Order, Sigma/Order, Prod/Lex) all exist. Nothing to ask in this file. (Order/PiLex.lean has its own stale `Data.Finset.Colex`, but that file is outside this Data-scoped PR.)
- module_doc in Mathlib/Data/Matrix/Mul.lean: `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean` defines `Matrix.conjTranspose` and the scoped `ᴴ` notation. Nothing to ask.
- command in Mathlib/Data/Nat/Init.lean (library note): I checked all ten listed files exist and have the stated instances. Group/Nat/Defs has `CommMonoid ℕ`, Group/Int/Defs has `AddCommGroup ℤ`, Ring/Int/Defs has `CommRing ℤ`, Ring/Nat has the semiring instances, and the four Order/* files have the ordered instances. Nothing to ask.
- module_doc in Mathlib/Data/Option/Defs.lean: `Mathlib/Data/Option/` holds Basic.lean and NAry.lean. Nothing to ask.
- module_doc in Mathlib/Data/Set/Basic.lean: `Mathlib/SetTheory/ZFC/` exists (Basic, PSet, Class, Ordinal, ...). The line wrap is forced by the 100-column limit. Nothing to ask.
- Vector3.unexpandNil and the command before it (one family, same comment edit): `Init/NotationExtra.lean (Lean core)` is a clear way to name a core file and resolves. No other Mathlib file names it differently. Nothing to ask.
"""

findings = [
 {
  "path": "Mathlib/Data/Complex/Basic.lean",
  "line_start": 281,
  "claim": "The comment before `instance : Nontrivial ℂ` (lines 281-283) still says the `ℝ`-action on `ℂ` and action transitivity are 'defined in `Data.Complex.Module`'. That file no longer exists: it is the stale reference this PR fixes ten lines later, in the `instSMulRealComplex` docstring, but it is left unfixed here in the same file.",
  "suggested_fix": "Change `defined in `Data.Complex.Module`` to `defined in `Mathlib/LinearAlgebra/Complex/Module.lean``, matching the reference the PR uses in the `Complex.SMul.instSMulRealComplex` docstring.",
  "severity": "advisory"
 },
 {
  "path": "Mathlib/Data/Finset/Defs.lean",
  "line_start": 34,
  "claim": "The module doc's big-operators pointer now targets `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`, which only proves theorems about `∑`/`∏`. The operators `Finset.prod`/`Finset.sum` and the `∑ i ∈ s, f i` notation that this paragraph introduces are defined and documented in `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean`.",
  "suggested_fix": "Point the sentence at `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean` (the file with the definitions and the notation section) instead of `.../Finset/Basic.lean`.",
  "severity": "advisory"
 },
 {
  "path": "Mathlib/Data/Finset/Defs.lean",
  "line_start": 38,
  "claim": "In the same module doc, the sentence describing a `Fintype α` instance and `univ` still says 'See `Mathlib/Data/Fintype/Basic.lean`'. That file is now 'Instances for finite types'. `class Fintype` and `Finset.univ` are defined in `Mathlib/Data/Fintype/Defs.lean`, so the reference is stale in the way this PR sets out to fix.",
  "suggested_fix": "Replace `Mathlib/Data/Fintype/Basic.lean` with `Mathlib/Data/Fintype/Defs.lean` in that sentence.",
  "severity": "advisory"
 },
 {
  "path": "Mathlib/Data/Finset/Defs.lean",
  "line_start": 53,
  "claim": "The 'Main definitions' list in the `Finset` module doc names `Finset.instMembershipFinset` and `Finset.instCoeSortFinsetType`, and neither is declared. The membership instance's generated name is `Finset.instMembership`, and the coercion to a type comes from `SetLike.instCoeSortType` via `Finset.instSetLike` (checked by elaborating both in the file).",
  "suggested_fix": "Rename the entry `Finset.instMembershipFinset` to `Finset.instMembership`. Replace the `Finset.instCoeSortFinsetType` entry with one saying the coercion `s : Finset α` to the type of `x ∈ s` comes from `SetLike` (`SetLike.instCoeSortType`), or drop that entry.",
  "severity": "advisory"
 },
 {
  "path": "Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean",
  "line_start": 39,
  "claim": "The rewritten implementation note still offers generalizing `Finset.Nat.antidiagonalTuple` to finitely supported functions as something to do 'in the future', 'as in `Finset.finsuppAntidiag`'. That generalization already exists: `Finset.finsuppAntidiag` (Antidiag/Finsupp.lean), and `Finset.piAntidiag`/`Finset.finAntidiagonal` in `Mathlib/Algebra/Order/Antidiag/Pi.lean`. The TODO there says `Finset.finAntidiagonal` is strictly more general than `Finset.Nat.antidiagonalTuple`. So the paragraph now cites the generalization as a model for work that is already done.",
  "suggested_fix": "Replace the 'In the future, we could consider generalizing ...' sentence with a pointer to the existing generalizations, e.g. 'See `Finset.finAntidiagonal` and `Finset.piAntidiag` in `Mathlib/Algebra/Order/Antidiag/Pi.lean`, and `Finset.finsuppAntidiag` in `Mathlib/Algebra/Order/Antidiag/Finsupp.lean`, for generalizations to arbitrary index types and to finitely supported functions.'",
  "severity": "advisory"
 },
 {
  "path": "Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean",
  "line_start": 36,
  "claim": "The implementation note in this module doc, edited in this PR, refers to `Fintype.PiFinset`, which does not exist. The declaration is `Fintype.piFinset` (Mathlib/Data/Fintype/Pi.lean).",
  "suggested_fix": "Change `(Fintype.PiFinset fun _ ↦ range (n + 1))` to `(Fintype.piFinset fun _ ↦ range (n + 1))`.",
  "severity": "advisory"
 }
]
out = {"notes": notes, "findings": findings}
with open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/post-carryover-replan/results/pr_review_v5/probes/contract-2026-10-01/swap/pr33315/S1/submission.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
