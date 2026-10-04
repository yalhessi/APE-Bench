# Review notes: PR #41930 (Monoid.Coprod recursor motive rename)

## What I did

- Read `pr.md`, `model.md` and `diff.patch`. The PR renames the motive `C` to `motive` in
  `Monoid.Coprod.induction_on'` and `Monoid.Coprod.induction_on`. It also adds one line break in
  `induction_on`, because the renamed signature no longer fits in 100 characters.
- Read `target/Mathlib/GroupTheory/Coprod/Basic.lean` lines 1-330 through `file_read`.
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors or warnings.
- `content_search` for other uses. Neither `induction_on` nor `induction_on'` is used anywhere with a
  named `(C := ...)` argument, so the rename breaks nothing downstream. The only external use is
  `induction x using Coprod.induction_on with | inl | inr | mul` in `GroupTheory/PushoutI.lean`, and
  it does not depend on the motive's name. There is no use of `AddMonoid.Coprod.induction_on(')`.
- `zulip_search`: calling the motive `motive` is the established convention, so the PR's direction
  is right.
- `precedent_search`: earlier rename PRs got requests to rename sibling recursors too ("could we
  rename the arguments to this one too", "this one could be `motive`d too"), and to keep unrelated
  changes in a separate PR.

## Object by object

### `Monoid.Coprod.induction_on'`
- correctness: compiles; the rename is complete within the declaration. Nothing to fix.
- naming: the motive is now `motive`, as required. The minor premises `one`, `inl_mul` and `inr_mul`
  already describe their cases. The prime departs from the "name the differing term, not a prime"
  convention; `CoprodI` calls the analogue `induction_left`. I did not request a rename: renaming the
  declaration would need a deprecation and falls outside this PR's purpose (precedent #23419: such
  changes "belong in a standalone PR").
- documentation: no docstring on the `theorem` or its additive version. Finding 2.
- style: the bound variables in the minor premises have no types, and the inner `m` shadows the
  major premise `m`. Finding 4. Line layout: `(one : motive 1)` would fit on the first line, but that
  layout predates the PR, which kept it. Asking for it would be a third-party stylistic change of
  marginal benefit, so I did not.
- proof-golf: the proof (`rcases mk_surjective`, then `FreeMonoid.inductionOn'` with structured
  `cases`) is short and idiomatic, and the PR does not touch it. Nothing to request.
- generalization: the motive cannot be generalized to `Sort*` here, because the type is a quotient
  and the proof goes through surjectivity of `mk`. The typeclass assumptions are already minimal
  (`MulOneClass`).
- duplication and scope: none.

### `Monoid.Coprod.induction_on`
- correctness: compiles. Its one downstream use, in PushoutI, depends only on the case names
  `inl`/`inr`/`mul`, which are unchanged.
- documentation: no docstring on the `theorem` or its additive version. Finding 3.
- style: the new break puts `inl`/`inr` on one line and `mul` with the conclusion on the next. That
  is needed because the line would otherwise exceed 100 characters, and it is a reasonable grouping.
  Untyped `∀ m`/`∀ n` binders shadow the major premise `m`; this is folded into finding 4 as the
  sibling edit.
- proof-golf: `induction_on' m (by simpa using inl 1) ...` is a one-line term proof. Nothing better.
- generalization, duplication, scope: none.

### PR title and description
- The description says the minor premises are renamed "according to their contents", but none is
  renamed. The title is vague. Finding 1. The title does follow `type(Area): description`; a
  pure rename is more usually `chore` than `fix`, and the suggested rewrite in finding 1 uses `chore`.

### Family conventions
- Both members of the family (`induction_on`, `induction_on'`) get the same rename, and their
  additive versions follow through `to_additive`. No sibling in this file is left behind. Other files
  still use `C` (`FreeGroup.induction_on`, `PresentedGroup.induction_on`, `Con.induction_on`,
  `QuotientGroup.induction_on`, `FreeMonoid.inductionOn`/`inductionOn'`). They are different types in
  different files, and precedent puts such renames in their own PRs, so I made no finding.

## Edits verified

- Line mode, lines 195-212: docstrings with `to_additive` docstrings on both declarations, plus
  explicitly typed minor-premise binders. Outcome `compiled`, no errors.
- (An earlier attempt in declaration mode, putting a docstring before the attribute, failed to parse
  only because the tool keeps the original attribute line in front of my docstring. That says
  nothing about the code itself; line mode settled it.)
