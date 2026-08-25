# PR Review v4 curation digest

Release: `inputs/pr_review_v4/releases/dev-medium-0.1.0`
PRs: 33145, 33149, 33285, 33294, 33321, 33337, 33362
Judgments: 19

Per item choose one of: confirm_atomic (one obligation, as stated) | split (list independently satisfiable obligations) | not_judgeable (exclude with reason) | revise (correct claim/scope).
Supporting proof steps normally stay inside one obligation; split only when parts are independently satisfiable.

## pr33145_i01 (PR #33145)

Status: `migration_proposal` / `presumed_atomic`
Concerns: duplication | speech act: request | blocking: advisory
Outcome: partially_adopted — The author adopted the renames: `Dense.continuous_upperBounds`/`Dense.continuous_lowerBounds` disappear post-revision while `Dense.upperBounds_image`/`Dense.lowerBounds_image` appear, but there is no evidence the lower-bounds lemma was reproved by dualizing via `OrderDual` (and `OrderDual` does not appear post-revision).

**Action:** kind='rename' object='Dense.continuous_upperBounds'

**Obligations:**
- (proposed_atomic) Rename the lemmas `Dense.continuous_upperBounds` and `Dense.continuous_lowerBounds` to `Dense.upperBounds_image` and `Dense.lowerBounds_image`, and reprove the lower-bounds lemma by dualizing the upper-bounds lemma via `OrderDual` (i.e. `lowerBounds (f '' S) = lowerBounds (range f) := hS.continuous_upperBounds (α := αᵒᵈ) hf`).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_upperBounds`
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_lowerBounds`

**Decision:** pending

## pr33145_i02 (PR #33145)

Status: `migration_proposal` / `presumed_atomic`
Concerns: duplication | speech act: request | blocking: advisory
Outcome: adopted — Although the anchor code wasn’t revised, later revision hunks add the requested lemmas `Dense.ciSup` and `Dense.ciInf` (and primed variants), matching the intervention’s refactor/duality request as shown by the identifier evidence: both `Dense.ciSup` and `Dense.ciInf` appear on the post-revision side.

**Action:** kind='refactor' object='Dense.ciSup'

**Obligations:**
- (proposed_atomic) Refactor the new dense-set supremum/infimum results into lemmas named `Dense.ciSup` and `Dense.ciInf` (with signature starting `theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ...`), and obtain the infimum statement by reusing the supremum lemma via order duality (e.g. prove `⨅ i, f i = ⨅ s : S, f s` by `hS.ciSup (α := αᵒᵈ) hf h`) rather than duplicating a separate lower-bounds argument.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_sup`
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_inf`

**Decision:** pending

## pr33145_i03 (PR #33145)

Status: `curator_confirmed` / `reviewed_decomposed` — signals: `explicit_numbered_components`
Concerns: duplication | speech act: request | blocking: advisory
Outcome: adopted — Although the original `Dense.continuous_upperBounds` anchor code was not revised, the post-revision code elsewhere adds the requested dualized lemmas `Dense.ciSup'` and `Dense.ciInf'`, and `Dense.ciInf'` is proved via order duality using `hS.ciSup' (α := αᵒᵈ) hf`, matching the maintainer’s intervention.

**Action:** kind='refactor' object='ciSup'

**Obligations:**
- (proposed_atomic) Generalize the dense-set supremum result into a `Dense.ciSup'` lemma with the requested typeclass-polymorphic statement.
  - resolution: The bespoke continuous supremum result is replaced or subsumed by a `Dense.ciSup'` lemma with the requested generality.
- (proposed_atomic) Provide the corresponding `Dense.ciInf'` lemma and prove it by applying `ciSup'` in the order dual.
  - resolution: A `Dense.ciInf'` result is present and its proof is reduced to `ciSup'` over `OrderDual` rather than duplicating the supremum argument.

**Scope targets:**
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_sup'`
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_inf'`

**Decision:** pending

## pr33145_i04 (PR #33145)

Status: `migration_proposal` / `presumed_atomic`
Concerns: style | speech act: request | blocking: advisory
Outcome: adopted — Post-revision code introduces the requested `by_cases h : BddAbove (range (fun x : S ↦ f x))` split, uses `h.closure.mono` in the bounded branch, and adds the unbounded-branch finish via `simp [ciSup_of_not_bddAbove, ...]` with a `suffices ¬ BddAbove (range f)` step, matching the intervention’s plan.

**Action:** kind='refactor' object='ciSup'

**Obligations:**
- (proposed_atomic) Refactor the `ciSup`/supremum proof to begin with a `by_cases` split on `BddAbove (range (fun x : S ↦ f x))`, using the bounded-above branch to apply the dense-set `ciSup` lemma via `h.closure.mono` and `hf.range_subset_closure_image_dense hS`, and using the unbounded branch to derive `¬ BddAbove (range f)` (by contraposition and monotonicity) and finish by simp with `ciSup_of_not_bddAbove`.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_sup'`

