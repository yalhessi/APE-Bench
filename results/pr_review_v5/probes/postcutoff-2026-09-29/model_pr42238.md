# The PR model for #42238 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: perf(Analysis/Normed/Operator/LinearIsometry): scope the four-ring variables to their two users
- description: The top `variable` block of this file declares a fourth ring `R₄`, a carrier type `E₄`, six ring homomorphisms, and 15 instance binders for them. Only two of the file's ~295 declarations use the fourth ring: `LinearIsometry.comp_assoc` and `LinearIsometryEquiv.trans_assoc`. All other declarations carry these instances in their local context. Every typeclass search for `RingHomInvPair` or `RingHomCompTriple` must examine them.

This PR removes the fourth-ring variables from the top `variable` block. Each of the two theorems now sits in a small `section` that declares only the variables that theorem needs.

The two statements do not change. A dump of all constant types in the module shows that every other declaration keeps its exact type. The two theorems keep the same hypotheses and the same explicit arguments. Only the order of their implicit and instance binders changes. Mathlib contains no `@`-application of either theorem.

Standalone elaboration of the file goes from 9.08 s to 7.10 s (medians of 6 interleaved runs, −22 %). The `!bench` result in this thread shows −26 % instructions for this module, but it ran on an earlier revision that used explicit binders in place of the sections. A new `!bench` is necessary.

The mechanism is the same as in #42214.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
- changed files: Mathlib/Analysis/Normed/Operator/LinearIsometry.lean

## Objects

### `section in LinearIsometry.lean` (command, added) [7a8ad8c0f5]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {R₄ E₄ : Type*} [Semiring R₄] [SeminormedAddCommGroup E₄] [Module R₄ E₄]
  {σ₁₄ : R →+* R₄} {σ₄₁ : R₄ →+* R} {σ₂₄ : R₂ →+* R₄} {σ₄₂ : R₄ →+* R₂}
  {σ₃₄ : R₃ →+* R₄} {σ₄₃ : R₄ →+* R₃}
  [RingHomInvPair σ₁₄ σ₄₁] [RingHomInvPair σ₄₁ σ₁₄] [RingHomInvPair σ₂₄ σ₄₂]
  [RingHomInvPair σ₄₂ σ₂₄] [RingHomInvPair σ₃₄ σ₄₃] [RingHomInvPair σ₄₃ σ₃₄]
  [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄] [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄] [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄]
  [RingHomCompTriple σ₄₂ σ₂₁ σ₄₁] [RingHomCompTriple σ₄₃ σ₃₂ σ₄₂] [RingHomCompTriple σ₄₃ σ₃₁ σ₄₁]
```

### `section in LinearIsometry.lean` (command, added) [aadc6766cc]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end assoc
```

### `section in LinearIsometry.lean` (command, added) [c378213602]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section assoc
```

### `section in LinearIsometry.lean` (command, modified) [e527296c8f]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: namespace:modified
- before the PR:
```lean
variable {R R₂ R₃ R₄ E E₂ E₃ E₄ F 𝓕 : Type*} [Semiring R] [Semiring R₂] [Semiring R₃] [Semiring R₄]
  {σ₁₂ : R →+* R₂} {σ₂₁ : R₂ →+* R} {σ₁₃ : R →+* R₃} {σ₃₁ : R₃ →+* R} {σ₁₄ : R →+* R₄}
  {σ₄₁ : R₄ →+* R} {σ₂₃ : R₂ →+* R₃} {σ₃₂ : R₃ →+* R₂} {σ₂₄ : R₂ →+* R₄} {σ₄₂ : R₄ →+* R₂}
  {σ₃₄ : R₃ →+* R₄} {σ₄₃ : R₄ →+* R₃} [RingHomInvPair σ₁₂ σ₂₁] [RingHomInvPair σ₂₁ σ₁₂]
  [RingHomInvPair σ₁₃ σ₃₁] [RingHomInvPair σ₃₁ σ₁₃] [RingHomInvPair σ₂₃ σ₃₂]
  [RingHomInvPair σ₃₂ σ₂₃] [RingHomInvPair σ₁₄ σ₄₁] [RingHomInvPair σ₄₁ σ₁₄]
  [RingHomInvPair σ₂₄ σ₄₂] [RingHomInvPair σ₄₂ σ₂₄] [RingHomInvPair σ₃₄ σ₄₃]
  [RingHomInvPair σ₄₃ σ₃₄] [RingHomCompTriple σ₁₂ σ₂₃ σ₁₃] [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄]
  [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄] [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄] [RingHomCompTriple σ₃₂ σ₂₁ σ₃₁]
  [RingHomCompTriple σ₄₂ σ₂₁ σ₄₁] [RingHomCompTriple σ₄₃ σ₃₂ σ₄₂] [RingHomCompTriple σ₄₃ σ₃₁ σ₄₁]
  [SeminormedAddCommGroup E] [SeminormedAddCommGroup E₂] [SeminormedAddCommGroup E₃]
  [SeminormedAddCommGroup E₄] [Module R E] [Module R₂ E₂] [Module R₃ E₃] [Module R₄ E₄]
  [NormedAddCommGroup F] [Module R F]
```
- as the PR leaves it:
```lean
variable {R R₂ R₃ E E₂ E₃ F 𝓕 : Type*} [Semiring R] [Semiring R₂] [Semiring R₃]
  {σ₁₂ : R →+* R₂} {σ₂₁ : R₂ →+* R} {σ₁₃ : R →+* R₃} {σ₃₁ : R₃ →+* R}
  {σ₂₃ : R₂ →+* R₃} {σ₃₂ : R₃ →+* R₂} [RingHomInvPair σ₁₂ σ₂₁] [RingHomInvPair σ₂₁ σ₁₂]
  [RingHomInvPair σ₁₃ σ₃₁] [RingHomInvPair σ₃₁ σ₁₃] [RingHomInvPair σ₂₃ σ₃₂]
  [RingHomInvPair σ₃₂ σ₂₃] [RingHomCompTriple σ₁₂ σ₂₃ σ₁₃] [RingHomCompTriple σ₃₂ σ₂₁ σ₃₁]
  [SeminormedAddCommGroup E] [SeminormedAddCommGroup E₂] [SeminormedAddCommGroup E₃]
  [Module R E] [Module R₂ E₂] [Module R₃ E₃]
  [NormedAddCommGroup F] [Module R F]
```

### `section in LinearIsometry.lean` (command, added) [faab7c9256]
- file: `Mathlib/Analysis/Normed/Operator/LinearIsometry.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {R₄ E₄ : Type*} [Semiring R₄] [SeminormedAddCommGroup E₄] [Module R₄ E₄]
  {σ₁₄ : R →+* R₄} {σ₂₄ : R₂ →+* R₄} {σ₃₄ : R₃ →+* R₄}
  [RingHomCompTriple σ₁₂ σ₂₄ σ₁₄] [RingHomCompTriple σ₂₃ σ₃₄ σ₂₄] [RingHomCompTriple σ₁₃ σ₃₄ σ₁₄]
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none
