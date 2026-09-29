# Review notes: PR #33066 (reviewer X2)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. Every tool call went through `./ptool`.
The workspace files are under `target/`. Scratch files are in `tmp/`. Each `lean_verify_edit`
compile of `ContinuousAlgEquiv.lean` took about 25 s. The file as the PR leaves it compiles
cleanly: no errors, no warnings.

## Mathlib/Topology/Algebra/Algebra/Equiv.lean

- `ContinuousAlgEquiv.ofAlgEquiv`: the name matches `StarAlgEquiv.ofAlgEquiv`. A Zulip thread
  (Aaron Liu) prefers the `X.ofY` shape over `Y.toX`. There is no existing constructor for this;
  the nearest analogue is `LinearEquiv.toContinuousLinearEquivOfContinuous` in Banach.lean.
  **Finding:** `_root_.AlgEquiv.isUniformEmbedding`, just above it, builds the same structure
  inline. I moved `ofAlgEquiv` up, reused it there, and it compiled.
- `coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`,
  `ofAlgEquiv_trans_ofAlgEquiv`: all `rfl`, the simp directions are sensible, and they follow
  sibling conventions. `naming_norm` gave insufficient_evidence for them. The untyped `(he he')`
  binders follow `equivOfInverse_apply`. Nothing to request.

## Mathlib/Analysis/InnerProductSpace/Adjoint.lean

- `LinearIsometryEquiv.conjStarAlgEquiv` and `_apply_apply`, `symm_..._apply_apply`, `_apply`,
  `symm_conjStarAlgEquiv`, `_refl`, `_trans` mirror the `ContinuousLinearEquiv.conjContinuousAlgEquiv`
  API in StrongTopology.lean:807-829 one-for-one, including which lemmas are simp. Nothing to
  request on the API shape or naming. The `CompleteSpace` assumptions are needed for the star
  structure.
  **Finding (docs):** "isometry linear equivalence" is non-standard wording that appears only in
  this PR.
- `conjStarAlgEquiv_trans`. **Finding:** it rebinds `{G : Type*} [NormedAddCommGroup G]
  [InnerProductSpace 𝕜 G]`, shadowing the file-level variable. A version with only
  `[CompleteSpace G]` compiled.
- `section linearIsometryEquiv` restructure: it only scopes `K` across both namespaces. Fine.
- I considered asking for a compatibility lemma with `Unitary.conjStarAlgAut` when `H = K`, but
  did not submit it: it is speculative, and Adjoint.lean does not import that file.

## Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean

- Module docstring. **Finding:** `### TODO:` should be `## TODO` (599 files use `## TODO`, 3 use
  `###`). The title line is 99 characters, within the limit. No added line exceeds 100
  characters.
- Imports / file placement. **Finding (scope):** the Hilbert-space half pulls
  `InnerProductSpace.Adjoint`/`Positive` into a `Normed/Operator` file whose original theorem
  needs none of them. Nothing but `Mathlib.lean` imports the file, so a split is free. I also
  checked `Pow.Real`: it is available transitively (the original proof compiles with that import
  line deleted). It is used only by the rpow scalar, which the sqrt finding removes.
- `auxContinuousLinearEquiv`. **Finding:** it re-derives `ContinuousLinearEquiv.equivOfInverse'`.
  The replacement compiled, and all dependants still compile.
- `coe_auxContinuousLinearEquiv`, `auxIsometry`, `coe_auxIsometry`, `coe_symm_auxIsometry`: these
  are non-public (private under the module system), as the PR description says. The `norm_map'`
  proof via `norm_map_iff_adjoint_comp_self` is reasonable. `grind` for `α' ≠ 0` is fine. The
  `auxIsometry` docstring wording is covered by the docs finding. I considered replacing the aux
  layer with `ContinuousLinearEquiv.smulLeft`, but did not pursue it. The author says the aux
  defs keep the main proof fast.
- `StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv`: the PR description invites golfing. I
  checked three independent golfs, each compiled on its own in declaration mode, and all three
  compiled together with the `Pow.Real` import removed (line mode):
  1. realness/positivity via `RCLike.pos_iff_exists_ofReal` plus `obtain ⟨r, hr, rfl⟩`. This
     removes the `thisα`/`this10`/`this1`/`replace this2` detour.
  2. `Real.sqrt` instead of `rpow (-(1/2))`. This matches the comment `1/√(re α)`, and `la`
     becomes one line.
  3. central scalar via `Algebra.IsCentral.mem_center_iff`, replacing `center_eq_bot` plus the
     `Algebra.ofId` cleanup simp.
  Combined, the proof shrinks from 70 to 59 lines. A first attempt at step 1 hit a whnf
  heartbeat timeout (`rw ... at this; exact this`). A type ascription on the
  `hα ▸ isPositive_adjoint_comp_self` term fixed it.
  Style findings: hypothesis naming (`this` rebound repeatedly, `this10`, and so on) and a double
  space in a `simp_rw` list. Docs finding: the proof-sketch comment names `y.conjAlgEquiv` (should
  be `conjContinuousAlgEquiv`) and has the typo "endormorphisms".
  `hf : Continuous f` is already covered by the author's TODO. I found no generalisation to
  request: completeness is needed for the adjoint and for Banach.
- The `OrderIsoClass` instance: priority 100 matches `StarRingEquivClass.instOrderIsoClass`,
  and the TODO is accurate. For `𝕜 = ℂ`, `StarOrderedRing (H →L[ℂ] H)` already exists
  (StarOrder.lean), but `OrderIsoClass` is a `Prop` class, so the overlap creates no diamond.
  Nothing to request.

## Mathlib/LinearAlgebra/GeneralLinearGroup/AlgEquiv.lean

- The one-line cross-reference added to the module doc is fine.

## Tools used

`file_read`, `file_search`, `content_search`, `declaration_search`, `naming_norm` (all
insufficient_evidence), `precedent_search` (nothing applicable), `zulip_search` (only the
`ofAddEquiv` naming context), and `lean_verify_edit` (baseline plus 12 edit checks).

Findings written: 12, all advisory.