**Decision:** pending

## pr33145_i05 (PR #33145) ⚠ FLAGGED

Status: `migration_proposal` / `unresolved_scope`
Concerns: style | speech act: request | blocking: advisory
Outcome: dropped — At the anchor sites the reviewed equalities remain oriented as `⨆ i, f i = ⨆ s : S, f s` / `⨅ i, f i = ⨅ s : S, f s`, and the subsequent revision is explicitly reported as having no changes there; the elsewhere changes shown are only lemma renames (e.g. `continuous_upperBounds`→`upperBounds_image`) and do not provide any evidence that the iSup/iInf equality sides were swapped.

**Action:** kind='change' object='iSup'

**Obligations:**
- (not_evaluable) Swap the sides of the `iSup`/`iInf` equalities so they are stated with the dense-set supremum/infimum on the left and the universe/index supremum/infimum on the right, e.g. change `⨆ i, f i = ⨆ s : S, f s` to `⨆ s : S, f s = ⨆ i, f i` (and similarly for `iInf`).
  - resolution: None

**Scope targets:**
- None

**Decision:** pending

## pr33149_i01 (PR #33149)

Status: `migration_proposal` / `presumed_atomic`
Concerns: correctness | speech act: request | blocking: blocking
Outcome: unknown — Although the reviewed code clearly introduces multiple `axiom` declarations (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`), the provided identifier search reports `axiom` appears on neither the reviewed nor post-revision side, so the evidence is internally inconsistent and insufficient to determine whether the axioms were removed or not.

**Action:** kind='remove' object='axiom'

**Obligations:**
- (proposed_atomic) Remove the newly introduced `axiom` declarations (and any reliance on them), replacing them with proved lemmas or existing Mathlib results so the file adds no new axioms.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall`

**Decision:** pending

## pr33149_i02 (PR #33149)

Status: `migration_proposal` / `presumed_atomic`
Concerns: duplication | speech act: request | blocking: blocking
Outcome: dropped — No subsequent revision was made at the intervention’s anchor sites or elsewhere in the PR (explicitly: “the author did not revise this code after review” and “Revisions ELSEWHERE… (none)”), so no replacement of custom Parseval-type identities with Mathlib lemmas occurred; the review thread is also unresolved (False).

**Action:** kind='replace' object="Replace any custom/axiomatized Parseval-type identity used in the PR with the existing Parseval's identity lemma(s) from Mathlib; if a specialized version (e.g. for the standard ba"

**Obligations:**
- (proposed_atomic) Replace any custom/axiomatized Parseval-type identity used in the PR with the existing Parseval's identity lemma(s) from Mathlib; if a specialized version (e.g. for the standard basis in ℝⁿ) is genuinely needed, add that specialization in the appropriate existing Mathlib location instead of duplicating it in this new file.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval3D`

**Decision:** pending

## pr33149_i03 (PR #33149)

Status: `migration_proposal` / `presumed_atomic`
Concerns: correctness | speech act: request | blocking: blocking
Outcome: dropped — No post-review revision was made at the anchor sites or elsewhere (explicitly noted as none), so the newly introduced axioms (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`) were not removed or replaced with definitions/lemmas proven from mathlib.

**Action:** kind='remove' object='cMoser'

**Obligations:**
- (proposed_atomic) Remove the newly introduced axioms (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`, etc.) and replace them with actual definitions/lemmas proved from existing mathlib results; when introducing new definitions/structures, also add basic supporting lemmas so the additions are maintainable.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall`

**Decision:** pending

## pr33149_i04 (PR #33149) ⚠ FLAGGED

Status: `migration_proposal` / `not_judgeable` — signals: `explicit_numbered_components`
Concerns: correctness | speech act: suggestion | blocking: blocking
Outcome: dropped — The author made no subsequent revision at the intervention’s anchor sites or elsewhere in the PR (explicitly stated), so none of the requested changes (eliminating `axiom`s, removing wrapper defs/using `abbrev`, and fixing vacuous definitions like `fourierDecay`/`spectralNSResidual`/`SolvesNavierStokes`) were implemented.

**Action:** kind='rewrite' object='axiom'

**Obligations:**
- (not_evaluable) Rewrite the file to meet mathlib standards by (1) eliminating all `axiom`s (replace with actual definitions/lemmas derived from Mathlib, or mark gaps with `sorry` during development), (2) removing/ inlining local wrapper definitions that merely rename existing Mathlib notions (optionally keep as `abbrev` only if truly needed), and (3) fixing definitions like `fourierDecay` and `spectralNSResidual` (and anything depending on them such as `SolvesNavierStokes`) so they are not vacuously true.
  - resolution: None

**Scope targets:**
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `bkm_implies_regularity`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierDecay`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `SolvesNavierStokes`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_ortho_integral`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_hs_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cSobolev`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourierCoeff_summable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `hs_gronwall_bound`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `smooth_initial_hs_finite`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cMoser_pos`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fubini_torus3`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `spectralNSResidual`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `moser_estimate`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `parseval_orthonormal`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `sobolev_embedding`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `integral_le_const_mul_length`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `vorticity_integrable`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `fourier_inversion`
- `Mathlib/Analysis/ODE/GalerkinRegularity.lean`: `cGronwall`

**Decision:** pending

## pr33285_i01 (PR #33285)

Status: `migration_proposal` / `presumed_atomic`
Concerns: proof-golf | speech act: request | blocking: advisory
Outcome: partially_adopted — At the anchor site the author switched from `rw/intros/change/apply` to a direct `fun _ h ↦ ...` lambda (`exact fun _ h ↦ add_mem h.1 h.2`), but they kept a `simp only [...]` prelude instead of fully replacing the proof with `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2` as requested (and similarly used `simp only ...; exact fun _ h ↦ smul_mem ...` in the new lemma elsewhere).

**Action:** kind='replace' object='comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q'

**Obligations:**
- (proposed_atomic) Golf the proof of `comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q` to a direct lambda, i.e. replace the tactic-style `rw/intros/change/apply` (or `simp`-tactic block) with `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2`.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Algebra/Module/Submodule/Map.lean`: `Submodule.inf_comap_le_comap_add`

**Decision:** pending

## pr33285_i02 (PR #33285)

Status: `migration_proposal` / `presumed_atomic`
Concerns: proof-golf | speech act: request | blocking: advisory
Outcome: adopted — At `cotangentEquivIdeal_symm_apply`, the revision replaces the manual `injective`/`rw`/`ext`/`rfl` tail with a single `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]`, matching the maintainer’s suggested simp-based proof at the anchor site.

**Action:** kind='replace' object='cotangentEquivIdeal_symm_apply'

**Obligations:**
- (proposed_atomic) In `cotangentEquivIdeal_symm_apply`, replace the manual injectivity/`ext`/`rfl` proof tail with a single `simp`-based proof, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (alternatively using `exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)`).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/RingTheory/Ideal/Cotangent.lean`: `Ideal.cotangentEquivIdeal_symm_apply`

