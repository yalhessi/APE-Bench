# The PR model for #30641 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: elementary lemmas aiding computations with `log⁺`
- description: Add several elementary lemmas aiding computations with `log⁺`. Improve the docstrings a little.
- changed files: Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean

## Objects

### `doc_comment in PosLog.lean` (command, modified) [206992eda5]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:modified
- before the PR:
```lean
/-- Estimate for `log⁺` of a sum. See `Real.posLog_add` for a variant involving
just two summands. -/
```
- as the PR leaves it:
```lean
/--
Estimate for `log⁺` of a sum. See `Real.posLog_add` for a variant involving just two summands.
-/
```

### `module_doc in PosLog.lean` (module_doc, added) [3640bb452e]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Estimates for Products
-/
```

### `module_doc in PosLog.lean` (module_doc, added) [531781b823]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# The Positive Part of the Logarithm

This file defines the function `Real.posLog = r ↦ max 0 (log r)` and introduces the notation
`log⁺`. For a finite length-`n` sequence `f i` of reals, it establishes the following standard
estimates.

- `theorem posLog_prod : log⁺ (∏ i, f i) ≤ ∑ i, log⁺ (f i)`

- `theorem posLog_sum : log⁺ (∑ i, f i) ≤ log n + ∑ i, log⁺ (f i)`

See `Mathlib.Analysis.SpecialFunctions.Integrals.PosLogEqCircleAverage` for the presentation of
`log⁺` as a Circle Average.
-/
```

### `doc_comment in PosLog.lean` (command, modified) [715b491cdf]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:modified
- before the PR:
```lean
/-- Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving
multiple summands. -/
```
- as the PR leaves it:
```lean
/--
Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving multiple summands.
-/
```

### `Real.posLog_norm_sum_le` (lemma, added) [717758b7a2]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma posLog_norm_sum_le {E : Type*} [NormedAddCommGroup E]
    {α : Type*} (s : Finset α) (f : α → E) :
    log⁺ ‖∑ t ∈ s, f t‖ ≤ log s.card + ∑ t ∈ s, log⁺ ‖f t‖ := by
  calc log⁺ ‖∑ t ∈ s, f t‖
  _ ≤ log⁺ (∑ t ∈ s, ‖f t‖) := by
    apply monotoneOn_posLog (by simp) _ (norm_sum_le s f)
    simp [Finset.sum_nonneg (fun i _ ↦ norm_nonneg (f i))]
  _ ≤ log s.card + ∑ t ∈ s, log⁺ ‖f t‖ :=
    posLog_sum s (‖f ·‖)
```

### `Real.posLog_pow` (lemma, added) [7bb89441d9]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma posLog_pow {n : ℕ} {a : ℝ} :
    log⁺ (a ^ n) = n * log⁺ a := by
  by_cases hn : n = 0
  · simp_all
  by_cases h₂a : |a| ≤ 1
  · simp_all [pow_le_one₀, (posLog_eq_zero_iff _).2]
  rw [not_le] at h₂a
  have : 1 < |a ^ n| := by simp [one_lt_pow₀ h₂a hn]
  simp [posLog_eq_log this.le, posLog_eq_log h₂a.le]
```

### `doc_comment in PosLog.lean` (command, added) [8f99740e21]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- The function `log⁺` commutes with taking powers. -/
```

### `Real.posLog_zero` (lemma, added) [9059e74e1c]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma posLog_zero : log⁺ 0 = 0 := by simp [posLog]
```

### `Real.posLog_one` (lemma, added) [e10f28b2ad]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp] lemma posLog_one : log⁺ 1 = 0 := by simp [posLog]
```

### `doc_comment in PosLog.lean` (command, modified) [e8a1480c90]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:modified
- before the PR:
```lean
/-- Estimate for `log⁺` of a sum. See `Real.posLog_sum` for a variant involving
multiple summands. -/
```
- as the PR leaves it:
```lean
/--
Variant of `posLog_sum` for norms of elements in normed additive commutative
groups, using monotonicity of `log⁺` and the triangle inequality.
-/
```

### `module_doc in PosLog.lean` (module_doc, modified) [fc10c6ae06]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:modified
- before the PR:
```lean
/-- Estimate for `log⁺` of a sum. See `Real.posLog_add` for a variant involving
just two summands. -/
```
- as the PR leaves it:
```lean
/-!
## Estimates for Sums
-/
```

### `module_doc in PosLog.lean` (module_doc, added) [fd86a8d338]
- file: `Mathlib/Analysis/SpecialFunctions/Log/PosLog.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
## Elementary Properties
-/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [hypothesis] `Real.posLog_norm_sum_le`, `Real.posLog_one`, `Real.posLog_pow`, `Real.posLog_zero` -- 4 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Real.posLog_one`, `Real.posLog_zero` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Real.posLog_one` -> `Real.posLog_zero`
- changed_siblings [high]: `Real.posLog_zero` -> `Real.posLog_one`
