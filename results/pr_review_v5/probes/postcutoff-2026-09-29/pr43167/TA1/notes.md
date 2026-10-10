# Review notes: PR #43167 (commutator distributivity over `⊔` for `N` normal)

I read `pr.md`, `model.md` and `diff.patch`. I then read the three files as the PR leaves them, through
`ptool file_read`: `Commutator/Basic.lean` lines 1-420, `Subgroup/Basic.lean` lines 440-600 and
`Subgroup/Pointwise.lean` lines 1-80 and 300-380. All compile checks used `ptool lean_verify_edit`. Every
edit below compiled (`outcome: compiled`), and none introduced errors or warnings except where a warning
was the point of the test.

## Checks run

1. Deleted the new import at line 13 of `Pointwise.lean`. Compiled. `content_search` finds no
   `commutator` or `⁅` in the file.
2. Rewrote lines 326-358 of Commutator/Basic.lean in one edit:
   - `@[to_additive]` on `commutator_sup_left'`, `commutator_sup_left` and `commutator_sup_right`;
   - `lemma` and a docstring for the private auxiliary;
   - docstrings for the public theorems and a strategy comment;
   - no `Subgroup.` prefixes;
   - `hHNM`/`hKNM` inlined.

   Compiled.
3. `commutator_mono` tagged `@[gcongr]` while `commutator_mono_left/right` were kept without it. Compiled,
   and the `grw` steps of `commutator_sup_left` still go through.
4. `gcongr` in place of `commutator_mono_left` in `commutator_sup_left'`. Compiled.
5. Indexed versions `commutator_iSup_left'` and `commutator_iSup_left` added after `commutator_sup_right`.
   Compiled.
6. Same as 5, with `commutator_sup_left` derived as
   `by simpa [iSup_bool_eq] using commutator_iSup_left (fun b ↦ cond b H K) N`, so the binary private
   auxiliary is no longer needed. Compiled.
7. `iInf_normalizer_le_normalizer_iSup` copied into `Subgroup/Basic.lean` after the moved lemma. Compiled.
8. `@[to_additive (attr := deprecated (since := ...))] alias normalizer_inf_normalizer_le_normalizer_sup :=
   inf_normalizer_le_normalizer_sup`, with test `example`s. Compiled. The deprecation warnings name the
   correct `Subgroup` and `AddSubgroup` targets. `content_search` found the same pattern already in
   Mathlib (`Pi/Lemmas.lean:75`).
9. `commutator_le_of_le` deleted and its two uses inlined as
   `(commutator_le_sup _ _).trans (sup_le _ _)`. Compiled.
10. `[N.Normal]` weakened to `(hH : H ≤ normalizer N) (hK : K ≤ normalizer N)`. Only `hHKN` changes,
    proved with `le_normalizer_iff_commutator_le_right.mp`. `commutator_sup_left` was then derived with
    `le_normalizer_of_normal`. Compiled.
11. `commutator_mono` tagged `gcongr`, both one-sided lemmas deleted, and `gcongr` used at their uses.
    Compiled.

Other tool use:
- `naming_norm` cannot resolve a subject for the commutator lemmas. For
  `inf_normalizer_le_normalizer_sup` it returns `emerging`, which is advisory at most. The rename matches
  its sibling `inf_normalizer_le_normalizer_inf`, so I asked for no rename.
- `declaration_search`: `Subgroup.map_iSup` and `map_sup` are both in `Subgroup/Map.lean`. The Lie
  analogues are `LieSubmodule.sup_lie`, `lie_sup` and `mono_lie_left`.
- `precedent_search` found nothing applicable.

## Object by object

- **`Subgroup.inf_normalizer_le_normalizer_sup`** (moved and renamed into `Subgroup/Basic.lean`).
  - The statement and proof are unchanged, and the new name matches `inf_normalizer_le_normalizer_inf`.
  - Filed: also move the indexed sibling `iInf_normalizer_le_normalizer_iSup`.
  - Filed, advisory: the rename is incidental to the PR's purpose.
