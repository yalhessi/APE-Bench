# Review notes: PR #30458, chore(Algebra): misc. generalizations

## Method

- Read `brief.md`, `pr.md`, `model.md` and `diff.patch`. Read the changed regions in the workspace with `file_read`:
  - `target/Mathlib/Algebra/Group/Basic.lean` 560-830;
  - `target/Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean` 1180-1280;
  - `target/Mathlib/Algebra/Group/Pointwise/Set/Finite.lean` 95-160.
- Listed every `section`/`variable` line in Group/Basic.lean with `content_search`, to see the file's existing section layout.
- Ran `declaration_search` on every moved name (`div_left_injective`, `div_right_injective`, `div_left_inj`, `div_right_inj`, `div_eq_self`, `div_eq_inv_self`) and on the helpers `inv_eq_one` and `mul_left_injective`. No duplicate exists elsewhere. `IsUnit.div_left_inj` is a different statement. The only other hit for `div_left_injective` is the Batteries `simpa` regression test.
- Ran `lean_verify_edit` 14 times; every result below says `compiled`.
- Searched Zulip once, on DivisionMonoid/cancellation generalisations, and ran precedent_search once on `div_left_inj`. Neither turned up anything that applies directly.

## Main observation (convention: change existing code only where the purpose requires)

The PR's purpose is to weaken typeclass assumptions. Every pre-PR proof the PR touched still compiles verbatim under the weakened assumptions. So every proof rewrite in this PR is incidental. Verified with lean_verify_edit against the PR's workspace:

| declaration | pre-PR proof under the new assumptions |
|---|---|
| `div_left_injective` (verbatim, FIXME and `fun a ↦ a / b` included) | compiled |
| `div_right_injective` (verbatim, FIXME and `fun a ↦ b / a` included) | compiled |
| `div_left_inj` (`rw [div_eq_mul_inv, div_eq_mul_inv]; exact mul_left_inj _`) | compiled |
| `div_left_inj` as `div_left_injective.eq_iff` | compiled |
| `div_right_inj` (`div_right_injective.eq_iff`) | compiled |
| `Finset.card_le_card_div_left` (term-mode `have ⟨_, ha⟩ := …`) | compiled |
| `Finset.card_le_card_div_right` (term-mode) | compiled |
| `Set.finite_div` (`fun _ _ ↦ div_left_injective.injOn …`) | compiled |
| `Set.infinite_div` (same) | compiled |

The proof-change findings come from this table. The worst case is `div_left_inj`, where a 2-line proof became a 6-line manual one; I marked that one blocking.

## Object by object

- **`div_eq_inv_self`**: statement and proof unchanged; it stays at line 636 under a new section `RightCancelDivInvMonoid` with `[DivInvMonoid G] [IsRightCancelMul G]`. `mul_eq_right` needs only `MulOneClass` and `IsRightCancelMul`, so the generalisation is sound. Finding: the PR splits the one-liner over two lines for no reason (style/scope).
- **`div_left_injective`**: generalisation sound. Finding: revert the proof and binder rewrite (above).
- **`div_left_inj`**: generalisation sound. Finding: restore the short proof (blocking).
- **`div_eq_self`**: moved to `LeftCancelDivisionMonoid` (`[DivisionMonoid G] [IsLeftCancelMul G]`). It needs `inv_eq_one`, hence DivisionMonoid, which is the right level. Finding: the line split during the move is incidental.
- **`div_right_injective`**: only the binder (`a` → `x : G`) and the dropped `-- FIXME see above` differ from the original. The verbatim original compiles. I filed no separate finding, because the cost is small. A maintainer asking for a pure move would cover it together with the `div_left_injective` finding. Side note: `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` now compiles for `div_left_injective`, so the FIXME's `simpa` bug appears fixed. That golf is a separate, optional change. I did not ask for it, because it would itself be incidental to this PR.
- **`div_right_inj`**: Finding: drop the redundant `(G := G) (b := a)`.
- **Group/Basic.lean section layout**: the two new sections each serve three declarations and follow the file's existing `LeftCancelMonoid`/`RightCancelMonoid` pattern, so they are acceptable. One thing I noted without filing: the `DivInvMonoid`-level section sits after `DivisionCommMonoid`, which is out of the file's generality order. Moving it next to `section DivInvMonoid` (line 356) would compile, since its dependencies `mul_eq_right` and `mul_left_injective` come earlier. But it would enlarge the diff, and I am not confident a maintainer would ask for it.
- **Finset/Basic.lean, `card_le_card_div_left` / `card_le_card_div_right`**: generalisations sound. Findings: revert the proof rewrites.
- **Finset/Basic.lean section structure**: three `variable` lines, each serving one lemma, with nested `LeftCancel`/`RightCancel` sections. This breaks the second convention in the brief. Finding: one `variable [DivisionMonoid α] [DecidableEq α] {s t : Finset α}` plus the cancellation instances in the signatures. Verified with a line-mode edit of lines 1244-1270: compiled. The trailing `variable` is also needlessly wrapped across two lines.
- **`card_le_card_div_self`**: needs only `IsLeftCancelMul`, as written. No finding. A right-cancel `'` twin, mirroring `card_le_card_mul_self'`, would be scope creep.
- **Set/Finite.lean `section DivisionMonoid`**: the `variable` with both cancellation classes is shared by the two lemmas, and both are genuinely needed for `finite_image2`/`infinite_image2`. Fine. Findings only on the proof rewrites.

## Checked, not filed

- **Value of the generalisation**: an instance search over `target/Mathlib` found no Mathlib type that is a `DivisionMonoid` (or `DivInvMonoid`) with `IsLeftCancelMul`/`IsRightCancelMul` and is not already a group. Such structures exist mathematically: ℕ with addition and `-a := a` is a cancellative SubtractionCommMonoid. On Zulip, Anne Baanen is quoted as calling Group→DivisionMonoid generalisations less likely to be useful, and Kevin Buzzard as saying weaker classes can help typeclass inference. A maintainer might question whether these generalisations are worth having. That would be a question rather than a concrete change, so I filed no finding.
- **Naming**: no new names; every declaration keeps its name, so naming_norm does not apply.
- **Documentation**: none of the declarations had docstrings before, and the PR adds none. The only "documentation" removed is the FIXME comments, covered above.
- **Correctness**: every file compiles in the PR's workspace, and each edit I proposed compiles. No API breakage: names and argument implicitness are unchanged, and `b` stays implicit.
