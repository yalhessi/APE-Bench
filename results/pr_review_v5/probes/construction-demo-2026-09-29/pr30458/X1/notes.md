# Review notes: PR #30458 (chore(Algebra): misc. generalizations)

I read pr.md, model.md and diff.patch, and used only `./ptool` (file_read, content_search,
declaration_search, lean_verify_edit, zulip_search, precedent_search). Workspace paths are
`target/Mathlib/...`. A baseline compile of Basic.lean as the PR leaves it succeeds. A negative
control (a deliberately wrong `div_right_inj := div_left_injective.eq_iff`) fails with a type
mismatch, so the tool does reject bad edits.

Overall: the generalizations are mathematically correct and everything compiles. The main issue is
diff churn. Every downstream proof the PR rewrites still compiles in its original form under the
new assumptions, and two Basic.lean proofs got longer rather than shorter.

## Mathlib/Algebra/Group/Basic.lean

- **Section structure** (`RightCancelDivInvMonoid` with `[DivInvMonoid G] [IsRightCancelMul G]`,
  `LeftCancelDivisionMonoid` with `[DivisionMonoid G] [IsLeftCancelMul G]`): these follow the file's
  existing `section LeftCancelMonoid` / `section RightCancelMonoid` pattern (lines 218-306). The
  assumptions are minimal:
  - The `DivInvMonoid` lemmas need only `div_eq_mul_inv` and right cancellation.
  - The `DivisionMonoid` lemmas need `inv_eq_one` / `inv_injective`, and `InvolutiveInv` cannot be
    added as a separate mixin without a second `Inv`.

  Nothing to request.
- **`div_eq_inv_self`**: the statement and proof are unchanged apart from a line break. `mul_eq_right`
  holds under `IsRightCancelMul`. I request keeping the one-liner (advisory; verified).
- **`div_left_injective`**: the PR's manual proof is longer than needed. The FIXME's `simpa` now
  works: `simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` (verified). The original proof
  also compiles (verified).
- **`div_left_inj`**: a six-line proof where `div_left_injective.eq_iff` or the original rw/exact
  proof works (both verified).
- **`div_eq_self`**: unchanged apart from a line break; I request the one-liner (verified).
- **`div_right_injective`**: the FIXME was dropped but not resolved. A `simpa` proof now works
  (verified). The binder was needlessly renamed from `a` to `x`.
- **`div_right_inj`**: the named arguments `(G := G) (b := a)` are unnecessary;
  `div_right_injective.eq_iff` compiles (verified).
- **Checked, nothing to request:**
  - Names are unchanged, so no deprecations are needed (the lemmas moved within one file).
  - The `to_additive` versions compile.
  - None of these short lemmas had a docstring before, and none is expected now.
  - The `simp` attributes are kept.
  - The trimmed variable line `{a b c : G}` (no `d`, `n`) is fine.

## Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

- **`card_le_card_div_left` / `card_le_card_div_right`**: the original term-mode proofs
  (`have ⟨_, ha⟩ := hs; ...`) compile unchanged (verified) and match the sibling
  `card_le_card_mul_left` / `card_le_card_mul_right`. I request restoring them.
- **`card_le_card_div_right`** can be stated under `[DivInvMonoid α] [IsRightCancelMul α]`, like the
  Basic.lean section it applies. I verified a restructured block that compiles.
- **`card_le_card_div_self` / section layout**: the stray duplicated `variable` after
  `end RightCancel`, and the redundant outer section, should go. The lemma belongs in the
  left-cancel section. The section names depart from the file's `IsLeftCancelMul` /
  `IsRightCancelMul` convention.
- **Considered, not requested:** a right-cancel counterpart `card_le_card_div_self'`, mirroring
  `card_le_card_mul_self'`. That would be new API beyond the PR's scope, and nothing in the PR
  motivates it.

## Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

- **`finite_div` / `infinite_div`**: the original one-line proofs compile under the new assumptions
  (verified), so the rewrite with named arguments is churn. I request reverting both.
- **Assumptions**: `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]` matches the sibling
  `section Cancel` (line 101), which also uses the two separate mixins. So I do not ask for
  `[IsCancelMul α]`, even though the author asks whether the assumptions could be stated more
  concisely.

## Considered at PR level, not requested

- **Value of the generalization.** I searched for DivisionMonoid instances in the base tree. Every
  non-group one I found (Set, Finset, Filter, WithZero, NonemptyInterval/Interval, LinearPMap) is
  non-cancellative or has no cancel instance, so no current Mathlib type other than a group seems to
  gain these lemmas. A model does exist: ℕ with trivial negation is a cancellative
  SubtractionMonoid, so the hypotheses are not vacuous.

  On Zulip (#22337 thread), Anne Baanen is reported as calling Group → DivisionMonoid a less useful
  generalization, while Kevin Buzzard noted that weaker classes can help typeclass inference. That
  is a judgement call, and "provide a motivating instance" is a question rather than a concrete
  change, so I did not file it as a finding.
- **Naming**: all names already existed at the base commit, and renaming is out of scope. No
  naming finding.
- **Duplication**: I found no pre-existing generalized versions of these lemmas. declaration_search
  finds `div_left_injective` only in Group/Basic.lean, plus a BatteriesTest file.
