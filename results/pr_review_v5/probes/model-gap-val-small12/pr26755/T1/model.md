# The PR model for #26755 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore: remove `noncomputable` from Set/Finset Monoid instances
- description: (not recoverable at review start)
- changed files: Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean, Mathlib/Algebra/Group/Pointwise/Set/Basic.lean

## Objects

### `command in Basic.lean` (command, removed) [135f074c09]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: value_or_body:removed
- before the PR:
```lean
#adaptation_note /-- nightly-2025-04-07
This now needs to be marked as noncomputable because of its dependence on `Set.monoid`.
We should either find a way to rewrite this definition to avoid this,
or request via @kim-em and @zwarich that changes in https://github.com/leanprover/lean4/pull/7824
be revisited to avoid needing as many `noncomputable`s.
-/
```

### `Finset.monoid` (def, modified) [d1b6bfb914]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "`Finset α` is an `AddMonoid` under pointwise operations if `α` is. "]
protected noncomputable def monoid : Monoid (Finset α) :=
  coe_injective.monoid _ coe_one coe_mul coe_pow
```
- as the PR leaves it:
```lean
@[to_additive "`Finset α` is an `AddMonoid` under pointwise operations if `α` is. "]
protected def monoid : Monoid (Finset α) :=
  coe_injective.monoid _ coe_one coe_mul coe_pow
```

### `Set.involutiveInv` (instance, modified) [1b7872fb24]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive (attr := simp)]
noncomputable instance involutiveInv : InvolutiveInv (Set α) where
  inv := Inv.inv
  inv_inv s := by simp only [← inv_preimage, preimage_preimage, inv_inv, preimage_id']
```
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
instance involutiveInv : InvolutiveInv (Set α) where
  inv := Inv.inv
  inv_inv s := by simp only [← inv_preimage, preimage_preimage, inv_inv, preimage_id']
```

### `Set.commMonoid` (def, modified) [41bcb923cf]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "`Set α` is an `AddCommMonoid` under pointwise operations if `α` is."]
protected noncomputable def commMonoid [CommMonoid α] : CommMonoid (Set α) :=
  { Set.monoid, Set.commSemigroup with }
```
- as the PR leaves it:
```lean
@[to_additive "`Set α` is an `AddCommMonoid` under pointwise operations if `α` is."]
protected def commMonoid [CommMonoid α] : CommMonoid (Set α) :=
  { Set.monoid, Set.commSemigroup with }
```

### `Set.mulOneClass` (def, modified) [630d392657]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "`Set α` is an `AddZeroClass` under pointwise operations if `α` is."]
protected noncomputable def mulOneClass : MulOneClass (Set α) :=
  { Set.one, Set.mul with
    mul_one := image2_right_identity mul_one
    one_mul := image2_left_identity one_mul }
```
- as the PR leaves it:
```lean
@[to_additive "`Set α` is an `AddZeroClass` under pointwise operations if `α` is."]
protected def mulOneClass : MulOneClass (Set α) :=
  { Set.one, Set.mul with
    mul_one := image2_right_identity mul_one
    one_mul := image2_left_identity one_mul }
```

### `Set.singletonMulHom` (def, modified) [7c0d356b34]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "The singleton operation as an `AddHom`."]
noncomputable def singletonMulHom : α →ₙ* Set α where
  toFun := singleton
  map_mul' _ _ := singleton_mul_singleton.symm
```
- as the PR leaves it:
```lean
@[to_additive "The singleton operation as an `AddHom`."]
def singletonMulHom : α →ₙ* Set α where
  toFun := singleton
  map_mul' _ _ := singleton_mul_singleton.symm
```

### `Set.divisionMonoid` (def, modified) [7d0981595e]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive
    "`Set α` is a subtraction monoid under pointwise operations if `α` is."]
protected noncomputable def divisionMonoid : DivisionMonoid (Set α) :=
  { Set.monoid, Set.involutiveInv, Set.div, @Set.ZPow α _ _ _ with
    mul_inv_rev := fun s t => by
      simp_rw [← image_inv_eq_inv]
      exact image_image2_antidistrib mul_inv_rev
    inv_eq_of_mul := fun s t h => by
      obtain ⟨a, b, rfl, rfl, hab⟩ := Set.mul_eq_one_iff.1 h
      rw [inv_singleton, inv_eq_of_mul_eq_one_right hab]
    div_eq_mul_inv := fun s t => by
      rw [← image_id (s / t), ← image_inv_eq_inv]
      exact image_image2_distrib_right div_eq_mul_inv }
```
- as the PR leaves it:
```lean
@[to_additive
    "`Set α` is a subtraction monoid under pointwise operations if `α` is."]
