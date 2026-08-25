# Interventions review digest

113 interventions | judgeable 78 | outcomes {'adopted': 31, 'unknown': 55, 'partially_adopted': 12, 'dropped': 15}

## pr33421_i01  [V3/scope/adopted]
**ask**: In `Mathlib/Algebra/Order/Round.lean`, add/provide the lemma `round_eq_div` (the formula `round x = (⌊2 * x⌋ + 1) / 2`) as part of the `round` API.
**anchors**: Round.lean:45  (* = inferred)
> [V3] How about `round_eq_div`?

## pr33421_i02  [V2/duplication/unknown | NOT JUDGEABLE]
**ask**: Decide whether the specific `Tendsto` facts being proved for `round` are actually instances of a more general lemma that should already exist; if so, replace the ad-hoc proof steps in `tendsto_round_nhdsGE_pure` and similarly in the following theorem `tendsto_round_nhdsLT_pure_half_ceil` with an application of such a general lemma (and, if it does not exist, consider adding the general lemma instead of repeating this pattern).
**anchors**: Floor.lean:195  (* = inferred)
> [V2] Is this not something very general that should exist as a lemma? Same in the next theorem

## pr33421_i03  [V2/style/adopted]
**ask**: In `Mathlib/Algebra/Order/Floor/Ring.lean`, rewrite the proof of `theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) : k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1` to match the provided suggestion: after `rw [fract, mul_sub, sub_eq_iff_eq_add']`, use `refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩; rintro ⟨n, hn⟩; convert hn; have hk0 : 0 < (k : R) := zero_le_one.trans_lt hk; rw [floor_eq_iff, ← mul_le_mul_iff_right₀ hk0, ← mul_lt_mul_iff_right₀ hk0, hn]; simp [mul_add, hk]`.
**anchors**: Ring.lean:267, Ring.lean:267  (* = inferred)
> [V2] Better I think as ```suggestion theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :     k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by   rw [fract, mul_sub, sub_eq_iff_eq_add']   refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩   rintro ⟨

## pr33419_i01  [V3/naming/adopted]
**ask**: Rename the new lemma at `Mathlib/Data/Finset/Card.lean:574` to `card_sub_card_eq` and give it the statement `lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ...` (replacing the currently proposed name such as `eq_card_diff_of_sdiff`).
**anchors**: Card.lean:574  (* = inferred)
> [V3] I couldn't parse the name you proposed. ```suggestion lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ```

## pr33413_i01  [V2/style/unknown | NOT JUDGEABLE]
**ask**: Optionally use the `to_dual` attribute to generate both deprecated aliases at once (instead of writing both deprecated aliases manually), if that works with the automated removal of deprecated declarations.
**anchors**:   (* = inferred)
> [V2] Thanks :tada:  maintainer merge  (You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want, but I don't know if the automated removal of deprecated declarations works with that)

## pr33401_i01  [V2/style/adopted]
**ask**: In `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`, rewrite the proof of `Subgroup.closure_pow_le` using the suggested pattern-matching branches: replace the `0` case proof with `| 0 => by simp_all`, and replace the successor case proof (currently a `calc ...`) with `| n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem]`.
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | 0 => by simp_all ```
> [V2] ```suggestion   | n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem] ``` instead of the `calc ...`

## pr33400_i01  [V3/naming/unknown | NOT JUDGEABLE]
**ask**: Decide whether to rename the relevant identifier in `Analysis/SchwartzSpace` to use `contDiff` instead of its current name (the maintainer suggests renaming it to `contDiff`).
**anchors**:   (* = inferred)
> [V3] pre-existing: I think we should also rename this to `contDiff`

## pr33395_i01  [V4/naming/adopted]
**ask**: Rename the declaration `IntrinsicStar.starLinearEquiv_eq` to `IntrinsicStar.starLinearEquiv_eq_arrowCongr` (i.e. `theorem IntrinsicStar.starLinearEquiv_eq : ...` -> `theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ...`) at the hunk around the new `IntrinsicStar` lemma near line 126 in `Mathlib/Algebra/Star/LinearMap.lean`.
**anchors**: LinearMap.lean:126  (* = inferred)
> [V4] I like this the best. It's verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this. ```suggestion theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ```

## pr33376_i01  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: Clarify/confirm whether the newly introduced lemma is actually needed for this PR; if it is not used, remove it from the PR.
**anchors**:   (* = inferred)
> [V2] This is a reasonable lemma, but you're not using it for this PR, right?

## pr33373_i01  [V2/duplication/unknown]
**ask**: In `Mathlib/Analysis/Calculus/IteratedDeriv/Lemmas.lean` (section `shift_invariance`), prove `iteratedDeriv_comp_sub_const` by reusing the existing lemma `iteratedDeriv_comp_add_const` via simp: replace the current inductive proof with `by simp [sub_eq_add_neg, iteratedDeriv_comp_add_const]`.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simp [sub_eq_add_neg, iteratedDeriv_comp_add_const] ```
> [V2] Let's reuse the existing theorems:

## pr33373_i02  [V2/duplication/unknown]
**ask**: In `Mathlib/Analysis/Calculus/IteratedDeriv/Lemmas.lean` within `section shift_invariance`, rewrite the proof of `iteratedDeriv_comp_const_sub` to reuse existing theorems, specifically by replacing the current proof with:

`by
  simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using
    iteratedDeriv_comp_neg n (fun z => f (z + s))`

(i.e. derive the `s - z` statement via `iteratedDeriv_comp_neg` and `iteratedDeriv_comp_add_const`, rather than a bespoke argument).
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using     iteratedDeriv_comp_neg n (fun z => f (z + s)) ```
> [V2] Let's reuse the existing theorems:

## pr33362_i01  [V3/scope/adopted]
**ask**: Move the new auxiliary lemma so it is defined inside the `namespace Complex` block (i.e. place `Complex.schwarz_aux` a few lines later, under `namespace Complex`, rather than before it / outside it).
**anchors**: Schwarz.lean:40, Schwarz.lean:40  (* = inferred)
> [V3] Why not move these a few lines below so that it's on the `Complex` namespace?

## pr33357_i01  [V3/docs/unknown]
**ask**: Fix the typo in the PR description text (the GitHub PR description, not Lean code).
**anchors**:   (* = inferred)
> [V3] (there's a typo in your PR desc)

## pr33356_i01  [V2/style/adopted]
**ask**: In `Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean`, rewrite the proof of `hasDetPlusMinusOne_iff_abs_det` to follow the suggested skeleton: start with `refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩`, i.e. use `h.abs_det` for the forward implication and begin the reverse implication as `fun h ↦ ⟨?_⟩` (instead of a different structure).
**anchors**: ArithmeticSubgroups.lean:43  (* = inferred)
> [V2] ```suggestion   refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩ ```

## pr33349_i01  [V4/style/adopted | NOT JUDGEABLE]
**ask**: Decide whether to apply the indentation/style change in the `LinearOrderedAddCommGroupWithTop` class header (the extra indentation before `SubNegMonoid α, Nontrivial α where`) in `Mathlib/Algebra/Order/AddGroupWithTop.lean` at the declaration `class LinearOrderedAddCommGroupWithTop`.
**anchors**: AddGroupWithTop.lean:41  (* = inferred)
> [V4] I don't think there is consensus here?

## pr33349_i02  [V2/style/unknown]
**ask**: In `Mathlib/Algebra/Order/AddGroupWithTop.lean` around the lemmas introduced near line ~140, reorder the new simp lemmas so they follow the usual convention: define the `..._iff_left_of_ne_top` versions before the corresponding `..._iff_right_of_ne_top` versions, matching the pattern in the suggestion block for `add_le_add_iff_left_of_ne_top`, `add_le_add_iff_right_of_ne_top`, `add_lt_add_iff_left_of_ne_top`, `add_lt_add_iff_right_of_ne_top` (and similarly for any analogous pairs added in the same area).
**anchors**: AddGroupWithTop.lean:140  (* = inferred)
> [V2] ```suggestion @[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c :=   (add_left_strictMono_of_ne_top _ h).le_iff_le  @[simp] lemma add_le_add_iff_right_of_ne_top {a b c : α} (h : a ≠ ⊤) : a + b ≤ a + c ↔
> [V2] Same here

## pr33345_i01  [V3/docs/adopted]
**ask**: Fix the typo in the docstring immediately above the `instance : Add (ArchimedeanClass R)` so it reads `/-– Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/` (i.e. change `Multipilication` -> `Multiplication`).
**anchors**: Archimedean.lean:72  (* = inferred)
> [V3] Probabily a good idea to fix that simultaneousily ```suggestion /-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/ ```

## pr33343_i01  [V3/style/adopted]
**ask**: In theorem `stdPart_nonneg`, in the `mk x = 0` branch after `rw [stdPart, dif_pos hx.ge]`, replace the proof-golfed `apply map_nonneg; assumption` with an explicit `exact map_nonneg _ h` (i.e. use the suggestion block `exact h`-style explicitness rather than `assumption`).
**anchors**: StandardPart.lean:402, StandardPart.lean:402  (* = inferred)
> [V3] ```suggestion     exact h ``` I think it is better to be explicit here, especially when it is not syntactically eq

## pr33337_i01  [V3/naming/partially_adopted]
**ask**: Rename the theorem `orthogonalProjection_coe_eq_linearProjOfIsCompl` to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` in `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean` (around line 191), updating its declaration line accordingly.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] : ```

## pr33337_i02  [V3/naming/dropped]
**ask**: Rename the lemma `starProjection_coe_eq_isCompl_projection` to `toLinearMap_starProjection_eq_isComplProjection` (i.e., change the theorem declaration header to `theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] :`).
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] : ```

