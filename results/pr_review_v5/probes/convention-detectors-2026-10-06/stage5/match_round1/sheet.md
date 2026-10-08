# Stage 5, round1: blind sheet


## PR 28484 (stratum A)

**TARGET v0644** `Mathlib/Data/List/Nodup.lean`
```
-  · exact count_eq_one_of_mem d h
-  · exact count_eq_zero_of_not_mem h
+    count a l = if a ∈ l then 1 else 0 :=
+  Nodup.count d
```
> If you're golfing, I'd suggest:
```suggestion
  d.count
```

- fact 0 [Where dot notation may apply]: `Mathlib/Data/List/Nodup.lean:160` (List.count_eq_of_nodup): `Nodup.count d` applies a `Nodup` lemma to `d : Nodup …`; it can be written `d.count`.

### R1

- [0] `Mathlib/Data/ENNReal/Real.lean:346` (blocking): `ENNReal.toReal_eq_toReal` is now just the old spelling of the existing `ENNReal.toReal_eq_toReal_iff'`, but it is left as a non-deprecated public theorem; this does not actually deprecate the old API name.
  -> Add a deprecation attribute pointing to the replacement, e.g. `@[deprecated ENNReal.toReal_eq_toReal_iff' (since := "2026-10-07")]` immediately before `theorem toReal_eq_toReal`, and update any in-tree uses of the old name if the deprecation warning is triggered.
- [1] `Mathlib/Data/List/Nodup.lean:158` (blocking): `List.count_eq_of_nodup` is now only a wrapper around the canonical `List.Nodup.count`, but the old wrapper remains non-deprecated, so the PR leaves the duplicate API in place instead of deprecating it.
  -> Add a deprecation attribute pointing to the replacement, e.g. `@[deprecated List.Nodup.count (since := "2026-10-07")]` immediately before `theorem count_eq_of_nodup`, and update any in-tree uses of the old name if the deprecation warning is triggered.
- [2] `Mathlib/LinearAlgebra/Matrix/Notation.lean:376` (blocking): `Matrix.smul_mat_cons` is now just the matrix-specialized old spelling of the more general `Matrix.smul_cons`, but it is still exposed as a non-deprecated theorem; this misses the intended deprecation of the obsolete name.
  -> Add a deprecation attribute pointing to the replacement, e.g. `@[deprecated Matrix.smul_cons (since := "2026-10-07")]` immediately before `theorem smul_mat_cons`, and update any in-tree uses of the old name if the deprecation warning is triggered.

### R2

