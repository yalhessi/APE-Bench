# Review notes: PR #33337 (rename lemmas, InnerProductSpace/Projection/Submodule)

## What I did

Read `pr.md`, `model.md` and `diff.patch`. Read `Submodule.lean` in full (lines 1-246) and the header and scope commands of `Positive.lean` through `ptool file_read` and `content_search`. Read `LinearAlgebra/Projection.lean` lines 60-245 (`linearProjOfIsCompl`, `IsCompl.projection` and the lemmas named after them) and `Projection/Basic.lean` lines 650-685 (the `coe_starProjection` siblings). Tools used: `declaration_search` (`IsCompl.projection`), `content_search` (name spellings), `naming_norm` (all three renamed lemmas), `precedent_search`, `zulip_search`, and four `lean_verify_edit` runs.

## Object by object

- **`Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`** (renamed from `orthogonalProjection_eq_linearProjOfIsCompl`). The `_apply` makes sense: the LHS is `K.orthogonalProjection x`, and the change frees the unapplied form for the bundled lemma. The RHS is named `linearProjOfIsCompl` without `_apply`, as `IsCompl.projection_apply` does, so the name is fine. `naming_norm` returned `insufficient_evidence`. **Filed:** the redundant `Submodule.` prefixes inside `namespace Submodule` (lines 186, 187, 191). I checked that the unprefixed version compiles. I did not ask for proof golf: the proof is unchanged, and this is a rename PR.
- **`Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`** (renamed from `orthogonalProjection_coe_eq_linearProjOfIsCompl`). `coe_` before the function follows head-first order and matches `coe_orthogonalProjection_apply` and `isSymmetricProjection_iff_eq_coe_starProjection`. `naming_norm` returned `insufficient_evidence`, with `coe_` the plurality. The statement already uses the coercion `(K.orthogonalProjection : E →ₗ[𝕜] K)`. It is stated as an equality of bundled maps, and the pointwise lemma also exists. **Filed:** the redundant `Submodule.` prefix (line 200). That edit compiled.
- **`Submodule.coe_starProjection_eq_isComplProjection`** (renamed from `starProjection_coe_eq_isCompl_projection`). **Filed (blocking):** `isComplProjection` re-tokenises `IsCompl.projection`. Mathlib's names spell it `isCompl_projection` (Projection.lean:224, 604, 612), so the name should be `coe_starProjection_eq_isCompl_projection`; that edit compiled. **Filed (advisory):** the statement uses raw `.toLinearMap` where the `coe_` name and the sibling use the coercion. `with_reducible rfl` showed the coerced form is the same term, and the edit compiled once the line was broken under 100 characters. `naming_norm` flagged `toLinearMap_` as an *emerging* prefix (21 vs 7) for the statement as currently spelled. I resolved the mismatch toward the area's `coe_` siblings rather than ask for a rename to `toLinearMap_`.
- **`open Submodule in`** before that theorem (line 208, diff context). It looks redundant inside `namespace Submodule`, but it is not. A `lean_verify_edit` with it removed failed: `Invalid field 'projection': The environment does not contain 'IsCompl.projection'`. Generalized field notation on `h : IsCompl K Kᗮ` needs `open Submodule` to find `Submodule.IsCompl.projection`. Not filed.
- **The deprecated aliases** (three Submodule.lean commands, two retargeted and one added). The old 2025-07-11 aliases `orthogonalProjection_eq_linear_proj` and `orthogonalProjection_coe_linearMap_eq_linearProj` are kept and retargeted to the new names. New aliases with `since := "2025-12-26"` are added for each renamed lemma. Each alias is one line, pointing directly at the non-deprecated replacement (no chain), and the parallel one-liners are adjacent. Nothing to ask.
- **`LinearMap.IsSymmetricProjection.le_iff_range_le_range`** (Positive.lean:245). The only change is the call site. `Submodule` is not open there (opens at line 44: `InnerProductSpace RCLike LinearMap ContinuousLinearMap`), so the `Submodule.` prefix is needed. Only the rename in finding 1 would require updating it.
- **`Submodule.starProjection_le_starProjection_iff`** (Positive.lean:504). The only change is the call site, unprefixed inside a `Submodule.`-dotted declaration, which is correct. It needs the same update under finding 1.
- **The PR as a whole.** The title follows `type(Area): description`. **Filed (question):** "rename lemmas" does not say what is renamed to what, and no description is available.
- **Precedent and Zulip.** PR #32927 (themathqueen) pointed an author at the bundled `starProjection_coe_eq_isCompl_projection` instead of adding a pointwise `starProjection_eq_isCompl_projection`. So I did not ask for a pointwise `starProjection_apply_...` counterpart. On Zulip, Jireh Loreaux and Monica Omar chose the name `IsCompl.projection` (2025-07); nothing there supports fusing it into `isComplProjection`.
- **Generalization, duplication, scope, correctness.** Nothing to request. The PR only renames, with aliases, and moves nothing. The file compiles as left, and every verify run reported zero pre-existing errors.

