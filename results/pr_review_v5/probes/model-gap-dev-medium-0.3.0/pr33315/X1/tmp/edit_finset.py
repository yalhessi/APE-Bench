import json
rep = """More information can be found in `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean`.

Finsets are directly used to define fintypes in Lean.
A `Fintype α` instance for a type `α` consists of a universal `Finset α` containing every term of
`α`, called `univ`. See `Mathlib/Data/Fintype/Defs.lean`.

`Finset.card`, the size of a finset is defined in `Mathlib/Data/Finset/Card.lean`.
This is then used to define `Fintype.card`, the size of a type.

## File structure

This file defines the `Finset` type and the membership and subset relations between finsets.
Most constructions involving `Finset`s have been split off to their own files.

## Main definitions

* `Finset`: Defines a type for the finite subsets of `α`.
  Constructing a `Finset` requires two pieces of data: `val`, a `Multiset α` of elements,
  and `nodup`, a proof that `val` has no duplicates.
* `Finset.instMembership`: Defines membership `a ∈ (s : Finset α)`.
* `Finset.instSetLike`: Provides a coercion `s : Finset α` to `s : Set α`, and through
  `SetLike` a coercion of `s : Finset α` to the type of all `x ∈ s`."""
print(json.dumps({"path":"Mathlib/Data/Finset/Defs.lean","line_start":34,"line_end":55,"replacement":rep}))
