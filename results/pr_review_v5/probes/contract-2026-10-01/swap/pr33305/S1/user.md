# Pull request #33305

**Title:** doc(GroupTheory): fix file refs

**Description:**
Fix some stale documentation file refs.

**Changed files:**
  - `Mathlib/GroupTheory/Abelianization/Defs.lean`
  - `Mathlib/GroupTheory/FreeAbelianGroup.lean`
  - `Mathlib/GroupTheory/FreeGroup/Basic.lean`
  - `Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean`
  - `Mathlib/GroupTheory/GroupExtension/Defs.lean`
  - `Mathlib/GroupTheory/Perm/Sign.lean`
  - `Mathlib/GroupTheory/Submonoid/Inverses.lean`

**Tools available:** read files, grep the repo (content_search), find files by name (file_search), compile your edit against the reviewed workspace (lean_verify_edit)


---

## The PR model (pass 0)

# The PR model for #33305 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: doc(GroupTheory): fix file refs
- description: Fix some stale documentation file refs.
- changed files: Mathlib/GroupTheory/Abelianization/Defs.lean, Mathlib/GroupTheory/FreeAbelianGroup.lean, Mathlib/GroupTheory/FreeGroup/Basic.lean, Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean, Mathlib/GroupTheory/GroupExtension/Defs.lean, Mathlib/GroupTheory/Perm/Sign.lean, Mathlib/GroupTheory/Submonoid/Inverses.lean

## Objects

### `module_doc in Defs.lean` (module_doc, modified) [c16454a65b]
- file: `Mathlib/GroupTheory/Abelianization/Defs.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# The abelianization of a group

This file defines the commutator and the abelianization of a group. It furthermore prepares for the
result that the abelianization is left adjoint to the forgetful functor from abelian groups to
groups, which can be found in `Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.

## Main definitions

* `Abelianization`: defines the abelianization of a group `G` as the quotient of a group by its
  commutator subgroup.
* `Abelianization.map`: lifts a group homomorphism to a homomorphism between the abelianizations
* `MulEquiv.abelianizationCongr`: Equivalent groups have equivalent abelianizations

-/
```
- as the PR leaves it:
```lean
/-!
# The abelianization of a group

This file defines the commutator and the abelianization of a group. It furthermore prepares for the
result that the abelianization is left adjoint to the forgetful functor from abelian groups to
groups, which can be found in `Mathlib/Algebra/Category/Grp/Adjunctions.lean`.

## Main definitions

* `Abelianization`: defines the abelianization of a group `G` as the quotient of a group by its
  commutator subgroup.
* `Abelianization.map`: lifts a group homomorphism to a homomorphism between the abelianizations
* `MulEquiv.abelianizationCongr`: Equivalent groups have equivalent abelianizations

-/
```

### `module_doc in FreeAbelianGroup.lean` (module_doc, modified) [fce498ce08]
- file: `Mathlib/GroupTheory/FreeAbelianGroup.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Free abelian groups

The free abelian group on a type `α`, defined as the abelianisation of
the free group on `α`.