## pr33333_i01  [V4/style/dropped]
**ask**: Refactor the proof of `theorem floor_pi_eq_three : ⌊π⌋ = 3` in `Mathlib/Analysis/Real/Pi/Bounds.lean` (around line 223) to use `rw [Int.floor_eq_iff]` followed by `grind [pi_gt_three, pi_lt_four]`, i.e.
```
theorem floor_pi_eq_three : ⌊π⌋ = 3 := by
  rw [Int.floor_eq_iff]
  grind [pi_gt_three, pi_lt_four]
```
Adopt this as a possible middle-ground proof style compared to the existing `Int.floor_eq_iff.mpr`/`exact_mod_cast`/`norm_num` versions.
**anchors**: Bounds.lean:223, Bounds.lean:223  (* = inferred)
> [V4] Thanks! I'm not sure if I prefer those, though (same with the other). I'll wait for another opinion.
> [V4] I don't have a strong preference. But would this be a middle ground? ```suggestion theorem floor_pi_eq_three : ⌊π⌋ = 3 := by   rw [Int.floor_eq_iff]   grind [pi_gt_three, pi_lt_four] ```

## pr33333_i02  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: If you want to add a similar result for `exp 1`, use the existing bounds in `Mathlib.Analysis.Complex.ExponentialBounds` rather than introducing new bounds in `Mathlib/Analysis/Real/Pi/Bounds.lean`.
**anchors**:   (* = inferred)
> [V2] Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.

## pr33332_i01  [V1/style/unknown]
**ask**: In `SimpleGraph.adj_of_mem_walk_support` (in `Combinatorics/SimpleGraph/Connectivity/Connected.lean`), change the pattern binder `| @cons u v w h p ih =>` to `| cons h p ih =>` since the explicit names `u v w` are no longer used.
**anchors**: Connected.lean:252, Connected.lean:248*  (* = inferred)
> [V1] The names aren't used anymore ```suggestion   | cons h p ih => ```

## pr33328_i01  [V4/scope/partially_adopted | NOT JUDGEABLE]
**ask**: Decide whether to make this simp-lemma style change (using `self_mem_Ici` etc., and the broader refactor from `x ∈ Ixx a b ↔ False` to `x ∉ Ixx a b`) in this PR or to defer it / apply it consistently across other analogous interval lemmas elsewhere; i.e. justify or adjust the scope so it isn’t only changed here in `Mathlib/Order/Interval/Set/Basic.lean` (notably in `theorem Ici_subset_Ici` and similar `[simp]` lemmas).
**anchors**: Basic.lean:288, Basic.lean:316*  (* = inferred)
> [V4] Why this style change here and not in the other analogous places? (I'm neutral to the style changes, maybe they can be left to another PR)

## pr33321_i01  [V3/docs/dropped]
**ask**: Update the docstring attached to `IsMulIndecomposable.baseOf` (the `@[to_additive]` block) to complete the sentence starting “In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the …” (currently truncated).
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] ```suggestion In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ```

## pr33321_i02  [V3/style/unknown]
**ask**: In `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`, change the definition of `IsMulIndecomposable.baseOf` so that it is a set-comprehension of indices rather than relying on definitional equality between `Set ι` and `ι → Prop`: replace the current `def IsMulIndecomposable.baseOf ... : Set ι := IsMulIndecomposable v {i | 1 < f (v i)}` with `def IsMulIndecomposable.baseOf ... : Set ι := {j | IsMulIndecomposable v {i | 1 < f (v i)} j}`.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] Isn't this abusing the defeq between predicates and sets? ```suggestion def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=   {j | IsMulIndecomposable v {i | 1 < f (v i)} j} ```

## pr33321_i03  [V3/docs/adopted | NOT JUDGEABLE]
**ask**: In `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`, adjust the implementation details/docs and/or the development so that the proof explicitly uses (and provides) a set of ordered coefficients, despite the ultimate existence statement not requiring ordered coefficients.
**anchors**: BaseExists.lean:1  (* = inferred)
> [V3] ```suggestion The proof needs a set of ordered coefficients, even though the ultimate existence statement does ```

## pr33316_i01  [V3/naming/adopted | NOT JUDGEABLE]
**ask**: Decide whether the remaining/canonical name for the scalar product as a sesquilinear form should avoid non-ASCII characters, and if so, rename/choose an ASCII declaration name instead of a non-ASCII one (the maintainer notes the alternative name is more readable and that non-ASCII in declarations is generally discouraged).
**anchors**: RiemannLebesgueLemma.lean:199*, Adjoint.lean:247*, Adjoint.lean:577*, Basic.lean:120*, CanonicalTensor.lean:32*, Symmetric.lean:63*, CharacteristicFunction.lean:66*, CharacteristicFunction.lean:155*, CharacteristicFunction.lean:238*, ComplexMGF.lean:320*  (* = inferred)
> [V3] Getting rid of the duplication is fine, but the other name comes off as more readable to me. I thought using non-ASCII characters in declarations was generally discouraged.

## pr33310_i01  [V2/style/partially_adopted]
**ask**: In `Mathlib/RingTheory/WittVector/Complete.lean`, avoid defining the ring isomorphism `quotientPEquiv` via a tactic proof that rewrites the quotient ideal. Instead: (1) introduce an auxiliary lemma `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` (keeping `ker` on the LHS); (2) use `Ideal.quotEquivOfEq ker_constantCoeff.symm` composed with `RingHom.quotientKerEquivOfSurjective` (with a lemma `constantCoeff_surjective : Function.Surjective (constantCoeff : 𝕎 k → k)` stated as `fun r ↦ ⟨teichmuller p r, rfl⟩`) to define `quotientPEquiv : 𝕎 k ⧸ Ideal.span {(p : 𝕎 k)} ≃+* k`; and (3) add the definitional simp lemma `@[simp] lemma quotientPEquiv_mk (x : 𝕎 k) : quotientPEquiv (Quot.mk _ x) = constantCoeff x := rfl` (which relies on using `Ideal.quotEquivOfEq` rather than rewriting). Also move `constantCoeff_surjective` to the `Teichmuller` file.
**anchors**: Complete.lean:95, Complete.lean:95, Teichmuller.lean:125*  (* = inferred)
> [V2] It would be useful to introduce auxiliary lemmas: ```lean lemma ker_constantCoeff :     RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)} := by   ext   simp [mem_span_p_iff_coeff_zero_eq_zero]  -- this should be moved to the `Teichmuller` file lemma
> [V3] It seems more logical to me to keep `ker` in the LHS, as arguably the RHS is a "more basic term" as compared to the LHS.

## pr33305_i01  [V1/style/unknown]
**ask**: Shorten the overlong line in `Mathlib/GroupTheory/Submonoid/Inverses.lean` around line 20 (the doc/file reference to `Mathlib/Algebra/Group/Submonoid/Pointwise.lean`) by breaking it across lines so it satisfies the formatter/linter line-length check.
**anchors**:   (* = inferred)
> [V1] bors r- bors d+  There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36

## pr33302_i01  [V2/style/adopted]
**ask**: Change `CategoryTheory.ShiftedHom` in `Mathlib/CategoryTheory/Shift/ShiftedHom.lean` from a `def` to an `abbrev`, and then remove the `AddCommGroup` and `Module` instances that were defined specifically for this type. After this change, fix any broken proofs in downstream files (notably those currently using explicit `erw [Iso.homToEquiv_apply]`) by relying on `dsimp`-driven definitional unfolding instead; if any proof fix is nontrivial, it may be left as `sorry` for maintainer follow-up.
**anchors**: ShiftedHom.lean:13*, ShiftedHom.lean:29*, ShiftedHom.lean:181*, ShiftedHom.lean:184*, SmallShiftedHom.lean:209*, SmallShiftedHom.lean:219*, SmallShiftedHom.lean:239*, ExtClass.lean:81*, ShiftedHomOpposite.lean:139*  (* = inferred)
> [V2] Could you also make `ShiftedHom` an abbrev instead of a `def`. Then, the `AddCommGroup` and `Module` instances on this type could be removed. I have tried this, and overall, it improves automation. A few proofs should break, but the fix should be eas

## pr33296_i01  [V2/generalization/unknown]
**ask**: Add/land the cleaner, golfed, and more general proof/lemma suite for characterizing central endomorphisms of a free module as scalar maps, and adjust imports accordingly: (1) in `Mathlib/LinearAlgebra/FreeModule/Basic`, add `Module.End.mem_center_iff` with the provided proof and then define the center variants `Module.End.mem_submonoidCenter_iff` and `Module.End.mem_subsemigroupCenter_iff` by reuse of `Module.End.mem_center_iff`; (2) in `Mathlib/Algebra/Central/End`, strengthen the import to `Mathlib.Algebra.Central.Basic`, and add `Module.End.mem_subsemiringCenter_iff` (by `Module.End.mem_center_iff`) and the generalized `Module.End.mem_subalgebraCenter_iff` statement (as in the suggestion block).
**anchors**:   (* = inferred)
> [V2] I was just about to make this PR lol. Here is a cleaner proof. Along with a golf and a generalization for the instance. I can still make this PR, or you can just apply this, whatever :)  Note that you need to strengthen the import to `Mathlib.Algeb

