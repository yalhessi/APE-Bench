# Review notes: PR #41930 (fix(GroupTheory/Coprod): fix recursor argument name)

Inputs read: pr.md, model.md, diff.patch, brief.md. Tools used: file_read on
`target/Mathlib/GroupTheory/Coprod/Basic.lean` (lines 1-300), content_search, zulip_search,
precedent_search and lean_verify_edit (one compiled edit, including a MetaM `#eval` that prints binder names).

## What the PR does
It renames the motive `C` to `motive` in `Monoid.Coprod.induction_on'` and
`Monoid.Coprod.induction_on`, and re-breaks the `induction_on` signature over three lines, since the
old second line would now be 125 characters. Proofs, minor-premise names and attributes are all
unchanged.

## Monoid.Coprod.induction_on'
- Correctness/build: the file compiles as the PR leaves it (lean_verify_edit outcome `compiled`).
  The library's only external use of these recursors is `Mathlib/GroupTheory/PushoutI.lean:179`
  (`induction x using Coprod.induction_on with | inl g | inr h | mul x y ihx ihy`). It does not
  depend on the motive's name. No library use passes `(C := ...)` to these recursors; the only
  `(C := ...)` uses are for `AdjoinRoot.induction_on`, which is unrelated.
- to_additive: a binder-name `#eval` shows `AddMonoid.Coprod.induction_on'` gets
  `[motive, m, zero, inl_add, inr_add]`, so the additive names are already translated. Nothing to
  ask.
- Sibling/"variant for siblings" item: the sibling eliminators in the area already use `motive`:
  `Monoid.CoprodI.induction_left` and `induction_on`, `Monoid.PushoutI.induction_on`,
  `HNNExtension.induction_on`. Both recursors in this file are changed. Other recursors that still
  use `C` (FreeMonoid.recOn/inductionOn/casesOn, FreeGroup.induction_on, Con.induction_on,
  QuotientGroup.induction_on, PresentedGroup.induction_on) live in other files and types. Asking
  for them would widen a focused PR, so I dropped this item.
- "Purely stylistic change by a third party" item: dropped. Renaming eliminator motives to
  `motive` is established community practice. Zulip has Jeremy Tan's series "fix induction branch
  names (and rename their motive variables to `motive`)", and in review precedents Eric Wieser
  asks for more recursors to be "`motive`d".
- Prime item: dropped. The unprimed sibling `induction_on` exists, and
  `scripts/nolints_prime_decls.txt` already lists `Monoid.Coprod.induction_on'`.
- Strict-implicit `∀ ⦃x⦄` item: dropped. These are minor premises of an eliminator, and their
  explicit binders are what `induction ... with | mul x y ihx ihy` binds (PushoutI does this).
  Making them strict-implicit would break that usage and depart from the eliminator convention.
- `variable` for the motive item: dropped. Recursors in Mathlib bind their motive in the
  signature, and the sibling recursors (CoprodI, PushoutI, HNNExtension) do the same.
- Letter `m` for both the major premise and the `M`-element: pre-existing and unchanged. The area
  uses this pattern itself (CoprodI: `(m : CoprodI M)` and `(m : M i)`), so I dropped it.
- Line-breaking item (`(one : motive 1)` could join line 1, at 74 chars): the line structure
  predates the PR, which only substitutes the motive name. Mathlib does not require greedy line
  filling, so I dropped it.
- Proof: unchanged by the PR, so there is no golf request in scope.

## Monoid.Coprod.induction_on
- Same build, use-site, to_additive (`[motive, m, inl, inr, add]`), sibling, binder and
  stylistic-change checks as above. None of them gives a request.
- Re-break: the PR breaks at binder boundaries after the old second line grew to 125 chars. The
  alternative of pulling `(inl : ...)` onto line 1 (84 chars) is not clearly better, and the
  CoprodI sibling uses a similar layout. I dropped this item.
- The local hypotheses `inl`/`inr` shadow `Coprod.inl`/`Coprod.inr` inside the proof term. This
  predates the PR, works as intended (`inl 1` is the hypothesis), and there is nothing to ask.

## PR description
- The description says the PR will "name the minor premises according to their contents", but no
  minor premise is renamed; the binder-name `#eval` confirms the names are identical to the base.
  Finding 1 (advisory) asks the author to make the description match the change.

## Not found / nothing to request
Documentation: neither recursor has a docstring before or after the PR, and the PR does not touch
docs. Asking for one would be out of scope for a rename. Scope: the PR touches exactly the two
recursors in the file.
