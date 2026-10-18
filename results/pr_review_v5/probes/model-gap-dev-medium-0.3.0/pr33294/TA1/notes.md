# Review notes: PR #33294, "deprecate `Ordinal.IsNormal` for `Order.IsNormal`"

## Method

I read `brief.md`, `pr.md`, `model.md` (objects, families, relations) and the full `diff.patch`. I read
the reviewed files through `ptool file_read`/`content_search` under `target/` and checked
existence with `declaration_search`. I ran `naming_norm` on the new names, did one `zulip_search` and
one `precedent_search` (nothing applicable), and checked every proposed edit with
`lean_verify_edit`. All scratch argument files are in `tmp/`. findings.json holds 28 findings.

## Object by object

### Mathlib/Order/IsNormal.lean
- `Order.IsNormal.monotone` (added): correct and minimal. `protected` is harmless. It is the
  natural replacement for `Ordinal.IsNormal.monotone`, but the PR's deprecation does not point to
  it (finding). `IsNormal` is defined only for `LinearOrder`, so there is nothing to generalize.
- Module docstring: the TODO "Replace `Ordinal.IsNormal` by this more general notion" is made stale by
  this PR, and the other TODO is already done in Topology/Order/IsNormal.lean (finding).

### Mathlib/SetTheory/Ordinal/Arithmetic.lean
- Module docstring: the `pred` bullet was dropped although `Ordinal.pred` is still defined and not
  deprecated (finding). The new `Order.succ`/`IsSuccLimit`/`IsNormal` paragraph is fine.
- Removed section header `### Normal ordinal functions`: the deprecated block now sits under the
  "predecessor" header (finding).
- `Ordinal.IsNormal` (def): `protected` plus `@[deprecated Order.IsNormal]` is the right mechanism, and
  the docstring is fine.
- Deprecated lemmas:
  - `limit_le`, `limit_lt`, `strictMono`, `refl`, `trans` and `isSuccLimit` point to drop-in
    replacements. Nothing to ask.
  - `monotone` points to the wrong replacement (finding).
  - `lt_iff`, `le_iff`, `inj`, `id_le`, `le_apply`, `le_iff_eq`, `le_set` and `le_set'` need usage
    messages (findings: le_iff_eq, lt_iff group, inj, le_set group).
  - `isNormal_iff_strictMono_limit → isNormal_iff` differs only in the implicitness of `f`. I left it
    alone.
  - The `set_option linter.deprecated false in` wrappers can be removed by stating the hypotheses
    with `IsNormal f`. Verified on `IsNormal.isSuccLimit` (finding).
  - The rewritten proof of `le_set` is a short derivation from `map_isLUB`, which is fine for a
    deprecated lemma whose statement differs.
- `isNormal_add_right`, `isSuccLimit_add`, `isNormal_mul_right`, `isSuccLimit_mul`: mechanical
  migrations, correct.

### Mathlib/SetTheory/Cardinal/Aleph.lean
- `isNormal_preOmega`, `isNormal_omega`: mechanical, fine.
- `preOmega_omega0`: changed only because of the `apply_omega0` rename. It would revert under the
  `Order.IsNormal.apply_omega0` finding.

### Mathlib/SetTheory/Cardinal/Cofinality.lean
- `isFundamentalSequence_of_isNormal`, `cof_eq_of_isNormal`, `cof_le_of_isNormal`: these should be
  `Order.IsNormal.*`, so dot notation keeps working and the edits to `cof_add`, `cof_preOmega` and
  `cof_omega` become unnecessary. Verified compile. The `isFundamentalSequence` alias also lost
  `protected` (findings).
- Deprecated aliases: same-statement aliases are correct in form, and the dates are consistent.
- `cof_add`, `cof_preOmega`, `cof_omega`: correct as written. They are touched only because of the
  rename.

### Mathlib/SetTheory/Ordinal/Enum.lean
- `isNormal_enumOrd`: `isNormal_iff.2` migration. Fine.

### Mathlib/SetTheory/Ordinal/Exponential.lean
- `isNormal_opow`: the type ascription is needed now that `IsNormal` is polymorphic. Fine.
- `opow_lt_opow_iff_right`, `opow_le_opow_iff_right`, `opow_right_inj`, `isSuccLimit_opow`,
  `right_le_opow`: correct `.strictMono.*` / `map_isSuccLimit` migrations.
- `opow_add`: unused `have`, a redundant `pos_iff_ne_zero` round trip, and `;` (finding, verified).
- `opow_mul`: `;` (finding, verified).
- The base-case rewrites of both and the docstring reflow are out of scope (finding).
- `iSup_pow_natCast`: the statement has no cast, so the name is wrong (finding, verified by probe).

