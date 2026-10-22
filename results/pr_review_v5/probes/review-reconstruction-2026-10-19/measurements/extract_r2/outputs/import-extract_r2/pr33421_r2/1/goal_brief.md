# Goal brief

## 1. Kind of contribution

- New results (the main part).
- Proof changes: `round_eq`, `round_two_inv`, `round_neg_two_inv`, `round_eq_zero_iff` in
  `Mathlib/Algebra/Order/Round.lean` get new proofs; statements unchanged.
- Maintenance (imports): the twelve packet files outside the floor, round and topology-of-floor files
  change only their imports.

## 2. Capability

α is a linearly ordered ring with floor and ceiling; `round` is the existing rounding (halves go up).
Call x *exceptional* when 2x is an odd integer (in a field, x = n + 1/2 with n ∈ ℤ).

1. For z ∈ ℤ, an identity for ⌈z + a⌉ in terms of z and ⌈a⌉ (integer on the left; the base has it on
   the right); also for z a natural number, z = 1, and z a numeral ≥ 2.
2. An expression of round x through floor or ceiling and integer arithmetic, with no division in α,
   so valid in every such α.
3. In a linearly ordered field, for n ∈ ℤ: round x = n ⟺ n − 1/2 ≤ x < n + 1/2.

With a topology compatible with the order, as in `Topology/Algebra/Order/Floor.lean`:

4. Floor and ceiling are continuous at each non-integer, and on the set of non-integers.
5. Near every x, round is constant on each side: on some [x, b) it equals round x; on some (c, x) it
   equals round x, or round x − 1 when x is exceptional.
6. Round is continuous at each non-exceptional point, and on the set of them.

## 3. What must keep working

- Every existing statement of `Round.lean`, including `round_eq` (round x = ⌊x + 1/2⌋ in a field).
- `Int.ceil_add_intCast`, `Int.ceil_add_natCast`, `Int.ceil_add_one`, `Int.ceil_add_ofNat`.
- `continuousOn_fract`, `continuousAt_fract` and the existing one-sided floor and ceiling limits.
- The special cases in item 1.
- Every downstream file builds.

## 4. Open questions

- The exact hypotheses for items 4-6.
- Whether 4 and 6 concern the maps into ℤ, their casts into α, or both.
- The topology file already has `continuousOn_floor` and `continuousOn_ceil` (local constancy on unit
  intervals, for the casts into α). Whether they stay, gain companions, or are restated is unsettled.
- Whether item 3 also wants a division-free form for rings.
- How the exceptional set and the non-integers are expressed.
- The inputs do not say why twelve files gain imports; which import adjustments the work needs is the
  designer's call.

## 5. Where the requirements come from

- No description: the PR had none at the start of review.
- The title "chore(Algebra/Order/Floor): review API about `round`" (current title, not verified to be
  the one at review time) grounds the focus on round.
- Items 1, 2-3 and 4-6: the change adds these results to `Algebra/Order/Floor/Ring.lean`,
  `Round.lean` and the topology file respectively.
- Sections 1 and 3: the change modifies the proofs of the four named round lemmas, keeps every
  statement listed in section 3, and edits only the imports of the twelve files.
