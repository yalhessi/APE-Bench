# Interventions review digest

113 interventions | judgeable 87 | outcomes {'adopted': 36, 'dropped': 46, 'unknown': 21, 'partially_adopted': 9, 'contested': 1}

## pr33421_i01  [V3/naming/adopted]
**ask**: Rename the lemma `round_eq'` to `round_eq_div`.
**why** (stated): Maintainer asked “How about `round_eq_div`?”, indicating the current name `round_eq'` should be replaced by a more descriptive API name reflecting the division-by-2 formula.
**anchors**: Round.lean:45  (* = inferred)
> [V3] How about `round_eq_div`?

## pr33421_i02  [V2/duplication/dropped | NOT JUDGEABLE]
**ask**: Replace the ad-hoc repeated proof pattern with a general lemma (and use it here and in the immediately following theorem), rather than re-proving the same “very general” fact inline.
**why** (stated): The reviewer notes “Is this not something very general that should exist as a lemma? Same in the next theorem”, indicating the proof steps in this theorem and the next one are generic and should be factored out into a reusable lemma to avoid duplication.
**anchors**: Floor.lean:195  (* = inferred)
> [V2] Is this not something very general that should exist as a lemma? Same in the next theorem

## pr33421_i03  [V2/generalization/adopted]
**ask**: Replace the specialized lemma `two_mul_fract_eq_one_iff_exists_int` about `2 * fract x = 1` with a generalized lemma `mul_fract_eq_one_iff_exists_int` parameterized by a factor `k : R` and hypothesis `hk : 1 < k`, stating `k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1`, and adjust the proof to use `hk0 : 0 < k` derived from `hk` (instead of `two_pos`) and include `hk` in the final simp.
**why** (stated): The maintainer suggests generalizing from the hard-coded constant `2` to an arbitrary multiplier `k` (with `1 < k`) to make the lemma more reusable and avoid a narrowly specialized API lemma; this also requires replacing `two_pos` with a derived positivity fact `hk0` and updating simp inputs accordingly.
**anchors**: Ring.lean:267, Ring.lean:267  (* = inferred)
> [V2] Better I think as ```suggestion theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :     k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by   rw [fract, mul_sub, sub_eq_iff_eq_add']   refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩   rintro ⟨

## pr33419_i01  [V3/naming/adopted]
**ask**: Rename the new lemma `eq_card_diff_of_sdiff` to `card_sub_card_eq` (keeping the statement `#t - #s = #(t \ s) - #(s \ t)`).
**why** (stated): The maintainer could not parse the proposed name and suggested a clearer name: `lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) :=`.
**anchors**: Card.lean:574  (* = inferred)
> [V3] I couldn't parse the name you proposed. ```suggestion lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ```

## pr33413_i01  [V2/style/dropped | NOT JUDGEABLE]
**ask**: Optionally use the `to_dual` attribute to auto-generate both deprecated aliases when renaming theorems (instead of writing the two aliases manually), provided this works with automated deprecated-declaration removal.
**why** (stated): Maintainer notes that `to_dual` can generate both deprecated aliases “at once”, which would streamline the rename/alias churn, but they are unsure whether the tooling for automated removal of deprecated declarations supports aliases generated this way.
**anchors**:   (* = inferred)
> [V2] Thanks :tada:  maintainer merge  (You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want, but I don't know if the automated removal of deprecated declarations works with that)

## pr33401_i01  [V2/style/adopted]
**ask**: Refactor the proof of `Subgroup.closure_pow_le` to use the suggested simp/rewriting structure: replace the custom `0`-case proof with `| 0 => by simp_all`, and replace the `n+1`-case `calc` chain with `| n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem]`.
**why** (stated): The maintainer proposes shorter, more idiomatic proof steps: discharge the `0` case by simp, and avoid the explicit `calc` block in the successor case by using `grw` with the relevant rewrite lemmas (`pow_succ`, `closure_mul_le`, recursive `closure_pow_le`, `sup_idem`).
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | 0 => by simp_all ```
> [V2] ```suggestion   | n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem] ``` instead of the `calc ...`

## pr33400_i01  [V3/naming/dropped]
**ask**: Rename the relevant identifier currently named along the lines of `cont_diff` to `contDiff` to match Mathlib naming conventions.
**why** (stated): The maintainer says: “I think we should also rename this to `contDiff`”, indicating the existing name uses the older/incorrect casing and should be updated to the standard `contDiff`.
**anchors**:   (* = inferred)
> [V3] pre-existing: I think we should also rename this to `contDiff`

## pr33395_i01  [V4/naming/adopted]
**ask**: Rename the theorem `IntrinsicStar.starLinearEquiv_eq` to `IntrinsicStar.starLinearEquiv_eq_arrowCongr` (keeping the statement `starLinearEquiv R (A := E →ₗ[R] F) = (starLinearEquiv R).arrowCongr (starLinearEquiv R)` unchanged).
**why** (stated): Maintainer prefers a more explicit/verbose name indicating the RHS is `arrowCongr`, since otherwise it’s hard to guess what appears on the other side of the equality: “It’s verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this.”
**anchors**: LinearMap.lean:126  (* = inferred)
> [V4] I like this the best. It's verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this. ```suggestion theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ```

## pr33376_i01  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: Clarify whether the newly introduced lemma is actually needed for this PR; if it is unused, drop it (or otherwise justify its inclusion).
**why** (stated): The maintainer notes the lemma is "reasonable" but questions its relevance to the stated housekeeping goal (fixing a non-terminal simp lemma), implying it should not be added unless it is used by the PR.
**anchors**:   (* = inferred)
> [V2] This is a reasonable lemma, but you're not using it for this PR, right?

## pr33373_i01  [V2/duplication/unknown]
**ask**: Rewrite the proof of `iteratedDeriv_comp_sub_const` to reuse existing shift lemmas by simplifying `z - s` as `z + (-s)` and then applying `iteratedDeriv_comp_add_const` (i.e. replace the inductive/deriv-based proof with `simp [sub_eq_add_neg, iteratedDeriv_comp_add_const]`).
**why** (stated): Maintainer asks to “reuse the existing theorems” and explicitly suggests `simp [sub_eq_add_neg, iteratedDeriv_comp_add_const]`, avoiding a redundant induction/`deriv_comp_sub_const` proof by reducing subtraction to addition with negation and invoking the already-proved add-constant lemma.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simp [sub_eq_add_neg, iteratedDeriv_comp_add_const] ```
> [V2] Let's reuse the existing theorems:

