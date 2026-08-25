# Interventions review digest

128 interventions | judgeable 95 | outcomes {'adopted': 33, 'dropped': 19, 'unknown': 59, 'partially_adopted': 16, 'contested': 1}

## pr33421_i01  [V3/naming/adopted]
**ask**: In `Mathlib/Algebra/Order/Round.lean`, add (or rename to) a lemma named `round_eq_div` giving the formula `round x = (⌊2 * x⌋ + 1) / 2` (instead of only having it under a different name such as `round_eq'`).
**anchors**: Round.lean:45  (* = inferred)
> [V3] How about `round_eq_div`?

## pr33421_i02  [V2/duplication/dropped | NOT JUDGEABLE]
**ask**: In `Mathlib/Topology/Algebra/Order/Floor.lean`, avoid ad-hoc uses of `continuous_of_discreteTopology` to get continuity of `⌊·⌋`/`fract`; instead introduce (or use an existing) general lemma giving `ContinuousOn`/`ContinuousAt` for functions into a discrete topology (e.g. `ContinuousOn f s` and `ContinuousAt f x` when the codomain has `DiscreteTopology`), and rewrite `continuousOn_fract` and `continuousAt_fract` using that lemma (and similarly for the next theorem(s) below that rely on the same pattern).
**anchors**: Floor.lean:195  (* = inferred)
> [V2] Is this not something very general that should exist as a lemma? Same in the next theorem

## pr33421_i03  [V2/style/adopted]
**ask**: In `Mathlib/Algebra/Order/Floor/Ring.lean` at the new lemma `mul_fract_eq_one_iff_exists_int`, change the statement to require `hk : 1 < k` (rather than any weaker/implicit hypothesis) and adjust the proof accordingly (derive `hk0 : 0 < k` from `hk` and use `mul_le_mul_iff_right₀`/`mul_lt_mul_iff_right₀` with `hk0`), following the suggested proof structure in the review comment.
**anchors**: Ring.lean:267, Ring.lean:267  (* = inferred)
> [V2] Better I think as ```suggestion theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :     k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by   rw [fract, mul_sub, sub_eq_iff_eq_add']   refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩   rintro ⟨

## pr33419_i01  [V3/naming/adopted]
**ask**: In `Mathlib/Data/Finset/Card.lean` around line 574, rename the newly introduced equality lemma for `#t - #s` so that its name is clear/parsible; use the suggested name `lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ...` (instead of the proposed name in the PR).
**anchors**: Card.lean:574  (* = inferred)
> [V3] I couldn't parse the name you proposed. ```suggestion lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ```

## pr33413_i01  [V2/style/unknown | NOT JUDGEABLE]
**ask**: No change requested (maintainer only notes that the `to_dual` attribute could be used to generate both deprecated aliases at once, but does not ask to modify any specific declarations or files).
**anchors**:   (* = inferred)
> [V2] Thanks :tada:  maintainer merge  (You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want, but I don't know if the automated removal of deprecated declarations works with that)

## pr33401_i01  [V2/proof-golf/adopted]
**ask**: In `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`, simplify the `n = 0` case of `Subgroup.closure_pow_le` to `| 0 => by simp_all` instead of the manual elementwise argument.
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | 0 => by simp_all ```

## pr33401_i02  [V2/proof-golf/adopted]
**ask**: In `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`, in the proof of `Subgroup.closure_pow_le` (the `| n + 1 =>` case after removing the `n ≠ 0` hypothesis), replace the explicit `calc` proof with the shorter `by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem]`.
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem] ``` instead of the `calc ...`

## pr33400_i01  [V3/naming/unknown | NOT JUDGEABLE]
**ask**: No concrete change request can be recovered from the provided context: the only comment is an unanchored suggestion to rename “this” to `contDiff`, but the target declaration/file and exact identifier to rename are not specified.
**anchors**:   (* = inferred)
> [V3] pre-existing: I think we should also rename this to `contDiff`

## pr33395_i01  [V4/naming/adopted]
**ask**: In `Mathlib/Algebra/Star/LinearMap.lean`, rename the lemma currently introduced as `theorem IntrinsicStar.starLinearEquiv_eq ...` to the more descriptive name `theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr ...` (keeping the statement `starLinearEquiv R (A := E →ₗ[R] F) = (starLinearEquiv R).arrowCongr (starLinearEquiv R)` unchanged).
**anchors**: LinearMap.lean:126  (* = inferred)
> [V4] I like this the best. It's verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this. ```suggestion theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ```

## pr33376_i01  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: It’s unclear what change is being requested: the maintainer only asks whether the newly added lemma is actually used in this PR, without specifying any concrete modification to make in any file or declaration.
**anchors**:   (* = inferred)
> [V2] This is a reasonable lemma, but you're not using it for this PR, right?

## pr33373_i01  [V2/duplication/unknown]
**ask**: In `Mathlib/Analysis/Calculus/IteratedDeriv/Lemmas.lean` within `section shift_invariance` (around the lemmas `iteratedDeriv_comp_const_add` / `iteratedDeriv_comp_add_const` and the new `iteratedDeriv_comp_sub_const`), simplify the proof of the subtraction/negation variant by rewriting it in terms of existing shift lemmas (notably `iteratedDeriv_comp_add_const` and `iteratedDeriv_comp_neg`) using `simp/simpa` (e.g. via `sub_eq_add_neg` / `neg_add_eq_sub`) rather than giving a separate bespoke proof.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simp [sub_eq_add_neg, iteratedDeriv_comp_add_const] ```
> [V2] ```suggestion   simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using     iteratedDeriv_comp_neg n (fun z => f (z + s)) ```
> [V2] Let's reuse the existing theorems:

## pr33362_i01  [V3/scope/partially_adopted]
**ask**: In `Mathlib/Analysis/Complex/Schwarz.lean` near the top of the file (around the `## TODO` section and the initial `open`/`namespace`/`variable` setup), move the relevant lines down a few lines so that they are placed inside `namespace Complex` (i.e. restructure the surrounding `namespace Complex` placement so the intended declarations live under `Complex`).
**anchors**: Schwarz.lean:40, Schwarz.lean:40  (* = inferred)
> [V3] Why not move these a few lines below so that it's on the `Complex` namespace?

