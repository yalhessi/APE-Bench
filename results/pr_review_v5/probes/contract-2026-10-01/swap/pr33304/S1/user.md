# Pull request #33304

**Title:** doc(CategoryTheory): fix file refs

**Description:**
(no description provided)

**Changed files:**
  - `Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean`
  - `Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean`
  - `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean`
  - `Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean`
  - `Mathlib/CategoryTheory/Functor/Basic.lean`
  - `Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean`
  - `Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean`
  - `Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean`
  - `Mathlib/CategoryTheory/Limits/HasLimits.lean`
  - `Mathlib/CategoryTheory/Limits/Preserves/Limits.lean`
  - `Mathlib/CategoryTheory/Limits/Preserves/Over.lean`
  - `Mathlib/CategoryTheory/Localization/Equivalence.lean`
  - `Mathlib/CategoryTheory/Monoidal/Mon_.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33304 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: doc(CategoryTheory): fix file refs
- description: (not recoverable at review start)
- changed files: Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean, Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean, Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean, Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean, Mathlib/CategoryTheory/Functor/Basic.lean, Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean, Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean, Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean, Mathlib/CategoryTheory/Limits/HasLimits.lean, Mathlib/CategoryTheory/Limits/Preserves/Limits.lean, Mathlib/CategoryTheory/Limits/Preserves/Over.lean, Mathlib/CategoryTheory/Localization/Equivalence.lean, Mathlib/CategoryTheory/Monoidal/Mon_.lean

## Objects

### `module_doc in StrictPseudofunctor.lean` (module_doc, modified) [575e0232ac]
- file: `Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Strict pseudofunctors

In this file we introduce the notion of strict pseudofunctors, which are pseudofunctors such
that `mapId` and `mapComp` are given by `eqToIso _`.

To a strict pseudofunctor between strict bicategories we can associate a functor between the
underlying categories, see `StrictPseudofunctor.toFunctor`.

## TODO

Once the deprecated `Functor/Strict.lean` is removed we should rename this file to
`Functor/Strict.lean`.

-/
```
- as the PR leaves it:
```lean
/-!
# Strict pseudofunctors

In this file we introduce the notion of strict pseudofunctors, which are pseudofunctors such
that `mapId` and `mapComp` are given by `eqToIso _`.

To a strict pseudofunctor between strict bicategories we can associate a functor between the
underlying categories, see `StrictPseudofunctor.toFunctor`.

## TODO

Once the deprecated `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean` is removed we should
rename this file to `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`.

-/
```

### `module_doc in Bundled.lean` (module_doc, modified) [df499d9032]
- file: `Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Bundled types

`Bundled c` provides a uniform structure for bundling a type equipped with a type class.

We provide `Category` instances for these in
`Mathlib/CategoryTheory/HasForget/UnbundledHom.lean`
(for categories with unbundled homs, e.g. topological spaces)
and in `Mathlib/CategoryTheory/HasForget/BundledHom.lean`
(for categories with bundled homs, e.g. monoids).

Note: this structure will be deprecated in the future in favor of defining the category manually
and then providing the `ConcreteCategory` instance on top of this. See `ConcreteCategory/Basic.lean`
for more details.
-/
```
- as the PR leaves it:
```lean
/-!
# Bundled types

`Bundled c` provides a uniform structure for bundling a type equipped with a type class.

We provide `Category` instances for these in
`Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean`
(for categories with unbundled homs, e.g. topological spaces)
and in `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean`
(for categories with bundled homs, e.g. monoids).

