# Review notes: PR #33315 `doc(Data): fix file refs`

Documentation-only PR across 11 files under `Mathlib/Data`. What I did: checked that every new path the
PR writes exists in the workspace and every old one does not (`file_search` with a full-path glob
from the root; a `directory_path` other than `.` returned nothing, so all lookups went from the root).
I also checked that the files cited hold what the prose says they hold (`declaration_search`,
`file_read`), and searched for the same stale references elsewhere (`content_search`). Every edit I
propose was compiled with `lean_verify_edit`: all eight edits returned `compiled`, with no errors or
warnings. Proof-golf, generalization, naming and duplication do not apply: no declaration's
statement or proof changes.

## Object by object

- **`Mathlib/Data/Array/Defs.lean` module doc.** The `##` -> `#` title fix is right. Deleting the
  pointer to `Mathlib/Data/Array.lean` is right: no file proves anything about `cyclicPermute!` or
  `permute!` (content_search found only uses in `Tactic/Translate/Core.lean`). Filed: the title and
  body are generic ("various definitions") for a file holding two permutation functions.
- **`Mathlib/Data/Complex/Basic.lean`, `instSMulRealComplex` docstring.** The new path exists, and
  `Mathlib/LinearAlgebra/Complex/Module.lean:53` does `open scoped SMul`, so the docstring is
  accurate. Nothing filed.
- **`Mathlib/Data/Fin/Tuple/NatAntidiagonal.lean` module doc.** The archive `Partition` file is gone.
  `Finset.finsuppAntidiag` exists at `Algebra/Order/Antidiag/Finsupp.lean:45`. Filed: the "in the
  future" note now describes a generalization that exists (`finAntidiagonal`, `piAntidiag`,
  `finsuppAntidiag`), and `Antidiag/Pi.lean` already carries the TODO to deduplicate.
- **`Mathlib/Data/Finset/Defs.lean` module doc.** `.../Finset/Basic.lean` exists, but `Finset.prod`
  and the notation live in `.../Finset/Defs.lean`. Filed: point there. Also filed: the line 38 pointer
  `Mathlib/Data/Fintype/Basic.lean` for the `Fintype` class is stale; `Fintype` is declared in
  `Data/Fintype/Defs.lean:56`. `Mathlib/Data/Finset/Card.lean` for `Finset.card` is correct
  (`Card.lean:47`).
- **`Mathlib/Data/Finsupp/MonomialOrder.lean` module doc.** `MonomialOrder/DegLex.lean` exists and is
  the only file in that directory. Filed: the edited sentence has no period.
- **`Mathlib/Data/List/Lex.lean` module doc.** `Combinatorics/Colex.lean` and `Order/PiLex.lean`
  exist, and their titles match the descriptions. `Data/PSigma/Order.lean`, `Data/Sigma/Order.lean`
  and `Data/Prod/Lex.lean` exist. Filed: the twin "Related files" lists in those three Data files
  still name `Data.Finset.Colex`/`CoLex` and `Data.Pi.Lex`. Also filed (convention-driven): no blank
  line between "Related files are:" and the list.
- **`Mathlib/Data/Matrix/Mul.lean` module doc.** The new path exists and defines `ᴴ` (line 45).
  Filed: the identical stale sentence remains in `Mathlib/LinearAlgebra/Matrix/Defs.lean:32`.
- **`Mathlib/Data/Nat/Init.lean` library note.** All ten paths exist. The instances are where the note
  says: `Nat.instCommMonoid` in Group/Nat/Defs, `Int.instAddCommGroup` in Group/Int/Defs,
  `Int.instCommRing` in Ring/Int/Defs, `Nat.instCommSemiring` in Ring/Nat, and the ordered instances
  in Order/{Group,Ring}/{Nat,Int}. Filed (convention-driven): the bullets have no periods, and no
  blank line separates them from "The relevant files are:".
- **`Mathlib/Data/Option/Defs.lean` module doc.** `Mathlib/Data/Option/` exists (Basic, NAry, Defs).
  Nothing filed.