## pr33357_i01  [V3/docs/unknown]
**ask**: Fix the typo in the PR description for PR #33357 ("chore(CateggoryTheory/Monoidal/NaturalTransformation): monoidality of whiskers").
**anchors**:   (* = inferred)
> [V3] (there's a typo in your PR desc)

## pr33356_i01  [V2/style/adopted]
**ask**: In `Mathlib/NumberTheory/ModularForms/ArithmeticSubgroups.lean`, in the proof of `lemma hasDetPlusMinusOne_iff_abs_det`, restructure the `↔` proof using `refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩` (i.e. use the forward direction via `HasDetPlusMinusOne.abs_det` and build the backward direction by constructing `HasDetPlusMinusOne` with a single remaining goal).
**anchors**: ArithmeticSubgroups.lean:43  (* = inferred)
> [V2] ```suggestion   refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩ ```

## pr33349_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No concrete change request can be recovered from the comment “I don't think there is consensus here?” on Mathlib/Algebra/Order/AddGroupWithTop.lean; clarify/resolve the lack of maintainer consensus before proceeding with the edits in this PR.
**anchors**: AddGroupWithTop.lean:41  (* = inferred)
> [V4] I don't think there is consensus here?

## pr33349_i02  [V2/style/unknown]
**ask**: In `Mathlib/Algebra/Order/AddGroupWithTop.lean` around the new `*_of_ne_top` monotonicity/injectivity lemmas (hunk at line ~140), add the missing `[simp]` cancellation lemmas derived from `add_left_strictMono_of_ne_top` / `add_right_strictMono_of_ne_top`: `@[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c := (add_left_strictMono_of_ne_top _ h).le_iff_le`, `@[simp] lemma add_le_add_iff_right_of_ne_top ... : a + b ≤ a + c ↔ b ≤ c := (add_right_strictMono_of_ne_top _ h).le_iff_le`, `@[simp] lemma add_lt_add_iff_left_of_ne_top ... : b + a < c + a ↔ b < c := (add_left_strictMono_of_ne_top _ h).lt_iff_lt`, and similarly `@[simp] lemma add_lt_add_iff_right_of_ne_top ... : a + b < a + c ↔ b < c := (add_right_strictMono_of_ne_top _ h).lt_iff_lt` ("Same here" indicates to do the analogous right/lt versions as well).
**anchors**: AddGroupWithTop.lean:140  (* = inferred)
> [V2] ```suggestion @[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c :=   (add_left_strictMono_of_ne_top _ h).le_iff_le  @[simp] lemma add_le_add_iff_right_of_ne_top {a b c : α} (h : a ≠ ⊤) : a + b ≤ a + c ↔
> [V2] Same here

## pr33345_i01  [V3/docs/partially_adopted]
**ask**: In `Mathlib/Algebra/Order/Ring/Archimedean.lean`, fix the docstring immediately above the `instance : Add (ArchimedeanClass R)` by correcting the spelling and wording to `/-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/`.
**anchors**: Archimedean.lean:72  (* = inferred)
> [V3] Probabily a good idea to fix that simultaneousily ```suggestion /-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/ ```

## pr33343_i01  [V3/style/adopted]
**ask**: In `Mathlib/Algebra/Order/Ring/StandardPart.lean`, in the proof of `theorem stdPart_nonneg`, replace the final `exact h` after rewriting with `stdPart_of_mk_ne_zero` by an explicit proof term (e.g. `apply map_nonneg; assumption`) rather than relying on `exact h`, since the goal is not syntactically the same as `h`.
**anchors**: StandardPart.lean:402, StandardPart.lean:402  (* = inferred)
> [V3] ```suggestion     exact h ``` I think it is better to be explicit here, especially when it is not syntactically eq

## pr33337_i01  [V3/naming/adopted]
**ask**: In `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean` around the lemma currently named `coe_orthogonalProjection_eq_linearProjOfIsCompl` (PR hunk at line ~191), rename this lemma to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` so the name reflects that it is an equality of linear maps `(K.orthogonalProjection : E →ₗ[𝕜] K)`.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] : ```

## pr33337_i02  [V3/naming/dropped]
**ask**: In `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean` at the lemma currently being renamed to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`/`coe_orthogonalProjection_eq_linearProjOfIsCompl` (around line 191), rename it instead to `toLinearMap_starProjection_eq_isComplProjection` (under `[K.HasOrthogonalProjection]`).
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] : ```

## pr33333_i01  [V4/style/dropped]
**ask**: In `Mathlib/Analysis/Real/Pi/Bounds.lean`, rewrite the proof of `theorem floor_pi_eq_three : ⌊π⌋ = 3` to use `rw [Int.floor_eq_iff]` followed by `grind [pi_gt_three, pi_lt_four]` (i.e., `by rw [Int.floor_eq_iff]; grind [pi_gt_three, pi_lt_four]`) instead of the current `Int.floor_eq_iff.mpr`/`norm_num`/`exact_mod_cast` style.
**anchors**: Bounds.lean:223, Bounds.lean:223  (* = inferred)
> [V4] Thanks! I'm not sure if I prefer those, though (same with the other). I'll wait for another opinion.
> [V4] I don't have a strong preference. But would this be a middle ground? ```suggestion theorem floor_pi_eq_three : ⌊π⌋ = 3 := by   rw [Int.floor_eq_iff]   grind [pi_gt_three, pi_lt_four] ```

## pr33333_i02  [V2/duplication/unknown]
**ask**: In `Mathlib/Analysis/Real/Pi/Bounds.lean` (around line 223, the hunks that introduce/need bounds for `exp 1`), stop proving or restating bounds for `Real.exp 1` locally, and instead import and use the existing lemmas from `Mathlib.Analysis.Complex.ExponentialBounds`.
**anchors**: Bounds.lean:223*, Bounds.lean:223*  (* = inferred)
> [V2] Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.

## pr33332_i01  [V1/style/unknown]
**ask**: In `Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean`, in the proof of `lemma adj_of_mem_walk_support`, simplify the `cons` case pattern by removing the unused binder names, changing `| @cons u v w h p ih =>` to `| cons h p ih =>`.
**anchors**: Connected.lean:252  (* = inferred)
> [V1] The names aren't used anymore ```suggestion   | cons h p ih => ```

## pr33328_i01  [V4/style/contested | NOT JUDGEABLE]
**ask**: In `Mathlib/Order/Interval/Set/Basic.lean`, avoid making the localized proof-style refactor (e.g. changing `fun h => h <| left_mem_Ici, fun h _ hx => h.trans hx` to `fun h => h self_mem_Ici, fun h _ => h.trans`) in `theorem Ici_subset_Ici` unless you apply the same style consistently to the other analogous `[simp]` interval-subset lemmas in this file; otherwise leave these style changes for a separate PR.
**anchors**: Basic.lean:288, Basic.lean:316*  (* = inferred)
> [V4] Why this style change here and not in the other analogous places? (I'm neutral to the style changes, maybe they can be left to another PR)

## pr33321_i01  [V3/docs/unknown]
**ask**: Fix the typo in the docstring of `IsMulIndecomposable.baseOf` in `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`: change “crystallogrphic root system” to “crystallographic root system” (in the `[to_additive]` doc comment for `IsMulIndecomposable.baseOf`).
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] ```suggestion In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ```

## pr33321_i02  [V3/style/unknown]
**ask**: In `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`, change the definition of `IsMulIndecomposable.baseOf` so it does not rely on definitional equality between predicates and sets: define it explicitly as a `Set ι` using set-builder notation, e.g. `def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι := {j | IsMulIndecomposable v {i | 1 < f (v i)} j}`.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] Isn't this abusing the defeq between predicates and sets? ```suggestion def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=   {j | IsMulIndecomposable v {i | 1 < f (v i)} j} ```

## pr33321_i03  [V3/docs/partially_adopted]
**ask**: In `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean`, revise the module docstring under "## Implementation details" to clearly explain that the proof requires an ordering on coefficients even though the final existence theorem does not (i.e. fix/clarify this explanatory text).
**anchors**: BaseExists.lean:1  (* = inferred)
> [V3] ```suggestion The proof needs a set of ordered coefficients, even though the ultimate existence statement does ```

## pr33316_i01  [V3/naming/adopted | NOT JUDGEABLE]
**ask**: Avoid introducing or preferring a non-ASCII declaration name for the scalar product as a sesquilinear form; keep/use the more readable ASCII name when deprecating the duplicate declaration (and update any references in the touched files accordingly).
**anchors**: RiemannLebesgueLemma.lean:199*, CharacteristicFunction.lean:66*, CharacteristicFunction.lean:155*, CharacteristicFunction.lean:238*, ComplexMGF.lean:320*  (* = inferred)
> [V3] Getting rid of the duplication is fine, but the other name comes off as more readable to me. I thought using non-ASCII characters in declarations was generally discouraged.

## pr33310_i01  [V2/style/adopted]
**ask**: In `Mathlib/RingTheory/WittVector/Complete.lean` around the new `quotientPEquiv`, refactor to (1) introduce an auxiliary lemma `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` and use it via `Ideal.quotEquivOfEq ker_constantCoeff.symm` rather than rewriting the kernel equality in a local `have`, and (2) keep `RingHom.ker constantCoeff` on the LHS (don’t swap sides) since the RHS is the more basic term; additionally, add a separate lemma `constantCoeff_surjective : Function.Surjective (constantCoeff : 𝕎 k → k)` (proved by `r ↦ ⟨teichmuller p r, rfl⟩`) and use it in `RingHom.quotientKerEquivOfSurjective`, with `constantCoeff_surjective` moved to `Mathlib/RingTheory/WittVector/Teichmuller.lean`.
**anchors**: Complete.lean:95, Complete.lean:95, Teichmuller.lean:125*  (* = inferred)
> [V2] It would be useful to introduce auxiliary lemmas: ```lean lemma ker_constantCoeff :     RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)} := by   ext   simp [mem_span_p_iff_coeff_zero_eq_zero]  -- this should be moved to the `Teichmuller` file lemma
> [V3] It seems more logical to me to keep `ker` in the LHS, as arguably the RHS is a "more basic term" as compared to the LHS.

## pr33305_i01  [V1/style/partially_adopted]
**ask**: In `Mathlib/GroupTheory/Submonoid/Inverses.lean` around line 20 (the doc/file reference to `Mathlib/Algebra/Group/Submonoid/Pointwise.lean`), reformat the overly long line so it satisfies Mathlib's line-length/style checks (e.g. by breaking it across lines).
**anchors**: Inverses.lean:20*, Inverses.lean:20*  (* = inferred)
> [V1] bors r- bors d+  There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36

## pr33302_i01  [V2/style/adopted]
**ask**: In `Mathlib/CategoryTheory/Shift/ShiftedHom.lean`, change `ShiftedHom` from a `def` to an `abbrev`, and then delete the redundant `AddCommGroup` and `Module` instances currently provided for `ShiftedHom`; update any downstream proofs that break (notably in `Mathlib/CategoryTheory/Localization/SmallShiftedHom.lean` and `Mathlib/Algebra/Homology/DerivedCategory/Ext/ExtClass.lean`) to work with the new reducibility/`dsimp` behavior, using simple fixes like removing now-unnecessary `erw [Iso.homToEquiv_apply]` where appropriate.
**anchors**: ShiftedHom.lean:13*, ShiftedHom.lean:29*, ShiftedHom.lean:181*, ShiftedHom.lean:184*, SmallShiftedHom.lean:209*, SmallShiftedHom.lean:219*, SmallShiftedHom.lean:239*, ExtClass.lean:81*  (* = inferred)
> [V2] Could you also make `ShiftedHom` an abbrev instead of a `def`. Then, the `AddCommGroup` and `Module` instances on this type could be removed. I have tried this, and overall, it improves automation. A few proofs should break, but the fix should be eas

