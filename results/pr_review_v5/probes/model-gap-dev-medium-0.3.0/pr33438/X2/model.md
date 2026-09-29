# The PR model for #33438 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Analysis): `arctan (√3) = π / 3` and `arctan (√3)⁻¹ = π / 6`
- description: (not recoverable at review start)
- changed files: Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean

## Objects

### `Real.arctan_inv_sqrt_three` (theorem, added) [3ef5b17a80]
- file: `Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem arctan_inv_sqrt_three : arctan (√3)⁻¹ = π / 6 := by
  rw [inv_eq_one_div, ← tan_pi_div_six, arctan_tan]
  all_goals
  · field_simp
    norm_num
```

### `Real.arctan_sqrt_three` (theorem, added) [5fd8ab9206]
- file: `Mathlib/Analysis/SpecialFunctions/Trigonometric/Arctan.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem arctan_sqrt_three : arctan (√3) = π / 3 := by
  rw [← tan_pi_div_three, arctan_tan]
  all_goals
  · field_simp
    norm_num
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `Real.arctan_inv_sqrt_three`, `Real.arctan_sqrt_three` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Real.arctan_inv_sqrt_three` -> `Real.arctan_sqrt_three`
- changed_siblings [high]: `Real.arctan_sqrt_three` -> `Real.arctan_inv_sqrt_three`