## pr33373_i02  [V2/duplication/dropped]
**ask**: Refactor the new shift-invariance lemma(s) to reuse existing theorems (notably `iteratedDeriv_comp_neg` and `iteratedDeriv_comp_add_const`) by proving them via `simpa`/rewriting (e.g. `simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using iteratedDeriv_comp_neg n (fun z => f (z + s))`) instead of introducing a fresh induction/derivative-comp proof.
**why** (stated): The maintainer explicitly asks to “reuse the existing theorems” and provides a concrete `simpa` proof pattern deriving the desired statement from `iteratedDeriv_comp_neg` plus rewriting (`neg_add_eq_sub`, `iteratedDeriv_comp_add_const`), avoiding duplicative induction arguments.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using     iteratedDeriv_comp_neg n (fun z => f (z + s)) ```
> [V2] Let's reuse the existing theorems:

## pr33362_i01  [V3/scope/adopted]
**ask**: Move the relevant declarations a few lines down so they are placed inside the `namespace Complex` (i.e. start `namespace Complex` earlier so the subsequent lemmas live in that namespace).
**why** (stated): The maintainer asks: “Why not move these a few lines below so that it's on the `Complex` namespace?”—i.e. adjust the placement of `namespace Complex`/surrounding structure so the items in question are actually within `Complex`.
**anchors**: Schwarz.lean:40, Schwarz.lean:40  (* = inferred)
> [V3] Why not move these a few lines below so that it's on the `Complex` namespace?

## pr33357_i01  [V3/docs/dropped]
**ask**: Fix the typo in the PR description.
**why** (stated): The maintainer comment explicitly says “there's a typo in your PR desc”, indicating the only requested change is correcting that textual typo in the pull request description (not code).
**anchors**:   (* = inferred)
> [V3] (there's a typo in your PR desc)

## pr33356_i01  [V2/style/adopted]
**ask**: Refactor the proof of `hasDetPlusMinusOne_iff_abs_det` to use `refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩` as the initial structure of the ↔-proof (i.e. provide the forward implication by `h.abs_det` and set up the backward implication by introducing the `HasDetPlusMinusOne` constructor hole).
**why** (stated): The maintainer suggests a cleaner, more idiomatic `refine ⟨..., ...⟩` structure for the equivalence proof, directly using the existing lemma/method `h.abs_det` for the forward direction and preparing the backward direction via `⟨?_⟩` to fill the `HasDetPlusMinusOne` field.
**anchors**: ArithmeticSubgroups.lean:43  (* = inferred)
> [V2] ```suggestion   refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩ ```

## pr33349_i01  [V4/other/dropped | NOT JUDGEABLE]
**ask**: Resolve the lack of consensus on the proposed change (i.e. decide/clarify whether to keep or revert the indentation/style change in the `extends` list of `LinearOrderedAddCommGroupWithTop`, rather than proceeding without agreement).
**why** (stated): The maintainer comment “I don't think there is consensus here?” indicates the change as presented is contentious/unclear and should not be merged until agreement is reached; the only visible concrete change in the referenced hunk is a whitespace/indentation adjustment in the `extends` clause, so the decision target is whether that formatting change should stand.
**anchors**: AddGroupWithTop.lean:41  (* = inferred)
> [V4] I don't think there is consensus here?

## pr33349_i02  [V2/style/unknown]
**ask**: Add the simp lemmas `add_le_add_iff_left_of_ne_top`, `add_le_add_iff_right_of_ne_top`, `add_lt_add_iff_left_of_ne_top`, and `add_lt_add_iff_right_of_ne_top` (in that usual left/right order), each proved via `(add_left_strictMono_of_ne_top _ h).le_iff_le` / `.lt_iff_lt` and `(add_right_strictMono_of_ne_top _ h).le_iff_le` / `.lt_iff_lt`, under the hypothesis `a ≠ ⊤`.
**why** (stated): Maintainer indicates these equivalence lemmas should follow the ‘more usual order’ (left then right, and le-versions then lt-versions) and be stated as simp lemmas derived directly from the existing `add_left_strictMono_of_ne_top` / `add_right_strictMono_of_ne_top` API (`.le_iff_le` / `.lt_iff_lt`).
**anchors**: AddGroupWithTop.lean:140  (* = inferred)
> [V2] ```suggestion @[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c :=   (add_left_strictMono_of_ne_top _ h).le_iff_le  @[simp] lemma add_le_add_iff_right_of_ne_top {a b c : α} (h : a ≠ ⊤) : a + b ≤ a + c ↔
> [V2] Same here

## pr33345_i01  [V3/docs/partially_adopted]
**ask**: Fix the docstring typo by changing `/-- Multipilication in `R` transfers to Addition in `ArchimedeanClass R`. -/` to `/-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/`.
**why** (stated): The maintainer suggests correcting the spelling in the documentation comment ("Probabily a good idea to fix that simultaneously") and provides the corrected text in a suggestion block.
**anchors**: Archimedean.lean:72  (* = inferred)
> [V3] Probabily a good idea to fix that simultaneousily ```suggestion /-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/ ```

## pr33343_i01  [V3/style/adopted]
**ask**: In the `stdPart_nonneg` proof branch after `rw [stdPart, dif_pos hx.ge]`, replace the `apply map_nonneg; assumption` sequence with an explicit term-style conclusion `exact map_nonneg _ h` (i.e. explicitly provide the inequality argument rather than relying on `assumption`).
**why** (stated): Maintainer requests being explicit in the concluding step “especially when it is not syntactically eq”, preferring an `exact h`/explicit argument over `assumption` after `apply`.
**anchors**: StandardPart.lean:402, StandardPart.lean:402  (* = inferred)
> [V3] ```suggestion     exact h ``` I think it is better to be explicit here, especially when it is not syntactically eq

## pr33337_i01  [V3/naming/adopted]
**ask**: Rename the lemma `orthogonalProjection_coe_eq_linearProjOfIsCompl` to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` (i.e. use the `toLinearMap_...` naming scheme for the coercion to a linear map).
**why** (stated): Maintainer suggests the lemma name should explicitly indicate it is about the `toLinearMap`/linear-map coercion of `orthogonalProjection`, preferring the `toLinearMap_...` prefix over `..._coe_...` naming.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] : ```

## pr33337_i02  [V3/naming/partially_adopted]
**ask**: Rename the lemma about `starProjection.toLinearMap` from `coe_starProjection_eq_isComplProjection` to `toLinearMap_starProjection_eq_isComplProjection` (i.e. use the `toLinearMap_...` prefix rather than `coe_...`).
**why** (stated): Maintainer suggests the theorem name should reflect that the statement is about `K.starProjection.toLinearMap`, so the prefix should be `toLinearMap_...` rather than `coe_...`, aligning with Mathlib naming conventions for coercions/toLinearMap fields.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] : ```

## pr33333_i01  [V4/proof-golf/partially_adopted]
**ask**: Rewrite `floor_pi_eq_three` to use `rw [Int.floor_eq_iff]` followed by `grind [pi_gt_three, pi_lt_four]` instead of the manual `refine Int.floor_eq_iff.mpr ⟨..., ?_⟩; norm_num; exact ...` proof.
**why** (stated): Maintainer proposes a shorter/more idiomatic proof style for `floor_pi_eq_three` using `Int.floor_eq_iff` plus automation (`grind`) with the existing bounds `pi_gt_three` and `pi_lt_four`, as shown in the suggestion block.
**anchors**: Bounds.lean:223, Bounds.lean:223  (* = inferred)
> [V4] Thanks! I'm not sure if I prefer those, though (same with the other). I'll wait for another opinion.
> [V4] I don't have a strong preference. But would this be a middle ground? ```suggestion theorem floor_pi_eq_three : ⌊π⌋ = 3 := by   rw [Int.floor_eq_iff]   grind [pi_gt_three, pi_lt_four] ```

## pr33333_i02  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: If adding bounds for `exp 1`, use the existing results in `Mathlib.Analysis.Complex.ExponentialBounds` instead of introducing new ones (i.e., don’t implement exp(1) bounds in `Analysis/Real/Pi/Bounds.lean`; rely on the dedicated exponential bounds file).
**why** (stated): Maintainer points out that the relevant bounds already exist elsewhere: “Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.” This indicates any attempt to add analogous `exp 1` material here should be redirected to/derived from that existing file rather than duplicating work or placing it in the π bounds file.
**anchors**: Bounds.lean:223*, Bounds.lean:223*  (* = inferred)
> [V2] Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.

## pr33332_i01  [V1/style/unknown]
**ask**: In the `cons` case pattern of the match/induction in `adj_of_mem_walk_support`, remove the unused binder names `u v w` and pattern-match simply as `| cons h p ih =>`.
**why** (stated): The maintainer notes that these names are not used anymore (after the proof was replaced by `grind`), so the pattern should be simplified to avoid unused variables.
**anchors**: Connected.lean:252  (* = inferred)
> [V1] The names aren't used anymore ```suggestion   | cons h p ih => ```

## pr33328_i01  [V4/style/adopted]
**ask**: Replace `fun h _ ↦ h.trans` with `fun h _ => h.trans` (use `=>` instead of `↦` in this lambda) in the proof of `Ici_subset_Ici` (and the analogous simp lemma hunk).
**why** (inferred): The revision changes only the binder arrow in the second lambda, indicating the maintainer wanted consistent lambda syntax (`=>`) rather than mixing in `↦` for this proof style.
**anchors**: Basic.lean:288  (* = inferred)
> [V4] Why this style change here and not in the other analogous places? (I'm neutral to the style changes, maybe they can be left to another PR)

## pr33321_i01  [V3/docs/dropped]
**ask**: Fix/complete the docstring sentence for `IsMulIndecomposable.baseOf` so that the explanatory remark beginning “In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the …” is finished (i.e. replace the dangling incomplete sentence with a proper description).
**why** (stated): The maintainer points out the doc comment currently ends mid-sentence (“In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the”), so it should be completed to clearly state what `baseOf` represents in that context.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] ```suggestion In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ```

## pr33321_i02  [V3/style/unknown]
**ask**: Redefine `IsMulIndecomposable.baseOf` as a `Set ι` via set-builder notation `{j | IsMulIndecomposable v {i | 1 < f (v i)} j}` instead of returning the predicate `IsMulIndecomposable v {i | 1 < f (v i)}` directly (avoid relying on the defeq/coercion between predicates and sets).
**why** (stated): The maintainer flags that the original definition is “abusing the defeq between predicates and sets” by using a `Prop`-valued function where a `Set` is expected; the set-builder form makes the coercion explicit and idiomatic.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] Isn't this abusing the defeq between predicates and sets? ```suggestion def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=   {j | IsMulIndecomposable v {i | 1 < f (v i)} j} ```

## pr33321_i03  [V3/docs/partially_adopted | NOT JUDGEABLE]
**ask**: Clarify in the `## Implementation details` docstring that the proof requires coefficients in an ordered coefficient ring/field (even though the final existence theorem does not), and briefly outline how this is handled.
**why** (stated): The maintainer notes a mismatch between the proof’s needs (an ordered coefficient set) and the statement’s needs, and wants this reflected/justified in the documentation (“The proof needs a set of ordered coefficients, even though the ultimate existence statement does …”).
**anchors**: BaseExists.lean:1  (* = inferred)
> [V3] ```suggestion The proof needs a set of ordered coefficients, even though the ultimate existence statement does ```

## pr33316_i01  [V3/naming/partially_adopted | NOT JUDGEABLE]
**ask**: Decide which of the two duplicate scalar-product-as-sesquilinear-form declarations to keep, preferring the more readable (likely ASCII) name and avoiding introducing/keeping a non-ASCII declaration name if possible; then deprecate/remove the other accordingly.
**why** (stated): Maintainer agrees with removing duplication but objects that the retained/new name seems less readable and notes that non-ASCII characters in declaration names are generally discouraged, so the consolidation should likely target the readable/ASCII-named declaration rather than a non-ASCII one.
**anchors**: RiemannLebesgueLemma.lean:199*, Adjoint.lean:247*, Adjoint.lean:577*, Basic.lean:120*, CanonicalTensor.lean:32*, Symmetric.lean:63*, CharacteristicFunction.lean:66*, CharacteristicFunction.lean:155*, CharacteristicFunction.lean:238*, ComplexMGF.lean:320*  (* = inferred)
> [V3] Getting rid of the duplication is fine, but the other name comes off as more readable to me. I thought using non-ASCII characters in declarations was generally discouraged.

## pr33310_i01  [V2/style/adopted]
**ask**: Refactor the tactic-built `quotientPEquiv` into a definitional construction via auxiliary lemmas: add `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` (keeping `ker` on the LHS), use `Ideal.quotEquivOfEq ker_constantCoeff.symm` to rewrite the quotient, compose with `RingHom.quotientKerEquivOfSurjective` using a separate `constantCoeff_surjective` lemma (to be moved to `Teichmuller`), and add a simp lemma `[simp] quotientPEquiv_mk` stating `quotientPEquiv (Quot.mk _ x) = constantCoeff x` by `rfl`.
**why** (stated): The maintainer wants to avoid creating isomorphism data using tactics because it makes unfolding/definitional equalities brittle; using `Ideal.quotEquivOfEq` yields a definitional computation rule (`quotientPEquiv_mk`) that "would not work otherwise", and they also prefer the equality stated with `RingHom.ker` on the LHS as the more logical form.
**anchors**: Complete.lean:95, Complete.lean:95, Teichmuller.lean:125*  (* = inferred)
> [V2] It would be useful to introduce auxiliary lemmas: ```lean lemma ker_constantCoeff :     RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)} := by   ext   simp [mem_span_p_iff_coeff_zero_eq_zero]  -- this should be moved to the `Teichmuller` file lemma
> [V3] It seems more logical to me to keep `ker` in the LHS, as arguably the RHS is a "more basic term" as compared to the LHS.

## pr33305_i01  [V1/style/adopted]
**ask**: Wrap or reformat the too-long line in `Mathlib/GroupTheory/Submonoid/Inverses.lean` around line 20 so it satisfies Mathlib's maximum line length (likely splitting the file reference `Mathlib/Algebra/Group/Submonoid/Pointwise.lean` across lines or otherwise shortening the line).
**why** (stated): Maintainer notes CI failure: "There's a line that's too long" with a link to the lint output; thus the line needs to be shortened to pass style/lint checks.
**anchors**: Inverses.lean:20*, Inverses.lean:20*  (* = inferred)
> [V1] bors r- bors d+  There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36

## pr33302_i01  [V2/style/adopted]
**ask**: Change `CategoryTheory.ShiftedHom` from a `def` to an `abbrev`, and consequently remove the explicit `AddCommGroup` and `Module` instances currently declared on `ShiftedHom` (letting them be inferred/defeq), updating any downstream proofs as needed (typically `dsimp` will replace manual `erw [Iso.homToEquiv_apply]`).
**why** (stated): The maintainer asks to make `ShiftedHom` an abbrev so definitional reduction (`dsimp`) works better, which “overall, improves automation”, and then the additive/module instances become unnecessary and should be removed; minor proof breakages are expected but should be easy to fix.
**anchors**: ShiftedHom.lean:13*, ShiftedHom.lean:29*, ShiftedHom.lean:181*, ShiftedHom.lean:184*, SmallShiftedHom.lean:209*, SmallShiftedHom.lean:219*, SmallShiftedHom.lean:239*, ExtClass.lean:81*, ShiftedHomOpposite.lean:139*  (* = inferred)
> [V2] Could you also make `ShiftedHom` an abbrev instead of a `def`. Then, the `AddCommGroup` and `Module` instances on this type could be removed. I have tried this, and overall, it improves automation. A few proofs should break, but the fix should be eas

## pr33296_i01  [V2/generalization/dropped]
**ask**: Replace the existing center-of-GL/end proof with the maintainer’s cleaner, more general lemma(s) characterizing central endomorphisms as scalar maps, and strengthen the import in `Mathlib/Algebra/Central/End` to `Mathlib.Algebra.Central.Basic` to support these statements (including corresponding `Submonoid/Subsemigroup/Subsemiring/Subalgebra` center iff lemmas).
**why** (stated): Maintainer provides an alternate proof and indicates it is “cleaner”, includes “a golf and a generalization for the instance”, and explicitly notes: “you need to strengthen the import to `Mathlib.Algebra.Central.Basic` in the `Mathlib/Algebra/Central/End` file.” The provided code block shows the intended generalized lemmas to use/introduce.
**anchors**:   (* = inferred)
> [V2] I was just about to make this PR lol. Here is a cleaner proof. Along with a golf and a generalization for the instance. I can still make this PR, or you can just apply this, whatever :)  Note that you need to strengthen the import to `Mathlib.Algeb