## pr33296_i01  [V2/scope/unknown]
**ask**: In `Mathlib/Algebra/Central/End.lean`, strengthen the imports by replacing the current imports with (or adding) `import Mathlib.Algebra.Central.Basic` so that the central/algebraic infrastructure used by the new GL(center) development is available without relying on `import Mathlib`.
**anchors**:   (* = inferred)
> [V2] I was just about to make this PR lol. Here is a cleaner proof. Along with a golf and a generalization for the instance. I can still make this PR, or you can just apply this, whatever :)  Note that you need to strengthen the import to `Mathlib.Algeb

## pr33294_i01  [V3/naming/partially_adopted]
**ask**: In `Mathlib/SetTheory/Cardinal/Cofinality.lean` around line 532, rename the lemma currently introduced as `IsFundamentalSequence.of_isNormal`/`isFundamentalSequence_of_isNormal` to `isFundamentalSequence.of_isNormal` (i.e. use a lower-case lemma name `isFundamentalSequence` rather than the `IsFundamentalSequence` namespace or a snake_case name) while keeping the `.of_isNormal` suffix.
**anchors**: Cofinality.lean:532  (* = inferred)
> [V3] ```suggestion theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f) ```

## pr33294_i02  [V2/style/partially_adopted]
**ask**: In `Mathlib/SetTheory/Ordinal/Topology.lean` around line 178 (both hunks `@582b57c7ef` and `@b784bc1471`), replace the `iSup` rewrite `rw [IsNormal.map_iSup h g]`/`rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with the form `rw [h.map_iSup (bddAbove_of_small _)]` (i.e. use the method lemma on `h` with an explicit `bddAbove` argument rather than the namespaced lemma).
**anchors**: Topology.lean:178  (* = inferred)
> [V2] ```suggestion     rw [h.map_iSup (bddAbove_of_small _)] ``` no? 

## pr33287_i01  [V2/style/adopted]
**ask**: In `Mathlib/CategoryTheory/Sites/IsSheafFor.lean`, in the definition `Arrows.toCompatible` (around line 799), simplify the proof of the `property` field to:
```lean
property i j Z gi gj h := by
  simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]
```
(i.e. use `simp` with those lemmas and `h` rather than the existing `dsimp; simp only ...`).
**anchors**: IsSheafFor.lean:799, IsSheafFor.lean:799*  (* = inferred)
> [V2] ```suggestion   property i j Z gi gj h := by     simp [← FunctorToTypes.map_comp_apply, ← op_comp, h] ```

## pr33287_i02  [V2/style/unknown]
**ask**: In `Mathlib/CategoryTheory/Sites/IsSheafFor.lean`, in the proof around `isSheafFor_ofArrows_iff_bijective_toCompabible`, rewrite the goal in terms of a `Presieve.ofArrows` built from the maps `(Over.map p).map (f i)` by inserting a line like `have : IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ...` (i.e. use `Presieve.ofArrows` with those morphisms rather than the current form).
**anchors**: IsSheafFor.lean:799, IsSheafFor.lean:799*  (* = inferred)
> [V2] ```suggestion       IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ```

## pr33285_i01  [V2/proof-golf/partially_adopted]
**ask**: In `Mathlib/Algebra/Module/Submodule/Map.lean`, further golf the proof of `theorem inf_comap_le_comap_add (f₁ f₂ : M →ₛₗ[τ₁₂] M₂) : comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q` by replacing the current `simp`/`exact` proof with the shorter term-style proof `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2` (i.e. avoid `SetLike.le_def` rewriting and the extra `simp` lines), and apply this simplification to both occurrences/versions of the lemma in the file.
**anchors**: Map.lean:595, Map.lean:597  (* = inferred)
> [V2] here's an even better golf ```suggestion     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=   fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2 ```

## pr33285_i02  [V2/proof-golf/unknown]
**ask**: In `Mathlib/RingTheory/Ideal/Cotangent.lean`, simplify the proof of `theorem cotangentEquivIdeal_symm_apply` (around line 151) by replacing the manual `injective`/`rw`/`ext`/`rfl` argument with a `simp`-based proof, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (or equivalently `exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)`).
**anchors**: Cotangent.lean:151, Cotangent.lean:151  (* = inferred)
> [V2] or ```lean   simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff] ``` or ```lean   exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _) ```

## pr33283_i01  [V3/style/dropped]
**ask**: In `Mathlib/RingTheory/Polynomial/Chebyshev.lean`, adjust the formatting of the `linear_combination` calls around line ~807 so that the expression being combined is on the same line as `linear_combination (norm := (push_cast; ring_nf))` (i.e. avoid the awkward line break after `linear_combination ...`), applying this consistently to the similar occurrences noted by “and the other ones”.
**anchors**: Chebyshev.lean:807, Chebyshev.lean:807  (* = inferred)
> [V3] ```suggestion   linear_combination (norm := (push_cast; ring_nf)) h ``` I personally find this line break a bit weird but if you are attached to this style I don't particular want to block this PR because of it.
> [V3] (and the other ones)

## pr33268_i01  [V3/style/unknown]
**ask**: In `Mathlib/Order/BoundedOrder/Lattice.lean`, reorder the lemmas so that the paired `max_left` and `max_right` lemmas are placed adjacent to each other (i.e., move them to be consecutive).
**anchors**: Lattice.lean:26  (* = inferred)
> [V3] I think a more natural ordering is to put the max_left and max_right lemmas right after eachother.

## pr33267_i01  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: No change requested in this PR: although the code in `Mathlib/Order/WithBot.lean` around the new dual-equivalence section (near line 872) could use `toDual_symm` instead of applying some theorem, the maintainer explicitly notes this is outside the scope of the PR.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] I feel like this theorem should not be applied; it can just be `toDual_symm`. But that is outside the scope of this PR.

## pr33267_i02  [V3/naming/unknown]
**ask**: In `Mathlib/Order/WithBot.lean` around the new section introducing the `(WithBot α)ᵒᵈ ≃ WithTop αᵒᵈ` / `(WithTop α)ᵒᵈ ≃ WithBot αᵒᵈ` equivalences (the hunk at line ~872), rename the declaration currently documented as ``WithBot.toDual`` (the equivalence sending `⊥` to `⊤`) to the more specific name `toDual_bot`.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] And this could just be called `toDual_bot`.

## pr33267_i03  [V3/style/unknown]
**ask**: In `Mathlib/Order/WithBot.lean` around the new duality section introduced near line 872, since the `WithBot` namespace is open, remove unnecessary `WithBot.` qualifiers and refer to declarations in that namespace unqualified (e.g. use `toDual` rather than `WithBot.toDual`) throughout this hunk.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] Since the WithBot namespace is open, you can avoid the `WithBot.`

## pr33267_i04  [V3/style/unknown]
**ask**: In `Mathlib/Order/WithBot.lean` around line 872 (the section introducing the dual equivalences), adjust formatting/indentation so that any statement that fits on a single line is written on one line rather than split across multiple lines (apply to both duplicated hunks at this location).
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] I think the indentation where the whole statement fits one  one line is actually preferred.

## pr33267_i05  [V2/docs/unknown]
**ask**: In `Mathlib/Order/WithBot.lean` around the documentation for `WithBot.toDual` (in the section introduced by `/-! ### (WithBot α)ᵒᵈ ≃ WithTop αᵒᵈ, (WithTop α)ᵒᵈ ≃ WithBot αᵒᵈ -/`), update the docstring reference from the old name `WithBot.toDual_top_equiv` to the current declaration name `WithBot.toDualTopEquiv` (as in `Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv`).
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] ```suggestion See `WithBot.toDualTopEquiv` for the related order-iso. -/ ``` Looks like this was renamed at some point: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv

## pr33232_i01  [V3/style/partially_adopted]
**ask**: In `Mathlib/Analysis/Distribution/TemperedDistribution.lean`, in the proof of `fourierTransformInv_toTemperedDistributionCLM_eq`, rewrite the `calc` chain in the more idiomatic style that keeps the starting/ending goals as `_` (i.e. `𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc ... _ = _ := fourierInv_fourier_eq _`), rather than using a separate `:= calc` with explicit LHS/RHS, and apply this style change to both duplicated hunks.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] style nit. I didn't actually test that it still elaborates properly with the starting and ending `_`, but I don't see which it shouldn't. ```suggestion     𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc   _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) :=