### Mathlib/SetTheory/Ordinal/Family.lean
- Deprecated `map_iSup_of_bddAbove`, `map_iSup`, `map_sSup_of_bddAbove`, `map_sSup`: these need usage
  messages (finding). The `set_option` on `map_sSup` is unnecessary (finding, verified).
- `IsNormal.apply_of_isSuccLimit`: drop-in replacement, fine. `apply_of_isLimit` is retargeted to the
  new target, which is correct per the alias-retargeting convention.
- `IsNormal.bsup`: fully qualified `Order.IsNormal.map_iSup` where dot notation fits (finding,
  verified).
- `IsNormal.bsup`, `bsup_eq`, `blsub_eq` stay non-deprecated in the deprecated `Ordinal.IsNormal`
  namespace. The file's own TODO says `bsup` is slated for removal, so I did not file this.
- `IsNormal.eq_iff_zero_and_succ`: keeping its own statement under `@[deprecated]` is right (0 vs ⊥),
  but it needs a message (finding).
- `apply_omega0_of_isNormal`: should be `Order.IsNormal.apply_omega0` (finding, verified).
- `iSup_add_natCast`, `iSup_mul_natCast`: these names are accurate, but the renames are out of scope
  (finding).

### Mathlib/SetTheory/Ordinal/FixedPoint.lean
- Module docstring change (three forms → two forms): accurate (no `nfpBFamily` left in the file).
  Fine.
- `apply_lt_nfpFamily_iff`, `nfpFamily_fp`, `apply_le_nfpFamily`, `derivFamily_fp`,
  `le_iff_derivFamily`, `fp_iff_derivFamily`: mechanical, fine.
- `apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv`,
  `mem_range_deriv`: these lost dot notation, so I suggest `Order.IsNormal.*` (finding, verified for
  the nfp group). The counter-argument is that the family siblings live at root, so this is advisory.
- `IsNormal.mem_range_deriv` was deleted without deprecation (finding, blocking).
- Wrong `since` dates on four deprecations (finding, blocking).
- `fp_iff_deriv` is born deprecated, and `IsNormal.fp_iff_deriv` aliases a deprecated declaration
  (finding, verified).
- `deriv_eq_id_of_nfp_eq_id`, `deriv_add_eq_mul_omega0_add`, `deriv_mul_eq_opow_omega0_mul`
  (`bot_eq_zero` added for `IsNormal.ext`), `nfp_add_zero`, `nfp_mul_one`, `add_eq_right_iff_*`,
  `add_le_right_iff_*`, `mul_le_right_iff_*`, `nfp_mul_opow_omega0_add`: correct migrations.

### Mathlib/SetTheory/Ordinal/Principal.lean
- `op_eq_self_of_principal`, `add_omega0_opow`, `mul_lt_omega0_opow`: mechanical, correct.

### Mathlib/SetTheory/Ordinal/Topology.lean
- `enumOrd_isNormal_iff_isClosed`: should use dot notation for `map_iSup` (finding, verified).
- `Ordinal.isNormal_iff_strictMono_and_continuous` was already deprecated (2025-08-21), so there is
  nothing to ask.

### Mathlib/SetTheory/Ordinal/Veblen.lean
- `IsNormal.veblenWith` deprecated alias, `isNormal_veblenWith_zero` rename plus alias,
  `isNormal_veblen`, `isNormal_veblen_zero`, `veblenWith_succ`, `veblenWith_right_strictMono`,
  `omega0_opow_epsilon`, `mem_range_gamma`, `veblen_gamma_zero`: correct. `isNormal_veblenWith_zero`
  follows conclusion naming and matches `isNormal_veblen_zero`.

## Conventions: where filed, where left

1. **Name built from the declarations in the statement.** Filed: `iSup_pow_natCast` (no `Nat.cast`
   in the statement). Left: `iSup_add_natCast` and `iSup_mul_natCast` (`o + n` and `o * n` do cast),
   and `isNormal_veblenWith_zero` (statement `IsNormal (veblenWith f · 0)`).
2. **protected on clash.** Filed: inside the `isFundamentalSequence_of_isNormal` finding, where the
   deprecated alias dropped the original `protected`. Left: `Order.IsNormal.monotone`, which is
   already `protected`, and `IsNormal.veblenWith`, still `protected alias`.
3. **PR cut at natural seams.** Filed: the `iSup_*` renames (`iSup_add_natCast`) and the Exponential
   golf (Exponential.lean).
4. **Module docstring covers the main results.** Filed: Arithmetic `pred` bullet. Left: the FixedPoint
   docstring (accurate) and the Topology docstring (unchanged by the PR).
