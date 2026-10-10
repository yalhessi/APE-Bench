# Review notes: PR #30458, "chore(Algebra): misc. generalizations"

I read `pr.md`, `model.md` and `diff.patch`, then used `ptool` to read the three changed files (`target/...`) and to compile candidate edits with `lean_verify_edit`. The edit arguments are kept in `tmp/*.json`. Every proposed edit below was compiled. The changed files compile as the PR leaves them: no `errors_already_in_the_file` were reported in any run.

## Object by object

### Mathlib/Algebra/Group/Basic.lean
- **section RightCancelDivInvMonoid / LeftCancelDivisionMonoid (new) and the Group section (re-opened).**
  - The hypotheses match what each proof needs:
    - `mul_eq_right` and `mul_left_injective` need `IsRightCancelMul`.
    - `mul_eq_left` and `mul_right_injective` need `IsLeftCancelMul`.
    - `inv_eq_one` and `inv_injective` need the involutive inverse that `DivisionMonoid` provides.
  - Blank lines around section, variable and end are present.
  - Attributes are carried over unchanged:
    - `div_eq_inv_self`, `div_left_inj`, `div_eq_self` and `div_right_inj` keep `@[to_additive (attr := simp)]`.
    - The two injectivity lemmas keep `@[to_additive]`.
- **`div_eq_inv_self`.** The statement is unchanged. The proof is the same `rw`, now split over two lines although it fits on one (85 characters). Filed as style.
- **`div_left_injective`.**
  - The proof is convoluted: `have h'` plus `mul_right_cancel (a := …) (b := …) (c := …)`.
  - `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` compiles (test A/A2). The old FIXME said exactly this `simpa` failed, so deleting the FIXME is right, provided the proof takes that form.
  - The `: G` ascription is unneeded (A2). Filed (blocking).
- **`div_left_inj`.**
  - The proof duplicates `div_left_injective`'s argument, uses `constructor` + `intro`, and has `rintro rfl; rfl`.
  - `div_left_injective.eq_iff` compiles (D). The old `rw … ; exact mul_left_inj _` also compiles (E). Filed (blocking).
- **`div_eq_self`.** Same as `div_eq_inv_self`: a needless line split (90 characters on one line). Filed.
- **`div_right_injective`.**
  - The proof is unchanged, but the FIXME was deleted without adopting the `simpa` it asked for. `simpa only [div_eq_mul_inv] using (mul_right_injective b).comp inv_injective` compiles (H2).
  - The `a`→`x` rename and the `: G` are unneeded (G2). Filed (advisory).
- **`div_right_inj`.** The `(G := G) (b := a)` are unneeded: `div_right_injective.eq_iff` compiles (F). Filed.
- **Combined check.** A splice of lines 631-672 with all of the above proposed forms compiles (B).
- **Generalization.** I checked whether any lemma could go further.
  - `div_right_injective` needs injectivity of the inverse, so `DivisionMonoid` is the natural class.
  - `div_left_*` is already at `DivInvMonoid`.
  - The remaining `Group`-section lemmas need `a * a⁻¹ = 1`, so they cannot be generalized this way.
  - Nothing more to ask in this file.

### Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean
- **`card_le_card_div_left` / `card_le_card_div_right`.** Both were rewritten from term to tactic proofs with named `(b := …)`. The original term proofs compile unchanged (I, J). Filed as unnecessary changes.
- **`card_le_card_div_self`.** Unchanged apart from its section. Nothing to ask beyond the section layout.
- **Section layout.**
  - Three duplicated `variable` lines, each serving one lemma. Filed with a compiled restructure (K1; the alternative K2 also compiles).
  - No blank line after `section LeftCancel` / `section RightCancel`. Filed.
  - A needlessly broken `variable` line (80 characters joined). Filed.
- **Family check.**
  - The mul siblings have `card_le_card_mul_self'` (right-cancel). I did not ask for a `card_le_card_div_self'`: over a `DivisionMonoid`, left and right cancellation are equivalent (test R), so it would add nothing mathematically.

### Mathlib/Algebra/Group/Pointwise/Set/Finite.lean
- **`finite_div` / `infinite_div`.** The proof rewrites are unneeded: the original one-line proofs compile (L, L2). Filed.
- **Section variable.**
  - `[IsLeftCancelMul α] [IsRightCancelMul α]` is the unfolded form of `IsCancelMul`. `[DivisionMonoid α] [IsCancelMul α]` compiles (M, M2).
  - Over a `DivisionMonoid` the two mixins are equivalent (R compiled), so bundling them loses no generality. Filed as advisory.