## pr33232_i02  [V3/docs/adopted]
**ask**: In `Mathlib/Analysis/Distribution/TemperedDistribution.lean`, add a docstring (Lean `/- ... -/` comment) immediately before the theorem `fourierTransformInv_toTemperedDistributionCLM_eq` stating that the distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)` (i.e. update/insert the documentation for this lemma to match that wording).
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] ```suggestion /-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/ theorem fourierTransformInv_toTemperedDistributionCLM_eq (f : 𝓢(E, F)) : ```

## pr33208_i01  [V2/style/unknown]
**ask**: In `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`, rename/introduce the lemma currently being added so that it is named `isMulIndecomposable_id_univ` and has the binder order `[Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ...` (i.e. take `hx : x ≠ 1` explicitly).
**anchors**: Indecomposable.lean:1, Indecomposable.lean:1*  (* = inferred)
> [V2] ```suggestion lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ```

## pr33208_i02  [V3/docs/unknown]
**ask**: In `Mathlib/Algebra/Group/Irreducible/Indecomposable.lean`, improve the docstring for the Serre lemma statement (and any related new declarations in this file) so that the lemma’s hypotheses and conclusion are easier to parse, e.g. by explicitly describing the setting (`S` linearly ordered cancellative monoid, `f : M →* S`, family `v : ι → M`) and what the generated submonoid/group is, following the reviewer’s suggested expanded explanation.
**anchors**: Indecomposable.lean:1, Indecomposable.lean:1*  (* = inferred)
> [V3] I found the statement a bit hard to parse, so I found myself wanting a more informative docstring. Please check that my interpretation is correct, or otherwise improve it.  ```suggestion /-- This is [serre1965](Ch. V, §9, Lemma 2) and may be used to 

## pr33207_i01  [V4/duplication/unknown | NOT JUDGEABLE]
**ask**: In `Mathlib/Order/Argmin.lean`, avoid introducing a standalone `Function.argmin` definition via `Set.Finite.exists_minimal`; instead, (a) relate the construction/lemmas to the existing `Minimal`/`MinimalFor` API (adding the appropriate bridge lemmas so `argmin` is expressed/usable in terms of `MinimalFor`), and prefer using choice/`obtain` on `Set.Finite.exists_minimal` rather than a new definition when possible; optionally consider alignment with existing `List.argmin` material.
**anchors**: Argmin.lean:1  (* = inferred)
> [V4] Is it definitely easier to use this definition rather than using choice/`obtain` on `Set.Finite.exists_minimal`?   It would be nice to connect the material here to the `Minimal`/`MinimalFor` API (the latter of which isn't quite complete at the mome

## pr33203_i01  [V3/naming/dropped | NOT JUDGEABLE]
**ask**: In `Mathlib/NumberTheory/Padics/HeightOneSpectrum.lean`, rename or otherwise change the declaration `Rat.intEquiv` (around the docstring “If `R` has field of fractions `ℚ` ... isomorphic to `ℤ`”) so its name reflects that it is a ring equivalence `R ≃+* ℤ` under `IsIntegralClosure R ℤ ℚ` (not an “`ℚ ≃ ℤ`” equivalence), since `Rat.intEquiv`/`Rat.intEquiv`-style naming is misleading.
**anchors**: HeightOneSpectrum.lean:62, HeightOneSpectrum.lean:70  (* = inferred)
> [V3] I'd just like to mention that this is not at all what I'd expect from something called `Rat.intEquiv`! I was expecting some sort of bijection `ℚ ≃ ℤ` instead.

## pr33201_i01  [V2/duplication/partially_adopted]
**ask**: In `Mathlib/AlgebraicTopology/SimplicialSet/HomotopyCat.lean` around the new instances at line ~455, replace the bespoke proofs/instances `instance (X : Truncated 2) [Subsingleton (X _⦋0⦌₂)] : Subsingleton X.HomotopyCategory`, `instance subsingleton_hom ... : Subsingleton (x ⟶ y)`, and `instance (X) : Unique X.HomotopyCategory` with instances derived from existing general lemmas about free (refl) categories/quivers with unique objects and subsingleton homs and about quotient categories preserving `SubsingletonHom`/`Unique` (e.g. via `CategoryTheory.Quotient.instSubsingletonHom`/`CategoryTheory.Quotient.instUnique`), and use existing results like `Cat.isTerminalOfUniqueOfIsDiscrete` for the terminal-object statement instead of a homotopy-category-specific argument.
**anchors**: HomotopyCat.lean:455, HomotopyCat.lean:455  (* = inferred)
> [V2] I feel like this proof is too specialized for the homotopy category. Mathlib arleady knows that quotient categories of categories with unique objects and subsingleton homs have subsingleton homs, and that free categories on quivers with unique object
> [V2] Same here: we already have `Cat.isTerminalOfUniqueOfIsDiscrete`: ```suggestion instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory :=    letI : Unique (OneTruncation₂ X) := inferInstanceAs (Unique (X _⦋0⦌₂))   CategoryTh

## pr33201_i02  [V2/duplication/dropped]
**ask**: In `Mathlib/CategoryTheory/Monoidal/Cartesian/FunctorCategory.lean` at the new instance
`instance {J' : Type*} [Category J'] (F : J ⥤ J') : (((Functor.whiskeringLeft J J' C).obj F).Monoidal) := ...`, remove this custom `Monoidal` instance and instead use (or directly reference) the already-existing `CategoryTheory.Functor.Monoidal.whiskeringLeft` construction, since it provides the same functionality more generally.
**anchors**: FunctorCategory.lean:192  (* = inferred)
> [V2] This seems to be a (less general) duplicate of [CategoryTheory.Functor.Monoidal.whiskeringLeft](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Monoidal/FunctorCategory.html#CategoryTheory.Functor.Monoidal.whiskeringLeft)

## pr33201_i03  [V3/other/adopted]
**ask**: In `Mathlib/CategoryTheory/Functor/Currying.lean` and `Mathlib/CategoryTheory/Functor/CurryingThree.lean`, whenever you introduce a `FullyFaithful` proof for the currying functors (`fullyFaithfulCurry` for `curry` and `fullyFaithfulCurry₃` for `curry₃`), also add the corresponding `instance` declarations `: Full` and `: Faithful` for these functors (analogous to the existing `Full`/`Faithful` instances for `uncurry`/`uncurry₃`).
**anchors**: Currying.lean:110, Currying.lean:110, CurryingThree.lean:43, CurryingThree.lean:43  (* = inferred)
> [V3] Please add the corresponding `Full` and `Faithful` instances (we really need a way to automate adding those via an attribute we can put on a `FullyFaithful` definition!).
> [V3] Same  comment: please also add the `Full` and `Faithful` instances

## pr33200_i01  [V1/scope/unknown | NOT JUDGEABLE]
**ask**: Do not merge this PR: remove all newly introduced axioms and all `sorry` placeholders, and rewrite/split the contribution into small, human-written, style-compliant PRs that are feasible to review; otherwise close/withdraw PR #33200.
**anchors**:   (* = inferred)
> [V1] The issue is nothing to do with the code of conduct. This PR is completely unsuitable for mathlib for multiple reasons. (a) it is far too long to review (b) it has axioms (c) it has sorries (d) it was written by an AI which seems to have no understan
> [V1] > no axioms  I encourage you to learn how to use `grep`, as you have in one file introduced 4 times as many axioms as we use in *all* of Mathlib.  I won't be engaging further and wasting my time.

## pr33198_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: In `Mathlib/SetTheory/Ordinal/Basic.lean` around the section comment `/-! ### The first infinite ordinal ω -/` (line ~760), do not introduce a mixed naming scheme like `omega0`/`aleph0` alongside `omega_one`/`aleph_one`; instead, standardize the spelling consistently for both zero and one (e.g. prefer `omega_zero` and `aleph_zero` to match `omega_one`/`aleph_one`).
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] I'm confused, you want to write `omega0` and `aleph0` and also `omega_one` and `alepg_one`? I'm virtually certain that if you asked on Zulip, the poll would go in favor of `omega_zero` too and `aleph_zero` too (at least, assuming votes from the same 

## pr33198_i02  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No concrete code change is requested: the reviewer is noting that an apparent asymmetry in the relevant lemma (in Mathlib/SetTheory/Ordinal/Basic.lean around the ω section at line ~760) is meaningful and should not be “symmetrized” or refactored away during the `ℵ₁`→`aleph_one` renaming.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] Oh I see! Then I think the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.

## pr33198_i03  [V1/other/unknown | NOT JUDGEABLE]
**ask**: Fix the CI build failures for PR #33198 before merging, then re-run bors (remove the current bors rejection and try again only after the build passes).
**anchors**: Basic.lean:760*  (* = inferred)
> [V1] The build is failing: https://github.com/leanprover-community/mathlib4/actions/runs/20436145675/job/58717788626#step:22:905 bors r- bors d+

## pr33190_i01  [V3/style/adopted]
**ask**: In `Mathlib/Algebra/Polynomial/Roots.lean`, in the proof of lemma `eq_of_natDegree_lt_card_of_eval_eq` (around line 630), make the `hf` argument to `eq_zero_of_natDegree_lt_card_of_eval_eq_zero` explicit in the `apply` line (e.g. `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf` or `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero (hf := hf)`), to avoid confusion about where `hf` is supplied.
**anchors**: Roots.lean:630  (* = inferred)
> [V3] only because I was confused why `hf` wasn't an explicit argument, and then after looking above, I realized it is. ```suggestion   apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf ```

## pr33183_i01  [V3/style/unknown]
**ask**: In `Mathlib/CategoryTheory/Pi/Monoidal.lean`, when defining the pointwise `MonoidalCategory` structure on `Π i, C i`, rewrite the component definitions in pointwise form by adding the index argument explicitly, i.e. define `tensorObj X Y i := X i ⊗ Y i`, `tensorHom f g i := f i ⊗ₘ g i`, `whiskerLeft X _ _ f i := X i ◁ f i`, `whiskerRight f Y i := f i ▷ Y i`, and `tensorUnit i := 𝟙_ (C i)` (and similarly for any adjacent pointwise fields).
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   tensorObj X Y i := X i ⊗ Y i   tensorHom f g i := f i ⊗ₘ g i   whiskerLeft X _ _ f i := X i ◁ f i   whiskerRight f Y i := f i ▷ Y i   tensorUnit i := 𝟙_ (C i) ```

## pr33183_i02  [V3/docs/dropped]
**ask**: In `Mathlib/CategoryTheory/Pi/Monoidal.lean`, revise the docstring describing the construction so it starts with “`Pi.monoidalCategory C` equips the product of an indexed family of categories with …” (i.e. explicitly name `Pi.monoidalCategory C` in the opening line of the documentation).
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion /-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ```

## pr33183_i03  [V3/style/unknown]
**ask**: In `Mathlib/CategoryTheory/Pi/Monoidal.lean`, when defining the `Closed` structure for an object `X` in the pointwise closed monoidal structure on `Π i, C i`, construct it using record syntax with explicit fields `rightAdj := ihom X`, `adj.unit := closedUnit X`, and `adj.counit := closedCounit X` (i.e. `closed X := { rightAdj := ihom X, adj.unit := closedUnit X, adj.counit := closedCounit X }`) instead of the current construction.
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   closed X := {     rightAdj := ihom X     adj.unit := closedUnit X     adj.counit := closedCounit X } ```

## pr33169_i01  [V4/style/dropped]
**ask**: In `Mathlib/LinearAlgebra/Matrix/FixedDetMatrices.lean` (the `succ` case of the `induction n with` proof around lines 228–229), revert the whitespace/line-break reformatting of the `simpa only [...]` line so it matches the previous one-line formatting (`add_comm (n:ℤ)` etc.), rather than the new multi-line version.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V4] Please revert this one; I'm not convinced it's better.

## pr33169_i02  [V2/style/adopted]
**ask**: In `Mathlib/LinearAlgebra/Matrix/FixedDetMatrices.lean`, reformat the `| succ n hn =>` induction case so that `add_comm` is written as `add_comm (n : ℤ)` (with spaces around `:`) and break the long `simpa only [...]` list across lines with proper indentation, placing `prop_red_T hS hT` on a new line as in the suggested formatting.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V2] ```suggestion   | succ n hn =>     simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,       prop_red_T hS hT] ```

## pr33158_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No change requested; the maintainer only expresses approval and indicates the PR can be merged as-is.
**anchors**:   (* = inferred)
> [V4] I'm not so sure that we will ever care about Stieltjes measures on the empty space, but in any case I agree this can't hurt. Thanks! bors r+

## pr33156_i01  [V3/docs/adopted]
**ask**: Add the missing doc-string for the newly introduced `optAttrArg` syntax in `Mathlib/Util/AddRelatedDecl.lean` (in the `namespace Mathlib.Tactic` section where it is defined/used).
**anchors**: AddRelatedDecl.lean:19*, AddRelatedDecl.lean:19*  (* = inferred)
> [V3] (Please add the missing doc-string, though.)

## pr33154_i01  [V3/docs/unknown | NOT JUDGEABLE]
**ask**: It is unclear what file or text “line 24” refers to and no code hunks are provided, so no concrete change request can be recovered beyond the question “should line 24 also mention `to_fun`?”.
**anchors**:   (* = inferred)
> [V3] Pre-existing: should line 24 also mention `to_fun`?

## pr33153_i01  [V2/other/unknown | NOT JUDGEABLE]
**ask**: No concrete change request can be recovered from the comment: the maintainer only notes they cannot see any difference in the proposed edit, without pointing to a specific file/hunk or asking for a particular modification.
**anchors**:   (* = inferred)
> [V2] I can't see the difference here. 

## pr33152_i01  [V2/duplication/dropped]
**ask**: In `Mathlib/Analysis/Meromorphic/Basic.lean`, do not add a specialized lemma `Meromorphic.meromorphicOn_univ`; instead rely on the existing lemma `Meromorphic.meromorphicOn` (supplying the implicit `s := Set.univ` argument explicitly when inference can’t find it), and if such a lemma were ever kept it would need to be `protected`.
**anchors**: Basic.lean:562*  (* = inferred)
> [V2] I don't think we generally include the new declaration `Meromorphic.meromorphicOn_univ`. It would need to be protected if we did, but you should also just be able to use `Meromorphic.meromorphicOn`. When Lean can infer `univ`, it works, and when it c

## pr33151_i01  [V2/naming/adopted]
**ask**: In `Mathlib/Tactic/Translate/ToDual.lean`, extend `GuessName.GuessNameData.abbreviationDict` (the `abbreviationDict` definition) with entries that map `succColimit` → `SuccLimit` and `predColimit` → `PredLimit` (i.e. un-translate `colimit` to `limit` specifically in the `succ`/`pred` cases) so the `to_dual` naming comes out correctly without manual fixes elsewhere.
**anchors**: ToDual.lean:181*, ToDual.lean:153*  (* = inferred)
> [V2] Is it true that all instances of the word `limit` that need to be translated are preceded by either `succ` or `pred`? In that case it may be better to use the fixAbbreviations dictionary to un-translate `colimit` to`limit` in these cases.  (I agree w
> [V2] In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.

## pr33150_i01  [V2/naming/adopted | NOT JUDGEABLE]
**ask**: In `Mathlib/Order/SuccPred/Basic.lean` (section `Preorder` around line ~828), fix the `@[to_dual ...]` annotation on `lemma le_succ_pred` because it currently generates the wrong dual lemma name; adjust the tag so the dual is named correctly (i.e. corresponds to `pred_succ_le` as intended).
**anchors**: Basic.lean:828  (* = inferred)
> [V2] I think this generates the wrong dual name

## pr33149_i01  [V1/scope/unknown | NOT JUDGEABLE]
**ask**: Remove any new `axiom`/`constant` assumptions introduced by PR #33149 (in particular, do not add any new axioms anywhere in the PR); instead, restate results as theorems with proofs or as lemmas assuming hypotheses via variables/parameters, so the PR introduces no new axioms.
**anchors**:   (* = inferred)
> [V1] Mathlib has a no-axioms policy. Please don't introduce any new axioms.

## pr33149_i02  [V2/duplication/unknown | NOT JUDGEABLE]
**ask**: Replace any custom/proved-from-scratch Parseval identity used in PR #33149 with Mathlib’s existing `Real/Complex` Parseval identity lemma (and adapt the proof to invoke it); if a specialization is truly needed (e.g. for the standard basis of `ℝ^n`), add that specialized lemma to the existing Parseval-identity location in Mathlib rather than defining a new ad-hoc version in the Navier–Stokes/ODE development.
**anchors**:   (* = inferred)
> [V2] Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).

## pr33149_i03  [V3/other/unknown | NOT JUDGEABLE]
**ask**: Remove any newly introduced axioms from this PR: replace them with actual definitions and proofs, or derive the needed assumptions from existing Mathlib results/structures, rather than postulating new axioms anywhere in the added/modified files for the Navier–Stokes Galerkin regularity development on T³.
**anchors**:   (* = inferred)
> [V3] Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) 
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33149_i04  [V4/scope/unknown | NOT JUDGEABLE]
**ask**: Rewrite the PR to meet mathlib standards by removing all new axioms: either replace them with actual definitions/structures and proven lemmas, or derive the needed assumptions from existing mathlib results, so that no `axiom`/`constant`-style placeholders remain anywhere in the added Navier–Stokes/Galerkin development (Analysis/ODE-related files).
**anchors**:   (* = inferred)
> [V4] Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33146_i01  [V3/docs/adopted]
**ask**: In `Mathlib/CategoryTheory/Category/Basic.lean`, change the docstring capitalization so that the documentation for the theorem about precomposing an equation reads `/-- Precompose an equation between morphisms by another morphism -/` (i.e. capitalize “Precompose”; similarly keep “Postcompose” capitalized).
**anchors**: Basic.lean:223  (* = inferred)
> [V3] Might as well fix some capitalization. ```suggestion /-- Precompose an equation between morphisms by another morphism -/] ```

## pr33145_i01  [V2/generalization/partially_adopted]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean` around the newly added lemmas `Dense.continuous_upperBounds`/`Dense.continuous_lowerBounds`, replace them with more general lemmas about images that do not assume continuity: add `theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ...` and `theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ...` (and use these instead of the continuous-specific versions).
**anchors**: IsLUB.lean:166, IsLUB.lean:166*  (* = inferred)
> [V2] ```suggestion theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] ```suggestion theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```

## pr33145_i02  [V2/duplication/unknown]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean`, for the forthcoming lemma `Dense.continuous_lowerBounds` (the sibling of `Dense.continuous_upperBounds`), replace the bespoke proof with the `OrderDual` trick by proving it via `hS.continuous_upperBounds (α := αᵒᵈ) hf`, e.g. `lowerBounds (f '' S) = lowerBounds (range f) := hS.continuous_upperBounds (α := αᵒᵈ) hf`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] There's a trick you can use for this kind of thing by using the `OrderDual`. ```suggestion     lowerBounds (f '' S) = lowerBounds (range f) :=   hS.continuous_upperBounds (α := αᵒᵈ) hf ```

