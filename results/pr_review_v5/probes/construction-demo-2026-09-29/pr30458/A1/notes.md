# Review notes: PR #30458 (chore(Algebra): misc. generalizations)

## What I did

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`. I read the changed regions of the three
files as the PR leaves them through `ptool file_read`: `target/Mathlib/Algebra/Group/Basic.lean`
lines 1-900, `.../Pointwise/Finset/Basic.lean` lines 1150-1280, and `.../Pointwise/Set/Finite.lean`
lines 1-160. I compiled every edit I propose with `lean_verify_edit`; every one returned
`outcome=compiled` with no errors. I ran `declaration_search` on `div_left_injective`,
`div_right_injective`, `mul_left_injective` and `div_left_inj`, ran `precedent_search` on the new
`div_left_injective` (nothing applicable), and ran two `zulip_search` queries (one relevant hit, on
how useful Group -> DivisionMonoid generalizations are).

One fact runs through most findings: in the PR workspace the *pre-PR* proofs of `div_left_injective`,
`div_left_inj`, `div_right_inj`, `Finset.card_le_card_div_left/right` and `Set.finite_div/infinite_div`
all still compile under the generalized assumptions. So every proof rewrite in the PR is incidental.

## Object by object

### Mathlib/Algebra/Group/Basic.lean

- **Section split** (`RightCancelDivInvMonoid` with `[DivInvMonoid G] [IsRightCancelMul G]`,
  `LeftCancelDivisionMonoid` with `[DivisionMonoid G] [IsLeftCancelMul G]`). The assumptions are the
  right ones: `div_left_injective` needs only `mul_left_injective` (right-cancel); `div_right_injective`
  needs `mul_right_injective` (left-cancel) and `inv_injective` (involutive inverse, so a
  DivisionMonoid). The sections have blank lines around `section`/`variable`/`end`, and the moved
  lemmas keep their attributes (`to_additive`, `simp`). No finding on the split itself.
- **div_eq_inv_self**: the statement and generality are right (`mul_eq_right` needs right-cancel). The
  one-line declaration (85 chars) was split over two lines. Advisory finding: restore it, so the
  diff is a pure move. The one-line form compiles.
- **div_left_injective**: convoluted AI-style proof (intro / have via simpa / `simpa using` around
  a term that already has the goal's type, plus three redundant named arguments). Blocking finding:
  `by simpa only [div_eq_mul_inv] using mul_left_injective b⁻¹` compiles. The Batteries regression
  test `BatteriesTest/simpa.lean:56` (`div_left_inj_issue.div_left_injective`) shows the simpa bug
  behind the removed FIXME is fixed. The `: G` ascription is not needed either.
- **div_left_inj**: convoluted `constructor` proof with `rintro rfl; rfl` on one line. Blocking
  finding: `div_left_injective.eq_iff` compiles, which mirrors `div_right_inj`.
- **div_eq_self**: the generality is right (needs left-cancel plus `inv_eq_one`, so a DivisionMonoid).
  It was split over two lines although it is 90 chars. Advisory finding.
- **div_right_injective**: the FIXME was deleted but the non-simpa proof it was about was kept, and
  the binder was renamed to `x : G` for no reason. Advisory finding: original statement plus the
  simpa proof, which compiles.
- **div_right_inj**: `(G := G) (b := a)` are redundant. Advisory finding: `div_right_injective.eq_iff`
  compiles.
- I checked whether any of these could be generalized further: `div_eq_self` and
  `div_right_injective` need injective inversion, for which no class weaker than `DivisionMonoid`
  exists. Nothing to ask.
- Names are unchanged and match their siblings, so there is no naming finding. The module docstring
  is still accurate.

I compiled one combined edit of lines 631-672 holding all the Basic.lean proposals: `compiled`.

### Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean

- **card_le_card_div_left / card_le_card_div_right**: the term proofs were rewritten into
  `obtain`/`exact` with named `(b := _)` arguments, and the original terms still compile. One
  advisory finding each: revert.
- **Section structure / card_le_card_div_self**: the outer `section DivisionMonoid` has no variables.
  The same `[DivisionMonoid α] ... [DecidableEq α] {s t : Finset α}` is declared three times, the third
  time only for `card_le_card_div_self` and needlessly wrapped (80 chars). Advisory finding: one outer
  variable, inner sections adding only the cancel class (named `IsLeftCancelMul`/`IsRightCancelMul`
  like the file's `Mul` sections), and `card_le_card_div_self` moved into the left-cancel section. The
  restructure compiles (line-mode edit of 1244-1270).
- Considered and not raised: a right-cancel sibling `card_le_card_div_self'` mirroring
  `card_le_card_mul_self'`. It would add more unused API to a PR that already lacks motivation, so I
  do not think a maintainer would ask for it. The missing blank line after `section LeftCancel`
  matches this file's existing `section CancelMonoid` style, so no finding.

### Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

- **finite_div / infinite_div**: the proofs gained inferable `(b := _)` arguments and were wrapped
  onto two lines. The original one-liners (88 and 90 chars) still compile. One advisory finding each.
- **Section assumptions** `[DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α]`: not raised.
  Replacing them with `[IsCancelMul α]` would be more concise, but the sibling `section Cancel` in
  the same file uses the two separate classes, and the separate classes are friendlier to instance
  search. The section name `DivisionMonoid` is fine.

### PR description

- Advisory finding: the title "misc. generalizations" does not say what changed, and the description
  gives no use or non-group instance for the new assumptions ("no intended use"). It should list
  exactly which declarations move to which classes and give a motivation. If none exists, it should
  keep the Finset/Set lemmas at `Group`. Supported by the PR text and by a pre-PR Zulip remark
  (Anne Baanen, relayed in #PR-reviews "#22337 type class generalization") that Group ->
  DivisionMonoid is a less-likely-useful generalization. AI use is disclosed ("found by asking
  Codex"), so the disclosure convention is met.

## Tool calls (all lean_verify_edit results: outcome=compiled, no errors)

- Basic.lean: original `div_left_injective` proof; simpa `div_left_injective` (with and without
  `simp` args or the `: G` ascription); term variant; simpa `div_right_injective` with both the
  `x : G` and original `a` binders; `div_left_inj := div_left_injective.eq_iff`; original
  `div_left_inj`; `div_right_inj := div_right_injective.eq_iff`; one-line `div_eq_inv_self`; one-line
  `div_eq_self`; combined lines 631-672.
- Finset/Basic.lean: original `card_le_card_div_left`; original `card_le_card_div_right`; restructured
  sections (lines 1244-1270).
- Set/Finite.lean: original `finite_div`; original `infinite_div`; combined lines 141-149.