**Decision:** pending

## pr33294_i01 (PR #33294)

Status: `migration_proposal` / `presumed_atomic`
Concerns: naming | speech act: request | blocking: advisory
Outcome: adopted — At the anchor the lemma was renamed from `isFundamentalSequence_of_isNormal` to dot-notation as `theorem IsFundamentalSequence.of_isNormal ...`, and subsequent uses/alias were updated to refer to `IsFundamentalSequence.of_isNormal`, with the old name disappearing post-revision.

**Action:** kind='rename' object='isFundamentalSequence_of_isNormal'

**Obligations:**
- (proposed_atomic) Rename the theorem `isFundamentalSequence_of_isNormal` to use dot-notation as `isFundamentalSequence.of_isNormal` (i.e. make it an `IsFundamentalSequence.of_isNormal` theorem rather than a standalone `*_of_*` name).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/SetTheory/Cardinal/Cofinality.lean`: `Ordinal.isFundamentalSequence_of_isNormal`

**Decision:** pending

## pr33294_i02 (PR #33294)

Status: `migration_proposal` / `presumed_atomic`
Concerns: style | speech act: request | blocking: advisory
Outcome: adopted — At the intervention anchor in Mathlib/SetTheory/Ordinal/Topology.lean:178, the reviewed rewrite `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` was changed in the subsequent revision to the method-call form `rw [h.map_iSup (bddAbove_of_small _)]`, matching the maintainer’s requested replacement.

**Action:** kind='replace' object='rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]'

**Obligations:**
- (proposed_atomic) Replace the rewrite `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with the method call `rw [h.map_iSup (bddAbove_of_small _)]`.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/SetTheory/Ordinal/Topology.lean`: `Ordinal.enumOrd_isNormal_iff_isClosed`

**Decision:** pending

## pr33321_i01 (PR #33321)

Status: `migration_proposal` / `presumed_atomic`
Concerns: docs | speech act: request | blocking: advisory
Outcome: adopted — At the anchor site, the `IsMulIndecomposable.baseOf` docstring was revised to fix the typo (“crystallogrphic” → “crystallographic”) and the previously unfinished sentence is completed as “this is the base of the root system associated to `f`.”

**Action:** kind='fix' object='IsMulIndecomposable.baseOf'

**Obligations:**
- (proposed_atomic) Complete/fix the docstring for `IsMulIndecomposable.baseOf` so that the sentence “In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the …” is finished (and correct any typo such as “crystallogrphic”).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: `IsMulIndecomposable.baseOf`

**Decision:** pending

## pr33321_i02 (PR #33321)

Status: `migration_proposal` / `presumed_atomic`
Concerns: style | speech act: question | blocking: advisory
Outcome: dropped — At the anchor for `IsMulIndecomposable.baseOf`, the post-revision definition still appears as `def IsMulIndecomposable.baseOf ... : Set ι :=` (per the full-text identifier evidence) with no sign of being rewritten into a set comprehension `{j | IsMulIndecomposable v {i | 1 < f (v i)} j}`; no alternative adoption of that comprehension shows up in the other revision hunks either.

**Action:** kind='other' object='IsMulIndecomposable.baseOf'

**Obligations:**
- (proposed_atomic) Redefine `IsMulIndecomposable.baseOf` as a set comprehension `{j | IsMulIndecomposable v {i | 1 < f (v i)} j}` rather than using the predicate `IsMulIndecomposable v {i | 1 < f (v i)}` directly as a `Set ι` via definitional equality between predicates and sets.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: `IsMulIndecomposable.baseOf`

**Decision:** pending

## pr33321_i03 (PR #33321)

Status: `migration_proposal` / `presumed_atomic`
Concerns: docs | speech act: request | blocking: advisory
Outcome: dropped — At the intervention’s anchor site, the module-level documentation text is unchanged except for a minor wording tweak (“existence ultimate” → “ultimate existence”), and no other revision hunk shows an added or expanded “Implementation details” discussion specifically addressing ordered coefficients.

**Action:** kind='other' object='Revise the module-level documentation to explicitly account for the need for an ordered coefficient set in the proof (despite the final existence statement not needing it), by addi'

**Obligations:**
- (proposed_atomic) Revise the module-level documentation to explicitly account for the need for an ordered coefficient set in the proof (despite the final existence statement not needing it), by adding an “Implementation details” discussion outlining the approach taken to handle ordered coefficients.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`: `module_doc`

