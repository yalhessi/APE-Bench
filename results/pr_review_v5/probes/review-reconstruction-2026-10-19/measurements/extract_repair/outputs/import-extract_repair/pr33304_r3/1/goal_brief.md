# Goal brief

## 1. Kind of contribution

Documentation only. Every change is to prose: module docstrings, one declaration's doc comment, one
code comment, and the message text of two existing deprecations.

## 2. Capability

When a reader follows a file reference in the documentation of these CategoryTheory files, it should
lead to a file that exists at the base commit and contains the material the sentence describes. The
references concerned are listed below. Each place is given relative to `Mathlib/CategoryTheory/`, and
each reference is quoted as the base text writes it:

- `ConcreteCategory/Bundled.lean`, module docstring: `Mathlib/CategoryTheory/HasForget/UnbundledHom.lean`,
  `Mathlib/CategoryTheory/HasForget/BundledHom.lean`, `ConcreteCategory/Basic.lean`.
- The deprecation messages of `CategoryTheory.BundledHom` and `CategoryTheory.UnbundledHom`:
  `ConcreteCategory/Basic.lean`.
- `Bicategory/Functor/StrictPseudofunctor.lean`, the TODO: `Functor/Strict.lean` (twice).
- `Functor/Basic.lean`, the comment before `Functor.map_comp_assoc`: `Mathlib/Tactic/Reassoc.lean`.
- `Limits/HasLimits.lean`, the doc comment just before `colimit.ι_desc`: `Tactic/reassoc_axiom.lean`.
- `Groupoid/Subgroupoid.lean`, "Implementation details": `Mathlib/GroupTheory/Subgroup/Basic.lean`.
- `Limits/FunctorCategory/Filtered.lean` and `Limits/FunctorCategory/Finite.lean`, module docstrings:
  `Mathlib/CategoryTheory/Limits/FunctorCategory.lean`.
- `Limits/Preserves/Limits.lean`, module docstring: `preserves/shapes.lean`.
- `Limits/Preserves/Over.lean`, module docstring: `Mathlib/CategoryTheory/Adjunction/Over.lean`.
- `Localization/Equivalence.lean`, module docstring: `Localization/Predicate.lean`.
- `Monoidal/Mon_.lean`, the section docstring: `Mathlib/CategoryTheory/Monoidal/Braided.lean` (twice).

Some are full paths, some partial. Where the cited material lives at the base commit must be found
in the library; the packet holds only the files above.

## 3. What must keep working

- No statement, definition or proof in these files changes, and every existing use of their
  declarations still compiles and behaves as before.

## 4. Open questions

- **Form.** A reference could be a path from the repository root, a path relative to some directory, a
  module name, or a pointer to a declaration in the target file. The base files mix these forms.
- **Partial references.** Do partial references that may resolve relative to a nearby directory
  (`Functor/Strict.lean`, `ConcreteCategory/Basic.lean`, `Localization/Predicate.lean`) need to change
  at all?
- **Targets with no single obvious file:**
  - the pointer to results on preserving (co)limits of specific shapes in `Preserves/Limits.lean`;
  - the pointer for the fact that `Over.forget X` is a left adjoint in `Preserves/Over.lean`;
  - in `HasLimits.lean`, whether to point to a file or to the `reassoc` attribute itself.
- Whether the StrictPseudofunctor TODO still applies as written.
- Whether deprecation messages, which users see as warnings, belong in a documentation fix.
- **Scope.** Do stale references elsewhere in CategoryTheory, or in Mathlib generally, belong in this
  contribution?

## 5. Where the requirements come from

- **Description:** absent. The PR had no description at the start of review.
- **Title** "doc(CategoryTheory): fix file refs" (the current title, not verified to be the one at
  review time): the kind, the area, and the aim that file references be correct (section 2, first
  sentence).
- **The change itself:** it modifies exactly the references listed in section 2, and only prose
  (comments, doc comments, deprecation message strings) (sections 1 and 3).
