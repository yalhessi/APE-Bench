# Decision context: out-of-date file references in CategoryTheory docstrings

Twelve sources, grouped under six decisions. Paths are at the base commit. Excerpts that collect
lines from several files keep the `path:line:` prefix that the search printed.

## 1. Scope of the edits (brief, open question 1)

### S1: `library_example`
- **Where:** `Mathlib/CategoryTheory/**` (bare file names in prose) and `Mathlib.lean` (the module list)
- **Excerpt:**
```
Mathlib/CategoryTheory/Limits/Cones.lean:35:For more results about the category of cones, see `cone_category.lean`.
Mathlib/CategoryTheory/Comma/Basic.lean:36:* `Over X`: the over category of the object `X` (developed in `Over.lean`).
Mathlib/CategoryTheory/Comma/Basic.lean:38:* `Arrow T`: the arrow category of the category `T` (developed in `Arrow.lean`).
Mathlib/CategoryTheory/Functor/Basic.lean:130:-- Natural isomorphisms are also provided in `Whiskering.lean`.
Mathlib/CategoryTheory/Functor/Category.lean:142:/-- Flip the arguments of a bifunctor. See also `Currying.lean`. -/
Mathlib/CategoryTheory/Abelian/Basic.lean:27:`NonPreadditiveAbelian.lean`. However, this fact is of little practical
Mathlib/CategoryTheory/Sites/Grothendieck.lean:611:given object for the given covering sieve. See `Sheaf.lean` for an equivalent sheaf condition
Mathlib.lean:2218:public import Mathlib.CategoryTheory.Abelian.NonPreadditive
Mathlib.lean:2351:public import Mathlib.CategoryTheory.Comma.Over.Basic
Mathlib.lean:2439:public import Mathlib.CategoryTheory.Functor.Currying
Mathlib.lean:2535:public import Mathlib.CategoryTheory.Limits.ConeCategory
Mathlib.lean:3141:public import Mathlib.CategoryTheory.Whiskering
```
- **Bears on:** other CategoryTheory prose (one line, `Functor/Basic.lean:130`, inside a file the
  brief lists) names files by a bare or Mathlib 3 style name whose module at base sits under a
  different name or directory, so it shows what a wider scope would take in. A search across
  `Mathlib/` for the brief's own old paths (`GroupTheory/Subgroup/Basic.lean`, `Tactic/Reassoc.lean`,
  `Limits/FunctorCategory.lean`, `Monoidal/Braided.lean`, `Adjunction/Over.lean`, `HasForget/`,
  `reassoc_axiom`, `Functor/Strict.lean`) returned only the places the brief lists. In the brief's
  files, the other full-path references (`Limits/HasLimits.lean:447`, `Monoidal/Mon_.lean:27` and
  `:38`) name modules that exist at base (`Mathlib.lean:2249`, `:6482`, `:2831`).

### S2: `earlier_decision`
- **Where:** Zulip `#mathlib4 > Broken file references`, 2024-11-04
- **Excerpt:**
```
Damiano Testa [maintainer] — 2024-11-04T07:20:20Z
Would having a `#assert_imported`/`#assert_not_imported` be something useful?  There would probably still have to be a linter checking that what looks like a file path/module name in comments has a corresponding command, but the machinery for the `#assert_xxx` already has its API.

Kim Morrison [maintainer] — 2024-11-04T07:25:38Z
Why not just a linter that directly reads the module docs?
```
- **Bears on:** maintainers proposed a tool to catch broken references, rather than fixing them one
  by one. The search results do not show whether the thread reached a conclusion.

## 2. How a file reference is spelled (the "shortened path" half of the capability)

### S3: `earlier_decision`
- **Where:** Zulip `#mathlib4 > Broken file references`, 2024-11-04
- **Excerpt:**
```
Eric Wieser [maintainer] — 2024-11-04T07:29:40Z
Should we standardize on the path spelling to refer to modules in docstrings?

Yaël Dillies [maintainer] — 2024-11-04T08:33:48Z
Eric Wieser said:  Should we standardize on the path spelling to refer to modules in docstrings?  That would be great, because the reason I introduce inconstencies when renaming files is that I only look for the module name, not the file name
```
- **Bears on:** two maintainers favour the `Mathlib/…/X.lean` path spelling over the dotted module
  name. Their reason is that people who rename a file search for one spelling. The results do not
  show whether this became a rule.