The free abelian group on `α` can be abstractly defined as the left adjoint of the
forgetful functor from abelian groups to types. Alternatively, one could define
it as the functions `α → ℤ` which send all but finitely many `(a : α)` to `0`,
under pointwise addition. In this file, it is defined as the abelianisation
of the free group on `α`. All the constructions and theorems required to show
the adjointness of the construction and the forgetful functor are proved in this
file, but the category-theoretic adjunction statement is in
`Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.

## Main definitions

Here we use the following variables: `(α β : Type*) (A : Type*) [AddCommGroup A]`

* `FreeAbelianGroup α` : the free abelian group on a type `α`. As an abelian
  group it is `α →₀ ℤ`, the functions from `α` to `ℤ` such that all but finitely
  many elements get mapped to zero, however this is not how it is implemented.

* `lift f : FreeAbelianGroup α →+ A` : the group homomorphism induced
  by the map `f : α → A`.

* `map (f : α → β) : FreeAbelianGroup α →+ FreeAbelianGroup β` : functoriality
    of `FreeAbelianGroup`.

* `instance [Monoid α] : Semigroup (FreeAbelianGroup α)`

* `instance [CommMonoid α] : CommRing (FreeAbelianGroup α)`

It has been suggested that we would be better off refactoring this file
and using `Finsupp` instead.

## Implementation issues

The definition is `def FreeAbelianGroup : Type u := Additive <| Abelianization <| FreeGroup α`.

Chris Hughes has suggested that this all be rewritten in terms of `Finsupp`.
Johan Commelin has written all the API relating the definition to `Finsupp`
in the lean-liquid repo.

The lemmas `map_pure`, `map_of`, `map_zero`, `map_add`, `map_neg` and `map_sub`
are proved about the `Functor.map` `<$>` construction, and need `α` and `β` to
be in the same universe. But
`FreeAbelianGroup.map (f : α → β)` is defined to be the `AddGroup`
homomorphism `FreeAbelianGroup α →+ FreeAbelianGroup β` (with `α` and `β` now
allowed to be in different universes), so `(map f).map_add`
etc. can be used to prove that `FreeAbelianGroup.map` preserves addition. The
functions `map_id`, `map_id_apply`, `map_comp`, `map_comp_apply` and `map_of_apply`
are about `FreeAbelianGroup.map`.

-/
```
- as the PR leaves it:
```lean
/-!
# Free abelian groups

The free abelian group on a type `α`, defined as the abelianisation of
the free group on `α`.

The free abelian group on `α` can be abstractly defined as the left adjoint of the
forgetful functor from abelian groups to types. Alternatively, one could define
it as the functions `α → ℤ` which send all but finitely many `(a : α)` to `0`,
under pointwise addition. In this file, it is defined as the abelianisation
of the free group on `α`. All the constructions and theorems required to show
the adjointness of the construction and the forgetful functor are proved in this
file, but the category-theoretic adjunction statement is in
`Mathlib/Algebra/Category/Grp/Adjunctions.lean`.

## Main definitions

Here we use the following variables: `(α β : Type*) (A : Type*) [AddCommGroup A]`

* `FreeAbelianGroup α` : the free abelian group on a type `α`. As an abelian
  group it is `α →₀ ℤ`, the functions from `α` to `ℤ` such that all but finitely
  many elements get mapped to zero, however this is not how it is implemented.

* `lift f : FreeAbelianGroup α →+ A` : the group homomorphism induced
  by the map `f : α → A`.

* `map (f : α → β) : FreeAbelianGroup α →+ FreeAbelianGroup β` : functoriality
    of `FreeAbelianGroup`.

* `instance [Monoid α] : Semigroup (FreeAbelianGroup α)`

* `instance [CommMonoid α] : CommRing (FreeAbelianGroup α)`

It has been suggested that we would be better off refactoring this file
and using `Finsupp` instead.

## Implementation issues

The definition is `def FreeAbelianGroup : Type u := Additive <| Abelianization <| FreeGroup α`.

Chris Hughes has suggested that this all be rewritten in terms of `Finsupp`.
Johan Commelin has written all the API relating the definition to `Finsupp`
in the lean-liquid repo.

The lemmas `map_pure`, `map_of`, `map_zero`, `map_add`, `map_neg` and `map_sub`
are proved about the `Functor.map` `<$>` construction, and need `α` and `β` to
be in the same universe. But
`FreeAbelianGroup.map (f : α → β)` is defined to be the `AddGroup`
homomorphism `FreeAbelianGroup α →+ FreeAbelianGroup β` (with `α` and `β` now
allowed to be in different universes), so `(map f).map_add`
etc. can be used to prove that `FreeAbelianGroup.map` preserves addition. The
functions `map_id`, `map_id_apply`, `map_comp`, `map_comp_apply` and `map_of_apply`
are about `FreeAbelianGroup.map`.

-/
```

### `module_doc in Basic.lean` (module_doc, modified) [314dbc8564]
- file: `Mathlib/GroupTheory/FreeGroup/Basic.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Free groups

This file defines free groups over a type. Furthermore, it is shown that the free group construction
is an instance of a monad. For the result that `FreeGroup` is the left adjoint to the forgetful
functor from groups to types, see `Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.

## Main definitions

* `FreeGroup`/`FreeAddGroup`: the free group (resp. free additive group) associated to a type
  `α` defined as the words over `a : α × Bool` modulo the relation `a * x * x⁻¹ * b = a * b`.