### Sibling outside the diff
- **`Set.natCard_div_le`** (Set/Card.lean) is still at `[Group G]`. Under `[DivisionMonoid G] [IsCancelMul G]` it compiles (N). Filed as an advisory family completion.

### PR as a whole
- **Motivation.** The PR has none ("no intended use") and names no non-group instance. Filed as advisory.
- **Title and description.** The title "misc. generalizations" does not say what is generalized to what. Filed as advisory.

## Message: conventions ledger (filed places / left places)

1. **Reuse existing `variable`s.** Filed: Finset/Basic.lean DivisionMonoid section (three repeated variable lines). Left:
   - Group/Basic.lean's new sections need new typeclass variables. They reuse the file's `variable {α β G M : Type*}` (line 25).
   - Set/Finite.lean has a single section variable.
2. **Library-named predicate instead of its unfolding.** Filed: Set/Finite.lean line 139, `[IsLeftCancelMul α] [IsRightCancelMul α]` → `[IsCancelMul α]`. Left: Finset/Basic.lean, where each lemma uses only one of the two mixins, so there is no `IsCancelMul` to name.
3. **Drop unneeded hypotheses.** Filed indirectly through the Set/Finite.lean `IsCancelMul` finding, whose evidence shows `IsRightCancelMul` follows from `IsLeftCancelMul` in a `DivisionMonoid`. Left: every Group/Basic.lean lemma, because each proof uses its stated mixin (`mul_eq_right` / `mul_left_injective` need right-cancel, and so on). The checks compiled with exactly those assumptions.
4. **Derive from library API, do not reprove.** Filed: `div_left_inj` (use `div_left_injective.eq_iff`) and `div_left_injective` (use `mul_left_injective`).
5. **Blank line around section/variable/end.** Filed: Finset/Basic.lean `section LeftCancel` and `section RightCancel`. Left:
   - Group/Basic.lean: the lines `section RightCancelDivInvMonoid` / blank / `variable …`, and likewise for the others, already have the blank lines.
   - Set/Finite.lean: `section DivisionMonoid` / blank / `variable …` already has them.
6. **Binder kind follows inferability.** Left. The implicit `{b}` of `div_left_injective` / `div_right_injective` is inferred at every call site: the original call forms in I, J, L and L2 compile without `(b := …)`. It is the existing API.
7. **AI disclosure.** Left. pr.md says "All found by asking Codex to search for low-hanging generalization opportunities", which discloses that AI was used and how.
8. **A short tactic block that one term proves is written as the term.** Filed:
   - `div_left_inj` → `div_left_injective.eq_iff`;
   - `Finset.card_le_card_div_left` / `_right` → the original terms.
9. **Motivation for a design change.** Filed: PR description (no intended use and no non-group instance named).
10. **No `by exact` / `by simpa` around a term that already fits.** Filed:
    - `Finset.card_le_card_div_left` / `_right` (`by obtain …` / `exact …` where the term works);
    - `div_left_injective` (`simpa using (mul_right_cancel …)` after a `have`).
11. **Break lines only past 100 characters.** Filed: `div_eq_inv_self` (85 characters), `div_eq_self` (90), and the Finset `variable` line (80). Left:
    - The PR's two-line `finite_div` / `infinite_div` proofs would exceed 100 characters if joined. They are filed instead for reverting to the original one-liners (88 and 90 characters).
    - The proposed `div_left_injective` proof would be 124 characters on one line, so two lines is right.
12. **Arguments that can be inferred are not passed.** Filed:
    - `div_right_inj` (`(G := G) (b := a)`);
    - `Finset.card_le_card_div_left` / `_right` (`(b := …)`);
    - `Set.finite_div` / `Set.infinite_div` (`(b := …)`);
    - `div_left_injective` / `div_left_inj` (`mul_right_cancel (a := …) (b := …) (c := …)`).
