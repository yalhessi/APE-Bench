# Review notes: PR #33315, "doc(Data): fix file refs"

This is a documentation-only PR: 11 files, all module docs, docstrings or comments. No
declaration's statement or proof changes, so proof-golf, generalization, duplication and naming
of code do not arise. For every reference, the main check was whether the new path exists in the
reviewed workspace (`file_read` on `target/<path>`; `file_search` returned nothing even for known
files, so it was not used) and whether the file it names really holds what the prose claims.

## Tooling notes
- Workspace paths are `target/Mathlib/...`.
- For the reference checks, `file_read` on the first lines of a file was used: "File not found"
  means the file is missing.
- All the old paths are gone (Data/Complex/Module, BigOperators/Group/Finset.lean,
  Data/Finsupp/DegLex, Data/Finset/Colex, Data/Pi/Lex, Data/Matrix/ConjTranspose,
  Algebra/Group/Nat.lean, Algebra/Group/Int.lean, Algebra/Ring/Int.lean), so each fix is warranted.

## Object by object

- **Array/Defs module doc**: `##` -> `#` title fix is correct. The dropped pointer to the
  non-existent `Mathlib/Data/Array.lean` is fine: `Mathlib/Data/Array/` has only `Defs.lean` and
  `Extract.lean`, and Extract holds lemmas about core `Array.extract`. No file proves anything about
  `cyclicPermute!` or `permute!` (content_search: they appear only in Defs and Tactic/Translate/Core).
  So "It does not contain proofs about these definitions." is accurate. No finding.
- **Complex/Basic docstring of `instSMulRealComplex`**: `Mathlib/LinearAlgebra/Complex/Module.lean`
  exists and has `open scoped SMul` (line 53), so the docstring's claim holds. No finding.
- **Fin/Tuple/NatAntidiagonal module doc**: `Finset.finsuppAntidiag` exists in the cited file.
  But the note still frames the finsupp generalization as future work. `Finset.piAntidiag` and
  `Finset.finAntidiagonal` already generalize `antidiagonalTuple`, with
  `piAntidiag_univ_fin_eq_antidiagonalTuple`, and Antidiag/Pi.lean carries a "Deduplicate" TODO.
  **Finding 1** (advisory). The replacement text compiles.
- **Finset/Defs module doc**: `.../BigOperators/Group/Finset/Basic.lean` exists. Three things:
  - `Mathlib/Data/Fintype/Basic.lean` in the same paragraph is stale: `class Fintype` and `univ`
    are in `Fintype/Defs.lean`. **Finding 2**.
  - `Finset/Defs.lean` is the better big-operators target: it defines them and documents the
    notation. **Finding 3**.
  - The Main-definitions list names `Finset.instMembershipFinset` and
    `Finset.instCoeSortFinsetType`, and neither exists. I confirmed this by compiling probes with
    lean_verify_edit; `Finset.instMembership` and `Finset.instSetLike` exist. **Finding 4**.

  `Mathlib/Data/Finset/Card.lean` does define `Finset.card`. The combined doc edit compiles.
  All three findings are advisory.
- **Finsupp/MonomialOrder module doc**: `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean` exists
  and defines `MonomialOrder.degLex`. The sentence has no final period, which was already the case
  before this PR. Too minor to request; no finding.
- **List/Lex module doc**: `Mathlib/Combinatorics/Colex.lean` is the colex order on finsets, and
  `Mathlib/Order/PiLex.lean` defines the `Πₗ` notation. The PSigma/Order, Sigma/Order and Prod/Lex
  references exist and are correct. No finding.
- **Matrix/Mul module doc**: `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean` declares
  `scoped postfix "ᴴ" => Matrix.conjTranspose`. No finding.
- **Nat/Init library note**: all ten listed files exist. Group/Nat/Defs holds the monoid instances,
  Group/Int/Defs the `AddCommGroup ℤ`, Ring/Nat the semiring instances and Ring/Int/Defs
  `CommRing ℤ`. The four Order/... files hold the ordered instances. No finding.
- **Option/Defs module doc**: `Mathlib/Data/Option/` holds Basic, Defs and NAry. No finding.
- **Set/Basic module doc**: `Mathlib/SetTheory/ZFC/` exists (Basic, PSet, Class, Ordinal, Rank, ...),
  and a directory reference suits a multi-file encoding. `Data/Set/Defs.lean` (`def Set`) and
  `Data/Set/Operations.lean` are also correct. No finding.
- **Vector3 comments (`unexpandNil`, `unexpandCons`)**: the change is only a respelling of the
  core path, now `Init/NotationExtra.lean` marked "(Lean core)". I could not check Lean core inside
  the allowed workspace. It matches the well-known location of the `List.nil`/`List.cons`
  unexpanders, so no finding.

## Other tools
- A precedent_search on the NatAntidiagonal note returned nothing directly relevant.
- Zulip ("Broken file references", 2024-11) shows maintainers preferring the full
  `Mathlib/...lean` path spelling in docs. The PR follows it throughout.