## pr33294_i01  [V3/naming/partially_adopted]
**ask**: Rename the theorem currently named `isFundamentalSequence_of_isNormal` to use dot-style naming: `isFundamentalSequence.of_isNormal` (i.e. make it a method on `IsFundamentalSequence` rather than a standalone `..._of_isNormal` name).
**why** (stated): Maintainer suggests the statement header `theorem isFundamentalSequence.of_isNormal {f : Ordinal → Ordinal} (hf : IsNormal f)`, indicating a preference for dot-notation naming over the underscore `..._of_isNormal` style, consistent with Mathlib naming conventions for lemmas constructing/transporting a structure.
**anchors**: Cofinality.lean:532  (* = inferred)
> [V3] ```suggestion theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f) ```

## pr33294_i02  [V2/style/adopted]
**ask**: Replace the rewrite `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with the shorter method call `rw [h.map_iSup (bddAbove_of_small _)]`.
**why** (stated): The maintainer suggests using the dot-notation lemma `map_iSup` directly from the `h : Order.IsNormal ...` hypothesis, rather than referencing it through the namespace `Order.IsNormal.map_iSup`; this is a style/proof-golf simplification ("rw [h.map_iSup (bddAbove_of_small _)]" no?).
**anchors**: Topology.lean:178  (* = inferred)
> [V2] ```suggestion     rw [h.map_iSup (bddAbove_of_small _)] ``` no? 

## pr33287_i01  [V2/style/dropped]
**ask**: (1) In `Arrows.toCompatible`’s `property` proof, replace the `dsimp; simp only [...]` block with a single `by simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]`. (2) In the lemma where a sheaf condition is proven for an `ofArrows` presieve in an over-category, change the goal statement to use `Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))` (i.e. explicitly insert the `(Over.map p).map` on the family of arrows).
**why** (inferred): (1) The maintainer prefers a simpler, more idiomatic simp proof for compatibility (`simp` with the given rewrite lemmas and hypothesis `h` instead of `dsimp` + `simp only`). (2) They want the `IsSheafFor` statement to be phrased with an explicit `Presieve.ofArrows` built from the mapped arrows in `Over`, likely to make the intended presieve construction clearer and align with surrounding API conventions.
**anchors**: IsSheafFor.lean:799  (* = inferred)
> [V2] ```suggestion   property i j Z gi gj h := by     simp [← FunctorToTypes.map_comp_apply, ← op_comp, h] ```
> [V2] ```suggestion       IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ```

## pr33285_i01  [V2/proof-golf/partially_adopted]
**ask**: Golf the proof of `comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q` to a direct lambda proof, i.e. replace the `rw [SetLike.le_def]; intro ...; change ...; apply ...` block with `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2` (using `mem_comap`/`mem_inf` simp to unpack `h`).
**why** (stated): Maintainer proposes a shorter, cleaner proof term: directly construct the `≤` function and use `mem_comap.mpr` plus `add_mem` on the two components from `h` instead of explicit `SetLike.le_def` rewriting and `change` steps.
**anchors**: Map.lean:595, Map.lean:597  (* = inferred)
> [V2] here's an even better golf ```suggestion     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=   fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2 ```

## pr33285_i02  [V2/proof-golf/adopted]
**ask**: Replace the manual injectivity/ext proof in `cotangentEquivIdeal_symm_apply` (`apply I.cotangentEquivIdeal.injective; rw [apply_symm_apply]; ext; rfl` after rewriting) with a `simp`-based proof, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (or equivalently use `I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)`).
**why** (stated): Maintainer suggests golfing the proof: instead of explicitly applying injectivity and doing `ext`/`rfl`, use `simp` with `symm_apply_eq` and `Subtype.ext_iff` (or a one-line injectivity argument). This simplifies and makes the proof more idiomatic and robust.
**anchors**: Cotangent.lean:151, Cotangent.lean:151  (* = inferred)
> [V2] or ```lean   simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff] ``` or ```lean   exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _) ```

## pr33283_i01  [V3/style/dropped]
**ask**: Rewrite the `linear_combination` call so it is a single line: `linear_combination (norm := (push_cast; ring_nf)) h` (i.e. don’t break after the `norm := ...`), and apply the same formatting to the other similar `linear_combination` occurrences.
**why** (stated): Maintainer finds the line break after `linear_combination (norm := ...)` “a bit weird” and suggests the one-line form `linear_combination (norm := (push_cast; ring_nf)) h`, adding “(and the other ones)” to indicate the same style tweak should be made for similar instances.
**anchors**: Chebyshev.lean:807, Chebyshev.lean:807  (* = inferred)
> [V3] ```suggestion   linear_combination (norm := (push_cast; ring_nf)) h ``` I personally find this line break a bit weird but if you are attached to this style I don't particular want to block this PR because of it.
> [V3] (and the other ones)

## pr33268_i01  [V3/style/unknown]
**ask**: Reorder the file so that the `max_left` and `max_right` lemmas are placed adjacent to each other (immediately one after the other).
**why** (stated): Maintainer notes it is a more natural ordering to have the paired `max_left`/`max_right` lemmas next to each other, improving readability and organization.
**anchors**: Lattice.lean:26  (* = inferred)
> [V3] I think a more natural ordering is to put the max_left and max_right lemmas right after eachother.

## pr33267_i01  [V2/naming/unknown | NOT JUDGEABLE]
**ask**: Use the standard simp lemmas for these equivalences: replace applications of a more general symmetry theorem by `toDual_symm`, and rename/use the lemma as `toDual_bot` rather than the current name.
**why** (stated): Maintainer notes that a theorem currently being applied is overkill and should be replaced by the dedicated lemma `toDual_symm`, and that another lemma should be named `toDual_bot` for consistency with the `toDual` API.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] I feel like this theorem should not be applied; it can just be `toDual_symm`. But that is outside the scope of this PR.
> [V3] And this could just be called `toDual_bot`.

## pr33267_i02  [V3/style/unknown]
**ask**: Remove redundant `WithBot.` namespace qualifiers in references because the `WithBot` namespace is already open (use unqualified names instead of `WithBot.<name>`).
**why** (stated): Maintainer notes: "Since the WithBot namespace is open, you can avoid the `WithBot.`"; i.e. prefer unqualified identifiers when `open WithBot`/being inside an open `WithBot` namespace makes the prefix unnecessary.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] Since the WithBot namespace is open, you can avoid the `WithBot.`

## pr33267_i03  [V3/style/unknown]
**ask**: Adjust formatting/indentation so that when a declaration’s whole statement fits on one line, it is written on a single line (avoid splitting/extra indentation).
**why** (stated): Maintainer notes: “the indentation where the whole statement fits one one line is actually preferred”, i.e. prefer one-line layout for short statements/declarations that fit.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] I think the indentation where the whole statement fits one  one line is actually preferred.

## pr33267_i04  [V2/docs/unknown]
**ask**: In the docstring for `WithBot.toDual`, replace the reference `See `WithBot.toDual_top_equiv` for the related order-iso.` with `See `WithBot.toDualTopEquiv` for the related order-iso.` (and similarly use the `...TopEquiv` naming in these `WithBot` dualization doc references).
**why** (stated): Maintainer notes the related order-iso lemma/definition is named `WithBot.toDualTopEquiv` (not `WithBot.toDual_top_equiv`), so the documentation should point to the correct, current name.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] ```suggestion See `WithBot.toDualTopEquiv` for the related order-iso. -/ ``` Looks like this was renamed at some point: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv

## pr33232_i01  [V3/style/adopted]
**ask**: Rewrite `fourierTransformInv_toTemperedDistributionCLM_eq` so the theorem statement is written as `:= calc` on the same line (i.e. `theorem ... : ... := calc`), rather than putting `:=` on one line and starting `calc` on the next.
**why** (stated): Maintainer called this a style nit and suggested a formatting change: inline the `calc` block after `:=` in the theorem definition; they also note they didn't test elaboration with leading/trailing `_` but expect it to work.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] style nit. I didn't actually test that it still elaborates properly with the starting and ending `_`, but I don't see which it shouldn't. ```suggestion     𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc   _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) :=

## pr33232_i02  [V3/docs/adopted]
**ask**: Add a docstring to `fourierTransformInv_toTemperedDistributionCLM_eq` stating that the distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(E, F)` (Schwartz space).
**why** (stated): The maintainer explicitly suggested inserting a lemma doc comment for `fourierTransformInv_toTemperedDistributionCLM_eq` describing the intended meaning (“distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(…, F)`). This improves documentation/clarity for the new convenience lemma.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] ```suggestion /-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/ theorem fourierTransformInv_toTemperedDistributionCLM_eq (f : 𝓢(E, F)) : ```