5. **Dot notation for namespaced lemmas.** Filed: `IsNormal.bsup` (Family l.383) and
   `enumOrd_isNormal_iff_isClosed` (Topology l.186). Left: the `Order.IsNormal.map_iSup H` / `map_sSup H`
   / `strictMono H` / `apply_of_isSuccLimit H` bodies of the deprecated lemmas whose `H` is
   `Ordinal.IsNormal`, because there `H.foo` resolves to the deprecated `Ordinal.IsNormal.foo`
   itself.
6. **Removed or moved declarations deprecated.** Filed: `IsNormal.mem_range_deriv`. Left: every other
   removed name, each of which has an alias (checked by content_search: cof_eq, cof_le,
   isFundamentalSequence, apply_omega0, iSup_add_nat, iSup_mul_nat, iSup_pow, apply_lt_nfp,
   nfp_le_apply, nfp_fp, apply_le_nfp, deriv_fp, le_iff_deriv, fp_iff_deriv, veblenWith_zero).
7. **Deprecation names the replacement and says how when it is not drop-in.** Filed: `IsNormal.monotone`
   (wrong replacement), `le_iff_eq`, `lt_iff` group, `inj`, `le_set` group, `map_iSup` group,
   `eq_iff_zero_and_succ`. Left: `limit_le`, `limit_lt`, `strictMono`, `refl`, `trans`, `isSuccLimit`,
   `apply_of_isSuccLimit` (drop-in), and `isNormal_iff_strictMono_limit` (only `f` implicitness).
8. **Deprecated declaration kept as a one-line derivation.** Left: the aliases are one line. `le_set`
   has a 3-line derivation, acceptable because its statement differs. `IsNormal.inj` and
   `IsNormal.le_iff` are already one-liners.
9. **Tactics one per line, no `;`.** Filed: `opow_add`, `opow_mul`. Left: `isFundamentalSequence_of_isNormal`
   (proof unchanged by the PR).
10. **Declaration in its main hypothesis's namespace.** Filed: `cof_eq_of_isNormal`, `cof_le_of_isNormal`,
    `isFundamentalSequence_of_isNormal`, `apply_omega0_of_isNormal`, and the FixedPoint group
    (`nfp_fp`). Left: `isNormal_veblenWith_zero` (its conclusion is the `IsNormal` statement).
11. **Unneeded steps removed.** Filed: `opow_add` (unused `have`, redundant `pos_iff_ne_zero` round trip),
    and the unnecessary `set_option` on `IsNormal.map_sSup`.
12. **Deprecate to the general counterpart, not to another redundant or deprecated lemma.** Filed:
    `IsNormal.fp_iff_deriv` aliases deprecated `fp_iff_deriv` (finding on `fp_iff_deriv`).
13. **Name states the conclusion; `_of_h` only to disambiguate.** Folded into convention 10: the
    `_of_isNormal` suffixes disappear when the lemmas move to `Order.IsNormal`.
14. **Comments and docstrings in step (stale TODO).** Filed: the Order/IsNormal.lean TODO. Also the
    removed section header in Arithmetic.lean.
15. **PR title and description precise.** Filed (PR-level finding).
16. **Duplicate lemmas deprecated.** Left: `Ordinal.isNormal_iff_strictMono_and_continuous` is already
    deprecated (Topology l.171, since 2025-08-21).
17. **Linter exemption not used for a warning fixable at source.** Filed: the `set_option
    linter.deprecated false in` block (target `IsNormal.limit_le`, verified on `isSuccLimit`) and the
    unnecessary one on `map_sSup`.
18. **Deprecated with a differing statement: keep its own statement.** Filed: inside the `fp_iff_deriv`
    finding. Left: `IsNormal.eq_iff_zero_and_succ`, which keeps its own statement, as it should.
19. **Siblings' naming pattern.** Left: the FixedPoint `nfp_fp` etc. mirror `nfpFamily_fp`,
    `derivFamily_fp`, `le_iff_derivFamily`, which is why the namespace finding there is advisory.
20. **Deprecate only to a replacement stating the same result.** Covered by the `IsNormal.monotone`
    (wrong target) and `le_iff_eq` (`StrictMono.le_apply` is not the same result) findings.
21. **Definition change lengthens proofs → intermediate lemmas.** Left: migrated proofs are the same
    length or shorter (`.strictMono.lt_iff_lt` and similar). `Order.IsNormal.monotone` was added
    for `H.monotone` uses.
22. **Only change what the purpose requires.** Filed: Exponential golf and the `iSup_*` renames (as
    in 3), and the Arithmetic `pred` docstring removal.
23. **A deprecated alias stays until its period ends; retarget rather than remove.** Left:
    `IsNormal.apply_of_isLimit` is retargeted, not removed (Family l.274), which is correct.
24. **No bare `_eq` suffix.** Left: no new name ends in a bare `_eq`.
25. **`since` in the attribute.** Left: every deprecation uses `since := ...`. The wrong dates are
    filed separately under correctness.
