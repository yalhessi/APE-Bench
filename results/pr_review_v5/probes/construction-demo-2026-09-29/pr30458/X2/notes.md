# Review notes: PR #30458, "chore(Algebra): misc. generalizations"

## What I did

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`.
- Located the workspace. The tools serve the PR state under `target/`. `file_read` on
  `target/Mathlib/Algebra/Group/Basic.lean` shows the new sections, which confirms it is the PR state.
- Read the relevant regions through `file_read`:
  - Basic.lean 1-200 and 216-420: the cancel-monoid sections and `mul_eq_left`/`mul_eq_right`.
    Line 134 sets `attribute [local simp] mul_assoc`, which likely explains the old `simpa` trouble.
  - Basic.lean 625-860: the new sections and the rest of `section Group`.
  - Finset/Basic.lean 1180-1285.
  - Set/Finite.lean 1-160.
- Checked every proposed edit with `lean_verify_edit` on the PR's workspace. As a sanity check, one
  deliberately wrong edit failed as expected: `div_left_inj := div_right_injective.eq_iff`, where
  `div_right_injective` is declared later.
- Ran `declaration_search`, `naming_norm`, `content_search` (two censuses), `zulip_search` and
  `precedent_search`.

## Object by object

### Mathlib/Algebra/Group/Basic.lean

- **Section structure.** The new sections are `RightCancelDivInvMonoid` (`[DivInvMonoid G]
  [IsRightCancelMul G]`) and `LeftCancelDivisionMonoid` (`[DivisionMonoid G] [IsLeftCancelMul G]`).
  - Their names follow the file's existing `LeftCancelMonoid`/`RightCancelMonoid` sections.
  - They are placed after `DivisionCommMonoid`, so `mul_eq_left`, `mul_eq_right` and `inv_eq_one`
    are all available. The placement is fine.
  - The hypotheses are mathematically right for each lemma. Right-cancel is needed for `a * b⁻¹`
    injective in `a`. Left-cancel plus an involutive inverse (so `DivisionMonoid`) is needed in `b`.
    `inv_eq_one` needs `DivisionMonoid` for `div_eq_self`. I found nothing weaker that would be
    reasonable.
- **`div_eq_inv_self`.** The statement is unchanged and the hypotheses are right. The proof is
  identical but now split over two lines, which is a trivial diff; not worth a request.
- **`div_left_injective`.** Finding: golf to `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹`
  (verified).
  - The old proof also still works (verified).
  - Batteries' `simpa.lean` test `div_left_inj_issue` shows the bug the removed FIXME referred to
    is fixed.
  - The `: G` ascription is unnecessary (verified without it).
- **`div_left_inj`.** Finding (blocking): the proof duplicates `div_left_injective`. It should be
  `div_left_injective.eq_iff` (verified). The old proof also still compiles (verified).
- **`div_eq_self`.** Only the line break changed. No request.
- **`div_right_injective`.** Finding: the FIXME was dropped without fixing it. The `simpa` form
  `(mul_right_injective b).comp inv_injective` compiles (verified). The binder rename to `x : G` is
  unnecessary.
- **`div_right_inj`.** Finding: the explicit `(G := G) (b := a)` is unnecessary.
  `div_right_injective.eq_iff` compiles (verified).
- **All the Basic.lean golfs together.** A line-mode edit of lines 631-672 with every suggestion
  applied compiles.
- **Naming.**
  - No declaration is renamed.
  - `naming_norm` on `div_left_injective` returned `subject_unresolved`, so naming is unmeasured.
  - The existing names follow the `div_left_inj`/`div_right_inj` convention (the side is where the
    varying argument sits). Nothing to request.
- **Generalization value (advisory finding).**
  - A census over all of Mathlib found that `DivInvMonoid`/`DivisionMonoid`/`Subtraction*` combined
    with a cancel class occurs only in this PR's own variable lines.
  - A census of `IsCancelMul`-family instances found no non-group cancellative `DivInvMonoid`.
  - I asked for the lemmas to stay in `Group` until there is an instance that needs the
    generalization. This is the least certain finding: a maintainer could accept it as harmless.
  - A related observation I did not submit: in a `DivisionMonoid`, left- and right-cancellation are
    equivalent, because `mul_inv_rev` and `inv_injective` give one from the other. So
    `[IsLeftCancelMul α] [IsRightCancelMul α]` on top of `DivisionMonoid` is mathematically
    redundant. Using that would need a new instance or lemma, and I judged it unlikely to be asked
    for here.

### Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

- **`Finset.card_le_card_div_left` and `Finset.card_le_card_div_right`.** Finding: the proof
  rewrites are unnecessary. Both original term proofs compile under the PR's hypotheses (verified),
  and the sibling `card_le_card_mul_right` uses the original style.
- **`Finset.card_le_card_div_right`.** Finding: it only needs `[DivInvMonoid α]
  [IsRightCancelMul α]`, which verified in a line-mode edit.
- **`card_le_card_div_self` and the trailing variable block.** Finding: the variable block
  duplicates `section LeftCancel` (and is wrapped although it fits on one line). Moving the lemma
  into `LeftCancel` compiles (verified).
- **Section names (not submitted).** The neighbouring sections in this file are named
  `IsLeftCancelMul`/`IsRightCancelMul`, while the new ones are `LeftCancel`/`RightCancel`. This is a
  cosmetic inconsistency, too minor to submit on its own.
- **Documentation.** The pre-PR lemmas had no docstrings and none were removed. No request.

### Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

- **Section rename and variables.** `section Group` becomes `section DivisionMonoid`, with
  `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]`.
  - Listing both cancel classes separately matches the `section Cancel` above
    (`[Mul α] [IsLeftCancelMul α] [IsRightCancelMul α]`), so no `IsCancelMul` request.
  - `finite_div` needs `div_right_injective`, so `DivisionMonoid` is needed. No further
    generalization is available.
- **`Set.finite_div` and `Set.infinite_div`.** Finding: the proof rewrites are unnecessary. The
  original one-liners compile (verified).

## Checked, nothing to request

- **Correctness.** Every lemma statement is unchanged. The file-level builds succeed. No semantic,
  API or deprecation problem, because the names are unchanged and the declarations only moved within
  the file.
- **Duplication.** No new declarations beyond the moved ones. `declaration_search` shows
  `div_left_injective` defined only in Basic.lean (plus the Batteries test).
- **Zulip and precedent searches.** Neither returned anything directly bearing on this change.

## Counts

9 findings (1 blocking, 8 advisory). The brief asks for no constructions.