- **Deprecated aliases** (`Subgroup/Basic.lean` lines 530-535). The old name is properly deprecated, for
  both `Subgroup` and `AddSubgroup`.
  - Filed: the attribute sits inline on a two-line header.
  - Filed: the additive alias is hand-written where `to_additive (attr := deprecated ...)` generates it
    (check 8).
- **`conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`, `normalizer_le_normalizer_sup_of_normalizer_le_left`**:
  only the callee was renamed. Nothing wrong.
- **`Pointwise.lean` import**: filed as blocking. It is unused, compiles without it, and adds a dependency
  on `GroupTheory.Commutator.Basic` (and `QuotientGroup.Defs`) to a low-level file.
- **`commutator_mono_left` / `commutator_mono_right`**: the names match `_mono_left/_right` usage
  elsewhere (`Ideal.mul_mono_left`), and `@[to_additive (attr := gcongr)]` is the correct attribute form.
  Filed: each is an instantiation of `commutator_mono`; tag `commutator_mono` with `gcongr` instead
  (checks 3 and 11).
- **`commutator_le_of_le`**: filed as a mere combination of `commutator_le_sup` and `sup_le`.
- **`commutator_sup_left'`** (private). Filed:
  - `theorem` with no docstring;
  - redundant `Subgroup.` prefixes;
  - named monotonicity lemma where `gcongr` works.

  I considered a golf of the rewrite-at-`hH hK` block but found nothing shorter, so I filed nothing for it.
- **`commutator_sup_left`**. Mathematically correct; normality is genuinely needed in general. My
  counterexample is in `S4`: `N = ⟨(12)⟩`, `H = ⟨(34)⟩`, `K = ⟨(23)⟩`. Here `⁅H, N⁆ ⊔ ⁅K, N⁆` has
  order 3, but `⁅H ⊔ K, N⁆` contains 3-cycles on `{1,2,3}` and on `{1,2,4}`. Filed:
  - missing `to_additive`;
  - the iSup generalization (check 6);
  - the normalizer generalization (check 10);
  - a docstring;
  - a strategy comment;
  - a redundant `Subgroup.` prefix;
  - the inlinable `hHNM`/`hKNM`.
- **`commutator_sup_right`**: filed the missing `to_additive` and the missing docstring. The proof
  (`simp_rw [commutator_comm N, commutator_sup_left]`) is fine.

## Conventions ledger (the submission's `message`)

- **Namespace prefix**: filed at `commutator_sup_left'` (lines 332-333, `Subgroup.map_eq_bot_iff` and
  `Subgroup.commutator_eq_bot_iff_le_centralizer`) and at `commutator_sup_left` (line 348,
  `Subgroup.normal_subgroupOf_of_le_normalizer`). Left: `_root_.AddSubgroup.` in the additive alias,
  which is needed inside `namespace Subgroup`. It disappears anyway under the `to_additive` finding.
- **Inline short `have`**: filed at `commutator_sup_left`, for `hHNM`/`hKNM` (lines 342-343, used once at
  line 349). Left:
  - `hHM`/`hKM`/`hNM`, used in three places;
  - `hHKN`, used twice;
  - `hH`/`hK` in `commutator_sup_left'`, which are rewritten `at` and so cannot be inlined as terms.
- **Unneeded import**: filed at `Pointwise.lean` line 13 (check 1). Left: `Commutator/Basic.lean`'s
  imports are unchanged by the PR, and `QuotientGroup` is used there at lines 546-570.
- **Deprecate rather than delete**: left. `Subgroup/Basic.lean` lines 530-535 deprecate the old name for
  both `Subgroup` and `AddSubgroup`.
- **Attribute applied to some siblings only**: filed for `@[to_additive]` at `commutator_sup_left` (with
  its private auxiliary) and at `commutator_sup_right`. Every other `Subgroup` declaration in the touched
  region has it. Left: `@[gcongr]` is on both one-sided mono lemmas, though the separate finding moves it
  to `commutator_mono`.
- **`gcongr` rather than a named monotonicity lemma**: filed at `commutator_sup_left'` line 329. Left:
  - `commutator_sup_left`, which already uses `grw`;
  - `commutator_mono_left/right` themselves, which are the monotonicity lemmas.