## pr33145_i03  [V2/naming/dropped]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean` (around the new lemmas added after line ~166), add the suggested theorems `theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ...` and `theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ...` (as `Dense`-namespace lemmas) corresponding to the PR’s new results about sup/inf of a continuous function on a dense set equaling the sup/inf on `univ`/`range`.
**anchors**: IsLUB.lean:166, IsLUB.lean:166*  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ```

## pr33145_i04  [V2/style/unknown]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean` at the proof that identifies the `iInf`/`iSup` over a dense subset with the one over the ambient type (the lemma where you currently write something like `⨅ i, f i = ⨅ s : S, f s := ...`), replace the manual proof with the existing lemma `hS.ciSup' (α := αᵒᵈ) hf` (or `hS.ciSup (α := αᵒᵈ) hf h` if the extra hypothesis `h` is needed).
**anchors**: IsLUB.lean:166, IsLUB.lean:166*  (* = inferred)
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup (α := αᵒᵈ) hf h ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup' (α := αᵒᵈ) hf ```

## pr33145_i05  [V2/naming/dropped]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean` around the new `Dense.continuous_upperBounds`/`Dense.continuous_lowerBounds` lemmas (hunk at line ~166), add corresponding theorems named `Dense.ciSup'` and `Dense.ciInf'` (with implicit arguments starting `theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ...` and similarly for `ciInf'`).
**anchors**: IsLUB.lean:166, IsLUB.lean:166*  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf' {α : Type*} [TopologicalSpace α] ```

