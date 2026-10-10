# Review notes: PR #30458 "chore(Algebra): misc. generalizations"

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Tools were called only through `./ptool`. The workspace files are under `target/`, and `lean_verify_edit` takes the `Mathlib/...` path.

Baseline: `lean_verify_edit` with no edit reports that `Mathlib/Algebra/Group/Basic.lean` and `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean` compile as the PR leaves them, with no errors or warnings.

## Mathlib/Algebra/Group/Basic.lean

I read lines 218-420 (the existing `LeftCancelMonoid`, `RightCancelMonoid`, `InvolutiveInv`, `DivInvMonoid` and `DivisionMonoid` sections) and lines 620-840 (the PR's two new sections and the remaining `Group` section).

- **`div_eq_inv_self`** (moved to `[DivInvMonoid G] [IsRightCancelMul G]`). `mul_eq_right` needs only `[Monoid M] [IsRightCancelMul M]`, so the hypotheses are right and minimal. The proof is unchanged apart from a line break. No finding.
- **`div_left_injective`**: finding 1 (proof-golf). The deleted FIXME's `simpa` one-liner, `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹`, now compiles. The PR's hand-rolled `intro`/`have`/`simpa using mul_right_cancel (a := ..) ..` proof is longer. The `: G` binder ascription is unneeded; the original `fun a ↦ a / b` compiles.
- **`div_left_inj`**: finding 2 (proof-golf). `div_left_injective.eq_iff` compiles, and so does the original `rw`/`mul_left_inj` proof. The PR's seven-line constructor proof is unnecessary.
- **`div_eq_self`** (moved to `[DivisionMonoid G] [IsLeftCancelMul G]`). It needs `mul_eq_left` (left cancel) and `inv_eq_one` (DivisionMonoid). `b⁻¹ = 1 → b = 1` fails in a bare `DivInvMonoid`, so `DivisionMonoid` is the right level. No finding.
- **`div_right_injective`**. The proof is the pre-PR one. The statement's binder changed from `fun a ↦ b / a` to `fun x : G ↦ b / x`. The original spelling compiles (verified), so this is harmless churn, and I did not raise it as a separate ask. `DivisionMonoid` is needed for `inv_injective`, since a separate `InvolutiveInv` would create a diamond. No finding.
- **`div_right_inj`**: finding 3 (style). `(div_right_injective (G := G) (b := a)).eq_iff` → `div_right_injective.eq_iff` compiles.
- The four proposed Basic.lean edits compile together (line-mode splice of lines 639-670: compiled).
- **Section names** `RightCancelDivInvMonoid` / `LeftCancelDivisionMonoid`, and their variable style `[Class G] [IsXCancelMul G]`, match the file's existing `LeftCancelMonoid` / `RightCancelMonoid` sections (`[Monoid M] [IsLeftCancelMul M]`). No finding.
- **Naming.** No declaration is renamed and no new name is introduced, so I made no naming ask.
- **Documentation.** The moved lemmas had no docstrings before and have none now. The module docstring still fits. No finding.
- **Duplication.** `declaration_search` finds each lemma once in the base and once in the PR, which confirms a move rather than a copy. The only other hit is `IsUnit.div_left_inj` in `Algebra/Group/Units/Basic.lean`, which is a different, unit-hypothesis lemma. No finding.

## Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

I read lines 1180-1280 and the file's section skeleton.

- **`Finset.card_le_card_div_right`**: finding 4 (generalization). It uses only `div_left_injective`, which the PR states for `DivInvMonoid` + `IsRightCancelMul`. Verified: the lemma compiles under `[DivInvMonoid α] [IsRightCancelMul α]`.
- **File section structure**: finding 5 (style). The PR has three redundant `variable` lines, a loose wrapped `variable` before `card_le_card_div_self`, and section names that differ from the file's `IsLeftCancelMul`/`IsRightCancelMul` siblings. The two-section layout compiles.
- **`Finset.card_le_card_div_left`** (with `_right`): finding 6. The original term proofs compile unchanged, so the `obtain`/`(b := a)` rewrites are noise.
- **`Finset.card_le_card_div_self`**. The statement and proof are unchanged, under `[DivisionMonoid α] [IsLeftCancelMul α]`, and this is correct. A primed right-cancel variant (as with `card_le_card_mul_self'`) would be possible, but I am not asking for a new lemma here.

## Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

I read lines 1-160.

- **`Set.finite_div` / `Set.infinite_div`**: finding 7, with the file as target. The original bodies compile under the new variable line, so the proof rewrites are noise.
- **Variable line** `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]`. Both cancellations are needed (`div_left_injective` uses the right one, `div_right_injective` the left one), and `DivisionMonoid` is needed for the latter. The two-class style matches the file's own `section Cancel` (`[Mul α] [IsLeftCancelMul α] [IsRightCancelMul α]`), so I did not ask for `[IsCancelMul α]`. No finding.

## Considered and not raised

- **Whether the generalization is useful at all.** The PR states no use case. `zulip_search` turned up Anne Baanen's view (reported by Vlad Tsyrklevich, PR-reviews thread on #22337) that Group→DivisionMonoid generalizations are less likely to be useful. A search of `Mathlib/Algebra/Group` for `IsLeftCancelMul|IsRightCancelMul|IsCancelMul` found no non-group cancellative `DivisionMonoid` instance. Mathematically, a cancellative DivisionMonoid need not be a group: Multiplicative ℕ with `inv = id` is one. Since I could not establish that a maintainer would ask for removal rather than merely question it, I did not file a finding.
- **`precedent_search`** on the `div_eq_self` block returned only unrelated comments (unit lemmas, a prime cleanup, WithTop instance renames).
- **Correctness.** All three files compile, and no semantic or API error was found. The `@[simp]` attributes are unchanged, and the `to_additive` translations (`IsRightCancelAdd`, `SubNegMonoid`, `SubtractionMonoid`) are automatic.
