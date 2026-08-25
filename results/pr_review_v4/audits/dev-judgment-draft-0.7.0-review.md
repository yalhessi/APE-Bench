# PR Review v4 judgment decomposition review

Release: `0.7.0-judgment-draft`
Presumed atomic: 80
Needs decomposition review: 9

For each item, choose one of: accept as one atomic obligation, split into independently satisfiable obligations, or mark non-evaluable. Supporting proof steps should normally remain inside one obligation.

## pr33310_i01 (PR #33310)

Signals: `explicit_numbered_components`

**Current claim:** Refactor `quotientPEquiv` to avoid constructing the ring isomorphism via tactics and rewriting `Ideal.span {p}` into a kernel: instead, (1) add a lemma `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` (with `ker` on the LHS), (2) add a surjectivity lemma `constantCoeff_surjective`, (3) define `quotientPEquiv` as `(Ideal.quotEquivOfEq ker_constantCoeff.symm).trans (RingHom.quotientKerEquivOfSurjective constantCoeff_surjective)`, and (4) add a simp lemma `quotientPEquiv_mk` stating the map on `Quot.mk` is `constantCoeff`.

**Scope targets:**
- `Mathlib/RingTheory/WittVector/Complete.lean`: `WittVector.quotientPEquiv` (`change:f42043073f4a3d915958eb7ce45cb1fdd4ade22cb0401726dfdc76a51e5ef487`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33296_i01 (PR #33296)

Signals: `additional_independent_clause`

**Current claim:** Replace the lemma `Module.End.exists_apply_eq_smul` (which assumes `hf : f ∈ Subsemiring.center (End R M)`) with a more general “mem_center_iff” characterization for `Set.center (End R M)` and then derive specialized iff-lemmas for `Submonoid.center`, `Subsemigroup.center`, `Subsemiring.center`, and `Subalgebra.center`; additionally, strengthen `Mathlib/Algebra/Central/End.lean`’s imports by adding `Mathlib.Algebra.Central.Basic`.

**Scope targets:**
- `Mathlib/Algebra/Central/End.lean`: `Module.End.exists_apply_eq_smul` (`change:aa1c85317e13692918f1e48f1e4e85533bd2bc848fed4624f6f3fe254a6447c3`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33287_i01 (PR #33287)

Signals: `explicit_numbered_components`

**Current claim:** (1) In the `Arrows.toCompatible` definition, replace the `property` proof body `dsimp; simp only [← FunctorToTypes.map_comp_apply, ← op_comp, h]` with `simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]`. (2) In the lemma/proof about sheafness for presieves in an over-category, state the goal as `IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by` (i.e. explicitly use `Presieve.ofArrows` with the mapped arrows) instead of the current formulation.

**Scope targets:**
- `Mathlib/CategoryTheory/Sites/IsSheafFor.lean`: `CategoryTheory.Presieve.isSheafFor_over_map_op_comp_ofArrows_iff` (`change:a7c9e97e9678021f3e5e4008f99c6ff1d0a7e3803cdc4e126f849eddc7c68fc3`)
- `Mathlib/CategoryTheory/Sites/IsSheafFor.lean`: `CategoryTheory.Presieve.Arrows.toCompatible` (`change:d6170929348d86ff9526ab12d60bb602426c57410502c4a64861685d13f37776`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33208_i01 (PR #33208)

Signals: `additional_independent_clause`

**Current claim:** Change `IsMulIndecomposable_id_univ` to take `{x : M}` as an implicit argument (and correspondingly use `hx : x ≠ 1`), and improve documentation by replacing/expanding the docstring for `Submonoid.closure_image_one_lt_and_isMulIndecomposable` to include a clearer explanatory paragraph of the statement; additionally, add a docstring for the additive `to_additive` version.

**Scope targets:**
- `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: `Submonoid.closure_image_one_lt_and_isMulIndecomposable` (`change:3659dd120059c114a6e27ccdfc44126a1d7753c8a891930c09caf2d4caafc8c9`)
- `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: `IsMulIndecomposable_id_univ` (`change:d5761f45d6d2dbca7deaba4cfcf744018a4ebde9737c842952bb86e717a23ff1`)
- `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: `command` (`change:eaf9f8314cd3b9c0b4dcc28b1943d7c5952f51f1534804368088b321798b947d`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33201_i01 (PR #33201)

Signals: `semicolon_imperative_clause`

**Current claim:** Replace the specialized proofs that `X.HomotopyCategory` has subsingleton homs and is terminal with the standard library route: set up `Unique (OneTruncation₂ X)` and `Subsingleton (x ⟶ y)` in `OneTruncation₂ X` (via `X.Edge`), then obtain `Subsingleton (x ⟶ y)` by `CategoryTheory.Quotient.instSubsingletonHom`; add `Unique X.HomotopyCategory` via `CategoryTheory.Quotient.instUnique`; and define `isTerminal` using `letI : IsDiscrete (X.HomotopyCategory) := { eq_of_hom := by subsingleton }` followed by `Cat.isTerminalOfUniqueOfIsDiscrete` (instead of `IsTerminal.ofUniqueHom` / ad hoc arguments).

**Scope targets:**
- `Mathlib/AlgebraicTopology/SimplicialSet/HomotopyCat.lean`: `SSet.Truncated.HomotopyCategory.subsingleton_hom` (`change:307bf00f4751afc6b482b301583d322f9fc4ced1b86cc1500a5cd44982458bb7`)
- `Mathlib/AlgebraicTopology/SimplicialSet/HomotopyCat.lean`: `SSet.Truncated.HomotopyCategory.isTerminal` (`change:3ea96df78aa26a0f2be4d4d06cc7ccd1651b7b39e45317dfe3370b29b4bb3afd`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33145_i03 (PR #33145)

Signals: `explicit_numbered_components`

**Current claim:** Refactor the dense-set boundedness/supremum/infimum lemmas into dualized `ciSup`/`ciInf` versions by (1) introducing lemmas `Dense.ciSup' {α : Type*} [TopologicalSpace α] ...` and `Dense.ciInf' {α : Type*} [TopologicalSpace α] ...` (rather than separate bespoke sup/inf lemmas), and (2) prove the `ciInf'` statement via order duality by rewriting it as a `ciSup'` on `αᵒᵈ` (e.g. `⨅ i, f i = ⨅ s : S, f s := hS.ciSup' (α := αᵒᵈ) hf`).

**Scope targets:**
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_sup'` (`change:026d50893ce6c7e3d003a7f76523fd7517e5c8524765c393ada02f72dd58eae3`)
- `Mathlib/Topology/Order/IsLUB.lean`: `Dense.continuous_inf'` (`change:d060e494ca7a39fb99bfad4fb43ded7c411b933bbbced7dd98a6bd57965b359a`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33098_i01 (PR #33098)

Signals: `additional_independent_clause`

**Current claim:** Replace the case-split proof of `minimalCover_subset` with a one-liner `grind` proof (`by grind [minimalCover]`), adding `attribute [grind .] finite_empty` (and similarly `IsSeparated.empty` for the analogous maximal-separated-set lemmas) so `grind` can close the related lemmas; additionally adjust lemma headers to introduce an `encard_` prefix for the `minimalCover`/`maximalSeparatedSet` cardinality lemmas (e.g. `encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ...`).

**Scope targets:**
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.maximalSeparatedSet` (`change:0adc9a11d9ba3185dacd4e3ad92e958987fa124b1f9cbbd0ded5be2e6a89b79a`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.minimalCover_subset` (`change:390f4748ccfdedd20b9952b48ba363f7a6aed223eceabdb507c44c21d87d03e1`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.minimalCover` (`change:8238b5e18737441c64bde7be13dc5249a81a502ede839996204734d10b073080`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.card_maximalSeparatedSet` (`change:c5c9da88f1d990a90cb9913c331dedd39539e7c571bf7a0c98dce91de28c648f`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.maximalSeparatedSet_subset` (`change:c7ef58137fa4b7b4ee0f8b13686be4a5afcefe2e8e8c434092e3c25c8510acc0`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.card_minimalCover` (`change:dcb9537a719f49117887583fbaf00dbaec1c34855e0f6f1f5061814e5a699b69`)
- `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`: `Metric.card_le_of_isSeparated` (`change:f36711f88985da8ca9fdecb17a4bbca6b2ce641c8a72161c6dd4d4495209c825`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33078_i01 (PR #33078)

Signals: `explicit_numbered_components`

**Current claim:** Replace the direct simp/prod-of-roots proof that constructs `NeZero (n : ℂ)` with a proof that (1) introduces `have : NeZero n := ⟨hn⟩`, (2) reduces Mahler measure to the product over `primitiveRoots n ℂ` of `max 1 ‖x‖`, and (3) shows this product is `1` by proving `∀ x ∈ primitiveRoots n ℂ, ‖x‖ ≤ 1` and applying `Multiset.prod_eq_one` (using `IsPrimitiveRoot.norm'_eq_one ... hn`).

**Scope targets:**
- `Mathlib/NumberTheory/MahlerMeasure.lean`: `Polynomial.cyclotomic_mahlerMeasure_eq_one` (`change:2dfdb214f28fd7c7f787b1ec4df7b77f6c2ccf668a5192de6d10730bfbc3e21b`)

**Decision:** pending

**Proposed obligations/corrections:**
- 

## pr33067_i01 (PR #33067)

Signals: `additional_independent_clause`

**Current claim:** Reconsider marking the `recall` identifier as a binder: avoid setting `(isBinder := true)` for `recall`’s syntax info unless that syntax actually generates a declaration in the environment, and additionally apply the same info-reporting fix to the `alias_in` command as well.

**Scope targets:**
- `Mathlib/Tactic/Recall.lean`: `command` (`change:c16d184071d368126cedb4680a0b8b24168f4f2f640567e8d09395f59c213d5c`)

**Decision:** pending

**Proposed obligations/corrections:**
-