## pr33294_i01  [V3/naming/adopted]
**ask**: Rename the lemma currently introduced as `IsFundamentalSequence.of_isNormal` (formerly `protected theorem IsNormal.isFundamentalSequence`) to use lowerCamelCase: `theorem isFundamentalSequence.of_isNormal {f : Ordinal → Ordinal} (hf : IsNormal f) ...` in `Mathlib/SetTheory/Cardinal/Cofinality.lean` around line 532.
**anchors**: Cofinality.lean:532  (* = inferred)
> [V3] ```suggestion theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f) ```

## pr33294_i02  [V2/style/adopted]
**ask**: In `Mathlib/SetTheory/Ordinal/Topology.lean` at the `enumOrd` `iSup` rewrite (around line 178), replace the rewrite `rw [IsNormal.map_iSup h g]`/`rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with `rw [h.map_iSup (bddAbove_of_small _)]`.
**anchors**: Topology.lean:178  (* = inferred)
> [V2] ```suggestion     rw [h.map_iSup (bddAbove_of_small _)] ``` no? 

## pr33287_i01  [V2/style/adopted]
**ask**: In `Arrows.toCompatible` (the `property` proof), replace the existing proof with the suggested simp proof:

```
property i j Z gi gj h := by
  simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]
```
**anchors**: IsSheafFor.lean:799  (* = inferred)
> [V2] ```suggestion   property i j Z gi gj h := by     simp [← FunctorToTypes.map_comp_apply, ← op_comp, h] ```
> [V2] ```suggestion       IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ```

## pr33285_i01  [V2/proof-golf/partially_adopted]
**ask**: In `Mathlib/Algebra/Module/Submodule/Map.lean`, golf the proof of `theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂)` to the suggested term-style proof:
```
    comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=
  fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2
```
(i.e. replace the current simp/rw-based proof with this direct lambda proof using `mem_comap.mpr` and `add_mem`).
**anchors**: Map.lean:595, Map.lean:597  (* = inferred)
> [V2] here's an even better golf ```suggestion     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=   fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2 ```

## pr33285_i02  [V2/proof-golf/unknown]
**ask**: In `Mathlib/RingTheory/Ideal/Cotangent.lean`, in the proof of `theorem cotangentEquivIdeal_symm_apply`, replace the current injectivity/`rw`/`ext` proof with one of the suggested shorter proofs, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (or alternatively `exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)`).
**anchors**: Cotangent.lean:151, Cotangent.lean:151  (* = inferred)
> [V2] or ```lean   simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff] ``` or ```lean   exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _) ```

## pr33283_i01  [V3/style/dropped]
**ask**: In `Mathlib/RingTheory/Polynomial/Chebyshev.lean` around line ~807, rewrite the `linear_combination` invocation(s) to put the hypothesis `h` on the same line as the tactic, i.e. change `linear_combination (norm := (push_cast; ring_nf))\n  h` to `linear_combination (norm := (push_cast; ring_nf)) h` (and similarly for the other analogous `linear_combination` occurrences the reviewer refers to by “and the other ones”).
**anchors**: Chebyshev.lean:807, Chebyshev.lean:807  (* = inferred)
> [V3] ```suggestion   linear_combination (norm := (push_cast; ring_nf)) h ``` I personally find this line break a bit weird but if you are attached to this style I don't particular want to block this PR because of it.
> [V3] (and the other ones)

## pr33268_i01  [V3/style/unknown]
**ask**: Reorder the lemmas so that the `max_left` and `max_right` declarations are placed immediately next to each other (right after one another) in `Mathlib/Order/BoundedOrder/Lattice.lean`.
**anchors**: Lattice.lean:26  (* = inferred)
> [V3] I think a more natural ordering is to put the max_left and max_right lemmas right after eachother.

## pr33267_i01  [V2/naming/dropped | NOT JUDGEABLE]
**ask**: No concrete change requested in this PR: maintainer notes (outside scope) that a use of a theorem could be replaced by `toDual_symm`, and something could be named `toDual_bot`, but does not ask to implement either change here.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] I feel like this theorem should not be applied; it can just be `toDual_symm`. But that is outside the scope of this PR.
> [V3] And this could just be called `toDual_bot`.

## pr33267_i02  [V3/style/unknown]
**ask**: In the section starting at the hunk around line 872, remove the `WithBot.` qualifier where it is redundant because the `WithBot` namespace is open (i.e., refer to declarations without the `WithBot.` prefix in that context).
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] Since the WithBot namespace is open, you can avoid the `WithBot.`

## pr33267_i03  [V3/style/unknown]
**ask**: Adjust the formatting/indentation of the declaration `protected def toDual : WithBot α ≃ WithTop αᵒᵈ := Equiv.refl _` (in the hunk around line 872) so that, since the whole statement fits on one line, it is written on a single line rather than split across multiple lines / with extra indentation.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] I think the indentation where the whole statement fits one  one line is actually preferred.

## pr33267_i04  [V2/docs/unknown]
**ask**: Update the docstring references in the `WithBot.toDual`/`WithTop.toDual` equivalence section to point to the current order-iso name: replace any mention of `WithBot.toDual_top_equiv` with `WithBot.toDualTopEquiv` (and similarly ensure the related reference uses `WithBot.toDualTopEquiv`).
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] ```suggestion See `WithBot.toDualTopEquiv` for the related order-iso. -/ ``` Looks like this was renamed at some point: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv

## pr33232_i01  [V3/style/unknown]
**ask**: In `Mathlib/Analysis/Distribution/TemperedDistribution.lean`, rewrite the `calc` proof of `theorem fourierTransformInv_toTemperedDistributionCLM_eq` to use the maintainer's suggested `calc` layout with explicit starting and ending `_` lines, i.e. change `𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc ...` into `𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc
  _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) := by
    congr; exact (fourier_fourierInv_eq f).symm
  _ = 𝓕⁻ (𝓕 (toTemperedDistributionCLM E F volume (𝓕⁻ f))) := by
    rw [fourierTransform_toTemperedDistributionCLM_eq]
  _ = _ := fourierInv_fourier_eq _`.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] style nit. I didn't actually test that it still elaborates properly with the starting and ending `_`, but I don't see which it shouldn't. ```suggestion     𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc   _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) :=

## pr33232_i02  [V3/docs/adopted]
**ask**: Add a docstring to the declaration `theorem fourierTransformInv_toTemperedDistributionCLM_eq` matching the suggested text: `/-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/` immediately before that theorem.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] ```suggestion /-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/ theorem fourierTransformInv_toTemperedDistributionCLM_eq (f : 𝓢(E, F)) : ```

