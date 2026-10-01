import json
notes = """Review of #33285 (golf + one new lemma). Every proposed edit below was compiled with lean_verify_edit against the PR's workspace.

- Submodule.inf_comap_le_comap_add (Map.lean): proof only. The PR replaces two `change`s with `simp only [...] at h ⊢`, but membership in comap/inf and `(f₁ + f₂) m` all unfold by defeq, so `fun _ h ↦ q.add_mem h.1 h.2` compiles as a term proof. (Plain `add_mem` does not elaborate there; `q.add_mem` does.) Statement, name and placement unchanged; nothing in the library replaces it. Finding: golf to the term proof.

- IsContDiffImplicitAt.implicitFunctionData (ImplicitContDiff.lean): only the first `isCompl_ker` branch changed. I checked whether `Prod.mk_zero_zero` can be dropped from `simp +contextual`: it cannot (the goal is left at `f' (0, y) = 0 ↔ f' (0, y) = f' (0, 0)`). The new proof is shorter and readable. Nothing to ask.

- Submodule.IsOrtho.map (Orthogonal.lean): proof replaced by a terminal `aesop (add simp [isOrtho_iff_inner_eq])`. `simpa [isOrtho_iff_inner_eq] using h` and `simp_all [isOrtho_iff_inner_eq]` both compile without warnings, and maintainers (Kim Morrison on Zulip) have asked for terminal aesop to be replaced by simp/simp_all where that works. Statement and name unchanged. Finding: use simpa.

- ContinuousLinearMap.antilipschitz_of_injective_of_isClosed_range (Banach.lean): the calc proof becomes a term built from `AntilipschitzWith.subtype_coe` and `ContinuousLinearEquiv.antilipschitz` on `equivRange`. It is a clean golf. Both completeness hypotheses are still needed (one for the domain, one for the closed range), and the statement is unchanged. Nothing to ask.

- ContinuousLinearMap.equivRange_symm_apply (Banach.lean): the 8-line proof and its "is there an API lemma" comment are replaced by `simp [ContinuousLinearEquiv.symm_apply_eq, Subtype.ext_iff]`. Removing the comment is fine. The API lemma the old comment asked for is `symm_apply_apply`: `⟨f x, _⟩` is defeq to `f.equivRange hinj hclo x`, so `(f.equivRange hinj hclo).symm_apply_apply x` closes the goal as a term (`symm_apply_eq.mpr rfl` also works). Attribute and statement unchanged. Finding: use the term proof.

- LinearIsometry.isComplete_image_iff / isComplete_image_iff' (LinearIsometry.lean, one family): the PR tags the class-generic lemma `@[simp]` because lean4#3107 is fixed, and deprecates the LinearIsometry-specific primed version. I checked that `simp` now proves the primed statement through the generic lemma, so the simp tag works. The deprecation date matches the PR's push date (2025-12-25), and no uses of `isComplete_image_iff'` remain in Mathlib. Keeping the deprecated declaration as a `theorem` rather than an `alias` keeps dot notation on `LinearIsometry` working. The similar lean4#3107 comments on `nnnorm_map`/`enorm_map` point to class lemmas that do not exist, so they are a separate job. Nothing to ask.

- Matrix.rank_eq_finrank_range_toLin (Rank.lean; the change graph lists it as both modified and removed, which is one declaration whose proof changed): the hand-proved `range_e₂` is replaced by the existing `LinearEquiv.range`. Correct and minimal; statement unchanged. Nothing to ask.

- LinearEquiv.symm_prodComm (Prod.lean, new): a `@[simp]` rfl lemma `(prodComm R M M₂).symm = prodComm R M₂ M`. No `LinearEquiv.prodComm_symm` exists, so this does not duplicate anything. The statement, attribute and placement in `section prodComm` are right. The name does not match its siblings: `Equiv.prodComm_symm`, `ContinuousLinearEquiv.prodComm_symm`, `Homeomorph.prodComm_symm`, `AffineEquiv.prodComm_symm`, `OrderIso.prodComm_symm`, `Diffeomorph.prodComm_symm` and, in this same file, `LinearEquiv.prodProdProdComm_symm` all put `_symm` last. Only `LinearIsometryEquiv.symm_prodComm` uses the `symm_` prefix. naming_norm on the `symm` subject came back insufficient_evidence (plurality only), so this rests on the sibling names. Finding: rename to `prodComm_symm`.

- Ideal.cotangentEquivIdeal_symm_apply (Cotangent.lean): the PR drops the `(R := R)`, `(F := ...)`/`(f := ...)` and `by exact` workarounds and their stale comments, and the statement still elaborates without a timeout, which is a good cleanup. The proof `rw [symm_apply_eq]; ext; simp` can be the term `I.cotangentEquivIdeal.symm_apply_eq.mpr rfl`. Finding: golf.

- ContinuousLinearMap.iInfKerProjEquiv (Topology/Algebra/Module/Equiv.lean): the explicit `@continuous_subtype_val _ _ (fun x => ...)` becomes plain `continuous_subtype_val`, which compiles. It could be squeezed onto one line, but that is too minor to ask for. Nothing to ask.

- ContinuousLinearEquiv.submoduleMap (Topology/Algebra/Module/Equiv.lean): the fields are rebuilt from `LinearEquiv.submoduleMap` via `__ :=`, a good use of existing API. Two problems. (1) The PR also changes the codomain type from `Submodule.map e p` to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p`. I compiled the new body against the original statement and the whole file still compiles. The change is not needed, it changes a public def's type, and it makes the def disagree with `LinearIsometryEquiv.submoduleMap` and with this file's own `submoduleMap_symm_apply (x : p.map e)` and `ofSubmodules_apply (h : p.map e = q)`. Finding: revert the type. (2) `continuous_invFun` rebuilds the membership proof by applying `(LinearEquiv.submoduleMap e.toLinearEquiv p).symm ⟨x, hx⟩` inside `Continuous.restrict`, and the two fields are written in different styles. The symmetric `(e.continuous.comp continuous_subtype_val).subtype_mk _` and `(e.symm.continuous.comp continuous_subtype_val).subtype_mk _` compile with either statement. Finding: use them.
"""
findings = [
 {"path":"Mathlib/Algebra/Module/Submodule/Map.lean","line_start":596,
  "claim":"`Submodule.inf_comap_le_comap_add`: the golfed proof still runs `rw [SetLike.le_def]; intro; simp only [mem_comap, mem_inf, LinearMap.add_apply] at h ⊢; exact add_mem ...`. Membership in `comap`/`⊓` and `(f₁ + f₂) m` unfold by definition, so the whole tactic block is unnecessary.",
  "suggested_fix":"Replace the proof with the term `fun _ h ↦ q.add_mem h.1 h.2` (it compiles; plain `add_mem` does not elaborate here).",
  "severity":"advisory"},
 {"path":"Mathlib/Analysis/InnerProductSpace/Orthogonal.lean","line_start":334,
  "claim":"`Submodule.IsOrtho.map`: the new proof is a terminal `aesop (add simp [isOrtho_iff_inner_eq])` where `simp` already closes the goal. Terminal aesop is slower and less predictable than the simp call it amounts to.",
  "suggested_fix":"Replace the proof with `simpa [isOrtho_iff_inner_eq] using h` (or `simp_all [isOrtho_iff_inner_eq]`); both compile without warnings.",
  "severity":"advisory"},
 {"path":"Mathlib/Analysis/Normed/Operator/Banach.lean","line_start":368,
  "claim":"`ContinuousLinearMap.equivRange_symm_apply`: the proof is a `simp [ContinuousLinearEquiv.symm_apply_eq, Subtype.ext_iff]` call, but the statement is an instance of `ContinuousLinearEquiv.symm_apply_apply`, since `⟨f x, _⟩` is definitionally `f.equivRange hinj hclo x`. That is the API lemma the removed comment was asking for.",
  "suggested_fix":"Replace the proof with the term `(f.equivRange hinj hclo).symm_apply_apply x` (compiles).",
  "severity":"advisory"},
 {"path":"Mathlib/LinearAlgebra/Prod.lean","line_start":657,
  "claim":"`LinearEquiv.symm_prodComm` is named with a `symm_` prefix, while the `(X.prodComm ...).symm = ...` lemmas put `_symm` last: `Equiv.prodComm_symm`, `ContinuousLinearEquiv.prodComm_symm`, `Homeomorph.prodComm_symm`, `AffineEquiv.prodComm_symm`, `OrderIso.prodComm_symm`, and `LinearEquiv.prodProdProdComm_symm` later in this same file.",
  "suggested_fix":"Rename the lemma to `LinearEquiv.prodComm_symm`.",
  "severity":"advisory"},
 {"path":"Mathlib/RingTheory/Ideal/Cotangent.lean","line_start":153,
  "claim":"`Ideal.cotangentEquivIdeal_symm_apply`: the new tactic proof `rw [I.cotangentEquivIdeal.symm_apply_eq]; ext; simp` is longer than needed. After `symm_apply_eq` the goal holds by `rfl`.",
  "suggested_fix":"Replace the proof with the term `I.cotangentEquivIdeal.symm_apply_eq.mpr rfl` (compiles).",
  "severity":"advisory"},
 {"path":"Mathlib/Topology/Algebra/Module/Equiv.lean","line_start":1291,
  "claim":"`ContinuousLinearEquiv.submoduleMap`: the PR changes the def's codomain from `Submodule.map e p` to `Submodule.map (e : M →ₛₗ[σ₁₂] M₂) p`, but the new `__ := LinearEquiv.submoduleMap e.toLinearEquiv p` body compiles against the original statement, so the change is not needed. It alters a public type and makes it disagree with `LinearIsometryEquiv.submoduleMap` and with this file's own `submoduleMap_symm_apply (x : p.map e)` and `ofSubmodules_apply (h : p.map e = q)`.",
  "suggested_fix":"Restore the type `p ≃SL[σ₁₂] Submodule.map e p` and keep the new body (the whole file compiles with it).",
  "severity":"advisory"},
 {"path":"Mathlib/Topology/Algebra/Module/Equiv.lean","line_start":1291,
  "claim":"`ContinuousLinearEquiv.submoduleMap`: `continuous_invFun` rebuilds the membership proof by applying `(LinearEquiv.submoduleMap e.toLinearEquiv p).symm ⟨x, hx⟩` inside `Continuous.restrict`, and the two continuity fields are written in different styles, though they prove mirror-image facts.",
  "suggested_fix":"Write both fields symmetrically: `continuous_toFun := (e.continuous.comp continuous_subtype_val).subtype_mk _` and `continuous_invFun := (e.symm.continuous.comp continuous_subtype_val).subtype_mk _` (compiles).",
  "severity":"advisory"},
]
out = {"notes": notes, "findings": findings}
json.dump(out, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/post-carryover-replan/results/pr_review_v5/probes/contract-2026-10-01/swap/pr33285/S1/submission.json","w"), ensure_ascii=False, indent=1)
