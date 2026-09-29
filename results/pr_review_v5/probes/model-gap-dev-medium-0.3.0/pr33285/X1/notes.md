# Review notes: PR #33285 "chore(*): golf, add missing lemmas"

I read `brief.md`, `pr.md`, `model.md` and `diff.patch`, then used the tools (`ptool`): file_read
and content_search on the `target/` tree, declaration_search, naming_norm, precedent_search,
zulip_search, and lean_verify_edit. Every edit I propose was compiled with lean_verify_edit, which
recompiles the whole file. Findings are in `findings.json` (9, all advisory).

## Object by object

- **`Submodule.inf_comap_le_comap_add`** (Map.lean). The golf is correct, but the tactic block
  is still longer than it needs to be. `fun _ h ↦ q.add_mem h.1 h.2` compiles; without the `q.`
  it fails. Finding (proof-golf).

- **`IsContDiffImplicitAt.implicitFunctionData`** (ImplicitContDiff.lean). Only the first
  `isCompl_ker` branch changed. The PR's version works, but its `← injective.eq_iff` rewrite
  needs `Prod.mk_zero_zero` to undo itself: without it, the goal
  `f' (0, y) = 0 ↔ f' (0, y) = f' (0, 0)` is left open. One line,
  `simp +contextual [Prod.ext_iff, ← map_eq_zero_iff _ h.bijective.injective]`, compiles.
  Finding (proof-golf, low priority). The other fields are unchanged; no issue.

- **`Submodule.IsOrtho.map`** (Orthogonal.lean). `aesop (add simp ...)` works, but
  `simpa [isOrtho_iff_inner_eq] using h` and `simp_all [isOrtho_iff_inner_eq]` both compile.
  Maintainers on Zulip (Morrison, Rothgang) prefer simp/simp_all over a terminal aesop.
  Finding (style). The neighbouring `IsOrtho.comap` is unchanged, so I raised nothing on it.

- **`ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range`** (Banach.lean). The term
  proof via `(equivRange ..).antilipschitz` composed with `AntilipschitzWith.subtype_coe` is
  clean. The witness `_` is fine because the statement is existential. Nothing to request.

- **`ContinuousLinearMap.equivRange_symm_apply`** (Banach.lean). The simp proof works;
  `(f.equivRange hinj hclo).symm_apply_apply x` is the canonical term, and it compiles with the
  whole file. Removing the "is there an API lemma" comment is right. Finding (proof-golf).

- **`LinearIsometry.isComplete_image_iff` / `isComplete_image_iff'`** (LinearIsometry.lean).
  Adding `@[simp]` to the class-generic lemma and deprecating the primed specialisation is
  consistent. I checked that `simp only [LinearIsometry.isComplete_image_iff]` fires on a
  concrete `LinearIsometry`. `isComplete_image_iff'` has no remaining uses (only
  `scripts/nolints_prime_decls.txt`), and the deprecation date 2025-12-25 matches the review
  time. A theorem rather than an alias is acceptable, since the signature is narrower. The same
  file still carries lean4#3107 workaround comments for `nnnorm_map`/`enorm_map` (lines 99, 200,
  204, 873), which this change makes stale. I checked that the class `nnnorm_map` fires under
  simp on a `LinearIsometry`. Finding (scope/documentation, advisory).

- **`Matrix.rank_eq_finrank_range_toLin`** (Rank.lean). Replacing the local `range_e₂` with
  `e₂.range` is correct and idiomatic. The model's "removed" entry is a change-graph artifact:
  the declaration is only modified. Nothing to request.

- **`LinearEquiv.symm_prodComm`** (Prod.lean, new). The statement and `rfl` proof are fine, and
  it does not duplicate anything in `LinearEquiv` (declaration_search/content_search).
  Naming: 8 sibling families use `prodComm_symm`, including `ContinuousLinearEquiv.prodComm_symm`
  in a file this PR touches, and the same-file siblings use `_symm` suffixes
  (`prodCongr_symm`, `prodProdProdComm_symm`). Only `LinearIsometryEquiv.symm_prodComm` differs.
  naming_norm was inconclusive for the bare subject `symm`. Finding (naming).

- **`Ideal.cotangentEquivIdeal_symm_apply`** (Cotangent.lean). Dropping `(R := R)`, the
  `by exact` and the explicit `(F := ..) (f := ..)` from the statement is good cleanup, and it
  compiles. The proof reduces to `I.cotangentEquivIdeal.symm_apply_eq.2 rfl`, which I verified.
  Finding (proof-golf, low priority). I considered asking for `@[simp]` and did not: nothing
  shows it is wanted.

- **`ContinuousLinearMap.iInfKerProjEquiv`** (Equiv.lean). Dropping the explicit `@` predicate
  on `continuous_subtype_val` is fine. I tried to golf further, with `(continuous_apply _).comp
  continuous_subtype_val` and with `fun_prop`, with and without `dsimp`; all fail because the
  `toFun` is not syntactically `Subtype.val`. Nothing to request.

- **`ContinuousLinearEquiv.submoduleMap`** (Equiv.lean). Two findings.
  (a) The type change to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p` is unnecessary: the original
  `Submodule.map e p` compiles with the PR's new body, and so does the rest of the file
  (`submoduleMap_apply`, `submoduleMap_symm_apply`, `ofSubmodules`). It also leaves the def
  spelled differently from `submoduleMap_symm_apply (x : p.map e)`.
  (b) The two continuity fields are proved in asymmetric, roundabout ways. Each is
  `(e(.symm).continuous.comp continuous_subtype_val).subtype_mk _`, which compiles with either
  signature. `by fun_prop` does not work.

## Checked, no finding
- Whether the PR as it stands compiles: I did not rerun it on its own, but every whole-file
  lean_verify_edit call reported no `errors_already_in_the_file`.
- Documentation: no docstrings were removed. The "documentation:removed" entries in `model.md`
  are code comments, and removing them is appropriate (the stale lean4#3107 note, the
  heartbeat/timeout notes, the "is there an API lemma" note).
- Correctness: I found no semantic problem in any changed statement.