## pr33145_i06  [V2/style/unknown]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean`, simplify the proof of `Dense.continuous_upperBounds` by splitting on whether `BddAbove (range (fun x : S ↦ f x))` holds; in the bounded case, use `hS.ciSup hf` together with `h.closure.mono` and `hf.range_subset_closure_image_dense hS`, and in the unbounded case reduce to `¬ BddAbove (range f)` and finish by `simp [ciSup_of_not_bddAbove]` (as in the suggested proof sketch).
**anchors**: IsLUB.lean:166, IsLUB.lean:166*  (* = inferred)
> [V2] It's easier if you case split on whether the range of the function from the subtype is bounded above or not. ```suggestion   by_cases h : BddAbove (range (fun x : S ↦ f x))   · refine hS.ciSup hf <| h.closure.mono ?_     simpa [← Function.comp_def, r

## pr33145_i07  [V3/style/unknown | NOT JUDGEABLE]
**ask**: In `Mathlib/Topology/Order/IsLUB.lean`, rewrite any lemmas/declarations in this PR that state an equality involving `iSup`/`iInf` so that the left-hand side is the `S`-indexed supremum/infimum and the right-hand side is the `i`-indexed one; e.g. prefer `⨆ s : S, f s = ⨆ i, f i := by` (and similarly for `iInf`) instead of the reversed equality.
**anchors**: IsLUB.lean:166*, IsLUB.lean:166*  (* = inferred)
> [V3] I suggest turning the declarations involving `iSup` and `iInf` around so that they read: ```lean     ⨆ s : S, f s = ⨆ i, f i := by ``` instead.

## pr33144_i01  [V4/scope/unknown | NOT JUDGEABLE]
**ask**: No concrete change requested: the maintainer only raises the question of whether the redundant `fun_` lemmas should be removed at all (PR-level scope decision), without specifying any code edits.
**anchors**:   (* = inferred)
> [V4] This PR itself it straightforward; the main question is whether we want it.

## pr33144_i02  [V2/duplication/unknown]
**ask**: In `Analysis/Meromorphic/Basic`, remove the unused redundant `fun_`-prefixed lemma variants (i.e., do not add/keep `fun_` versions unless they are actually needed/used elsewhere).
**anchors**:   (* = inferred)
> [V2] @kebekus Thanks for the explanation! Let's only add `fun_` versions as needed then --- as these lemmas are unused, let's remove them. bors r+

## pr33141_i01  [V2/style/adopted]
**ask**: In `Mathlib/RingTheory/Coalgebra/MonoidAlgebra.lean`, add `@[to_additive (relevant_arg := X)]` to every declaration in this file that uses `to_additive` (not just some of them), i.e. ensure the `relevant_arg := X` option is present consistently on the `to_additive` attributes for `instCoalgebra`, `instIsCocomm`, `counit_single`, and `comul_single` (and any other `to_additive`-tagged declarations in the file).
**anchors**: MonoidAlgebra.lean:35  (* = inferred)
> [V2] I think you need the `(relevant_arg := X)` on all of the declarations in this file

## pr33137_i01  [V2/style/unknown]
**ask**: In `Mathlib/Algebra/MonoidAlgebra/Basic.lean`, in the definition `mapDomainNonUnitalAlgHom`, replace the lambda `map_mul' := fun x y => mapDomain_mul f x y` with the eta-reduced form `map_mul' := mapDomain_mul f`.
**anchors**: Basic.lean:217  (* = inferred)
> [V2] ```suggestion   map_mul' := mapDomain_mul f ```

## pr33127_i01  [V2/scope/adopted]
**ask**: Remove the `example {n : ℕ} [NeZero n] (hn : 2 ≤ n) : (1 : Fin n).val = 1 := by ...` test code from `Mathlib/Order/Interval/Finset/Fin.lean` near the `pm_one` section (around line 896), leaving only the intended lemmas.
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V2] I assume this is test code, and can be removed? ```suggestion ```

## pr33127_i02  [V3/docs/adopted]
**ask**: In `Mathlib/Order/Interval/Finset/Fin.lean`, at the start of the section `/-! ### Perturbations of endpoints by one -/` (section `pm_one`, around the lemmas like `Iio_add_one_eq_Iic`), turn the existing explanatory `/- ... -/` note about the `haveI`/`[NeZero n]` design choice into a proper comment at the top of the section (so future readers see the rationale immediately).
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V3] This may be worth turning into a comment at the top of the section!

## pr33117_i01  [V2/style/partially_adopted]
**ask**: In `Mathlib/Analysis/Meromorphic/Basic.lean`, import `Mathlib.Tactic.ToFun` (non-`public`) and change the lemmas in `namespace Meromorphic` such as `Meromorphic.neg`, `Meromorphic.add`, and the subsequent similar lemmas (`sum`, etc.) to use the `@[to_fun (attr := fun_prop)]` attribute instead of plain `@[fun_prop]`, so `fun_prop` can see through the `Meromorphic` definitional wrapper via `to_fun`.
**anchors**: Basic.lean:631, Basic.lean:8*, Basic.lean:632*  (* = inferred)
> [V2] There is some new metaprogramming that can help here: the `to_fun` attribute. To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).  ```suggestion @[to_fun (attr := fun_prop)] lemma neg (hf : Meromorphic

## pr33111_i01  [V3/naming/partially_adopted | NOT JUDGEABLE]
**ask**: In `Mathlib/Order/Monotone/Defs.lean`, rename the newly introduced/weakened lemma currently called `injective_of_le_imp_le` to `injective_of_eq_imp_le` (and then adjust the naming of the related `injective_of_*_imp_*` lemmas in the same area for consistency, updating any downstream uses accordingly).
**anchors**: Defs.lean:320*  (* = inferred)
> [V3] why not call it `injective_of_eq_imp_le`?
> [V3] Meh, rename away. I only suggested it to keep things consistent. So let's keep things consistent and rename the others in a better way!

## pr33111_i02  [V2/style/partially_adopted]
**ask**: In `Mathlib/Order/Monotone/Defs.lean`, at the new lemma/proof around `injective_of_le_imp_le`, move the new lemma earlier (before the lemma being proved) and simplify the proof by either replacing the current argument with the suggested `exact injective_of_eq_imp_le f (fun {x y} ↦ not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x))` proof, or by using `grind [injective_of_eq_imp_le]`.
**anchors**: Defs.lean:320*  (* = inferred)
> [V2] if you move the new lemma before this one, you could do ```suggestion   exact injective_of_eq_imp_le f fun {x y} ↦     not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x) ``` or ```suggestion   grind [injective_of_eq_imp_le] ```

## pr33111_i03  [V4/docs/unknown | NOT JUDGEABLE]
**ask**: In PR #33111, update the PR title (and any related description text) to accurately reflect the change: it is not a weakening of the hypothesis of `injective_of_le_imp_le`, but rather the addition of a new lemma/variant that works in a more general setting.
**anchors**:   (* = inferred)
> [V4] The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.

## pr33111_i04  [V3/scope/dropped]
**ask**: In `Mathlib/Order/Monotone/Defs.lean`, do not change the existing theorem `injective_of_le_imp_le`; instead keep it with its current statement and add a `@[deprecated Function.Injective.of_... (since := ...)]` attribute pointing users to the new `Function.Injective.of_...` lemma.
**anchors**: Defs.lean:320*  (* = inferred)
> [V3] You could deprecate it. Probably a good idea. ~~But I'd suggest keeping the theorem as is, just add the `@[deprecated Function.Injective.of_... (since := ...)]`.~~

## pr33107_i01  [V4/scope/unknown | NOT JUDGEABLE]
**ask**: Refactor the core definitions `LinearMap.range` and `LinearMap.ker` in Mathlib so they take an actual `LinearMap`/`LinearMapClass` instance argument (i.e. the morphism itself) rather than being defined in terms of the linear-map *class*; this enables dot-notation and makes range/ker simp lemmas for structures like `ContinuousLinearMap` come for free.
**anchors**:   (* = inferred)
> [V4] I think we should refactor the definitions of `LinearMap.range` and `LinearMap.ker` to take in an actual linear map and not a linear map class. That way, all of this comes for free. It'll also allow for dot notation, solve more of these issues, etc..
> [V4] @Timeroot yes, Monica is correct here. Unfortunately you are exposing a flaw that exists currently in the library. Help ripping it out is encouraged! For more information see the Zulip thread: [#mathlib4 > Mathlib's morphism hierarchy](https://leanpr

## pr33104_i01  [V3/naming/unknown | NOT JUDGEABLE]
**ask**: Define the transfer constructions as protected abbreviations named `pseudoMetricSpace` for both equivalence types—add `protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ...` and similarly `protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ...`—so they can be referenced as `Homeomorph.pseudoMetricSpace` and `UniformEquiv.pseudoMetricSpace`.
**anchors**:   (* = inferred)
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ```
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ```

## pr33101_i01  [V3/scope/adopted]
**ask**: In `Mathlib/LinearAlgebra/Dual/Lemmas.lean`, avoid duplicating the global `variable {K V₁ V₂ : Type*} [Field K] [AddCommGroup V₁] [Module K V₁] [AddCommGroup V₂] [Module K V₂]` declarations introduced after `end Module.Dual` by enclosing the preceding block of declarations in an explicit `section ... end` (or otherwise restructuring scope) so that variable scopes are clear and do not create surprising redeclarations before `namespace LinearMap` and `theorem dualPairing_nondegenerate`.
**anchors**: Lemmas.lean:781, Lemmas.lean:780  (* = inferred)
> [V3] It looks like this duplicates the `variable`s.  Could you enclose the previous one in a `section`/`end` block, to avoid "surprises"?

## pr33098_i01  [V2/proof-golf/unknown]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, simplify the subset lemmas for the new definitions by proving them via `grind`: replace the manual proofs of `minimalCover_subset` with `by grind [minimalCover]` (after adding `attribute [grind .] finite_empty` so `grind` can handle `finite_minimalCover`), and similarly replace the manual proof of `maximalSeparatedSet_subset` with `by grind [maximalSeparatedSet]` (after adding `attribute [grind .] IsSeparated.empty` so `grind` can handle `isSeparated_maximalSeparatedSet`).
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add ```lean attribute [grind .] finite_empty ``` but I think we should do that anyway. ```suggestion lemma minimalCover_subset : min
> [V2] This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add ```lean attribute [grind .] IsSeparated.empty ``` but I think we should do that anyway.  ```suggestion lemma maximalSe

## pr33098_i02  [V2/naming/dropped]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, rename the newly added lemmas to follow the `encard_...` naming scheme: change `exists_set_encard_eq_coveringNumber` to `encard_minimalCover`, similarly add/rename the corresponding packing lemma to `encard_maximalSeparatedSet`, and rename the supporting lemma about cardinal bounds for separated sets to `encard_le_of_isSeparated (h_subset : C ⊆ A)`.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] ```suggestion lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_le_of_isSeparated (h_subset : C ⊆ A) ```

## pr33098_i03  [V2/proof-golf/unknown]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, refactor the proof around the `by_contra!`/`insert` step to use the lemma `Metric.isSeparated_insert_of_notMem` (as in the suggested golf), simplifying the construction and separation proof for `{x} ∪ maximalSeparatedSet ε A`; apply this change to the corresponding proof occurrence(s) in the hunk(s) at line ~351/390 where the same argument is repeated.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228, CoveringNumbers.lean:351*, CoveringNumbers.lean:390*  (* = inferred)
> [V2] I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`. ```lean   intro x hxA   by_contra! h_dist   let C :=

## pr33098_i04  [V2/style/partially_adopted]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, revise the proof of `theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X)` to use `by_cases! h_top : packingNumber ε A ≠ ⊤` (so negations are pushed automatically) and replace the current `iInf_le`/`simp` argument with the lemma `IsCover.coveringNumber_le_encard` applied to `isCover_maximalSeparatedSet h_top`, after rewriting by `← encard_maximalSeparatedSet h_top` (and keep the `⊤` case as `simp [h_top]`).
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley: ```suggestion   by_cases! h_top : packingNumber ε A ≠ ⊤   · rw [← 

## pr33098_i05  [V2/style/unknown]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, in the proof of `theorem coveringNumber_two_mul_le_externalCoveringNumber` (around the added case split on `A`), replace the manual `rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty); · simp [h_empty]` with the pattern `rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty); · simp` (i.e. use `rfl` for the empty-case and discharge it by `simp`).
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] ```suggestion   rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)   · simp ```