Note: this structure will be deprecated in the future in favor of defining the category manually
and then providing the `ConcreteCategory` instance on top of this. See
`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean` for more details.
-/
```

### `CategoryTheory.BundledHom` (structure, modified) [593c012b50]
- file: `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean`; changed: attributes:modified
- before the PR:
```lean
@[deprecated "The preferred method for talking about concrete categories is to implement the \
category manually and then provide the `ConcreteCategory` instance on top of this. See \
`ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
structure BundledHom where
  /-- the underlying map of a bundled morphism -/
  toFun : ∀ {α β : Type u} (Iα : c α) (Iβ : c β), hom Iα Iβ → α → β
  /-- the identity as a bundled morphism -/
  id : ∀ {α : Type u} (I : c α), hom I I
  /-- composition of bundled morphisms -/
  comp : ∀ {α β γ : Type u} (Iα : c α) (Iβ : c β) (Iγ : c γ), hom Iβ Iγ → hom Iα Iβ → hom Iα Iγ
  /-- a bundled morphism is determined by the underlying map -/
  hom_ext : ∀ {α β : Type u} (Iα : c α) (Iβ : c β), Function.Injective (toFun Iα Iβ) := by
    cat_disch
  /-- compatibility with identities -/
  id_toFun : ∀ {α : Type u} (I : c α), toFun I I (id I) = _root_.id := by cat_disch
  /-- compatibility with the composition -/
  comp_toFun :
    ∀ {α β γ : Type u} (Iα : c α) (Iβ : c β) (Iγ : c γ) (f : hom Iα Iβ) (g : hom Iβ Iγ),
      toFun Iα Iγ (comp Iα Iβ Iγ g f) = toFun Iβ Iγ g ∘ toFun Iα Iβ f := by
    cat_disch
```
- as the PR leaves it:
```lean
@[deprecated "The preferred method for talking about concrete categories is to implement the \
category manually and then provide the `ConcreteCategory` instance on top of this. See \
`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
structure BundledHom where
  /-- the underlying map of a bundled morphism -/
  toFun : ∀ {α β : Type u} (Iα : c α) (Iβ : c β), hom Iα Iβ → α → β
  /-- the identity as a bundled morphism -/
  id : ∀ {α : Type u} (I : c α), hom I I
  /-- composition of bundled morphisms -/
  comp : ∀ {α β γ : Type u} (Iα : c α) (Iβ : c β) (Iγ : c γ), hom Iβ Iγ → hom Iα Iβ → hom Iα Iγ
  /-- a bundled morphism is determined by the underlying map -/
  hom_ext : ∀ {α β : Type u} (Iα : c α) (Iβ : c β), Function.Injective (toFun Iα Iβ) := by
    cat_disch
  /-- compatibility with identities -/
  id_toFun : ∀ {α : Type u} (I : c α), toFun I I (id I) = _root_.id := by cat_disch
  /-- compatibility with the composition -/
  comp_toFun :
    ∀ {α β γ : Type u} (Iα : c α) (Iβ : c β) (Iγ : c γ) (f : hom Iα Iβ) (g : hom Iβ Iγ),
      toFun Iα Iγ (comp Iα Iβ Iγ g f) = toFun Iβ Iγ g ∘ toFun Iα Iβ f := by
    cat_disch
```

### `CategoryTheory.UnbundledHom` (class, modified) [18f696bdc3]
- file: `Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean`; changed: attributes:modified
- before the PR:
```lean
@[deprecated "The preferred method for talking about concrete categories is to implement the \
category manually and then provide the `ConcreteCategory` instance on top of this. See \
`ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
class UnbundledHom {c : Type u → Type u} (hom : ∀ ⦃α β⦄, c α → c β → (α → β) → Prop) : Prop where
  hom_id : ∀ {α} (ia : c α), hom ia ia id
  hom_comp : ∀ {α β γ} {Iα : c α} {Iβ : c β} {Iγ : c γ} {g : β → γ} {f : α → β} (_ : hom Iβ Iγ g)
      (_ : hom Iα Iβ f), hom Iα Iγ (g ∘ f)
```
- as the PR leaves it:
```lean
@[deprecated "The preferred method for talking about concrete categories is to implement the \
category manually and then provide the `ConcreteCategory` instance on top of this. See \
`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
class UnbundledHom {c : Type u → Type u} (hom : ∀ ⦃α β⦄, c α → c β → (α → β) → Prop) : Prop where
  hom_id : ∀ {α} (ia : c α), hom ia ia id
  hom_comp : ∀ {α β γ} {Iα : c α} {Iβ : c β} {Iγ : c γ} {g : β → γ} {f : α → β} (_ : hom Iβ Iγ g)
      (_ : hom Iα Iβ f), hom Iα Iγ (g ∘ f)
```

### `section in Basic.lean` (command, modified) [72cf2d3cda]
- file: `Mathlib/CategoryTheory/Functor/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
attribute [grind _=_] Functor.map_comp

-- Note: We manually add this lemma which could be generated by `reassoc`,
-- since we will import this file into `Mathlib/Tactic/Reassoc.lean`.
```
- as the PR leaves it:
```lean
attribute [grind _=_] Functor.map_comp

-- Note: We manually add this lemma which could be generated by `reassoc`,
-- since we will import this file into `Mathlib/Tactic/CategoryTheory/Reassoc.lean`.
```

### `module_doc in Subgroupoid.lean` (module_doc, modified) [8d6373e12d]
- file: `Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Subgroupoid

This file defines subgroupoids as `structure`s containing the subsets of arrows and their
stability under composition and inversion.
Also defined are:

* containment of subgroupoids is a complete lattice;
* images and preimages of subgroupoids under a functor;
* the notion of normality of subgroupoids and its stability under intersection and preimage;
* compatibility of the above with `CategoryTheory.Groupoid.vertexGroup`.


## Main definitions

Given a type `C` with associated `groupoid C` instance.

* `CategoryTheory.Subgroupoid C` is the type of subgroupoids of `C`
* `CategoryTheory.Subgroupoid.IsNormal` is the property that the subgroupoid is stable under
  conjugation by arbitrary arrows, _and_ that all identity arrows are contained in the subgroupoid.
* `CategoryTheory.Subgroupoid.comap` is the "preimage" map of subgroupoids along a functor.
* `CategoryTheory.Subgroupoid.map` is the "image" map of subgroupoids along a functor _injective on
  objects_.
* `CategoryTheory.Subgroupoid.vertexSubgroup` is the subgroup of the *vertex group* at a given
  vertex `v`, assuming `v` is contained in the `CategoryTheory.Subgroupoid` (meaning, by definition,
  that the arrow `𝟙 v` is contained in the subgroupoid).

## Implementation details

The structure of this file is copied from/inspired by `Mathlib/GroupTheory/Subgroup/Basic.lean`
and `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean`.

## TODO

* Equivalent inductive characterization of generated (normal) subgroupoids.
* Characterization of normal subgroupoids as kernels.
* Prove that `CategoryTheory.Subgroupoid.full` and `CategoryTheory.Subgroupoid.disconnect` preserve
  intersections (and `CategoryTheory.Subgroupoid.disconnect` also unions)

## Tags

category theory, groupoid, subgroupoid
-/
```
- as the PR leaves it:
```lean
/-!
# Subgroupoid

This file defines subgroupoids as `structure`s containing the subsets of arrows and their
stability under composition and inversion.
Also defined are:

* containment of subgroupoids is a complete lattice;
* images and preimages of subgroupoids under a functor;
* the notion of normality of subgroupoids and its stability under intersection and preimage;
* compatibility of the above with `CategoryTheory.Groupoid.vertexGroup`.


## Main definitions

Given a type `C` with associated `groupoid C` instance.

* `CategoryTheory.Subgroupoid C` is the type of subgroupoids of `C`
* `CategoryTheory.Subgroupoid.IsNormal` is the property that the subgroupoid is stable under
  conjugation by arbitrary arrows, _and_ that all identity arrows are contained in the subgroupoid.
* `CategoryTheory.Subgroupoid.comap` is the "preimage" map of subgroupoids along a functor.
* `CategoryTheory.Subgroupoid.map` is the "image" map of subgroupoids along a functor _injective on
  objects_.
* `CategoryTheory.Subgroupoid.vertexSubgroup` is the subgroup of the *vertex group* at a given
  vertex `v`, assuming `v` is contained in the `CategoryTheory.Subgroupoid` (meaning, by definition,
  that the arrow `𝟙 v` is contained in the subgroupoid).

## Implementation details

The structure of this file is copied from/inspired by `Mathlib/Algebra/Group/Subgroup/Basic.lean`
and `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean`.

## TODO

* Equivalent inductive characterization of generated (normal) subgroupoids.
* Characterization of normal subgroupoids as kernels.
* Prove that `CategoryTheory.Subgroupoid.full` and `CategoryTheory.Subgroupoid.disconnect` preserve
  intersections (and `CategoryTheory.Subgroupoid.disconnect` also unions)

## Tags

category theory, groupoid, subgroupoid
-/
```

### `module_doc in Filtered.lean` (module_doc, modified) [44d4f69100]
- file: `Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Functor categories have filtered colimits when the target category does

These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory.lean` because
that file shouldn't import `Mathlib/CategoryTheory/Limits/Filtered.lean`.
-/
```
- as the PR leaves it:
```lean
/-!
# Functor categories have filtered colimits when the target category does

These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean` because
that file shouldn't import `Mathlib/CategoryTheory/Limits/Filtered.lean`.
-/
```

### `module_doc in Finite.lean` (module_doc, modified) [15ce692e21]
- file: `Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean`; changed: documentation:modified
- before the PR:
```lean
/-!

# Functor categories have finite limits when the target category does

These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory.lean` because
that file shouldn't import `Mathlib/CategoryTheory/Limits/Shapes/FiniteProducts.lean`.
-/
```
- as the PR leaves it:
```lean
/-!

# Functor categories have finite limits when the target category does

These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean` because
that file shouldn't import `Mathlib/CategoryTheory/Limits/Shapes/FiniteProducts.lean`.
-/
```

### `command in HasLimits.lean` (command, modified) [56645c67e9]
- file: `Mathlib/CategoryTheory/Limits/HasLimits.lean`; changed: value_or_body:modified
- before the PR:
```lean
/-- We have lots of lemmas describing how to simplify `colimit.ι F j ≫ _`,
and combined with `colimit.ext` we rely on these lemmas for many calculations.

However, since `Category.assoc` is a `@[simp]` lemma, often expressions are
right associated, and it's hard to apply these lemmas about `colimit.ι`.

We thus use `reassoc` to define additional `@[simp]` lemmas, with an arbitrary extra morphism.
(see `Tactic/reassoc_axiom.lean`)
-/
```
- as the PR leaves it:
```lean
/-- We have lots of lemmas describing how to simplify `colimit.ι F j ≫ _`,
and combined with `colimit.ext` we rely on these lemmas for many calculations.

However, since `Category.assoc` is a `@[simp]` lemma, often expressions are
right associated, and it's hard to apply these lemmas about `colimit.ι`.

We thus use `reassoc` to define additional `@[simp]` lemmas, with an arbitrary extra morphism.
(see `Mathlib/Tactic/CategoryTheory/Reassoc.lean`)
-/
```

### `module_doc in Limits.lean` (module_doc, modified) [aaeaab1561]
- file: `Mathlib/CategoryTheory/Limits/Preserves/Limits.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Isomorphisms about functors which preserve (co)limits

If `G` preserves limits, and `C` and `D` have limits, then for any diagram `F : J ⥤ C` we have a
canonical isomorphism `preservesLimitsIso : G.obj (Limit F) ≅ Limit (F ⋙ G)`.
We also show that we can commute `IsLimit.lift` of a preserved limit with `Functor.mapCone`:
`(PreservesLimit.preserves t).lift (G.mapCone c₂) = G.map (t.lift c₂)`.

The duals of these are also given. For functors which preserve (co)limits of specific shapes, see
`preserves/shapes.lean`.
-/
```
- as the PR leaves it:
```lean
/-!
# Isomorphisms about functors which preserve (co)limits

If `G` preserves limits, and `C` and `D` have limits, then for any diagram `F : J ⥤ C` we have a
canonical isomorphism `preservesLimitsIso : G.obj (Limit F) ≅ Limit (F ⋙ G)`.
We also show that we can commute `IsLimit.lift` of a preserved limit with `Functor.mapCone`:
`(PreservesLimit.preserves t).lift (G.mapCone c₂) = G.map (t.lift c₂)`.

The duals of these are also given. For functors which preserve (co)limits of specific shapes, see
the files in the directory `Mathlib/CategoryTheory/Limits/Preserves/Shapes/`.
-/
```

### `module_doc in Over.lean` (module_doc, modified) [d066f65314]
- file: `Mathlib/CategoryTheory/Limits/Preserves/Over.lean`; changed: documentation:modified
- before the PR:
```lean
/-!

# Forgetful functor from `Over X` preserves cofiltered limits

Note that `Over.forget X : Over X ⥤ C` already preserves all colimits because it is a left adjoint.
See `Mathlib/CategoryTheory/Adjunction/Over.lean`

-/
```
- as the PR leaves it:
```lean
/-!

# Forgetful functor from `Over X` preserves cofiltered limits

Note that `Over.forget X : Over X ⥤ C` already preserves all colimits because it is a left adjoint.
See `Mathlib/CategoryTheory/Comma/Over/Pullback.lean`

-/
```

### `module_doc in Equivalence.lean` (module_doc, modified) [ce9e0c61db]
- file: `Mathlib/CategoryTheory/Localization/Equivalence.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Localization functors are preserved through equivalences

In `Localization/Predicate.lean`, the lemma `Localization.of_equivalence_target` already
showed that the predicate of localized categories is unchanged when we replace the
target category (i.e. the candidate localized category) by an equivalent category.
In this file, we show the same for the source category (`Localization.of_equivalence_source`).
More generally, `Localization.of_equivalences` shows that we may replace both the
source and target categories by equivalent categories. This is obtained using
`Localization.isEquivalence` which provide a sufficient condition in order to show
that a functor between localized categories is an equivalence.

-/
```
- as the PR leaves it:
```lean
/-!
# Localization functors are preserved through equivalences

In `Mathlib/CategoryTheory/Localization/Predicate.lean`, the lemma
`Localization.of_equivalence_target` already showed that the predicate of localized categories is
unchanged when we replace the target category (i.e. the candidate localized category) by an
equivalent category.
In this file, we show the same for the source category (`Localization.of_equivalence_source`).
More generally, `Localization.of_equivalences` shows that we may replace both the
source and target categories by equivalent categories. This is obtained using
`Localization.isEquivalence` which provide a sufficient condition in order to show
that a functor between localized categories is an equivalence.

-/
```

### `module_doc in Mon_.lean` (module_doc, modified) [e55b4122c3]
- file: `Mathlib/CategoryTheory/Monoidal/Mon_.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
In this section, we prove that the category of monoids in a braided monoidal category is monoidal.

Given two monoids `M` and `N` in a braided monoidal category `C`,
the multiplication on the tensor product `M.X ⊗ N.X` is defined in the obvious way:
it is the tensor product of the multiplications on `M` and `N`,
except that the tensor factors in the source come in the wrong order,
which we fix by pre-composing with a permutation isomorphism constructed from the braiding.

(There is a subtlety here: in fact there are two ways to do these,
using either the positive or negative crossing.)

A more conceptual way of understanding this definition is the following:
The braiding on `C` gives rise to a monoidal structure on
the tensor product functor from `C × C` to `C`.
A pair of monoids in `C` gives rise to a monoid in `C × C`,
which the tensor product functor by being monoidal takes to a monoid in `C`.
The permutation isomorphism appearing in the definition of
the multiplication on the tensor product of two monoids is
an instance of a more general family of isomorphisms
which together form a strength that equips the tensor product functor with a monoidal structure,
and the monoid axioms for the tensor product follow from the monoid axioms for the tensor factors
plus the properties of the strength (i.e., monoidal functor axioms).
The strength `tensorμ` of the tensor product functor has been defined in
`Mathlib/CategoryTheory/Monoidal/Braided.lean`.
Its properties, stated as independent lemmas in that module,
are used extensively in the proofs below.
Notice that we could have followed the above plan not only conceptually
but also as a possible implementation and
could have constructed the tensor product of monoids via `mapMon`,
but we chose to give a more explicit definition directly in terms of `tensorμ`.

To complete the definition of the monoidal category structure on the category of monoids,
we need to provide definitions of associator and unitors.
The obvious candidates are the associator and unitors from `C`,
but we need to prove that they are monoid morphisms, i.e., compatible with unit and multiplication.
These properties translate to the monoidality of the associator and unitors
(with respect to the monoidal structures on the functors they relate),
which have also been proved in `Mathlib/CategoryTheory/Monoidal/Braided.lean`.

-/

-- The proofs that associators and unitors preserve monoid units don't require braiding.
```
- as the PR leaves it:
```lean
/-!
In this section, we prove that the category of monoids in a braided monoidal category is monoidal.

Given two monoids `M` and `N` in a braided monoidal category `C`,
the multiplication on the tensor product `M.X ⊗ N.X` is defined in the obvious way:
it is the tensor product of the multiplications on `M` and `N`,
except that the tensor factors in the source come in the wrong order,
which we fix by pre-composing with a permutation isomorphism constructed from the braiding.

(There is a subtlety here: in fact there are two ways to do these,
using either the positive or negative crossing.)

A more conceptual way of understanding this definition is the following:
The braiding on `C` gives rise to a monoidal structure on
the tensor product functor from `C × C` to `C`.
A pair of monoids in `C` gives rise to a monoid in `C × C`,
which the tensor product functor by being monoidal takes to a monoid in `C`.
The permutation isomorphism appearing in the definition of
the multiplication on the tensor product of two monoids is
an instance of a more general family of isomorphisms
which together form a strength that equips the tensor product functor with a monoidal structure,
and the monoid axioms for the tensor product follow from the monoid axioms for the tensor factors
plus the properties of the strength (i.e., monoidal functor axioms).
The strength `tensorμ` of the tensor product functor has been defined in
`Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`.
Its properties, stated as independent lemmas in that module,
are used extensively in the proofs below.
Notice that we could have followed the above plan not only conceptually
but also as a possible implementation and
could have constructed the tensor product of monoids via `mapMon`,
but we chose to give a more explicit definition directly in terms of `tensorμ`.

To complete the definition of the monoidal category structure on the category of monoids,
we need to provide definitions of associator and unitors.
The obvious candidates are the associator and unitors from `C`,
but we need to prove that they are monoid morphisms, i.e., compatible with unit and multiplication.
These properties translate to the monoidality of the associator and unitors
(with respect to the monoidal structures on the functors they relate),
which have also been proved in `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`.

-/

-- The proofs that associators and unitors preserve monoid units don't require braiding.
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none

---

## The diff

```diff
diff --git a/Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean b/Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean
--- a/Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean
+++ b/Mathlib/CategoryTheory/Bicategory/Functor/StrictPseudofunctor.lean
@@ -18,8 +18,8 @@ underlying categories, see `StrictPseudofunctor.toFunctor`.
 
 ## TODO
 
-Once the deprecated `Functor/Strict.lean` is removed we should rename this file to
-`Functor/Strict.lean`.
+Once the deprecated `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean` is removed we should
+rename this file to `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean`.
 
 -/
 
diff --git a/Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean b/Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean
--- a/Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean
+++ b/Mathlib/CategoryTheory/ConcreteCategory/Bundled.lean
@@ -14,14 +14,14 @@ public import Batteries.Tactic.Lint.Misc
 `Bundled c` provides a uniform structure for bundling a type equipped with a type class.
 
 We provide `Category` instances for these in
-`Mathlib/CategoryTheory/HasForget/UnbundledHom.lean`
+`Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean`
 (for categories with unbundled homs, e.g. topological spaces)
-and in `Mathlib/CategoryTheory/HasForget/BundledHom.lean`
+and in `Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean`
 (for categories with bundled homs, e.g. monoids).
 
 Note: this structure will be deprecated in the future in favor of defining the category manually
-and then providing the `ConcreteCategory` instance on top of this. See `ConcreteCategory/Basic.lean`
-for more details.
+and then providing the `ConcreteCategory` instance on top of this. See
+`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean` for more details.
 -/
 
 @[expose] public section
diff --git a/Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean b/Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean
--- a/Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean
+++ b/Mathlib/CategoryTheory/ConcreteCategory/BundledHom.lean
@@ -31,7 +31,7 @@ variable {c : Type u → Type u} (hom : ∀ ⦃α β : Type u⦄ (_ : c α) (_ :
 This way we can use `⟨@MonoidHom.toFun, @MonoidHom.id ...⟩` in an instance. -/
 @[deprecated "The preferred method for talking about concrete categories is to implement the \
 category manually and then provide the `ConcreteCategory` instance on top of this. See \
-`ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
+`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
 structure BundledHom where
   /-- the underlying map of a bundled morphism -/
   toFun : ∀ {α β : Type u} (Iα : c α) (Iβ : c β), hom Iα Iβ → α → β
diff --git a/Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean b/Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean
--- a/Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean
+++ b/Mathlib/CategoryTheory/ConcreteCategory/UnbundledHom.lean
@@ -28,7 +28,7 @@ take two types `α`, `β` and instances of the corresponding structures,
 and return a predicate on `α → β`. -/
 @[deprecated "The preferred method for talking about concrete categories is to implement the \
 category manually and then provide the `ConcreteCategory` instance on top of this. See \
-`ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
+`Mathlib/CategoryTheory/ConcreteCategory/Basic.lean`" (since := "2025-11-17")]
 class UnbundledHom {c : Type u → Type u} (hom : ∀ ⦃α β⦄, c α → c β → (α → β) → Prop) : Prop where
   hom_id : ∀ {α} (ia : c α), hom ia ia id
   hom_comp : ∀ {α β γ} {Iα : c α} {Iβ : c β} {Iγ : c γ} {g : β → γ} {f : α → β} (_ : hom Iβ Iγ g)
diff --git a/Mathlib/CategoryTheory/Functor/Basic.lean b/Mathlib/CategoryTheory/Functor/Basic.lean
--- a/Mathlib/CategoryTheory/Functor/Basic.lean
+++ b/Mathlib/CategoryTheory/Functor/Basic.lean
@@ -62,7 +62,7 @@ attribute [grind =] Functor.map_id
 attribute [grind _=_] Functor.map_comp
 
 -- Note: We manually add this lemma which could be generated by `reassoc`,
--- since we will import this file into `Mathlib/Tactic/Reassoc.lean`.
+-- since we will import this file into `Mathlib/Tactic/CategoryTheory/Reassoc.lean`.
 lemma Functor.map_comp_assoc {C : Type u₁} [Category* C] {D : Type u₂} [Category* D] (F : C ⥤ D)
     {X Y Z : C} (f : X ⟶ Y) (g : Y ⟶ Z) {W : D} (h : F.obj Z ⟶ W) :
     (F.map (f ≫ g)) ≫ h = F.map f ≫ F.map g ≫ h := by
diff --git a/Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean b/Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean
--- a/Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean
+++ b/Mathlib/CategoryTheory/Groupoid/Subgroupoid.lean
@@ -40,7 +40,7 @@ Given a type `C` with associated `groupoid C` instance.
 
 ## Implementation details
 
-The structure of this file is copied from/inspired by `Mathlib/GroupTheory/Subgroup/Basic.lean`
+The structure of this file is copied from/inspired by `Mathlib/Algebra/Group/Subgroup/Basic.lean`
 and `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean`.
 
 ## TODO
diff --git a/Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean b/Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean
--- a/Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean
+++ b/Mathlib/CategoryTheory/Limits/FunctorCategory/Filtered.lean
@@ -11,7 +11,7 @@ public import Mathlib.CategoryTheory.Limits.Filtered
 /-!
 # Functor categories have filtered colimits when the target category does
 
-These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory.lean` because
+These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean` because
 that file shouldn't import `Mathlib/CategoryTheory/Limits/Filtered.lean`.
 -/
 
diff --git a/Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean b/Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean
--- a/Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean
+++ b/Mathlib/CategoryTheory/Limits/FunctorCategory/Finite.lean
@@ -13,7 +13,7 @@ public import Mathlib.CategoryTheory.Limits.Preserves.Finite
 
 # Functor categories have finite limits when the target category does
 
-These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory.lean` because
+These declarations cannot be in `Mathlib/CategoryTheory/Limits/FunctorCategory/Basic.lean` because
 that file shouldn't import `Mathlib/CategoryTheory/Limits/Shapes/FiniteProducts.lean`.
 -/
 
diff --git a/Mathlib/CategoryTheory/Limits/HasLimits.lean b/Mathlib/CategoryTheory/Limits/HasLimits.lean
--- a/Mathlib/CategoryTheory/Limits/HasLimits.lean
+++ b/Mathlib/CategoryTheory/Limits/HasLimits.lean
@@ -706,7 +706,7 @@ However, since `Category.assoc` is a `@[simp]` lemma, often expressions are
 right associated, and it's hard to apply these lemmas about `colimit.ι`.
 
 We thus use `reassoc` to define additional `@[simp]` lemmas, with an arbitrary extra morphism.
-(see `Tactic/reassoc_axiom.lean`)
+(see `Mathlib/Tactic/CategoryTheory/Reassoc.lean`)
 -/
 @[reassoc (attr := simp)]
 theorem colimit.ι_desc {F : J ⥤ C} [HasColimit F] (c : Cocone F) (j : J) :
diff --git a/Mathlib/CategoryTheory/Limits/Preserves/Limits.lean b/Mathlib/CategoryTheory/Limits/Preserves/Limits.lean
--- a/Mathlib/CategoryTheory/Limits/Preserves/Limits.lean
+++ b/Mathlib/CategoryTheory/Limits/Preserves/Limits.lean
@@ -16,7 +16,7 @@ We also show that we can commute `IsLimit.lift` of a preserved limit with `Funct
 `(PreservesLimit.preserves t).lift (G.mapCone c₂) = G.map (t.lift c₂)`.
 
 The duals of these are also given. For functors which preserve (co)limits of specific shapes, see
-`preserves/shapes.lean`.
+the files in the directory `Mathlib/CategoryTheory/Limits/Preserves/Shapes/`.
 -/
 
 @[expose] public section
diff --git a/Mathlib/CategoryTheory/Limits/Preserves/Over.lean b/Mathlib/CategoryTheory/Limits/Preserves/Over.lean
--- a/Mathlib/CategoryTheory/Limits/Preserves/Over.lean
+++ b/Mathlib/CategoryTheory/Limits/Preserves/Over.lean
@@ -12,7 +12,7 @@ public import Mathlib.CategoryTheory.Limits.Preserves.Filtered
 # Forgetful functor from `Over X` preserves cofiltered limits
 
 Note that `Over.forget X : Over X ⥤ C` already preserves all colimits because it is a left adjoint.
-See `Mathlib/CategoryTheory/Adjunction/Over.lean`
+See `Mathlib/CategoryTheory/Comma/Over/Pullback.lean`
 
 -/
 
diff --git a/Mathlib/CategoryTheory/Localization/Equivalence.lean b/Mathlib/CategoryTheory/Localization/Equivalence.lean
--- a/Mathlib/CategoryTheory/Localization/Equivalence.lean
+++ b/Mathlib/CategoryTheory/Localization/Equivalence.lean
@@ -11,9 +11,10 @@ public import Mathlib.CategoryTheory.CatCommSq
 /-!
 # Localization functors are preserved through equivalences
 
-In `Localization/Predicate.lean`, the lemma `Localization.of_equivalence_target` already
-showed that the predicate of localized categories is unchanged when we replace the
-target category (i.e. the candidate localized category) by an equivalent category.
+In `Mathlib/CategoryTheory/Localization/Predicate.lean`, the lemma
+`Localization.of_equivalence_target` already showed that the predicate of localized categories is
+unchanged when we replace the target category (i.e. the candidate localized category) by an
+equivalent category.
 In this file, we show the same for the source category (`Localization.of_equivalence_source`).
 More generally, `Localization.of_equivalences` shows that we may replace both the
 source and target categories by equivalent categories. This is obtained using
diff --git a/Mathlib/CategoryTheory/Monoidal/Mon_.lean b/Mathlib/CategoryTheory/Monoidal/Mon_.lean
--- a/Mathlib/CategoryTheory/Monoidal/Mon_.lean
+++ b/Mathlib/CategoryTheory/Monoidal/Mon_.lean
@@ -266,7 +266,7 @@ which together form a strength that equips the tensor product functor with a mon
 and the monoid axioms for the tensor product follow from the monoid axioms for the tensor factors
 plus the properties of the strength (i.e., monoidal functor axioms).
 The strength `tensorμ` of the tensor product functor has been defined in
-`Mathlib/CategoryTheory/Monoidal/Braided.lean`.
+`Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`.
 Its properties, stated as independent lemmas in that module,
 are used extensively in the proofs below.
 Notice that we could have followed the above plan not only conceptually
@@ -280,7 +280,7 @@ The obvious candidates are the associator and unitors from `C`,
 but we need to prove that they are monoid morphisms, i.e., compatible with unit and multiplication.
 These properties translate to the monoidality of the associator and unitors
 (with respect to the monoidal structures on the functors they relate),
-which have also been proved in `Mathlib/CategoryTheory/Monoidal/Braided.lean`.
+which have also been proved in `Mathlib/CategoryTheory/Monoidal/Braided/Basic.lean`.
 
 -/
 

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.