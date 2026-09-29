# PR #30458 review notes (X3)

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then ran `ptool describe`. The file tools
use the `target/` prefix. The workspace was populated only after the first `lean_verify_edit` call.
I read the changed regions of all three files as the PR leaves them (`file_read`), plus the
cancellation lemmas in `Group/Defs.lean` (`content_search`). I tested every alternative proof I
propose with `lean_verify_edit`, and every one I cite returned success with no errors or warnings.
I also compiled `Group/Basic.lean` as the PR leaves it (as-is check): it compiles.

## Mathlib/Algebra/Group/Basic.lean

- **Section layout**: the new sections are `RightCancelDivInvMonoid`
  (`[DivInvMonoid G] [IsRightCancelMul G]`) and `LeftCancelDivisionMonoid`
  (`[DivisionMonoid G] [IsLeftCancelMul G]`). Both follow the file's own `LeftCancelMonoid` /
  `RightCancelMonoid` naming, and their position, after `DivisionCommMonoid` and before `Group`,
  is sensible. No finding.
- **Hypotheses**: each lemma's assumptions are right. `div_left_injective`, `div_left_inj` and
  `div_eq_inv_self` need only right cancellation. `div_right_injective`, `div_right_inj` and
  `div_eq_self` need left cancellation plus `InvolutiveInv` / `inv_eq_one`, and `DivisionMonoid`
  provides those. I found no further weakening worth asking for. No finding.
- **`div_eq_inv_self`, `div_eq_self`**: the statements are unchanged. The one-line `by rw [...]`
  was split onto two lines, which is unnecessary but harmless. I left it out of the findings
  because it is too minor to be a likely request.
- **`div_left_injective`**: the proof became longer and uses named arguments to
  `mul_right_cancel`. The original proof still works, because `mul_left_injective` needs only
  `IsRightCancelMul`. `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` also works now,
  so the old FIXME is resolved. Filed as a finding.
- **`div_left_inj`**: six lines where `div_left_injective.eq_iff` suffices. Filed as a finding.
- **`div_right_injective`**: the proof is unchanged, but the FIXME was deleted. `simpa` now works:
  `simpa only [div_eq_mul_inv] using (mul_right_injective b).comp inv_injective`. Filed as a
  finding.
- **`div_right_inj`**: the `(G := G) (b := a)` named arguments are unnecessary, and the original
  `div_right_injective.eq_iff` compiles. Filed as a finding.
- **Naming**: no declaration is renamed, and the `to_additive` names are unchanged. No finding.
- **Documentation**: the moved lemmas had no docstrings before the PR. No finding.
- **Duplication**: `content_search` finds no other place in Mathlib that uses
  `[DivInvMonoid/DivisionMonoid] + [Is*CancelMul]`, so the new lemmas duplicate nothing. No
  finding.

## Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

- **`card_le_card_div_left`, `card_le_card_div_right`**: the proofs were rewritten from term-mode
  `have ⟨_, ha⟩ := …; …` to `obtain`/`exact` with named arguments. The original proofs compile
  under the new hypotheses, and the siblings `card_le_card_mul_left/right` use the term style.
  Filed two findings: revert each proof.
- **Section structure**: the outer `section DivisionMonoid` has no variables, and the variable
  line is repeated three times, the third time dangling and split across two lines. The file's
  convention names these sections `IsLeftCancelMul` / `IsRightCancelMul`. I verified a
  restructure (shared variables in the outer section, the mixin in each subsection,
  `card_le_card_div_self` moved into the left-cancel subsection). Filed as a finding.
- **`card_le_card_div_self`**: its statement and proof are unchanged. It is left-cancel only,
  while the `mul` API has both `card_le_card_mul_self` and `card_le_card_mul_self'`. I verified a
  right-cancel `card_le_card_div_self'`, and `declaration_search` shows no such lemma exists.
  Filed as an advisory finding.

## Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

- **Hypotheses**: `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]` matches the
  sibling `section Cancel` (`[Mul α] [IsLeftCancelMul α] [IsRightCancelMul α]`). For that reason
  I did not ask for `[IsCancelMul α]`.
- **`finite_div`, `infinite_div`**: the proofs were rewritten with named `(b := …)` arguments and
  line splits, and the original one-liners still compile. Filed two findings: revert each proof.
- **Section name**: `DivisionMonoid` is acceptable. No finding.

## Considered and not filed

- **Whether the generalization is useful**: no Mathlib instance of a non-group cancellative
  division monoid turned up (a content search found the combination only in this PR). A
  maintainer might ask for a use case, but that is a question, not a concrete change, so I did
  not file it.
- **Commit type**: whether "chore" is the right commit type for a generalization is not a code
  issue.
- **Tools that turned up nothing to act on**: `zulip_search` for cancellative division monoid
  generalizations and `precedent_search` on the new `div_left_injective` code found nothing
  directly applicable. The closest precedent was Eric Wieser's "Does the one below generalize in
  the same way?", which loosely motivates the `card_le_card_div_self'` finding.