## pr33208_i01  [V2/docs/unknown]
**ask**: Edit `IsMulIndecomposable_id_univ` to match the suggested signature by making `x` implicit and taking `hx : x ≠ 1` as the only explicit argument: change
`lemma IsMulIndecomposable_id_univ [Subsingleton Mˣ] (x : M) (hx : x ≠ 1) : ...`
to
`lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ...`.
Also improve the docstring of `Submonoid.closure_image_one_lt_and_isMulIndecomposable` to the more informative version given in the suggestion block (describing the full statement with hypotheses `S` linearly ordered cancellative, `f : M →* S`, and `v : ι → M`), and add a corresponding docstring for the additive version generated by `@[to_additive]` (currently missing its own docstring).
**anchors**: Indecomposable.lean:1, Indecomposable.lean:1*  (* = inferred)
> [V2] ```suggestion lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ```
> [V3] I found the statement a bit hard to parse, so I found myself wanting a more informative docstring. Please check that my interpretation is correct, or otherwise improve it.  ```suggestion /-- This is [serre1965](Ch. V, §9, Lemma 2) and may be used to 

## pr33207_i01  [V4/scope/unknown | NOT JUDGEABLE]
**ask**: Connect the new/rewritten `Mathlib/Order/Argmin.lean` material to the existing `Minimal` / `MinimalFor` API (and, if feasible, also consider connecting to `List.argmin`). Also decide whether using the new `Function.argmin`-style definition is actually easier than obtaining a minimizer via `Set.Finite.exists_minimal` (i.e. whether this definition should be preferred over a `choice`/`obtain`-based approach).
**anchors**: Argmin.lean:1  (* = inferred)
> [V4] Is it definitely easier to use this definition rather than using choice/`obtain` on `Set.Finite.exists_minimal`?   It would be nice to connect the material here to the `Minimal`/`MinimalFor` API (the latter of which isn't quite complete at the mome

## pr33203_i01  [V3/naming/dropped | NOT JUDGEABLE]
**ask**: Decide whether the name `Rat.intEquiv` / `Rat.IsIntegralClosure.intEquiv` should be changed to something that better reflects its type and meaning (a ring equivalence `R ≃+* ℤ` for an integral closure `R` of `ℤ` in `ℚ`), since the current name is misleading (it sounds like a bijection `ℚ ≃ ℤ`).
**anchors**: HeightOneSpectrum.lean:62, HeightOneSpectrum.lean:70, HeightOneSpectrum.lean:103*  (* = inferred)
> [V3] I'd just like to mention that this is not at all what I'd expect from something called `Rat.intEquiv`! I was expecting some sort of bijection `ℚ ≃ ℤ` instead.

## pr33201_i01  [V2/generalization/partially_adopted]
**ask**: Replace the specialized proofs about `Truncated 2` homotopy categories with the existing general instances/lemmas by (1) adding a general instance in `Mathlib/CategoryTheory/Category/ReflQuiv.lean` (around line 312) giving `Subsingleton (x ⟶ y)` in `FreeRefl V` under `[ReflQuiver V] [Unique V] [∀ x y, Subsingleton (x ⟶ y)]` (as in the provided code snippet), and (2) adding an instance in `Mathlib/AlgebraicTopology/SimplicialSet/CompStructTruncated.lean` that `X.Edge x y` is subsingleton assuming `[Subsingleton (X _⦋1⦌₂)]` (as in the provided snippet). Then in `Mathlib/AlgebraicTopology/SimplicialSet/HomotopyCat.lean`, rewrite the `subsingleton_hom` instance for `X.HomotopyCategory` to use `CategoryTheory.Quotient.instSubsingletonHom` via the `OneTruncation₂` instances (exactly as in the suggested `subsingleton_hom` code). Also, define `instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory := ... CategoryTheory.Quotient.instUnique _` and redefine `isTerminal` to use `Cat.isTerminalOfUniqueOfIsDiscrete` with a local `IsDiscrete` instance `{ eq_of_hom := by subsingleton }` (as in the suggestion block), instead of the current specialized constructions.
**anchors**: HomotopyCat.lean:455, HomotopyCat.lean:455  (* = inferred)
> [V2] I feel like this proof is too specialized for the homotopy category. Mathlib arleady knows that quotient categories of categories with unique objects and subsingleton homs have subsingleton homs, and that free categories on quivers with unique object
> [V2] Same here: we already have `Cat.isTerminalOfUniqueOfIsDiscrete`: ```suggestion instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory :=    letI : Unique (OneTruncation₂ X) := inferInstanceAs (Unique (X _⦋0⦌₂))   CategoryTh

