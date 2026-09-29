# Review notes: PR #36822, feat(Order/Interval/Set/Disjoint): use `to_dual`

## Method

- Read `pr.md`, `model.md` and `diff.patch`. Read both changed files as the PR leaves them, through `ptool file_read`; workspace paths are under `target/`.
- `lean_verify_edit` with no edit: `Mathlib/Order/Interval/Set/Disjoint.lean` compiles as the PR leaves it, with no warnings.
- Printed every generated dual with `#check`, spliced after `iUnion_Ioo_right`. Each matches the statement of the declaration it replaces, up to renaming of bound or implicit variables:
  - `Ici_disjoint_Iio : b ≤ a → Disjoint (Ici a) (Iio b)` (new)
  - `Ioi_disjoint_Iic : b ≤ a → Disjoint (Ioi a) (Iic b)` (new)
  - `Iic_disjoint_Ici : Disjoint (Iic a) (Ici b) ↔ ¬b ≤ a`
  - `Iio_disjoint_Ioi_of_not_lt : ¬b < a → Disjoint (Iio a) (Ioi b)`
  - `Iio_disjoint_Ioi_of_le : b ≤ a → Disjoint (Iio b) (Ioi a)`
  - `Iio_disjoint_Ioi_same`
  - `Iio_disjoint_Ioi_iff [DenselyOrdered α] : Disjoint (Iio a) (Ioi b) ↔ ¬b < a`
  - `iUnion_Ici`, `iUnion_Icc_left`, `iUnion_Ico_left`, `iUnion_Ioi [NoMinOrder]`, `iUnion_Ioc_left [NoMinOrder]` and `iUnion_Ioo_left [NoMinOrder]`, all as before.
- The `translateGenerateName` linter is active in this environment: it fired on redundant names in my own probe. It fired on none of the PR's explicit names, so every explicit dual name the PR gives is needed. My guess is that `disjoint` is translated, which is why the PR spells those names out.

## Mathlib/Order/Interval/Set/Disjoint.lean

- `Iic_disjoint_Ioi` and `Iio_disjoint_Ici`: `(attr := simp)` keeps simp. They generate the new `Ici_disjoint_Iio` and `Ioi_disjoint_Iic`. `declaration_search` finds no existing declaration under either name, and a content search for `Disjoint (Ici` / `Disjoint (Ioi` finds no Set-level duplicate (only the unrelated `Finset.disjoint_Ioi_Iio`). No finding.
- `Ici_disjoint_Iic` (dual `Iic_disjoint_Ici`): simp kept, statement correct. No finding.
- `Ioi_disjoint_Iio_of_not_lt` and `Ioi_disjoint_Iio_of_le`: neither was simp before. The duals match after renaming of implicit variables. No finding.
- `Ioi_disjoint_Iio_same`: **finding (blocking)**. The PR drops `@[simp]` on it and on its dual. I confirmed with `lean_verify_edit` that `simp` no longer proves `Disjoint (Ioi a) (Iio a)` or `Disjoint (Iio a) (Ioi a)`, and that `@[to_dual (attr := simp) ...]` restores both with no warnings. The PR adds no simp lemma that would make this one redundant, and it was simp at base.
- `Ioi_disjoint_Iio_iff`: **finding (blocking)**, for the same reason: the simp attribute is lost on it and on `Iio_disjoint_Ioi_iff`. Confirmed the same way.
- `iUnion_Iic`, `iUnion_Iio`, `iUnion_Icc_right`, `iUnion_Ioc_right`, `iUnion_Ico_right` and `iUnion_Ioo_right`: simp kept, and the typeclass assumptions translate correctly (`NoMaxOrder` becomes `NoMinOrder`). The explicit binder on the `_left` duals is now named `a` instead of `b`, which matters only to `(b := _)` callers, and a content search found none. No finding.
- Rest of the file (scope): **finding (advisory)**. Four `IsGLB`/`IsLUB` pairs and two `iUnion`/`biUnion` `_self_iff` pairs in the same file translate with bare `@[to_dual]`, and I verified that both edits compile. I also checked two pairs that do not translate at this commit and left them out of the request: `Ico_disjoint_Ico`/`Ioc_disjoint_Ioc`, because `Ico_inter_Ico` has no dual, and `iUnion_Ici_eq_Ioi_iInf`/`iUnion_Iic_eq_Iio_iSup`, because `isGLB_iInf` has no dual.
- `Iic_disjoint_Ioc`, `Ioc_disjoint_Ioc_of_le`, `Ico_disjoint_Ico_same`, `Ioc_disjoint_Ioi` and `Ioc_disjoint_Ioi_same` are unchanged and have no hand-written dual in the file, so tagging them would add new lemmas. Not requested.
- Documentation: none of these theorems had a docstring before, and the module docstring still describes the file. No finding.

## Mathlib/Order/Filter/AtTopBot/Disjoint.lean

- `disjoint_atBot_principal_Ioi` (dual `disjoint_atTop_principal_Iio`), `disjoint_pure_atTop` (dual `disjoint_pure_atBot`) and `disjoint_atBot_atTop` (dual `disjoint_atTop_atBot`): the explicit names are needed (no linter warning), the statements are unchanged, and the typeclass assumptions translate correctly. None of these was simp. No finding.
- `disjoint_atTop_principal_Iic`: **finding (advisory, proof-golf)**. It can use the PR's own new `Ioi_disjoint_Iic le_rfl` instead of `(Iic_disjoint_Ioi le_rfl).symm`, which fits the proof on one 96-character line. I verified with `lean_verify_edit` that it compiles with the `to_dual` attribute in place.
- The proof of `disjoint_atBot_atTop` is untouched by the PR. I did not pursue a golf on it.

## Other tools

- `precedent_search` on the converted lemmas returned only unrelated interval and Finset comments.
- `zulip_search` for to_dual on intervals turned up nothing relevant.
- `naming_norm` does not answer for generated names. The new names `Ici_disjoint_Iio` and `Ioi_disjoint_Iic` follow the sibling `X_disjoint_Y` pattern in the file.

## Rule deviation

- Early on, while working out why `file_read` could not find the file (the paths need a `target/` prefix), I ran one `cat` on this ptool's own stderr logs under `.ape/probe_scratch/val_small12/raw/pr36822/X2/`, which is outside the working directory. It printed nothing. I read no other path outside this directory and no other reviewer's output.