## pr33098_i06  [V3/style/unknown]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, in the proof block around line ~390 (hunk `Mathlib/Topology/MetricSpace/CoveringNumbers.lean@a660288aa0`), reformat the inequality-to-`calc` step so that the `:= calc` is placed on the same line as the inequality statement (e.g. `coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc ...`), to avoid needing to indent all subsequent `calc` lines per style guidelines.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V3] otherwise style guidelines would require to indent all lines below the first `calc` line. ```suggestion     coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc   coveringNumber ε A ```

## pr33092_i01  [V3/docs/adopted]
**ask**: In `Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean`, for the private definition `walk_toSimpleGraph` (formerly `walk_toSimpleGraph'`) add a docstring explanation of why it exists despite being private, explicitly stating which subsequent public result it is used to prove (e.g. `reachable_toSimpleGraph`).
**anchors**: Connected.lean:643, Connected.lean:643, Connected.lean:653  (* = inferred)
> [V3] I don't undertand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.

## pr33090_i01  [V3/style/dropped]
**ask**: In `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`, replace the one-way positivity simp lemma `externalCoveringNumber_pos (hA : A.Nonempty) : 0 < externalCoveringNumber ε A` with an iff lemma `externalCoveringNumber_pos_iff : 0 < externalCoveringNumber ε A ↔ A.Nonempty` (so `simp` can use it more efficiently).
**anchors**: CoveringNumbers.lean:80, CoveringNumbers.lean:98, CoveringNumbers.lean:80*  (* = inferred)
> [V3] Could you make this one an iff lemma? `simp` would be more efficient then.

## pr33086_i01  [V3/docs/unknown]
**ask**: In `Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean`, add explicit documentation (docstrings and/or module docs near the introductions of the APIs) explaining the intended usage difference between `cofibrantObjects`/`fibrantObjects` and the Prop-classes `IsCofibrant`/`IsFibrant`: namely that `IsCofibrant`/`IsFibrant` should be used as Prop-classes on objects, while `cofibrantObjects`/`fibrantObjects` are just object-properties (not meant to be used as instances), and similarly for the fibrant/bifibrant variants.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] I think there should be a documentation entry here about the "intented usages" of the two APIs `cofibrantObjects`/`IsCofibrant`. As far as I understand, `IsCofibrant` is to be used as a Prop-Class, while the object property shouldn’t. This needs to b

## pr33086_i02  [V3/duplication/unknown]
**ask**: In `Mathlib/AlgebraicTopology/ModelCategory/Bifibrant.lean`, add the missing simp lemma
```lean
@[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}
    [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :
    WeakEquivalence (homMk f) ↔ WeakEquivalence f := by
  simp only [weakEquivalence_iff]
  rfl
```
so it is available alongside the corresponding lemmas for the other properties.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] Was this one intentionally left out compared to the others?  ```suggestion  @[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}     [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :     We

## pr33081_i01  [V2/proof-golf/unknown | NOT JUDGEABLE]
**ask**: Replace the existing lambda/proof term with the more explicit term `fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl)` (at the place in the PR where a function `fun i _ ↦ ...` is used to produce membership in an `iUnion` of a `setOf`), using `Set.mem_iUnion_of_mem` and `Set.mem_setOf.mpr le_rfl`.
**anchors**:   (* = inferred)
> [V2] ```suggestion     fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl) ```

## pr33079_i01  [V3/naming/dropped]
**ask**: In `Mathlib/Data/Fin/Basic.lean` at the newly added lemma near line ~90, rename the lemma `neZero` to `Fin.neZero` (so it can be used via dot-notation), and simplify its proof to a direct constructor proof such as `⟨i.2.ne⟩`/`⟨Nat.ne_zero_of_lt i.isLt⟩` rather than the longer `neZero_of_exists`-style argument; remove/avoid adding the redundant alternative lemma.
**anchors**: Basic.lean:90, Basic.lean:90  (* = inferred)
> [V3] Does something like ⟨i.2.ne⟩ work as a proof? Also, what about calling this `Fin.neZero` for dot notation?

## pr33078_i01  [V2/style/adopted]
**ask**: In `Mathlib/NumberTheory/MahlerMeasure.lean`, in the proof of `theorem cyclotomic_mahlerMeasure_eq_one`, avoid manually constructing `NeZero (n : ℂ)` (e.g. via `@NeZero.charZero ...`) and instead assume/provide `have : NeZero n := ⟨hn⟩` from `hn : n ≠ 0`, letting typeclass inference obtain `NeZero (n : ℂ)`; correspondingly simplify the proof along the lines of reducing to showing `∀ z ∈ primitiveRoots n ℂ, ‖z‖ ≤ 1` and using `IsPrimitiveRoot.norm'_eq_one (isPrimitiveRoot_of_mem_primitiveRoots hz) hn`.
**anchors**: MahlerMeasure.lean:113, MahlerMeasure.lean:113  (* = inferred)
> [V2] I think it is enough to provide `NeZero n`, and then the typeclass system will find `have : NeZero (n : ℂ)`.
> [V2] ```suggestion   have : NeZero n := ⟨hn⟩   suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1 by     simpa [mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ,       Polynomial.cyclotomic.roots_eq_primitiveRoots_val]   suffices ∀ a ∈ pri

## pr33070_i01  [V2/style/adopted]
**ask**: In `Mathlib/Algebra/BigOperators/Group/Finset/Defs.lean` around the `Finset.sum` pretty-printer code at line ~296 (both corresponding changed hunks), replace the binder-annotation setup with the simpler equivalent `let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes` (i.e., use `getPPOption getPPFunBinderTypes` under `withAppArg` instead of the current approach).
**anchors**: Defs.lean:296*  (* = inferred)
> [V2] I think this is the same as ```suggestion   let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes ```

## pr33067_i01  [V2/other/dropped]
**ask**: In `Mathlib/Tactic/Recall.lean`’s `recall` command elaborator and similarly in `Mathlib/Util/AliasIn.lean` for the `alias_in` command, adjust the syntax info annotations so that `isBinder` is set to `true` only for syntax that actually creates a new declaration in the environment; in particular, do not mark `recall` (and likewise `alias_in`) as a binder location for jump-to-definition purposes.
**anchors**: Recall.lean:44, AliasIn.lean:55*  (* = inferred)
> [V2] `isBinder` should be true only when this piece of syntax generates a declaration in the environment (so this point should be used as the "jump-to" location). That does not hold for `recall`, right?
> [V2] Can you also change `alias_in` please? Thanks!  I am surprised that without this, jump-to-definition still works. I thought the `isBinder` annotation was responsible for that (maybe jump-to-definition uses a non-binder location as fallback?)

## pr33066_i01  [V3/docs/adopted]
**ask**: In `Mathlib/Analysis/InnerProductSpace/Adjoint.lean`, at the docstring immediately preceding `LinearIsometryEquiv.conjStarAlgEquiv` (the new `namespace LinearIsometryEquiv` block after `end ContinuousLinearMap`, around line ~683 in both sibling hunks), fix the wording to say “An isometric linear equivalence …” (not “An isometry linear equivalence …”).
**anchors**: Adjoint.lean:683  (* = inferred)
> [V3] ```suggestion /-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of ```

## pr33066_i02  [V2/duplication/dropped]
**ask**: In `Mathlib/Topology/Algebra/Algebra/Equiv.lean` (around the new definition at line ~302), delete the newly added definition `ContinuousAlgEquiv.ofAlgEquiv` and its accompanying simp lemmas (`coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`, `ofAlgEquiv_trans_ofAlgEquiv`, etc.), and instead use the existing constructor `ContinuousAlgEquiv.mk` (or the existing API) to build a `ContinuousAlgEquiv` from an `AlgEquiv` together with continuity proofs.
**anchors**: Equiv.lean:302  (* = inferred)
> [V2] This is just the pre-existing constructor for `ContinuousAlgEquiv`: ``` ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]   [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra

## pr33066_i03  [V2/style/unknown]
**ask**: In `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean` at the proof near line 85, restate the goal using a typed hole `_` and remove the explicit elaboration: write `Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ...`, letting Lean infer the codomain.
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V2] You can still phrase this as: ```suggestion     Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ``` and I think Lean shouldn't need you to fill in the `_`.

