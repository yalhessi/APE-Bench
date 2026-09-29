# PR #33304 review notes: doc(CategoryTheory): fix file refs

The PR changes only documentation. In 13 files it replaces stale or short-form file references
with full `Mathlib/...lean` paths. None of the edits touches any Lean content: every object is a
module doc, a comment, a docstring, or the message string of a `deprecated` attribute. So most of
the checklist (proof-golf, generalization, duplication, naming) has nothing to act on. The review
came down to:

- whether each new path exists;
- whether the text around each path is still true;
- whether stale references are left in the touched files or elsewhere in the tree;
- line lengths;
- whether the files compile.

## Method

- **Paths.** I tried every old and new path with `file_read` on `target/<path>`. All 13 new
  paths exist. The 6 old full paths do not exist: `Limits/FunctorCategory.lean`,
  `Tactic/Reassoc.lean`, `GroupTheory/Subgroup/Basic.lean`, `Adjunction/Over.lean`,
  `Monoidal/Braided.lean` and `HasForget/UnbundledHom.lean`.
- **Rest of the tree.** I ran `content_search` over `target/Mathlib` (7445 files) for the old
  spellings. No other occurrences are left, so the PR is complete for the paths it fixes.
- **Line lengths.** All added lines are at most 98 characters.
- **Compilation.** `lean_verify_edit` with no edit on BundledHom.lean, where the deprecation
  string changed, reports that it compiles with no errors or warnings.

## Object by object

- **StrictPseudofunctor.lean module doc.** Correct. `Functor/Strict.lean` was ambiguous, and the
  PR resolves it to `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`. That file exists and
  is a `deprecated_module (since := "2025-10-02")` re-exporting `Bicategory.Strict.Pseudofunctor`,
  so the TODO still makes sense. No finding.
- **Bundled.lean module doc.** `HasForget/...` becomes `ConcreteCategory/...`, and
  `ConcreteCategory/Basic.lean` becomes a full path. All three targets exist. No finding. The
  "will be deprecated in the future" note is outside what a file-refs PR should change.
- **`BundledHom` and `UnbundledHom` deprecation messages.** Only the path inside the string
  changed. It exists, and the file compiles. No finding.
- **Functor/Basic.lean, line 65 comment.** Correct: `Mathlib/Tactic/CategoryTheory/Reassoc.lean`
  exists and does `public import Mathlib.CategoryTheory.Functor.Basic`.
  - **Finding (advisory).** Line 130 of the same file still has the short-form, stale
    "Natural isomorphisms are also provided in `Whiskering.lean`."
  - `Functor.leftUnitor`, `Functor.rightUnitor` and `Functor.associator` are defined in
    `Mathlib/CategoryTheory/Functor/Category.lean` (lines 158, 166 and 177). Whiskering.lean only
    proves the triangle and pentagon identities.
  - I tested the two-line replacement comment with `lean_verify_edit`: success.
- **Subgroupoid.lean module doc.** `Mathlib/Algebra/Group/Subgroup/Basic.lean` exists, and so does
  `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean`, which the PR does not change. No finding.
- **FunctorCategory/Filtered.lean and FunctorCategory/Finite.lean module docs.**
  `FunctorCategory/Basic.lean` exists. Its imports are `Functor.Currying` and
  `Limits.Preserves.Limits`, neither of which is Filtered or FiniteProducts, so the "cannot be in"
  rationale still holds. The other referenced files exist. No finding.
- **HasLimits.lean, docstring above `colimit.ι_desc`.** `Mathlib/Tactic/CategoryTheory/Reassoc.lean`
  is the right target for `reassoc`. The other references in the file,
  `Adjunction/Limits.lean` and `Limits/ConeCategory.lean`, exist and are already full paths.
  - Two older issues are too minor or out of scope for a refs PR, so I did not raise them: the
    remark is a general note attached as `colimit.ι_desc`'s docstring, and the full stop comes
    before "(see ...)".
- **Preserves/Limits.lean module doc.** The `Mathlib/CategoryTheory/Limits/Preserves/Shapes/`
  directory exists and holds 14 files (Products, Pullbacks, Equalizers, ...). No finding.
- **Preserves/Over.lean module doc.** `Over.forgetAdjStar` (`Over.forget X ⊣ Over.star X`) is
  declared in `Mathlib/CategoryTheory/Comma/Over/Pullback.lean`, per `declaration_search`, so the
  new reference is correct. Naming `Over.forgetAdjStar` as well would be a nicety, not something
  a maintainer would ask for. No finding.
- **Localization/Equivalence.lean module doc.** `Localization.of_equivalence_target` is declared
  in `Mathlib/CategoryTheory/Localization/Predicate.lean`, and the rewrap stays at 97 characters or
  fewer. No finding.
- **Mon_.lean section doc.** `tensorμ` is defined at line 597 of
  `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`. `tensor_associativity`,
  `leftUnitor_monoidal`, `rightUnitor_monoidal` and `associator_monoidal` are at lines 692-751 of
  the same file, so both changed sentences are accurate. The file's other references,
  `Tactic/Attr/Register.lean` and `Monoidal/Internal/Module.lean`, exist. No finding.

## Tool notes

- `file_search` returned empty results for every directory under `target/`, so I listed
  directories with `content_search` instead.
- `precedent_search` on two of the doc fragments returned nothing that applies.
- Zulip ('Broken file references', 2024-11) supports using the full path spelling in docs.
