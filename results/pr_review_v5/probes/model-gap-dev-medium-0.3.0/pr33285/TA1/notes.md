# Review notes: PR #33285 "chore(*): golf, add missing lemmas"

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Every tool call went through `./ptool`.
The argument files and raw outputs are in `tmp/`. Each edit I propose was compiled with
`lean_verify_edit`. Some first-round checks ran in parallel; every positive result was then re-run
sequentially and compiled again. One parallel as-is check hit an environment failure (missing
workspace dir) and passed when re-run. The as-is compile check passes for all 9 changed files, with
no errors or warnings.

## Object by object

**`Submodule.inf_comap_le_comap_add`** (Map.lean). The PR replaces `change` with a squeezed `simp only ... at h ⊢`
followed by `exact add_mem h.1 h.2`. That is the right form, because the `simp` feeds `exact`. The
`rw [SetLike.le_def]` line it keeps is redundant: the edit without it compiles. Finding filed
(advisory). Alternatives checked:
- `intro m h; simp_all [add_mem]` compiles. Not proposed: the explicit two-liner is short and readable.
- The term `fun _ h ↦ add_mem h.1 h.2` fails with a type mismatch.

**`IsContDiffImplicitAt.implicitFunctionData`** (ImplicitContDiff.lean). The new bullet is a 7-lemma `rw` and then
`simp +contextual [Prod.mk_zero_zero]`. A single `simp +contextual [Prod.ext_iff,
← h.bijective.injective.eq_iff, Prod.mk_zero_zero]` after `ext ⟨x, y⟩` compiles. Finding filed
(advisory). `Prod.mk_zero_zero` is not a simp lemma (`@[to_additive] mk_one_one` has no simp attr),
so it has to stay in the list. The second bullet is unchanged; I found nothing to ask there.

**`Submodule.IsOrtho.map`** (Orthogonal.lean). `aesop (add simp [isOrtho_iff_inner_eq])` replaces a readable
three-line proof. `simpa [isOrtho_iff_inner_eq] using h` compiles, and so does `simp_all [...]`.
Finding filed (blocking): use the lighter tactic, or keep the original proof.

**`ContinuousLinearMap.equivRange_symm_apply`** (Banach.lean). The new proof is the terminal, unsqueezed
`simp [ContinuousLinearEquiv.symm_apply_eq, Subtype.ext_iff]`, which conforms. I also checked the term
`(f.equivRange hinj hclo).symm_apply_apply x`, which compiles. I did not file it: it closes the goal only
across the definitional unfolding `e x ≡ ⟨f x, _⟩`, which the "rewrite rather than rfl across a
defeq" convention argues against. Dropping the stale "is there an API lemma" comment was right.

**`ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range`** (Banach.lean). The term proof is fine and
short. The argument `(Set.range f)` given to `.subtype_coe` can be inferred: `.subtype_coe _` compiles.
Finding filed (advisory). The docstring still matches the code, and the Fredholm TODO above it still
applies and stays.

**`LinearIsometry.isComplete_image_iff` / `isComplete_image_iff'`** (LinearIsometry.lean).
- The class-level lemma becomes `@[simp]`, and the primed one becomes
  `@[deprecated LinearIsometry.isComplete_image_iff (since := "2025-12-25")]` without `@[simp]`.
- I checked that the new simp lemma fires on a `LinearIsometry`: `simp only [LinearIsometry.isComplete_image_iff]`
  and `simpa using hs` both compile in examples.
- The deprecated lemma is a one-line derivation and records `since`, and simp and deprecated are not
  combined. All of that conforms.
- content_search finds no other use sites of `isComplete_image_iff'`.
- The same lean4#3107 workaround and its comments remain at l.99, 200, 204 and 873, and
  `simp only [SemilinearIsometryClass.nnnorm_map]` fires on a `LinearIsometry`. Finding filed
  (advisory, file-level): do the same for `nnnorm_map`, or fix the comments. The l.204 comment also
  names `SemilinearIsometryClass.enorm_map`, which does not exist.

**`Matrix.rank_eq_finrank_range_toLin`** (Rank.lean). The `range_e₂` `have` is replaced by `e₂.range`
(`LinearEquiv.range`), which is the inlining the convention asks for. The rest is unchanged context.
`aux₁`/`aux₂` are rewritten `at` before use, so they cannot be inlined as short terms. Nothing filed.