### S4: `counterexample`
- **Where:** several files (grep over `Mathlib/CategoryTheory` and `Mathlib/Tactic`)
- **Excerpt:**
```
Mathlib/CategoryTheory/Equivalence/Symmetry.lean:14:Using the calculus of mates in `Mathlib.CategoryTheory.Adjunction.Mates`, we prove that passing
Mathlib/CategoryTheory/Shift/CommShiftTwo.lean:25:a `TwistShiftData` structure (see the file `Mathlib.CategoryTheory.Shift.Twist`).
Mathlib/CategoryTheory/Triangulated/Opposite/Pretriangulated.lean:17:The shift on `Cᵒᵖ` was constructed in `Mathlib.CategoryTheory.Triangulated.Opposite.Basic`,
Mathlib/CategoryTheory/Triangulated/Opposite/Pretriangulated.lean:31:In the file `Mathlib.Triangulated.Opposite.Triangulated`, we show that `Cᵒᵖ` is
Mathlib/Tactic/CategoryTheory/Reassoc.lean:29:The `Mathlib.Tactic.CategoryTheory.IsoReassoc` extends `@[reassoc]` and `reassoc_of%`
Mathlib/Tactic/Linter/DirectoryDependency.lean:291:because modules in `Mathlib/Algebra/Notation.lean` cannot import modules in `Mathlib.Algebra` that are
```
- **Bears on:** at base, docstrings also name files by dotted module name, and one sentence mixes
  both spellings. This competes with the full-path spelling used in most of the brief's files (for
  example `Monoidal/Mon_.lean:27`, ``Please read the documentation in `Mathlib/Tactic/Attr/Register.lean` ``).

No written guidance (style note or library note) on the spelling turned up at base. A search of
`Mathlib/Tactic/Linter` for `.lean\``, "file path" and "module name" found no linter that checks
file references in docstrings.

## 3. What a reference should lead to, especially where the old material has no single home (open question 3)

### S5: `library_example`
- **Where:** `Mathlib.lean` and declaration sites, at base
- **Excerpt:**
```
Mathlib.lean:2364:public import Mathlib.CategoryTheory.ConcreteCategory.Basic
Mathlib.lean:2366:public import Mathlib.CategoryTheory.ConcreteCategory.BundledHom
Mathlib.lean:2370:public import Mathlib.CategoryTheory.ConcreteCategory.UnbundledHom
Mathlib.lean:2568:public import Mathlib.CategoryTheory.Limits.FunctorCategory.Basic
Mathlib.lean:2746:public import Mathlib.CategoryTheory.Localization.Predicate
Mathlib.lean:2777:public import Mathlib.CategoryTheory.Monoidal.Braided.Basic
Mathlib.lean:3295:public import Mathlib.Combinatorics.SimpleGraph.Subgraph
Mathlib.lean:6518:public import Mathlib.Tactic.CategoryTheory.Reassoc
Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean:597:def tensorμ (X₁ X₂ Y₁ Y₂ : C) : (X₁ ⊗ X₂) ⊗ Y₁ ⊗ Y₂ ⟶ (X₁ ⊗ Y₁) ⊗ X₂ ⊗ Y₂ :=
Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean:751:theorem associator_monoidal (X₁ X₂ X₃ Y₁ Y₂ Y₃ : C) :
Mathlib/CategoryTheory/Localization/Predicate.lean:393:theorem of_equivalence_target {E : Type*} [Category* E] (L' : C ⥤ E) (eq : D ≌ E)
Mathlib/Tactic/CategoryTheory/Reassoc.lean:88:syntax (name := reassoc) "reassoc" (" (" &"attr" " := " Parser.Term.attrInstance,* ")")? : attr
```
- **Bears on:** these are the base modules that hold the material behind several old references,
  where a single module holds it. The module list has no `GroupTheory.Subgroup.Basic`,
  `CategoryTheory.Adjunction.Over` or `CategoryTheory.HasForget.*`.

