# Review notes: PR #33315, doc(Data): fix file refs

## Method

- Read brief.md, pr.md, model.md and diff.patch.
- The file tools could not see the workspace until the first `lean_verify_edit`, an as-is compile
  of Mathlib/Data/Array/Defs.lean (compiles, no errors). After that the tree appears under `target/`.
- `file_search` globs match the full path, so existence checks used `*target/<path>`.
- Checked every new path the PR writes: all 11 exist. Checked every old path it replaces: none
  exist. So every edit in the diff fixes a genuinely broken reference.
- Collected every backticked slash-style `Mathlib/...` reference under Mathlib/Data (94 paths in
  70 files) and checked each one. All resolve. The one apparent miss, `Mathlib/Data/Set` with no
  trailing slash, is a directory reference.
- Then searched the changed files and the Lex siblings for dotted-style module references, which the
  PR did not target.

## Object by object

- **Array/Defs module doc.** The title changes from `##` to `#`, which is correct for a module title.
  The dangling pointer to `Mathlib/Data/Array.lean` is removed. The only other file in
  Mathlib/Data/Array is Extract.lean. `cyclicPermute!` and `permute!` have no lemmas anywhere; they
  are used only in Tactic/Translate/Core. So "It does not contain proofs about these definitions."
  is accurate. No finding.
- **Complex/Basic `instSMulRealComplex` docstring.** The new path exists, and that file opens
  `scoped SMul`, which is correct. Line 283, in the same file, still says `Data.Complex.Module` for
  the same moved file. **Finding 1.** The `Mathlib.Analysis.Complex.Polynomial.Basic` reference on
  line 20 exists.
- **NatAntidiagonal module doc.** `Finset.finsuppAntidiag` exists in Antidiag/Finsupp.lean. But
  Antidiag/Pi.lean already has `finAntidiagonal`, which it documents as strictly more general, plus
  `piAntidiag` and `piAntidiag_univ_fin_eq_antidiagonalTuple`. The "In the future" framing is
  therefore stale, and the closest analogue is not mentioned. **Finding 2.** The edit compiles.
- **Finset/Defs module doc.** The BigOperators pointer goes to Finset/Basic.lean. The notation and
  `Finset.prod` are in Finset/Defs.lean. **Finding 3.** The Fintype pointer on the neighbouring,
  unchanged line goes to Fintype/Basic.lean. `class Fintype` and `univ` are in Fintype/Defs.lean.
  **Finding 4.** The `Finset/Card.lean` pointer is correct. The Main definitions list uses possibly
  outdated instance names (for example, there is no explicit CoeSort instance in the file), but that
  is outside a file-reference PR, so no finding.
- **MonomialOrder module doc.** `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean` exists and defines
  `DegLex`. The line lacks a trailing period, but that was already true before the PR and is too
  small to raise. No finding.
- **List/Lex module doc.** The new Colex and PiLex paths exist, and their contents match the
  descriptions. The unchanged entries PSigma/Order, Sigma/Order and Prod/Lex exist. The sibling files
  keep dotted-style stale refs (`Data.Finset.Colex`/`CoLex`, `Data.Pi.Lex`, `Combinatorics.CoLex`).
  **Finding 5** (scope, advisory). Order/PiLex.lean also has `Data.Finset.Colex`, but it lies
  outside Data/, so I left it out.
- **Matrix/Mul module doc.** `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean` defines
  `conjTranspose` and the scoped `ᴴ` notation. No finding.
- **Nat/Init library note.** Checked all ten listed files. Group/Nat/Defs has `CommMonoid ℕ` and
  related instances. Group/Int/Defs has `AddCommGroup ℤ`. Ring/Nat has `CommSemiring ℕ`.
  Ring/Int/Defs has `CommRing ℤ`. Order/Group/Nat has `IsOrderedAddMonoid ℕ`. Order/Group/Int has
  `IsOrderedAddMonoid ℤ`. Order/Ring/Nat and Order/Ring/Int have `IsStrictOrderedRing`. All
  descriptions are accurate. No finding.
- **Option/Defs module doc.** The `Mathlib/Data/Option/` directory exists and holds Basic.lean and
  NAry.lean. No finding.
- **Set/Basic module doc.** The `Mathlib/SetTheory/ZFC/` directory exists (Basic, PSet, Class, and
  others). The old `SetTheory/ZFC.lean` does not. Set/Defs and Set/Operations exist. No finding.
- **Vector3 comments (`unexpandNil`, `unexpandCons`).** The `src/` prefix is dropped and "(Lean
  core)" is added. That is reasonable. Lean core sources are not in the workspace, so I could not
  confirm the path, but `Init/NotationExtra.lean` is the core file for the List-literal unexpanders.
  No finding.

## Concern families

None of the changes are proofs or declarations, so proof-golf, generalization, naming and
correctness (build) do not apply. Every changed file is a doc or comment edit and compiles.
Duplication: nothing new. Style: nothing beyond the findings above.

## Tool calls of note

- `lean_verify_edit` in line mode succeeded for the three edits proposed in findings 1-4:
  Complex/Basic lines 281-283, NatAntidiagonal lines 39-41, and Finset/Defs lines 34-38. The first
  attempt lost its backticked text to shell substitution in an unquoted heredoc. I re-ran with the
  text intact, and those results are the ones cited.
- `precedent_search` on the NatAntidiagonal note returned unrelated antidiagonal and weight comments.
  `zulip_search` found the 2024 "Broken file references" thread, which is general context only.
