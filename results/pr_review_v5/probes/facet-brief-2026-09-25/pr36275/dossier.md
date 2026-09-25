# Dossier for PR #36275 (built deterministically from the diff; no review text)

Each changed object, with what changed, and the cells to check for its object kind (see the procedure).

## theorem: `NumberField.FiniteAdeleRing.norm_def` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem norm_def (x : 𝔸ᶠ[K]) : ‖x‖ = ∏' v, ‖x.1 v‖`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.tprod_norm_of_unit`

## theorem: `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem unitEmbedding_norm_eq_inv_abs_norm (x : Kˣ) : ‖(unitEmbedding (𝓞 K) K x).1‖ = |Algebra.norm ℚ x.1|⁻¹`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.tprod_norm_of_unit`

## section in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## theorem: `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem unitEmbedding_norm_apply_eq_finprod_finitePlace (x : Kˣ) : ‖(unitEmbedding (𝓞 K) K x).1‖ = ∏ᶠ v : FinitePlace K, v x`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.tprod_norm_of_unit`

## theorem: `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem tprod_norm_of_isUnit {x : 𝔸ᶠ[K]} (hx : IsUnit x) : ∏' v, ‖x.1 v‖ = ∏ᶠ v, ‖x.1 v‖`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`

## attribute in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: unknown:added

## section in `Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## theorem: `NumberField.FinitePlace.two_le_norm_of_one_lt_norm` (lemma, added)
- file: `Mathlib/NumberTheory/NumberField/Completion/FinitePlace.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `lemma FinitePlace.two_le_norm_of_one_lt_norm {v : HeightOneSpectrum R} (x : v.adicCompletion K) (h : 1 < ‖x‖) : 2 ≤ ‖x‖`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one`, `NumberField.HeightOneSpectrum.two_le_absNorm_nnreal`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`

## theorem: `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem tprod_eq_zero_of_not_isUnit {x : 𝔸ᶠ[K]} (hx : ¬ IsUnit x) : ∏' v, ‖x.1 v‖ = 0`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.tprod_norm_of_unit`

## theorem: `IsDedekindDomain.FiniteAdeleRing.cofinite_mem_adicCompletionIntegers` (lemma, added)
- file: `Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `lemma cofinite_mem_adicCompletionIntegers (a : FiniteAdeleRing R K) : ∀ᶠ v in Filter.cofinite, a v ∈ v.adicCompletionIntegers K`
- siblings in this PR sharing a name token: none

## import in `Mathlib/NumberTheory/NumberField/Completion/FinitePlace.lean` (modified)
- changed: imports:modified

## module_doc in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: documentation:added

## section in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## import in `Mathlib.lean` (modified)
- changed: imports:added

## theorem: `Valued.toNormedField.norm_eq_one_iff` (theorem, added)
- file: `Mathlib/Topology/Algebra/Valued/NormedValued.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem norm_eq_one_iff : ‖x‖ = 1 ↔ val.v x = 1`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`

## section in `Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## command in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: value_or_body:added

## theorem: `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `private theorem hasProd_subset_valued_lt_one (x : 𝔸ᶠ[K]) : HasProd (fun v : {v | 1 < Valued.v (x v)} ↦ ‖x v‖) (∏ᶠ v : {v | 1 < Valued.v (x v)}, ‖x v‖)`
- siblings in this PR sharing a name token: `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`, `IsDedekindDomain.FiniteAdeleRing.finite_valued_one_lt`

## command in `Mathlib/NumberTheory/NumberField/AdeleRing.lean` (removed)
- changed: value_or_body:removed

## instance: `None` (instance, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: attributes:added, statement_or_type:added, value_or_body:added
- header: `noncomputable instance : Norm 𝔸ᶠ[K] where norm x`
- siblings in this PR sharing a name token: none