## pr33208_i01  [V2/docs/dropped]
**ask**: (1) Adjust the lemma `IsMulIndecomposable_id_univ` to take `{x : M}` as an implicit argument (and keep `hx : x ≠ 1` explicit), and rename it to `isMulIndecomposable_id_univ` (lowercase initial). (2) Expand/improve the docstring on `Submonoid.closure_image_one_lt_and_isMulIndecomposable` to include an explanatory paragraph describing the statement (as in the suggested extended docstring), and add a corresponding docstring for the additive version as well.
**why** (stated): The maintainer found the current statement/docstring hard to parse and requested a “more informative docstring” clarifying the meaning (including the setup with `S`, `f`, and `v`, and the generated submonoid statement), and noted that the additive version lacks its own docstring. Separately, they suggested a signature/style change for `IsMulIndecomposable_id_univ`, making `x` implicit and adjusting naming to the non-capitalized lemma style.
**anchors**: Indecomposable.lean:1  (* = inferred)
> [V2] ```suggestion lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ```
> [V3] I found the statement a bit hard to parse, so I found myself wanting a more informative docstring. Please check that my interpretation is correct, or otherwise improve it.  ```suggestion /-- This is [serre1965](Ch. V, §9, Lemma 2) and may be used to 

## pr33207_i01  [V4/duplication/dropped | NOT JUDGEABLE]
**ask**: Connect the new `argmin` material/definitions to the existing `Minimal`/`MinimalFor` API (and optionally also relate it to `List.argmin`).
**why** (stated): The maintainer questions whether introducing a new definition is preferable to existing `Set.Finite.exists_minimal` + choice, and explicitly says “It would be nice to connect the material here to the `Minimal`/`MinimalFor` API … And potentially also to the `List.argmin` stuff”.
**anchors**: Argmin.lean:1  (* = inferred)
> [V4] Is it definitely easier to use this definition rather than using choice/`obtain` on `Set.Finite.exists_minimal`?   It would be nice to connect the material here to the `Minimal`/`MinimalFor` API (the latter of which isn't quite complete at the mome

## pr33203_i01  [V3/naming/unknown]
**ask**: Rename `Rat.intEquiv` to a less misleading name scoped to the `IsIntegralClosure` context (e.g. `Rat.IsIntegralClosure.intEquiv`), and keep `Rat.intEquiv` only as a deprecated alias.
**why** (stated): Maintainer notes that a name like `Rat.intEquiv` suggests an equivalence `ℚ ≃ ℤ`, not an isomorphism between an integral closure `R` of `ℤ` in `ℚ` and `ℤ`; so the definition should be renamed/scoped to reflect its true domain and assumptions.
**anchors**: HeightOneSpectrum.lean:62, HeightOneSpectrum.lean:70  (* = inferred)
> [V3] I'd just like to mention that this is not at all what I'd expect from something called `Rat.intEquiv`! I was expecting some sort of bijection `ℚ ≃ ℤ` instead.

## pr33201_i01  [V2/scope/adopted]
**ask**: Replace the specialized hand-written proofs about `X.HomotopyCategory` being subsingleton/terminal with instance-based constructions: define `subsingleton_hom` by reducing to `OneTruncation₂ X` and using `CategoryTheory.Quotient.instSubsingletonHom`, add an instance `Unique X.HomotopyCategory` via `CategoryTheory.Quotient.instUnique`, and redefine `isTerminal` using `Cat.isTerminalOfUniqueOfIsDiscrete` (with a local `IsDiscrete` instance from `subsingleton`), instead of the bespoke `MorphismProperty`/`IsTerminal.ofUniqueHom` proof.
**why** (stated): Maintainer says the existing proof is “too specialized for the homotopy category” and that Mathlib already has general facts about quotient categories and discreteness/terminality; so the code should use those existing instances/lemmas (Quotient `instSubsingletonHom`/`instUnique` and `Cat.isTerminalOfUniqueOfIsDiscrete`) rather than building custom `MorphismProperty` arguments and explicit terminal cones.
**anchors**: HomotopyCat.lean:455, HomotopyCat.lean:455  (* = inferred)
> [V2] I feel like this proof is too specialized for the homotopy category. Mathlib arleady knows that quotient categories of categories with unique objects and subsingleton homs have subsingleton homs, and that free categories on quivers with unique object
> [V2] Same here: we already have `Cat.isTerminalOfUniqueOfIsDiscrete`: ```suggestion instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory :=    letI : Unique (OneTruncation₂ X) := inferInstanceAs (Unique (X _⦋0⦌₂))   CategoryTh

## pr33201_i02  [V2/duplication/dropped]
**ask**: Remove the new `Monoidal` instance for `((Functor.whiskeringLeft J J' C).obj F)` in `Monoidal/Cartesian/FunctorCategory.lean` and instead use (or refer to) the existing `CategoryTheory.Functor.Monoidal.whiskeringLeft` construction (possibly via an instance alias), avoiding re-proving the same result.
**why** (stated): The maintainer notes the added instance “seems to be a (less general) duplicate of `CategoryTheory.Functor.Monoidal.whiskeringLeft`”, so they want to avoid duplicating existing infrastructure and rely on the more general lemma/instance already in Mathlib.
**anchors**: FunctorCategory.lean:192  (* = inferred)
> [V2] This seems to be a (less general) duplicate of [CategoryTheory.Functor.Monoidal.whiskeringLeft](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Monoidal/FunctorCategory.html#CategoryTheory.Functor.Monoidal.whiskeringLeft)

## pr33201_i03  [V3/other/adopted]
**ask**: For the newly introduced `FullyFaithful` currying functors (`fullyFaithfulCurry` and `fullyFaithfulCurry₃`), add the corresponding typeclass instances `Full` and `Faithful` (analogous to the existing instances for `uncurry`/`uncurry₃`).
**why** (stated): Maintainer requests that whenever a `FullyFaithful` structure is defined, the downstream `Full` and `Faithful` instances should also be provided so users can use instance search automation (`fullyFaithfulX.full` / `.faithful`). They explicitly say “Please add the corresponding `Full` and `Faithful` instances” and repeat the same comment.
**anchors**: Currying.lean:110, Currying.lean:110, CurryingThree.lean:43, CurryingThree.lean:43  (* = inferred)
> [V3] Please add the corresponding `Full` and `Faithful` instances (we really need a way to automate adding those via an attribute we can put on a `FullyFaithful` definition!).
> [V3] Same  comment: please also add the `Full` and `Faithful` instances

## pr33200_i01  [V1/scope/dropped | NOT JUDGEABLE]
**ask**: Do not merge this PR: remove all new axioms and all `sorry` placeholders (and generally avoid AI-generated, non-mathlib-style large changes) before any resubmission.
**why** (stated): Maintainers state the PR is unsuitable because it is too long to review and, critically, it introduces many axioms and contains sorries; either is individually a hard blocker for Mathlib inclusion. They explicitly note it introduced far more axioms than Mathlib uses overall and ask not to submit PRs of this nature.
**anchors**:   (* = inferred)
> [V1] The issue is nothing to do with the code of conduct. This PR is completely unsuitable for mathlib for multiple reasons. (a) it is far too long to review (b) it has axioms (c) it has sorries (d) it was written by an AI which seems to have no understan
> [V1] > no axioms  I encourage you to learn how to use `grep`, as you have in one file introduced 4 times as many axioms as we use in *all* of Mathlib.  I won't be engaging further and wasting my time.

## pr33198_i01  [V4/naming/dropped]
**ask**: Also standardize the English spelling of ω₁ to `omega_one` by renaming `omega0`→`omega_zero` and `aleph0`→`aleph_zero` (so the 0/1 naming scheme is consistent: `omega_zero`/`aleph_zero` alongside `omega_one`/`aleph_one`).
**why** (stated): Maintainer is confused about mixing styles (`omega0`/`aleph0` but `omega_one`/`aleph_one`) and expects community preference for spelling out zero as well; they suggest a consistent convention (`omega_zero`, `aleph_zero`) if adopting `*_one`.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] I'm confused, you want to write `omega0` and `aleph0` and also `omega_one` and `alepg_one`? I'm virtually certain that if you asked on Zulip, the poll would go in favor of `omega_zero` too and `aleph_zero` too (at least, assuming votes from the same 

## pr33198_i02  [V4/other/unknown | NOT JUDGEABLE]
**ask**: Preserve the lemma’s asymmetry (do not refactor/rename/rewrite it into a symmetric form), because the asymmetric statement is mathematically meaningful.
**why** (stated): Maintainer notes: “the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.” This implies the refactor should not eliminate or obscure that asymmetric formulation.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] Oh I see! Then I think the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.

## pr33198_i03  [V1/other/dropped | NOT JUDGEABLE]
**ask**: Fix the CI/build failure so the PR compiles (resolve whatever errors the `aleph_one` refactor introduced) before merging.
**why** (stated): Maintainer notes “The build is failing” and applies `bors r-` (remove approval) and `bors d+` (delegate/allow), indicating merging is blocked until the build is repaired.
**anchors**: Basic.lean:760*  (* = inferred)
> [V1] The build is failing: https://github.com/leanprover-community/mathlib4/actions/runs/20436145675/job/58717788626#step:22:905 bors r- bors d+

## pr33190_i01  [V3/style/adopted]
**ask**: In `eq_of_natDegree_lt_card_of_eval_eq`, replace `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero (hf := hf)` with `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf`, making `hf` an explicit argument in the `apply` call.
**why** (stated): The maintainer was momentarily confused why `hf` was not passed as an explicit argument; making it explicit improves readability/clarity of the proof application.
**anchors**: Roots.lean:630  (* = inferred)
> [V3] only because I was confused why `hf` wasn't an explicit argument, and then after looking above, I realized it is. ```suggestion   apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf ```

