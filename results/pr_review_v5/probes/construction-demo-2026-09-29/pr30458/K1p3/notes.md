# PR #30458, pass 3: statements and the family

This is a generalisation PR. Six division lemmas in `Algebra/Group/Basic.lean` move from `[Group G]`
to one-sided cancellative settings, and their Set and Finset consumers follow. The PR adds no new
statement shapes. The pass-3 question is whether the new hypotheses are the ones consumers hold, and
whether the split by cancellation side leaves them a closed family.

One mathematical fact runs through every family. **In a `DivisionMonoid`, `IsLeftCancelMul` and
`IsRightCancelMul` are equivalent** (c5 proves both directions in six lines: apply `⁻¹`, use
`mul_inv_rev`, cancel, then `inv_injective`). The PR treats the two sides as independent
hypotheses at DivisionMonoid, in Basic.lean, in the Finset file and in the Set file.

## Family 1: `div_eq_inv_self`, `div_left_injective`, `div_left_inj` (RightCancelDivInvMonoid); `div_eq_self`, `div_right_injective`, `div_right_inj` (LeftCancelDivisionMonoid)

- **Usage.** Group and AddGroup clients are unaffected. All six members and their additive names
  apply by plain terms (c1). A `[DivisionMonoid M] [IsCancelMul M]` client reaches both halves (c2).
  A one-sided client reaches only its half: a left-cancel client's `div_left_inj` and a right-cancel
  client's `div_right_inj` both fail with "failed to synthesize" (c3, c4). The same holds for simp
  (c16).
- **Generalised statements.** Each section is minimal for its proofs. Dropping `IsRightCancelMul`
  breaks `mul_eq_right` (c10). `div_eq_self` and `div_right_injective` need DivisionMonoid, via
  `inv_eq_one` and `InvolutiveInv` (c8, c9). But at DivisionMonoid each member also holds under the
  *other* side: `div_right_injective` from right cancellation (c6), `div_left_injective` from left
  cancellation (c7), and all four iff members once c5 is in scope (c12).
- **Closure.** `div_left_inj` is `div_left_injective.eq_iff` (c11), the usual inj/injective pairing.
  No member duplicates another. The missing pieces are the side-implication lemmas themselves. The
  area has exactly this pattern for `CommMagma`: four lemmas, not instances, in `Group/Defs.lean`
  (c35). The DivisionMonoid analogue exists neither at base nor in the PR. This is finding 2.
- **Automation.** Registrations match the siblings. Unconditional iff lemmas are simp in 7 of 7,
  `Function.Injective` lemmas in 0 of 5 (c17). The PR tags the four iff members simp and the two
  injectivity lemmas not. simp still closes the group forms (c13) and the new-generality forms under
  `IsCancelMul` (c15). The attribute is load-bearing: without it simp makes no progress (c14).
- **Binders and form.** The section names and unbundled `variable` lines follow the file's
  `LeftCancelMonoid` / `RightCancelMonoid` sections (c32). The implicit `b` of the injectivity
  lemmas is the base form (c37), and callers need no named arguments (c23, c24).

## Family 2: `Set.finite_div`, `Set.infinite_div`

- **Usage.** Group and AddCommGroup clients are fine (c25). A `[DivisionMonoid M] [IsLeftCancelMul M]`
  client fails on `finite_div` (c26).
- **Generalised statements.** Both lemmas hold under `[DivisionMonoid M] [IsLeftCancelMul M]` alone
  (c27), so `[IsRightCancelMul α]` in the PR's section is redundant. DivisionMonoid cannot drop to
  DivInvMonoid (c30). This is finding 1.
- **Closure.** The twin pattern `finite_mul` / `infinite_mul` versus `finite_div` / `infinite_div` is
  complete. Neither is simp, like their mul siblings.
- **Binders and form.** The split pair `[IsLeftCancelMul α] [IsRightCancelMul α]` appears in Mathlib
  only in this file: in its own `section Cancel`, and in the PR's copy of it. `[IsCancelMul _]` is
  used 26 times (c31). At DivisionMonoid neither spelling is needed; one side suffices.

## Family 3 (hypothesis confirmed): `Finset.card_le_card_div_left`, `Finset.card_le_card_div_right`, `Finset.card_le_card_div_self`

The statements are mirror images (`#t ≤ #(s / t)` from `s.Nonempty`, `#s ≤ #(s / t)` from
`t.Nonempty`), with `self` as the diagonal. The family is real.

- **Usage.** Group, AddGroup and CommGroup clients are fine (c18). A right-cancel DivisionMonoid
  client cannot get the self bound (c22). Callers need no `(b := _)` (c23).
- **Generalised statements.** `card_le_card_div_right` compiles at `[DivInvMonoid] [IsRightCancelMul]`
  with its proof unchanged (c20). That is the generality the PR gave `div_left_injective`. The left
  bound needs DivisionMonoid (c28). The left bound also holds for a right-cancel client via c5 (c21).
  This is finding 4.
- **Closure.** The file's mul pattern is left / right / self / self' (c34). The div family lacks
  `card_le_card_div_self'`. It compiles in the PR's RightCancel section (c19), and even at
  DivInvMonoid (c29). This is finding 3.
- **Binders and form.** `card_le_card_div_self` sits after `end RightCancel` under a third, repeated
  `variable` line. Moving it into `section LeftCancel` compiles (c33) and matches where
  `card_le_card_mul_self` sits (c34). This is finding 5. The section names `LeftCancel` / `RightCancel`
  differ from the file's `IsLeftCancelMul` / `IsRightCancelMul` (c32). That is left to the naming and
  layout pass.

## Observations outside this pass (not filed as findings)

- **Proofs.** `div_left_inj` could be `div_left_injective.eq_iff` (c11), as its sibling
  `div_right_inj` is. The `(b := _)` named arguments the PR adds at every call site are unnecessary:
  the base terms compile against the generalised lemmas (c23, c24).
- **The PR as a change.** Among the explicit DivisionMonoid instances in Mathlib, none is a
  non-group with a cancellation instance (c36). `NonemptyInterval` over an ordered comm group is
  mathematically a cancellative non-group DivisionCommMonoid, but it has no cancel instance. At base,
  the only concrete clients of the new generality are groups.

No finding is blocking. The PR's statements are correct and serve every existing client. Every
request concerns the closure and conciseness of the new one-sided generality.