## pr33201_i02  [V2/duplication/dropped]
**ask**: Remove the new instance `instance {J' : Type*} [Category J'] (F : J ⥤ J') : ((Functor.whiskeringLeft J J' C).obj F).Monoidal := ...` and instead use the existing (more general) declaration `CategoryTheory.Functor.Monoidal.whiskeringLeft` from `Mathlib/CategoryTheory/Monoidal/FunctorCategory.lean`.
**anchors**: FunctorCategory.lean:192  (* = inferred)
> [V2] This seems to be a (less general) duplicate of [CategoryTheory.Functor.Monoidal.whiskeringLeft](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Monoidal/FunctorCategory.html#CategoryTheory.Functor.Monoidal.whiskeringLeft)

## pr33201_i03  [V3/other/adopted]
**ask**: Add the missing `Full` and `Faithful` instances corresponding to the `FullyFaithful` definitions for the currying functors. Concretely: in `Mathlib/CategoryTheory/Functor/Currying.lean`, after `def fullyFaithfulCurry`, add `instance : (curry : (C × D ⥤ E) ⥤ C ⥤ D ⥤ E).Full := fullyFaithfulCurry.full` and `instance : (curry : (C × D ⥤ E) ⥤ C ⥤ D ⥤ E).Faithful := fullyFaithfulCurry.faithful`; and in `Mathlib/CategoryTheory/Functor/CurryingThree.lean`, after `def fullyFaithfulCurry₃`, add `instance : (curry₃ : (C₁ × C₂ × C₃ ⥤ E) ⥤ (C₁ ⥤ C₂ ⥤ C₃ ⥤ E)).Full := fullyFaithfulCurry₃.full` and `instance : (curry₃ : (C₁ × C₂ × C₃ ⥤ E) ⥤ (C₁ ⥤ C₂ ⥤ C₃ ⥤ E)).Faithful := fullyFaithfulCurry₃.faithful`.
**anchors**: Currying.lean:110, Currying.lean:110, CurryingThree.lean:43, CurryingThree.lean:43  (* = inferred)
> [V3] Please add the corresponding `Full` and `Faithful` instances (we really need a way to automate adding those via an attribute we can put on a `FullyFaithful` definition!).
> [V3] Same  comment: please also add the `Full` and `Faithful` instances

## pr33200_i01  [V1/scope/unknown | NOT JUDGEABLE]
**ask**: Do not merge or resubmit this PR in its current form; remove all `sorry`s and all newly introduced `axiom`s from the codebase (i.e., replace them with actual proofs/definitions) and substantially reduce/split the changes into reviewable pieces before attempting a new submission.
**anchors**:   (* = inferred)
> [V1] The issue is nothing to do with the code of conduct. This PR is completely unsuitable for mathlib for multiple reasons. (a) it is far too long to review (b) it has axioms (c) it has sorries (d) it was written by an AI which seems to have no understan
> [V1] > no axioms  I encourage you to learn how to use `grep`, as you have in one file introduced 4 times as many axioms as we use in *all* of Mathlib.  I won't be engaging further and wasting my time.

## pr33198_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide on and apply a consistent naming scheme for both ω₁ and ℵ₁: if introducing `omega_one`/`aleph_one`, also rename the existing `omega0`/`aleph0` to `omega_zero`/`aleph_zero` (rather than mixing `omega0`/`aleph0` with `omega_one`/`aleph_one`).
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] I'm confused, you want to write `omega0` and `aleph0` and also `omega_one` and `alepg_one`? I'm virtually certain that if you asked on Zulip, the poll would go in favor of `omega_zero` too and `aleph_zero` too (at least, assuming votes from the same 

## pr33198_i02  [V4/other/unknown | NOT JUDGEABLE]
**ask**: Decide whether the lemma in the `ω` section of `Mathlib/SetTheory/Ordinal/Basic.lean` should remain asymmetric, and if so, avoid refactoring it into a symmetric statement; the asymmetry is meaningful.
**anchors**:   (* = inferred)
> [V4] Oh I see! Then I think the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.

## pr33198_i03  [V1/other/unknown | NOT JUDGEABLE]
**ask**: Fix the CI/build failure in this PR (see linked GitHub Actions log) before merging; do not proceed with bors until the build passes.
**anchors**: Basic.lean:760*  (* = inferred)
> [V1] The build is failing: https://github.com/leanprover-community/mathlib4/actions/runs/20436145675/job/58717788626#step:22:905 bors r- bors d+

## pr33190_i01  [V3/style/adopted]
**ask**: In `lemma eq_of_natDegree_lt_card_of_eval_eq` in `Mathlib/Algebra/Polynomial/Roots.lean` (around line 630), change the line `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf` to `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf` (i.e. make `hf` an explicit argument in the `apply` call, as in the suggestion block).
**anchors**: Roots.lean:630  (* = inferred)
> [V3] only because I was confused why `hf` wasn't an explicit argument, and then after looking above, I realized it is. ```suggestion   apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf ```

## pr33183_i01  [V3/style/unknown]
**ask**: (1) In `instance monoidalCategoryStruct : MonoidalCategoryStruct (∀ i, C i)`, rewrite the field assignments in pointwise form exactly as in the suggestion block: `tensorObj X Y i := X i ⊗ Y i`, `tensorHom f g i := f i ⊗ₘ g i`, `whiskerLeft X _ _ f i := X i ◁ f i`, `whiskerRight f Y i := f i ▷ Y i`, `tensorUnit i := 𝟙_ (C i)` (i.e. avoid `fun ... ↦ ...` wrappers). (2) Update the module docstring line beginning `/-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with` to use the suggested wording prefix (i.e. start the docstring with that exact sentence fragment). (3) In the definition of the `closed` structure (the `MonoidalClosed` instance/field), define it via an explicit record literal exactly as suggested: `closed X := { rightAdj := ihom X, adj.unit := closedUnit X, adj.counit := closedCounit X }`.
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   tensorObj X Y i := X i ⊗ Y i   tensorHom f g i := f i ⊗ₘ g i   whiskerLeft X _ _ f i := X i ◁ f i   whiskerRight f Y i := f i ▷ Y i   tensorUnit i := 𝟙_ (C i) ```
> [V3] ```suggestion /-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ```
> [V3] ```suggestion   closed X := {     rightAdj := ihom X     adj.unit := closedUnit X     adj.counit := closedCounit X } ```

## pr33169_i01  [V2/style/partially_adopted]
**ask**: In `Mathlib/LinearAlgebra/Matrix/FixedDetMatrices.lean` at the `intro B n; induction n with` proof (around lines 228–229), revert the whitespace/line-break change for the `| succ n hn =>` case: keep it as a multi-line branch with `| succ n hn =>` on its own line and the following `simpa only [...]` formatted as in the suggestion block, including spacing `(n : ℤ)` and breaking the `simpa only` list so `prop_red_T hS hT` is on the next line.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V4] Please revert this one; I'm not convinced it's better.
> [V2] ```suggestion   | succ n hn =>     simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,       prop_red_T hS hT] ```

## pr33158_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No changes requested (maintainer approved and merged via `bors r+`).
**anchors**:   (* = inferred)
> [V4] I'm not so sure that we will ever care about Stieltjes measures on the empty space, but in any case I agree this can't hurt. Thanks! bors r+

## pr33156_i01  [V3/docs/adopted]
**ask**: Add a missing doc-string for the newly introduced `optAttrArg` syntax in `Mathlib/Util/AddRelatedDecl.lean`.
**anchors**: AddRelatedDecl.lean:19*, AddRelatedDecl.lean:19*  (* = inferred)
> [V3] (Please add the missing doc-string, though.)

## pr33154_i01  [V3/docs/unknown | NOT JUDGEABLE]
**ask**: Update the documentation/comment around line 24 to also mention the `to_fun` attribute (i.e., include `to_fun` in whatever list/description is currently there).
**anchors**:   (* = inferred)
> [V3] Pre-existing: should line 24 also mention `to_fun`?

## pr33153_i01  [V2/docs/dropped | NOT JUDGEABLE]
**ask**: Clarify or point out the specific documentation change in the diff at the location being reviewed, since the maintainer cannot see any difference.
**anchors**:   (* = inferred)
> [V2] I can't see the difference here. 

## pr33152_i01  [V2/naming/dropped]
**ask**: Do not add the declaration `Meromorphic.meromorphicOn_univ`; instead use the existing `Meromorphic.meromorphicOn` (letting Lean infer `univ` when possible, or supplying the implicit argument manually when needed).
**anchors**: Basic.lean:562*  (* = inferred)
> [V2] I don't think we generally include the new declaration `Meromorphic.meromorphicOn_univ`. It would need to be protected if we did, but you should also just be able to use `Meromorphic.meromorphicOn`. When Lean can infer `univ`, it works, and when it c

## pr33151_i01  [V2/naming/adopted]
**ask**: Update `Mathlib/Tactic/Translate/ToDual.lean`'s `GuessName.abbreviationDict` so the to_dual name-guessing translates `succColimit` to `SuccLimit` (and analogously `predColimit` to `PredLimit`). Optionally, if all occurrences of `limit` that need translating are always preceded by `succ`/`pred`, consider instead using the `fixAbbreviations` dictionary to un-translate `colimit` to `limit` specifically in those cases.
**anchors**: ToDual.lean:181*, ToDual.lean:153*  (* = inferred)
> [V2] Is it true that all instances of the word `limit` that need to be translated are preceded by either `succ` or `pred`? In that case it may be better to use the fixAbbreviations dictionary to un-translate `colimit` to`limit` in these cases.  (I agree w
> [V2] In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.

## pr33150_i01  [V2/naming/adopted | NOT JUDGEABLE]
**ask**: Fix the `@[to_dual ...]` attribute so it generates the correct dual lemma name(s) for the affected declarations in `Mathlib/Order/SuccPred/Basic.lean` (section `Preorder` around the lemmas `le_succ_pred` and `pred_le_iff_le_succ`).
**anchors**: Basic.lean:828  (* = inferred)
> [V2] I think this generates the wrong dual name

## pr33149_i01  [V1/scope/unknown | NOT JUDGEABLE]
**ask**: Remove any new axioms introduced by this PR (i.e. do not add `axiom`/`constant` assumptions to Mathlib); in particular, refactor the new results such as `GalerkinLimit.smooth` so they are proved without introducing new axioms.
**anchors**:   (* = inferred)
> [V1] Mathlib has a no-axioms policy. Please don't introduce any new axioms.

## pr33149_i02  [V2/duplication/unknown | NOT JUDGEABLE]
**ask**: Replace any custom proof/lemma of Parseval's identity used in this PR with Mathlib's existing Parseval's identity lemma; if a specialized version (e.g. for the standard basis in ℝ^n) is genuinely needed, add that specialization as a lemma near the existing Parseval identity in Mathlib instead of re-proving it locally in this PR.
**anchors**:   (* = inferred)
> [V2] Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).

## pr33149_i03  [V3/other/unknown | NOT JUDGEABLE]
**ask**: Update the PR description to clearly disclose whether and how AI was used to generate the code (which parts, what prompts, and whether the author understands the mathematics). Remove any newly introduced axioms (do not add additional axioms). For any new definitions introduced in the PR (including around the main declaration `GalerkinLimit.smooth`), add basic supporting lemmas so the new API is maintainable.
**anchors**:   (* = inferred)
> [V3] Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) 

## pr33149_i04  [V4/other/unknown | NOT JUDGEABLE]
**ask**: Close the PR and request a complete rewrite before resubmission: (1) eliminate any axioms by either providing proofs/constructive definitions, deriving them from existing Mathlib results, or replacing them with `sorry` placeholders while developing; (2) remove definitions that are merely shorter names for existing Mathlib definitions (e.g. `fourier1D`, `smoothInTime`) by inlining them, only using `abbrev` sparingly if absolutely necessary for readability; (3) fix the definitions `fourierDecay` and `spectralNSResidual` (and hence `SolvesNavierStokes`) so they are not vacuously true, and carefully audit the rest of the PR’s definitions to avoid similar vacuity.
**anchors**:   (* = inferred)
> [V4] Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33146_i01  [V3/docs/adopted]
**ask**: Capitalize the first word in the docstring for `eq_whisker`: change `/-- postcompose an equation between morphisms by another morphism -/` to `/-- Postcompose an equation between morphisms by another morphism -/` at the comment immediately preceding `theorem eq_whisker`.
**anchors**: Basic.lean:223  (* = inferred)
> [V3] Might as well fix some capitalization. ```suggestion /-- Precompose an equation between morphisms by another morphism -/] ```

## pr33145_i01  [V2/duplication/unknown]
**ask**: Refactor the new dense-image bounds lemmas in `Mathlib/Topology/Order/IsLUB.lean` around line ~166 by (1) introducing more general lemmas
- `theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ...`
- `theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ...`
(as suggested), and (2) for the lower-bounds statement, reuse the upper-bounds proof via `OrderDual`, i.e. prove it by something like
`hS.continuous_upperBounds (α := αᵒᵈ) hf`
rather than duplicating the argument.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] ```suggestion theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] There's a trick you can use for this kind of thing by using the `OrderDual`. ```suggestion     lowerBounds (f '' S) = lowerBounds (range f) :=   hS.continuous_upperBounds (α := αᵒᵈ) hf ```