## pr33183_i01  [V3/style/dropped]
**ask**: Refactor the `MonoidalCategoryStruct` (and the later `closed` structure) record definitions to use pointwise field lambdas with the index argument in the binder (e.g. `tensorObj X Y i := X i ⊗ Y i`, `tensorHom f g i := f i ⊗ₘ g i`, `whiskerLeft X _ _ f i := X i ◁ f i`, `whiskerRight f Y i := f i ▷ Y i`, `tensorUnit i := 𝟙_ (C i)`), add/improve the docstring for `Pi.monoidalCategory C` (starting `/-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ...`), and rewrite the `closed X` definition in the same explicit structured form `closed X := { rightAdj := ihom X, adj.unit := closedUnit X, adj.counit := closedCounit X }`.
**why** (inferred): The maintainer suggests a consistent pointwise style for record field definitions (binding the index `i` directly on each field), wants a clearer documentation comment for the main instance `Pi.monoidalCategory C`, and prefers an explicit structured definition for the `closed` data rather than a more implicit/less structured formulation.
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   tensorObj X Y i := X i ⊗ Y i   tensorHom f g i := f i ⊗ₘ g i   whiskerLeft X _ _ f i := X i ◁ f i   whiskerRight f Y i := f i ▷ Y i   tensorUnit i := 𝟙_ (C i) ```
> [V3] ```suggestion /-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ```
> [V3] ```suggestion   closed X := {     rightAdj := ihom X     adj.unit := closedUnit X     adj.counit := closedCounit X } ```

## pr33169_i01  [V2/style/adopted]
**ask**: In the `| succ n hn =>` branch, format the `simpa only` list with proper spacing in the cast `(n : ℤ)` and break the list across lines so `prop_red_T hS hT` is on its own indented continuation line (i.e., keep `| succ n hn =>` and `simpa` on separate lines, not inline).
**why** (stated): The maintainer suggests a specific whitespace/style formatting for the `succ` case: use `(n : ℤ)` (space after `:`) and line-break/indent the long `simpa only [...]` argument list for readability and style consistency.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V4] Please revert this one; I'm not convinced it's better.
> [V2] ```suggestion   | succ n hn =>     simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,       prop_red_T hS hT] ```

## pr33158_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No change requested (maintainer approval only).
**why** (stated): The maintainer expresses mild uncertainty about usefulness but explicitly agrees the change "can't hurt" and approves/merges ("bors r+") without requesting any modification.
**anchors**:   (* = inferred)
> [V4] I'm not so sure that we will ever care about Stieltjes measures on the empty space, but in any case I agree this can't hurt. Thanks! bors r+

## pr33156_i01  [V3/docs/dropped]
**ask**: Add the missing doc-string for the newly introduced `optAttrArg` syntax (or the relevant new declaration) in `Mathlib/Util/AddRelatedDecl.lean`.
**why** (stated): Maintainer explicitly requested: "Please add the missing doc-string, though." This indicates the new syntax/declaration was added without the expected documentation header.
**anchors**:   (* = inferred)
> [V3] (Please add the missing doc-string, though.)

## pr33154_i01  [V3/docs/dropped | NOT JUDGEABLE]
**ask**: Update the comment/documentation at line 24 to also mention `to_fun`.
**why** (stated): Maintainer asks whether an existing note at line 24 should explicitly reference `to_fun`, implying the documentation currently omits it and should be clarified to include it.
**anchors**:   (* = inferred)
> [V3] Pre-existing: should line 24 also mention `to_fun`?

## pr33153_i01  [V2/docs/dropped | NOT JUDGEABLE]
**ask**: Make the change(s) in the diff visible/meaningful (the maintainer reports they “can’t see the difference here”), e.g. by adjusting the edit so it produces an observable textual change or otherwise clarifying what changed.
**why** (stated): The only feedback is “I can't see the difference here.” This indicates the maintainer could not detect any effective change in the PR (likely whitespace-only or otherwise imperceptible), so they are asking for an edit that yields a clearly visible/justified difference.
**anchors**:   (* = inferred)
> [V2] I can't see the difference here. 

## pr33152_i01  [V2/duplication/dropped]
**ask**: Remove the declaration `Meromorphic.meromorphicOn_univ`; instead use the existing lemma `Meromorphic.meromorphicOn`, relying on typeclass inference for `univ` when possible and otherwise supplying the implicit set argument explicitly (and do not add an unprotected `..._univ` lemma).
**why** (stated): Maintainer indicates Mathlib generally does not include specialized `..._univ` declarations for this, and if such a lemma existed it would need to be protected; moreover `Meromorphic.meromorphicOn` already covers the `univ` case and can be used by inference or by providing the argument manually.
**anchors**:   (* = inferred)
> [V2] I don't think we generally include the new declaration `Meromorphic.meromorphicOn_univ`. It would need to be protected if we did, but you should also just be able to use `Meromorphic.meromorphicOn`. When Lean can infer `univ`, it works, and when it c

## pr33151_i01  [V2/naming/adopted]
**ask**: Update `Mathlib/Tactic/Translate/ToDual.lean`’s `GuessName.abbreviationDict` (or equivalently `fixAbbreviations`) to ensure dual-name guessing maps `succColimit` to `SuccLimit` and `predColimit` to `PredLimit` (i.e. un-translate `colimit` back to `limit` when preceded by `succ`/`pred`), instead of relying on other workaround entries like `("cocones", ["Cones"])` / `("fan", ["Cofan"])`.
**why** (stated): Maintainer suspects all relevant `limit` occurrences are in `succ`/`pred` contexts, so it’s easier and more targeted to fix the translation machinery: “use the fixAbbreviations dictionary to un-translate `colimit` to `limit` in these cases” and “In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.”
**anchors**: ToDual.lean:153*, ToDual.lean:181*  (* = inferred)
> [V2] Is it true that all instances of the word `limit` that need to be translated are preceded by either `succ` or `pred`? In that case it may be better to use the fixAbbreviations dictionary to un-translate `colimit` to`limit` in these cases.  (I agree w
> [V2] In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.

## pr33150_i01  [V2/naming/adopted]
**ask**: Fix the `to_dual` tag on `pred_le_iff_le_succ` so it generates the correct dual lemma name: change `@[to_dual]` to `@[to_dual le_succ_iff_pred_le]`.
**why** (stated): The maintainer noted that the current annotation "generates the wrong dual name"; explicitly supplying the intended dual name in the attribute makes the dualization automation produce the correct lemma name.
**anchors**: Basic.lean:828  (* = inferred)
> [V2] I think this generates the wrong dual name

## pr33149_i01  [V1/scope/dropped | NOT JUDGEABLE]
**ask**: Remove any newly introduced axioms from the PR (replace them with theorems proved from existing Mathlib foundations, or restructure the development so no new axioms are required).
**why** (stated): Maintainer: "Mathlib has a no-axioms policy. Please don't introduce any new axioms."
**anchors**:   (* = inferred)
> [V1] Mathlib has a no-axioms policy. Please don't introduce any new axioms.

## pr33149_i02  [V2/duplication/dropped]
**ask**: Replace any locally defined/used “Parseval’s identity” lemma in this PR with the existing Mathlib Parseval lemma; if a specialized variant (e.g. for the standard basis in ℝ^n) is genuinely needed, add that specialization alongside the existing Parseval lemma rather than duplicating it in this development.
**why** (stated): Maintainer notes that Mathlib already provides Parseval’s identity and asks to use it instead of duplicating it; any needed specialization should be contributed where Parseval is defined so it is reusable.
**anchors**:   (* = inferred)
> [V2] Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).

## pr33149_i03  [V3/other/dropped | NOT JUDGEABLE]
**ask**: Update the PR to (1) explicitly disclose in the PR description whether/how AI was used (which parts, prompts, and author understanding), (2) remove any newly introduced axioms (do not add axioms), and (3) for any new definitions introduced, add a basic supporting lemma suite so the additions are maintainable.
**why** (stated): The maintainer flags reviewability/attribution concerns (“did you use AI… Please make this abundantly clear in the PR description”), and identifies two blocking technical issues: “Introducing additional axioms is a no go” and “lots of new definitions without supporting lemmas … not maintainable; please add basic lemmas about them.”
**anchors**:   (* = inferred)
> [V3] Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) 

## pr33149_i04  [V4/other/dropped | NOT JUDGEABLE]
**ask**: Rewrite the PR to meet mathlib standards by (1) eliminating any axioms (replace with derived facts or mark gaps with `sorry`), (2) removing/ inlining definitions that merely rename existing mathlib definitions (at most keep as sparse `abbrev`s), and (3) fixing definitions like `fourierDecay` and `spectralNSResidual` (and dependent `SolvesNavierStokes`) so they are not vacuously true.
**why** (stated): Maintainer says the PR would need to be completely rewritten; specifically asks to avoid axioms (fill in/deduce or use `sorry` as placeholder), to inline short-name wrappers around existing definitions (or use `abbrev` sparingly), and warns that key definitions are vacuous, indicating the formalization is not expressing the intended mathematics and must be corrected before resubmission.
**anchors**:   (* = inferred)
> [V4] Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33146_i01  [V3/docs/adopted]
**ask**: Capitalize the docstring for the `whisker_eq` theorem: change `/-- precompose an equation between morphisms by another morphism -/` to `/-- Precompose an equation between morphisms by another morphism -/`.
**why** (stated): Maintainer notes “Might as well fix some capitalization” and provides the corrected docstring text with `Precompose` capitalized.
**anchors**: Basic.lean:223  (* = inferred)
> [V3] Might as well fix some capitalization. ```suggestion /-- Precompose an equation between morphisms by another morphism -/] ```

## pr33145_i01  [V2/duplication/dropped]
**ask**: Rename the new lemmas `Dense.continuous_upperBounds` and `Dense.continuous_lowerBounds` to `Dense.upperBounds_image` and `Dense.lowerBounds_image`, and refactor the proof of the lower-bounds lemma to be obtained by applying the upper-bounds lemma to `OrderDual` (i.e. prove `lowerBounds (f '' S) = lowerBounds (range f)` via `hS.continuous_upperBounds (α := αᵒᵈ) hf`) instead of duplicating the closure/frequently proof.
**why** (stated): Maintainer suggests the lemma names `Dense.upperBounds_image` and `Dense.lowerBounds_image` and points out a standard trick: the lower-bounds statement should follow from the upper-bounds statement by switching to `OrderDual`, avoiding duplicated proof structure.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] ```suggestion theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] There's a trick you can use for this kind of thing by using the `OrderDual`. ```suggestion     lowerBounds (f '' S) = lowerBounds (range f) :=   hS.continuous_upperBounds (α := αᵒᵈ) hf ```

## pr33145_i02  [V2/duplication/dropped]
**ask**: Replace the bespoke lemmas `Dense.continuous_upperBounds` / `Dense.continuous_lowerBounds` (and downstream `continuous_sup`/`continuous_inf`-style results) by introducing general lemmas `Dense.ciSup` and `Dense.ciInf` (with signature starting `theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ...` and similarly for `ciInf`), and obtain the `ciInf` statement by reusing `ciSup` on the order dual (e.g. prove `⨅ i, f i = ⨅ s : S, f s` via `hS.ciSup (α := αᵒᵈ) hf h`).
**why** (inferred): Maintainer is steering the development toward canonical `ciSup/ciInf` API on `Dense` (rather than ad-hoc `continuous_upperBounds/lowerBounds` lemmas) and wants `ciInf` derived from `ciSup` via order duality to avoid duplicated proofs.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup (α := αᵒᵈ) hf h ```

## pr33145_i03  [V2/duplication/dropped]
**ask**: Add lemmas `Dense.ciSup'` and `Dense.ciInf'` (with binder `{α : Type*} [TopologicalSpace α]`) and use order-duality to prove the infimum version by rewriting it as a `ciSup'` statement on `αᵒᵈ`, i.e. implement `⨅ i, f i = ⨅ s : S, f s` via `hS.ciSup' (α := αᵒᵈ) hf`.
**why** (inferred): The maintainer suggests introducing dualized `ciSup'`/`ciInf'` theorems and explicitly proving the `ciInf'` result by applying the `ciSup'` theorem to the order dual `αᵒᵈ`, avoiding separate/duplicated proof work and aligning with Mathlib conventions for inf/sup duality.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup' (α := αᵒᵈ) hf ```

## pr33145_i04  [V2/style/dropped]
**ask**: Refactor the proof of the `Dense.continuous_ciSup`/`continuous_sup`-style lemma to start with a `by_cases` split on `BddAbove (range (fun x : S ↦ f x))`; in the bounded case, use `hS.ciSup hf (h.closure.mono ...)` with `hf.range_subset_closure_image_dense hS` (rewritten via `range_comp`/`Function.comp_def`), and in the unbounded case, derive `¬ BddAbove (range f)` by contraposition and finish by simp using `ciSup_of_not_bddAbove`.
**why** (stated): The maintainer indicates the proof becomes simpler/cleaner if it first case-splits on whether the subtype-range is bounded above, and then handles the unbounded case by reducing it to the unboundedness of `range f` and letting `simp` discharge the `ciSup` goals via `ciSup_of_not_bddAbove`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] It's easier if you case split on whether the range of the function from the subtype is bounded above or not. ```suggestion   by_cases h : BddAbove (range (fun x : S ↦ f x))   · refine hS.ciSup hf <| h.closure.mono ?_     simpa [← Function.comp_def, r