* `FreeGroup.mk`/`FreeAddGroup.mk`: the canonical quotient map `List (α × Bool) → FreeGroup α`.
* `FreeGroup.of`/`FreeAddGroup.of`: the canonical injection `α → FreeGroup α`.
* `FreeGroup.lift f`/`FreeAddGroup.lift`: the canonical group homomorphism `FreeGroup α →* G`
  given a group `G` and a function `f : α → G`.

## Main statements

* `FreeGroup.Red.church_rosser`/`FreeAddGroup.Red.church_rosser`: The Church-Rosser theorem for word
  reduction (also known as Newman's diamond lemma).
* `FreeGroup.freeGroupUnitEquivInt`: The free group over the one-point type
  is isomorphic to the integers.
* The free group construction is an instance of a monad.

## Implementation details

First we introduce the one step reduction relation `FreeGroup.Red.Step`:
`w * x * x⁻¹ * v   ~>   w * v`, its reflexive transitive closure `FreeGroup.Red.trans`
and prove that its join is an equivalence relation. Then we introduce `FreeGroup α` as a quotient
over `FreeGroup.Red.Step`.

For the additive version we introduce the same relation under a different name so that we can
distinguish the quotient types more easily.


## Tags

free group, Newman's diamond lemma, Church-Rosser theorem
-/
```
- as the PR leaves it:
```lean
/-!
# Free groups

This file defines free groups over a type. Furthermore, it is shown that the free group construction
is an instance of a monad. For the result that `FreeGroup` is the left adjoint to the forgetful
functor from groups to types, see `Mathlib/Algebra/Category/Grp/Adjunctions.lean`.

## Main definitions

* `FreeGroup`/`FreeAddGroup`: the free group (resp. free additive group) associated to a type
  `α` defined as the words over `a : α × Bool` modulo the relation `a * x * x⁻¹ * b = a * b`.
* `FreeGroup.mk`/`FreeAddGroup.mk`: the canonical quotient map `List (α × Bool) → FreeGroup α`.
* `FreeGroup.of`/`FreeAddGroup.of`: the canonical injection `α → FreeGroup α`.
* `FreeGroup.lift f`/`FreeAddGroup.lift`: the canonical group homomorphism `FreeGroup α →* G`
  given a group `G` and a function `f : α → G`.

## Main statements

* `FreeGroup.Red.church_rosser`/`FreeAddGroup.Red.church_rosser`: The Church-Rosser theorem for word
  reduction (also known as Newman's diamond lemma).
* `FreeGroup.freeGroupUnitEquivInt`: The free group over the one-point type
  is isomorphic to the integers.
* The free group construction is an instance of a monad.

## Implementation details

First we introduce the one step reduction relation `FreeGroup.Red.Step`:
`w * x * x⁻¹ * v   ~>   w * v`, its reflexive transitive closure `FreeGroup.Red.trans`
and prove that its join is an equivalence relation. Then we introduce `FreeGroup α` as a quotient
over `FreeGroup.Red.Step`.

For the additive version we introduce the same relation under a different name so that we can
distinguish the quotient types more easily.


## Tags

free group, Newman's diamond lemma, Church-Rosser theorem
-/
```

### `module_doc in ActionHom.lean` (module_doc, modified) [58c8f1b4c2]
- file: `Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Action of `Mᵈᵐᵃ` on `α →[N] β` and `A →+[N] B`

In this file we define action of `DomMulAct M = Mᵈᵐᵃ` on `α →[N] β` and on `A →+[N] B`. At the
time of writing, these homomorphisms are not widely used in the library, so we put these instances
into a separate file, not with the definition of `DomMulAct`.

## TODO

Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/Algebra/Hom/GroupAction.lean` and
`SMulCommClass` instances saying that left and right actions commute.
-/
```
- as the PR leaves it:
```lean
/-!
# Action of `Mᵈᵐᵃ` on `α →[N] β` and `A →+[N] B`

In this file we define action of `DomMulAct M = Mᵈᵐᵃ` on `α →[N] β` and on `A →+[N] B`. At the
time of writing, these homomorphisms are not widely used in the library, so we put these instances
into a separate file, not with the definition of `DomMulAct`.

## TODO

Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/Algebra/Group/Action/Hom.lean` and
`SMulCommClass` instances saying that left and right actions commute.
-/
```

### `module_doc in Defs.lean` (module_doc, modified) [3594bd9308]
- file: `Mathlib/GroupTheory/GroupExtension/Defs.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Group Extensions

This file defines extensions of multiplicative and additive groups and their associated structures
such as splittings and equivalences.

## Main definitions

- `(Add?)GroupExtension N E G`: structure for extensions of `G` by `N` as short exact sequences
  `1 → N → E → G → 1` (`0 → N → E → G → 0` for additive groups)
- `(Add?)GroupExtension.Equiv S S'`: structure for equivalences of two group extensions `S` and `S'`
  as specific homomorphisms `E → E'` such that each diagram below is commutative

```text
For multiplicative groups:
      ↗︎ E  ↘
1 → N   ↓    G → 1
      ↘︎ E' ↗︎️

For additive groups:
      ↗︎ E  ↘
0 → N   ↓    G → 0
      ↘︎ E' ↗︎️
```

- `(Add?)GroupExtension.Section S`: structure for right inverses to `rightHom` of a group extension
  `S` of `G` by `N`
- `(Add?)GroupExtension.Splitting S`: structure for section homomorphisms of a group extension `S`
  of `G` by `N`
- `SemidirectProduct.toGroupExtension φ`: the multiplicative group extension associated to the
  semidirect product coming from `φ : G →* MulAut N`, `1 → N → N ⋊[φ] G → G → 1`

## TODO

If `N` is abelian,

- there is a bijection between `N`-conjugacy classes of
  `(SemidirectProduct.toGroupExtension φ).Splitting` and `groupCohomology.H1`
  (which will be available in `GroupTheory/GroupExtension/Abelian.lean` to be added in a later PR).
- there is a bijection between equivalence classes of group extensions and `groupCohomology.H2`
  (which is also stated as a TODO in `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`).
-/
```
- as the PR leaves it:
```lean
/-!
# Group Extensions

This file defines extensions of multiplicative and additive groups and their associated structures
such as splittings and equivalences.

## Main definitions

- `(Add?)GroupExtension N E G`: structure for extensions of `G` by `N` as short exact sequences
  `1 → N → E → G → 1` (`0 → N → E → G → 0` for additive groups)
- `(Add?)GroupExtension.Equiv S S'`: structure for equivalences of two group extensions `S` and `S'`
  as specific homomorphisms `E → E'` such that each diagram below is commutative

```text
For multiplicative groups:
      ↗︎ E  ↘
1 → N   ↓    G → 1
      ↘︎ E' ↗︎️

For additive groups:
      ↗︎ E  ↘
0 → N   ↓    G → 0
      ↘︎ E' ↗︎️
```

- `(Add?)GroupExtension.Section S`: structure for right inverses to `rightHom` of a group extension
  `S` of `G` by `N`
- `(Add?)GroupExtension.Splitting S`: structure for section homomorphisms of a group extension `S`
  of `G` by `N`
- `SemidirectProduct.toGroupExtension φ`: the multiplicative group extension associated to the
  semidirect product coming from `φ : G →* MulAut N`, `1 → N → N ⋊[φ] G → G → 1`

## TODO

If `N` is abelian,

- there is a bijection between `N`-conjugacy classes of
  `(SemidirectProduct.toGroupExtension φ).Splitting` and `groupCohomology.H1`
  (which will be available in the planned file `Mathlib/GroupTheory/GroupExtension/Abelian.lean` to
  be added in a later PR).
- there is a bijection between equivalence classes of group extensions and `groupCohomology.H2`
  (which is also stated as a TODO in `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`).
-/
```

### `module_doc in Sign.lean` (module_doc, modified) [42e2f120d9]
- file: `Mathlib/GroupTheory/Perm/Sign.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Sign of a permutation

The main definition of this file is `Equiv.Perm.sign`,
associating a `ℤˣ` sign with a permutation.

Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Fintype.lean`

-/
```
- as the PR leaves it:
```lean
/-!
# Sign of a permutation

The main definition of this file is `Equiv.Perm.sign`,
associating a `ℤˣ` sign with a permutation.

Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`

-/
```

### `module_doc in Inverses.lean` (module_doc, modified) [10636e03b0]
- file: `Mathlib/GroupTheory/Submonoid/Inverses.lean`; changed: documentation:modified
- before the PR:
```lean
/-!

# Submonoid of inverses

Given a submonoid `N` of a monoid `M`, we define the submonoid `N.leftInv` as the submonoid of
left inverses of `N`. When `M` is commutative, we may define `fromCommLeftInv : N.leftInv →* N`
since the inverses are unique. When `N ≤ IsUnit.Submonoid M`, this is precisely
the pointwise inverse of `N`, and we may define `leftInvEquiv : S.leftInv ≃* S`.

For the pointwise inverse of submonoids of groups, please refer to the file
`Mathlib/Algebra/Group/Submonoid/Pointwise.lean`.

`N.leftInv` is distinct from `N.units`, which is the subgroup of `Mˣ` containing all units that are
in `N`. See the implementation notes of `Mathlib/GroupTheory/Submonoid/Units.lean` for more details
on related constructions.

## TODO

Define the submonoid of right inverses and two-sided inverses.
See the comments of https://github.com/leanprover-community/mathlib4/pull/10679 for a possible
implementation.
-/
```
- as the PR leaves it:
```lean
/-!

# Submonoid of inverses

Given a submonoid `N` of a monoid `M`, we define the submonoid `N.leftInv` as the submonoid of
left inverses of `N`. When `M` is commutative, we may define `fromCommLeftInv : N.leftInv →* N`
since the inverses are unique. When `N ≤ IsUnit.Submonoid M`, this is precisely
the pointwise inverse of `N`, and we may define `leftInvEquiv : S.leftInv ≃* S`.

For the pointwise inverse of submonoids of groups, please refer to the file
`Mathlib/Algebra/Group/Submonoid/Pointwise.lean`.

`N.leftInv` is distinct from `N.units`, which is the subgroup of `Mˣ` containing all units that are
in `N`. See the implementation notes of `Mathlib/Algebra/Group/Submonoid/Units.lean` for more details
on related constructions.

## TODO

Define the submonoid of right inverses and two-sided inverses.
See the comments of https://github.com/leanprover-community/mathlib4/pull/10679 for a possible
implementation.
-/
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
diff --git a/Mathlib/GroupTheory/Abelianization/Defs.lean b/Mathlib/GroupTheory/Abelianization/Defs.lean
--- a/Mathlib/GroupTheory/Abelianization/Defs.lean
+++ b/Mathlib/GroupTheory/Abelianization/Defs.lean
@@ -12,7 +12,7 @@ public import Mathlib.GroupTheory.Commutator.Basic
 
 This file defines the commutator and the abelianization of a group. It furthermore prepares for the
 result that the abelianization is left adjoint to the forgetful functor from abelian groups to
-groups, which can be found in `Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.
+groups, which can be found in `Mathlib/Algebra/Category/Grp/Adjunctions.lean`.
 
 ## Main definitions
 
diff --git a/Mathlib/GroupTheory/FreeAbelianGroup.lean b/Mathlib/GroupTheory/FreeAbelianGroup.lean
--- a/Mathlib/GroupTheory/FreeAbelianGroup.lean
+++ b/Mathlib/GroupTheory/FreeAbelianGroup.lean
@@ -22,7 +22,7 @@ under pointwise addition. In this file, it is defined as the abelianisation
 of the free group on `α`. All the constructions and theorems required to show
 the adjointness of the construction and the forgetful functor are proved in this
 file, but the category-theoretic adjunction statement is in
-`Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.
+`Mathlib/Algebra/Category/Grp/Adjunctions.lean`.
 
 ## Main definitions
 
diff --git a/Mathlib/GroupTheory/FreeGroup/Basic.lean b/Mathlib/GroupTheory/FreeGroup/Basic.lean
--- a/Mathlib/GroupTheory/FreeGroup/Basic.lean
+++ b/Mathlib/GroupTheory/FreeGroup/Basic.lean
@@ -16,7 +16,7 @@ public import Mathlib.Algebra.BigOperators.Group.List.Basic
 
 This file defines free groups over a type. Furthermore, it is shown that the free group construction
 is an instance of a monad. For the result that `FreeGroup` is the left adjoint to the forgetful
-functor from groups to types, see `Mathlib/Algebra/Category/GrpCat/Adjunctions.lean`.
+functor from groups to types, see `Mathlib/Algebra/Category/Grp/Adjunctions.lean`.
 
 ## Main definitions
 
diff --git a/Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean b/Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean
--- a/Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean
+++ b/Mathlib/GroupTheory/GroupAction/DomAct/ActionHom.lean
@@ -16,7 +16,7 @@ into a separate file, not with the definition of `DomMulAct`.
 
 ## TODO
 
-Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/Algebra/Hom/GroupAction.lean` and
+Add left actions of, e.g., `M` on `α →[N] β` to `Mathlib/Algebra/Group/Action/Hom.lean` and
 `SMulCommClass` instances saying that left and right actions commute.
 -/
 
diff --git a/Mathlib/GroupTheory/GroupExtension/Defs.lean b/Mathlib/GroupTheory/GroupExtension/Defs.lean
--- a/Mathlib/GroupTheory/GroupExtension/Defs.lean
+++ b/Mathlib/GroupTheory/GroupExtension/Defs.lean
@@ -46,7 +46,8 @@ If `N` is abelian,
 
 - there is a bijection between `N`-conjugacy classes of
   `(SemidirectProduct.toGroupExtension φ).Splitting` and `groupCohomology.H1`
-  (which will be available in `GroupTheory/GroupExtension/Abelian.lean` to be added in a later PR).
+  (which will be available in the planned file `Mathlib/GroupTheory/GroupExtension/Abelian.lean` to
+  be added in a later PR).
 - there is a bijection between equivalence classes of group extensions and `groupCohomology.H2`
   (which is also stated as a TODO in `Mathlib/RepresentationTheory/GroupCohomology/LowDegree.lean`).
 -/
diff --git a/Mathlib/GroupTheory/Perm/Sign.lean b/Mathlib/GroupTheory/Perm/Sign.lean
--- a/Mathlib/GroupTheory/Perm/Sign.lean
+++ b/Mathlib/GroupTheory/Perm/Sign.lean
@@ -25,7 +25,7 @@ public import Mathlib.Data.Finset.Sigma
 The main definition of this file is `Equiv.Perm.sign`,
 associating a `ℤˣ` sign with a permutation.
 
-Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Fintype.lean`
+Other lemmas have been moved to `Mathlib/GroupTheory/Perm/Finite.lean`
 
 -/
 
diff --git a/Mathlib/GroupTheory/Submonoid/Inverses.lean b/Mathlib/GroupTheory/Submonoid/Inverses.lean
--- a/Mathlib/GroupTheory/Submonoid/Inverses.lean
+++ b/Mathlib/GroupTheory/Submonoid/Inverses.lean
@@ -20,7 +20,7 @@ For the pointwise inverse of submonoids of groups, please refer to the file
 `Mathlib/Algebra/Group/Submonoid/Pointwise.lean`.
 
 `N.leftInv` is distinct from `N.units`, which is the subgroup of `Mˣ` containing all units that are
-in `N`. See the implementation notes of `Mathlib/GroupTheory/Submonoid/Units.lean` for more details
+in `N`. See the implementation notes of `Mathlib/Algebra/Group/Submonoid/Units.lean` for more details
 on related constructions.
 
 ## TODO

```

---

When you have reviewed the PR as the brief asks, call `submit_findings`. For each finding, give:

- `path` and `line_start` -- where in the reviewed file the problem is, so the finding can be located. Give the line of the declaration your claim is about.
- `claim` -- name the declaration and say what is wrong with it.
- `suggested_fix` -- what to do instead.
- `severity` -- `blocking` if the change is needed for correctness or policy; `advisory` for every other change you would request. Advisory findings count in full.

Also give `notes`: your account of the review, with an entry for every changed declaration in the PR model (declarations of one family may share an entry). In each entry, say what you checked for that declaration under each concern that applies to it -- its proof, its statement and how general it is, whether the library already has it, its name, its docstring, its attributes and placement -- and close it with what you concluded, "nothing to ask" included.

Finish by calling `submit_findings` once. If there is nothing to ask, call it with an empty `findings` list and your `notes`.