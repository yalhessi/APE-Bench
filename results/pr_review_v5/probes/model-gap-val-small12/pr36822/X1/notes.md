# Review notes: PR #36822 (use `to_dual` in Order/Interval/Set/Disjoint and Filter/AtTopBot/Disjoint)

## What I did

- Read brief.md, pr.md, model.md and diff.patch.
- Read both changed files as the PR leaves them: `target/Mathlib/Order/Interval/Set/Disjoint.lean` and `target/Mathlib/Order/Filter/AtTopBot/Disjoint.lean`.
- Compiled the Interval file as it stands. It compiles with no warnings.
- For every generated dual I ran `#check`, using lean_verify_edit with `#check` lines appended, and compared the result with the statement the PR removed.
- I ran `by simp` probes before and after restoring the `simp` attributes. I searched for downstream uses of the reordered or de-simped names, looked up the new dual names, and ran one precedent search, which turned up nothing relevant.

## Mathlib/Order/Interval/Set/Disjoint.lean

- **`Iic_disjoint_Ioi`** now has `to_dual (attr := simp) Ici_disjoint_Iio`. It generates `Ici_disjoint_Iio : b ≤ a → Disjoint (Ici a) (Iio b)`, which is a new lemma: it is not in the base tree. It is simp, like its source. No issue.
- **`Iio_disjoint_Ici`** now has `to_dual (attr := simp) Ioi_disjoint_Iic`. It generates the new lemma `Ioi_disjoint_Iic : b ≤ a → Disjoint (Ioi a) (Iic b)`. No issue.
- **`Ici_disjoint_Iic`** now has `to_dual (attr := simp) Iic_disjoint_Ici`. The generated `Disjoint (Iic a) (Ici b) ↔ ¬b ≤ a` is exactly the removed statement, and it keeps simp. No issue.
- **`Ioi_disjoint_Iio_of_not_lt` and `Ioi_disjoint_Iio_of_le`** (no simp before or after).
  - The generated duals match the removed statements up to renaming the implicit `a`/`b`. The order of the implicit arguments changes:
    - old `Iio_disjoint_Ioi_of_le : a ≤ b → Disjoint (Iio a) (Ioi b)`
    - new `b ≤ a → Disjoint (Iio b) (Ioi a)`
  - content_search found no uses outside this file, so this is harmless. No finding.
- **`Ioi_disjoint_Iio_same`**: `@[simp]` is lost on both it and its dual. This is a finding (blocking).
  - Probe: `by simp` no longer proves `Disjoint (Ioi a) (Iio a)` or `Disjoint (Iio a) (Ioi a)`.
  - Fix: `@[to_dual (attr := simp) Iio_disjoint_Ioi_same]`. Verified to compile, and the simp probes pass with it.
- **`Ioi_disjoint_Iio_iff`**: `@[simp]` is lost in the same way. This is a finding (blocking). Probed and fixed the same way. The generated dual statement matches the removed `Iio_disjoint_Ioi_iff` exactly.
- **`iUnion_Iic` and `iUnion_Iio`** use `to_dual (attr := simp)` with the names generated automatically. They generate `iUnion_Ici` and `iUnion_Ioi` (the latter with `[NoMinOrder α]`), which match the removed lemmas. No issue.
- **`iUnion_Icc_right`, `iUnion_Ioc_right`, `iUnion_Ico_right` and `iUnion_Ioo_right`** name their duals explicitly (`iUnion_Icc_left`, `iUnion_Ico_left`, `iUnion_Ioc_left`, `iUnion_Ioo_left`).
  - The generated statements match the removed ones up to the name of the bound or explicit variable, and they keep simp and the `NoMinOrder` hypotheses.
  - The explicit names are presumably needed because automatic naming would not map right to left and would dualise "disjoint". The compile reports no warning about a redundant name. No issue.
- **Also dualise `Ico_disjoint_Ico` / `Ioc_disjoint_Ioc`?** I considered asking for `Ioc_disjoint_Ioc` in the LinearOrder section, which is still proved by hand via `toDual`, to be generated too. I tested `@[to_dual (attr := simp) Ioc_disjoint_Ioc]` on `Ico_disjoint_Ico`. It fails because `Ico_inter_Ico` has no registered dual. Doing it would mean tagging lemmas in another file, which is beyond this PR, so I raise no finding.
- **Unchanged neighbours**: the remaining unconverted lemmas (`Iic_disjoint_Ioc`, `Ioc_disjoint_Ioc_of_le`, `Ico_disjoint_Ico_same`, `Ioc_disjoint_Ioi(_same)`) and the UnionIxx section. Dualising them would add new lemmas or need extra tagging. I am not requesting that.
- **Docstrings and imports**: none of the converted theorems had docstrings, and none are needed. `open OrderDual (toDual)` is still used by `Ioc_disjoint_Ioc`.

## Mathlib/Order/Filter/AtTopBot/Disjoint.lean

- **`disjoint_atBot_principal_Ioi`** generates `disjoint_atTop_principal_Iio (x) : Disjoint atTop (𝓟 (Iio x))`. This matches the old statement. No issue.
- **`disjoint_atTop_principal_Iic`** generates `disjoint_atBot_principal_Ici` with `[NoBotOrder α]`. It matches. No issue.
- **`disjoint_pure_atTop`** generates `disjoint_pure_atBot` with `[NoBotOrder α]`. It matches. No issue.
- **`disjoint_atBot_atTop`** generates `disjoint_atTop_atBot : Disjoint atTop atBot` under `[PartialOrder α] [Nontrivial α]`. It matches. No issue.
- None of these had simp before, so no attribute is lost. Their proofs are unchanged, and I saw no golf worth requesting within this PR's scope.

## Summary

There are 2 findings, both about the lost `@[simp]` on the `Ioi_disjoint_Iio_same` and `Ioi_disjoint_Iio_iff` families. I found nothing else to request.
