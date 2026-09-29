# The PR model for #41271 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(LinearAlgebra/Matrix/Nondegenerate): generalize lemmas to CommSemiring
- description: This PR generalizes the `SeparatingLeft`/`SeparatingRight`/`Nondegenerate` lemmas from `CommRing` to `CommSemiring` (the determinant section keeps `CommRing`), and golfs `nondegenerate_def` using the `@[mk_iff]`-generated `nondegenerate_iff`. Follow-up to https://github.com/leanprover-community/mathlib4/pull/39634, which generalized the definitions but left the lemmas at `CommRing`.

🤖 Prepared with Claude Code
- changed files: Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean

## Objects

### `section in Nondegenerate.lean` (command, modified) [1763da9512]
- file: `Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`; changed: namespace:modified
- before the PR:
```lean
variable {m n R : Type*} [CommRing R] {M : Matrix m n R}
```
- as the PR leaves it:
```lean
section CommSemiring
```

### `Matrix.nondegenerate_def` (lemma, modified) [3eec003058]
- file: `Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`; changed: proof:modified
- before the PR:
```lean
lemma nondegenerate_def [Fintype m] [Fintype n] :
    M.Nondegenerate ↔
      (∀ v, (∀ w, v ⬝ᵥ M *ᵥ w = 0) → v = 0) ∧ (∀ w, (∀ v, v ⬝ᵥ M *ᵥ w = 0) → w = 0) := by
  constructor
  · exact fun h ↦ ⟨separatingLeft_def.mp h.1, separatingRight_def.mp h.2⟩
  · exact fun h ↦ ⟨separatingLeft_def.mpr h.1, separatingRight_def.mpr h.2⟩
```
- as the PR leaves it:
```lean
lemma nondegenerate_def [Fintype m] [Fintype n] :
    M.Nondegenerate ↔
      (∀ v, (∀ w, v ⬝ᵥ M *ᵥ w = 0) → v = 0) ∧ (∀ w, (∀ v, v ⬝ᵥ M *ᵥ w = 0) → w = 0) := by
  rw [nondegenerate_iff, separatingLeft_def, separatingRight_def]
```

### `section in Nondegenerate.lean` (command, modified) [50baf4736e]
- file: `Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`; changed: namespace:modified
- before the PR:
```lean
variable {m n R : Type*} [CommRing R] {M : Matrix m n R}
```
- as the PR leaves it:
```lean
variable {m n R : Type*} [CommSemiring R] {M : Matrix m n R}
```

### `section in Nondegenerate.lean` (command, modified) [7cc3db6c76]
- file: `Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`; changed: namespace:modified
- before the PR:
```lean
variable [DecidableEq m] {M : Matrix m m R}
```
- as the PR leaves it:
```lean
variable {m R : Type*} [CommRing R] [Fintype m] [DecidableEq m] {M : Matrix m m R}
```

### `section in Nondegenerate.lean` (command, added) [df7020fb11]
- file: `Mathlib/LinearAlgebra/Matrix/Nondegenerate.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end CommSemiring
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none
