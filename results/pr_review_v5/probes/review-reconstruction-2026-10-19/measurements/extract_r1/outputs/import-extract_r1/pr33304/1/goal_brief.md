# Goal brief

## 1. Kind of contribution

Documentation only.

## 2. Capability

In thirteen existing files under `Mathlib/CategoryTheory/`, prose that sends the reader to another
Mathlib source file must send them to a file that exists at the base commit and that holds the
material the sentence describes. Some of these pointers name paths that no longer hold that
material.

The places concerned (paths relative to `Mathlib/CategoryTheory/`):

- `Bicategory/Functor/StrictPseudofunctor.lean`: the TODO in the module docstring;
- `ConcreteCategory/Bundled.lean`: the module docstring;
- `ConcreteCategory/BundledHom.lean` and `ConcreteCategory/UnbundledHom.lean`: the messages of the
  deprecation attributes on `CategoryTheory.BundledHom` and `CategoryTheory.UnbundledHom`;
- `Functor/Basic.lean`: the comment above `Functor.map_comp_assoc`;
- `Groupoid/Subgroupoid.lean`: the "Implementation details" section of the module docstring;
- `Limits/FunctorCategory/Filtered.lean`, `Limits/FunctorCategory/Finite.lean`,
  `Limits/Preserves/Limits.lean`, `Limits/Preserves/Over.lean`, `Localization/Equivalence.lean`:
  the module docstrings;
- `Limits/HasLimits.lean`: the doc comment above `colimit.ι_desc`;
- `Monoidal/Mon_.lean`: the docstring explaining the monoidal structure on the category of monoids.

## 3. What must keep working

- No declaration's statement, proof or attributes change; only prose and message text do.
- `CategoryTheory.BundledHom` and `CategoryTheory.UnbundledHom` stay deprecated, with the same date
  and the same advice (build the category by hand, then provide a `ConcreteCategory` instance).
- Each edited passage keeps its meaning, including the TODO about renaming
  `StrictPseudofunctor.lean` once the deprecated file it mentions is removed.
- The files still build and pass Mathlib's style linters.

## 4. Open questions

- What "fix" covers: (a) only pointers whose path no longer holds the material; or (b) also pointers
  that still resolve but are written relative to some subdirectory.
- Where the material a pointer cites has been split across several files or has no single
  successor: whether to point to one file, to several, or to a directory.
- Whether other stale prose in the same passages (claims, not file pointers) belongs in this change.
- Whether similar stale pointers in other files, in category theory or elsewhere, belong here.

## 5. Where the requirements come from

- Kind and capability: the title (the current title, not verified to be the one at review time)
  describes a documentation change in category theory that fixes file references; the change itself
  edits only file pointers in the places listed under 2.
- The list of places: the change itself.
- Everything under 3: the change itself. It modifies only comments, docstrings and the message text
  of the two deprecation attributes, and in the TODO only the file names.
- The PR had no description at the start of review.