### S6: `library_example`
- **Where:** `Mathlib/Algebra/Group/Subgroup/` at base
- **Excerpt:**
```
Mathlib/Algebra/Group/Subgroup/Defs.lean:294:structure Subgroup (G : Type*) [Group G] extends Submonoid G where
Mathlib/Algebra/Group/Subgroup/Defs.lean:609:structure Normal : Prop where
Mathlib/Algebra/Group/Subgroup/Lattice.lean:261:instance : CompleteLattice (Subgroup G) :=
Mathlib/Algebra/Group/Subgroup/Map.lean:112:def map (f : G →* N) (H : Subgroup G) : Subgroup N :=
Mathlib.lean:425:public import Mathlib.Algebra.Group.Subgroup.Basic
```
- **Bears on:** the subgroup counterparts of what `Subgroupoid.lean` says it models (the complete
  lattice, images, normality) are spread over several modules. A `Subgroup/Basic` module also
  exists, and `Subgroupoid.lean:8` imports `Mathlib.Algebra.Group.Subgroup.Defs`.

### S7: `library_example`
- **Where:** `Mathlib/CategoryTheory/Comma/Over/Pullback.lean:135-157`;
  `Mathlib/CategoryTheory/LocallyCartesianClosed/Over.lean:292`
- **Excerpt:**
```
Mathlib/CategoryTheory/Comma/Over/Pullback.lean:135:section HasBinaryProducts
Mathlib/CategoryTheory/Comma/Over/Pullback.lean:136:variable [HasBinaryProducts C]
Mathlib/CategoryTheory/Comma/Over/Pullback.lean:149:def forgetAdjStar : forget X ⊣ star X := (coalgebraEquivOver X).symm.toAdjunction.comp (adj _)
Mathlib/CategoryTheory/Comma/Over/Pullback.lean:155:instance : (forget X).IsLeftAdjoint := ⟨_, ⟨forgetAdjStar X⟩⟩
Mathlib/CategoryTheory/Comma/Over/Pullback.lean:157:end HasBinaryProducts
Mathlib/CategoryTheory/LocallyCartesianClosed/Over.lean:292:def forgetAdjToOver (X : C) : Over.forget X ⊣ toOver X where
```
- **Bears on:** at base, two places exhibit `Over.forget X` as a left adjoint (the
  `Preserves/Over.lean` sentence names neither). The one with the `IsLeftAdjoint` instance sits
  under `[HasBinaryProducts C]`, which bears on where "See" could point. It also bears on the
  sentence around that reference, "already preserves all colimits because it is a left adjoint"
  (`Limits/Preserves/Over.lean:14`). My search for a colimit-preservation instance under the
  spelling `Over.forget` found none, and that search was not exhaustive.

### S8: `counterexample`
- **Where:** several files; `Mathlib.lean:2608-2621`
- **Excerpt:**
```
Mathlib/CategoryTheory/Limits/Shapes/BinaryProducts.lean:1149:In `Mathlib/CategoryTheory/Limits/Preserves/` we show
Mathlib/CategoryTheory/Limits/Over.lean:18:Note that the folder `CategoryTheory.Limits.Shapes.Constructions.Over` further shows that
Mathlib/CategoryTheory/Adjunction/Basic.lean:38:## Overview of the directory `CategoryTheory.Adjunction`
Mathlib/CategoryTheory/Adjunction/Basic.lean:40:* Adjoint lifting theorems are in the directory `Lifting`.
Mathlib/Analysis/Calculus/FDeriv/Defs.lean:36:Other files in the folder `Analysis/Calculus/FDeriv/` contain the usual formulas
Mathlib/Topology/OpenPartialHomeomorph/Defs.lean:26:partial homeomorphisms can be found in other files under `Mathlib/Topology/PartialHomeomorph/`.
Mathlib/Algebra/Ring/Subsemiring/Pointwise.lean:20:This file is almost identical to the files `Mathlib/Algebra/GroupWithZero/Submonoid/Pointwise.lean`
Mathlib.lean:2608:public import Mathlib.CategoryTheory.Limits.Preserves.Shapes.AbelianImages
Mathlib.lean:2609:public import Mathlib.CategoryTheory.Limits.Preserves.Shapes.BinaryProducts
Mathlib.lean:2621:public import Mathlib.CategoryTheory.Limits.Preserves.Shapes.Zero
```
- **Bears on:** at base, `preserves/shapes.lean` corresponds to a directory of fourteen modules
  (`Mathlib.lean:2608-2621`). The library points at a group of files in competing ways: a path
  directory with a trailing slash, a dotted folder name, a shortened folder, or a list of files.

## 4. Whether the statements around a reference are brought up to date (open question 2)

