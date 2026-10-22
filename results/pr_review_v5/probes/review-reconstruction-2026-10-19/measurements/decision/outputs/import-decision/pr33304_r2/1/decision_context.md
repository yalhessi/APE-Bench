# Decision context: out-of-date file references in CategoryTheory documentation

All paths are at the base commit. Ten sources (S1-S10). No source names a base location for any of
the old references listed in the brief; finding where that material now lives is left to the
designer.

## 1. Breadth of the edits (open question 1)

**S1** · kind: `library_example` · other file references in the thirteen files, outside the listed places

```
Mathlib/CategoryTheory/Functor/Basic.lean:130:-- Natural isomorphisms are also provided in `Whiskering.lean`.
Mathlib/CategoryTheory/Limits/HasLimits.lean:446:-- `hasLimitCompEquivalence` and `hasLimitOfCompEquivalence`
Mathlib/CategoryTheory/Limits/HasLimits.lean:447:-- are proved in `Mathlib/CategoryTheory/Adjunction/Limits.lean`.
Mathlib/CategoryTheory/Monoidal/Mon_.lean:27:Please read the documentation in `Mathlib/Tactic/Attr/Register.lean` for full details.
Mathlib/CategoryTheory/Monoidal/Mon_.lean:35:  available in https://github.com/leanprover-community/mathlib3/pull/3463)
Mathlib/CategoryTheory/Monoidal/Mon_.lean:38:  in `Mathlib/CategoryTheory/Monoidal/Internal/Module.lean`.)
Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean:44:and `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean`.
```

Bears on whether the edit stops at the listed places: the same files hold further references,
one of them shortened (`Whiskering.lean`); whether any of these is out of date was not checked.

**S2** · kind: `library_example` · shortened references elsewhere in `Mathlib/CategoryTheory`

```
Mathlib/CategoryTheory/Abelian/Basic.lean:27:`NonPreadditiveAbelian.lean`. However, this fact is of little practical
Mathlib/CategoryTheory/Bicategory/Functor/Lax.lean:34:since lax functors had not yet been added (e.g `FunctorBicategory.lean`). A possible project would
Mathlib/CategoryTheory/Functor/Category.lean:142:/-- Flip the arguments of a bifunctor. See also `Currying.lean`. -/
Mathlib/CategoryTheory/Limits/EssentiallySmall.lean:16:See also the file `FinallySmall.lean` for more general results.
Mathlib/CategoryTheory/Limits/Shapes/IsTerminal.lean:20:objects are defined in `Terminal.lean`.
Mathlib/CategoryTheory/Monoidal/Free/Basic.lean:23:theorem. Both of these properties are proved in the file `Coherence.lean`.
Mathlib/CategoryTheory/Sites/Grothendieck.lean:598:-- This is used extensively in `Plus.lean`, etc.
Mathlib/CategoryTheory/Sites/Grothendieck.lean:599:-- We place this definition here as it will be used in `Sheaf.lean` as well.
Mathlib/CategoryTheory/Sites/Pretopology.lean:21:The pretopology associated to a topological space is defined in `Spaces.lean`.
```

Bears on how far "shortened path" extends beyond the listed files: a regex search for backticked
capitalised `….lean` references in `Mathlib/CategoryTheory` found 140, of which 113 start with
`Mathlib/`, 2 with `Counterexamples/`, and 25 have no root directory (the brief's own places
included); lower-case paths such as `preserves/shapes.lean` were outside that search.

**Mechanism: nothing found.** A search of `Mathlib/Tactic/Linter` at base for a check on file paths
in docstrings or comments returned nothing; no automation was found that detects or repairs such
references, at the scale of these files or of Mathlib. The Zulip thread under S3 contains proposals
for tooling, none of which is shown there as adopted.

No review comment or Zulip message was found that argues for or against fixing references beyond a
given list in one change.

## 2. How a repaired reference is expressed

**S3** · kind: `earlier_decision` · Zulip `#mathlib4` > "Broken file references", 2024-11-04

