# Review notes: PR #33294 (deprecate `Ordinal.IsNormal` for `Order.IsNormal`)

## What I did
I read `brief.md`, `pr.md`, all of `model.md` and all of `diff.patch`. I read the changed files as the PR
leaves them through `ptool file_read` / `content_search` (workspace root `target/`). Every edit I propose
was compiled with `lean_verify_edit`, and all of them succeeded with no warnings. I also used
`declaration_search`, which is fuzzy here: it reports `Ordinal.nfp_fp` as "before this PR", although the
base only had `Ordinal.IsNormal.nfp_fp`. I therefore relied on content_search and the diff instead. I also
ran `naming_norm` (no usable census), `zulip_search` (review time as_of 2025-12-26) and `precedent_search`
(nothing applicable).

The result is 11 findings: 1 blocking and 10 advisory. See `findings.json`.

## Object by object

### Mathlib/Order/IsNormal.lean
- `Order.IsNormal.monotone` (added). This is correct, and `protected` matches `IsNormal.id` and `IsNormal.ext`.
  The structure only exists for `[LinearOrder α] [LinearOrder β]`, so there is no generalisation to ask for.
- Module docstring. The TODO "Replace `Ordinal.IsNormal` by this more general notion" is now done by this PR
  and should be removed (finding 5).

### Aleph.lean
- `isNormal_preOmega`, `isNormal_omega`, `preOmega_omega0` are mechanical swaps
  (`isNormal_iff`, `.comp`, `apply_omega0_of_isNormal`). Nothing to ask.

### Cofinality.lean
- `isFundamentalSequence_of_isNormal`, `cof_eq_of_isNormal` and `cof_le_of_isNormal` are renamed out of the
  `Ordinal.IsNormal` namespace. That is necessary, because dot notation on an `Order.IsNormal` hypothesis no
  longer reaches `Ordinal.IsNormal.*`. All three have deprecated aliases with the right date. naming_norm on
  `cof_eq_of_isNormal` shows the `cof_` prefix is the convention (27/27).
- `cof_add`, `cof_preOmega`, `cof_omega` are call-site updates. Fine.

### Arithmetic.lean
- `Ordinal.IsNormal`, now protected and deprecated. The approach is fine. The removed section header leaves
  the deprecated block under "The predecessor of an ordinal" (finding 10).
- Deprecated lemmas `limit_le`, `limit_lt`, `strictMono`, `lt_iff`, `le_iff`, `inj`, `id_le`, `le_apply`,
  `le_iff_eq`, `le_set`, `le_set'`, `refl`, `trans`, `isSuccLimit`, `isNormal_iff_strictMono_limit`: the
  targets check out, except `IsNormal.monotone`, which points to `Order.IsNormal.strictMono` although the PR
  adds `Order.IsNormal.monotone` (finding 4). `le_iff_eq -> StrictMono.le_apply` and
  `inj -> Injective.eq_iff` are loose but usable hints, so I did not raise them. The new `le_set` proof
  shadows `H` inside a lambda, but in a deprecated lemma that is not worth an ask.
- Module docstring. It drops the `pred` bullet although `Ordinal.pred` still exists (finding 9). The rest of
  the reorganisation (the "generalized to other orders" list) is fine.
- `isNormal_add_right`, `isNormal_mul_right`, `isSuccLimit_add`, `isSuccLimit_mul` are mechanical. Fine.

### Enum.lean / Topology.lean
- `isNormal_enumOrd` is fine.
- `enumOrd_isNormal_iff_isClosed` uses `Order.IsNormal.map_iSup h ...` where `h.map_iSup ...` works. I
  folded this into finding 7 and verified it compiles.

### Exponential.lean
- `isNormal_opow`: the type ascription `(a ^ · : Ordinal → Ordinal)` is needed now that `IsNormal` is
  type-generic. Fine.
- `opow_lt_opow_iff_right`, `opow_le_opow_iff_right`, `opow_right_inj`, `right_le_opow`, `isSuccLimit_opow`
  are mechanical. Fine.
