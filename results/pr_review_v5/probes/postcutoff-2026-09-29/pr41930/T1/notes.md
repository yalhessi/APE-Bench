# Review notes: PR #41930 (Monoid.Coprod recursor argument names)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools used: ptool describe, file_read (the
whole changed region, lines 1-330 of `Mathlib/GroupTheory/Coprod/Basic.lean`), content_search,
precedent_search, zulip_search, lean_verify_edit (as-is compile check).

## What the PR does
Renames the motive `C` to `motive` in `Monoid.Coprod.induction_on'` and `Monoid.Coprod.induction_on`
(and so in their `to_additive` twins), and splits the over-long `induction_on` signature line.
The minor premises (`one`, `inl_mul`, `inr_mul`; `inl`, `inr`, `mul`) are unchanged; they were
already named after their contents, so the description's "name the minor premises according to
their contents" describes the existing state rather than a change in the diff. That is a PR-text
matter, not a code request, so it is not filed.

## Object by object

### `Monoid.Coprod.induction_on'`
- correctness/build: `lean_verify_edit` with no edit -> `outcome: compiled`, no errors, no linter
  warnings. Callers: `content_search` for `Coprod.induction_on` over `Mathlib/` finds only
  `GroupTheory/PushoutI.lean:179` (`induction x using Coprod.induction_on with | inl g => ...`),
  which uses case tags, not the motive's name, so the rename breaks nothing; no `(C := ...)` use.
- naming: `motive` matches Lean core and the sibling recursors in the area, which already use it:
  `Monoid.CoprodI.induction_on` (`one`, `of`, `mul`), `HNNExtension.induction_on`,
  `PushoutI.induction_on`. Minor premise names match the shapes they cover (`inl m * x` ->
  `inl_mul`).
- proof-golf: the proof is untouched by the PR and already short (`rcases mk_surjective` +
  `induction ... using FreeMonoid.inductionOn'`); nothing to ask.
- generalization/duplication/scope: unchanged statement apart from the binder name; nothing new.
- documentation: theorems carry no docstring; Mathlib does not require one on theorems and the PR
  does not change their meaning, so no request.
- style: binders and layout fine; lines under 100 chars.

### `Monoid.Coprod.induction_on`
- Same checks as above. The signature split over three lines keeps it under 100 columns. The
  hypotheses `inl`/`inr` shadow `Monoid.Coprod.inl`/`inr` in the proof body, but that is the
  established constructor-named-case convention (it is what makes `| inl g =>` work in PushoutI)
  and predates the PR.

## Consistency sweep (the "rename this one too" ask)
precedent_search surfaced eric-wieser asking for siblings to be `motive`d too (PRs #22848,
#28096). Searched the Coprod directory for any other `elab_as_elim`/`induction_on`/`{C :`
declarations: none remain in `Coprod/Basic.lean` after this PR. Other `C`-motive recursors in
`GroupTheory` (`Con.induction_on`, `QuotientGroup.induction_on`, `PresentedGroup.induction_on`,
`Localization.induction_on` with `p`) live in unrelated files; asking for them here would be
scope creep for a two-declaration fix, so no request.

## Result
No actionable request; findings.json is an empty list.