## pr33066_i04  [V3/docs/partially_adopted]
**ask**: In `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean` (around the new `section auxiliaryDefs` starting near line 85), intersperse the new development with explanatory comments/docstrings throughout the code, rather than presenting a large uncommented block (e.g. add brief comments before/around `auxContinuousLinearEquiv` and related definitions/lemmas to explain the purpose and flow).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V3] This is nice, but it would be even nicer if it were interspersed throughout the code.

## pr33066_i05  [V3/style/adopted]
**ask**: In `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean`, in the `section auxiliaryDefs` variable block introducing `e : V ≃L[𝕜] W` and scalars `α α'`, reorder/simplify the binder so that the `variable` line reads `variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)` (i.e. make `α`/`α'` implicit and place them before the hypothesis `hα`).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V3] ```suggestion section auxiliaryDefs  variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0) ```

## pr33066_i06  [V3/naming/unknown | NOT JUDGEABLE]
**ask**: In `Mathlib/Analysis/Normed/Operator/ContinuousAlgEquiv.lean` (around the new `section auxiliaryDefs` starting near line 85), rename/improve the names of the local `have` statements in the added proofs so they are descriptive and maintainable (instead of vague or placeholder names).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V3] The naming of your `have`s could use some work. Please improve them.

## pr33065_i01  [V3/docs/dropped]
**ask**: In `Mathlib/Topology/ContinuousOn.lean`, update the docstring for `ContinuousWithinAt.of_not_accPt` (and thus the surrounding added documentation) to fix the wording: replace “accumulated point” with the standard term “accumulation point” in the opening comment line.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V3] ```suggestion /-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulation point of ```

## pr33065_i02  [V3/naming/adopted]
**ask**: In `Mathlib/Topology/ContinuousOn.lean` around the new lemmas after `continuousWithinAt_singleton.diff_iff`, rename `ContinuousWithinAt.of_not_accPt` to `continuousWithinAt_of_not_accPt` and rename `ContinuousAt.of_not_accPt` to `continuousAt_of_not_accPt` (updating their docstrings and all uses) to match existing naming conventions for lemmas that don’t take a continuity hypothesis.
**anchors**: ContinuousOn.lean:296, ContinuousOn.lean:296*  (* = inferred)
> [V3] I think it would make sense to call this `continuousWithinAt_of_not_accPt` instead to stay consistent with e.g. `continuousWithinAt_of_notMem_closure` - since the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used m
> [V4] Note that `AccPt x (𝓟 {x}ᶜ)` is equivalently just `AccPt x ⊤`: ``` import Mathlib  open Topology Filter Set  example {α : Type*} [TopologicalSpace α] {x : α} : AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤ := by   simp [← principal_univ, accPt_principal_iff_nh

## pr33057_i01  [V1/other/adopted | NOT JUDGEABLE]
**ask**: Fix the remaining CI/proof error in PR #33057 (the last failing check), then re-run and obtain a successful `bors d+` merge approval.
**anchors**: Mathlib.lean:6088*, Expand.lean:7*, Expand.lean:84*, Expand.lean:189*, Basic.lean:71*, Expand.lean:1*, Expand.lean:33*  (* = inferred)
> [V1] Thanks! Delegating so you can fix the last error.   bors d+

## pr33056_i01  [V4/naming/unknown | NOT JUDGEABLE]
**ask**: Do not proceed with standardizing the spelling of ℵ₁ as `aleph1` without first holding a Zulip vote/consensus on the naming convention for this identifier (e.g. whether to prefer `alephOne` or `aleph_one` over numerals in identifiers).
**anchors**:   (* = inferred)
> [V4] I think there should be a Zulip vote for this. I would have expected that we go the *other* way, potentially with `alephOne` instead of `alepha_one`. The point being that we generally don't use numerals in identifiers (cf. `cos_pi_div_two` for exampl

## pr33048_i01  [V3/other/adopted]
**ask**: In `Mathlib/Algebra/Order/Ring/Archimedean.lean`, add a simp lemma for `ArchimedeanClass.mk` on `ofNat` under `[n.AtLeastTwo]`, namely
```
@[simp] theorem mk_ofNat {n : ℕ} [n.AtLeastTwo] : mk (ofNat n : S) = 0 :=
  mod_cast mk_intCast (n := n)
```
(and similarly in the parallel section/hunk if needed), since currently only the `mk_natCast` lemma with an explicit `n ≠ 0` hypothesis exists.
**anchors**: Archimedean.lean:181, Archimedean.lean:174  (* = inferred)
> [V3] Just realising: we do not have  ``` @[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 :=   mod_cast mk_intCast (n := n) ``` Mind adding?

## pr33048_i02  [V2/style/partially_adopted]
**ask**: In `Mathlib/Algebra/Order/Ring/StandardPart.lean` around the new `FiniteElement.mk_*` simp lemmas (hunk `StandardPart.lean@10afa56872`), change the binders for the hypotheses `hx` and `hy` from implicit (`{hx : 0 ≤ mk x}` / `{hy : 0 ≤ mk y}`) to explicit (`(hx : 0 ≤ mk x)` / `(hy : 0 ≤ mk y)`) in the lemmas `mk_add`, `mk_sub`, `mk_mul`, `mk_le_mk_iff`, and `mk_lt_mk_iff`, so they can be used for backwards rewriting.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V2] ```suggestion theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ``` Same below
> [V3] I would make those explicit for backwards rewriting: ```suggestion theorem mk_lt_mk_iff {x y : K} (hx hy) : ```

## pr33048_i03  [V3/naming/unknown]
**ask**: In `Mathlib/Algebra/Order/Ring/StandardPart.lean` around the new simp lemmas for `FiniteElement.mk`, remove the `_iff` suffix from `mk_le_mk_iff` by renaming it to `mk_le_mk` (keeping the same statement `FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y := .rfl`).
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] Do we really need the `_iff` here? ```suggestion theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :     FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=   .rfl ```

## pr33048_i04  [V3/style/unknown]
**ask**: In `Mathlib/Algebra/Order/Ring/StandardPart.lean`, add a `RatCast` instance for `FiniteElement K` (e.g. `instance : RatCast (FiniteElement K) where ...`) so that rationals can be coerced/cast into `FiniteElement K` directly, instead of relying on existing coercions.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] ```suggestion instance : RatCast (FiniteElement K) where ``` no?

## pr33047_i01  [V4/style/unknown | NOT JUDGEABLE]
**ask**: No concrete change request can be recovered from the review: the maintainer only asks for justification of preferring the longer spelling `toSpanSingleton` over `smulRight (1 : R →L[R] R)` (or vice versa), without pointing to any specific location or requesting a specific edit in any file/lemma.
**anchors**:   (* = inferred)
> [V4] Might I ask why the longer spelling should be the preferred one?

## pr31342_i01  [V3/docs/unknown]
**ask**: Add a descriptive summary of what the PR does to the PR message/description (the text shown on the PR itself), explaining the change that `extract_goal` now preserves explicit `forall`s.
**anchors**:   (* = inferred)
> [V3] Could you add a description to the PR message?