- `opow_add` has an unused `have` whose content is proved again by `exact`, plus a
  `pos_iff_ne_zero.2 ha.ne'` round trip (finding 6). No linter flags either one; the as-is compile reports
  no warnings.
- `opow_mul`: I checked the golfed proof and found nothing to ask.
- `iSup_pow_natCast`: the name is wrong, because the statement contains no cast (finding 8).
- The module doc header reformat is harmless.

### Family.lean
- The deprecated `map_iSup_of_bddAbove`, `map_iSup`, `map_sSup_of_bddAbove` and `apply_of_isSuccLimit`
  are fine. `map_sSup` is the one sibling whose binder was not switched to `Ordinal.IsNormal` (finding 11).
- `IsNormal.bsup` should use dot notation and go back to one line (finding 7).
- `IsNormal.bsup_eq` and `IsNormal.blsub_eq` stay in the `Ordinal.IsNormal` namespace with an
  `Order.IsNormal` binder. Every use site already calls them by full name (content_search), so nothing
  breaks. Renaming them would be scope creep, so I did not ask.
- `apply_omega0_of_isNormal`, `iSup_add_natCast`, `iSup_mul_natCast` and their aliases are fine; the
  `natCast` suffix is correct for `+` and `*`.
- `IsNormal.eq_iff_zero_and_succ` is deprecated to `IsNormal.ext`. Fine.

### FixedPoint.lean
- `IsNormal.mem_range_deriv` was removed with no deprecated alias. That is a breaking rename (finding 1,
  blocking).
- The new deprecations use `since := "2025-10-25"`, but the rest of the PR uses 2025-12-25 (finding 2).
- `Ordinal.fp_iff_deriv` is a new name that is deprecated on arrival (finding 3). I verified the
  replacement; `Ordinal.mem_range_deriv` has to be written fully qualified inside `theorem IsNormal.…`.
- `apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv` and
  `mem_range_deriv` are renames with aliases (apart from the date issue). Fine.
- Call-site updates in `nfpFamily_fp`, `apply_le_nfpFamily`, `apply_lt_nfpFamily_iff`, `derivFamily_fp`,
  `le_iff_derivFamily`, `fp_iff_derivFamily`, `deriv_eq_id_of_nfp_eq_id`, `deriv_add_eq_mul_omega0_add`
  (`bot_eq_zero` from `IsNormal.ext`), `deriv_mul_eq_opow_omega0_mul`, `add_eq_right_iff_mul_omega0_le`,
  `add_le_right_iff_mul_omega0_le`, `mul_le_right_iff_opow_omega0_dvd`, `nfp_add_zero`, `nfp_mul_one`,
  `nfp_mul_opow_omega0_add`: all fine.
- Module doc: "two forms" matches the remaining API.

### Principal.lean / Veblen.lean
- `op_eq_self_of_principal`, `add_omega0_opow`, `mul_lt_omega0_opow` are mechanical.
- `isNormal_veblenWith_zero` is a rename with an alias. The existing `IsNormal.veblenWith` alias is now
  deprecated.
- `isNormal_veblen`, `isNormal_veblen_zero`, `veblenWith_succ`, `veblenWith_right_strictMono`,
  `omega0_opow_epsilon`, `mem_range_gamma`, `veblen_gamma_zero` are mechanical. Fine.

## Considered and not raised
- Dot-notation aliases in `Ordinal.IsNormal.*` do not rescue downstream code of the form
  `(isNormal_opow h).deriv_fp`, because that term now has type `Order.IsNormal`. This is inherent to the
  migration, not something this PR can fix.
- Splitting the `iSup_*_nat` renames and the `opow_add`/`opow_mul` golf into a separate PR is plausible,
  but it is a judgement call rather than a concrete defect. I raised only the wrong `iSup_pow_natCast` name.
- Asking for `Order.IsNormal.le_apply` / `le_iff_eq` helpers to replace the repeated
  `.strictMono.le_apply.ge_iff_eq'` would be a design preference, so I left it out.
