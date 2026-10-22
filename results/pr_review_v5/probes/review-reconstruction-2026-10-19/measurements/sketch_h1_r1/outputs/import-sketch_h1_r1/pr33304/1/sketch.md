# Sketch: repairing file references in CategoryTheory prose

Prose only: no statement, proof, attribute or `since` date changes. Lean below is unchecked.

### 1. Breadth
- **Choice:** the places listed in the brief, nothing more.
- **Alternatives:** also the other rootless reference in a touched file (`Whiskering.lean`); all 25 rootless references in CategoryTheory (S2); a sweep plus a lint.
- **References:** `Functor/Basic.lean:130`; S2.
- **What would decide it:** open. No recorded preference on sweep size; a wide sweep without a check that keeps it fixed decays again (S2: no such lint exists).

### 2. How a reference is spelled
- **Choice:** full path from the repository root, in backticks (`Mathlib/CategoryTheory/.../X.lean`), keeping any declaration name the passage already gives.
- **Alternatives:** dotted module names (S5); a declaration name alone (S6).
- **References:** S4 (113 of 140 references use full paths); `Localization/Equivalence.lean:14` and `Monoidal/Mon_.lean:268` already pair a path with a declaration.
- **What would decide it:** an adopted standard. S3 shows it asked and supported, not adopted.

### 3. References with one obvious successor
- **Choice:**
  - `Limits/FunctorCategory/Filtered.lean:14`, `Finite.lean:16` → `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean` (both import it, `Filtered.lean:8`, `Finite.lean:8`).
  - `Monoidal/Mon_.lean:269,283` → `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean` (`Mon_.lean:9`; `tensorμ` and the associator/unitor monoidality lemmas live there, recalled).
  - `Localization/Equivalence.lean:14` → `Mathlib/CategoryTheory/Localization/Predicate.lean` (`Equivalence.lean:8`).
  - `ConcreteCategory/Bundled.lean:17,19` → `Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean` and `.../BundledHom.lean` (`UnbundledHom.lean:8`); `Bundled.lean:23` → `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean` (`BundledHom.lean:8`).
  - `Functor/Basic.lean:65` and `Limits/HasLimits.lean:709` → `Mathlib/Tactic/CategoryTheory/Reassoc.lean` (recalled; `Functor/Basic.lean:10-11` show category tactics under `Mathlib/Tactic/CategoryTheory/`).
- **Alternatives:** at `HasLimits.lean:709`, drop the parenthetical, since line 708 already names `reassoc`.
- **What would decide it:** the Reassoc path is from memory; confirm it exists and imports `Mathlib.CategoryTheory.Functor.Basic`, which the comment's reason relies on.

### 4. Material that no longer has one file
- **Choice:** `Limits/Preserves/Limits.lean:19`: "see the files in `Mathlib/CategoryTheory/Limits/Preserves/Shapes/`". `Groupoid/Subgroupoid.lean:43`: `Mathlib/Algebra/Group/Subgroup/` (the old file is now split across `Defs`, `Basic`, `Lattice`, `Map`, ...; recalled, `Subgroupoid.lean:8` imports `Mathlib.Algebra.Group.Subgroup.Defs`).
- **Alternatives:** one representative file (`.../Shapes/Pullbacks.lean`, `.../Subgroup/Basic.lean`); declarations (`PreservesPullback.iso`, `Subgroup`).
- **References:** S7 (directory references with and without trailing slash).
- **What would decide it:** open. "The structure of this file" (Subgroupoid) was copied from material now spread over several files, which favours the directory.

### 5. `Limits/Preserves/Over.lean:15`
- **Choice:** "See `Over.forgetAdjStar` in `Mathlib/CategoryTheory/Comma/Over/Pullback.lean`." (recalled as the successor of `Adjunction/Over.lean`).
- **Alternatives:** path alone; declaration alone; point instead to where `Over.forget X` is shown to create colimits, which needs no binary products.
- **References:** S6, S8.
- **What would decide it:** the base location of `Over.forgetAdjStar`; a `deprecated_module` stub at the old path, if any, names the successor (S8). The declaration name survives the next move.

### 6. The two deprecation messages
- **Choice:** same wording, full path, reflowed under 100 columns (`BundledHom.lean:32-34`, `UnbundledHom.lean:29-31`):
  ```lean
  @[deprecated "The preferred method for talking about concrete categories is to implement the \
  category manually and then provide the `ConcreteCategory` instance on top of this. See \
  `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`." (since := "2025-11-17")]
  ```
- **Alternatives:** name the class `CategoryTheory.ConcreteCategory` instead of a file; dotted module name.
- **References:** S10 (the other messages name declarations or an approach, never a file).
- **What would decide it:** open; decision 2 favours the path, S10 the declaration.

### 7. The Bundled note
- **Choice:** fix the paths, and make the touched sentences true at base: the `Category` instances in the two hom files are deprecated (since 2025-11-17); `Bundled` itself may follow. Sketch of `Bundled.lean:16-24`:
  > The deprecated files `Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean` and
  > `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean` provide `Category` instances for
  > these. New concrete categories should instead be defined manually, with a `ConcreteCategory`
  > instance on top; see `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`. `Bundled` itself
  > may be deprecated in the future.
- **Alternatives:** paths only; a full rewrite of the module docstring.
- **References:** S9; `BundledHom.lean:32-35`, `UnbundledHom.lean:29-32`, `Bundled.lean:37` (not deprecated).
- **What would decide it:** whether the PR owns the claims beside a reference (brief, open question 2). Whether the examples (topological spaces, monoids) still use these files is not visible here.

### 8. The StrictPseudofunctor TODO
- **Choice:** full paths in both places (`Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`). If no deprecated file remains at that path at base, reword to "Rename this file to `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`", since the condition is met.
- **Alternatives:** paths only, whatever the premise; do the rename (not a documentation change).
- **References:** `StrictPseudofunctor.lean:19-22`; S8.
- **What would decide it:** whether a `deprecated_module` stub exists at that path at base; not visible here.

### 9. Other claims beside the references
- **Choice:** leave unchanged: the "shouldn't import" reasons (`Filtered.lean:14-15`, `Finite.lean:16-17`), the reason at `Functor/Basic.lean:64-65`, and "because it is a left adjoint" (`Over.lean:14`; the adjunction needs binary products).
- **Alternatives:** check each against base imports and correct the false ones in the same edit.
- **What would decide it:** the base import graph, not visible here; open.