**Decision:** pending

## pr33337_i01 (PR #33337)

Status: `migration_proposal` / `presumed_atomic`
Concerns: naming | speech act: request | blocking: advisory
Outcome: adopted — At the anchor site the lemma was renamed from `orthogonalProjection_coe_eq_linearProjOfIsCompl` (reviewed) to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` (post-revision), matching the requested `toLinearMap_...` naming convention.

**Action:** kind='rename' object='orthogonalProjection_coe_eq_linearProjOfIsCompl'

**Obligations:**
- (proposed_atomic) Rename the lemma `orthogonalProjection_coe_eq_linearProjOfIsCompl` to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` (using the `toLinearMap_...` naming convention for equalities about the `E →ₗ[𝕜] K` coercion of `K.orthogonalProjection`).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`

**Decision:** pending

## pr33337_i02 (PR #33337)

Status: `migration_proposal` / `presumed_atomic`
Concerns: naming | speech act: request | blocking: advisory
Outcome: adopted — At the anchor, `coe_orthogonalProjection_eq_linearProjOfIsCompl` was renamed to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`, and elsewhere `coe_starProjection_eq_isComplProjection` was replaced by `toLinearMap_starProjection_eq_isComplProjection` (with the old identifiers disappearing and the new `toLinearMap_...` ones appearing only post-revision).

**Action:** kind='rename' object='coe_starProjection_eq_isComplProjection'

**Obligations:**
- (proposed_atomic) Rename the lemma `coe_starProjection_eq_isComplProjection` (and similarly `coe_orthogonalProjection_eq_linearProjOfIsCompl`) to use the `toLinearMap_...` prefix, i.e. change it to `toLinearMap_starProjection_eq_isComplProjection` (and `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`) to reflect that the statement is about `.toLinearMap`.
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`: `Submodule.coe_starProjection_eq_isComplProjection`
- `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`

**Decision:** pending

## pr33362_i01 (PR #33362)

Status: `migration_proposal` / `presumed_atomic`
Concerns: scope | speech act: request | blocking: advisory
Outcome: adopted — In the subsequent revision, `namespace Complex` is moved to after the `variable` block and before `theorem schwarz_aux`, so the lemmas now live inside the `Complex` namespace at the anchor site.

**Action:** kind='move' object='namespace Complex'

**Obligations:**
- (proposed_atomic) Move the relevant declarations a few lines down so they are inside the `namespace Complex` (i.e. put `namespace Complex` before the lemmas so they live in the `Complex` namespace).
  - resolution: The requested transformation is satisfied at every required target, and any superseded form named by the request is no longer used there.

**Scope targets:**
- `Mathlib/Analysis/Complex/Schwarz.lean`: `Complex.schwarz_aux`

**Decision:** pending
