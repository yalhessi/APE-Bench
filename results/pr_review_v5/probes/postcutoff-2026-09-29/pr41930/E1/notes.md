# Review notes: PR #41930 (Monoid.Coprod recursor argument names)

Result: no findings. The PR renames the motive `C` to `motive` in two eliminators and reflows one
signature. I found nothing a maintainer would plausibly ask to change.

## What I did

- Read `pr.md`, `model.md` and `diff.patch`. Read the changed file, lines 1-300, through `file_read`
  (`target/Mathlib/GroupTheory/Coprod/Basic.lean`).
- `lean_verify_edit` with no edit: the file compiles as the PR leaves it, with no errors and no warnings.

## `Monoid.Coprod.induction_on'`

- Correctness: this is a binder rename only (`C` to `motive`), and the proof body is unchanged.
  The minor premises `one`, `inl_mul` and `inr_mul` keep their names, so the case tags that
  `induction ... using` produces are the same. `to_additive` carries the renamed binder over to
  `AddMonoid.Coprod.induction_on'`.
- Downstream breakage from the rename: searched for `Coprod.induction_on'` and `(C := ` in
  `Mathlib/GroupTheory`. Nothing passes the motive by name, so no deprecation or follow-up fix is needed.
- Naming and convention: a Zulip search found the "naming arguments to recursors" thread
  (2025-04): name the motive `motive` and name minor premises after constructors. Sibling
  eliminators already follow it: `CoprodI.induction_left`, `CoprodI.induction_on`,
  `PushoutI.induction_on` and `HNNExtension.induction_on` all use `motive`. The PR conforms.
- Scope: a search of the file for other eliminator-like declarations (`→ Prop`, `Sort*`, `rec`,
  `induction`) finds only these two. Nothing in the file was left un-renamed.
  `FreeMonoid.inductionOn'` (motive `p`), which the proof uses, lives in another file. Asking for it
  here would widen the PR's scope, so I did not request it.
- Documentation: the declaration has no docstring. It had none before either, Mathlib does not
  require docstrings on theorems, and local siblings (`CoprodI.induction_left`) also lack one.
  So I did not ask for one in a binder-rename PR.
- Proof-golf, generalization, duplication and style: the proof is untouched, and
  `rcases mk_surjective` plus `FreeMonoid.inductionOn'` is already short. Generalizing to a
  `Sort*` motive does not fit a quotient-based theorem and is out of scope. Formatting is fine.

## `Monoid.Coprod.induction_on`

- Same rename. The signature is reflowed so `(mul : ...)` sits on its own line, which keeps it
  under 100 columns. The layout is fine.
- The binder names `inl`, `inr` and `mul` are unchanged, so the one in-library use is unaffected:
  `induction x using Coprod.induction_on with | inl g | inr h | mul x y ihx ihy` in
  `Mathlib/GroupTheory/PushoutI.lean:179`. The search over all of Mathlib for
  `Coprod.induction_on` returned only that file.
- `(inl : ∀ m, motive (inl m))` shadows the function `inl` with the hypothesis inside the proof
  body. That was there before the PR, it elaborates correctly, and the binder name is now the
  conventional constructor-style name, so I made no request.

## Conventions check (from the brief)

- "A design change comes with motivation in the docstring or PR description": this PR is a
  conventional binder rename, not a new concept or a design change. The description says what is
  renamed and the scheme followed (motive named `motive`, minor premises after their contents).
  The convention is settled on Zulip, so further motivation would not plausibly be asked for. One
  small point: the description's sentence about naming the minor premises describes the existing
  names rather than a change in the diff. I judged that too minor to be an ask.

## Tool calls

describe; file_read (failed once on a path without the `target/` prefix, then succeeded);
file_search x3; content_search x5; zulip_search x3; precedent_search x1 (precedents were Eric
Wieser asking to "motive" sibling recursors in the same PR, which does not apply here because no
sibling in the file is left); lean_verify_edit (as-is compile: compiled, no warnings).
