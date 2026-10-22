# Goal brief

## 1. Kind of contribution

Documentation only: docstrings, comments and two deprecation messages in thirteen existing
CategoryTheory files.

## 2. Capability

In each place below, the prose sends the reader to another Mathlib source file, and that reference
is out of date in one or both of two ways: the path it names no longer holds the material meant, or
it is a shortened path that leaves the reader to work out which directory it starts from. After the
change, each place must lead a reader to the material it means, as the library stands at the base
commit.

Files are under `Mathlib/CategoryTheory/`; the old reference is in brackets.

- `Bicategory/Functor/StrictPseudofunctor.lean`: the TODO in the module docstring
  (`Functor/Strict.lean`).
- `ConcreteCategory/Bundled.lean`: the module docstring (`Mathlib/CategoryTheory/HasForget/UnbundledHom.lean`,
  `Mathlib/CategoryTheory/HasForget/BundledHom.lean`, `ConcreteCategory/Basic.lean`).
- `ConcreteCategory/BundledHom.lean` and `ConcreteCategory/UnbundledHom.lean`: the deprecation
  messages of `BundledHom` and `UnbundledHom` (`ConcreteCategory/Basic.lean`).
- `Functor/Basic.lean`: the comment before `Functor.map_comp_assoc` (`Mathlib/Tactic/Reassoc.lean`).
- `Groupoid/Subgroupoid.lean`: "Implementation details" in the module docstring
  (`Mathlib/GroupTheory/Subgroup/Basic.lean`).
- `Limits/FunctorCategory/Filtered.lean` and `Limits/FunctorCategory/Finite.lean`: the module
  docstrings (`Mathlib/CategoryTheory/Limits/FunctorCategory.lean`).
- `Limits/HasLimits.lean`: the doc comment of `colimit.ι_desc` (`Tactic/reassoc_axiom.lean`).
- `Limits/Preserves/Limits.lean`: the module docstring (`preserves/shapes.lean`).
- `Limits/Preserves/Over.lean`: the module docstring (`Mathlib/CategoryTheory/Adjunction/Over.lean`).
- `Localization/Equivalence.lean`: the module docstring (`Localization/Predicate.lean`).
- `Monoidal/Mon_.lean`: the docstring opening the section showing that monoids in a braided monoidal
  category form a monoidal category (`Mathlib/CategoryTheory/Monoidal/Braided.lean`, twice).

## 3. What must keep working

- Every declaration in these files keeps its statement, proof and attributes (the wording of the
  two deprecation messages aside).
- `BundledHom` and `UnbundledHom` stay deprecated since 2025-11-17, and their messages still direct
  users to the preferred approach: build the category by hand, then provide the `ConcreteCategory`
  instance.

## 4. Open questions

1. Breadth: only the places above, or also other out-of-date or shortened file references in these
   files, elsewhere in CategoryTheory, or across Mathlib.
2. Whether the statements around a reference (what the referred file is said to contain, the plan in
   the TODO, the note on the future of `Bundled`) should also be checked and brought up to date, or
   only the references.
3. Where the material an old reference named has no single home at the base commit, what the passage
   should lead to. The inputs name no intended target.

## 5. Where the requirements come from

- Description: absent at the start of review.
- Title (the current one, not verified to be the one at review time): a documentation change in
  CategoryTheory that fixes file references. Source of 1 and of the capability in 2.
- The change itself modifies each place listed in 2, and only docstrings, comments and deprecation
  messages, never a statement or proof. Source of the list in 2 and of 3's first point.
- The change itself modifies the deprecation messages of `BundledHom` and `UnbundledHom`, deprecated
  since 2025-11-17 at the base commit. Source of 3's second point.