protected def divisionMonoid : DivisionMonoid (Set α) :=
  { Set.monoid, Set.involutiveInv, Set.div, @Set.ZPow α _ _ _ with
    mul_inv_rev := fun s t => by
      simp_rw [← image_inv_eq_inv]
      exact image_image2_antidistrib mul_inv_rev
    inv_eq_of_mul := fun s t h => by
      obtain ⟨a, b, rfl, rfl, hab⟩ := Set.mul_eq_one_iff.1 h
      rw [inv_singleton, inv_eq_of_mul_eq_one_right hab]
    div_eq_mul_inv := fun s t => by
      rw [← image_id (s / t), ← image_inv_eq_inv]
      exact image_image2_distrib_right div_eq_mul_inv }
```

### `Set.singletonOneHom` (def, modified) [81a156a7b7]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "The singleton operation as a `ZeroHom`."]
noncomputable def singletonOneHom : OneHom α (Set α) where
  toFun := singleton; map_one' := singleton_one
```
- as the PR leaves it:
```lean
@[to_additive "The singleton operation as a `ZeroHom`."]
def singletonOneHom : OneHom α (Set α) where
  toFun := singleton; map_one' := singleton_one
```

### `Set.singletonMonoidHom` (def, modified) [a7b94a88b6]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "The singleton operation as an `AddMonoidHom`."]
noncomputable def singletonMonoidHom : α →* Set α :=
  { singletonMulHom, singletonOneHom with }
```
- as the PR leaves it:
```lean
@[to_additive "The singleton operation as an `AddMonoidHom`."]
def singletonMonoidHom : α →* Set α :=
  { singletonMulHom, singletonOneHom with }
```

### `Set.one` (def, modified) [b4df906e7c]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "The set `0 : Set α` is defined as `{0}` in locale `Pointwise`."]
protected noncomputable def one : One (Set α) :=
  ⟨{1}⟩
```
- as the PR leaves it:
```lean
@[to_additive "The set `0 : Set α` is defined as `{0}` in locale `Pointwise`."]
protected def one : One (Set α) :=
  ⟨{1}⟩
```

### `Set.divisionCommMonoid` (def, modified) [cf46e0b384]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive subtractionCommMonoid
      "`Set α` is a commutative subtraction monoid under pointwise operations if `α` is."]
protected noncomputable def divisionCommMonoid [DivisionCommMonoid α] :
    DivisionCommMonoid (Set α) :=
  { Set.divisionMonoid, Set.commSemigroup with }
```
- as the PR leaves it:
```lean
@[to_additive subtractionCommMonoid
      "`Set α` is a commutative subtraction monoid under pointwise operations if `α` is."]
protected def divisionCommMonoid [DivisionCommMonoid α] :
    DivisionCommMonoid (Set α) :=
  { Set.divisionMonoid, Set.commSemigroup with }
```

### `Set.monoid` (def, modified) [ee4a5092ff]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Basic.lean`; changed: attributes:modified
- before the PR:
```lean
@[to_additive "`Set α` is an `AddMonoid` under pointwise operations if `α` is."]
protected noncomputable def monoid : Monoid (Set α) :=
  { Set.semigroup, Set.mulOneClass, @Set.NPow α _ _ with }
```
- as the PR leaves it:
```lean
@[to_additive "`Set α` is an `AddMonoid` under pointwise operations if `α` is."]
protected def monoid : Monoid (Set α) :=
  { Set.semigroup, Set.mulOneClass, @Set.NPow α _ _ with }
```

## Removed or renamed

- `command in Basic.lean`

## Families (declarations that may be one decision)

- [exact] `Set.divisionCommMonoid`, `Set.divisionMonoid` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Set.singletonMonoidHom`, `Set.singletonMulHom`, `Set.singletonOneHom` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `Set.commMonoid` -> `Set.monoid`
- direct_use_of_changed_declaration [exact]: `Set.divisionCommMonoid` -> `Set.divisionMonoid`
- direct_use_of_changed_declaration [exact]: `Set.divisionMonoid` -> `Set.monoid`
- direct_use_of_changed_declaration [exact]: `Set.divisionMonoid` -> `Set.involutiveInv`
- direct_use_of_changed_declaration [exact]: `Set.monoid` -> `Set.mulOneClass`
- direct_use_of_changed_declaration [exact]: `Set.mulOneClass` -> `Set.one`
- direct_use_of_changed_declaration [exact]: `Set.singletonMonoidHom` -> `Set.singletonOneHom`
- direct_use_of_changed_declaration [exact]: `Set.singletonMonoidHom` -> `Set.singletonMulHom`
- name_family [high]: `Set.divisionCommMonoid` -> `Set.divisionMonoid`
- name_family [high]: `Set.divisionMonoid` -> `Set.divisionCommMonoid`
- name_family [high]: `Set.singletonMonoidHom` -> `Set.singletonOneHom`
- name_family [high]: `Set.singletonMonoidHom` -> `Set.singletonMulHom`
- name_family [high]: `Set.singletonMulHom` -> `Set.singletonMonoidHom`
- name_family [high]: `Set.singletonMulHom` -> `Set.singletonOneHom`
- name_family [high]: `Set.singletonOneHom` -> `Set.singletonMonoidHom`
- name_family [high]: `Set.singletonOneHom` -> `Set.singletonMulHom`