## pr33145_i05  [V3/style/unknown]
**ask**: Rewrite equalities involving `iSup`/`iInf` so the left-hand side is the `iSup` over `S` and the right-hand side is the `iSup` over the full index/type, i.e. change statements/proof headers to the form `⨆ s : S, f s = ⨆ i, f i := by` (and similarly for `iInf`) instead of the opposite orientation.
**why** (stated): The maintainer explicitly suggests “turning the declarations involving `iSup` and `iInf` around so that they read `⨆ s : S, f s = ⨆ i, f i := by` instead”, i.e. prefer this directional formatting/orientation for the lemma statements.
**anchors**: IsLUB.lean:166*, IsLUB.lean:166*  (* = inferred)
> [V3] I suggest turning the declarations involving `iSup` and `iInf` around so that they read: ```lean     ⨆ s : S, f s = ⨆ i, f i := by ``` instead.

## pr33144_i01  [V2/duplication/dropped]
**ask**: Remove the redundant eta-expanded `fun_` lemmas `fun_deriv` and `fun_iterated_deriv` from `Analysis/Meromorphic/Basic` (and avoid adding such `fun_` variants unless actually needed/used).
**why** (stated): Maintainer decision: since the `fun_` versions are unused and merely restate existing derivative/iterated-derivative lemmas with a trivial `fun _ => ...` wrapper, they add no value; thus they should be removed and only introduced when needed.
**anchors**:   (* = inferred)
> [V4] This PR itself it straightforward; the main question is whether we want it.
> [V2] @kebekus Thanks for the explanation! Let's only add `fun_` versions as needed then --- as these lemmas are unused, let's remove them. bors r+

## pr33141_i01  [V2/style/adopted]
**ask**: Add `(relevant_arg := X)` to the `@[to_additive]` attributes on all declarations in this file (instances/lemmas like `instIsCocomm`, `counit_single`, `comul_single`), not just `instCoalgebra`.
**why** (stated): Maintainer indicates `to_additive` needs `relevant_arg := X` everywhere here so the additive translations treat `X` as the relevant parameter consistently across all generated additive analogues.
**anchors**: MonoidAlgebra.lean:35  (* = inferred)
> [V2] I think you need the `(relevant_arg := X)` on all of the declarations in this file

## pr33137_i01  [V2/style/dropped]
**ask**: In the `mapDomainNonUnitalAlgHom` definition, replace the lambda `map_mul' := fun x y => mapDomain_mul f x y` with the point-free assignment `map_mul' := mapDomain_mul f`.
**why** (stated): The maintainer suggests using the existing lemma `mapDomain_mul f` directly as the field value, instead of wrapping it in an unnecessary `fun x y => ...` lambda, for a cleaner record construction.
**anchors**: Basic.lean:217  (* = inferred)
> [V2] ```suggestion   map_mul' := mapDomain_mul f ```

## pr33127_i01  [V2/docs/adopted]
**ask**: Remove the stray `example` test code preceding the new section, and replace it with a brief section-level comment explaining why the subsequent lemmas use `haveI := _.neZero` (instead of e.g. assuming `[NeZero n]`).
**why** (stated): The maintainer indicates the `example` is just test code and should be removed, and suggests that the point it illustrates (why the `haveI`s are present) should be documented as a comment at the top of the section.
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V2] I assume this is test code, and can be removed? ```suggestion ```
> [V3] This may be worth turning into a comment at the top of the section!

## pr33117_i01  [V2/duplication/dropped]
**ask**: Import `Mathlib.Tactic.ToFun` and replace the `[fun_prop]`-tagged `Meromorphic.*` closure lemmas (and the extra `fun_*` variants) with single lemmas annotated `@[to_fun (attr := fun_prop)]` (e.g. `neg`, `add`, `sum`, `sub`, `mul`, `prod`, `div`, `pow`, `zpow`, `deriv`, `iterated_deriv`), so `to_fun` generates the corresponding `fun x ↦ ...` versions automatically.
**why** (stated): Maintainer points out new metaprogramming support: the `to_fun` attribute can automatically produce the `fun x ↦ ...` versions, avoiding manual duplication of `fun_neg`, `fun_add`, `fun_sum`, `fun_sub`, etc., while still registering the main lemma with `fun_prop` via `(attr := fun_prop)`. This requires adding `import Mathlib.Tactic.ToFun`.
**anchors**: Basic.lean:631  (* = inferred)
> [V2] There is some new metaprogramming that can help here: the `to_fun` attribute. To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).  ```suggestion @[to_fun (attr := fun_prop)] lemma neg (hf : Meromorphic

## pr33111_i01  [V3/naming/partially_adopted | NOT JUDGEABLE]
**ask**: Decide on and implement a consistent naming scheme for the renamed injectivity lemmas: in particular, consider naming the lemma `injective_of_eq_imp_le` (rather than `Function.Injective.of_eq_imp_le`) and, if proceeding with renames, rename the related lemmas consistently (including `injective_of_lt_imp_ne`) and optionally keep/deprecate the old names via `@[deprecated ...]`.
**why** (stated): Maintainer questions the chosen new name (“why not call it `injective_of_eq_imp_le`?”), suggests deprecating old names, and then concludes that if renaming, it should be done consistently across the family (“rename away… keep things consistent and rename the others in a better way!”).
**anchors**: Defs.lean:318*, Defs.lean:320*  (* = inferred)
> [V3] why not call it `injective_of_eq_imp_le`?
> [V3] You could deprecate it. Probably a good idea. ~~But I'd suggest keeping the theorem as is, just add the `@[deprecated Function.Injective.of_... (since := ...)]`.~~
> [V3] Meh, rename away. I only suggested it to keep things consistent. So let's keep things consistent and rename the others in a better way!

## pr33111_i02  [V2/proof-golf/dropped]
**ask**: Refactor the proof of `injective_of_lt_imp_ne` to use the newly introduced lemma `injective_of_eq_imp_le` (placed earlier so it is available), either by replacing the existing argument with the one-liner `exact injective_of_eq_imp_le f (fun {x y} ↦ not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x))` or by discharging it via automation `grind [injective_of_eq_imp_le]`.
**why** (stated): The maintainer suggests shortening/simplifying the proof by deriving injectivity from the new lemma `injective_of_eq_imp_le` instead of reproving it manually; they explicitly propose an `exact ...` proof term or an automated `grind` proof, noting it works if the new lemma is moved earlier.
**anchors**: Defs.lean:320*  (* = inferred)
> [V2] if you move the new lemma before this one, you could do ```suggestion   exact injective_of_eq_imp_le f fun {x y} ↦     not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x) ``` or ```suggestion   grind [injective_of_eq_imp_le] ```

## pr33111_i03  [V4/docs/unknown | NOT JUDGEABLE]
**ask**: Revise the PR title/description to reflect that it is adding a new more general lemma (rather than “weakening the hypothesis” of the existing lemma).
**why** (stated): Maintainer notes: “The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.” So the requested change is to adjust how the change is presented (title/wording) to match what the PR actually does.
**anchors**:   (* = inferred)
> [V4] The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.

## pr33107_i01  [V4/scope/dropped]
**ask**: Refactor `LinearMap.ker` and `LinearMap.range` so they take an actual `LinearMap` argument (not a `LinearMapClass`), thereby making the proposed `ContinuousLinearMap` simp lemmas unnecessary/automatic and enabling dot-notation and better rewriting.
**why** (stated): Maintainers say the PR is “exposing a flaw” in the current library: `LinearMap.range`/`ker` are defined via a linear map *class* rather than a concrete linear map. They suggest changing these definitions so that simp behavior for structures like `ContinuousLinearMap` comes “for free” and dot-notation works, rather than adding ad-hoc simp lemmas.
**anchors**:   (* = inferred)
> [V4] I think we should refactor the definitions of `LinearMap.range` and `LinearMap.ker` to take in an actual linear map and not a linear map class. That way, all of this comes for free. It'll also allow for dot notation, solve more of these issues, etc..
> [V4] @Timeroot yes, Monica is correct here. Unfortunately you are exposing a flaw that exists currently in the library. Help ripping it out is encouraged! For more information see the Zulip thread: [#mathlib4 > Mathlib's morphism hierarchy](https://leanpr

## pr33104_i01  [V3/style/dropped]
**ask**: Define the transported structure as a `protected abbrev pseudoMetricSpace` taking an equivalence `e` (both for `e : α ≃ₜ β` and for `e : α ≃ᵤ β`) with an implicit `[PseudoMetricSpace β]` instance, returning `PseudoMetricSpace α`.
**why** (stated): The maintainer suggests introducing a concise, namespaced constructor for the pulled-back `PseudoMetricSpace` along a `Homeomorph`/`UniformEquiv`, using `protected abbrev` (rather than a longer `def`/instance setup) to standardize naming and reduce boilerplate while keeping it accessible as `Homeomorph.pseudoMetricSpace` / `UniformEquiv.pseudoMetricSpace`.
**anchors**:   (* = inferred)
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ```
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ```

## pr33101_i01  [V3/scope/adopted]
**ask**: Wrap the earlier duplicated `variable` declarations in a `section`/`end` block, inserting an `end` before the new `variable {K V₁ V₂ : Type*} ...` so the second set of variables is scoped separately and doesn’t unexpectedly affect later code.
**why** (stated): Maintainer notes the file now has duplicated `variable`s and asks to enclose the previous ones in a `section`/`end` “to avoid surprises”, i.e. avoid leaking/overlapping variable scopes across parts of the file.
**anchors**: Lemmas.lean:781, Lemmas.lean:780, Lemmas.lean:722*, Lemmas.lean:721*  (* = inferred)
> [V3] It looks like this duplicates the `variable`s.  Could you enclose the previous one in a `section`/`end` block, to avoid "surprises"?

## pr33098_i01  [V2/style/unknown]
**ask**: Replace the manual case-split proofs of subset/finite properties for the extremal constructions with one-line `grind` proofs, and add the needed `[grind .]` attributes (`finite_empty` for `finite_minimalCover`, `IsSeparated.empty` for `isSeparated_maximalSeparatedSet`); specifically rewrite `minimalCover_subset` (and similarly `maximalSeparatedSet_subset` and related lemmas) as `by grind [minimalCover]` / `by grind [maximalSeparatedSet]`, and adjust lemma headers to use the shorter names `encard_minimalCover` / `encard_maximalSeparatedSet`.
**why** (stated): Maintainer indicates several lemmas can be proven uniformly by `grind` if `finite_empty` and `IsSeparated.empty` are added to the grind simp-set, and provides exact replacement proofs for `minimalCover_subset` and `maximalSeparatedSet_subset`. They also suggest renaming lemma statements to `encard_minimalCover` / `encard_maximalSeparatedSet` (and `encard_le_of_isSeparated` header tweak).
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add ```lean attribute [grind .] finite_empty ``` but I think we should do that anyway. ```suggestion lemma minimalCover_subset : min
> [V2] This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add ```lean attribute [grind .] IsSeparated.empty ``` but I think we should do that anyway.  ```suggestion lemma maximalSe
> [V2] ```suggestion lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_le_of_isSeparated (h_subset : C ⊆ A) ```

## pr33098_i02  [V2/proof-golf/unknown]
**ask**: Refactor the proof (in `Topology/MetricSpace/CoveringNumbers.lean` around line ~228) by introducing `C := {x} ∪ maximalSeparatedSet ε A` and using `Metric.isSeparated_insert_of_notMem` (via `isSeparated_insert_of_notMem hx_not_mem |>.mpr ⟨isSeparated_maximalSeparatedSet, ...⟩`) together with `encard_insert_of_notMem` and the contradiction pattern shown, instead of the existing longer/shuffled argument.
**why** (stated): The maintainer provides a “golf” whose “main point is to use `Metric.isSeparated_insert_of_notMem`”, simplifying the separatedness step and streamlining the contradiction by packaging `{x} ∪ maximalSeparatedSet ε A` and rewriting the encard computation via `encard_insert_of_notMem`.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`. ```lean   intro x hxA   by_contra! h_dist   let C :=

## pr33098_i03  [V2/style/dropped]
**ask**: In `coveringNumber_le_packingNumber`, replace the manual `by_cases` split and `iInf`-based proof with a `by_cases!` on `packingNumber ε A ≠ ⊤` that (1) rewrites using `encard_maximalSeparatedSet h_top` (not `card_maximalSeparatedSet`), (2) derives the bound via `IsCover.coveringNumber_le_encard` applied to `isCover_maximalSeparatedSet h_top` and `maximalSeparatedSet_subset`, and (3) simplifies the `⊤` case with `simp [h_top]`.
**why** (stated): Maintainer notes that `by_cases!` should be used to automatically push negations in the second branch, and that there is an existing lemma `IsCover.coveringNumber_le_encard` which should be used instead of the current bespoke `iInf_le`/`simp` argument. The suggestion also switches from `card_` to `encard_` to match `coveringNumber_le_encard` (works in `ℕ∞`).
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley: ```suggestion   by_cases! h_top : packingNumber ε A ≠ ⊤   · rw [← 

## pr33098_i04  [V2/style/dropped]
**ask**: In `coveringNumber_two_mul_le_externalCoveringNumber`, replace `rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty); · simp [h_empty]` by `rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty); · simp`, i.e. pattern-match the empty-set case as `rfl` so simp can close it directly.
**why** (stated): The maintainer suggests destructing `A` as `∅` via `rfl` rather than carrying an explicit `h_empty : A = ∅`, allowing the empty case to be discharged by a bare `simp` and keeping the proof shorter/cleaner.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] ```suggestion   rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)   · simp ```

