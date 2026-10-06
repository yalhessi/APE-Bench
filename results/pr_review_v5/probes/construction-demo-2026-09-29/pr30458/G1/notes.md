# Review notes: PR #30458 `chore(Algebra): misc. generalizations`

I read pr.md, model.md, diff.patch and the brief's convention items, then checked each item with
the ptool tools. Every proposed edit was compiled with `lean_verify_edit` against the PR's
workspace, and each one returned `compiled` with no errors. findings.json has 15 findings: 1
blocking, 14 advisory.

## Mathlib/Algebra/Group/Basic.lean

Overall: the PR generalizes six lemmas from `Group` into two new sections,
`[DivInvMonoid G] [IsRightCancelMul G]` and `[DivisionMonoid G] [IsLeftCancelMul G]`.

- **Is the generalization worth having? (blocking, PR-level)** I searched the base tree for
  instances of `DivisionMonoid`, `DivInvMonoid` and the cancellation classes. Every non-group
  carrier I found is either a transfer instance or not cancellative (it has a zero, or it is a
  pointwise Set/Finset/Filter). NonemptyInterval has no cancel instance. So I found no type the new
  statements reach beyond groups. Zulip quotes from Buzzard and Dillies against generality with no
  examples support asking for a motivating instance or dropping the change.
- **Are the hypotheses minimal? Checked, no finding.** `div_left_injective`, `div_left_inj` and
  `div_eq_inv_self` need only right cancellation and `div_eq_mul_inv`. `div_right_injective`,
  `div_right_inj` and `div_eq_self` also need inverse injectivity or `inv_eq_one`, so
  `DivisionMonoid` is needed.
  - The left/right asymmetry is forced by the mathematics, so I dropped the "siblings" item.
  - `div_eq_one` and `div_ne_one` do not generalize: `a / a = 1` fails in a non-group cancellative
    division monoid (for example ℕ+ with the trivial inverse). I dropped those sibling items.
- **`div_left_injective`:** the old proof compiles. `simpa only [div_eq_mul_inv] using
  mul_left_injective b⁻¹` also compiles, and Batteries now tests this exact simpa case
  (`div_left_inj_issue`), so the deleted FIXME is resolved. The finding asks for the one-liner and
  the original `fun a ↦ a / b`.
  - Binder kind of `b`: it was implicit before the PR too, so the PR did not change it. No finding.
- **`div_left_inj`:** `div_left_injective.eq_iff` compiles, and so does the old `rw`/`exact`. The
  finding asks for the `.eq_iff` term, which also removes `rintro rfl; rfl`.
- **`div_right_injective`:** the PR deletes the FIXME but keeps the workaround.
  `simpa only [div_eq_mul_inv] using (mul_right_injective b).comp inv_injective` with the original
  `fun a ↦ b / a` compiles. Finding.
- **`div_right_inj`:** `div_right_injective.eq_iff` compiles without `(G := G) (b := a)`. Finding.
- **`div_eq_inv_self` and `div_eq_self`:** each gained a line break although it fits on one line
  (85 and about 90 characters). Two advisory findings. All six lemmas together with the proposed
  proofs compiled in one line-mode edit of lines 631-672.
- **Variable letter `G`: no finding.** The file already uses `G` for `DivInvMonoid` and
  `InvolutiveInv`, and Yaël Dillies on Zulip calls division monoids group-like, so `G` fits.
- **Section names `RightCancelDivInvMonoid` / `LeftCancelDivisionMonoid`: no finding.** They match
  the file's `LeftCancelMonoid` / `RightCancelMonoid`.
- **Existing-API duplication: no finding.** `IsUnit.div_left_inj` exists but takes an `IsUnit`
  hypothesis, a different shape.
- **simp attributes: no finding.** They are kept, and the generalized simp lemmas raise no
  correctness issue. Typeclass-search cost was not measured, so I make no claim about it.

## Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

- **`card_le_card_div_left` / `card_le_card_div_right`:** the pre-PR term proofs compile unchanged
  under the new hypotheses. Two findings to restore them.
- **`card_le_card_div_right`:** it needs only `DivInvMonoid` plus `IsRightCancelMul`. Compiled;
  advisory finding to generalize it, only if the generalization is kept at all.
- **Trailing `variable` after `end RightCancel`:** it duplicates `LeftCancel`'s binders and is
  needlessly split across two lines. Moving `card_le_card_div_self` into `LeftCancel` compiled.
  Finding.
- **Blank line after `section LeftCancel`/`RightCancel` and single-use sections: no separate
  finding.** The file's own `section CancelMonoid` puts `variable` directly after `section`, so the
  blank-line item does not hold locally. The single-use sections are subsumed by the restructure
  finding.

## Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

- **`finite_div` / `infinite_div`:** the pre-PR one-liners (`div_left_injective.injOn` with no
  named args) compile. Two findings.
- **The two mixins:** `[IsCancelMul α]` compiles. The library uses `IsCancelMul` in 11 files; the
  paired spelling appears only in this file's `Cancel` section. Advisory, because the author asked
  whether the assumptions could be more concise.
- **Weakening `DivisionMonoid`: not possible.** `div_right_injective` needs it.

## PR-level

- **Motivation:** covered by the blocking finding.
- **Title and description:** they name nothing that changes. Advisory finding.
- **Splitting the PR: no finding.** The Finset and Set changes depend on the Basic.lean ones and
  only make sense with them, so a split would be arbitrary.