**`LinearEquiv.symm_prodComm`** (Prod.lean, new). It is `rfl` and `@[simp]`, which is fine. Its name breaks the sibling
pattern `prodComm_symm`: `Equiv`, `ContinuousLinearEquiv` (same `@[simp] ... := rfl` shape),
`AffineEquiv`, `ContinuousAffineEquiv`, `OrderIso`, `Homeomorph`, `UniformEquiv` and `Diffeomorph` all use
it, and so do this file's own `prodCongr_symm` and `prodProdProdComm_symm`. The rename compiles, and the name is
free. Finding filed (blocking). naming_norm returned insufficient_evidence on the leading prefix alone,
which does not measure the `X_symm` sibling pattern.

**`Ideal.cotangentEquivIdeal_symm_apply`** (Cotangent.lean).
- The statement cleanup (dropping the `by exact` timeout workaround, the `(F := ...) (f := ...)` named
  arguments and `(R := R)`, plus the obsolete comments) conforms to the workaround and
  inferable-argument conventions.
- The proof is `rw [symm_apply_eq]; ext; simp`, and `simp [LinearEquiv.symm_apply_eq, Subtype.ext_iff]`
  alone compiles. That matches the PR's own `equivRange_symm_apply`. Finding filed (advisory).

**`ContinuousLinearMap.iInfKerProjEquiv`** (Equiv.lean). The PR drops the `@continuous_subtype_val _ _ fun x => ...`
spelling, which is good. Checks on what is left:
- `(A := φ)` is required: removing it fails with a type mismatch.
- `by fun_prop` fails.
- The `<|` before the single identifier is redundant. A two-line form without it compiles. Finding filed
  (advisory).

**`ContinuousLinearEquiv.submoduleMap`** (Equiv.lean). It now uses `__ := LinearEquiv.submoduleMap e.toLinearEquiv p`,
which conforms to the `__ :=` convention. Two findings:
1. The statement change to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p` is not needed: the original
   `Submodule.map e p` compiles with the new body, and `submoduleMap_symm_apply` still states
   `x : p.map e`. Filed (advisory): revert the ascription.
2. The continuity fields are asymmetric, and `continuous_invFun` rebuilds membership through the inverse
   LinearEquiv. `(e.continuous.comp continuous_subtype_val).subtype_mk _` and its `e.symm` twin compile
   with either header. `by fun_prop` fails for both fields. Filed (advisory).

**PR title and description.** "golf, add missing lemmas" with "Cherry-picked parts of #33241". The PR adds only
one lemma, and it also deprecates a lemma, changes a simp set, changes a def's stated type and removes
workarounds, none of which is described. Filed (advisory). It also asks the author to state the relation
to #33241. Splitting a large PR is not a duplicate-PR situation, so I filed no duplicate finding.

## Conventions: places filed and places left

1. **Finishing tactic over hand-written rewrite chain.** Filed: `implicitFunctionData` (isCompl_ker first bullet),
   `cotangentEquivIdeal_symm_apply`, `IsOrtho.map`. Left: `inf_comap_le_comap_add`. Its
   `simp only ... at h ⊢; exact add_mem h.1 h.2` is a short explicit proof; `simp_all [add_mem]` compiles
   but would replace a readable two-liner (convention 5). `equivRange_symm_apply` is already a single `simp`.
2. **Derive from library API rather than rebuild.** Already in that form: `submoduleMap` reuses `LinearEquiv.submoduleMap`
   via `__ :=`, `antilipschitz_...` composes `equivRange.antilipschitz`, and Rank uses `e₂.range`. Left:
   `equivRange_symm_apply` → `symm_apply_apply x`. It compiles but relies on defeq, which conflicts with convention 10.
3. **Inline a short auxiliary `have`.** Rank's `range_e₂` was inlined by the PR (`e₂.range`), so it conforms. Left: `aux₁`/`aux₂`
   are modified by `rw ... at` before use, and they are not part of the diff.
4. **Terminal `simp` not squeezed.** It conforms everywhere: `equivRange_symm_apply` `simp [...]`, `implicitFunctionData`
   `simp +contextual [...]` and Cotangent `simp` are all terminal and unsqueezed.
5. **Omit syntax that elaboration supplies.** Filed: the `submoduleMap` type ascription
   `(e : M →ₛₗ[σ₁₂] M₂)` (the original statement compiles), and the redundant `<|` in `iInfKerProjEquiv`. In
   Cotangent the PR already removed `by exact`, `(R := R)` and the named args.
6. **Automation only when the explicit proof is not short and readable.** Filed: `IsOrtho.map` (aesop replaced
   3 readable lines). Left: `implicitFunctionData`'s old proof was 8 lines, and `simp +contextual` is reasonable.
7. **Short tactic block → term.** Left: `equivRange_symm_apply` term form relies on defeq (see 2), and the
   `inf_comap_le_comap_add` term `fun _ h ↦ add_mem h.1 h.2` fails to elaborate. The `submoduleMap` and
   `antilipschitz` proofs are already terms.
8. **Cleanup leaves out hunks that cost readability.** Filed: `IsOrtho.map` aesop, and the `submoduleMap`
   `continuous_invFun` (I propose a readable replacement rather than a revert).
9. **No `by exact`/`by simpa` around a term of matching type.** Already conforms: the PR removed `by exact` in Cotangent.
   No `by simpa using` wrappers remain in the diff.
10. **Rewrite rather than `change`/`rfl` across defeq.** Already conforms: `inf_comap_le_comap_add` and `equivRange_symm_apply`
    dropped `change`, and Cotangent replaced `ext; rfl` with `ext; simp`. Nothing to file. This is why
    the `symm_apply_apply` term was not proposed.
11. **Re-check workarounds.** Already conforms for Cotangent (`by exact` timeout) and `isComplete_image_iff` (lean4#3107).
    Filed: the remaining lean4#3107 workarounds/comments in LinearIsometry.lean. Left:
    `ContinuousLinearEquiv.ofBijective` in Banach.lean ("Porting note: `by exact` was not previously needed").
    Without `by exact` it fails ("Application type mismatch ... Continuous ⇑f expected Continuous
    ⇑(LinearEquiv.ofBijective ?m ⋯)"), so the workaround is still needed.
12. **Deprecated declaration is a one-line derivation.** Already conforms: `isComplete_image_iff'` is
    `LinearIsometry.isComplete_image_iff _`.
