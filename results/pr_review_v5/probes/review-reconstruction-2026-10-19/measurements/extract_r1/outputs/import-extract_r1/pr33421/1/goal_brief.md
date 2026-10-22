# Goal brief

## 1. Kind of contribution

- New results.
- Generalization of existing results: `continuousOn_floor`, `continuousOn_ceil`
  (`Mathlib/Topology/Algebra/Order/Floor.lean`).
- Proof changes: `round_eq`, `round_two_inv`, `round_neg_two_inv`, `round_eq_zero_iff`,
  `continuousOn_fract`, `continuousAt_fract`.
- Maintenance (imports): `Round.lean`, the topology file above, and the twelve other packet files,
  whose only change is their imports.

## 2. Capability

α is a linearly ordered ring with a floor function; ℤ is discrete; `round` is the existing function
(halves round up).

1. ⌊·⌋ and ⌈·⌉ are locally constant, so continuous, near every x ∉ ℤ, and continuous on α ∖ ℤ.
2. `round` is constant on some [x, x + ε), with value round x, and on some (x − ε, x), with value
   round x except at half-odd-integers (2x odd), where it is round x − 1.
3. `round` is continuous at every x with 2x not an odd integer, and on that set.
4. A closed formula for round x valid in every such α, not only in fields (the existing `round_eq`,
   round x = ⌊x + 1/2⌋, needs a field).
5. Over a field, for n ∈ ℤ: round x = n ⟺ n − 1/2 ≤ x < n + 1/2.
6. ⌈z + a⌉ = z + ⌈a⌉ for an integer z added on the left (existing lemmas such as
   `Int.ceil_add_intCast` add it on the right).

## 3. What must keep working

- The existing statements in `Round.lean`, including `round_eq`, `round_two_inv` (round(1/2) = 1),
  `round_neg_two_inv` (round(−1/2) = 0), `round_eq_zero_iff` (item 5 at n = 0), `abs_sub_round`.
- The statements of `continuousOn_fract`, `continuousAt_fract` and the one-sided limit lemmas for
  floor and ceiling, such as `tendsto_floor_right_pure_floor`.
- The right-translation ceiling lemmas; item 6 also for z a natural number, z = 1, z a numeral.
- Every dependent module still builds.

## 4. Open questions

- Generality: which topological and order-algebraic hypotheses each of items 1-3 needs; whether
  item 5 also wants a division-free form over rings.
- How to express the exceptional set (item 3) and the left value (item 2).
- Whether floor/ceiling continuity concerns the integer-valued maps, their casts into α, or both,
  and what that means for `continuousOn_floor`, `continuousOn_ceil` (stated for the casts) and
  their users.
- Whether `round`'s definition may change.
- How far the "review" reaches: which existing proofs are re-derived.
- No input states the purpose of the import changes.
- Whether item 6 belongs, since the title names only `round`.

## 5. Where the requirements come from

- Description: none at the start of review.
- Title (current, not verified to be the one at review time): "chore(Algebra/Order/Floor): review
  API about `round`": the focus on `round` and the clean-up character.
- The change itself: it adds results providing items 1-6 and the special cases of item 6; it
  modifies the proofs of the six lemmas listed under 1; it changes `continuousOn_floor` and
  `continuousOn_ceil`; it changes only imports in twelve files; it keeps the statements under 3.
