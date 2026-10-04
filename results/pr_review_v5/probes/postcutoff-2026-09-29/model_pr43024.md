# The PR model for #43024 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: `isMulCommutative_anti` for subobjects
- description: (not recoverable at review start)
- changed files: Mathlib/Algebra/Group/Subsemigroup/Defs.lean

## Objects

### `setLike_mul_comm` (lemma, added) [45b54334c3]
- file: `Mathlib/Algebra/Group/Subsemigroup/Defs.lean`; changed: attributes:added, documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive /-- Commutativity of addition in commutative subobjects. -/ ]
lemma setLike_mul_comm {S M : Type*} [SetLike S M] [Mul M] [MulMemClass S M]
    {s : S} [IsMulCommutative s] ⦃a b : M⦄ (ha : a ∈ s) (hb : b ∈ s) :
    a * b = b * a :=
  isMulCommutative_iff_of_setLike.mp ‹_› a ha b hb
```

### `isMulCommutative_mono` (lemma, added) [5c7b53fec1]
- file: `Mathlib/Algebra/Group/Subsemigroup/Defs.lean`; changed: attributes:added, documentation:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive /-- Commutativity of addition passes to smaller subobjects. -/ ]
lemma isMulCommutative_mono {S M : Type*} [SetLike S M] [Mul M] [MulMemClass S M]
    [LE S] [IsConcreteLE S M] {s t : S} (h : s ≤ t) [IsMulCommutative t] :
    IsMulCommutative s :=
  .of_setLike_mul_comm fun _ ha _ hb ↦
    setLike_mul_comm (mem_of_le_of_mem h ha) (mem_of_le_of_mem h hb)
```

### `doc_comment in Defs.lean` (command, added) [ab53b1741f]
- file: `Mathlib/Algebra/Group/Subsemigroup/Defs.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Commutativity of multiplication passes to smaller subobjects. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `isMulCommutative_mono` -> `setLike_mul_comm`
