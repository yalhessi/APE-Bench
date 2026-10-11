# Review notes: PR #33315, doc(Data): fix file refs

This PR changes documentation only, across 11 files under `Mathlib/Data/`. My main check was that
every path the PR introduces exists in the reviewed workspace, and that the file or declaration it
names really holds what the sentence says. All tool calls went through `./ptool`. Workspace paths
are under `target/`.

## Existence check (file_read on each referenced path)

Every path introduced or left by the PR exists:
- `Mathlib/LinearAlgebra/Complex/Module.lean`
- `Mathlib/Algebra/Order/Antidiag/Finsupp.lean`
- `Mathlib/Algebra/BigOperators/Group/Finset/Basic.lean`
- `Mathlib/Data/Finsupp/MonomialOrder/DegLex.lean`
- `Mathlib/Combinatorics/Colex.lean`
- `Mathlib/Order/PiLex.lean`
- `Mathlib/Data/{PSigma/Order,Sigma/Order,Prod/Lex}.lean`
- `Mathlib/LinearAlgebra/Matrix/ConjTranspose.lean`
- `Mathlib/Algebra/Group/{Nat,Int}/Defs.lean`
- `Mathlib/Algebra/Ring/Nat.lean`
- `Mathlib/Algebra/Ring/Int/Defs.lean`
- `Mathlib/Algebra/Order/{Group,Ring}/{Nat,Int}.lean`
- `Mathlib/Data/Nat/Basic.lean`
- `Mathlib/Data/Int/Init.lean`
- `Mathlib/Data/Set/{Defs,Operations}.lean`
- `Mathlib/Data/Fintype/Basic.lean`
- `Mathlib/Data/Finset/Card.lean`
- the directories `Mathlib/Data/Option/` and `Mathlib/SetTheory/ZFC/` (Basic, Class, PSet, Ordinal,
  Rank, VonNeumann, Cardinal)

The old targets (`Data/Complex/Module.lean`, `BigOperators/Group/Finset.lean`,
`Data/Finsupp/DegLex.lean`) are gone, which confirms they were stale. A content_search for
path-like strings in all 11 changed files found no remaining stale reference in them.

## Object by object

- **Array/Defs module doc.** The heading level was fixed from `##` to `#`, which is correct. The
  reference to `Mathlib/Data/Array.lean` was removed. A search for `cyclicPermute` / `permute!`
  across Mathlib finds no file of lemmas about these definitions, so "It does not contain proofs
  about these definitions." is accurate and there is nothing to point to. No finding.
- **Complex/Basic, `instSMulRealComplex` docstring.** `Mathlib/LinearAlgebra/Complex/Module.lean`
  has `open scoped SMul` at line 53. It is the only file other than Basic.lean that opens the
  scope, so "used here and in ..." is accurate. No finding.
- **Fin/Tuple/NatAntidiagonal module doc.** **Finding 1.** The cited file and declaration exist.
  However, the sentence still calls a generalization "future" work when it already exists:
  - `Finset.finAntidiagonal` and `Finset.piAntidiag` live in `Algebra/Order/Antidiag/Pi.lean`.
  - That file has `piAntidiag_univ_fin_eq_antidiagonalTuple` and a "Deduplicate" TODO.
  - `finsuppAntidiag` covers finitely supported functions.

  The rewrite I propose compiles.
- **Finset/Defs module doc.** **Finding 2.** `BigOperators/Group/Finset/Basic.lean` exists but
  only proves lemmas. The definitions `Finset.prod`/`sum` and the notation documentation are in
  `.../Finset/Defs.lean`. That is the right target for "More information". Compiles.
- **Finsupp/MonomialOrder module doc.** **Finding 3**, advisory. The path is correct and
  `MonomialOrder.degLex` lives there. The edited sentence lacks its closing period and does not
  name the declaration. Compiles.
- **List/Lex module doc.** `Combinatorics/Colex.lean` is the Finset colex file and
  `Order/PiLex.lean` defines `Πₗ`. Both are correct, and the unchanged entries exist. No finding.
  - Outside this PR, the sibling "See also" lists in `Order/PiLex.lean` (`Data.Finset.Colex`) and
    `Combinatorics/Colex.lean` (`Data.Pi.Lex`) still carry the same stale references.
  - Neither file is in `Data/`, which is this PR's stated scope, so I did not file a finding.
- **Matrix/Mul module doc.** `Matrix.conjTranspose` and the scoped `ᴴ` notation are declared in
  `LinearAlgebra/Matrix/ConjTranspose.lean` (lines 41 and 45). Correct. No finding.
- **Nat/Init library note.** I listed each file's instances:
  - Group/Nat/Defs: `CommMonoid ℕ` etc.
  - Group/Int/Defs: `AddCommGroup ℤ`.
  - Ring/Nat: `CommSemiring ℕ`.
  - Ring/Int/Defs: `CommRing ℤ`.
  - Order/Group/Nat and Order/Group/Int: ordered add monoid instances.
  - Order/Ring/Nat and Order/Ring/Int: `IsStrictOrderedRing`.

  Every line matches its description. Data/Nat/Basic and Data/Int/Init exist and cite the note.
  No finding.
- **Option/Defs module doc.** The directory `Mathlib/Data/Option/` exists (e.g. Basic.lean). No
  finding.
- **Set/Basic module doc.** `Mathlib/SetTheory/ZFC/` exists with the ZFC encoding. No finding.
- **Vector3 comments (`unexpandNil`, `unexpandCons`).** `src/Init/NotationExtra.lean` was in
  fact a valid lean4-repo path. The new `Init/NotationExtra.lean` (Lean core) is equally valid.
  Mathlib's own `Data/PSigma/Order.lean` imports `Init.NotationExtra`. I could not inspect core
  from the workspace. The change is harmless, so no finding.

## Context checked

- Zulip "Broken file references" (2024-11): maintainers favour the path spelling
  `Mathlib/Foo/Bar.lean` in docs. The PR follows it.
- precedent_search on the NatAntidiagonal note returned nothing applicable.
- Per-family checklist: proof-golf, generalization, naming and correctness of code do not arise,
  because no declaration's statement or body changes. Duplication and scope gave nothing beyond
  the sibling-file remark above.

## Edits verified with lean_verify_edit (all `compiled`, no errors or warnings)

- NatAntidiagonal.lean lines 39-41: the replacement paragraph.
- Finset/Defs.lean line 34: the path changed to `.../Finset/Defs.lean`.
- MonomialOrder.lean line 37: the period added and `MonomialOrder.degLex` named.