## Message: conventions, places filed, places left

1. **Namespace grouping / no redundant prefix.** Filed: `orthogonalProjection_apply_eq_linearProjOfIsCompl` (lines 186, 187, 191) and `coe_orthogonalProjection_eq_linearProjOfIsCompl` (line 200). Left: Positive.lean:245 `Submodule.coe_starProjection_eq_isComplProjection`, because `Submodule` is not open in `namespace LinearMap` (open list at line 44). Positive.lean:504 is already unprefixed.
2. **Name built from the declarations' own spellings.** Filed: `coe_starProjection_eq_isComplProjection`, which should use `isCompl_projection`. Left: `linearProjOfIsCompl`, `orthogonalProjection` and `starProjection` are spelled as declared (`Submodule.linearProjOfIsCompl`, Projection.lean:145).
3. **Redundant or unused `open`.** Left: `open Submodule in` at line 208. Removing it failed to compile (dot notation `.projection` needs it).
4. **Head-first order.** Left: all three new names put `coe_` or `_apply` on the LHS head first (`coe_orthogonalProjection_...`, `coe_starProjection_...`, `orthogonalProjection_apply_eq_...`), which is the PR's own fix.
5. **Removed or moved declaration deprecated.** Left: all three old names have deprecated aliases (lines 195, 205, 213).
6. **Deprecation names its replacement.** Left: each alias's RHS is the drop-in replacement.
7. **Deprecated declaration as a one-line derivation.** Left: all are `alias` one-liners.
8. **Bundled-map equality over pointwise.** Left: the bundled `coe_orthogonalProjection_eq_linearProjOfIsCompl` exists, and the starProjection lemma is already bundled.
9. **Variants named by the differing term, not primes.** Left: no primes are introduced.
10. **Deprecate to the general counterpart, not a redundant local lemma.** Left: no alias chains. The 2025-07-11 aliases now target the new names directly.
11. **Coercion, not raw projection.** Filed: `coe_starProjection_eq_isComplProjection` (`.toLinearMap` -> `(K.starProjection : E →ₗ[𝕜] E)`). Left: `coe_orthogonalProjection_eq_linearProjOfIsCompl`, which already writes `(K.orthogonalProjection : E →ₗ[𝕜] K)` (line 199).
12. **Name states the conclusion, no needless `_of_h`.** Left: no hypothesis suffixes.
13. **Marginal-benefit change.** Left: three renames with deprecations have a clear benefit (head-first names), so I am not recommending closure.
14. **Case convention by kind.** Left: all theorems are lowerCamel-token snake_case, as Mathlib theorem names are.
15. **Title and description precise.** Filed (as a question): PR #33337, where "rename lemmas" names no renames and no description is available.
16. **Third-party stylistic change left to the author.** Left: the PR's changes are renames with deprecations, not taste edits to prose.
17. **Title follows `type(Area): description`.** Left: `chore(Analysis/InnerProductSpace/Projection/Submodule): rename lemmas` conforms.
18. **Name follows siblings' patterns.** Covered by the filed `isCompl_projection` finding, since the siblings at Projection.lean:224 and 604 spell it that way. Left: the `coe_`/`_apply` patterns match `coe_orthogonalProjection_apply` and `IsCompl.projection_apply`.
19. **Parallel one-liners adjacent.** Left: the paired deprecated aliases (lines 193-196 and 203-206) are adjacent with no blank line.
20. **Deprecate only to a replacement stating the same result.** Left: each alias targets the same statement under a new name.
21. **Rename with deprecation, without minimising deprecations.** Left: done for all three.
22. **Change only what the purpose requires.** Left: only names and call sites change, with no incidental proof rewrites. Findings 3-4 ask for small prefix cleanups in the declarations the PR touches, filed as advisory.
23. **Deprecated alias kept and retargeted on a further rename.** Left: both 2025-07-11 aliases are kept and retargeted (lines 193-194 and 203-204), as the convention asks.
24. **Equation lemma not ending in a bare `_eq`.** Left: every new name is `lhs_eq_rhs`.
25. **`since` in the attribute.** Left: every alias uses `@[deprecated (since := "...")]`.

## Verify runs (all in `tmp/`)

- `edit1.json`: the rename, the coercion, and `open Submodule in` removed. Result `compile_errors`: `IsCompl.projection` not found. This shows the `open` is needed.
- `edit2.json`: the rename and the coercion on one line, `open` kept, plus a `with_reducible rfl` example. Result `compiled`, with a longLine warning.
- `edit3.json`: the `Submodule.` prefixes dropped in lines 184-201. Result `compiled`, no warnings.
- `edit4.json`: the rename and the coercion with a line break. Result `compiled`, no warnings.
