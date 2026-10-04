# Review notes: PR #30458 (chore(Algebra): misc. generalizations)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. All tool calls went through `./ptool`.
Workspace paths are prefixed with `target/`. `lean_verify_edit` builds against the PR's
workspace, so a downstream file sees the generalised Basic.lean. A deliberately wrong edit to
`Set.infinite_div` failed with a type mismatch, which shows the tool really compiles.

## Mathlib/Algebra/Group/Basic.lean

Read lines 216-420 (the existing `LeftCancelMonoid`, `RightCancelMonoid`, `InvolutiveInv`,
`DivInvMonoid` and `DivisionMonoid` sections) and 625-860 (the PR's new sections and the
`Group` section they were taken from).

- `div_eq_inv_self`: moved to `[DivInvMonoid G] [IsRightCancelMul G]`. `mul_eq_right` needs only
  `Monoid` plus `IsRightCancelMul`, so these hypotheses are right and minimal. The proof is
  unchanged apart from a line break. No finding.
- `div_left_injective`: the generalisation is fine, but the new proof is a longer manual one.
  The original proof compiles under the new hypotheses. The FIXME's `simpa` form
  (`simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹`) now works as well, so the
  deleted FIXME is resolved only if that form is used. **Finding (blocking, proof-golf).**
- `div_left_inj`: a six-line manual proof where `div_left_injective.eq_iff` works, matching
  `div_right_inj`. The original `rw …; exact mul_left_inj _` also works. **Finding (blocking,
  proof-golf).**
- `div_eq_self`: moved to `[DivisionMonoid G] [IsLeftCancelMul G]`. This needs `mul_eq_left`
  (left cancel) and `inv_eq_one` (DivisionMonoid). Hypotheses are fine and the proof is
  unchanged. No finding.
- `div_right_injective`: the hypotheses are the natural ones (it needs `inv_injective`, hence
  an involutive inverse). The PR removed `-- FIXME see above` but kept the workaround proof.
  `simpa only [div_eq_mul_inv] using (mul_right_injective b).comp inv_injective` compiles.
  **Finding (advisory, proof-golf).**
- `div_right_inj`: the `(G := G) (b := a)` named arguments are unnecessary; plain
  `div_right_injective.eq_iff` compiles. **Finding (advisory, style).**
- Section commands (`RightCancelDivInvMonoid`, `LeftCancelDivisionMonoid`, re-opened `Group`):
  the placement after `DivisionCommMonoid` and before `Group` is reasonable, and the names are
  close to the file's `LeftCancelMonoid`/`RightCancelMonoid`. No finding.
- Naming: every name is unchanged; the lemmas only move. `naming_norm` could not resolve a
  subject for `div_left_injective`, so naming is unmeasured, but no renames happen. No finding.
- Deprecations: none needed, because no name changes.
- The combined golfed block (lines 631-672: simpa `div_left_injective`, `.eq_iff` `div_left_inj`,
  simpa `div_right_injective`, `.eq_iff` `div_right_inj`, original one-line `div_eq_inv_self` and
  `div_eq_self`) compiles with no errors or warnings.
- Duplication: `declaration_search` found no other Mathlib `div_left_injective` (apart from a
  batteries test file). A content search found no other file using a
  `DivInvMonoid`/`DivisionMonoid` plus `Is*CancelMul` combination on a Latin-named type. Nothing
  existing is duplicated.

## Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

Read lines 1180-1280.

- `Finset.card_le_card_div_left`: the generalisation is fine. The proof was rewritten into
  tactic mode with `(b := a)`, but the original term proof compiles. **Finding (advisory,
  revert churn).**
- `Finset.card_le_card_div_right`: same churn, and the original proof compiles. **Finding
  (advisory).** It also needs only `DivInvMonoid` plus `IsRightCancelMul`, because it rests
  only on `div_left_injective`, but the PR assumes `DivisionMonoid`. A version under
  `DivInvMonoid` compiles. **Finding (advisory, generalization).**
- `Finset.card_le_card_div_self` and the section structure: the variable block for the left
  cancel section is redeclared at the outer level just for `card_le_card_div_self`, and the
  section names differ from the file's `IsLeftCancelMul`/`IsRightCancelMul` convention. The
  restructured layout compiles. **Finding (advisory, style).**
- I considered asking for a right-cancel twin `card_le_card_div_self'`, since the file has
  `card_le_card_mul_self'`. I did not file it: it adds new API beyond the PR's scope.

## Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

Read lines 1-160.

- Section variables `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]`: this matches
  the file's existing `section Cancel` (`[Mul α] [IsLeftCancelMul α] [IsRightCancelMul α]`), and
  both cancellations are genuinely used (`div_left_injective` needs right cancel,
  `div_right_injective` needs left cancel). I considered `[IsCancelMul α]` for brevity but did
  not file it, since the pair is the local convention.
- `Set.finite_div` and `Set.infinite_div`: the proofs were rewritten with explicit
  `(b := b)`/`(b := a)` and split over two lines, but the original one-liners compile.
  **Finding each (advisory, revert churn).**

## Other checks

- `precedent_search` on the new `div_left_injective` proof returned only loosely related
  comments: a request to add both left and right variants, and a suggestion to shorten a proof
  to one line. That is consistent with the golf asks, but I relied on no precedent.
- `zulip_search` on typeclass generalisations (Group to DivisionMonoid/CancelMonoid) found
  maintainers neutral to positive (e.g. Kevin Buzzard: weaker classes can ease instance search).
  So I did not file an ask to drop the generalisations as unmotivated.
- Documentation: no docstrings on the changed declarations. Removing the two FIXME comments is
  correct once the `simpa` proofs are used, and those are covered by the golf findings. The
  module docstring needs no change.
- Correctness: every file compiles as the PR leaves it (checked through the verify runs, which
  report no errors already in the files). No semantic or API errors found.
