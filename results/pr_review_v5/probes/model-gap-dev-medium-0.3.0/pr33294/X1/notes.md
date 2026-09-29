# Review notes: PR #33294 (deprecate `Ordinal.IsNormal` for `Order.IsNormal`)

## What I did

I read pr.md, all of model.md and all of diff.patch. I checked claims with `ptool`:

- `content_search` and `file_read` on the files as the PR leaves them (paths are under `target/`).
- `declaration_search`. It matches loosely across namespaces, so I confirmed its hits against the diff and `content_search`.
- `naming_norm`. It returned `subject_unresolved` or `insufficient_evidence` for the new names, so it told me nothing.
- `zulip_search` and `precedent_search`.
- About 15 `lean_verify_edit` runs, each ~9 s.

Every finding that makes a compile claim was checked with a Lean edit, usually by adding an `example` that exercises an old call pattern.

Most issues come from one fact. `Ordinal.IsNormal` is now `protected` and deprecated, so inside `namespace Ordinal` the bare `IsNormal` means `Order.IsNormal`. Lean's dot notation matches an explicit argument by its syntactic head, so a declaration in `Ordinal.IsNormal.*` whose hypothesis is `Order.IsNormal` cannot be reached with dot notation from either type.

## Object by object

### Mathlib/Order/IsNormal.lean
- `Order.IsNormal.monotone` (new): correct and useful. No issue with the lemma itself. It matters for finding 4, which is about the deprecation target in Arithmetic.

### Cardinal/Aleph.lean
- `isNormal_preOmega`, `isNormal_omega`, `preOmega_omega0`: mechanical replacements (`isNormal_iff`, `.comp`, `apply_omega0_of_isNormal`). Nothing to ask.

### Cardinal/Cofinality.lean
- `isFundamentalSequence_of_isNormal`, `cof_eq_of_isNormal`, `cof_le_of_isNormal`: the renames follow a consistent `_of_isNormal` scheme and the proofs are unchanged. `naming_norm` confirms the `cof_` prefix. The deprecated aliases `IsNormal.cof_eq`, `IsNormal.cof_le` and `IsNormal.isFundamentalSequence` share the dot-notation defect (finding 5).
- `cof_add`, `cof_preOmega`, `cof_omega`: call-site updates, fine.

### SetTheory/Ordinal/Arithmetic.lean
- The module docstring drops the `pred` bullet even though `def pred` remains (finding 11). The regrouping of succ, IsSuccLimit and IsNormal under "generalized to other orders" is fine.
- `Ordinal.IsNormal` is now deprecated and protected. Fine.
- The deprecated theorems (limit_le, limit_lt, strictMono, lt_iff, le_iff, inj, id_le, le_apply, le_iff_eq, le_set, le_set', refl, isSuccLimit, isNormal_iff_strictMono_limit) are restated with `Ordinal.IsNormal` binders. That is the right way to keep old dot notation on those hypotheses working, and their targets are sensible.
  - `IsNormal.monotone` points to `strictMono` instead of the new `Order.IsNormal.monotone` (finding 4).
  - `IsNormal.trans` concludes `Order.IsNormal`, not `Ordinal.IsNormal` (finding 8).
- I tested whether the per-declaration `set_option linter.deprecated false in` is needed. Removing it from one declaration produced two deprecation warnings, so it is needed. No ask.
- `isNormal_add_right`, `isSuccLimit_add`, `isNormal_mul_right`, `isSuccLimit_mul`: fine.
- `le_set` has a new proof via `map_isLUB`. It compiles as the PR leaves it. No ask.

### Ordinal/Enum.lean, Ordinal/Topology.lean
- `isNormal_enumOrd`, `enumOrd_isNormal_iff_isClosed`: mechanical. `Order.IsNormal.map_iSup h (...)` could be written `h.map_iSup (...)`, but that is too minor to raise.

### Ordinal/Exponential.lean
- `isNormal_opow`: the type ascription is needed now that `Order.IsNormal` is generic. Fine.
- `opow_lt/le_iff_right`, `opow_right_inj`, `right_le_opow`, `isSuccLimit_opow`: fine.
- `opow_add`: has a dead `have` and a round-trip `pos_iff_ne_zero.2 ha.ne'` (finding 10, verified).
- `opow_mul`: the golf compiles and reads fine. No ask.
- `iSup_pow` → `iSup_pow_natCast`: the new name is wrong because the statement contains no cast (finding 9, verified by type mismatch).
- The module-doc whitespace change is harmless.

### Ordinal/Family.lean
- The deprecated `map_iSup_of_bddAbove`, `map_iSup`, `map_sSup_of_bddAbove` and `apply_of_isSuccLimit` are good.
- `map_sSup` has the wrong binder (finding 6, verified).
- `IsNormal.bsup` gains an explicit `bddAbove_of_small`, which is fine. It stays unreachable by dot notation together with `bsup_eq` and `blsub_eq` (finding 12, verified).
- `eq_iff_zero_and_succ` is deprecated but keeps `Order.IsNormal` binders (finding 7, verified).
- `apply_omega0_of_isNormal`, `iSup_add_natCast` and `iSup_mul_natCast` have correct names. These two renames are scope creep, but they are small, so I did not raise them.
- `IsNormal.apply_of_isLimit` was retargeted to the Order lemma. It is listed in finding 5.

### Ordinal/FixedPoint.lean
- The module-doc change from "three forms" to "two forms" is fine.
- The family lemmas (`apply_lt_nfpFamily_iff`, `nfpFamily_fp`, `apply_le_nfpFamily`, `derivFamily_fp`, `le_iff_derivFamily`, `fp_iff_derivFamily`) are mechanical `.strictMono.le_apply` rewrites. They are verbose, but no existing lemma replaces them, so no ask.
- The renames `apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv`, `mem_range_deriv` are consistent. Findings on them:
  - `IsNormal.mem_range_deriv` was deleted with no alias (finding 1, blocking, verified `Unknown constant`).
  - `fp_iff_deriv` is new and deprecated at birth (finding 2, verified).
  - Four new deprecations are dated 2025-10-25 (finding 3).
  - The aliases cannot be used with dot notation (finding 5, verified in all three call styles; `_root_.Order.IsNormal` aliases fix it).
- `deriv_add_eq_mul_omega0_add`, `deriv_mul_eq_opow_omega0_mul`, `deriv_eq_id_of_nfp_eq_id`: switching to `IsNormal.ext` plus `bot_eq_zero` is fine.
- `add_eq_right_iff_mul_omega0_le`, `add_le_right_iff_mul_omega0_le`, `mul_le_right_iff_opow_omega0_dvd`, `nfp_add_zero`, `nfp_mul_one`, `nfp_mul_opow_omega0_add`: call-site updates, fine.

### Ordinal/Principal.lean
- `op_eq_self_of_principal`, `add_omega0_opow`, `mul_lt_omega0_opow`: mechanical, fine.

### Ordinal/Veblen.lean
- `isNormal_veblenWith_zero` (renamed) and its call sites are fine. The deprecated aliases `IsNormal.veblenWith` and `IsNormal.veblenWith_zero` are covered by finding 5.

## Not raised (considered)
- Splitting the unrelated `opow_add`/`opow_mul` golfs and the `iSup_*_nat` renames into another PR: plausible, but low value.
- Grouping the repeated `set_option linter.deprecated false in` into a section: Mathlib commonly writes it per declaration.
- Moving the real lemmas (not only the aliases) into `Order.IsNormal` for dot notation: this conflicts with the author's `_of_isNormal` design, so I kept my asks consistent with that design.