## pr33145_i02  [V2/duplication/unknown]
**ask**: Refactor the dense-set supremum/infimum results by introducing general lemmas `theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ...` and `theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ...`, and then obtain the `ciInf` statement via order duality: replace the direct `ciInf` proof with the line `hS.ciSup (α := αᵒᵈ) hf h` (i.e. prove `ciInf` by applying `ciSup` to `αᵒᵈ`).
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup (α := αᵒᵈ) hf h ```

## pr33145_i03  [V2/duplication/unknown]
**ask**: Add lemmas `Dense.ciSup'` and `Dense.ciInf'` (with explicit parameters `{α : Type*} [TopologicalSpace α]`) and in the proof of the infimum variant use the duality rewrite `hS.ciSup' (α := αᵒᵈ) hf` to obtain `⨅ i, f i = ⨅ s : S, f s`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup' (α := αᵒᵈ) hf ```

## pr33145_i04  [V2/style/unknown]
**ask**: In the proof of the dense-set supremum lemma(s) (the `Dense.continuous_sup`/`Dense.continuous_sup'` development that follows the shown additions in `Mathlib/Topology/Order/IsLUB.lean`), rewrite the argument by first splitting on whether `BddAbove (range (fun x : S ↦ f x))`. Use the structure of the provided suggestion: `by_cases h : BddAbove (range (fun x : S ↦ f x))`; in the bounded case, finish via `hS.ciSup hf <| h.closure.mono ?_` and `simpa [← Function.comp_def, range_comp] using hf.range_subset_closure_image_dense hS`; in the unbounded case, derive `¬ BddAbove (range f)` and close with `simp [ciSup_of_not_bddAbove, this, h]`, using `contrapose h; exact h.mono fun _ ↦ by aesop`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] It's easier if you case split on whether the range of the function from the subtype is bounded above or not. ```suggestion   by_cases h : BddAbove (range (fun x : S ↦ f x))   · refine hS.ciSup hf <| h.closure.mono ?_     simpa [← Function.comp_def, r

## pr33145_i05  [V3/style/unknown | NOT JUDGEABLE]
**ask**: Rewrite the `iSup`/`iInf` equality declarations so the `:= by` line reads with the left-hand side first, i.e. state them in the form `⨆ s : S, f s = ⨆ i, f i := by` (and similarly for any analogous `iInf` statement), instead of the reversed equation.
**anchors**:   (* = inferred)
> [V3] I suggest turning the declarations involving `iSup` and `iInf` around so that they read: ```lean     ⨆ s : S, f s = ⨆ i, f i := by ``` instead.

## pr33144_i01  [V2/duplication/unknown]
**ask**: Remove the unused redundant eta-expanded lemmas `fun_deriv` and `fun_iterated_deriv` from `Analysis/Meromorphic/Basic` (only introduce such `fun_` wrapper lemmas when actually needed).
**anchors**:   (* = inferred)
> [V4] This PR itself it straightforward; the main question is whether we want it.
> [V2] @kebekus Thanks for the explanation! Let's only add `fun_` versions as needed then --- as these lemmas are unused, let's remove them. bors r+

## pr33141_i01  [V2/style/adopted]
**ask**: Add `(relevant_arg := X)` to the `@[to_additive]` attribute on every declaration in `RingTheory/Coalgebra/MonoidAlgebra.lean` that is being translated via `to_additive`, i.e. update `@[to_additive]` on `MonoidAlgebra.instCoalgebra`, `MonoidAlgebra.instIsCocomm`, `MonoidAlgebra.counit_single`, and `MonoidAlgebra.comul_single` so each has `@[to_additive (relevant_arg := X) ...]`.
**anchors**: MonoidAlgebra.lean:35  (* = inferred)
> [V2] I think you need the `(relevant_arg := X)` on all of the declarations in this file

## pr33137_i01  [V2/style/unknown]
**ask**: In `mapDomainNonUnitalAlgHom`, set `map_mul'` directly to `mapDomain_mul f` (i.e. replace the current `map_mul'` assignment with `map_mul' := mapDomain_mul f`).
**anchors**: Basic.lean:217  (* = inferred)
> [V2] ```suggestion   map_mul' := mapDomain_mul f ```

## pr33127_i01  [V2/docs/adopted]
**ask**: Remove the `example {n : ℕ} [NeZero n] (hn : 2 ≤ n) : (1 : Fin n).val = 1 := by ...` block (test code) from `Mathlib/Order/Interval/Finset/Fin.lean` near the start of the `/-! ### Perturbations of endpoints by one -/` section, or (if it is meant to stay) convert it into an explanatory comment at the top of that section.
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V2] I assume this is test code, and can be removed? ```suggestion ```
> [V3] This may be worth turning into a comment at the top of the section!

## pr33117_i01  [V2/style/partially_adopted]
**ask**: Use the new metaprogramming support via the `to_fun` attribute for the `Meromorphic` operation lemmas (e.g. `Meromorphic.neg`, `Meromorphic.add`, `Meromorphic.sum`, `Meromorphic.sub`, `Meromorphic.mul`, `Meromorphic.prod`, `Meromorphic.div`, `Meromorphic.pow`, `Meromorphic.zpow`, `Meromorphic.deriv`, `Meromorphic.iterated_deriv`): add `import Mathlib.Tactic.ToFun` (not `public`) to `Mathlib/Analysis/Meromorphic/Basic.lean`, and change the attribute on these lemmas from `@[fun_prop]` to `@[to_fun (attr := fun_prop)]` (as in the suggestion block).
**anchors**: Basic.lean:631, Basic.lean:8*  (* = inferred)
> [V2] There is some new metaprogramming that can help here: the `to_fun` attribute. To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).  ```suggestion @[to_fun (attr := fun_prop)] lemma neg (hf : Meromorphic

## pr33111_i01  [V3/naming/unknown | NOT JUDGEABLE]
**ask**: Decide on and apply a consistent naming scheme for the renamed injectivity lemmas: either rename the new lemma to `injective_of_eq_imp_le` (instead of `Function.Injective.of_eq_imp_le`) and/or rename the related lemma(s) similarly for consistency (notably `injective_of_lt_imp_ne` -> a consistent name such as `Function.Injective.of_lt_imp_ne`).
**anchors**:   (* = inferred)
> [V3] why not call it `injective_of_eq_imp_le`?
> [V3] You could deprecate it. Probably a good idea. ~~But I'd suggest keeping the theorem as is, just add the `@[deprecated Function.Injective.of_... (since := ...)]`.~~
> [V3] Meh, rename away. I only suggested it to keep things consistent. So let's keep things consistent and rename the others in a better way!

## pr33111_i02  [V2/proof-golf/unknown]
**ask**: In `Mathlib/Order/Monotone/Defs.lean`, reorder the new lemma `injective_of_eq_imp_le` to appear before the lemma currently being proved, then simplify the proof of the later lemma by replacing the current argument with either (1) `exact injective_of_eq_imp_le f fun {x y} ↦ not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x)` or (2) `grind [injective_of_eq_imp_le]`.
**anchors**:   (* = inferred)
> [V2] if you move the new lemma before this one, you could do ```suggestion   exact injective_of_eq_imp_le f fun {x y} ↦     not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x) ``` or ```suggestion   grind [injective_of_eq_imp_le] ```

## pr33111_i03  [V4/naming/unknown | NOT JUDGEABLE]
**ask**: Revise the PR title to more accurately reflect the change: it is not a weakening of the hypothesis of `injective_of_le_imp_le`, but rather adding a lemma that works in a more general setting.
**anchors**:   (* = inferred)
> [V4] The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.

## pr33107_i01  [V4/scope/unknown | NOT JUDGEABLE]
**ask**: Refactor `LinearMap.range` and `LinearMap.ker` so that they take an actual `LinearMap` argument (not a linear-map-as-a-class/morphism), after checking/confirming on Zulip that there are no objections to changing these definitions.
**anchors**:   (* = inferred)
> [V4] I think we should refactor the definitions of `LinearMap.range` and `LinearMap.ker` to take in an actual linear map and not a linear map class. That way, all of this comes for free. It'll also allow for dot notation, solve more of these issues, etc..
> [V4] @Timeroot yes, Monica is correct here. Unfortunately you are exposing a flaw that exists currently in the library. Help ripping it out is encouraged! For more information see the Zulip thread: [#mathlib4 > Mathlib's morphism hierarchy](https://leanpr

## pr33104_i01  [V3/style/unknown]
**ask**: Change the relevant `PseudoMetricSpace`-transfer definitions to use protected abbreviations with the following signatures:
- `protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ...`
- `protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ...`
**anchors**:   (* = inferred)
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ```
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ```

## pr33101_i01  [V3/scope/partially_adopted]
**ask**: Avoid duplicated `variable` declarations around `end Module.Dual` / `namespace LinearMap` by enclosing the earlier `variable` block in an explicit `section ... end` block (instead of leaving a stray `end` and then reintroducing the same `variable {K V₁ V₂ : Type*} [Field K] ...`), so the scope of the earlier variables is clearly delimited and later variables are not surprising.
**anchors**: Lemmas.lean:781, Lemmas.lean:780  (* = inferred)
> [V3] It looks like this duplicates the `variable`s.  Could you enclose the previous one in a `section`/`end` block, to avoid "surprises"?

## pr33098_i01  [V2/proof-golf/unknown]
**ask**: Use `grind` to shorten several lemmas in `Topology/MetricSpace/CoveringNumbers.lean`, and add supporting `grind` attributes so the proofs go through. Concretely: (1) add `attribute [grind .] finite_empty` (needed for `finite_minimalCover`) and `attribute [grind .] IsSeparated.empty` (needed for `isSeparated_maximalSeparatedSet`); (2) replace the proofs of `minimalCover_subset` with `by grind [minimalCover]` and `maximalSeparatedSet_subset` with `by grind [maximalSeparatedSet]`; (3) rename lemma statements to use `encard_...` names: change `lemma exists_set_encard_eq_coveringNumber ...` to `lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ...`, change the analogous packing lemma to `lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ...`, and change `lemma encard_le_of_isSeparated` to take argument name `h_subset : C ⊆ A`.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add ```lean attribute [grind .] finite_empty ``` but I think we should do that anyway. ```suggestion lemma minimalCover_subset : min
> [V2] This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add ```lean attribute [grind .] IsSeparated.empty ``` but I think we should do that anyway.  ```suggestion lemma maximalSe
> [V2] ```suggestion lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_le_of_isSeparated (h_subset : C ⊆ A) ```

## pr33098_i02  [V2/proof-golf/unknown]
**ask**: In the proof (in `Topology/MetricSpace/CoveringNumbers.lean`, around the added maximal-separated-set argument), refactor the `insert`/`by_contra` portion to use `Metric.isSeparated_insert_of_notMem` as in j-loreaux’s suggested golf: define `C := {x} ∪ maximalSeparatedSet ε A`, derive `hx_not_mem : x ∉ maximalSeparatedSet ε A`, prove `C ⊆ A ∧ IsSeparated ε C` via `isSeparated_insert_of_notMem hx_not_mem |>.mpr ⟨isSeparated_maximalSeparatedSet, ...⟩`, and then conclude using `encard_insert_of_notMem` and the existing `encard_le_of_isSeparated` contradiction chain.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`. ```lean   intro x hxA   by_contra! h_dist   let C :=

## pr33098_i03  [V2/style/adopted]
**ask**: In `Topology/MetricSpace/CoveringNumbers.lean`, rewrite the proof of `theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X)` to use `by_cases!` (so negations are pushed automatically) and to use the lemma `IsCover.coveringNumber_le_encard` instead of the current `iInf`/`card_maximalSeparatedSet` argument. Concretely, replace the current `by_cases h_top : packingNumber ε A ≠ ⊤` split with:

```
by_cases! h_top : packingNumber ε A ≠ ⊤
· rw [← encard_maximalSeparatedSet h_top]
  exact isCover_maximalSeparatedSet h_top |>.coveringNumber_le_encard maximalSeparatedSet_subset
