# Review notes: PR #41930 (Monoid.Coprod recursor motive rename)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. The workspace file is
`target/Mathlib/GroupTheory/Coprod/Basic.lean`. I read lines 1-330 with proofs shown.

## What the PR does

In `Monoid.Coprod.induction_on'` and `Monoid.Coprod.induction_on`, both `@[to_additive (attr :=
elab_as_elim)]`, the PR renames the implicit motive from `C` to `motive`. It also reflows the
`induction_on` signature over three lines, because `motive` is longer than `C`. No proof changes,
and no declaration is renamed or removed.

## Object by object

### `Monoid.Coprod.induction_on'` (and `AddMonoid.Coprod.induction_on'` via `to_additive`)
- correctness: the file compiles as the PR leaves it. `lean_verify_edit` with no edit returned
  `compiles: true`, no errors, no warnings. The proof still refers to the minor premises `one`,
  `inl_mul` and `inr_mul`, whose names did not change.
- naming: `motive` follows the convention for `elab_as_elim` motives. The sibling file
  `Mathlib/GroupTheory/CoprodI.lean` already uses `motive` (`induction_left`, `induction_on`,
  `consRecOn`, `smul_induction`). A Zulip search ("naming arguments to recursors") confirms the
  convention: the motive is `motive`, and minor premises are named after their content or
  constructor. The minor premises `one`, `inl_mul` and `inr_mul` already follow it.
- style: `(one : motive 1)` sits alone on its own line, although it would fit on the first
  signature line (74 chars). This is formatting from before the PR and a pure nit. I would not
  ask for it on a one-line housekeeping PR, so it is not filed.
- the major premise `m` is shadowed by the bound `∀ m x` in `inl_mul`. This predates the PR and is
  harmless, so it is not filed.
- proof-golf, generalization, duplication, documentation, scope: nothing to ask. The proof is
  unchanged. The hypotheses are the natural ones (`MulOneClass`). No other declaration duplicates
  it. The lemma has no docstring before or after, and Mathlib would not ask this PR to add one.

### `Monoid.Coprod.induction_on` (and its additive version)
- correctness: compiles, as above. The term proof `induction_on' m (by simpa using inl 1) ...`
  still refers to the minor premises `inl`, `inr` and `mul`, which are unchanged.
- naming: the minor premises `inl`, `inr` and `mul` give the case names that downstream
  `induction ... using Coprod.induction_on with | inl g => ...` uses in
  `Mathlib/GroupTheory/PushoutI.lean:179`, so they must not be renamed. The motive rename is
  correct.
- style: the new three-line wrap is within 100 columns and uses the standard 4-space continuation.
- downstream breakage: I searched the tree for `Coprod.induction_on` and for named-argument uses
  `(C := ...)`. The only use is the `induction ... using` in PushoutI, which does not depend on the
  motive's name. Nothing passes `C :=` to these lemmas, so the rename breaks nothing and needs no
  deprecation (a binder rename is not a declaration rename).

### File `Mathlib/GroupTheory/Coprod/Basic.lean`
- scope: these two are the only `elab_as_elim` or induction principles in the file (grep for
  `elab_as_elim|induction|{C |motive`), so the PR covers the whole file. The precedent search
  surfaced reviewer asks of the form "this one could be `motive`d too". Here no sibling in the file
  is left with `C`. Other files in `GroupTheory` still use `{C : ...}` motives:
  `Congruence/Defs.lean` (`Con.induction_on`, `induction_on₂`), `Coset/Defs.lean`
  (`QuotientGroup.induction_on`) and `PresentedGroup.lean`. They are unrelated to Coprod, and
  asking this PR to fix them would be scope creep, so nothing is filed.

## Not code findings (left out on purpose)
- The PR description says the minor premises are named "according to their contents". The diff
  renames only the motive; the minor premises already had content names before the PR. This
  concerns the description, not the code.

## Tools used
`describe`, `file_search`, `file_read`, `content_search` (three times), `precedent_search`,
`zulip_search`, and `lean_verify_edit` (compile check of the file as-is).

## Result
0 findings. The change is a complete and correct convention fix for this file, and I found no
concrete request a maintainer would plausibly make.