13. **Do not pass inferable arguments.** Filed: `antilipschitz_...` `(Set.range f)`. Left: `iInfKerProjEquiv`'s
    `(A := φ)`, which is required (checked).
14. **Attributes transferred on deprecation/move.** Already conforms: `@[simp]` moved from `isComplete_image_iff'` to
    `isComplete_image_iff`.
15. **Deprecate to the general counterpart.** Already conforms: it points at the class-level `LinearIsometry.isComplete_image_iff`.
16. **Squeeze a `simp` consumed by another tactic.** Already conforms: `inf_comap_le_comap_add` uses `simp only [...]` before
    `exact`, and the `implicitFunctionData` second bullet uses `simp only` before `obtain`/`exact` (unchanged).
17. **Comments kept in step with code.** The PR's removals of stale comments are correct. Filed: the remaining
    3107 comments in LinearIsometry.lean. The Banach "Fredholm" TODO still applies and stays. The `submoduleMap`
    docstring still holds.
18. **Precise PR title/description.** Filed (PR-level).
19. **`__ := obj` for reused fields.** Already conforms: `submoduleMap` uses `__ := LinearEquiv.submoduleMap ...`.
20. **No dense one-liners.** Filed: the `submoduleMap` `continuous_invFun`. Left: the `antilipschitz` term is short and
    reads on its own.
21. **Lighter tactic over grind/aesop.** Filed: `IsOrtho.map`.
22. **Names follow siblings.** Filed: `LinearEquiv.symm_prodComm` → `prodComm_symm`.
23. **`@[simp]` lemma not deprecated; simp and deprecated not combined.** Already conforms: the deprecated
    `isComplete_image_iff'` lost `@[simp]`, and its replacement is `@[simp]`.
24. **Duplicate of an open PR.** Not filed: this PR is a split of #33241, not a duplicate. The description
    finding asks the author to state the relation.
25. **Deprecation date in `since`.** Already conforms: `(since := "2025-12-25")`.