· simp [h_top]
```

(adjusting `card_` to `encard_` accordingly).
**anchors**: CoveringNumbers.lean:390, CoveringNumbers.lean:351*  (* = inferred)
> [V2] We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley: ```suggestion   by_cases! h_top : packingNumber ε A ≠ ⊤   · rw [← 

## pr33098_i04  [V2/style/unknown]
**ask**: In `coveringNumber_two_mul_le_externalCoveringNumber` (in `Topology/MetricSpace/CoveringNumbers.lean`), replace the current `by_cases`/`rcases` handling of `A` with the suggested pattern `rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty); · simp` (i.e., use `rfl` in the empty-case branch rather than naming `h_empty`).
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] ```suggestion   rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)   · simp ```

## pr33098_i05  [V3/style/unknown]
**ask**: In `Topology/MetricSpace/CoveringNumbers.lean`, within the proof of `lemma coveringNumber_subset_le (h : A ⊆ B) : coveringNumber ε A ≤ coveringNumber (ε / 2) B`, rewrite the `calc` block so that the first line is on the same line as `:= calc`, i.e. change

`:= by
  calc coveringNumber ε A`

to

`:= by
    coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc
  coveringNumber ε A`

so that subsequent lines need not be indented under the `calc` per style guidelines.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V3] otherwise style guidelines would require to indent all lines below the first `calc` line. ```suggestion     coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc   coveringNumber ε A ```

## pr33092_i01  [V3/docs/adopted | NOT JUDGEABLE]
**ask**: Clarify why the private definition `walk_toSimpleGraph'`/`walk_toSimpleGraph` exists by adding an explanatory docstring stating what it is used for (e.g. that it is used to prove `reachable_toSimpleGraph`), or otherwise decide whether it should remain private if it is needed for an important theorem below.
**anchors**: Connected.lean:643, Connected.lean:643, Connected.lean:653  (* = inferred)
> [V3] I don't undertand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.

## pr33090_i01  [V3/style/partially_adopted]
**ask**: Change the positivity lemmas from taking a `Nonempty` hypothesis to being iff lemmas: replace `externalCoveringNumber_pos (hA : A.Nonempty) : 0 < externalCoveringNumber ε A` with `externalCoveringNumber_pos_iff : 0 < externalCoveringNumber ε A ↔ A.Nonempty`, and similarly replace `coveringNumber_pos (hA : A.Nonempty) : 0 < coveringNumber ε A` with `coveringNumber_pos_iff : 0 < coveringNumber ε A ↔ A.Nonempty` (and apply the same change to any analogous packing-number positivity lemma if present).
**anchors**: CoveringNumbers.lean:80, CoveringNumbers.lean:98  (* = inferred)
> [V3] Could you make this one an iff lemma? `simp` would be more efficient then.

## pr33086_i01  [V3/docs/dropped]
**ask**: Add explicit documentation in `Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean` describing the intended usage distinction between `cofibrantObjects` and `IsCofibrant` (and similarly `fibrantObjects` and `IsFibrant`): document that `IsCofibrant`/`IsFibrant` should be used as Prop typeclasses, while `cofibrantObjects`/`fibrantObjects` (the `ObjectProperty` wrappers) are only meant to define the corresponding full subcategories (`CofibrantObject`/`FibrantObject`) and are otherwise not the preferred API.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] I think there should be a documentation entry here about the "intented usages" of the two APIs `cofibrantObjects`/`IsCofibrant`. As far as I understand, `IsCofibrant` is to be used as a Prop-Class, while the object property shouldn’t. This needs to b

## pr33086_i02  [V3/style/unknown]
**ask**: Add the missing simp lemma `weakEquivalence_homMk_iff` (with attribute `@[simp]`) in `Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean`, stating that for cofibrant/fibrant objects `X Y` in a `CategoryWithWeakEquivalences C`, `WeakEquivalence (homMk f) ↔ WeakEquivalence f` for `f : X ⟶ Y`, proved by `simp only [weakEquivalence_iff]; rfl` as in the provided suggestion.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] Was this one intentionally left out compared to the others?  ```suggestion  @[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}     [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :     We

## pr33081_i01  [V2/style/unknown | NOT JUDGEABLE]
**ask**: Replace the existing anonymous function with `fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl)` at the relevant proof site (the one constructing an `iUnion` membership proof).
**anchors**:   (* = inferred)
> [V2] ```suggestion     fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl) ```

## pr33079_i01  [V3/naming/adopted]
**ask**: Replace the verbose proof of `lemma neZero_of_exists {n : ℕ} (i : Fin n) : NeZero n` (and avoid duplicating it) by using the direct construction `⟨i.2.ne⟩` / `⟨Nat.ne_zero_of_lt i.isLt⟩`, and consider renaming the lemma to `Fin.neZero` so it can be used via dot notation.
**anchors**: Basic.lean:90, Basic.lean:90  (* = inferred)
> [V3] Does something like ⟨i.2.ne⟩ work as a proof? Also, what about calling this `Fin.neZero` for dot notation?

## pr33078_i01  [V2/style/adopted]
**ask**: In `Mathlib/NumberTheory/MahlerMeasure.lean`, in the proof of `theorem cyclotomic_mahlerMeasure_eq_one`, avoid constructing `NeZero (n : ℂ)` via `@NeZero.charZero ...` and instead provide `have : NeZero n := ⟨hn⟩` (from `hn : n ≠ 0`) and then use the suggested proof structure: after the `n = 0` case, set `have : NeZero n := ⟨hn⟩`; reduce the goal to `suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1`; then reduce further to `suffices ∀ a ∈ primitiveRoots n ℂ, ‖a‖ ≤ 1` and finish with `IsPrimitiveRoot.norm'_eq_one (isPrimitiveRoot_of_mem_primitiveRoots hz) hn` (using `hn : n ≠ 0`) and `.le`, with the final `simpa` using `[mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ, Polynomial.cyclotomic.roots_eq_primitiveRoots_val]`.
**anchors**: MahlerMeasure.lean:113, MahlerMeasure.lean:113  (* = inferred)
> [V2] I think it is enough to provide `NeZero n`, and then the typeclass system will find `have : NeZero (n : ℂ)`.
> [V2] ```suggestion   have : NeZero n := ⟨hn⟩   suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1 by     simpa [mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ,       Polynomial.cyclotomic.roots_eq_primitiveRoots_val]   suffices ∀ a ∈ pri

## pr33070_i01  [V2/style/unknown]
**ask**: In `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean` inside the `Finset.sum` pretty-printer code starting `whenPPOption getPPNotation <| withOverApp 5 do`, replace the current computation of the domain pretty-printing flag with `let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes` (as in the suggestion), i.e. ensure the binder-domain option is obtained under `withAppArg`.
**anchors**:   (* = inferred)
> [V2] I think this is the same as ```suggestion   let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes ```

## pr33067_i01  [V2/other/partially_adopted | NOT JUDGEABLE]
**ask**: Decide whether the `recall` command elaborator in `Mathlib.Tactic.Recall` should mark the identifier syntax as a binder location (`isBinder := true`) given that `recall` does not generate a declaration in the environment (i.e. should it be used as the jump-to location or not). Also apply the same kind of change to `alias_in` in `Mathlib.Util.AliasIn` (i.e. adjust its info-reporting similarly rather than only fixing `recall`).
**anchors**: Recall.lean:44, AliasIn.lean:55*  (* = inferred)
> [V2] `isBinder` should be true only when this piece of syntax generates a declaration in the environment (so this point should be used as the "jump-to" location). That does not hold for `recall`, right?
> [V2] Can you also change `alias_in` please? Thanks!  I am surprised that without this, jump-to-definition still works. I thought the `isBinder` annotation was responsible for that (maybe jump-to-definition uses a non-binder location as fallback?)

## pr33066_i01  [V3/docs/adopted]
**ask**: Fix the docstring for `LinearIsometryEquiv.conjStarAlgEquiv` in `Mathlib/Analysis/InnerProductSpace/Adjoint.lean` to use the suggested wording: change “An isometric linear equivalence of two Hilbert spaces induces an equivalence of ⋆-algebras of their endomorphisms.” (currently written with the typo “An isometry linear equivalence …” in one of the hunks) so that it starts with “An isometric linear equivalence of two Hilbert spaces induces an equivalence of …”.
**anchors**: Adjoint.lean:683  (* = inferred)
> [V3] ```suggestion /-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of ```

## pr33066_i02  [V2/duplication/dropped]
**ask**: In `Mathlib/Topology/Algebra/Algebra/Equiv.lean` at the hunk defining `ofAlgEquiv` and its simp lemmas, delete the custom definition `ofAlgEquiv` and the associated lemmas (`coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`, `ofAlgEquiv_trans_ofAlgEquiv`) and instead construct the `ContinuousAlgEquiv` using the existing constructor `ContinuousAlgEquiv.mk` applied to the given `AlgEquiv` together with continuity proofs (using the default `:= by fun_prop` where possible).
**anchors**: Equiv.lean:302  (* = inferred)
> [V2] This is just the pre-existing constructor for `ContinuousAlgEquiv`: ``` ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]   [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra

## pr33066_i03  [V2/style/unknown]
**ask**: In `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`, revise the new auxiliary section to follow existing style: (1) restate the surjectivity line as `Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by` without manually filling the `_`; (2) intersperse the explanatory/commentary text throughout the code rather than grouping it separately; (3) format the auxiliary section header/variables exactly as suggested: `section auxiliaryDefs` followed by `variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)` (and then the remaining hypotheses); (4) improve the names of local `have` bindings in the added proofs (replace vague names like `have := ...` with more descriptive names).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V2] You can still phrase this as: ```suggestion     Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ``` and I think Lean shouldn't need you to fill in the `_`.
> [V3] This is nice, but it would be even nicer if it were interspersed throughout the code.
> [V3] ```suggestion section auxiliaryDefs  variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0) ```
> [V3] The naming of your `have`s could use some work. Please improve them.

