# Review notes: PR #41930 (fix(GroupTheory/Coprod): fix recursor argument name)

Result: no findings. The PR renames the motive `C` to `motive` in two `elab_as_elim` recursors and
re-wraps one signature. I checked every concern family against both declarations and found nothing a
maintainer would ask to change.

## What I did

- Read `pr.md`, `model.md` and `diff.patch`, then read
  `target/Mathlib/GroupTheory/Coprod/Basic.lean` lines 1-330 with `file_read` (proofs shown).
- `lean_verify_edit` with no edit, as a compile check of the file as the PR leaves it: it
  compiles, with no errors and no warnings.
- `content_search` for `elab_as_elim`, `→ Prop}`, `Prop|Sort|induction|rec` in
  `GroupTheory/Coprod/Basic.lean`. These two lemmas are the only recursors in the file, and the
  `Coprod/` directory holds only this file, so no sibling still uses a `C` motive.
- `content_search` for `Coprod.induction_on` across Mathlib. The only downstream use is
  `GroupTheory/PushoutI.lean:179`, `induction x using Coprod.induction_on with | inl g => ...`.
  Case names come from the minor premises, which this PR leaves alone, so it is unaffected. No
  `(C := ...)` named-argument uses exist, so no in-tree caller breaks.
- `content_search` for `elab_as_elim` over `GroupTheory/` to learn the local conventions:
  `CoprodI.induction_on`, `CoprodI.induction_left`, `FreeAbelianGroup.induction_on`,
  `HNNExtension.induction_on` and `Perm.swap_induction_on` all already use `motive`. Several
  recursors in other files still use `C` (`FreeGroup.induction_on`, `Con.induction_on`,
  `QuotientGroup.induction_on`). Those are outside this PR's scope (`GroupTheory/Coprod`), and
  precedent (eric-wieser on #23419) is that such renames belong in their own PRs.
- `precedent_search` on both recursors. The similar review comments ask for the same rename on
  sibling recursors "for consistency" (#22848, #28096) or ask for `elab_as_elim` (#25770).
  Neither applies: both lemmas here are already renamed and already carry `elab_as_elim`.
- `zulip_search` for recursor argument naming. The convention is to call the motive `motive` and to
  name minor premises after the constructors or cases they cover (Robin Arnez, "naming arguments to
  recursors", 2025-04). The PR follows it. Nothing was found about `Monoid.Coprod.induction_on`
  itself.

## Object by object

### `Monoid.Coprod.induction_on'`
- correctness: compiles, and `to_additive` carries the rename over to the additive version.
- naming: `motive` is the convention. The minor premises `one`, `inl_mul` and `inr_mul` already
  name their cases (`1`, `inl m * x`, `inr n * x`) and are unchanged.
- style: the binder order (motive, then major premise, then minor premises) matches the `*_on`
  convention. Formatting is unchanged.
- proof-golf, generalization, duplication: the proof is untouched. `MulOneClass` is already the
  weakest setting in the file.
- documentation: no docstring, both before and after the PR. The sibling recursors in `CoprodI` and
  `FreeAbelianGroup` have none either, so I would not ask for one here.
- scope: fine for a rename-only PR.

### `Monoid.Coprod.induction_on`
- Same checks as above. The signature is re-wrapped over three lines and stays under 100
  characters. The minor premises `inl`, `inr` and `mul` are named after their cases. Inside the body,
  the premise `inl` shadows `Coprod.inl`, as it did before the PR. That matches how Mathlib usually
  does it (for example, the `C` premise of `MvPolynomial.induction_on_monomial`) and is not worth an
  ask.

### Not code findings (PR metadata only, so not emitted)
- The PR description says the minor premises are renamed "according to their contents". They
  already were before the PR, and only the motive changes.
- A binder rename is arguably `chore` rather than `fix`.
Both are about the title and description, not the code, so neither is a finding under this brief.
