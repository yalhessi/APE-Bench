# Review notes: PR #33294 (deprecate `Ordinal.IsNormal` for `Order.IsNormal`)

## Method

- Read `pr.md`, all of `model.md` (every object, family and relation) and the whole of `diff.patch`.
- All tool calls went through `./ptool`. I read the PR's files at `target/Mathlib/...`.
- I used `content_search` / `declaration_search` to check for missing aliases, remaining uses of deprecated names, and the TODO in `Order/IsNormal.lean`.
- `zulip_search`, `precedent_search` and `naming_norm` were used for context. None settled the dot-notation question below.
- Every edit I propose was compiled with `lean_verify_edit`; all compiled clean.
  - One control edit with a deliberately unknown identifier was rejected, which confirms the tool really compiles.
- Edit argument files are in `tmp/`.

## Findings written: 10 (see findings.json)

1. **`IsNormal.mem_range_deriv` removed with no deprecated alias** (blocking). It was declared in the base; this is the only renamed lemma in the PR with no alias.
2. **Wrong `since` dates (`2025-10-25`) on four FixedPoint deprecations** (blocking). Everything else in the PR uses `2025-12-25`.
3. **`Ordinal.fp_iff_deriv` is a new name, deprecated at birth.** Make `IsNormal.fp_iff_deriv` the deprecated theorem instead.
   - It needs the qualified `Ordinal.mem_range_deriv`. With the bare name, Lean resolved to the deprecated `IsNormal.mem_range_deriv` and warned.
4. **`Ordinal.IsNormal.monotone` points to `Order.IsNormal.strictMono`.** It should point to `Order.IsNormal.monotone`, which this PR adds.
5. **Stale TODO in `Mathlib/Order/IsNormal.lean`:** "Replace `Ordinal.IsNormal` by this more general notion." This PR does that replacement.
6. **The `pred o` bullet was dropped from the Arithmetic.lean module doc.** `Ordinal.pred` is still defined there at line 290.
7. **`iSup_pow_natCast` is misnamed.** The statement uses the monoid power `o ^ (n : ℕ)`, not a cast; Lean rejected the cast version of the statement. Keep `iSup_pow`.
8. **`opow_add` has a dead `have`** and a roundabout `pos_iff_ne_zero.2 ha.ne'` / `one_le_iff_ne_zero.2 ha.ne'`. I compiled a golfed version.
9. **`IsNormal.bsup` should use dot notation `H.map_iSup (bddAbove_of_small _)`.** It removes the awkward `<;>`/`rfl` line split; the same applies in Topology.lean.
10. **Restore a section header for the deprecated `Ordinal.IsNormal` block in Arithmetic.lean.** It now sits under "The predecessor of an ordinal".

## Object by object: checked, nothing to request

- **`Order.IsNormal.monotone` (added):** correct, `protected` like `IsNormal.id`, and placed in the LinearOrder section. No generalisation is available, because the structure needs `LinearOrder`.
- **Aleph.lean (`isNormal_preOmega`, `isNormal_omega`, `preOmega_omega0`):** mechanical switches to `isNormal_iff` / `.comp` / `apply_omega0_of_isNormal`. Fine.
- **Cofinality.lean (`isFundamentalSequence_of_isNormal`, `cof_eq_of_isNormal`, `cof_le_of_isNormal`, plus aliases):**
  - Aliases are present with consistent dates.
  - `naming_norm` says `cof_` conforms (27/27).
  - I considered asking for `Order.IsNormal.cof_eq` etc. to keep dot notation. Call sites got longer (`cof_eq_of_isNormal isNormal_preOmega ...`). I found no Zulip or precedent evidence of a convention either way, so I did not file it.
  - The call sites `cof_add`, `cof_preOmega` and `cof_omega` are fine.
- **Arithmetic.lean deprecated block:**
  - I tested whether the 15 `set_option linter.deprecated false in` lines are needed. Deleting the one before `IsNormal.limit_le` produced a "`Ordinal.IsNormal` has been deprecated" warning, so they are needed (no finding).
  - Deprecation targets are fine apart from `monotone`. `le_iff_eq -> StrictMono.le_apply` is acceptable, since no exact lemma exists.
  - The `le_set` proof rewrite via `map_isLUB` is fine. It shadows `H` in `fun H ↦`, which is minor and not filed.
  - `IsNormal.trans` now concludes `Order.IsNormal (f ∘ g)`; this is defeq and harmless.
- **`isNormal_add_right`, `isNormal_mul_right`, `isSuccLimit_add`, `isSuccLimit_mul`:** mechanical. Fine.
- **Enum.lean `isNormal_enumOrd` and Topology.lean `enumOrd_isNormal_iff_isClosed`:** fine. The Topology call site is covered by finding 9.
- **Exponential.lean:**
  - `isNormal_opow` needs the `(a ^ · : Ordinal → Ordinal)` ascription because `Order.IsNormal` is heterogeneous. Fine.
  - `opow_lt/le_opow_iff_right`, `opow_right_inj`, `right_le_opow` and `isSuccLimit_opow` are fine.
  - `opow_mul`'s golf (`by_cases c = 0 <;> simp_all`) compiles and is acceptable.
  - The module-doc whitespace change is unrelated but harmless (not filed).
- **Family.lean:**
  - Deprecations of `map_iSup(_of_bddAbove)`, `map_sSup(_of_bddAbove)` and `apply_of_isSuccLimit` are fine.
  - The `apply_of_isLimit` retarget is fine.
  - `apply_omega0_of_isNormal`, `iSup_add_natCast` and `iSup_mul_natCast` are correctly named (their statements contain `↑n`) and have aliases.
  - Noted, not filed:
    - Deprecated `IsNormal.map_sSup` takes `Order.IsNormal` while its siblings take `Ordinal.IsNormal`, so its `set_option` is redundant.
    - `IsNormal.bsup`, `bsup_eq` and `blsub_eq` remain in the `Ordinal.IsNormal` namespace with `Order.IsNormal` hypotheses, so dot notation cannot reach them. This is inconsistent with the `_of_isNormal` renames, but plausibly left for the bsup deprecation.
    - The `iSup_add_nat`/`iSup_mul_nat` renames are slightly out of scope for the PR title.
  - `IsNormal.eq_iff_zero_and_succ -> IsNormal.ext` is fine.
- **FixedPoint.lean:**
  - Renames `apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv` and `mem_range_deriv` are fine; findings 1-3 cover the alias and date problems.
  - The module-doc change ("two forms") matches the file's two sections.
  - The `bot_eq_zero` additions after the `IsNormal.ext` switch are fine, as are `deriv_eq_id_of_nfp_eq_id` (`.ext .id`) and the `.strictMono.le_apply.ge_iff_eq'` replacements.
- **Principal.lean (`op_eq_self_of_principal`, `add_omega0_opow`, `mul_lt_omega0_opow`):** mechanical. Fine.
- **Veblen.lean:** the `isNormal_veblenWith_zero` rename has an alias. The newly deprecated `protected alias IsNormal.veblenWith` and the call-site updates are fine.
- **Remaining uses:** a search over `target/Mathlib` found no uses of the deprecated names outside the changed files: `isNormal_iff_strictMono_limit`, `IsNormal.refl`, `.apply_omega0`, `.limit_le`, `.limit_lt`, `IsNormal.trans`, `iSup_add_nat`, `iSup_mul_nat`, and Ordinal's `iSup_pow`.