## pr33065_i01  [V3/naming/dropped]
**ask**: Update the docstring wording for `ContinuousWithinAt.of_not_accPt` to say "isolated point" rather than "accumulated point" (i.e. change "not an accumulated point" to "not an accumulation point" / "isolated"). Rename `ContinuousWithinAt.of_not_accPt` -> `continuousWithinAt_of_not_accPt` (and likewise rename the second lemma `ContinuousAt.of_not_accPt` -> `continuousAt_of_not_accPt`) to match naming conventions like `continuousWithinAt_of_notMem_closure`, since these lemmas are not typically usable via dot notation.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V3] ```suggestion /-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulation point of ```
> [V3] I think it would make sense to call this `continuousWithinAt_of_not_accPt` instead to stay consistent with e.g. `continuousWithinAt_of_notMem_closure` - since the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used m

## pr33065_i02  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide whether `AccPt x (𝓟 {x}ᶜ)` in `ContinuousAt.of_not_accPt` should be rewritten/expressed equivalently as `AccPt x ⊤` (using `simp [← principal_univ, accPt_principal_iff_nhdsWithin, ← compl_eq_univ_diff]`), i.e. choose which hypothesis form to prefer in the API.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V4] Note that `AccPt x (𝓟 {x}ᶜ)` is equivalently just `AccPt x ⊤`: ``` import Mathlib  open Topology Filter Set  example {α : Type*} [TopologicalSpace α] {x : α} : AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤ := by   simp [← principal_univ, accPt_principal_iff_nh

## pr33057_i01  [V1/other/unknown | NOT JUDGEABLE]
**ask**: Fix the remaining Lean error(s) so the PR builds cleanly, then proceed with merging (bors d+).
**anchors**:   (* = inferred)
> [V1] Thanks! Delegating so you can fix the last error.   bors d+

## pr33056_i01  [V4/naming/unknown | NOT JUDGEABLE]
**ask**: Initiate a Zulip poll/discussion to decide the naming convention for the first uncountable aleph before proceeding with the refactor, specifically deciding whether to standardize on `aleph1` or instead use a non-numeral identifier such as `alephOne` (rather than `aleph_one`).
**anchors**:   (* = inferred)
> [V4] I think there should be a Zulip vote for this. I would have expected that we go the *other* way, potentially with `alephOne` instead of `alepha_one`. The point being that we generally don't use numerals in identifiers (cf. `cos_pi_div_two` for exampl

## pr33048_i01  [V3/scope/partially_adopted]
**ask**: Add a new simp lemma `@[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 := mod_cast mk_intCast (n := n)` (using `NeZero.ne n` to discharge `n ≠ 0`), in the `Archimedean.lean` sections near the existing `mk_natCast` lemma.
**anchors**: Archimedean.lean:181, Archimedean.lean:174  (* = inferred)
> [V3] Just realising: we do not have  ``` @[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 :=   mod_cast mk_intCast (n := n) ``` Mind adding?

## pr33048_i02  [V2/style/partially_adopted]
**ask**: In `Mathlib/Algebra/Order/Ring/StandardPart.lean`, change the lemmas `mk_add`, `mk_sub`, `mk_mul` so that the implicit `x y : K` become explicit binder arguments with explicit nonnegativity hypotheses: e.g. `theorem mk_add {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ...` (and similarly for `mk_sub`, `mk_mul`). Also, change `mk_lt_mk_iff` so that the hypotheses `hx hy` are explicit arguments (not implicit), i.e. `theorem mk_lt_mk_iff {x y : K} (hx hy) : ...` to facilitate backwards rewriting; apply the same principle to the analogous comparison lemma `mk_le_mk_iff` “below”.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V2] ```suggestion theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ``` Same below
> [V3] I would make those explicit for backwards rewriting: ```suggestion theorem mk_lt_mk_iff {x y : K} (hx hy) : ```

## pr33048_i03  [V3/naming/dropped]
**ask**: Decide whether the `_iff` suffix is necessary for the lemma `mk_le_mk_iff` in `Mathlib/Algebra/Order/Ring/StandardPart.lean` and, if not, rename it to `mk_le_mk` and format it as

`theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :
    FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=
  .rfl`.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] Do we really need the `_iff` here? ```suggestion theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :     FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=   .rfl ```

## pr33048_i04  [V3/style/unknown]
**ask**: Replace the `Coe ℚ (FiniteElement K)` instance with a `RatCast (FiniteElement K)` instance, i.e. change `instance : Coe ℚ (FiniteElement K) where ...` to `instance : RatCast (FiniteElement K) where ratCast q := .mk q (mk_ratCast_nonneg q)` in `Mathlib/Algebra/Order/Ring/StandardPart.lean` (in the `FiniteElement` section near the end).
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] ```suggestion instance : RatCast (FiniteElement K) where ``` no?

## pr33047_i01  [V4/naming/adopted | NOT JUDGEABLE]
**ask**: Decide/justify why the PR should prefer rewriting `smulRight (1 : R →L[R] R)` (or `smulRight (.id R R)`) to the longer spelling `toSpanSingleton R` as the standard form throughout the refactor.
**anchors**: Basic.lean:99*, Basic.lean:113*, Basic.lean:133*, Basic.lean:175*, Basic.lean:202*, Basic.lean:259*, Basic.lean:371*, Basic.lean:422*, Basic.lean:877*, Comp.lean:42*, Comp.lean:313*, Comp.lean:322*, Comp.lean:346*, Comp.lean:358*, Comp.lean:389*, CompMul.lean:30*, Inv.lean:31*, Inv.lean:79*, Mul.lean:237*, Mul.lean:248*, Mul.lean:527*, Mul.lean:553*, Extend.lean:162*, Measurable.lean:399*, Measurable.lean:921*, FaaDiBruno.lean:154*, FaaDiBruno.lean:171*, MeanValue.lean:748*, Basic.lean:178*, Conformal.lean:265*, Conformal.lean:304*, RealDeriv.lean:69*, FourierTransformDeriv.lean:119*, FourierTransformDeriv.lean:174*, FourierTransformDeriv.lean:823*, Adjoint.lean:378*, Bilinear.lean:402*, Mul.lean:208*, Deriv.lean:208*, Deriv.lean:221*, Transform.lean:129*, Transform.lean:194*, JacobianOneDim.lean:66*, JacobianOneDim.lean:412*, Determinant.lean:30*, LinearMap.lean:325*, LinearMap.lean:345*, LinearMap.lean:690*, LinearMap.lean:726*, LinearMap.lean:757*, LinearMap.lean:889*  (* = inferred)
> [V4] Might I ask why the longer spelling should be the preferred one?

## pr31342_i01  [V3/docs/unknown]
**ask**: Add a description to the PR message (i.e., update the PR description text to explain the change).
**anchors**:   (* = inferred)
> [V3] Could you add a description to the PR message?
