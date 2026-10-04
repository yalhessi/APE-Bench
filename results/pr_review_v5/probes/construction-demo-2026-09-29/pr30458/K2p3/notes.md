# Pass 3 notes: PR #30458, statements and the family

Tool note: the file tools address the reviewed tree under the `target/` prefix
(`target/Mathlib/...`). `lean_verify_edit` takes the bare `Mathlib/...` path.

## Family A: `div_eq_inv_self`, `div_left_injective`, `div_left_inj` / `div_eq_self`, `div_right_injective`, `div_right_inj` (Group/Basic.lean)

The PR moves six `[Group G]` lemmas into two new sections. The right-cancel section is
`[DivInvMonoid G] [IsRightCancelMul G]`; the left-cancel section is
`[DivisionMonoid G] [IsLeftCancelMul G]`.

- **Usage (c1-c6).** One-sided clients can apply every member directly:
  `[DivInvMonoid R] [IsRightCancelMul R]` for the right members,
  `[DivisionMonoid R] [IsLeftCancelMul R]` for the left members. `simpa` closes the iff goals,
  and the `(· / x)` / `(x / ·)` forms match. Group and AddGroup clients still get all four by
  `simp`, and the additive names exist at the new generality. The pre-PR call-site spellings in
  Set/Finite.lean and Finset/Basic.lean, and `div_right_injective.eq_iff`, compile unchanged. So
  the `(b := b)` / `(G := G)` named arguments the PR adds at call sites are not needed by the
  statements. That is a proof-pass matter, and I did not file it.
- **Generalised statements (c7-c11).** Every weakening I tried fails. Dropping the mixin fails
  for `div_eq_inv_self`, `div_left_injective` and `div_eq_self`. Replacing `DivisionMonoid` by
  `DivInvMonoid` fails for `div_eq_self` and `div_right_injective`, and replacing it by
  `DivInvOneMonoid` fails for `div_eq_self`: the step `b⁻¹ = 1 ↔ b = 1` needs an injective
  inverse. The DivInvMonoid/DivisionMonoid asymmetry is forced by the proofs, and each section
  is as weak as the classes on hand allow.
- **Closure (c12-c17).** The key fact is that in a DivisionMonoid, `IsLeftCancelMul` and
  `IsRightCancelMul` imply each other. Both bridges compile (c12), and each left/right partner
  can be derived from the other under the opposite mixin via `inv_inj`/`inv_div`. So within
  DivisionMonoid the left/right split is artificial. A left-cancel-only client cannot get
  `div_left_inj` from simp (c13) until the bridge is supplied by hand (c14). The library has
  this bridge only for CommMagma (c37); that feeds finding 4. The iff members are exactly
  `.eq_iff` of the injectivity members, as in the mul family. The `left_eq_mul` /
  `mul_ne_left` / `mul_ne_mul_left`-style twins all compile for div (c15), but none existed
  before the PR either (c16). That gap is pre-existing, so I did not file it. The
  `IsUnit.div_left_inj` and `div_left_inj'` variants take a hypothesis on the divisor and do
  not overlap (c17).
- **Automation (c18-c19).** Erasing each of the four simp attributes makes `simp` fail, both at
  the new generality and for a Group. With the attributes in place `simp` closes all of them, so
  the attributes are load-bearing. The registrations follow the siblings: iff forms are simp,
  `Function.Injective` forms are not (as with `mul_left_inj` / `mul_left_injective` and
  `inv_inj` / `inv_injective`).
- **Binders/form (c20-c21).** The section names and variable lines match the file's
  `LeftCancelMonoid` / `RightCancelMonoid` sections. No binder changes explicitness. The fixed
  operand `b` stays implicit, as it was before the PR, whereas the mul twins take it explicitly;
  that is pre-existing. The bound-variable name differs between the twins (`a` vs `x`), which
  is harmless.

No findings on this family by itself. Its cross-cancel fact feeds finding 4.

## Family B: `Finset.card_le_card_div_left`, `Finset.card_le_card_div_right` (+ `card_le_card_div_self`)

The hypothesis family is confirmed from the statements: the two lemmas are the left/right pair
for `#(s / t)`. `card_le_card_div_self` depends on `_left`, and its instance context also
changed.

- **Usage (c22).** Group, AddGroup and `[DivisionMonoid R] [IsCancelMul R]` clients work.
- **Generalised (c23-c24).** `card_le_card_div_right` compiles unchanged at
  `[DivInvMonoid α] [IsRightCancelMul α]`, which is the generality the PR gives
  `div_left_injective`. `card_le_card_div_left` really needs DivisionMonoid. This is **finding 1**.
- **Twin (c25-c26).** The mul family has `card_le_card_mul_self` and `card_le_card_mul_self'`
  with cross-referencing docstrings. The div family has only the left-cancel `_self`. The
  right-cancel `card_le_card_div_self'` compiles at DivInvMonoid, and `card_le_card_sub_self'`
  is generated. This is **finding 2**.
- **One-sided client (c27).** A `[DivisionMonoid R] [IsLeftCancelMul R]` client cannot use
  `_right`. This feeds finding 4.
- **Binders/form (c28).** The PR nests `LeftCancel`/`RightCancel` inside a variable-less
  `section DivisionMonoid` and adds a third, line-broken variable line. The file uses two flat
  `IsLeftCancelMul` / `IsRightCancelMul` sections. This is **finding 3**.
- **Automation (c29).** The `@[to_additive]`-only registration matches the mul siblings.

## Family C: `Set.finite_div`, `Set.infinite_div`

- **Usage (c30-c31).** Group, AddGroup and IsCancelMul clients work. A left-cancel-only
  DivisionMonoid client fails.
- **Generalised (c32-c34).** Without a bridge the proofs need both mixins, and DivInvMonoid is
  insufficient even with IsCancelMul. With the four-line bridge, both lemmas hold under
  `[DivisionMonoid R] [IsLeftCancelMul R]` alone, so the second mixin is redundant. This is
  **finding 4**.
- **Binders/form (c35).** The pair-of-mixins spelling copies the neighbouring `section Cancel`
  (the only other use in Mathlib). The bundled `[IsCancelMul _]` has 26 uses in 21 files. The
  spelling is consistent with the file, so it is not a finding by itself.
- **Automation (c36).** No simp, like `finite_mul` / `infinite_mul`. Fine.
- **Closure (c37).** The CommMagma bridge lemmas exist as lemmas, not instances, and there is
  no DivisionMonoid analogue.

## Not established

I did not check whether Mathlib has any instance that is a one-sided-cancellative or
cancellative DivisionMonoid, or a right-cancel DivInvMonoid, but not a group; that is, whether
the generalisation has a consumer in the library today. On paper, `ℕ` under addition with
`inv = id` is a cancellative DivisionMonoid that is not a group, so the generalisation is not
vacuous. I did not compile that. It belongs to the "PR as a change" pass.