- **Attribute on its own line for multi-line headers**: filed at the `Subgroup` deprecated alias (line
  530). Left: the `AddSubgroup` alias (line 533) and every `@[to_additive ...]` in Commutator/Basic.lean
  already put the attribute on its own line.
- **State for the indexed operation**: filed at `commutator_sup_left` (`commutator_iSup_left`, check 6).
  For `inf_normalizer_le_normalizer_sup` the indexed version `iInf_normalizer_le_normalizer_iSup`
  already exists. I filed a scope finding to move it alongside (check 7).
- **Tag monotone lemmas `@[gcongr]`**: left. `commutator_mono_left/right` carry it (lines 154 and 158).
  The `commutator_mono` finding proposes the tag on the general lemma instead.
- **Instantiation or combination lemmas not added**: filed at `commutator_mono_left`,
  `commutator_mono_right` and `commutator_le_of_le` (checks 9 and 11).
- **Strategy comments in long proofs**: filed at `commutator_sup_left`. Left: `commutator_sup_left'`, a
  6-step proof whose single rewrite chain is self-describing once it has a docstring.
- **`to_additive (attr := ...)`**: left. Lines 154 and 158 use `@[to_additive (attr := gcongr)]`, and
  the deprecated-alias finding uses the same form.
- **No heavier machinery than needed / earliest file**: left.
  - The moved lemma went to an earlier file, which is what the convention asks for.
  - The quotient used by `commutator_sup_left'` is already imported and used in Commutator/Basic.lean.
- **Generate twins**: filed at the hand-written `AddSubgroup` deprecated alias (check 8). The missing
  additive commutator lemmas are filed under `to_additive`.
- **Unqualified name for the unconditional statement**: left. `commutator_sup_left` is false without a
  normality-type hypothesis (counterexample above), and an instance hypothesis like `[N.Normal]` is
  conventionally not named, as in `commutator_le_right [H₂.Normal]`. The weaker-hypothesis form I
  propose is named `_of_le_normalizer`.
- **Prime only beside an unprimed primary**: left. `commutator_sup_left'` (line 326) has the unprimed
  primary `commutator_sup_left` (line 337).
- **Proof on the `:=` line only if it all fits**: left. Every new declaration with a term proof puts it
  on its own line (`commutator_mono_left` line 156, `commutator_mono_right` 160, `commutator_le_of_le`
  287, aliases 531 and 535). None puts an over-long proof on the statement line.
- **Name follows siblings**: left.
  - `commutator_sup_left/right` follow `commutator_bot_left/right` and `commutator_center_left`.
  - `inf_normalizer_le_normalizer_sup` follows `inf_normalizer_le_normalizer_inf`.
  - The vague `commutator_le_of_le` is covered by its removal finding.
- **Additive counterpart**: filed under the two `to_additive` findings.
- **Change only what the purpose needs**: filed at `inf_normalizer_le_normalizer_sup` (incidental rename,
  advisory) and at the `Pointwise.lean` import. Left: the caller updates in `Pointwise.lean` lines 344
  and 350 follow necessarily from the move.
- **`theorem` only with a docstring**:
  - filed as add-docstring at `commutator_sup_left` and `commutator_sup_right`;
  - filed as `lemma` plus docstring at `commutator_sup_left'`;
  - folded into the removal findings for `commutator_mono_left/right` and `commutator_le_of_le` ("if
    kept, use `lemma`").
- **Public versus `private`**: left. `commutator_sup_left'` serves one proof (its only use is line 346),
  and its hypothesis is an implementation device for the quotient step.
- **Docstring on a `private` or auxiliary lemma**: filed at `commutator_sup_left'`.
- **Hoist a step common to every branch**: left. In `commutator_sup_left` the steps
  `le_normalizer_iff_commutator_le_right, hHKN` occur in only two of the three branches of
  `refine sup_le (sup_le ?_ ?_) ?_` (lines 352-353). The third branch (line 354) does not perform them,
  so they are not common to every branch.
- **`have` immediately before its first use**: filed together with the inlining finding (`hHNM`/`hKNM`,
  lines 342-343, first used at line 349). Left: `hHKN` (line 350) sits right before its uses at lines
  352-353.