```
Eric Wieser [maintainer] — 2024-11-04T07:29:40Z
Should we standardize on the path spelling to refer to modules in docstrings?

Yaël Dillies [maintainer] — 2024-11-04T08:33:48Z
Eric Wieser said:  Should we standardize on the path spelling to refer to modules in docstrings?
That would be great, because the reason I introduce inconstencies when renaming files is that I
only look for the module name, not the file name
```

Eric Wieser's message is a question; Yaël Dillies answers it in favour, with a reason (a search by
one spelling misses references in the other when files are renamed); the excerpt does not show the
standard being adopted.

**S4** · kind: `library_example` · references by full path from the repository root

```
Mathlib/CategoryTheory/Adjunction/Basic.lean:72:* The file `Mathlib/CategoryTheory/Monad/Adjunction.lean` develops the basic relationship between
Mathlib/CategoryTheory/Galois/Basic.lean:33:This is proven in `Mathlib/CategoryTheory/Galois/Equivalence.lean`.
Mathlib/CategoryTheory/Limits/ConeCategory.lean:17:instance of `Cone`, please refer to `Mathlib/CategoryTheory/Limits/Cones.lean`.
Mathlib/CategoryTheory/SmallObject/Basic.lean:52:is done in the file `Mathlib/CategoryTheory/SmallObject/TransfiniteIteration.lean`.
Mathlib/CategoryTheory/Abelian/Pseudoelements.lean:413:`Counterexamples/Pseudoelement.lean` for details. -/
```

