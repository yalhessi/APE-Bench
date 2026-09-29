# The PR model for #41930 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: fix(GroupTheory/Coprod): fix recursor argument name
- description: Fix the argument names of `Monoid.Coprod.induction_on'` and `Monoid.Coprod.induction_on`. Name the motive `motive` and name the minor premises according to their contents.
- changed files: Mathlib/GroupTheory/Coprod/Basic.lean

## Objects

### `Monoid.Coprod.induction_on` (theorem, modified) [a7d45f00f1]
- file: `Mathlib/GroupTheory/Coprod/Basic.lean`; changed: statement_or_type:modified
- before the PR:
```lean
@[to_additive (attr := elab_as_elim)]
theorem induction_on {C : M ∗ N → Prop} (m : M ∗ N)
    (inl : ∀ m, C (inl m)) (inr : ∀ n, C (inr n)) (mul : ∀ x y, C x → C y → C (x * y)) : C m :=
  induction_on' m (by simpa using inl 1) (fun _ _ ↦ mul _ _ (inl _)) fun _ _ ↦ mul _ _ (inr _)
```
- as the PR leaves it:
```lean
@[to_additive (attr := elab_as_elim)]
theorem induction_on {motive : M ∗ N → Prop} (m : M ∗ N)
    (inl : ∀ m, motive (inl m)) (inr : ∀ n, motive (inr n))
    (mul : ∀ x y, motive x → motive y → motive (x * y)) : motive m :=
  induction_on' m (by simpa using inl 1) (fun _ _ ↦ mul _ _ (inl _)) fun _ _ ↦ mul _ _ (inr _)
```

### `Monoid.Coprod.induction_on'` (theorem, modified) [c72cedd5b4]
- file: `Mathlib/GroupTheory/Coprod/Basic.lean`; changed: statement_or_type:modified
- before the PR:
```lean
@[to_additive (attr := elab_as_elim)]
theorem induction_on' {C : M ∗ N → Prop} (m : M ∗ N)
    (one : C 1)
    (inl_mul : ∀ m x, C x → C (inl m * x))
    (inr_mul : ∀ n x, C x → C (inr n * x)) : C m := by
  rcases mk_surjective m with ⟨x, rfl⟩
  induction x using FreeMonoid.inductionOn' with
  | one => exact one
  | mul_of x xs ih =>
    cases x with
    | inl m => simpa using inl_mul m _ ih
    | inr n => simpa using inr_mul n _ ih
```
- as the PR leaves it:
```lean
@[to_additive (attr := elab_as_elim)]
theorem induction_on' {motive : M ∗ N → Prop} (m : M ∗ N)
    (one : motive 1)
    (inl_mul : ∀ m x, motive x → motive (inl m * x))
    (inr_mul : ∀ n x, motive x → motive (inr n * x)) : motive m := by
  rcases mk_surjective m with ⟨x, rfl⟩
  induction x using FreeMonoid.inductionOn' with
  | one => exact one
  | mul_of x xs ih =>
    cases x with
    | inl m => simpa using inl_mul m _ ih
    | inr n => simpa using inr_mul n _ ih
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `Monoid.Coprod.induction_on`, `Monoid.Coprod.induction_on'` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Monoid.Coprod.induction_on` -> `Monoid.Coprod.induction_on'`
- changed_siblings [high]: `Monoid.Coprod.induction_on'` -> `Monoid.Coprod.induction_on`
- direct_use_of_changed_declaration [exact]: `Monoid.Coprod.induction_on` -> `Monoid.Coprod.induction_on'`
- name_family [high]: `Monoid.Coprod.induction_on` -> `Monoid.Coprod.induction_on'`
- name_family [high]: `Monoid.Coprod.induction_on'` -> `Monoid.Coprod.induction_on`