## pr33098_i05  [V3/style/dropped]
**ask**: Rewrite the `calc` proof in `coveringNumber_subset_le` so that the initial line is combined with the lemma statement, i.e. change `:= by
  calc coveringNumber ε A
  ...` into `:= calc
  coveringNumber ε A
  ...` (placing `coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc` on the first line), to avoid requiring extra indentation under style guidelines.
**why** (stated): Maintainer notes that otherwise Mathlib style guidelines would require indenting all lines below the first `calc` line; the suggested rewrite starts the `calc` block directly after `:=` with the target inequality on the first line.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V3] otherwise style guidelines would require to indent all lines below the first `calc` line. ```suggestion     coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc   coveringNumber ε A ```

## pr33092_i01  [V3/docs/adopted]
**ask**: Explain in the docstring why the private definition `walk_toSimpleGraph'` exists by stating what important downstream result it is used to prove (or otherwise justify its presence if it is not used).
**why** (stated): Maintainer: “I don't understand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.” So the request is to document the purpose/usage of the private def (e.g. that it is used in `reachable_toSimpleGraph`).
**anchors**: Connected.lean:643, Connected.lean:643, Connected.lean:653  (* = inferred)
> [V3] I don't undertand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.

## pr33090_i01  [V3/style/partially_adopted]
**ask**: Change the positivity lemmas from one-way implications taking `hA : A.Nonempty` into `0 < ...` to iff lemmas `0 < ... ↔ A.Nonempty` (so that `simp` can use them more efficiently).
**why** (stated): Maintainer asked: “Could you make this one an iff lemma? `simp` would be more efficient then.” The existing lemma(s) are of the form `..._pos (hA : A.Nonempty) : 0 < ...`; turning them into `..._pos_iff : 0 < ... ↔ A.Nonempty` lets `simp` both prove and discharge nonemptiness/positivity goals.
**anchors**: CoveringNumbers.lean:80, CoveringNumbers.lean:98  (* = inferred)
> [V3] Could you make this one an iff lemma? `simp` would be more efficient then.

## pr33086_i01  [V3/docs/adopted]
**ask**: Add documentation clarifying intended usage: `cofibrantObjects`/`fibrantObjects` (the `ObjectProperty` definitions) are introduced only to form the corresponding full subcategories (`CofibrantObject`/`FibrantObject`), while the Prop typeclasses `IsCofibrant`/`IsFibrant` should be preferred for expressing the object property in practice.
**why** (stated): Maintainer requests an explicit doc entry about the “intented usages” of the two APIs, namely that `IsCofibrant` is meant to be used as a Prop-class and the `ObjectProperty` should not, and that the same clarification is needed for `IsFibrant` vs `fibrantObjects`.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] I think there should be a documentation entry here about the "intented usages" of the two APIs `cofibrantObjects`/`IsCofibrant`. As far as I understand, `IsCofibrant` is to be used as a Prop-Class, while the object property shouldn’t. This needs to b

## pr33086_i02  [V3/style/unknown]
**ask**: Add a `[simp]` lemma `weakEquivalence_homMk_iff` stating that for cofibrant/fibrant `X Y`, `WeakEquivalence (homMk f) ↔ WeakEquivalence f`, proved by `simp only [weakEquivalence_iff]; rfl`.
**why** (stated): The maintainer notes this simp lemma was missing “compared to the others” and provides an explicit suggested lemma to include, so that `WeakEquivalence` on the full-subcategory morphism constructor `homMk` simplifies to `WeakEquivalence` of the underlying morphism.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] Was this one intentionally left out compared to the others?  ```suggestion  @[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}     [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :     We

## pr33081_i01  [V2/style/dropped | NOT JUDGEABLE]
**ask**: Replace the existing anonymous function with `fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl)` to produce the required `iUnion` membership proof.
**why** (inferred): The maintainer provided a specific term-style proof to use, likely to simplify/standardize the construction of a proof of membership in a `Set.iUnion` via `Set.mem_iUnion_of_mem` and `Set.mem_setOf.mpr le_rfl`.
**anchors**:   (* = inferred)
> [V2] ```suggestion     fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl) ```

## pr33079_i01  [V3/naming/adopted]
**ask**: Replace the verbose lemma `neZero_of_exists` proving `NeZero n` from `i : Fin n` with a shorter proof (e.g. using `⟨i.2.ne⟩`/`Nat.ne_zero_of_lt i.isLt`) and rename it to `Fin.neZero` to support dot-notation.
**why** (stated): Maintainer suggests a simpler construction for the `NeZero n` proof (“Does something like ⟨i.2.ne⟩ work as a proof?”) and recommends naming it `Fin.neZero` (“what about calling this `Fin.neZero` for dot notation?”), aligning with Mathlib naming conventions and usability.
**anchors**: Basic.lean:90, Basic.lean:90  (* = inferred)
> [V3] Does something like ⟨i.2.ne⟩ work as a proof? Also, what about calling this `Fin.neZero` for dot notation?

## pr33078_i01  [V2/style/adopted]
**ask**: Replace the explicit construction of `NeZero (n : ℂ)` via `@NeZero.charZero ...` with `have : NeZero n := ⟨hn⟩` (letting typeclass inference derive `NeZero (n : ℂ)`), and restructure the proof to reduce `mahlerMeasure` to a product over `primitiveRoots n ℂ` and show that product is `1` by proving `∀ x ∈ primitiveRoots n ℂ, ‖x‖ ≤ 1` and applying `Multiset.prod_eq_one`.
**why** (stated): Maintainer indicates it suffices to assume `NeZero n` and have the typeclass system obtain `NeZero (n : ℂ)`, avoiding the manual `charZero` construction. The suggested proof also avoids a brittle `simp only` chain by using `suffices` steps: first rewrite `mahlerMeasure` into the product over primitive roots, then show each root has norm `≤ 1` (from `IsPrimitiveRoot.norm'_eq_one ...`), concluding the product is `1` via `Multiset.prod_eq_one`.
**anchors**: MahlerMeasure.lean:113, MahlerMeasure.lean:113  (* = inferred)
> [V2] I think it is enough to provide `NeZero n`, and then the typeclass system will find `have : NeZero (n : ℂ)`.
> [V2] ```suggestion   have : NeZero n := ⟨hn⟩   suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1 by     simpa [mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ,       Polynomial.cyclotomic.roots_eq_primitiveRoots_val]   suffices ∀ a ∈ pri

## pr33070_i01  [V2/style/adopted]
**ask**: In the `Finset.sum` pretty-printer, compute `ppDomain` using `withAppArg <| getPPOption getPPFunBinderTypes` (i.e. wrap the `getPPOption getPPFunBinderTypes` lookup in `withAppArg` so it is associated with the current application argument).
**why** (stated): Maintainer indicates the intended fix for the missing binder annotation/pp.analyze metadata is equivalent to setting `ppDomain` via `withAppArg <| getPPOption getPPFunBinderTypes`, ensuring binder-type pretty-printing options are read in the correct argument/binder context.
**anchors**: Defs.lean:296*  (* = inferred)
> [V2] I think this is the same as ```suggestion   let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes ```

## pr33067_i01  [V2/other/contested | NOT JUDGEABLE]
**ask**: Do not mark the `recall` identifier as a binder/jump-to declaration location: revert the `recall` elaborator’s info reporting to avoid `isBinder := true` (i.e. don’t use `addConstInfo` and also don’t use `addTermInfo' ... (isBinder := true)` there), and apply the corresponding change in `alias_in` as well.
**why** (stated): The maintainer states that `isBinder` should be true only when the syntax actually generates a declaration in the environment (so it is the correct jump-to location). They doubt this holds for `recall`, and additionally request making the same adjustment for `alias_in`.
**anchors**: Recall.lean:44, AliasIn.lean:55*  (* = inferred)
> [V2] `isBinder` should be true only when this piece of syntax generates a declaration in the environment (so this point should be used as the "jump-to" location). That does not hold for `recall`, right?
> [V2] Can you also change `alias_in` please? Thanks!  I am surprised that without this, jump-to-definition still works. I thought the `isBinder` annotation was responsible for that (maybe jump-to-definition uses a non-binder location as fallback?)