## theorem: `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem hasProd_zero_of_not_isUnit {x : 𝔸ᶠ[K]} (hx : ¬IsUnit x) : HasProd (fun v ↦ ‖x v‖) 0`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## section in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## theorem: `NumberField.FiniteAdeleRing.mulSupport_finite` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem mulSupport_finite (x : 𝔸ᶠ[K]ˣ) : (Function.mulSupport fun v ↦ ‖x.1 v‖).Finite`
- siblings in this PR sharing a name token: `IsDedekindDomain.FiniteAdeleRing.finite_valued_one_lt`

## doc_comment in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: documentation:added

## theorem: `NumberField.HeightOneSpectrum.two_le_absNorm_nnreal` (lemma, added)
- file: `Mathlib/NumberTheory/NumberField/Completion/FinitePlace.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `lemma two_le_absNorm_nnreal : 2 ≤ (absNorm v.asIdeal : ℝ≥0)`
- siblings in this PR sharing a name token: `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`

## theorem: `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `private theorem hasProd_zero_subset_one_lt_valued {x : 𝔸ᶠ[K]} (hx : ¬IsUnit x) (hx₀ : ∀ v, x v ≠ 0) : HasProd (fun v : {v | Valued.v (x v) < 1} ↦ ‖x v‖) 0`
- siblings in this PR sharing a name token: `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one`, `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit`, `IsDedekindDomain.FiniteAdeleRing.finite_valued_one_lt`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## theorem: `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem unitEmbedding_norm_apply (x : Kˣ) : ‖(unitEmbedding (𝓞 K) K x).1‖ = ∏ᶠ v, FinitePlace.mk v x.1`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`, `NumberField.FiniteAdeleRing.tprod_norm_of_unit`

## namespace in `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean` (added)
- changed: namespace:added

## doc_comment in `Mathlib/NumberTheory/NumberField/AdeleRing.lean` (removed)
- changed: documentation:removed

## theorem: `IsDedekindDomain.FiniteAdeleRing.finite_valued_one_lt` (theorem, added)
- file: `Mathlib/RingTheory/DedekindDomain/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem finite_valued_one_lt (a : FiniteAdeleRing R K) : {v | 1 < Valued.v (a v)}.Finite`
- siblings in this PR sharing a name token: `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_subset_valued_lt_one`, `NumberField.FiniteAdeleRing.mulSupport_finite`, `NumberField.FiniteAdeleRing.hasProd_zero_subset_one_lt_valued`

## theorem: `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem norm_eq_zero_of_not_isUnit {x : 𝔸ᶠ[K]} (hx : ¬IsUnit x) : ‖x‖ = 0`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.hasProd_zero_of_not_isUnit`

## theorem: `NumberField.FiniteAdeleRing.tprod_norm_of_unit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem tprod_norm_of_unit (x : 𝔸ᶠ[K]ˣ) : ∏' v, ‖x.1 v‖ = ∏ᶠ v, ‖x.1 v‖`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `NumberField.FiniteAdeleRing.tprod_eq_zero_of_not_isUnit`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`

## theorem: `NumberField.FiniteAdeleRing.norm_def_unit` (theorem, added)
- file: `Mathlib/NumberTheory/NumberField/FiniteAdeleRing.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem norm_def_unit (x : 𝔸ᶠ[K]ˣ) : ‖x.1‖ = ∏ᶠ v, ‖x.1 v‖`
- siblings in this PR sharing a name token: `NumberField.FiniteAdeleRing.norm_def`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_eq_inv_abs_norm`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply_eq_finprod_finitePlace`, `NumberField.FiniteAdeleRing.tprod_norm_of_isUnit`, `NumberField.FinitePlace.two_le_norm_of_one_lt_norm`, `Valued.toNormedField.norm_eq_one_iff`, `NumberField.FiniteAdeleRing.unitEmbedding_norm_apply`, `NumberField.FiniteAdeleRing.norm_eq_zero_of_not_isUnit`

## Removed declarations
none