### S9: `library_example`
- **Where:** `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean:1-5`
- **Excerpt:**
```
module

public import Mathlib.CategoryTheory.Bicategory.Strict.Pseudofunctor

deprecated_module (since := "2025-10-02")
```
- **Bears on:** the file the TODO in `StrictPseudofunctor.lean` names does exist at base. It is a
  deprecated module (since 2025-10-02) that re-exports `Bicategory/Strict/Pseudofunctor.lean`. That
  module's docstring, "# Pseudofunctors from strict bicategory", is about other material. This
  bears on whether the TODO's plan is still accurate and on whether its path is only shortened.

### S10: `earlier_decision`
- **Where:** Zulip `#mathlib4 > Bundled in CategoryTheory`, 2025-11-17 to 2025-11-30
- **Excerpt:**
```
Calle Sönne — 2025-11-17T22:37:33Z
`Bundled` seems to be used only 4-5 times in mathlib, and both `BundledHom` and `UnbundledHom` are used 0 times outside of the files they have been defined in. Should these be/are these in the process of being deprecated? The only time I see `Bundled` being used is to define subcategories of `Cat` (e.g. `Grpd` or `Quiver`, which should all be replaced with some bicategorical notion at some point a…

Calle Sönne — 2025-11-17T22:46:44Z
If so, can I remove the final instances of bundled and deprecate these files?

Kim Morrison [maintainer] — 2025-11-17T23:16:27Z
Yes please!

Aaron Anderson [maintainer] — 2025-11-30T19:06:57Z
I'm trying it here: #32285
```
- **Bears on:** the `Bundled.lean` note ("this structure will be deprecated in the future") and its
  pointers to the files that give `Category` instances. A maintainer endorsed deprecating
  `BundledHom` and `UnbundledHom`, because they are unused, and removing `Bundled` was then being
  tried. At base `structure Bundled` (`ConcreteCategory/Bundled.lean:37`) carries no deprecation.
  `#mathlib4 > Reorganizing the ModelTheory Folder` (2025-11-30) also discusses removing
  `CategoryTheory.Bundled`.

### S11: `written_guidance`
- **Where:** `Mathlib/CategoryTheory/ConcreteCategory/Basic.lean:28-37`
- **Excerpt:**
```
## Implementation notes

We are currently switching over from `HasForget` to a new class `ConcreteCategory`,
see Zulip thread: https://leanprover.zulipchat.com/#narrow/channel/287929-mathlib4/topic/Concrete.20category.20class.20redesign

Previously, `ConcreteCategory` had the same definition as now `HasForget`; the coercion of
objects/morphisms to types/functions was defined as `(forget C).obj` and `(forget C).map`
respectively. This leads to defeq issues since existing `CoeFun` and `FunLike` instances provide
their own casts. We replace this with a less bundled `ConcreteCategory` that does not directly
use these coercions.
```
- **Bears on:** three references send readers here "for more details": `Bundled.lean:23` and the
  two deprecation messages. This is what the file says about the switch, and neither it nor the
  class docstring (`Basic.lean:237-247`) spells out building a category by hand. The phrase
  "category manually" occurs at base only in the three places the brief lists. This bears on
  open question 2 and on what the deprecation messages lead to.

### S12: `consumer`
- **Where:** `Mathlib/Tactic/CategoryTheory/Reassoc.lean:8-9`
- **Excerpt:**
```
public import Mathlib.CategoryTheory.Functor.Basic
public meta import Mathlib.CategoryTheory.Functor.Basic
```
- **Bears on:** the comment at `Functor/Basic.lean:64-65` justifies writing
  `Functor.map_comp_assoc` by hand: "we will import this file into" the reassoc file. At base the
  reassoc file lives at `Mathlib/Tactic/CategoryTheory/Reassoc.lean` and does import
  `Functor.Basic`, so this bears on whether the surrounding claim still holds.

## 5. The two deprecation messages (`BundledHom`, `UnbundledHom`)

S11 shows what the current target says, and S10 gives the maintainers' stated reason for the
deprecation (no uses). I found no review comment or Zulip message that gives a reason for the
messages' wording or for which file they should name.

## 6. Registration with automation

No linter or other mechanism at base checks file references in docstrings (see the note under
decision 2). S2 records that maintainers proposed one in 2024. Nothing else found.