## pr33066_i01  [V3/docs/adopted]
**ask**: Fix the docstring typo on `LinearIsometryEquiv.conjStarAlgEquiv`: change “An isometry linear equivalence …” to “An isometric linear equivalence …”.
**why** (stated): The maintainer’s suggestion block shows the preferred wording for the definition’s documentation comment, correcting the adjective/grammar in the first line.
**anchors**: Adjoint.lean:683  (* = inferred)
> [V3] ```suggestion /-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of ```

## pr33066_i02  [V2/duplication/dropped]
**ask**: Delete the custom `ContinuousAlgEquiv.ofAlgEquiv` constructor (and its accompanying simp lemmas like `coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`, `ofAlgEquiv_trans_ofAlgEquiv`) and instead construct continuous algebra equivalences from an `AlgEquiv` using the existing `ContinuousAlgEquiv.mk` constructor (supplying continuity proofs as needed, defaulting to `by fun_prop` when possible).
**why** (stated): The maintainer notes the added `ofAlgEquiv` is "just the pre-existing constructor for `ContinuousAlgEquiv`" (up to definitional equalities), so it duplicates existing API and should be removed in favor of `ContinuousAlgEquiv.mk`.
**anchors**: Equiv.lean:302  (* = inferred)
> [V2] This is just the pre-existing constructor for `ContinuousAlgEquiv`: ``` ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]   [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra

## pr33066_i03  [V2/style/adopted]
**ask**: Add a blank line after `section auxiliaryDefs` and split the section header from the following `variable` declaration so it reads `section auxiliaryDefs` then a new line, then `variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)` (with the remaining hypotheses following on subsequent lines).
**why** (stated): Maintainer suggested reformatting the section start to be cleaner/readable: insert spacing and place `section auxiliaryDefs` on its own, then start the `variable` block below it (shown verbatim in the suggestion).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V2] You can still phrase this as: ```suggestion     Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ``` and I think Lean shouldn't need you to fill in the `_`.
> [V3] This is nice, but it would be even nicer if it were interspersed throughout the code.
> [V3] ```suggestion section auxiliaryDefs  variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0) ```
> [V3] The naming of your `have`s could use some work. Please improve them.

## pr33065_i01  [V3/naming/dropped]
**ask**: Fix the docstring typo “accumulated point” -> “accumulation point”, and rename the new lemmas from dot-notation `ContinuousWithinAt.of_not_accPt` / `ContinuousAt.of_not_accPt` to non-dot names `continuousWithinAt_of_not_accPt` / `continuousAt_of_not_accPt` for consistency with existing lemmas like `continuousWithinAt_of_notMem_closure` (since these lemmas don’t take a `ContinuousWithinAt` hypothesis, dot-notation is usually unusable).
**why** (stated): Maintainer suggests the docstring should say “accumulation point” and argues the lemma should be named `continuousWithinAt_of_not_accPt` to match existing naming conventions (`continuousWithinAt_of_notMem_closure`), noting dot notation isn’t appropriate when there is no `ContinuousWithinAt` hypothesis; “This also applies to the second lemma of course.”
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V3] ```suggestion /-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulation point of ```
> [V3] I think it would make sense to call this `continuousWithinAt_of_not_accPt` instead to stay consistent with e.g. `continuousWithinAt_of_notMem_closure` - since the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used m

## pr33065_i02  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide and standardize the statement of `ContinuousAt.of_not_accPt` by rewriting the hypothesis `¬ AccPt x (𝓟 {x}ᶜ)` into the equivalent form `¬ AccPt x ⊤` (or explicitly choose to keep the current `𝓟 {x}ᶜ` form), i.e. resolve which of these equivalent `AccPt`-filters is the preferred API form.
**why** (stated): The maintainer points out that `AccPt x (𝓟 {x}ᶜ)` is equivalent to `AccPt x ⊤` and explicitly asks for an opinion on which form to prefer; this is an API/statement-shape choice for the new lemma about isolated points.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V4] Note that `AccPt x (𝓟 {x}ᶜ)` is equivalently just `AccPt x ⊤`: ``` import Mathlib  open Topology Filter Set  example {α : Type*} [TopologicalSpace α] {x : α} : AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤ := by   simp [← principal_univ, accPt_principal_iff_nh

## pr33057_i01  [V1/other/unknown | NOT JUDGEABLE]
**ask**: Fix the remaining CI error(s) before merging (the maintainer delegated with “fix the last error”).
**why** (stated): The only actionable maintainer intervention is “Delegating so you can fix the last error”, indicating the PR still had one failing error/CI issue needing author correction prior to merge.
**anchors**:   (* = inferred)
> [V1] Thanks! Delegating so you can fix the last error.   bors d+

## pr33056_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide the naming convention for the `ℵ₁` identifier via community/Zulip vote, with a preference toward avoiding numerals in identifiers (e.g. use a word-based name like `alephOne` rather than `aleph1`).
**why** (stated): Maintainer says this change should be decided by a Zulip vote and notes an expectation to go the other way: generally not using numerals in identifiers (cf. `cos_pi_div_two`), suggesting `alephOne`-style naming instead of `aleph1`.
**anchors**:   (* = inferred)
> [V4] I think there should be a Zulip vote for this. I would have expected that we go the *other* way, potentially with `alephOne` instead of `alepha_one`. The point being that we generally don't use numerals in identifiers (cf. `cos_pi_div_two` for exampl

## pr33048_i01  [V3/scope/adopted]
**ask**: Add a simp lemma `mk_ofNat` (a.k.a. `mk_natCast` specialized to `ofNat`) stating `@[simp] theorem mk_ofNat {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0`, proved via `mod_cast mk_intCast` using `NeZero.ne` for the nonzero premise.
**why** (stated): Maintainer notes a missing simp lemma for `mk` applied to `ofNat(n)` when `[n.AtLeastTwo]`, suggesting it should be derivable from `mk_intCast` by `mod_cast`, and asks to add it to the API so simp can close such goals without manually providing `n ≠ 0`.
**anchors**: Archimedean.lean:181, Archimedean.lean:174  (* = inferred)
> [V3] Just realising: we do not have  ``` @[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 :=   mod_cast mk_intCast (n := n) ``` Mind adding?

## pr33048_i02  [V2/style/dropped]
**ask**: Change the new `FiniteElement.mk_*` simp lemmas so their hypotheses are explicit arguments (not implicit `{hx}`/`{hy}`), and rename the arithmetic lemmas to the more rewrite-friendly `mk_add_mk`/`mk_sub_mk`/`mk_mul_mk` style (i.e. `theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ...` etc.); likewise make `mk_lt_mk_iff` (and by “same below”, also `mk_le_mk_iff`) take `hx hy` explicitly as arguments rather than implicit.
**why** (stated): Maintainer requests `theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) :` and says “Same below”, indicating the same change for the sibling mk-sub/mul lemmas. They also ask to make the hypotheses in `mk_lt_mk_iff` explicit (“for backwards rewriting”), i.e. `theorem mk_lt_mk_iff {x y : K} (hx hy) :`, which also applies to the analogous `mk_le_mk_iff`. Explicit hypotheses and the `_mk` naming make the lemmas easier to use with `rw`/`simp` in both directions and avoid implicit-argument inference issues.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V2] ```suggestion theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ``` Same below
> [V3] I would make those explicit for backwards rewriting: ```suggestion theorem mk_lt_mk_iff {x y : K} (hx hy) : ```

## pr33048_i03  [V3/naming/dropped]
**ask**: Replace the lemma `mk_le_mk_iff` with a lemma named `mk_le_mk` (dropping the `_iff` suffix) stating the same equivalence `FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y` with proof `.rfl`.
**why** (stated): Maintainer questions the need for the `_iff` suffix (“Do we really need the `_iff` here?”) and provides the exact intended replacement lemma name and statement, indicating a naming/style preference to avoid `_iff` when the lemma is already an `↔`.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] Do we really need the `_iff` here? ```suggestion theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :     FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=   .rfl ```

## pr33048_i04  [V3/style/dropped]
**ask**: Replace the `instance : Coe ℚ (FiniteElement K)` with a `RatCast (FiniteElement K)` instance (i.e. implement rational casting via the `RatCast` typeclass instead of `Coe`).
**why** (stated): Maintainer explicitly suggests defining `instance : RatCast (FiniteElement K) where` rather than a bare coercion from `ℚ`, following Mathlib conventions for numeral/rational casts.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] ```suggestion instance : RatCast (FiniteElement K) where ``` no?

## pr33047_i01  [V4/style/adopted | NOT JUDGEABLE]
**ask**: Decide and justify whether the refactor should prefer the longer spelling `smulRight (1 : R →L[R] R)` over the dedicated map `toSpanSingleton R` (i.e. reconsider/defend the choice of preferred name).
**why** (stated): The maintainer questions the motivation for the PR’s direction: “why the longer spelling should be the preferred one?”, so they are asking for an explicit decision/justification (or change of direction) about which form should be preferred in statements/definitions.
**anchors**: Basic.lean:99*, Basic.lean:113*, Basic.lean:133*, Basic.lean:175*, Basic.lean:202*, Basic.lean:259*, Basic.lean:371*, Basic.lean:422*, Basic.lean:877*, Comp.lean:42*, Comp.lean:313*, Comp.lean:322*, Comp.lean:346*, Comp.lean:358*, Comp.lean:389*, CompMul.lean:30*, Inv.lean:31*, Inv.lean:79*, Mul.lean:237*, Mul.lean:248*, Mul.lean:527*, Mul.lean:553*, Extend.lean:162*, Measurable.lean:399*, Measurable.lean:921*, FaaDiBruno.lean:154*, FaaDiBruno.lean:171*, MeanValue.lean:748*, Basic.lean:178*, Conformal.lean:265*, Conformal.lean:304*, RealDeriv.lean:69*, FourierTransformDeriv.lean:119*, FourierTransformDeriv.lean:174*, FourierTransformDeriv.lean:823*, Adjoint.lean:378*, Bilinear.lean:402*, Mul.lean:208*, Deriv.lean:208*, Deriv.lean:221*, Transform.lean:129*, Transform.lean:194*, JacobianOneDim.lean:66*, JacobianOneDim.lean:412*, Determinant.lean:30*, LinearMap.lean:325*, LinearMap.lean:345*, LinearMap.lean:690*, LinearMap.lean:726*, LinearMap.lean:757*, LinearMap.lean:889*  (* = inferred)
> [V4] Might I ask why the longer spelling should be the preferred one?

## pr31342_i01  [V3/docs/unknown]
**ask**: Add a description to the PR message.
**why** (stated): Maintainer explicitly requests: "Could you add a description to the PR message?"—i.e., the PR description/body should be expanded to explain what the change does.
**anchors**:   (* = inferred)
> [V3] Could you add a description to the PR message?