13. **One tactic per line, no `;`.** Filed within the `div_left_inj` finding (`· rintro rfl; rfl`). Left: the restored original term proofs `have ⟨_, ha⟩ := hs; …` use term-level `;` in a `have`, not tactic sequencing, and are what the file had before.
14. **Attributes preserved on moved or generalized declarations.** Left. All six moved Group/Basic.lean lemmas keep their exact attributes, e.g. `@[to_additive (attr := simp)]` on `div_eq_inv_self`, `div_left_inj`, `div_eq_self` and `div_right_inj`, and `@[to_additive]` on both injectivity lemmas. The Finset and Set lemmas keep `@[to_additive]`.
15. **Provide the variant for the whole sibling family.** Filed: `Set.natCard_div_le` (still `Group`; compiles under `DivisionMonoid + IsCancelMul`). Left: `card_le_card_div_self'`, because left and right cancellation coincide over `DivisionMonoid` (R).
16. **Marginal-benefit changes.** Filed together with the motivation finding (PR description): the PR states no use for the generalization.
17. **Comments kept in step with the code.** Filed through the `div_right_injective` finding: the FIXME is deleted, but the proof does not take the `simpa` form the FIXME asked for, which now works (H2). Left: `div_left_injective`'s FIXME deletion is correct once its proof uses the `simpa` (A2).
18. **Title and description precise.** Filed: the PR title and description.
19. **`refine` binds its subgoals' hypotheses.** Filed within the `div_left_inj` finding (`constructor` then `intro h`), resolved by the term proof. Left: `div_left_injective`'s `intro a₁ a₂ h`, because it follows no `refine`/`constructor`, and the proposed proof removes it anyway.
20. **Change only what the purpose requires.** Filed:
    - `Finset.card_le_card_div_left` and `_right`;
    - `Set.finite_div` and `Set.infinite_div`;
    - `div_right_inj`;
    - the statement re-spellings (`: G`, `a`→`x`) in `div_left_injective` and `div_right_injective`;
    - the line splits of `div_eq_inv_self` and `div_eq_self`.
21. **Sections with the right typeclasses, not `omit`.** Left. The diff contains no `omit`, and each section declares exactly the classes its lemmas use.
22. **Close LLM code the submitter cannot revise.** Left. pr.md says "Hopefully I can get some feedback on this during review": the author asks to learn and revise, and the change is small.
23. **Do not state generality that no use needs.** Filed together with the motivation finding: the PR states no use for the generalization.
24. **A `variable` serves many declarations.** Filed: Finset/Basic.lean, where each sub-section variable serves one lemma. Left: Group/Basic.lean's new sections each serve three lemmas.
25. **Clean up AI-generated code.** Filed: `div_left_injective` and `div_left_inj` (convoluted `have` / `mul_right_cancel (a := …)` arguments).

## Tests run (all via `ptool lean_verify_edit`; arguments in `tmp/`)

| Test | File | Edit | Outcome |
|---|---|---|---|
| A, A2 | Basic.lean | `div_left_injective` by `simpa only … mul_left_injective b⁻¹` (with and without `: G`) | compiled |
| D | Basic.lean | `div_left_inj := div_left_injective.eq_iff` | compiled |
| E | Basic.lean | original `div_left_inj` proof | compiled |
| F | Basic.lean | `div_right_inj := div_right_injective.eq_iff` | compiled |
| G | Basic.lean | wrong composition (my error) | compile error, not used |
| G2 | Basic.lean | original `div_right_injective` statement and proof | compiled |
| H2 | Basic.lean | `div_right_injective` by `simpa only … (mul_right_injective b).comp inv_injective` | compiled |
| B | Basic.lean | combined proposed block, lines 631-672 | compiled |
| I, J | Finset/Basic.lean | original card lemma proofs | compiled |
| K1, K2 | Finset/Basic.lean | section restructures | compiled |
| L, L2 | Set/Finite.lean | original `finite_div` / `infinite_div` proofs | compiled |
| M, M2 | Set/Finite.lean | `IsCancelMul` variable (M2 also with original proofs) | compiled |
| R | Set/Finite.lean | `example`: `DivisionMonoid` + `IsLeftCancelMul` → `IsRightCancelMul` | compiled |
| N | Set/Card.lean | `natCard_div_le` under `DivisionMonoid + IsCancelMul` | compiled |

Other tools:
- `zulip_search` found nothing on cancellative division monoids. It did find that type-class generalization PRs are generally welcomed (#22337 thread), which is why the motivation finding is advisory.
- `precedent_search` gave nothing directly applicable.