- [0] `Mathlib/Data/ENNReal/Real.lean:346` (blocking): `ENNReal.toReal_eq_toReal` is left as an ordinary theorem even though this PR is replacing it by the existing canonical theorem `ENNReal.toReal_eq_toReal_iff'`; users of the old name will not get a deprecation warning.
  -> Mark `ENNReal.toReal_eq_toReal` deprecated in favor of `toReal_eq_toReal_iff'` (using the PR's deprecation date), and update any in-library uses of the old name.
- [1] `Mathlib/Data/List/Nodup.lean:158` (blocking): `List.count_eq_of_nodup` is left as an ordinary theorem even though it is now only a wrapper around the canonical `List.Nodup.count`; users of the old name will not get a deprecation warning.
  -> Mark `List.count_eq_of_nodup` deprecated in favor of `Nodup.count`/`List.Nodup.count` (using the PR's deprecation date), and update any in-library uses of the old name.
- [2] `Mathlib/LinearAlgebra/Matrix/Notation.lean:376` (blocking): `Matrix.smul_mat_cons` is left as an ordinary theorem even though it is now only a less-general wrapper around the existing `Matrix.smul_cons`; users of the old name will not get a deprecation warning.
  -> Mark `Matrix.smul_mat_cons` deprecated in favor of `smul_cons` (using the PR's deprecation date), and update any in-library uses of the old name.

## PR 30645 (stratum A)

**TARGET v1057** `Mathlib/RingTheory/Localization/FractionRing.lean`
```
+  obtain ⟨c, hc⟩ := h.exists_of_eq (x := 0) (y := 1) (Subsingleton.elim _ _)
+  simp [eq_comm] at hc
+
+theorem nontrivial' [Nontrivial S] : Nontrivial R := by
```
> Not sure about better names, but I don't know how I'd keep straight in my mind which one the primed/unprimed one is.

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/RingTheory/Localization/FractionRing.lean:500` (IsFractionRing.nontrivial'): `nontrivial'` is new, and `nontrivial` is declared at `Mathlib/RingTheory/Localization/FractionRing.lean:494`. `nontrivial'` concludes `Nontrivial R`; `nontrivial` concludes `Nontrivial S`.

### R1

- [0] `Mathlib/RingTheory/Localization/FractionRing.lean:494` (advisory): `IsFractionRing.nontrivial` manually unfolds the localization equality criterion to prove nontriviality, but `LocalizationMap.nontrivial` is the canonical API for exactly this argument when the localized submonoid does not contain zero.
  -> Replace the proof with `(IsLocalization.toLocalizationMap (nonZeroDivisors R) S).nontrivial zero_notMem_nonZeroDivisors`.
- [1] `Mathlib/RingTheory/Localization/FractionRing.lean:500` (blocking): `IsFractionRing.nontrivial'` duplicates the more general existing theorem `RingHom.domain_nontrivial`: the reverse implication from `Nontrivial S` to `Nontrivial R` holds for any algebra map and does not use the fraction-ring hypothesis.
  -> Remove `IsFractionRing.nontrivial'` and use `(algebraMap R S).domain_nontrivial` directly in the iff theorem.
- [2] `Mathlib/RingTheory/Localization/FractionRing.lean:506` (advisory): `IsFractionRing.nontrivial_iff_nontrivial` is redundantly named; in this namespace the subject is already the fraction-ring relation, and analogous equivalences such as `OreLocalization.nontrivial_iff` and `Valuation.Integers.nontrivial_iff` use the shorter `nontrivial_iff`.
  -> Rename the theorem to `IsFractionRing.nontrivial_iff`.

### R2

- [0] `Mathlib/RingTheory/Localization/FractionRing.lean:500` (advisory): `IsFractionRing.nontrivial'` is not a fraction-ring-specific fact: from `[Algebra R S]` and `[Nontrivial S]`, `Nontrivial R` already follows from the existing `RingHom.domain_nontrivial` applied to `algebraMap R S`, so this new theorem duplicates an existing, strictly more general API under extra hypotheses.
  -> Remove `IsFractionRing.nontrivial'` and prove the reverse direction of `nontrivial_iff_nontrivial` directly with `(algebraMap R S).domain_nontrivial`.

## PR 31007 (stratum A)

**TARGET v1096** `Mathlib/RingTheory/Perfection.lean`
```
 
 @[ext]
-theorem ext {f g : Ring.Perfection R p} (h : ∀ n, coeff R p n f = coeff R p n g) : f = g :=
+theorem ext' {f g : Perfection M p} (h : ∀ n, coeffMonoidHom M p n f = coeffMonoidHom M p n g) :
```
> `extMonoid` perhaps? Or docstring why prime and explain

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/FieldTheory/Perfect.lean:75` (powMulEquiv_mul'): `powMulEquiv_mul'` is new, and `powMulEquiv_mul` is declared at `Mathlib/FieldTheory/Perfect.lean:72`. `powMulEquiv_mul'` concludes `powMulEquiv M (p * q) = (powMulEquiv M q).trans (powMulEquiv M p)`; `powMulEquiv_mul` concludes `powMulEquiv M (p * q) = (powMulEquiv M p).trans (powMulEquiv M q)`.
- fact 1 [Primed names beside their unprimed sibling]: `Mathlib/RingTheory/Perfection.lean:73` (Perfection.ext'): `ext'` is new, and `ext` is declared at `Mathlib/RingTheory/Perfection.lean:190`. `ext'` concludes `f = g`; `ext` concludes `f = g`.
- fact 2 [Primed names beside their unprimed sibling]: `Mathlib/RingTheory/Perfection.lean:88` (Perfection.coeffMonoidHom_pow_p'): `coeffMonoidHom_pow_p'` is new, and `coeffMonoidHom_pow_p` is declared at `Mathlib/RingTheory/Perfection.lean:84`. `coeffMonoidHom_pow_p'` concludes `coeffMonoidHom M p (n + 1) f ^ p = coeffMonoidHom M p n f`; `coeffMonoidHom_pow_p` concludes `coeffMonoidHom M p (n + 1) (f ^ p) = coeffMonoidHom M p n f`.
- fact 3 [Primed names beside their unprimed sibling]: `Mathlib/RingTheory/Perfection.lean:105` (Perfection.coeffMonoidHom_iterate_powMonoidHom'): `coeffMonoidHom_iterate_powMonoidHom'` is new, and `coeffMonoidHom_iterate_powMonoidHom` is declared at `Mathlib/RingTheory/Perfection.lean:100`. `coeffMonoidHom_iterate_powMonoidHom'` concludes `coeffMonoidHom M p n ((powMonoidHom p)^[m] f) = coeffMonoidHom M p (n - m) f`; `coeffMonoidHom_iterate_powMonoidHom` concludes `coeffMonoidHom M p (n + m) ((powMonoidHom p)^[m] f) = coeffMonoidHom M p n f`.

### R1

- [0] `Mathlib/FieldTheory/Perfect.lean:51` (blocking): The new PerfectRing closure instances are named `one`, `mul`, and `pow` at the root namespace, so after importing this file unqualified `one`, `mul`, and `pow` refer to these PerfectRing instances. These names are far too generic for public root declarations.
  -> Rename the three instances to instance-style names such as `instPerfectRingOne`, `instPerfectRingMul`, and `instPerfectRingPow` (or place equivalently specific names in the `PerfectRing` namespace).
- [1] `Mathlib/RingTheory/Perfection.lean:424` (blocking): Changing `ModP` to `deriving CommRing` silently removes the existing public declaration `ModP.commRing`; explicit references to `ModP.commRing` no longer elaborate.
  -> Do not replace the named instance by an anonymous derived one: remove the `deriving CommRing` line and keep the existing `instance commRing : CommRing (ModP O p) := Ideal.Quotient.commRing ...`, or otherwise provide a deprecated `ModP.commRing` alias to a named replacement.
- [2] `Mathlib/FieldTheory/Perfect.lean:38` (advisory): The `PerfectRing` docstring is stale after this PR: it still says this is a ring of prime characteristic and the field doc says Frobenius, but the class now only assumes `[Pow R ℕ]` and the new instances include arbitrary commutative monoids at `p = 1`.
  -> Rewrite the class and field docstrings to say that `PerfectRing R p` means the `p`-th power map is bijective, and mention separately that for rings of prime characteristic this recovers the usual perfect-ring condition.
- [3] `Mathlib/RingTheory/Perfection.lean:31` (advisory): The docstring for `Perfection` refers to an unbound `M` in the displayed implementation even though the declaration's parameter is named `α`.
  -> Change the displayed implementation to use `α`, e.g. ``{ f : ℕ → α // ∀ n, f (n + 1) ^ p = f n }``.
- [4] `Mathlib/RingTheory/Perfection.lean:115` (advisory): The docstring for `Perfection.liftMonoidHom` says a monoid homomorphism has type `M →+* N`, which is the notation for ring homomorphisms and is not the type of this declaration.
  -> Change the docstring to say `M →* N` can be lifted to `M →* Perfection N p`.
- [5] `Mathlib/RingTheory/Perfection.lean:278` (advisory): The docstring for `Perfection.subring` says '`Perfection R p` as a semiring of `ℕ → R`', but the declaration constructs a `Subring`.
  -> Change the docstring to '`Perfection R p` as a subring of `ℕ → R`'.

### R2

- [0] `Mathlib/FieldTheory/Perfect.lean:51` (blocking): The new `PerfectRing` instances are declared at the root namespace with the names `one`, `mul`, and `pow`, which exposes extremely generic global constants for these instances.
  -> Rename these instances to descriptive names, for example `instPerfectRingOne`, `instPerfectRingMul`, and `instPerfectRingPow` (or put them in an appropriate namespace) instead of using the root names `one`, `mul`, and `pow`.
- [1] `Mathlib/RingTheory/Perfection.lean:426` (blocking): Changing `ModP` to `deriving CommRing` removes the previously public declaration `ModP.commRing` without a deprecation alias.
  -> Add a deprecated alias for the generated instance, e.g. immediately after the `deriving CommRing` line add `@[deprecated (since := "2025-10-28")] alias ModP.commRing := instCommRingModP`, or keep the explicit named instance.
- [2] `Mathlib/FieldTheory/Perfect.lean:209` (advisory): `instPerfectRingProd` is still restricted to commutative semirings with `ExpChar`, but after this PR the product instance only needs commutative monoids with perfect `p`-power maps.
  -> Generalize `instPerfectRingProd` to `[CommMonoid M] [CommMonoid N] [PerfectRing M p] [PerfectRing N p]` (and preferably place it with the other monoid-level `PerfectRing` API).
- [3] `Mathlib/FieldTheory/Perfect.lean:38` (advisory): The documentation for `PerfectRing` still says it is a ring in prime characteristic and that its field is Frobenius-bijectivity, but the class now only assumes `[Pow R ℕ]` and is used for monoids as well.
  -> Update the `PerfectRing` docstring and field docstring to describe bijectivity of the `p`-th power map at the generalized level, with the Frobenius/ring-in-characteristic-`p` interpretation described only as the semiring specialization.
- [4] `Mathlib/RingTheory/Perfection.lean:31` (advisory): The docstring for `Perfection` uses the undeclared name `M` in the displayed implementation even though the parameter is named `α`.
  -> Replace `M` by `α` in the displayed set in the `Perfection` docstring.
- [5] `Mathlib/RingTheory/Perfection.lean:115` (advisory): The docstring for `Perfection.liftMonoidHom` says a homomorphism `M →+* N` is lifted, but the declaration is about monoid homomorphisms `M →* N`.
  -> Change the docstring to say `M →* N` instead of `M →+* N`.
- [6] `Mathlib/RingTheory/Perfection.lean:278` (advisory): The docstring for `Perfection.subring` says it is a semiring of `ℕ → R`, but the declaration constructs a `Subring`.
  -> Change the docstring to say `subring` rather than `semiring`.

## PR 31077 (stratum B)

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/Topology/Compactness/Compact.lean:705` (generalized_tube_lemma'): `generalized_tube_lemma'` is new, and `generalized_tube_lemma` is declared at `Mathlib/Topology/Compactness/Compact.lean:686`. `generalized_tube_lemma'` concludes `∃ u ∈ 𝓝ˢ[s'] s, ∃ v ∈ 𝓝ˢ[t'] t, u ×ˢ v ⊆ n`; `generalized_tube_lemma` concludes `∃ (u : Set X) (v : Set Y), IsOpen u ∧ IsOpen v ∧ s ⊆ u ∧ t ⊆ v ∧ u ×ˢ v ⊆ n`.
- fact 1 [Primed names beside their unprimed sibling]: `Mathlib/Topology/ContinuousOn.lean:1466` (nhdsSetWithin_univ'): `nhdsSetWithin_univ'` is new, and `nhdsSetWithin_univ` is declared at `Mathlib/Topology/ContinuousOn.lean:1462`. `nhdsSetWithin_univ'` concludes `𝓝ˢ[s] univ = 𝓟 s`; `nhdsSetWithin_univ` concludes `𝓝ˢ[univ] s = 𝓝ˢ s`.
- fact 2 [Primed names beside their unprimed sibling]: `Mathlib/Topology/ContinuousOn.lean:1478` (nhdsSetWithin_empty'): `nhdsSetWithin_empty'` is new, and `nhdsSetWithin_empty` is declared at `Mathlib/Topology/ContinuousOn.lean:1474`. `nhdsSetWithin_empty'` concludes `𝓝ˢ[s] ∅ = ⊥`; `nhdsSetWithin_empty` concludes `𝓝ˢ[∅] s = ⊥`.
- fact 3 [Where dot notation may apply]: `Mathlib/Topology/ContinuousOn.lean:1534` (ContinuousOn.preimage_mem_nhdsSetWithin_of_mem_nhdsSet): `ContinuousOn.preimage_mem_nhdsSetWithin hf` applies a `ContinuousOn` lemma to `hf : ContinuousOn …`; it can be written `hf.preimage_mem_nhdsSetWithin`.

### R1

- [0] `Mathlib/Topology/ContinuousOn.lean:1489` (advisory): `mem_nhdsSet_induced` manually reproves the induced-topology neighborhood-set calculation that is already provided by `Topology.IsInducing.nhdsSet_eq_comap`.
  -> Move `nhdsSet_induced` before `mem_nhdsSet_induced`, prove it with `(Topology.IsInducing.induced f).nhdsSet_eq_comap s`, and then prove `mem_nhdsSet_induced` by `rw [nhdsSet_induced, mem_comap]`.
- [1] `Mathlib/Topology/Compactness/Compact.lean:705` (advisory): `generalized_tube_lemma'` introduces a public primed name for the `nhdsSetWithin` version of `generalized_tube_lemma`, so the name does not describe how this variant differs from the existing theorem.
  -> Rename it to a descriptive name such as `generalized_tube_lemma_nhdsSetWithin` and wrap the declaration line to stay under the line-length limit.
- [2] `Mathlib/Topology/ContinuousOn.lean:28` (advisory): The module docstring describes `𝓝ˢ[t] s` as the filter `nhdsWithin s t`, which is the point-neighborhood-within definition and has the wrong meaning here.
  -> Change this bullet to say that `𝓝ˢ[t] s` is the filter `nhdsSetWithin s t` of neighborhoods of a set `s` within a set `t`.
- [3] `Mathlib/Topology/Defs/Filter.lean:161` (advisory): The documentation for `nhdsSetWithin` misprints its notation as `𝓝[t] s`, and the file's notation list still omits the new `𝓝ˢ[t] s` notation.
  -> In the `nhdsSetWithin` docstring, replace `𝓝[t] s` with `𝓝ˢ[t] s`; also add a notation-list bullet for `𝓝ˢ[t] s` as `nhdsSetWithin s t`.

### R2

- [0] `Mathlib/Topology/ContinuousOn.lean:28` (advisory): The module documentation entry for `𝓝ˢ[t] s` names the wrong underlying filter: it says this notation is `nhdsWithin s t`, but the PR introduces `nhdsSetWithin s t`.
  -> Replace `nhdsWithin s t` with `nhdsSetWithin s t` in this notation bullet.
- [1] `Mathlib/Topology/Defs/Filter.lean:161` (advisory): The docstring for `nhdsSetWithin` displays the wrong notation, `𝓝[t] s`, which is the point-within notation rather than the new set-within notation `𝓝ˢ[t] s`.
  -> Change the docstring to say that elements of `𝓝ˢ[t] s` are sets containing the intersection of `t` and a neighborhood of `s`.
- [2] `Mathlib/Topology/Defs/Filter.lean:112` (advisory): The `## Notation` section of the module documentation omits the new notation `𝓝ˢ[t] s` introduced in this file.
  -> Add a notation bullet for `𝓝ˢ[t] s`, e.g. `* `𝓝ˢ[t] s`: the filter `nhdsSetWithin s t` ...`, and adjust the preceding `𝓝ˢ s` bullet punctuation accordingly.
- [3] `Mathlib/Topology/Compactness/Compact.lean:705` (advisory): The new public theorem `generalized_tube_lemma'` uses a prime even though its distinguishing feature is the `nhdsSetWithin` formulation, so the name is less descriptive than its sibling names `generalized_tube_lemma_left` and `generalized_tube_lemma_right`.
  -> Rename `generalized_tube_lemma'` to a descriptive name such as `generalized_tube_lemma_nhdsSetWithin`.
- [4] `Mathlib/Topology/Compactness/Compact.lean:703` (advisory): The three local commands `open Topology Set in` before the new tube lemmas are redundant, because this file already has `open Set Filter Topology TopologicalSpace Function` at the top and the preceding `IsCompact.nhdsSetWithin_prod_eq` uses the same notation without them.
  -> Delete the redundant `open Topology Set in` lines before `generalized_tube_lemma'`, `generalized_tube_lemma_left`, and `generalized_tube_lemma_right`.

## PR 31793 (stratum B)

- fact 0 [Where dot notation may apply]: `Mathlib/Dynamics/Ergodic/Ergodic.lean:100` (MeasureTheory.MeasurePreserving.ergodic_of_ergodic_semiconj): `ergodic_of_ergodic_semiconj` concludes `Ergodic …` and is named beside that namespace; inside it, it is `Ergodic.of_ergodic_semiconj`.

### R1

- [0] `Mathlib/Dynamics/Ergodic/MeasurePreserving.lean:93` (advisory): `MeasurePreserving.map_of_comp` unnecessarily requires `f` to be everywhere measurable; the proof only needs `f` to be a.e. measurable with respect to the source measure, since `f` only appears through `μa.map f`.
  -> Weaken the last hypothesis to `(hf : AEMeasurable f μa)` and prove the map equality with `hg.aemeasurable.map_map_of_aemeasurable hf`; update the call in `MeasurePreserving.of_semiconj` to pass `hfm.aemeasurable`.

### R2

- [0] `Mathlib/Dynamics/Ergodic/MeasurePreserving.lean:93` (advisory): `MeasurePreserving.map_of_comp` assumes `hf : Measurable f`, but the proof only needs `f` to be a.e.-measurable with respect to `μa`; the underlying measure identity is already available as `AEMeasurable.map_map_of_aemeasurable`. Keeping the stronger measurability hypothesis makes this basic pushforward lemma less reusable than the measure API supports.
  -> Weaken the last hypothesis to `(hf : AEMeasurable f μa)`, prove the map equality with `AEMeasurable.map_map_of_aemeasurable hg.aemeasurable hf`, and update the downstream call in `MeasurePreserving.of_semiconj` to pass `hfm.aemeasurable`.

## PR 31961 (stratum A)

**TARGET v1252** `Mathlib/Topology/DiscreteSubset.lean`
```
+lemma Set.Finite.compl_mem_codiscrete {S : Set X} (hs : S.Finite) : Sᶜ ∈ codiscrete X :=
+  codiscrete_le_cofinite (by simpa)
+
+lemma infinite_of_accPt {S : Set X} {x : X} (h : AccPt x (𝓟 S)) : S.Infinite := by
```
> I think you can leave it here, but I would change the name.
```suggestion
lemma AccPt.setInfinite {S : Set X} {x : X} (h : AccPt x (𝓟 S)) : S.Infinite := by
```
Or `Set.Infinite.of_accPt`

**TARGET v1254** `Mathlib/Topology/DiscreteSubset.lean`
```
+lemma Set.Finite.compl_mem_codiscrete {S : Set X} (hs : S.Finite) : Sᶜ ∈ codiscrete X :=
+  codiscrete_le_cofinite (by simpa)
+
+lemma infinite_of_accPt {S : Set X} {x : X} (h : AccPt x (𝓟 S)) : S.Infinite := by
```
> > I don't think `Set.Infinite.of_accPt` makes sense because `S.Infinite` is not a hypothesis.

The reason this makes sense is that if you have the expected type being `Set.Infinite _` then you can write `.of_accPt hAccPt`. This pattern is also present on e.g. `Filter.Eventually.of_forall` and `RegularSpace.of_exists_mem_nhds_isClosed_subset`.

- fact 0 [Where dot notation may apply]: `Mathlib/Topology/DiscreteSubset.lean:268` (infinite_of_accPt): `infinite_of_accPt` concludes `S.Infinite …` and is named beside that namespace; inside it, it is `Infinite.of_accPt`.

### R1

- [0] `Mathlib/Topology/DiscreteSubset.lean:268` (advisory): `infinite_of_accPt` is a basic T1 accumulation-point fact and its statement mentions neither codiscrete filters nor discrete subsets, so placing it in `Topology/DiscreteSubset.lean` hides it behind an unrelated import.
  -> Move `infinite_of_accPt` to `Mathlib/Topology/Separation/Basic.lean`, next to the existing `infinite_of_mem_nhds`, and remove it from `DiscreteSubset.lean`. A proof there is:
```lean
lemma infinite_of_accPt {S : Set X} {x : X} (h : AccPt x (𝓟 S)) : S.Infinite := by
  rw [← frequently_cofinite_mem_iff_infinite]
  exact (accPt_iff_frequently_nhdsNE.mp h).filter_mono (nhdsNE_le_cofinite x)
```

### R2

- [0] `Mathlib/Topology/DiscreteSubset.lean:268` (advisory): `infinite_of_accPt` is a general T1 accumulation-point lemma and does not depend on the codiscrete filter API introduced in this file, so placing it in `Topology/DiscreteSubset.lean` makes the lemma unavailable from the lower-level topology files where users of `AccPt` would expect it.
  -> Move this declaration to `Mathlib/Topology/Separation/Basic.lean` near `infinite_of_mem_nhds` (or another lower-level AccPt/T1 section) and prove it directly from `accPt_iff_nhds`; remove the copy from `DiscreteSubset.lean`.

## PR 32540 (stratum B)

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/RingTheory/SurjectiveOnStalks.lean:185` (RingHom.SurjectiveOnStalks.baseChange'): `baseChange'` is new, and `baseChange` is declared at `Mathlib/RingTheory/SurjectiveOnStalks.lean:165`. `baseChange'` concludes `(Algebra.TensorProduct.includeRight (R := R) (A := S) (B := T)).SurjectiveOnStalks`; `baseChange` concludes `(algebraMap S (S ⊗[R] T)).SurjectiveOnStalks`.
- fact 1 [Where dot notation may apply]: `Mathlib/RingTheory/TensorProduct/Finite.lean:158` (RingHom.surjective_of_tmul_eq_tmul_of_finite): `surjective_of_tmul_eq_tmul_of_finite` concludes `Function.Surjective …` and is named beside that namespace; inside it, it is `Surjective.of_tmul_eq_tmul_of_finite`.

### R1

- [0] `Mathlib/RingTheory/SurjectiveOnStalks.lean:185` (advisory): `RingHom.SurjectiveOnStalks.baseChange'` exposes a primed public name only to distinguish the `includeRight` variant of `baseChange`; the statement is about `Algebra.TensorProduct.includeRight`, so the prime does not describe the variant.
  -> Rename this lemma to `SurjectiveOnStalks.includeRight` and update the private helper to use `Hf.includeRight` instead of `Hf.baseChange'`.
- [1] `Mathlib/RingTheory/SurjectiveOnStalks.lean:205` (advisory): `RingHom.SurjectiveOnStalks.tensorProductMap` only states the same-base specialization of `Algebra.TensorProduct.map`, although `map` also allows the left morphism to be an algebra map over a larger base `P`.
  -> Generalize the statement to variables `{P A B C D}` with `[Algebra R P]`, towers `R → P → A` and `R → P → C`, `f : A →ₐ[P] C`, and `g : B →ₐ[R] D`; start the proof with `change (Algebra.TensorProduct.map (f.restrictScalars R) g).SurjectiveOnStalks` and then use the current factorization proof.
- [2] `Mathlib/RingTheory/TensorProduct/Finite.lean:197` (advisory): `RingHom.Finite.tensorProductMap` only covers `Algebra.TensorProduct.map` when both input maps are over the same base `R`; the theorem can be stated at the full generality of `Algebra.TensorProduct.map` with the left map over a larger base `P`.
  -> Generalize the public statement to `{R P A B C D}` with `[Algebra R P]`, towers `R → P → A` and `R → P → C`, `f : A →ₐ[P] C`, and `g : B →ₐ[R] D`; in the proof, `change` the target to the map using `f.restrictScalars R` and reuse the existing factorization through the private `_id` lemma.
- [3] `Mathlib/RingTheory/TensorProduct/Finite.lean:197` (advisory): `RingHom.Finite.tensorProductMap` is API for `AlgHom.Finite` hypotheses and an `Algebra.TensorProduct.map` result, but it is declared in the `RingHom.Finite` namespace; as a result, dot notation such as `Hf.tensorProductMap Hg` does not work for the usual `Hf : f.Finite` algebra-hom hypothesis.
  -> Move the public lemma to `AlgHom.Finite.tensorProductMap` (with conclusion `(Algebra.TensorProduct.map f g).Finite`) and rename the private helper consistently, or add that as the public API and use it for dot notation.

### R2

- [0] `Mathlib/RingTheory/TensorProduct/Finite.lean:197` (advisory): `RingHom.Finite.tensorProductMap` is an `AlgHom.Finite` theorem: its hypotheses are `Hf : f.Finite` and `Hg : g.Finite` for algebra homomorphisms, and its conclusion pretty-prints as `(Algebra.TensorProduct.map f g).Finite`. Keeping it in the `RingHom.Finite` namespace prevents the expected `Hf.tensorProductMap Hg` dot notation for `AlgHom.Finite`.
  -> Rename/move the public lemma to `AlgHom.Finite.tensorProductMap`, state the conclusion as `(Algebra.TensorProduct.map f g).Finite`, and keep a `change (Algebra.TensorProduct.map f g).toRingHom.Finite` at the start of the proof if needed. Update the private helper comment/reference accordingly.
- [1] `Mathlib/RingTheory/SurjectiveOnStalks.lean:185` (advisory): `RingHom.SurjectiveOnStalks.baseChange'` still uses the lower-level `surjectiveOnStalks_of_surjective (Algebra.TensorProduct.comm R T S).surjective` even though the PR adds the canonical `RingEquiv.surjectiveOnStalks` lemma immediately above.
  -> Replace the proof body with `convert (Algebra.TensorProduct.comm R T S).toRingEquiv.surjectiveOnStalks.comp (hf.baseChange (S := T))`.

## PR 32610 (stratum B)

- fact 0 [Where dot notation may apply]: `Mathlib/Algebra/Group/Hom/Defs.lean:710` (MonoidHom.isDedekindFiniteMonoid_of_injective): `isDedekindFiniteMonoid_of_injective` concludes `IsDedekindFiniteMonoid …` and is named beside that namespace; inside it, it is `IsDedekindFiniteMonoid.of_injective`.

### R1

- [0] `Mathlib/Algebra/Group/Submonoid/Defs.lean:373` (advisory): The new `SubmonoidClass` instance for `IsDedekindFiniteMonoid S` is missing `@[to_additive]`, so the additive submonoid analogue is not generated even though this section systematically provides additive counterparts.
  -> Add `@[to_additive]` to this instance so `AddSubmonoidClass` inherits `IsDedekindFiniteAddMonoid` from the ambient additive monoid.
- [1] `Mathlib/GroupTheory/DedekindFinite.lean:17` (advisory): The finite-monoid instance is missing `@[to_additive]`, leaving no generated instance that finite additive monoids are `IsDedekindFiniteAddMonoid`.
  -> Add `@[to_additive]` to the finite `IsDedekindFiniteMonoid` instance.

### R2

- [0] `Mathlib/GroupTheory/DedekindFinite.lean:17` (advisory): The finite-monoid instance is multiplicative-only even though the new class has an additive counterpart, so a finite noncommutative `AddMonoid` cannot synthesize `IsDedekindFiniteAddMonoid`.
  -> Add `@[to_additive]` to this instance so the finite additive-monoid instance is generated as well.
- [1] `Mathlib/Algebra/Group/Submonoid/Defs.lean:373` (advisory): The inherited Dedekind-finiteness instance for submonoids is missing its additive analogue, so additive submonoids of a Dedekind-finite additive monoid cannot infer `IsDedekindFiniteAddMonoid`.
  -> Add `@[to_additive]` to the `SubmonoidClass` instance.

## PR 32674 (stratum A)

**TARGET v1397** `Mathlib/Topology/GDelta/Basic.lean`
```
+/- The preimage of a Gδ set under a continuous map is Gδ. -/
+theorem isGδ_induced [TopologicalSpace Y] {f : X → Y} {s : Set Y} (hf : Continuous f)
+    (hs : IsGδ s) : IsGδ (f ⁻¹' s) := by
+  obtain ⟨U, hU1, hU2⟩ := IsGδ.eq_iInter_nat hs
```
> ```suggestion
  obtain ⟨U, hU1, hU2⟩ := hs.eq_iInter_nat
```

- fact 0 [Where dot notation may apply]: `Mathlib/Topology/Baire/Lemmas.lean:52` (IsGδ.baireSpace_of_dense): `baireSpace_of_dense` concludes `BaireSpace …` and is named beside that namespace; inside it, it is `BaireSpace.of_dense`.
- fact 1 [Where dot notation may apply]: `Mathlib/Topology/GDelta/Basic.lean:155` (isGδ_induced): `IsGδ.eq_iInter_nat hs` applies a `IsGδ` lemma to `hs : IsGδ …`; it can be written `hs.eq_iInter_nat`.

### R1

- [0] `Mathlib/Topology/GDelta/Basic.lean:149` (advisory): The docstring copied onto `IsGδ.iUnion` says this is the “bounded indexed union version”, but this declaration is the unbounded union over a `Finite` index type.
  -> Change the docstring to say this is the indexed union over a finite type, for example: “The union of finitely many Gδ sets is a Gδ set, indexed union version.”
- [1] `Mathlib/Topology/GDelta/Basic.lean:153` (advisory): `isGδ_induced` proves preservation of `IsGδ` under continuous preimage, but the name is not in the `IsGδ` namespace and `_induced` is misleading for a preimage theorem.
  -> Rename it to `IsGδ.preimage` and update the use in `LocallyCompactRegular.lean`, preferably with a docstring. A compiling replacement is `theorem IsGδ.preimage [TopologicalSpace Y] {f : X → Y} {s : Set Y} (hf : Continuous f) (hs : IsGδ s) : IsGδ (f ⁻¹' s) := ...`.
- [2] `Mathlib/Topology/Constructions.lean:643` (advisory): `exists_open_dense_of_open_dense_subtype` is stated only for subtype maps, but the proof only uses that the map is inducing with dense range.
  -> Prove the reusable theorem for an inducing map with dense range, then derive the subtype lemma from `Topology.IsInducing.subtypeVal` and `hs.denseRange_val`. For example, add `Topology.IsInducing.exists_open_dense_of_open_dense {f : X → Y} (hf : Topology.IsInducing f) (hfd : DenseRange f) ... : ∃ v, IsOpen v ∧ Dense v ∧ f ⁻¹' v = u`.
- [3] `Mathlib/Topology/Baire/LocallyCompactRegular.lean:62` (advisory): `IsGδ.of_t2Space_locallyCompactSpace` manually constructs the homeomorphism between `((↑) ⁻¹' s : Set (closure s))` and `s`, duplicating the standard embedding homeomorphism API.
  -> Replace the manual `Homeomorph` literal with `Topology.IsEmbedding.subtypeVal.homeomorphOfSubsetRange (by simpa using subset_closure)` and use its `.baireSpace`.

### R2

- [0] `Mathlib/Topology/GDelta/Basic.lean:148` (advisory): The docstring for `IsGδ.iUnion` says this is the "bounded indexed union version", but the declaration is the unbounded finite indexed union `⋃ i, f i`.
  -> Change the docstring to say "finite indexed union version" or "unbounded indexed union version" rather than "bounded indexed union version".
- [1] `Mathlib/Topology/GDelta/Basic.lean:153` (advisory): `isGδ_induced` is misnamed: the theorem is the general preimage theorem for a Gδ set under any continuous map, not a result specifically about induced topologies, and it is not in the `IsGδ` API namespace like the neighboring closure operations.
  -> Rename it to `IsGδ.preimage`, turn the preceding ordinary comment into its docstring, and update the use in `LocallyCompactRegular.lean` to call `hG.preimage continuous_subtype_val` (or `IsGδ.preimage continuous_subtype_val hG`).
- [2] `Mathlib/Topology/Baire/LocallyCompactRegular.lean:62` (advisory): `IsGδ.of_t2Space_locallyCompactSpace` does not name its conclusion; in the `IsGδ` namespace this reads like a constructor for `IsGδ`, while the theorem proves a `BaireSpace` instance.
  -> Rename it to `IsGδ.baireSpace_of_t2Space_locallyCompactSpace` (or the analogous `...locallyCompactSpace` spelling maintainers prefer) and update downstream references.
- [3] `Mathlib/Topology/Baire/LocallyCompactRegular.lean:70` (advisory): `IsGδ.of_t2Space_locallyCompactSpace` hand-builds the homeomorphism between `((↑) ⁻¹' s : Set (closure s))` and `s`, but this is exactly the existing embedding API `Topology.IsEmbedding.subtypeVal.homeomorphOfSubsetRange`.
  -> Replace the manual `Homeomorph` construction with:
```lean
  have h_homeo : ((↑) ⁻¹' s : Set (closure s)) ≃ₜ s :=
    Topology.IsEmbedding.subtypeVal.homeomorphOfSubsetRange (by simpa using subset_closure)
  exact h_homeo.baireSpace
```
- [4] `Mathlib/Topology/Constructions.lean:643` (advisory): `exists_open_dense_of_open_dense_subtype` manually reproves density by expanding `dense_iff_inter_open`, but the result follows directly from the dense-range image API for the subtype map.
  -> Use `hs.denseRange_val.dense_of_mapsTo continuous_subtype_val hud` after choosing the ambient open set; for example:
```lean
  choose v hv1 hv2 using huo
  refine ⟨v, hv1, hs.denseRange_val.dense_of_mapsTo continuous_subtype_val hud ?_, hv2⟩
  intro x hx
  show x.1 ∈ v
  simpa [← hv2] using hx
```

## PR 32715 (stratum A)

**TARGET v1412** `Mathlib/Data/Nat/Factorization/Basic.lean`
```
     simp [pp.factorization, hqp.symm]
 
+theorem ordProj_PrimePow_eq_self {p k : ℕ} (hp : Prime p) : ordProj[p] (p ^ k) = p ^ k := by
+  have pow_ne_zero : p ^ k ≠ 0 := pow_ne_zero k (Prime.ne_zero hp)
```
> ```suggestion
  have pow_ne_zero : p ^ k ≠ 0 := pow_ne_zero k hp.ne_zero
```

**TARGET v1413** `Mathlib/Data/Nat/Factorization/Basic.lean`
```
+  apply Nat.eq_of_factorization_eq
+  · exact pos_iff_ne_zero.mp (ordProj_pos (p ^ k) p)
+  · exact pow_ne_zero
+  · simp [Prime.factorization_pow hp]
```
> ```suggestion
  apply Nat.eq_of_factorization_eq
  · exact pos_iff_ne_zero.mp (ordProj_pos (p ^ k) p)
  · exact pow_ne_zero k hp.ne_zero
  · simp [Prime.factorization_pow hp]
```

**TARGET v1414** `Mathlib/Data/Nat/Factorization/Basic.lean`
```
+theorem ordCompl_PrimePow_eq_one {p k : ℕ} (hp : Prime p) : ordCompl[p] (p ^ k) = 1 := by
+  have pow_ne_zero : p ^ k ≠ 0 := pow_ne_zero k (Prime.ne_zero hp)
+  apply Nat.eq_of_factorization_eq
+  · exact pos_iff_ne_zero.mp (ordCompl_pos p pow_ne_zero)
```
> ```suggestion
  apply Nat.eq_of_factorization_eq
  · exact pos_iff_ne_zero.mp (ordCompl_pos p (pow_ne_zero k hp.ne_zero))
```

- fact 0 [Where dot notation may apply]: `Mathlib/Data/Nat/Factorization/Basic.lean:222` (Nat.ordProj_PrimePow_eq_self): `Prime.ne_zero hp` applies a `Prime` lemma to `hp : Prime …`; it can be written `hp.ne_zero`.
- fact 1 [Where dot notation may apply]: `Mathlib/Data/Nat/Factorization/Basic.lean:226` (Nat.ordProj_PrimePow_eq_self): `Prime.factorization_pow hp` applies a `Prime` lemma to `hp : Prime …`; it can be written `hp.factorization_pow`.
- fact 2 [Where dot notation may apply]: `Mathlib/Data/Nat/Factorization/Basic.lean:229` (Nat.ordCompl_PrimePow_eq_one): `Prime.ne_zero hp` applies a `Prime` lemma to `hp : Prime …`; it can be written `hp.ne_zero`.
- fact 3 [Where dot notation may apply]: `Mathlib/Data/Nat/Factorization/Basic.lean:233` (Nat.ordCompl_PrimePow_eq_one): `Prime.factorization_pow hp` applies a `Prime` lemma to `hp : Prime …`; it can be written `hp.factorization_pow`.

### R1

- [0] `Mathlib/Data/Nat/Factorization/Basic.lean:221` (advisory): `Nat.ordProj_PrimePow_eq_self` and the adjacent `Nat.ordCompl_PrimePow_eq_one`/`Nat.ordCompl_PrimePow_mul_eq_self` use the CamelCase segment `PrimePow` even though their statements are about the explicit expression `p ^ k`; analogous Mathlib theorem names for explicit prime powers use lower snake-case `prime_pow`.
  -> Rename these declarations to `ordProj_prime_pow_eq_self`, `ordCompl_prime_pow_eq_one`, and `ordCompl_prime_pow_mul_eq_self`, and update the internal reference in the last proof.
- [1] `Mathlib/Data/Nat/Factorization/Basic.lean:221` (advisory): `Nat.ordProj_PrimePow_eq_self` proves a definitional simplification by factorization extensionality, but `ordProj[p] (p ^ k)` reduces directly using `Prime.factorization_pow`.
  -> Replace the proof with:
```lean
theorem ordProj_PrimePow_eq_self {p k : ℕ} (hp : Prime p) : ordProj[p] (p ^ k) = p ^ k := by
  simp [Prime.factorization_pow hp]
```
- [2] `Mathlib/Data/Nat/Factorization/Basic.lean:228` (advisory): `Nat.ordCompl_PrimePow_eq_one` also uses factorization extensionality, although after simplifying the factorization it is just `p ^ k / p ^ k = 1`.
  -> Replace the proof with:
```lean
theorem ordCompl_PrimePow_eq_one {p k : ℕ} (hp : Prime p) : ordCompl[p] (p ^ k) = 1 := by
  simpa [Prime.factorization_pow hp] using Nat.div_self (pow_pos hp.pos k)
```

### R2

- [0] `Mathlib/Data/Nat/Factorization/Basic.lean:221` (advisory): The new lemmas `Nat.ordProj_PrimePow_eq_self`, `Nat.ordCompl_PrimePow_eq_one`, and `Nat.ordCompl_PrimePow_mul_eq_self` use `PrimePow` for an argument of the form `p ^ k` under a `Prime p` hypothesis. In theorem names Mathlib uses the snake-case token `prime_pow` for this situation; the `PrimePow` spelling is used for CamelCase definitions or for names involving the `IsPrimePow` predicate.
  -> Rename these declarations to `ordProj_prime_pow_eq_self`, `ordCompl_prime_pow_eq_one`, and `ordCompl_prime_pow_mul_eq_self`, and update the reference in the last proof accordingly.
- [1] `Mathlib/Data/Nat/Factorization/Basic.lean:239` (advisory): `Nat.ordCompl_eq_self_iff_zero_or_not_dvd` is only the prime/divisibility specialization of a more reusable equivalence: `ordCompl[p] n = n` is exactly `n.factorization p = 0`, with no `Prime p` hypothesis and also covering the zero and non-prime cases.
  -> Add the general lemma
```lean
theorem ordCompl_eq_self_iff_factorization_eq_zero (n p : ℕ) :
    ordCompl[p] n = n ↔ n.factorization p = 0 := by
  constructor
  · intro h
    have := DFunLike.congr_fun (factorization_ordCompl n p) p
    rwa [h, Finsupp.erase_same] at this
  · intro h
    by_cases hn : n = 0
    · simp [hn]
    · apply Nat.eq_of_factorization_eq (ordCompl_pos p hn).ne' hn
      intro q
      rw [factorization_ordCompl]
      by_cases hq : q = p
      · simp [hq, h]
      · simp [Finsupp.erase_ne hq]
```
Then either replace the current declaration with this one, or keep the current divisibility form as a short corollary using `factorization_eq_zero_iff` and `hp`.

## PR 32992 (stratum A)

**TARGET v1490** `Mathlib/Analysis/Fourier/Convolution.lean`
```
+variable [NormedSpace ℂ F₃]
+
+/-- Calculate the Fourier transform of the convolution as a symmetric integral. -/
+theorem fourier_bilin_convolution_eq' (B : F₁ →L[𝕜] F₂ →L[𝕜] F₃) {f₁ : E → F₁} {f₂ : E → F₂}
```
> Just so that the name is more informative, as the statement is pretty different from the version without `'`.
```suggestion
theorem fourier_bilin_convolution_eq_integral (B : F₁ →L[𝕜] F₂ →L[𝕜] F₃) {f₁ : E → F₁} {f₂ : E → F₂}
```

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/Analysis/Fourier/Convolution.lean:60` (Real.fourier_bilin_convolution_eq'): `fourier_bilin_convolution_eq'` is new, and `fourier_bilin_convolution_eq` is declared at `Mathlib/Analysis/Fourier/Convolution.lean:95`. `fourier_bilin_convolution_eq'` concludes `𝓕 (f₁ ⋆[B] f₂) ξ = ∫ y, ∫ x, 𝐞 (-inner ℝ (y + x) ξ) • B (f₁ x) (f₂ y)`; `fourier_bilin_convolution_eq` concludes `𝓕 (f₁ ⋆[B] f₂) ξ = B (𝓕 f₁ ξ) (𝓕 f₂ ξ)`.

### R1

- [0] `Mathlib/Analysis/Fourier/Convolution.lean:60` (blocking): `Real.fourier_bilin_convolution_eq'` does not compile: the final `simpa` in the Fubini integrability bound leaves the goal with `|‖B‖|`, so the proof of the bound from `B.le_opNorm₂` is not accepted.
  -> Replace that `simpa` by an explicit simplification of the phase norm and the norm of the nonnegative real bound, for example include `Function.uncurry`, `Circle.smul_def`, `norm_smul`, and `Real.norm_of_nonneg (norm_nonneg B)` (or otherwise prove the same bound explicitly).
- [1] `Mathlib/Analysis/Fourier/Convolution.lean:95` (blocking): `Real.fourier_bilin_convolution_eq` does not compile: the proof of the integrability needed for `integral_apply` does not simplify the norm of the unit-circle scalar, and the expected bound still contains `|‖B‖|`.
  -> Change the bound proof to simplify the circle scalar via `Circle.smul_def`/`norm_smul` and remove `|‖B‖|` via `Real.norm_of_nonneg (norm_nonneg B)`, e.g. use `simpa [Circle.smul_def, norm_smul, Real.norm_of_nonneg (norm_nonneg B)] using le_opNorm B (f₁ x)`.
- [2] `Mathlib/Analysis/Fourier/Convolution.lean:60` (advisory): `Real.fourier_bilin_convolution_eq'` and the downstream public convolution Fourier lemmas assume `Continuous f₁` and `Continuous f₂`, but the convolution/Fubini integrability needed here is already available from the two `Integrable` hypotheses; the continuity assumptions unnecessarily restrict the API.
  -> Use `MeasureTheory.Integrable.convolution_integrand` (with `B.flip`) for the product integrability, delete the private `integrable_prod_sub`, and remove the `hf₁' : Continuous f₁` and `hf₂' : Continuous f₂` arguments from `fourier_bilin_convolution_eq'`, `fourier_bilin_convolution_eq`, `fourier_smul_convolution_eq`, and `fourier_mul_convolution_eq`.
- [3] `Mathlib/Analysis/Fourier/Convolution.lean:8` (advisory): `Mathlib.Analysis.Fourier.Convolution` imports the higher-level distribution/Schwartz module `Mathlib.Analysis.Distribution.FourierSchwartz`, although this file only needs the Fourier transform API, convolution API, and Haar invariance instances; this makes a Fourier file depend on the Distribution hierarchy unnecessarily.
  -> Replace the `FourierSchwartz` import with lower-level imports, for example `Mathlib.Analysis.Fourier.FourierTransform`, `Mathlib.Analysis.Convolution`, and the Haar invariance module such as `Mathlib.MeasureTheory.Measure.Haar.Unique`.

### R2

- [0] `Mathlib/Analysis/Fourier/Convolution.lean:60` (blocking): `Real.fourier_bilin_convolution_eq'` does not compile: the `simpa` closing the domination proof at line 77 leaves the goal with `|‖B‖|` while the available inequality has `‖B‖`.
  -> Replace that final `simpa` in the domination proof with `simpa [abs_of_nonneg (norm_nonneg B)]` (or an equivalent simplification of `|‖B‖|`).
- [1] `Mathlib/Analysis/Fourier/Convolution.lean:95` (blocking): `Real.fourier_bilin_convolution_eq` does not compile: the proof of the `integral_apply` integrability bound uses `simpa [← Circle.smul_def]`, but after `Circle.smul_def` the scalar is complex, so Lean still has to simplify the unit scalar norm and the `|‖B‖|` coefficient.
  -> Replace the last line of that bound with `simpa [norm_smul, Circle.norm_coe, abs_of_nonneg (norm_nonneg B)] using le_opNorm B (f₁ x)`.
- [2] `Mathlib/Analysis/Fourier/Convolution.lean:95` (advisory): `Real.fourier_bilin_convolution_eq` and its primed/scalar/multiplication variants assume `Continuous f₁` and `Continuous f₂`, but the convolution Fourier identity only needs the two `Integrable` hypotheses; the continuity assumptions are not needed for the statement.
  -> Remove the `hf₁' : Continuous f₁` and `hf₂' : Continuous f₂` arguments from `fourier_bilin_convolution_eq'`, `fourier_bilin_convolution_eq`, `fourier_smul_convolution_eq`, and `fourier_mul_convolution_eq`. In the proof, use the existing convolution measurability/integrability API, e.g. prove `integrable_prod_sub` from `hf₂.norm.convolution_integrand (ContinuousLinearMap.mul ℝ ℝ) hf₁.norm`, and use `hf₂.aestronglyMeasurable.convolution_integrand B.flip hf₁.aestronglyMeasurable` for the product integrand measurability.
- [3] `Mathlib/Analysis/Fourier/Convolution.lean:8` (advisory): `Mathlib.Analysis.Fourier.Convolution` imports `Mathlib.Analysis.Distribution.FourierSchwartz`, which pulls the Distribution/Schwartz-space development into this Fourier-convolution file even though the file only uses the Fourier transform API, convolution API, and the Haar neg-invariance instance.
  -> Replace the `FourierSchwartz` import with the narrower imports `Mathlib.Analysis.Fourier.FourierTransform`, `Mathlib.Analysis.Convolution`, and `Mathlib.MeasureTheory.Measure.Haar.Unique`.

## PR 33006 (stratum B)

- fact 0 [Where dot notation may apply]: `Mathlib/CategoryTheory/Functor/Derived/PointwiseLeftDerived.lean:79` (CategoryTheory.Functor.hasPointwiseRightKanExtension_of_hasPointwiseLeftDerivedFunctor): `hasPointwiseRightKanExtension_of_hasPointwiseLeftDerivedFunctor` concludes `HasPointwiseRightKanExtension …` and is named beside that namespace; inside it, it is `HasPointwiseRightKanExtension.of_hasPointwiseLeftDerivedFunctor`.
- fact 1 [Where dot notation may apply]: `Mathlib/CategoryTheory/Functor/Derived/PointwiseLeftDerived.lean:86` (CategoryTheory.Functor.hasLeftDerivedFunctor_of_hasPointwiseLeftDerivedFunctor): `hasLeftDerivedFunctor_of_hasPointwiseLeftDerivedFunctor` concludes `F.HasLeftDerivedFunctor …` and is named beside that namespace; inside it, it is `HasLeftDerivedFunctor.of_hasPointwiseLeftDerivedFunctor`.
- fact 2 [Where dot notation may apply]: `Mathlib/CategoryTheory/Functor/Derived/PointwiseLeftDerived.lean:164` (CategoryTheory.Functor.hasPointwiseLeftDerivedFunctor_of_inverts): `hasPointwiseLeftDerivedFunctor_of_inverts` concludes `F.HasPointwiseLeftDerivedFunctor …` and is named beside that namespace; inside it, it is `HasPointwiseLeftDerivedFunctor.of_inverts`.
- fact 3 [Where dot notation may apply]: `Mathlib/CategoryTheory/Functor/Derived/PointwiseLeftDerived.lean:172` (CategoryTheory.Functor.isLeftDerivedFunctor_of_inverts): `isLeftDerivedFunctor_of_inverts` concludes `F'.IsLeftDerivedFunctor …` and is named beside that namespace; inside it, it is `IsLeftDerivedFunctor.of_inverts`.
- fact 4 [Where dot notation may apply]: `Mathlib/CategoryTheory/Functor/Derived/PointwiseLeftDerived.lean:183` (CategoryTheory.Functor.isIso_of_isLeftDerivedFunctor_of_inverts): `isIso_of_isLeftDerivedFunctor_of_inverts` concludes `IsIso …` and is named beside that namespace; inside it, it is `IsIso.of_isLeftDerivedFunctor_of_inverts`.

### R1


### R2


## PR 34241 (stratum A)

**TARGET v1661** `Mathlib/Analysis/Normed/Lp/Matrix.lean`
```
+
+@[simp]
+theorem ofLp_toLpLin (A : Matrix m n R) (x : WithLp p (n → R)) :
+    ofLp (Matrix.toLpLin p q A x) = Matrix.toLin' A (ofLp x) :=
```
> I feel like dot notation would look better throughout
```suggestion
    (A.toLpLin p q x).ofLp = A.toLin' x.ofLp :=
```

- fact 0 [Where dot notation may apply]: `Mathlib/Analysis/Normed/Lp/Matrix.lean:36` (Matrix.toLpLin_toLp): `Matrix.toLin' A` applies a `Matrix` lemma to `A : Matrix …`; it can be written `A.toLin'`.
- fact 1 [Where dot notation may apply]: `Mathlib/Analysis/Normed/Lp/Matrix.lean:40` (Matrix.ofLp_toLpLin): `Matrix.toLin' A` applies a `Matrix` lemma to `A : Matrix …`; it can be written `A.toLin'`.

### R1

- [0] `Mathlib/Analysis/Matrix/Spectrum.lean:40` (advisory): `Matrix.spectrum_toLpLin` is unnecessarily restricted by the surrounding `[RCLike 𝕜]` variables, even though the statement and proof only use the algebra equivalence behind `toLpLin`; this prevents using the lemma for matrices over an arbitrary commutative ring.
  -> State `spectrum_toLpLin` in a generic commutative-ring section, e.g. with `{R : Type*} [CommRing R] {A : Matrix n n R}`, and prove it via `AlgEquiv.spectrum_eq (Matrix.toLpLinAlgEquiv p) _`.
- [1] `Mathlib/Analysis/Normed/Lp/Matrix.lean:78` (advisory): `Matrix.toLpLinSymm_pow` uses a camel-case `Symm` component, while the surrounding API names lemmas about `(toLpLin ...).symm` with an underscore, as in `toLpLin_symm_id`.
  -> Rename `toLpLinSymm_pow` to `toLpLin_symm_pow`.

### R2

- [0] `Mathlib/Analysis/Matrix/Spectrum.lean:40` (advisory): `Matrix.spectrum_toLpLin` is stated only under the surrounding `RCLike 𝕜` assumptions, but the result is purely algebraic and the proof only needs the algebra equivalence between matrices and endomorphisms.
  -> Generalize the theorem to an arbitrary commutative ring, e.g. `theorem spectrum_toLpLin {R : Type*} [CommRing R] {n : Type*} [Fintype n] [DecidableEq n] {A : Matrix n n R} (p : ENNReal) : spectrum R (toLpLin p p A) = spectrum R A := AlgEquiv.spectrum_eq (Matrix.toLpLinAlgEquiv p) _`.
- [1] `Mathlib/Analysis/Normed/Lp/Matrix.lean:78` (advisory): `Matrix.toLpLinSymm_pow` uses a capitalized `Symm` component, unlike its sibling `.symm` lemmas `toLpLin_symm_id` and `toLpLin_symm_comp` and the usual snake-case naming for `symm` lemmas.
  -> Rename `Matrix.toLpLinSymm_pow` to `Matrix.toLpLin_symm_pow`.

## PR 35807 (stratum A)

**TARGET v1935** `Mathlib/Topology/LocallyFinsupp.lean`
```
+Assign a function with locally finite support within `U` to a function in the subgroup.
+-/
+@[simps]
+def mk_of_mem' [AddGroup Y] (f : X → Y) (hf : f ∈ locallyFinsuppWithin.addSubgroup U) :
```
> 
```suggestion
def mk_of_mem_addSubgroup [AddGroup Y] (f : X → Y) (hf : f ∈ locallyFinsuppWithin.addSubgroup U) :
```
Also, deprecate `mk_of_mem` to `mk_of_mem_addSubgroup`

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/Topology/LocallyFinsupp.lean:312` (Function.locallyFinsuppWithin.mk_of_mem'): `mk_of_mem'` is new, and `mk_of_mem` is declared at `Mathlib/Topology/LocallyFinsupp.lean:296`. `mk_of_mem'` concludes `locallyFinsuppWithin U Y`; `mk_of_mem` concludes `locallyFinsuppWithin U Y`.

### R1

- [0] `Mathlib/Topology/LocallyFinsupp.lean:253` (advisory): `Function.locallyFinsuppWithin.addSubmonoid` and the pointwise-addition API built from it are stated with `[AddMonoid Y]`, but the carrier, zero closure, and addition closure only need `[AddZeroClass Y]` (the class required by `AddSubmonoid` itself).
  -> Lower `addSubmonoid`, `memAddSubmonoid`, `mk_of_mem`, the `Add` instance, and `coe_add` to `[AddZeroClass Y]`; keep only the `SMul ℕ`/`AddMonoid` structure at `[AddMonoid Y]` and lower `coe_zero` to `[Zero Y]`.
- [1] `Mathlib/Topology/LocallyFinsupp.lean:300` (advisory): The new `Zero (locallyFinsuppWithin U Y)` instance under `[AddMonoid Y]` duplicates the existing instance under `[Zero Y]` at the top of the file.
  -> Remove this later `Zero` instance and use the existing `[Zero Y]` instance; `coe_zero` can be stated under `[Zero Y]`.
- [2] `Mathlib/Topology/LocallyFinsupp.lean:293` (advisory): The docstring for `Function.locallyFinsuppWithin.mk_of_mem` still says the input is a function in the subgroup, but the definition now takes membership in `locallyFinsuppWithin.addSubmonoid U`.
  -> Change this docstring to say “submonoid” instead of “subgroup”.
- [3] `Mathlib/Topology/LocallyFinsupp.lean:113` (advisory): `Function.locallyFinsupp.locallyFiniteSupport` proves membership in `Set.univ` via `mem_of_subset_of_mem (fun _ a ↦ a) trivial`, which is an unnecessarily indirect proof of `trivial`.
  -> Replace the proof with `fun z ↦ f.supportLocallyFiniteWithinDomain' z trivial`.

### R2

- [0] `Mathlib/Topology/LocallyFinsupp.lean:113` (advisory): `Function.locallyFinsupp.locallyFiniteSupport` proves membership in the univ domain via `mem_of_subset_of_mem (fun _ a ↦ a) trivial`, even though the second argument of `supportLocallyFiniteWithinDomain'` is just a proof of membership in `Set.univ`.
  -> Replace the proof by `fun z ↦ f.supportLocallyFiniteWithinDomain' z trivial`.
- [1] `Mathlib/Topology/LocallyFinsupp.lean:293` (advisory): The docstring for `Function.locallyFinsuppWithin.mk_of_mem` still says it assigns a function to the subgroup, but the declaration now takes membership in `locallyFinsuppWithin.addSubmonoid`.
  -> Change the docstring to say “additive submonoid” (or “addSubmonoid”) instead of “subgroup”.
- [2] `Mathlib/Topology/LocallyFinsupp.lean:300` (advisory): The `[AddMonoid Y] : Zero (locallyFinsuppWithin U Y)` instance duplicates the earlier `[Zero Y] : Zero (locallyFinsuppWithin U Y)` instance, adding another overlapping way to synthesize the same zero structure.
  -> Delete this later `Zero` instance and use the existing `[Zero Y]` instance; the following additive structure can still use `coe_zero`.
- [3] `Mathlib/Topology/LocallyFinsupp.lean:313` (advisory): The new public declaration `Function.locallyFinsuppWithin.mk_of_mem'` is a primed sibling of `mk_of_mem` whose distinguishing feature is that the membership proof is in `addSubgroup` rather than `addSubmonoid`. Mathlib names such variants by the differing hypothesis/object rather than by a bare prime.
  -> Rename it to a descriptive name such as `mk_of_mem_addSubgroup`, and update the `Neg`, `Sub`, and `SMul ℤ` instances to use the new name.
- [4] `Mathlib/Topology/LocallyFinsupp.lean:569` (advisory): `Function.locallyFinsuppWithin.restrictMonoidHom` still requires `[AddCommGroup Y]`, but after this PR the source and target only need the newly available `AddMonoid` structure, and the proof uses only zero and addition.
  -> Weaken `restrictMonoidHom` and its simp lemma `restrictMonoidHom_apply` to `[AddMonoid Y]`; while doing so, update the docstring from “group morphism” to “monoid morphism”.
- [5] `Mathlib/Topology/LocallyFinsupp.lean:586` (advisory): `Function.locallyFinsuppWithin.restrictLatticeHom` still requires `[AddCommGroup Y]`, but its construction only uses `restrict` and the lattice operations; the existing lattice instance for `locallyFinsuppWithin` needs only `[Zero Y] [Lattice Y]`.
  -> Weaken `restrictLatticeHom` and `restrictLatticeHom_apply` to `[Zero Y] [Lattice Y]`.

## PR 36355 (stratum A)

**TARGET v2081** `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean`
```
+  congr 1 with a : 1
+  rw [integral_smul_measure, integral_dirac, Measure.sum_smul_dirac, measureReal_def]
+
+theorem integral_countable (f : X → E) {s : Set X} (hs : s.Countable) (hf : IntegrableOn f s μ) :
```
> ```suggestion
theorem setIntegral_countable (f : X → E) {s : Set X} (hs : s.Countable) (hf : IntegrableOn f s μ) :
```
and you can remove the prime from the name of the lemma above.

- fact 0 [Primed names beside their unprimed sibling]: `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:178` (MeasureTheory.integral_countable'): `integral_countable'` is new, and `integral_countable` is declared at `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:185`. `integral_countable'` concludes `∫ x, f x ∂μ = ∑' x, μ.real {x} • f x`; `integral_countable` concludes `∫ x in s, f x ∂μ = ∑' x : s, μ.real {(x : X)} • f x`.
- fact 1 [Where dot notation may apply]: `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:94` (MeasureTheory.Integrable.summable_of_dirac): `summable_of_dirac` concludes `Summable …` and is named beside that namespace; inside it, it is `Summable.of_dirac`.

### R1

- [0] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:201` (advisory): `integral_finset` is a moved public theorem, but its binder shape was changed from the existing API `integral_finset s f hf` to `integral_finset s hf` by making `f` implicit. This unnecessarily breaks callers for a declaration that is otherwise just being moved.
  -> Restore the explicit function argument: `theorem integral_finset (s : Finset X) (f : X → E) (hf : IntegrableOn f s μ) : ...`.
- [1] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:205` (advisory): `integral_fintype` is also a moved public theorem whose explicit `f` argument was dropped, changing the existing API from `integral_fintype f hf` to `integral_fintype hf` without a mathematical reason.
  -> Restore the explicit function argument, `theorem integral_fintype [Fintype X] (f : X → E) (hf : Integrable f μ) : ...`, and then revert the downstream use in `PMF.integral_eq_sum` to `rw [integral_fintype _ .of_finite]`.
- [2] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:66` (advisory): `Integrable.summable_integral` is named as if it summed the integrals of `f`, but its conclusion is summability of the integrals of `‖f‖`. Nearby API uses the phrase `summable_integral_norm` for this condition (`hasSum_integral_of_summable_integral_norm`, `integral_tsum_of_summable_integral_norm`, `integrableOn_iUnion_of_summable_integral_norm`).
  -> Rename it to `Integrable.summable_integral_norm` and update its two uses in this file.
- [3] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:35` (advisory): The documentation for `integral_sum_dirac_eq_tsum` contains malformed integral notation (`∫ x, f x, ∂...`) and the main-statements bullet states the equality in the opposite direction from the theorem named `_eq_tsum`.
  -> Rewrite the bullet, and the matching declaration docstring below, as `∫ x, f x ∂Measure.sum (fun i ↦ (c i) • .dirac (x i)) = ∑' i, (c i).toReal • f (x i)` with no comma before `∂`.

### R2

- [0] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:201` (blocking): `MeasureTheory.integral_finset` was moved but its explicit `f` argument was accidentally made implicit, so existing calls of the old API such as `integral_finset s f hf` no longer elaborate.
  -> Restore the moved theorem's old explicit binder: `theorem integral_finset (s : Finset X) (f : X → E) (hf : IntegrableOn f s μ) : ...`.
- [1] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:205` (blocking): `MeasureTheory.integral_fintype` was moved but its explicit `f` argument was accidentally made implicit, breaking the pre-existing call shape `integral_fintype f hf` (the PR even has to change `PMF.integral_eq_sum` for this).
  -> Restore the explicit function binder, i.e. declare `theorem integral_fintype [Fintype X] (f : X → E) (hf : Integrable f μ) : ...`, and update the PMF proof back to `rw [integral_fintype _ .of_finite]`.
- [2] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:159` (advisory): `MeasureTheory.hasSum_integral_sum_dirac` assumes finite weights and summability of the weighted norms, but the HasSum conclusion only needs `Integrable f (Measure.sum (fun i ↦ (c i) • .dirac (x i)))`; the current hypotheses unnecessarily exclude integrable cases with infinite coefficients at zeros and also retain an unnecessary `[Countable ι]`.
  -> State the core lemma with the weaker hypothesis `(hf : Integrable f (Measure.sum (fun i ↦ (c i) • .dirac (x i))))`, drop `hc`, the summability assumption, and add `omit [Countable ι] in`; derive the summability-facing form as a corollary if desired.
- [3] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:167` (advisory): `MeasureTheory.integral_sum_dirac_eq_tsum` has the same avoidable `hc` and norm-summability assumptions: the equality follows from the weaker integrability hypothesis, with no countability assumption on the index type.
  -> Change the theorem to take `(hf : Integrable f (Measure.sum (fun i ↦ (c i) • .dirac (x i))))` and prove it from the generalized `hasSum_integral_sum_dirac`; users with the present hypotheses can pass `integrable_sum_dirac hc hf`.
- [4] `Mathlib/MeasureTheory/Integral/Bochner/SumMeasure.lean:35` (advisory): The documentation for `integral_sum_dirac_eq_tsum` contains malformed integral notation (for example `∫ x, f x, ∂...`), and the module overview also has a malformed `∫ f x ∂μ i` display.
  -> Correct the displayed formulas to valid notation, e.g. `∫ x, f x ∂Measure.sum (fun i ↦ (c i) • .dirac (x i)) = ∑' i, (c i).toReal • f (x i)` and `∫ x, f x ∂μ i`.

## PR 37009 (stratum B)

- fact 0 [Where dot notation may apply]: `Mathlib/Algebra/Algebra/StrictPositivity.lean:79` (IsStrictlyPositive.isStrictlyPositive_of_subsingleton): `isStrictlyPositive_of_subsingleton` concludes `IsStrictlyPositive …` and is named beside that namespace; inside it, it is `IsStrictlyPositive.of_subsingleton`.

### R1

- [0] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/Basic.lean:749` (blocking): `IsUnit.cfcSqrt` was changed so that it no longer has an `IsUnit a` hypothesis, even though it remains in the `IsUnit` namespace; this needlessly breaks the existing API/dot-notation theorem and makes the name misleading.
  -> Restore the old signature `lemma _root_.IsUnit.cfcSqrt (a : A) (ha_unit : IsUnit a) (ha : 0 ≤ a := by cfc_tac) : IsUnit (sqrt a)`. If a strict-positivity convenience theorem is wanted, put it under `IsStrictlyPositive` or use `ha.sqrt.isUnit`.
- [1] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/RingInverseOrder.lean:31` (advisory): `CFC.antitoneOn_ringInverse` reproves the unit inverse antitonicity theorem that already exists as `CStarAlgebra.inv_le_inv`.
  -> Lift the two strictly positive operands to units and invoke `CStarAlgebra.inv_le_inv`, rewriting `Ring.inverse` with `Ring.inverse_unit`, instead of the current custom `conjSqrt`/CFC argument.
- [2] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/Basic.lean:765` (advisory): `CFC.inverse_rpow` unnecessarily assumes `x ≠ 0`; the formula also holds for `x = 0`.
  -> Remove the `hx : x ≠ 0` argument, split on `x = 0`, prove the zero case with `rpow_zero` and `Ring.inverse_one`, and keep the current proof in the nonzero case.
- [3] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/ConjSqrt.lean:86` (advisory): `CFC.conjSqrt_one` assumes `IsStrictlyPositive c`, but the identity only needs `0 ≤ c`.
  -> Weaken the hypothesis to `(hc : 0 ≤ c := by cfc_tac)` and update positional call sites that pass strict positivity proofs to pass `.nonneg`.
- [4] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/ConjSqrt.lean:39` (advisory): `CFC.conjSqrt_apply` is the projection/apply lemma for a bundled continuous linear map, but it is not marked `[simp]`.
  -> Add the `[simp]` attribute to `conjSqrt_apply`.
- [5] `Mathlib/Algebra/Group/Units/Defs.lean:542` (advisory): `IsUnit.mul_iff₃` manually constructs units even though the existing lemmas `Units.isUnit_mul_units` and `Units.isUnit_units_mul` give the result directly; it also omits the additive counterpart expected for this multiplicative units API.
  -> Replace the proof by rewriting with `ha.unit_spec`, `hc.unit_spec`, `Units.isUnit_mul_units`, and `Units.isUnit_units_mul`, and add `@[to_additive (attr := grind =)]`.
- [6] `Mathlib/Algebra/Algebra/StrictPositivity.lean:108` (advisory): `isStrictlyPositive_iff_conjugate_of_isSelfAdjoint` manually proves the inverse direction, but it is exactly `IsUnit.isStrictlyPositive_star_right_conjugate_iff` after rewriting `star b = b`.
  -> Replace the proof with `simpa [hb₂.star_eq] using hb.isStrictlyPositive_star_right_conjugate_iff (a := a)`.
- [7] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/ConjSqrt.lean:58` (advisory): `CFC.conjSqrt_ringInverse_conjSqrt` and its sibling repeat rpow calculations to prove `sqrt (Ring.inverse c) * sqrt c = 1`, even though the file already has the canonical lemma `sqrt_ringInverse`.
  -> Use `sqrt_ringInverse` together with `Ring.inverse_mul_cancel`/`Ring.mul_inverse_cancel` (or prove the second inverse lemma from the first) instead of duplicating the rpow calculation in both proofs.

### R2

- [0] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/Basic.lean:749` (blocking): `IsUnit.cfcSqrt` was changed so it no longer takes an `IsUnit a` hypothesis, despite being the existing `IsUnit`-namespace API. This breaks existing dot-notation uses such as `ha_unit.cfcSqrt a ha_nonneg` and duplicates the strict-positivity route already available via `IsStrictlyPositive.sqrt.isUnit`.
  -> Restore the old signature `(a : A) (ha_unit : IsUnit a) (ha : 0 ≤ a := by cfc_tac) : IsUnit (sqrt a)` and prove it from `isUnit_sqrt_iff`; keep the new strict-positivity iff as a separate lemma if desired.
- [1] `Mathlib/Algebra/Algebra/StrictPositivity.lean:80` (advisory): `IsStrictlyPositive.isStrictlyPositive_of_subsingleton` repeats the namespace in the leaf name, giving the fully qualified name `IsStrictlyPositive.isStrictlyPositive_of_subsingleton`.
  -> Rename it to `IsStrictlyPositive.of_subsingleton` by declaring it as `lemma of_subsingleton ...` inside the `IsStrictlyPositive` namespace.
- [2] `Mathlib/Algebra/Group/Units/Defs.lean:542` (advisory): `IsUnit.mul_iff₃` is a generic multiplicative units lemma but lacks the additive counterpart that the surrounding `IsUnit` API provides via `to_additive`, and its proof manually constructs units instead of using the existing `Units.isUnit_units_mul`/`Units.isUnit_mul_units` lemmas.
  -> Add `to_additive` and replace the proof with the existing units-multiplication API, e.g. `@[to_additive (attr := grind =), grind =] ... := by obtain ⟨u, rfl⟩ := ha; obtain ⟨v, rfl⟩ := hc; simp only [Units.isUnit_units_mul, Units.isUnit_mul_units]`.
- [3] `Mathlib/Algebra/Algebra/StrictPositivity.lean:108` (advisory): `isStrictlyPositive_iff_conjugate_of_isSelfAdjoint` reproves cancellation by `Ring.inverse`, but it is exactly the existing `IsUnit.isStrictlyPositive_star_right_conjugate_iff` after rewriting `star b = b`.
  -> Replace the proof with `simpa [hb₂.star_eq] using hb.isStrictlyPositive_star_right_conjugate_iff (a := a)`.
- [4] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/ConjSqrt.lean:39` (advisory): `CFC.conjSqrt_apply` is the projection/application lemma for the new bundled continuous linear map, but it is not marked `[simp]`, so users must unfold it manually in exactly the situations where `foo_apply` lemmas are normally simplified.
  -> Add the `[simp]` attribute to `conjSqrt_apply`.
- [5] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/ConjSqrt.lean:72` (advisory): `CFC.conjSqrt_conjSqrt_ringInverse` duplicates the proof of `CFC.conjSqrt_ringInverse_conjSqrt` with the same two square-root inverse calculations.
  -> Derive it from `conjSqrt_ringInverse_conjSqrt (Ring.inverse c) a` and rewrite `Ring.inverse_inverse hc.isUnit` instead of repeating the calculation.
- [6] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/RingInverseOrder.lean:37` (advisory): `CFC.antitoneOn_ringInverse` introduces `hcont`, but that local hypothesis is never used in the proof.
  -> Delete the unused `have hcont : ContinuousOn ...` block.
- [7] `Mathlib/Analysis/SpecialFunctions/ContinuousFunctionalCalculus/Rpow/RingInverseOrder.lean:71` (advisory): `CFC.convexOn_ringInverse` introduces `zpos`, a duplicate of `hz`, and never uses it.
  -> Remove the redundant `have zpos : IsStrictlyPositive z := by grind` line.
