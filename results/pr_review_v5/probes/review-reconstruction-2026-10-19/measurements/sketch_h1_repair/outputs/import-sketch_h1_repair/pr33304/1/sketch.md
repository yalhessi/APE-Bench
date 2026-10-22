# Sketch: fix stale file references in CategoryTheory documentation

A prose-only change, so there is no Lean here. Paths marked "recalled" come from memory of Mathlib, not from `base/`.

### 1. Scope
- **Choice:** the listed places, plus any other file reference in the same files shown broken at base. Valid shortened references elsewhere (`Whiskering.lean`, `Functor/Basic.lean:130`) stay; no CategoryTheory-wide sweep.
- **Alternatives:** expand every shortened reference in the touched files; sweep the 25 shortened references in CategoryTheory (S2); a linter instead of hand edits.
- **References:** S1, S2; `Monoidal/Mon_.lean:27,35`.
- **What would decide it:** open; no recorded preference on breadth.

### 2. Spelling of a repaired reference
- **Choice:** backticked path from the repository root, `Mathlib/CategoryTheory/…/X.lean`.
- **Alternatives:** dotted module name (S5); path relative to a directory; a declaration name alone.
- **References:** S4 (113 of 140); the files' own other references, `Limits/HasLimits.lean:447,530`, `Monoidal/Mon_.lean:38`, `Groupoid/Subgroupoid.lean:44`.
- **What would decide it:** an adopted standard; S3 asks for one, with a reason, but does not show it adopted.

### 3. Partial references that already resolve
- **Choice:** expand them: `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean` (`ConcreteCategory/Bundled.lean:23`), `Mathlib/CategoryTheory/Localization/Predicate.lean` (`Localization/Equivalence.lean:14`); `Functor/Strict.lean` in decision 8.
- **Alternatives:** leave them; they resolve under `Mathlib/CategoryTheory/`, and `Equivalence.lean:14` already names `Localization.of_equivalence_target`.
- **References:** both targets exist at base (imported at `Localization/Equivalence.lean:8`, `ConcreteCategory/BundledHom.lean:8`); S3's reason (a rename search by one spelling misses the other).
- **What would decide it:** whether one searchable spelling is wanted (S3); otherwise open.

### 4. Moved files with one successor
- **Choice:**
  - `ConcreteCategory/Bundled.lean:17,19` → `Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean`, `…/BundledHom.lean`;
  - `Limits/FunctorCategory/Filtered.lean:14`, `Finite.lean:16` → `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean`;
  - `Monoidal/Mon_.lean:269,283` → `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`;
  - `Functor/Basic.lean:65` → `Mathlib/Tactic/CategoryTheory/Reassoc.lean` (recalled);
  - `Groupoid/Subgroupoid.lean:43` → `Mathlib/Algebra/Group/Subgroup/Basic.lean` (recalled).
- **Alternatives:** for Subgroupoid, the directory `Mathlib/Algebra/Group/Subgroup/`, since the material copied (lattice, map/comap, normality) is now split over several files.
- **References:** seen as imports: `Filtered.lean:8`, `Finite.lean:8`, `Mon_.lean:9`, `Subgroupoid.lean:8` (`…Subgroup.Defs`); the ConcreteCategory files are in the packet.
- **What would decide it:** existence of the two recalled paths at base, and that Reassoc imports `Functor.Basic` (keeping the comment's reason true); for Subgroupoid, where `Subgroup`'s lattice and map/comap live at base.

### 5. The `reassoc` pointer in `Limits/HasLimits.lean:709`
- **Choice:** "(see `Mathlib/Tactic/CategoryTheory/Reassoc.lean`)", the same target as decision 4.
- **Alternatives:** drop the parenthetical, since line 708 already names `reassoc`; name the attribute beside the path. Turning this misplaced comment (it is `colimit.ι_desc`'s docstring, lines 702–710) into a section comment is out of scope.
- **References:** S6; `HasLimits.lean:702-711`.
- **What would decide it:** open.

### 6. Preserved (co)limits of specific shapes (`Limits/Preserves/Limits.lean:18-19`)
- **Choice:** the directory `Mathlib/CategoryTheory/Limits/Preserves/Shapes/` (recalled: one file per shape, e.g. `Products.lean`, `Pullbacks.lean`).
- **Alternatives:** one or two representative files; a glob; a dotted prefix.
- **References:** S7 (`Mathlib/RingTheory/UniqueFactorizationDomain/`).
- **What would decide it:** whether one file at base gathers the shapes.

### 7. `Over.forget X` as a left adjoint (`Limits/Preserves/Over.lean:14-15`)
- **Choice:** declaration plus file: "(`Over.forgetAdjStar`, in `Mathlib/CategoryTheory/Comma/Over/Pullback.lean`)" — recalled, unchecked.
- **Alternatives:** path only; name the instance by which `Over.forget` preserves or creates colimits, which holds without `HasBinaryProducts`, unlike the adjunction.
- **References:** S6 (declaration beside path, `HasLimits.lean:530-531`).
- **What would decide it:** where `forgetAdjStar` lives at base; rewording "because" is decision 10.

### 8. StrictPseudofunctor TODO (`Bicategory/Functor/StrictPseudofunctor.lean:21-22`)
- **Choice:** spell both as `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`, keeping the TODO if a `deprecated_module` stub still sits there; if it is gone, the condition is met: reword to "Rename this file to …" and rename in a separate PR.
- **Alternatives:** rename here (not documentation); delete the TODO.
- **References:** S8.
- **What would decide it:** whether that stub exists at base.

### 9. Deprecation messages (`ConcreteCategory/BundledHom.lean:32-34`, `UnbundledHom.lean:29-31`)
- **Choice:** change only the path, to `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`; `since` unchanged. The warning is read in downstream files, where the partial path is least clear.
- **Alternatives:** name the class (`CategoryTheory.ConcreteCategory`), the usual form in S10; leave them out.
- **References:** S9, S10.
- **What would decide it:** open.

### 10. Claims next to a reference
- **Choice:** unchanged; each stays true once its target is fixed: `BundledHom.lean:69` still provides `Category (Bundled c)`; `Bundled` itself is not deprecated (`Bundled.lean:37`), so "will be deprecated" holds; FunctorCategory/Basic not importing `Filtered`/`FiniteProducts` is to be checked.
- **Alternatives:** note in `Bundled.lean` that `BundledHom`/`UnbundledHom` are deprecated since 2025-11-17; qualify Over.lean's "because".
- **References:** S9; `BundledHom.lean:32,69`.
- **What would decide it:** open (§4 found nothing).