- **`Mathlib/Data/Set/Basic.lean` module doc.** `Mathlib/SetTheory/ZFC/` exists (Basic, PSet, Class,
  ...). The joined sentence is 102 characters, so the line break is required. Nothing filed.
- **`Mathlib/Data/Vector3.lean`, two `-- this is copied from` comments (lines 55 and 60).** Filed, one
  per declaration: remove the provenance notes rather than reword them. The old `src/Init/...` was
  the lean4-repo path, so the hunk itself is marginal. The Lean core source is not in the workspace,
  so I could not check that the unexpanders are still there.
- **PR title/description.** The title has the `doc(Data): ...` form. Filed (advisory): the
  description does not mention the two non-mechanical changes (Array heading and deletion, the
  NatAntidiagonal re-pointing).

## Conventions: places filed and places left

- **Precise module-doc title:** filed at `Array/Defs.lean`. Left the other titles, which the PR does
  not touch.
- **Module doc covers every main result:** folded into the `Array/Defs.lean` finding (it names
  neither definition). No other changed docstring adds or drops a result.
- **Cleanup hunk costing readability:** no hunk costs readability. Left.
- **Standard spacing:** checked the changed lines; there are no doubled or trailing spaces and the
  markdown heading `# Definitions on Arrays` has its space. Left.
- **Line breaks only past 100 characters:** Array (102 joined), Set/Basic (102 joined) and
  NatAntidiagonal (120 joined) all exceed 100, so their breaks are required. Left.
- **Full sentences ending in a period:** filed at `MonomialOrder.lean:37` and at the `Nat/Init.lean`
  bullets. Left `Matrix/Mul.lean:35` ("See ... for" continues into the list) and the `List/Lex.lean`
  bullets (they already end in periods).
- **Same construct spelled the same way in a file:** every new reference is a backticked file path,
  matching its neighbours in the same list. Left.
- **Standard section headings only:** the PR adds no heading; it promotes the title to `#`. Left.
- **Marginal-benefit change:** the Vector3 rewording is marginal (`src/Init/...` was a valid lean4
  path). Raised inside the two Vector3 findings, not filed separately.
- **Comment kept in step with the code:** filed at `NatAntidiagonal.lean` ("in the future" describes
  a generalization that exists). Left `Complex/Basic.lean`: its "used ... in" was checked and holds.
- **PR title and description precise:** filed (advisory) on the description.
- **Purely stylistic change to existing prose:** the only candidate is the Vector3 rewording, and it
  is covered by the removal findings. Left.
- **"See also" cross-references:** the PR's See-also lists are what it fixes. Its twins are filed
  under the List/Lex and Matrix/Mul scope findings.
- **Concise description, template syntax:** the description is one line, with no dependencies.
  Left.
- **File path, not dotted module name:** every new reference is a file path. The dotted stale twins
  in PSigma/Sigma/Prod are filed in the List/Lex finding.
- **Title format `type(Area): description`:** `doc(Data): fix file refs` conforms. Left.
- **Names in backticks, full names:** all paths and names in the changed lines are backticked. Left.
- **Comment syntax matches role:** the Vector3 `--` provenance comments describe the declaration
  below. The findings ask to delete them, or else fold them into the docstring.
- **Generic reference named specifically:** the changed lines name files explicitly. Left.
- **`TODO` marker:** the PR adds none. The NatAntidiagonal finding proposes a `TODO:`.
- **Backticked fragment on one line:** checked; no fragment is split in the changed lines. Left.
- **Docstring text on the `/--` line:** the only `/--` in the changed objects is the Nat/Init
  `library_note2 ... /--` opening. The PR does not touch it, and the library notes use this form (20
  files open `/--` alone on the line, 2 do not). Left.
- **Change existing code only where needed:** the Array title promotion is needed (the title must be
  `#`). Left.
- **Blank line around bulleted lists:** filed at the two changed lists that follow their intro line
  directly: `List/Lex.lean` ("Related files are:", line 22) and `Nat/Init.lean` ("The relevant files
  are:", line 46), the latter folded into the bullet-period finding. Both edits compiled. Left
  `Matrix/Mul.lean:35`, which already has a blank line before `* `ᴴ``.
- **Adapted-from comments not kept:** filed at both Vector3 comments.