Shows the most frequent spelling in CategoryTheory (113 of the 140 in S2's count), including a path
rooted outside `Mathlib/`.

**S5** · kind: `counterexample` · references by dotted module name

```
Mathlib/CategoryTheory/Equivalence/Symmetry.lean:14:Using the calculus of mates in `Mathlib.CategoryTheory.Adjunction.Mates`, we prove that passing
Mathlib/CategoryTheory/Triangulated/Opposite/Pretriangulated.lean:17:The shift on `Cᵒᵖ` was constructed in `Mathlib.CategoryTheory.Triangulated.Opposite.Basic`,
```

A competing spelling for a module reference exists in the same part of the library (a narrow
search, `see`/`See`/`in` followed by a dotted name, found these two).

**S6** · kind: `counterexample` · sending the reader to a declaration rather than (or as well as) a file

```
Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean:16:To a strict pseudofunctor between strict bicategories we can associate a functor between the
Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean:17:underlying categories, see `StrictPseudofunctor.toFunctor`.
Mathlib/CategoryTheory/Limits/HasLimits.lean:529:of a right adjoint to the constant functor `C ⥤ (J ⥤ C)` is obtained in
Mathlib/CategoryTheory/Limits/HasLimits.lean:530:the file `Mathlib/CategoryTheory/Limits/ConeCategory.lean`: see the lemma
Mathlib/CategoryTheory/Limits/HasLimits.lean:531:`hasLimitsOfShape_iff_isLeftAdjoint_const`. In the definitions below, given an
Mathlib/CategoryTheory/Enriched/HomCongr.lean:23:`Mathlib/CategoryTheory/HomCongr.lean` and that for sorts in
Mathlib/CategoryTheory/Enriched/HomCongr.lean:24:`Mathlib/Logic/Equiv/Defs.lean` (cf. `Equiv.arrowCongr`). Note, however, that
Mathlib/CategoryTheory/Bicategory/Coherence.lean:163:  -- p ≠ nil required! See the docstring of `normalizeAux`.
```

Shows the library's other way of directing a reader, by naming a declaration in backticks, alone
(lines 16-17, 163) or beside a file path (530-531, 23-24); the passages in the brief at
`Localization/Equivalence.lean:14` and `Monoidal/Mon_.lean:268` already pair a file reference with
a named declaration (`Localization.of_equivalence_target`, `tensorμ`), and `Limits/HasLimits.lean:708`
names the attribute `reassoc` next to its file reference.

See also S2 (shortened paths, the form the brief calls out, as it occurs elsewhere).

## 3. What a passage leads to when the material has no single home (open question 3)

**S7** · kind: `library_example` · references to a family of files or a directory

```
Mathlib/Data/Nat/Factorization/Defs.lean:35:  `Mathlib/RingTheory/UniqueFactorizationDomain/`.
Mathlib/Data/Set/Operations.lean:20:More advanced theorems about these definitions are located in other files in `Mathlib/Data/Set`.
Mathlib/GroupTheory/Perm/Finite.lean:17:of those in `Mathlib/Logic/Equiv/Basic.lean` and other files in `Mathlib/GroupTheory/Perm/*`.
Mathlib/RingTheory/MvPolynomial/Expand.lean:15:available in `Mathlib.Algebra.*`.
```

Shows what is possible when no single file holds the material: a directory with or without a
trailing slash, a glob, or a dotted prefix; S6 (naming declarations) shows the other form seen.

**S8** · kind: `mechanism` · `Mathlib/Tactic/Linter/DeprecatedModule.lean:11`

````
/-!
# The `deprecated.module` linter

The `deprecated.module` linter emits a warning when a file that has been renamed or split
is imported.

The usage is as follows. Write
```lean
import B
...
import Z

deprecated_module "Optional string here with further details" (since := "yyyy-mm-dd")
```
in module `A` with the expectation that `A` contains nothing else.
This triggers the `deprecated.module` linter to notify every file with `import A`
to instead import the *direct imports* of `A`, that is `B, ..., Z`.
````

Bears on how a renamed or split file is recorded at base (a stub naming its successor modules as
imports), which is one place a contributor can learn where split material went, and on the
premise of the StrictPseudofunctor TODO, which speaks of a deprecated file awaiting removal.

## 4. Whether the statements around a reference are brought up to date (open question 2)

**S9** · kind: `written_guidance` · `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean:32`, beside `Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean:22`

```
Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean:32:@[deprecated "The preferred method for talking about concrete categories is to implement the \
Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean:33:category manually and then provide the `ConcreteCategory` instance on top of this. See \
Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean:34:`ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean:35:structure BundledHom where

Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean:22:Note: this structure will be deprecated in the future in favor of defining the category manually
Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean:23:and then providing the `ConcreteCategory` instance on top of this. See `ConcreteCategory/Basic.lean`
Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean:24:for more details.
```

Bears on whether the statements around the Bundled references (the instances "we provide" in the
`HasForget` files, the future deprecation) describe the base state: at base `BundledHom` and
`UnbundledHom` carry deprecations dated 2025-11-17, while `Bundled` itself carries none in the base
text.

S8 also bears here, on the premise of the StrictPseudofunctor TODO.

Nothing was found on whether a reference fix should also revise the claims next to it: the
`Limits/FunctorCategory/{Filtered,Finite}.lean` reasons ("that file shouldn't import …"), the
`Functor/Basic.lean:64-65` reason for stating `Functor.map_comp_assoc` by hand, or the plan in the
StrictPseudofunctor TODO. No review comment or Zulip message on this was found.

## 5. Wording of the two deprecation messages

**S10** · kind: `counterexample` · other deprecation messages at base

```
Mathlib/Algebra/Category/ModuleCat/Sheaf/Generators.lean:126:@[deprecated "Use the lemma `IsFiniteType.exists_localGeneratorsData` instead."
Mathlib/Algebra/Polynomial/Splits.lean:47:@[deprecated "Use `Splits.C` instead." (since := "2025-11-24")]
Mathlib/Analysis/Normed/Module/ENormedSpace.lean:51:@[deprecated "Use ENormedAddCommMonoid or talk to the Carleson project" (since := "2025-05-07")]
Mathlib/CategoryTheory/Monoidal/Closed/Cartesian.lean:104:@[deprecated "No replacement: use `asIso (coprodComparison (tensorLeft Z) _ _)` instead."
Mathlib/CategoryTheory/Monoidal/OfHasFiniteProducts.lean:85:@[deprecated "Use the `CartesianMonoidalCategory.associator_hom_...` lemmas"
```

Bears on what a deprecation message points to: these name declarations or describe an approach,
while a search for messages ending in a `.lean` path or dotted `Mathlib.` module name before
`(since` found only `BundledHom.lean:34` and `UnbundledHom.lean:31` (S9).

## 6. Decisions with nothing found

The abstraction and its generality, the form of statements, names, the API, registration with
automation, placement and the proof route do not arise: the change touches only prose. No source
was gathered for them.
