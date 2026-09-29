# The PR model for #42184 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Topology/InfiniteSum): non-negativity of tprod
- description: A surprisingly missing lemma. Hopefully I didn't miss anything
- changed files: Mathlib/Topology/Algebra/InfiniteSum/Order.lean

## Objects

### `section in Order.lean` (command, added) [789611417d]
- file: `Mathlib/Topology/Algebra/InfiniteSum/Order.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section WithZero
```

### `tprod_nonneg` (theorem, added) [84eb374146]
- file: `Mathlib/Topology/Algebra/InfiniteSum/Order.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem tprod_nonneg [CommMonoidWithZero α] [TopologicalSpace α] [Preorder α] [ZeroLEOneClass α]
    [PosMulMono α] [ClosedIciTopology α] [L.NeBot] {f : ι → α} (hf : ∀ i, 0 ≤ f i) :
    0 ≤ ∏'[L] x, f x := by
  by_cases h : Multipliable f L
  · exact ge_of_tendsto' h.hasProd fun s ↦ s.prod_nonneg fun i _ ↦ hf i
  · simp [tprod_eq_one_of_not_multipliable h]
```

### `section in Order.lean` (command, added) [a1e044627e]
- file: `Mathlib/Topology/Algebra/InfiniteSum/Order.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end WithZero
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none
