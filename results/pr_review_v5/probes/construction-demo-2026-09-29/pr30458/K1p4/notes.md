# Pass 4 (proofs) — PR #30458

Point of view: the maintainer who keeps these proofs working through refactors. Every
construction was compiled with `lean_verify_edit` against the PR's workspace. c19 is a control:
a deliberately wrong proof is rejected, so the successful compiles are real. `proof_profile` was
unavailable ("no declaration table" for the base commit), so the idiom was read from the siblings
in the same files: Defs.lean:134-171, Finset/Basic.lean:1147-1215, Set/Finite.lean:99-111.
An as-is compile of Basic.lean reports no errors or warnings.

The pattern across the PR: every proof the generalisation touched still compiles in its pre-PR
form (c1, c6, c10, c14, c15, c16, c20-c23, c27, c28). Each rewritten proof is longer than the
original or carries named arguments tied to binder names, and none of the rewrites was needed.

## Basic.lean, RightCancelDivInvMonoid

- **div_eq_inv_self**: the proof is the pre-PR line, reflowed. The pre-PR proof compiles (c15), and
  `simp [div_eq_mul_inv]` also closes it (c17). No proof change requested.
- **div_left_injective**: the pre-PR `simp only; exact mul_left_injective b⁻¹ h` compiles at
  [DivInvMonoid] [IsRightCancelMul] (c1), because mul_left_injective lives in Defs.lean's
  IsRightCancelMul section. The PR deleted the FIXME ("could be by simpa, but it fails"), and
  that simpa now compiles: `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` (c2).
  Term forms (c3, c4) compile too. In the PR's own proof, the three named arguments on
  mul_right_cancel and the closing simpa are unnecessary (c5). -> finding 2.
- **div_left_inj**: the PR's six-line constructor proof repeats div_left_injective's fragment
  inline. `div_left_injective.eq_iff` compiles (c7). That is the pattern of mul_left_inj,
  mul_right_inj and the PR's own div_right_inj. The pre-PR proof also compiles (c6), as does
  `simp [div_eq_mul_inv]` (c8). -> finding 1 (blocking: a duplicated, longer proof, dependent on
  binder names and the simp set, where the library's one-token derivation compiles).

## Basic.lean, LeftCancelDivisionMonoid

- **div_eq_self**: the pre-PR line compiles (c16), and the simp form works too (c18). No change.
- **div_right_injective**: the proof is the pre-PR one with the FIXME deleted, and it compiles
  (c10). The FIXME's simpa compiles: `simpa only [div_eq_mul_inv] using (mul_right_injective b).comp
  inv_injective` (c11). Other forms (c12, c13) compile too. Pass 3 showed one injectivity lemma
  can be derived from the other through inv_div. Done at the proof level (c30), it needs a local
  IsRightCancelMul instance and five lines, so it is not an improvement. -> finding 2.
- **div_right_inj**: `(G := G) (b := a)` is unnecessary, since the pre-PR `div_right_injective.eq_iff`
  compiles (c14). -> finding 3.
- The recommended family, with rw one-liners, simpa one-liners and `.eq_iff`, compiles as a
  whole (c26).

## Finset/Basic.lean

- **card_le_card_div_left / card_le_card_div_right**: the statements are unchanged, and the PR
  rewrote term proofs into obtain/exact blocks with `(b := _)`. The pre-PR terms compile in the
  PR's sections, one at a time (c20, c21) and together (c28). They match the siblings
  card_le_card_mul_left/right. Routing through card_le_card_mul_left on t⁻¹ also compiles (c24),
  but it is simp-dependent and has the same hypotheses, so it brings nothing. -> finding 4.
- **card_le_card_div_self**: the proof is unchanged. Where it sits relative to the side sections
  (pass 3 c33) is a layout question, not a proof one.

## Set/Finite.lean

- **finite_div / infinite_div**: the only change is the named arguments `(b := b)`/`(b := a)`,
  which depend on Basic.lean's implicit-variable name. The pre-PR proofs compile, one at a time
  (c22, c23) and together (c27). The siblings finite_mul/infinite_mul use the anonymous form.
  Deriving from finite_mul on t⁻¹ compiles (c25), and so does extracting the repeated
  injectivity pair into a private lemma (c29); neither improves on the one-line image2 proofs.
  -> finding 5.

## Not established here

- I could not test that a rename in Basic.lean breaks the named-argument call sites downstream.
  `lean_verify_edit` compiles one file against the PR's built workspace. The coupling to binder
  names comes from reading the code, not from a compile.
- Statement-level questions (the one-sided hypotheses, the missing card_le_card_div_self') belong
  to pass 3 and are not raised again.
