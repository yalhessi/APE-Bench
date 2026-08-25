# Interventions review digest

113 interventions | judgeable 94 | outcomes {'adopted': 52, 'dropped': 33, 'unknown': 12, 'partially_adopted': 16}

## pr33421_i01  [V3/naming/adopted]
**ask**: Rename the lemma `round_eq'` to `round_eq_div`.
**why** (inferred): Maintainer explicitly suggested the name `round_eq_div` (“How about `round_eq_div`?”), indicating preference for a more descriptive/conventional lemma name for the division formula.
**anchors**: Round.lean:45  (* = inferred)
> [V3] How about `round_eq_div`?

## pr33421_i02  [V2/duplication/dropped]
**ask**: Replace the ad-hoc in-proof constructions showing `Tendsto (2 * ·)` from `𝓝[≥] x` (resp. `𝓝[<] x`) to `𝓝[≥] (2*x)` (resp. `𝓝[<] (2*x)`) with a general lemma (and similarly for the analogous next theorem), i.e. factor these repeated `two_mul`/`tendsto_id.add tendsto_id`/`tendsto_principal_principal` arguments into a reusable statement.
**why** (inferred): Maintainer notes that the argument pattern used here (“Is this not something very general that should exist as a lemma? Same in the next theorem”) is general and duplicated across adjacent theorems, so it should be extracted into a lemma rather than re-proved locally in each theorem.
**anchors**: Floor.lean:195  (* = inferred)
> [V2] Is this not something very general that should exist as a lemma? Same in the next theorem

## pr33421_i03  [V2/generalization/adopted]
**ask**: Replace the specialized lemma `two_mul_fract_eq_one_iff_exists_int` with a generalized lemma `mul_fract_eq_one_iff_exists_int` that works for any factor `k : R` assuming `1 < k`, using a derived positivity hypothesis `hk0 : 0 < k` in the `mul_le_mul_iff_right₀`/`mul_lt_mul_iff_right₀` steps, and adjust the final simp to `simp [mul_add, hk]`.
**why** (inferred): The maintainer’s suggestion generalizes the fixed constant `2` to an arbitrary multiplier `k` with a simple order hypothesis, avoiding an overly specific API lemma and making the result reusable; it also updates the proof to use the appropriate positivity lemma for `k` rather than `two_pos`.
**anchors**: Ring.lean:267, Ring.lean:267  (* = inferred)
> [V2] Better I think as ```suggestion theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :     k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by   rw [fract, mul_sub, sub_eq_iff_eq_add']   refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩   rintro ⟨

## pr33419_i01  [V3/naming/adopted]
**ask**: Rename the lemma `eq_card_diff_of_sdiff` to `card_sub_card_eq` (keeping the statement `#t - #s = #(t \ s) - #(s \ t)`).
**why** (stated): The maintainer says they "couldn't parse the name" and proposes the clearer/standard name `card_sub_card_eq` for the lemma about subtraction of finset cardinals.
**anchors**: Card.lean:574  (* = inferred)
> [V3] I couldn't parse the name you proposed. ```suggestion lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ```

## pr33413_i01  [V2/duplication/dropped]
**ask**: Optionally replace the separate `@[to_dual]`/`attribute [deprecated ...]` pairs used to create dual deprecated aliases with a single use of the `to_dual` attribute that generates both deprecated aliases at once (if compatible with automated deprecated-declaration removal).
**why** (stated): Maintainer notes: "You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want"—i.e. reduce manual duplication in generating dual aliases; they’re uncertain whether tooling to auto-remove deprecated decls works with that approach.
**anchors**:   (* = inferred)
> [V2] Thanks :tada:  maintainer merge  (You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want, but I don't know if the automated removal of deprecated declarations works with that)

## pr33401_i01  [V2/proof-golf/adopted]
**ask**: In `closure_pow_le`, replace the explicit proof blocks for the `0` and `n+1` cases (the manual `intro`/`simp`/`suffices` argument for `0` and the `calc` chain for `n+1`) with the shorter tactic proofs: `| 0 => by simp_all` and `| n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem]`.
**why** (inferred): The maintainer suggests using simpler, more idiomatic tactic scripts instead of a longer hand-written `calc` proof and manual reasoning in the base case, improving concision and readability.
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | 0 => by simp_all ```
> [V2] ```suggestion   | n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem] ``` instead of the `calc ...`

## pr33400_i01  [V3/naming/dropped]
**ask**: Rename the newly introduced theorem `contDiffAt` to `contDiffAt`? specifically, rename the existing/added smoothness lemma currently named `smooth` to be named `contDiff` instead.
**why** (inferred): The maintainer comment says the lemma should be renamed to `contDiff`, aligning the name with the `ContDiff` predicate it proves (and matching common Mathlib naming conventions where lemmas are named after the property, e.g. `contDiff` rather than `smooth`).
**anchors**:   (* = inferred)
> [V3] pre-existing: I think we should also rename this to `contDiff`

## pr33395_i01  [V4/naming/adopted]
**ask**: Rename the theorem `IntrinsicStar.starLinearEquiv_eq` to `IntrinsicStar.starLinearEquiv_eq_arrowCongr`.
**why** (stated): The maintainer prefers a more descriptive name; they note that without explicitly mentioning `arrowCongr` in the name, it would be hard to guess the right-hand side of the equality.
**anchors**: LinearMap.lean:126  (* = inferred)
> [V4] I like this the best. It's verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this. ```suggestion theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ```

## pr33376_i01  [V2/scope/unknown]
**ask**: Decide whether the newly added lemma `rayleighQuotient_add` should be included in this PR; if it is not used for the simp/cleanup goals, remove it (or otherwise justify/ensure it is actually used here).
**why** (inferred): The maintainer questions the inclusion of `rayleighQuotient_add` as it appears unused for the stated purpose of the PR: “This is a reasonable lemma, but you're not using it for this PR, right?” This indicates concern about introducing extra, potentially out-of-scope API in a housekeeping/simp-fix PR.
**anchors**:   (* = inferred)
> [V2] This is a reasonable lemma, but you're not using it for this PR, right?

## pr33373_i01  [V2/duplication/unknown]
**ask**: Replace the inductive proof of `iteratedDeriv_comp_sub_const` with a `simp` proof that rewrites subtraction as addition of a negated constant and then applies the existing lemma `iteratedDeriv_comp_add_const` (i.e. `by simp [sub_eq_add_neg, iteratedDeriv_comp_add_const]`).
**why** (inferred): The maintainer asks to reuse existing theorems rather than reprove the result: `x - s` should be handled by rewriting to `x + (-s)` and then using the already-proved shift lemma for addition, simplifying the proof and avoiding duplication.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simp [sub_eq_add_neg, iteratedDeriv_comp_add_const] ```
> [V2] Let's reuse the existing theorems:

## pr33373_i02  [V2/duplication/unknown]
**ask**: Refactor the new shift/subtraction lemmas to reuse existing theorems (not new inductions): prove `iteratedDeriv_comp_sub_const` by rewriting `z - s` as `z + (-s)` and applying `iteratedDeriv_comp_add_const`, and prove `iteratedDeriv_comp_const_sub` by `simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const]` from `iteratedDeriv_comp_neg n (fun z => f (z + s))`.
**why** (stated): The maintainer explicitly asks to "reuse the existing theorems" and provides a concrete proof sketch showing `iteratedDeriv_comp_const_sub` should be derived from `iteratedDeriv_comp_neg` plus simp rewrites, rather than a fresh inductive proof (and similarly `iteratedDeriv_comp_sub_const` can be obtained from the existing add-const lemma via `sub_eq_add_neg`).
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using     iteratedDeriv_comp_neg n (fun z => f (z + s)) ```
> [V2] Let's reuse the existing theorems:

## pr33362_i01  [V3/scope/adopted]
**ask**: Move the `schwarz_aux` lemma (and associated namespace placement) a few lines down so it is defined inside the `namespace Complex` rather than before entering it.
**why** (stated): Maintainer asks: “Why not move these a few lines below so that it's on the `Complex` namespace?”—i.e., place the lemma under `namespace Complex` instead of defining it outside / with a qualified name.
**anchors**: Schwarz.lean:40, Schwarz.lean:40  (* = inferred)
> [V3] Why not move these a few lines below so that it's on the `Complex` namespace?

## pr33357_i01  [V3/docs/unknown | META]
**ask**: Fix the typo in the PR description.
**why** (stated): The maintainer comment explicitly says “there's a typo in your PR desc”, indicating the requested change is to correct the PR description text (metadata), not the Lean code.
**anchors**:   (* = inferred)
> [V3] (there's a typo in your PR desc)

## pr33356_i01  [V2/style/adopted]
**ask**: Refactor the proof of `hasDetPlusMinusOne_iff_abs_det` to start with `refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩`, i.e. use the `abs_det` method for the forward direction and package the reverse direction via `⟨?_⟩`.
**why** (inferred): The maintainer suggests a cleaner proof structure: derive the forward implication directly from `h.abs_det`, and set up the reverse implication as constructing a `HasDetPlusMinusOne` instance with a remaining goal.
**anchors**: ArithmeticSubgroups.lean:43  (* = inferred)
> [V2] ```suggestion   refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩ ```

## pr33349_i01  [V4/other/unknown | NOT JUDGEABLE | META]
**ask**: Clarify/resolve the lack of consensus on the PR’s approach (i.e., do not proceed without agreement on the changes being introduced).
**why** (stated): Maintainer comment: "I don't think there is consensus here?" indicates the PR should not move forward until the disagreement/uncertainty among maintainers about the proposed changes is addressed.
**anchors**: AddGroupWithTop.lean:41  (* = inferred)
> [V4] I don't think there is consensus here?

## pr33349_i02  [V2/style/adopted]
**ask**: Add simp cancellation lemmas in the usual argument order: introduce `[simp]` lemmas `add_le_add_iff_left_of_ne_top` and `add_lt_add_iff_left_of_ne_top` stated as `b + a ≤ c + a ↔ b ≤ c` / `b + a < c + a ↔ b < c` and `add_le_add_iff_right_of_ne_top` and `add_lt_add_iff_right_of_ne_top` stated as `a + b ≤ a + c ↔ b ≤ c` / `a + b < a + c ↔ b < c`, proved via `(add_left_strictMono_of_ne_top _ h).le_iff_le`/`.lt_iff_lt` and the analogous right version.
**why** (stated): The maintainer indicates these lemmas should be in the “more usual order”, i.e. with the fixed addend written on the appropriate side (`b + a` vs `a + b`) and the varying terms aligned, and marked `[simp]` for rewriting/cancellation; they also say “Same here” to apply the same ordering convention to the analogous `lt` lemmas.
**anchors**: AddGroupWithTop.lean:140  (* = inferred)
> [V2] ```suggestion @[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c :=   (add_left_strictMono_of_ne_top _ h).le_iff_le  @[simp] lemma add_le_add_iff_right_of_ne_top {a b c : α} (h : a ≠ ⊤) : a + b ≤ a + c ↔
> [V2] Same here

## pr33345_i01  [V3/docs/adopted]
**ask**: Fix the docstring typo by changing `Multipilication` to `Multiplication` in the comment `/-- Multipilication in `R` transfers to Addition in `ArchimedeanClass R`. -/` above the `Add (ArchimedeanClass R)` instance.
**why** (inferred): The maintainer suggests correcting the spelling in the documentation string ("Probabily a good idea to fix that simultaneousily" with a suggestion showing the corrected text).
**anchors**: Archimedean.lean:72  (* = inferred)
> [V3] Probabily a good idea to fix that simultaneousily ```suggestion /-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/ ```

## pr33343_i01  [V3/style/adopted]
**ask**: In the proof of `stdPart_nonneg`, replace the `apply map_nonneg; assumption` sequence with an explicit term proof `exact map_nonneg _ h` (i.e., pass `h` directly rather than relying on `assumption`).
**why** (stated): The maintainer prefers being explicit in the proof term when the goal is not syntactically identical to the available hypothesis, instead of letting `assumption` close it implicitly.
**anchors**: StandardPart.lean:402, StandardPart.lean:402  (* = inferred)
> [V3] ```suggestion     exact h ``` I think it is better to be explicit here, especially when it is not syntactically eq

## pr33337_i01  [V3/naming/adopted]
**ask**: Rename the lemma `coe_orthogonalProjection_eq_linearProjOfIsCompl` (previously `orthogonalProjection_coe_eq_linearProjOfIsCompl`) to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`.
**why** (inferred): The lemma identifies the `E →ₗ[𝕜] K` linear map underlying `K.orthogonalProjection`, so its name should indicate it is about the `toLinearMap`/coercion of `orthogonalProjection`, following the library’s naming convention for such coercion lemmas.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] : ```

## pr33337_i02  [V3/naming/adopted]
**ask**: Rename the lemma `coe_starProjection_eq_isComplProjection` to `toLinearMap_starProjection_eq_isComplProjection` (i.e. use the `toLinearMap_` prefix rather than `coe_` for the statement about `K.starProjection.toLinearMap`).
**why** (inferred): The maintainer suggests the lemma name should reflect that it is an equality about `starProjection.toLinearMap`, so the prefix should be `toLinearMap_...` instead of `coe_...` (aligning with naming conventions for coercions vs explicit `toLinearMap`).
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] : ```

## pr33333_i01  [V4/proof-golf/partially_adopted]
**ask**: Refactor `floor_pi_eq_three` to use `rw [Int.floor_eq_iff]` followed by a `grind` proof from `pi_gt_three` and `pi_lt_four`, instead of the manual `refine ...; norm_num; exact ...` style.
**why** (inferred): Maintainer suggests a shorter/simpler proof: rewrite with `Int.floor_eq_iff` and discharge the inequalities using automation (`grind`) with the existing lemmas `pi_gt_three` and `pi_lt_four`, rather than explicit `refine`/`norm_num`/`exact` steps.
**anchors**: Bounds.lean:223, Bounds.lean:223  (* = inferred)
> [V4] Thanks! I'm not sure if I prefer those, though (same with the other). I'll wait for another opinion.
> [V4] I don't have a strong preference. But would this be a middle ground? ```suggestion theorem floor_pi_eq_three : ⌊π⌋ = 3 := by   rw [Int.floor_eq_iff]   grind [pi_gt_three, pi_lt_four] ```

## pr33333_i02  [V2/scope/dropped | NOT JUDGEABLE]
**ask**: Move/point any prospective `exp 1` bounds work out of `Analysis/Real/Pi/Bounds.lean` and instead use/place it in `Mathlib.Analysis.Complex.ExponentialBounds` (since that file already contains bounds for `exp 1`).
**why** (stated): Maintainer notes that bounds for `exp 1` already exist in `Mathlib.Analysis.Complex.ExponentialBounds`, implying new bounds or discussion about adding them here would be misplaced/duplicative.
**anchors**: Bounds.lean:223*  (* = inferred)
> [V2] Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.

## pr33332_i01  [V1/style/dropped]
**ask**: In the `cons` branch pattern `| @cons u v w h p ih =>`, drop the explicit binder names `u v w` (since they are no longer used) so the branch header becomes `| cons h p ih =>`.
**why** (stated): The maintainer notes that the names `u v w` introduced by `@cons u v w ...` are not used anymore, so they should be removed to avoid unused identifiers and simplify the pattern.
**anchors**: Connected.lean:252  (* = inferred)
> [V1] The names aren't used anymore ```suggestion   | cons h p ih => ```

## pr33328_i01  [V4/scope/dropped | NOT JUDGEABLE]
**ask**: No concrete code change requested: maintainer questions the scope/motivation of applying this style refactor here rather than in other analogous files/lemmas, suggesting it might be better deferred to another PR.
**why** (stated): Maintainer asks: “Why this style change here and not in the other analogous places? … maybe they can be left to another PR”, i.e. the intervention is about consistency/scope of the style change across the library rather than a specific edit to the shown lemma.
**anchors**: Basic.lean:288, Basic.lean:316*  (* = inferred)
> [V4] Why this style change here and not in the other analogous places? (I'm neutral to the style changes, maybe they can be left to another PR)

## pr33321_i01  [V3/docs/adopted]
**ask**: Fix the docstring for `IsMulIndecomposable.baseOf` by correcting the typo “crystallogrphic” to “crystallographic” in the explanatory sentence about root systems.
**why** (inferred): The reviewer quoted the sentence beginning “In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, …”, indicating an edit is needed in that documentation line (it contains a spelling mistake in the reviewed code).
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] ```suggestion In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ```

## pr33321_i02  [V3/style/unknown]
**ask**: Redefine `IsMulIndecomposable.baseOf` as an explicit set-comprehension `{j | IsMulIndecomposable v {i | 1 < f (v i)} j}` instead of using `IsMulIndecomposable v {i | 1 < f (v i)}` directly, avoiding reliance on definitional equality between predicates and sets.
**why** (stated): Maintainer notes that the original definition appears to abuse the defeq between a predicate-valued function and a `Set`, and proposes writing the set explicitly to make the intended type/coercion clear.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] Isn't this abusing the defeq between predicates and sets? ```suggestion def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=   {j | IsMulIndecomposable v {i | 1 < f (v i)} j} ```

## pr33321_i03  [V3/docs/partially_adopted]
**ask**: Add/expand the module documentation in `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean` to explicitly explain that the proof requires an ordered coefficient ring (even though the final existence theorem does not), and outline the chosen approach for handling this (e.g. add an “Implementation details” note describing the need for ordered coefficients and possible strategies).
**why** (stated): The maintainer points out a mismatch between the hypotheses needed for intermediate arguments (ordered coefficients) and the statement of the end result, and wants this design constraint documented/justified in the file header.
**anchors**: BaseExists.lean:1  (* = inferred)
> [V3] ```suggestion The proof needs a set of ordered coefficients, even though the ultimate existence statement does ```

## pr33316_i01  [V3/naming/dropped]
**ask**: Avoid introducing a non-ASCII identifier for the inner product sesquilinear map (i.e. do not name it `innerₛₗ`); instead use an ASCII name (preferably keeping the more readable existing name) for the surviving declaration when removing the duplication.
**why** (stated): The maintainer is fine with removing the duplicate, but objects to the new declaration name being less readable and using non-ASCII characters, noting that non-ASCII in declaration names is generally discouraged.
**anchors**:   (* = inferred)
> [V3] Getting rid of the duplication is fine, but the other name comes off as more readable to me. I thought using non-ASCII characters in declarations was generally discouraged.

## pr33310_i01  [V2/style/adopted]
**ask**: Refactor `quotientPEquiv` to avoid constructing the ring isomorphism via tactics/rewriting: introduce a lemma `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` (with `ker` on the LHS), prove surjectivity separately (`constantCoeff_surjective`, to be moved to `Teichmuller.lean`), then define `quotientPEquiv` as `(Ideal.quotEquivOfEq ker_constantCoeff.symm).trans (RingHom.quotientKerEquivOfSurjective constantCoeff_surjective)` and add a simp lemma `quotientPEquiv_mk` stating it sends `Quot.mk _ x` to `constantCoeff x`.
**why** (stated): The maintainer notes that creating data (the isomorphism) using tactics/rewrites is problematic for unfolding definitions; using `Ideal.quotEquivOfEq` yields a definitional computation rule so `quotientPEquiv_mk` can be `rfl`. They also prefer keeping `RingHom.ker` on the LHS as the more structured/basic term.
**anchors**: Complete.lean:95, Complete.lean:95  (* = inferred)
> [V2] It would be useful to introduce auxiliary lemmas: ```lean lemma ker_constantCoeff :     RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)} := by   ext   simp [mem_span_p_iff_coeff_zero_eq_zero]  -- this should be moved to the `Teichmuller` file lemma
> [V3] It seems more logical to me to keep `ker` in the LHS, as arguably the RHS is a "more basic term" as compared to the LHS.

## pr33305_i01  [V1/style/adopted]
**ask**: Wrap/shorten the overlong doc line (at the updated file reference in `Mathlib/GroupTheory/Submonoid/Inverses.lean` around line 20) so it respects the max line-length lint.
**why** (stated): Maintainer notes the CI failure: “There's a line that's too long” with a link to the lint output; thus the change requested is to reflow the offending documentation line to pass the line-length check.
**anchors**: Inverses.lean:20*, Inverses.lean:20*  (* = inferred)
> [V1] bors r- bors d+  There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36

## pr33302_i01  [V2/style/adopted]
**ask**: Change `ShiftedHom` from a `def` to an `abbrev`, and consequently remove the `AddCommGroup` and `Module` instances currently defined on `ShiftedHom` (updating any downstream proofs to rely on definitional unfolding/`dsimp` rather than explicit `erw` steps).
**why** (stated): The maintainer says making `ShiftedHom` an `abbrev` "improves automation" and would allow dropping redundant algebraic instances; with an abbrev, definitional reduction via `dsimp` should make some previously manual rewrites (e.g. `erw [Iso.homToEquiv_apply]`) unnecessary.
**anchors**:   (* = inferred)
> [V2] Could you also make `ShiftedHom` an abbrev instead of a `def`. Then, the `AddCommGroup` and `Module` instances on this type could be removed. I have tried this, and overall, it improves automation. A few proofs should break, but the fix should be eas

## pr33296_i01  [V2/scope/dropped]
**ask**: Strengthen `Mathlib/Algebra/Central/End.lean` to import `Mathlib.Algebra.Central.Basic` (instead of only `Mathlib.LinearAlgebra.FreeModule.Basic`) so the needed centrality lemmas are available for the proposed center-of-`End` statements.
**why** (stated): Maintainer explicitly notes: “you need to strengthen the import to `Mathlib.Algebra.Central.Basic` in the `Mathlib/Algebra/Central/End` file.” This is required to support the center/sub(center) characterizations being added/used.
**anchors**:   (* = inferred)
> [V2] I was just about to make this PR lol. Here is a cleaner proof. Along with a golf and a generalization for the instance. I can still make this PR, or you can just apply this, whatever :)  Note that you need to strengthen the import to `Mathlib.Algeb

## pr33294_i01  [V3/naming/adopted]
**ask**: Rename the theorem currently introduced as `isFundamentalSequence_of_isNormal` to use dot-notation as `isFundamentalSequence.of_isNormal` (i.e. make it a lemma in the `isFundamentalSequence`/`IsFundamentalSequence` namespace rather than a standalone `_of_` name).
**why** (inferred): Maintainer suggests the preferred naming scheme: `theorem isFundamentalSequence.of_isNormal ...` instead of an `_of_`-style top-level name, aligning with Mathlib convention of using `.of_...` lemmas for constructing a structure/predicate from hypotheses.
**anchors**: Cofinality.lean:532  (* = inferred)
> [V3] ```suggestion theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f) ```

## pr33294_i02  [V2/style/adopted]
**ask**: Replace the rewrite `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with the shorter lemma call on the instance, `rw [h.map_iSup (bddAbove_of_small _)]`.
**why** (inferred): Use dot-notation (`h.map_iSup`) instead of referencing the lemma through the namespace (`Order.IsNormal.map_iSup h ...`) for a cleaner proof step.
**anchors**: Topology.lean:178  (* = inferred)
> [V2] ```suggestion     rw [h.map_iSup (bddAbove_of_small _)] ``` no? 

## pr33287_i01  [V2/style/partially_adopted]
**ask**: (1) In the `Arrows.toCompatible` definition, simplify the proof of `property` by replacing the `dsimp; simp only [...]` sequence with `by simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]`. (2) In the lemma/proof about sheaves on over-categories, state the target sieve explicitly as `Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))` (i.e. use `Presieve.ofArrows` with `Over.map p` applied to the arrows `f i`) when proving `IsSheafFor` for that presieve.
**why** (inferred): The maintainer is asking for more idiomatic proof simplification: `simp` with an explicit rewrite set instead of `dsimp` plus `simp only`. They also want the `IsSheafFor` goal written using the explicit `Presieve.ofArrows` expression over `Over X`, making the construction/intent clear and avoiding implicit/unification-heavy terms.
**anchors**: IsSheafFor.lean:799  (* = inferred)
> [V2] ```suggestion   property i j Z gi gj h := by     simp [← FunctorToTypes.map_comp_apply, ← op_comp, h] ```
> [V2] ```suggestion       IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ```

## pr33285_i01  [V2/proof-golf/partially_adopted]
**ask**: Replace the existing `by`-proof of `comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q` (using `rw [SetLike.le_def]`, `intro`, `change`, and `q.add_mem`) with a shorter term-style proof: `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2`.
**why** (stated): The maintainer proposes an "even better golf" version, i.e. a more concise proof term instead of the longer tactic/simp-based proof.
**anchors**: Map.lean:595, Map.lean:597  (* = inferred)
> [V2] here's an even better golf ```suggestion     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=   fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2 ```

## pr33285_i02  [V2/proof-golf/adopted]
**ask**: Replace the manual injectivity/ext proof of `cotangentEquivIdeal_symm_apply` with a `simp`-based proof, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (instead of `apply ...injective; rw ...; ext; ...`).
**why** (inferred): Maintainer suggests proof-golf/automation: either solve by `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` or use the shorter injective/apply-symm-apply `exact ...` pattern, avoiding the longer `apply ...; rw ...; ext; rfl` script.
**anchors**: Cotangent.lean:151, Cotangent.lean:151  (* = inferred)
> [V2] or ```lean   simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff] ``` or ```lean   exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _) ```

## pr33283_i01  [V3/style/dropped]
**ask**: Rewrite the `linear_combination` invocation so it is on a single line with its argument, i.e. `linear_combination (norm := (push_cast; ring_nf)) h` instead of splitting the tactic call and argument across lines.
**why** (inferred): The maintainer suggests a one-line formatting for `linear_combination` (and similar occurrences: “and the other ones”), indicating the current line break style is weird/unpreferred.
**anchors**: Chebyshev.lean:807, Chebyshev.lean:807  (* = inferred)
> [V3] ```suggestion   linear_combination (norm := (push_cast; ring_nf)) h ``` I personally find this line break a bit weird but if you are attached to this style I don't particular want to block this PR because of it.
> [V3] (and the other ones)

## pr33268_i01  [V3/style/dropped]
**ask**: Reorder the file so that the `max_left` and `max_right` lemmas are placed adjacent to each other (immediately one after the other).
**why** (stated): The maintainer says it is a “more natural ordering” to put the `max_left` and `max_right` lemmas right after each other, i.e. keep the paired left/right simp-style lemmas grouped together for readability.
**anchors**: Lattice.lean:26  (* = inferred)
> [V3] I think a more natural ordering is to put the max_left and max_right lemmas right after eachother.

## pr33267_i01  [V2/naming/dropped | NOT JUDGEABLE]
**ask**: Replace uses/mentions of the more specific dualization lemmas with the standard names: use `toDual_symm` instead of applying a separate theorem for the symmetry of `toDual`, and rename the corresponding lemma to `toDual_bot` (rather than an ad-hoc `..._bot` name).
**why** (inferred): The maintainer indicates the current theorem application is unnecessary because the standard lemma `toDual_symm` suffices, and that the lemma about `⊥` should follow the conventional name `toDual_bot`, aligning with the `toDual`/`ofDual` machinery refactor.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] I feel like this theorem should not be applied; it can just be `toDual_symm`. But that is outside the scope of this PR.
> [V3] And this could just be called `toDual_bot`.

## pr33267_i02  [V3/style/dropped]
**ask**: When the `WithBot` namespace is open, drop explicit `WithBot.` qualifiers and refer to identifiers unqualified.
**why** (stated): The maintainer notes: "Since the WithBot namespace is open, you can avoid the `WithBot.`", i.e. prefer unqualified names for style/readability when the namespace is already open.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] Since the WithBot namespace is open, you can avoid the `WithBot.`

## pr33267_i03  [V3/style/unknown]
**ask**: Reformat the definition/docstring so that when the entire statement fits on one line, it is kept on one line (avoid extra indentation/line breaks in such cases).
**why** (stated): Maintainer preference: "the indentation where the whole statement fits one one line is actually preferred."
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] I think the indentation where the whole statement fits one  one line is actually preferred.

## pr33267_i04  [V2/docs/partially_adopted]
**ask**: In the docstring for `WithBot.toDual` (and corresponding dual docs), replace the reference `WithBot.toDual_top_equiv` with the current lemma name `WithBot.toDualTopEquiv` (and similarly use `WithBot.ofDualTopEquiv` instead of `WithBot.ofDual_top_equiv`).
**why** (inferred): The referenced order-iso lemma was renamed; the docs should point to the existing canonical name `WithBot.toDualTopEquiv` (and its `ofDual` analogue) so links resolve and naming is consistent with current Mathlib conventions.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] ```suggestion See `WithBot.toDualTopEquiv` for the related order-iso. -/ ``` Looks like this was renamed at some point: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv

## pr33232_i01  [V3/style/adopted]
**ask**: Rewrite `fourierTransformInv_toTemperedDistributionCLM_eq` so the `:=` is immediately followed by `calc` (i.e. `... := calc ...`) rather than putting `calc` on the next line, using `_` placeholders for the start/end of the calc chain.
**why** (inferred): Maintainer requests a minor style tweak to the `calc` proof layout (start/end `_` and placing `calc` after `:=`), a formatting/nitpick change that should not affect elaboration.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] style nit. I didn't actually test that it still elaborates properly with the starting and ending `_`, but I don't see which it shouldn't. ```suggestion     𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc   _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) :=

## pr33232_i02  [V3/docs/adopted]
**ask**: Add a proper docstring to `fourierTransformInv_toTemperedDistributionCLM_eq` stating that the distributional inverse Fourier transform coincides with the classical inverse Fourier transform on `𝓢(E, F)` (not `𝓢(ℝ, F)`).
**why** (inferred): The maintainer supplied a suggested documentation comment for the theorem `fourierTransformInv_toTemperedDistributionCLM_eq`, indicating it should be documented as an extension/coincidence result on Schwartz space.
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] ```suggestion /-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/ theorem fourierTransformInv_toTemperedDistributionCLM_eq (f : 𝓢(E, F)) : ```

## pr33208_i01  [V2/docs/partially_adopted]
**ask**: (1) Rename and restate `IsMulIndecomposable_id_univ` to `isMulIndecomposable_id_univ` with the argument `x` made implicit: change the signature from `lemma IsMulIndecomposable_id_univ ... (x : M) (hx : x ≠ 1) :` to `lemma isMulIndecomposable_id_univ ... {x : M} (hx : x ≠ 1) :`. (2) Expand/improve the docstring for `Submonoid.closure_image_one_lt_and_isMulIndecomposable` to include the explanatory paragraph describing the setup (`S` linearly ordered cancellative, `f : M →* S`, `v : ι → M`) and the conclusion (the submonoid generated by `f (v i) > 1` is generated by the indecomposable subset), and add a corresponding docstring for the additive `to_additive` lemma.
**why** (stated): The maintainer found the Serre-lemma statement hard to parse and requested a more informative docstring spelling out the meaning, and noted that the additive version lacks its own docstring. They also suggested aligning lemma naming/style by using lowerCamelCase and making `x` implicit in `isMulIndecomposable_id_univ`.
**anchors**: Indecomposable.lean:1  (* = inferred)
> [V2] ```suggestion lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ```
> [V3] I found the statement a bit hard to parse, so I found myself wanting a more informative docstring. Please check that my interpretation is correct, or otherwise improve it.  ```suggestion /-- This is [serre1965](Ch. V, §9, Lemma 2) and may be used to 

## pr33207_i01  [V4/scope/adopted | NOT JUDGEABLE]
**ask**: Connect the new `Order/Argmin` material to the existing `Minimal`/`MinimalFor` API (and optionally, less importantly, to `List.argmin`), rather than leaving it as a standalone definition/API.
**why** (stated): Maintainer says it would be nice to connect the material here to the `Minimal`/`MinimalFor` API (and potentially `List.argmin`), suggesting the current approach may be less usable than leveraging existing minimality APIs like `Set.Finite.exists_minimal`.
**anchors**: Argmin.lean:1  (* = inferred)
> [V4] Is it definitely easier to use this definition rather than using choice/`obtain` on `Set.Finite.exists_minimal`?   It would be nice to connect the material here to the `Minimal`/`MinimalFor` API (the latter of which isn't quite complete at the mome

## pr33203_i01  [V3/naming/adopted]
**ask**: Rename the misleading `Rat.intEquiv` definition to a more descriptive name (as `Rat.IsIntegralClosure.intEquiv`) that reflects it is an isomorphism `R ≃+* ℤ` only under the integral-closure-of-ℤ-in-ℚ assumptions, keeping `Rat.intEquiv` only as a deprecated alias.
**why** (stated): Maintainer notes that a name like `Rat.intEquiv` suggests an equivalence involving `ℚ` itself (e.g. `ℚ ≃ ℤ`), not an isomorphism from an integral closure `R` of `ℤ` in `ℚ` to `ℤ`; the name should therefore encode the actual assumptions/intent to avoid confusion.
**anchors**: HeightOneSpectrum.lean:62, HeightOneSpectrum.lean:70  (* = inferred)
> [V3] I'd just like to mention that this is not at all what I'd expect from something called `Rat.intEquiv`! I was expecting some sort of bijection `ℚ ≃ ℤ` instead.

## pr33201_i01  [V2/duplication/adopted]
**ask**: Replace the bespoke homotopy-category-specific proofs of `Subsingleton (x ⟶ y)` and terminality with proofs that reuse existing generic instances: (1) define `subsingleton_hom` by transporting `Unique (X _⦋0⦌₂)` to `Unique (OneTruncation₂ X)`, get `Subsingleton` edge-homs via `X.Edge`, and then apply `CategoryTheory.Quotient.instSubsingletonHom`; (2) add `instance (X : Truncated 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory := ... CategoryTheory.Quotient.instUnique _`; (3) redefine `isTerminal` to use `Cat.isTerminalOfUniqueOfIsDiscrete` after installing `IsDiscrete` via `eq_of_hom := by subsingleton`, instead of `IsTerminal.ofUniqueHom` with an explicit functor-ext proof.
**why** (stated): The maintainer judged the existing proof as "too specialized for the homotopy category" and noted Mathlib already has general facts about quotient categories inheriting subsingleton homs and about terminality in `Cat` from `Unique` + `IsDiscrete`, so the code should leverage those library lemmas/instances rather than building ad hoc `MorphismProperty` arguments and explicit terminality constructions.
**anchors**: HomotopyCat.lean:455, HomotopyCat.lean:455  (* = inferred)
> [V2] I feel like this proof is too specialized for the homotopy category. Mathlib arleady knows that quotient categories of categories with unique objects and subsingleton homs have subsingleton homs, and that free categories on quivers with unique object
> [V2] Same here: we already have `Cat.isTerminalOfUniqueOfIsDiscrete`: ```suggestion instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory :=    letI : Unique (OneTruncation₂ X) := inferInstanceAs (Unique (X _⦋0⦌₂))   CategoryTh

## pr33201_i02  [V2/duplication/dropped]
**ask**: Remove the locally defined `Monoidal` instance for `((Functor.whiskeringLeft J J' C).obj F)` in `Monoidal/Cartesian/FunctorCategory.lean` and instead use (or restate via) the existing `CategoryTheory.Functor.Monoidal.whiskeringLeft` construction from `Mathlib/CategoryTheory/Monoidal/FunctorCategory`.
**why** (stated): The maintainer notes the added instance "seems to be a (less general) duplicate" of the existing `CategoryTheory.Functor.Monoidal.whiskeringLeft`, so the PR should avoid reintroducing an already-available (and more general) definition/instance.
**anchors**: FunctorCategory.lean:192  (* = inferred)
> [V2] This seems to be a (less general) duplicate of [CategoryTheory.Functor.Monoidal.whiskeringLeft](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Monoidal/FunctorCategory.html#CategoryTheory.Functor.Monoidal.whiskeringLeft)

## pr33201_i03  [V3/style/adopted]
**ask**: After defining `fullyFaithfulCurry`/`fullyFaithfulCurry₃` (and similarly for `uncurry₃`), also add the corresponding typeclass instances `Full` and `Faithful` for these currying/uncurrying functors, obtained from the `FullyFaithful` proofs (i.e. `instance : ... .Full := fullyFaithful... .full` and `instance : ... .Faithful := fullyFaithful... .faithful`).
**why** (stated): The maintainer explicitly requests that the PR not only provide `FullyFaithful` definitions but also register `Full` and `Faithful` instances so downstream code can use these properties via typeclass inference (“please also add the `Full` and `Faithful` instances”).
**anchors**: Currying.lean:110, Currying.lean:110, CurryingThree.lean:43, CurryingThree.lean:43  (* = inferred)
> [V3] Please add the corresponding `Full` and `Faithful` instances (we really need a way to automate adding those via an attribute we can put on a `FullyFaithful` definition!).
> [V3] Same  comment: please also add the `Full` and `Faithful` instances

## pr33200_i01  [V1/scope/dropped | NOT JUDGEABLE]
**ask**: Do not merge/submit this PR as-is: remove all `sorry`s and eliminate the newly introduced axioms (and generally avoid AI-generated, non-mathlib-style large additions), i.e. provide fully proved, axiom-free, reviewable mathlib-style code or close/withdraw the PR.
**why** (stated): Maintainers state the PR is "completely unsuitable for mathlib" because it is too long to review and "has axioms" and "has sorries"; one comment notes the author introduced "4 times as many axioms as we use in all of Mathlib". These are each given as individually sufficient reasons to close the PR.
**anchors**:   (* = inferred)
> [V1] The issue is nothing to do with the code of conduct. This PR is completely unsuitable for mathlib for multiple reasons. (a) it is far too long to review (b) it has axioms (c) it has sorries (d) it was written by an AI which seems to have no understan
> [V1] > no axioms  I encourage you to learn how to use `grep`, as you have in one file introduced 4 times as many axioms as we use in *all* of Mathlib.  I won't be engaging further and wasting my time.

## pr33198_i01  [V4/naming/dropped]
**ask**: Standardize the spelling scheme for ordinal/cardinal names: if introducing `omega_one`/`aleph_one`, also rename existing `omega0`/`aleph0` (and similar) to the corresponding `omega_zero`/`aleph_zero` to keep the convention consistent (rather than mixing digit/word forms).
**why** (stated): Maintainer objects to mixing styles: "you want to write `omega0` and `aleph0` and also `omega_one` and `aleph_one`?" and suggests that consistency would favor `omega_zero`/`aleph_zero` as well.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] I'm confused, you want to write `omega0` and `aleph0` and also `omega_one` and `alepg_one`? I'm virtually certain that if you asked on Zulip, the poll would go in favor of `omega_zero` too and `aleph_zero` too (at least, assuming votes from the same 

## pr33198_i02  [V4/other/unknown | NOT JUDGEABLE]
**ask**: Preserve the existing asymmetry in the relevant lemma; do not “symmetrize” it or rewrite it into a symmetric-looking statement, since the asymmetry is meaningful.
**why** (stated): The maintainer notes that “the asymmetry in that lemma is actually very important” and that it “indicates something meaningful about the difference between them,” so the lemma’s statement should remain asymmetric rather than being refactored into a symmetric form.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] Oh I see! Then I think the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.

## pr33198_i03  [V1/other/unknown]
**ask**: Fix the build failures (make the PR compile/CI pass) before merging.
**why** (stated): Maintainer explicitly notes the build is failing and sets bors to reject until fixed ("bors r-" / "bors d+").
**anchors**:   (* = inferred)
> [V1] The build is failing: https://github.com/leanprover-community/mathlib4/actions/runs/20436145675/job/58717788626#step:22:905 bors r- bors d+

## pr33190_i01  [V3/style/adopted]
**ask**: In `eq_of_natDegree_lt_card_of_eval_eq`, change the `apply` line to pass `hf` as a positional argument rather than a named implicit, i.e. replace `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero (hf := hf)` with `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf`.
**why** (stated): The maintainer was momentarily confused about why `hf` wasn’t an explicit argument; writing the `apply` with an explicit placeholder for the first argument and then `hf` as the next argument makes the argument order and usage clearer at the call site.
**anchors**: Roots.lean:630  (* = inferred)
> [V3] only because I was confused why `hf` wasn't an explicit argument, and then after looking above, I realized it is. ```suggestion   apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf ```

## pr33183_i01  [V3/style/unknown]
**ask**: Refactor pointwise definitions to use argument binders rather than nested lambdas (e.g. write `tensorObj X Y i := X i ⊗ Y i`, `tensorHom f g i := f i ⊗ₘ g i`, `whiskerLeft X _ _ f i := X i ◁ f i`, `whiskerRight f Y i := f i ▷ Y i`, `tensorUnit i := 𝟙_ (C i)`), add/complete the docstring to start `/-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ...`, and simplify the `closed` field to a record literal `closed X := { rightAdj := ihom X, adj.unit := closedUnit X, adj.counit := closedCounit X }`.
**why** (inferred): The maintainer suggests stylistic rewrites for readability/idiomatic Lean (avoiding `fun ... ↦ fun i ↦ ...`), wants the documentation comment to mention `Pi.monoidalCategory C` explicitly, and prefers the concise record literal for the `closed` construction.
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   tensorObj X Y i := X i ⊗ Y i   tensorHom f g i := f i ⊗ₘ g i   whiskerLeft X _ _ f i := X i ◁ f i   whiskerRight f Y i := f i ▷ Y i   tensorUnit i := 𝟙_ (C i) ```
> [V3] ```suggestion /-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ```
> [V3] ```suggestion   closed X := {     rightAdj := ihom X     adj.unit := closedUnit X     adj.counit := closedCounit X } ```

## pr33169_i01  [V2/style/adopted]
**ask**: Reformat the `| succ n hn =>` branch so that `simpa only [...]` is on the next line and the simp-lemma list is wrapped/indented as:
`| succ n hn =>
    simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,
      prop_red_T hS hT]` (including spacing `(n : ℤ)` and indenting `prop_red_T ...` under the bracket).
**why** (inferred): The maintainer is not convinced the current whitespace change is better and provides a preferred formatting for the `succ` case, with line breaks/indentation that match Mathlib style.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V4] Please revert this one; I'm not convinced it's better.
> [V2] ```suggestion   | succ n hn =>     simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,       prop_red_T hS hT] ```

## pr33158_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No change requested (maintainer approved and merged as-is).
**why** (stated): The maintainer expressed mild skepticism about usefulness (“not so sure that we will ever care…”) but explicitly agreed the change “can’t hurt” and approved (`bors r+`), with no further requested edits.
**anchors**:   (* = inferred)
> [V4] I'm not so sure that we will ever care about Stieltjes measures on the empty space, but in any case I agree this can't hurt. Thanks! bors r+

## pr33156_i01  [V3/docs/adopted]
**ask**: Add the missing doc-string for the newly introduced `optAttrArg` syntax (in `Mathlib/Util/AddRelatedDecl.lean`).
**why** (stated): The maintainer explicitly notes that a doc-string is missing; new public-facing syntax/utilities in Mathlib should be documented with a doc-string for clarity and maintainability.
**anchors**:   (* = inferred)
> [V3] (Please add the missing doc-string, though.)

## pr33154_i01  [V3/docs/dropped | NOT JUDGEABLE]
**ask**: Update the documentation/comment around line 24 to explicitly mention `to_fun` (in addition to whatever it currently references).
**why** (stated): Maintainer asks: “should line 24 also mention `to_fun`?”—i.e., the docs/comment at that location should include `to_fun` for clarity/completeness.
**anchors**:   (* = inferred)
> [V3] Pre-existing: should line 24 also mention `to_fun`?

## pr33153_i01  [V2/docs/dropped | NOT JUDGEABLE]
**ask**: Clarify the PR diff by making the changes visible/meaningful (i.e., ensure the edited doc/comment text actually differs from the original so the reviewer can see what changed).
**why** (stated): Reviewer states they "can't see the difference here", indicating the presented documentation edits are not discernible (possibly no-op/whitespace-only or too subtle) and should be adjusted so the change is clearly reflected in the diff.
**anchors**:   (* = inferred)
> [V2] I can't see the difference here. 

## pr33152_i01  [V2/duplication/partially_adopted]
**ask**: Remove the extra lemma `meromorphicOn_univ`; instead use the existing `Meromorphic.meromorphicOn` (optionally supplying the implicit `s := Set.univ` argument when inference fails), and do not add an unprotected `Meromorphic.meromorphicOn_univ` declaration.
**why** (stated): Maintainer says this declaration is not generally included; if it existed it would need to be `protected`, but it's unnecessary because `Meromorphic.meromorphicOn` already works with `univ` by typeclass inference or by manually providing the implicit set argument.
**anchors**: Basic.lean:562*  (* = inferred)
> [V2] I don't think we generally include the new declaration `Meromorphic.meromorphicOn_univ`. It would need to be protected if we did, but you should also just be able to use `Meromorphic.meromorphicOn`. When Lean can infer `univ`, it works, and when it c

## pr33151_i01  [V2/naming/adopted]
**ask**: Update `Mathlib/Tactic/Translate/ToDual.lean`’s `GuessName.abbreviationDict` (or related name-fixing dictionary) to explicitly map the dualized names so that `succColimit` is guessed/translated as `SuccLimit` and `predColimit` as `PredLimit` (i.e. un-translate `colimit` back to `limit` in these `succ`/`pred`-prefixed cases), instead of relying on broader `limit/colimit` translation.
**why** (stated): The maintainer suggests that, since the only problematic `limit` translations are those preceded by `succ` or `pred`, it’s simpler to fix name-guessing by adding targeted dictionary entries so `to_dual` produces the intended theorem/instance names (`SuccLimit`/`PredLimit`) rather than `succColimit`/`predColimit`.
**anchors**: ToDual.lean:153*  (* = inferred)
> [V2] Is it true that all instances of the word `limit` that need to be translated are preceded by either `succ` or `pred`? In that case it may be better to use the fixAbbreviations dictionary to un-translate `colimit` to`limit` in these cases.  (I agree w
> [V2] In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.

## pr33150_i01  [V2/naming/adopted]
**ask**: Change the `to_dual` attribute on `pred_le_iff_le_succ` to specify the correct dual lemma name, i.e. replace `@[to_dual]` with `@[to_dual le_succ_iff_pred_le]`.
**why** (stated): The maintainer notes that the current `to_dual` annotation "generates the wrong dual name", so the attribute needs an explicit target dual-name to avoid incorrect/undesired autogenerated naming.
**anchors**: Basic.lean:828  (* = inferred)
> [V2] I think this generates the wrong dual name

## pr33149_i01  [V1/other/dropped]
**ask**: Remove the newly introduced `axiom` declarations (and any dependence on them), replacing them with non-axiomatic constructions/proofs or existing Mathlib lemmas so that the file adds no new axioms.
**why** (stated): Maintainer cites Mathlib's no-axioms policy: "Please don't introduce any new axioms." The reviewed code adds multiple `axiom`s (`cMoser`, `cGronwall`, `cSobolev`, their positivity lemmas, `fourier_ortho_integral`, `fubini_torus3`, etc.), which violates this policy.
**anchors**:   (* = inferred)
> [V1] Mathlib has a no-axioms policy. Please don't introduce any new axioms.

## pr33149_i02  [V2/duplication/dropped | NOT JUDGEABLE]
**ask**: Replace any custom proof/axiom/lemma of Parseval's identity (including versions specialized to the standard basis of ℝ^n) with the existing Mathlib Parseval identity; if a specialized lemma is truly needed, add that specialization as a lemma in the existing Parseval/orthonormal-basis API rather than reintroducing Parseval locally in this new file.
**why** (stated): Maintainer notes that Mathlib already has Parseval's identity and asks to use it instead; only if a specialized version is required should it be added in the appropriate existing location (e.g. for the standard basis in ℝ^n), rather than duplicating it in this PR.
**anchors**:   (* = inferred)
> [V2] Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).

## pr33149_i03  [V3/other/dropped | NOT JUDGEABLE | META]
**ask**: Remove the newly introduced `axiom` declarations (no new axioms) and, for any new definitions/structures you keep, add a basic supporting lemma API so the additions are maintainable; additionally, disclose in the PR description whether/how AI was used to generate the code (what parts, prompts, and author understanding).
**why** (stated): Maintainer flags two blocking issues: (1) "Introducing additional axioms is a no go"—the file defines many `axiom`s (e.g. `cMoser`, `fourier_ortho_integral`, etc.), which cannot be accepted in mathlib. (2) "lots of new definitions without supporting lemmas (that is not maintainable; please add basic lemmas about them when adding them)." They also request PR metadata clarification: explain AI usage in the PR description to enable appropriate review.
**anchors**:   (* = inferred)
> [V3] Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) 

## pr33149_i04  [V4/other/dropped | NOT JUDGEABLE]
**ask**: Rewrite the file to meet mathlib standards by (1) removing all `axiom`s (replace with actual definitions/lemmas deduced from mathlib, or mark gaps with `sorry` during development), (2) eliminating local wrapper definitions that just rename existing mathlib definitions (inline them; only introduce a rare `abbrev` if truly needed), and (3) fixing definitions such as `fourierDecay` and `spectralNSResidual` (and hence `SolvesNavierStokes`) so they are not vacuously true.
**why** (stated): The maintainer states the PR would need a complete rewrite: mathlib does not accept new `axiom`s, short-name wrappers should be inlined or at most `abbrev` used sparingly, and some key definitions are currently vacuous (indicating likely incorrect formalization), which is a major red flag and makes the PR unacceptable as-is.
**anchors**:   (* = inferred)
> [V4] Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33146_i01  [V3/docs/adopted]
**ask**: Capitalize the docstring for the precompose lemma so it reads "/-- Precompose an equation between morphisms by another morphism -/" (instead of "precompose").
**why** (stated): The maintainer suggests fixing capitalization in the doc comment: "Might as well fix some capitalization" and provides the corrected docstring.
**anchors**: Basic.lean:223  (* = inferred)
> [V3] Might as well fix some capitalization. ```suggestion /-- Precompose an equation between morphisms by another morphism -/] ```

## pr33145_i01  [V2/duplication/adopted]
**ask**: Rename `Dense.continuous_upperBounds` to `Dense.upperBounds_image` and rename `Dense.continuous_lowerBounds` to `Dense.lowerBounds_image`, and refactor the proof of the lower-bounds lemma to be obtained via order duality from the upper-bounds lemma (i.e. `lowerBounds (f '' S) = lowerBounds (range f) := hS.continuous_upperBounds (α := αᵒᵈ) hf`).
**why** (inferred): The maintainer suggests more standard names (`upperBounds_image`/`lowerBounds_image`) and points out a standard trick to avoid duplicating essentially the same argument: derive the lower-bounds statement from the upper-bounds one using `OrderDual`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] ```suggestion theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] There's a trick you can use for this kind of thing by using the `OrderDual`. ```suggestion     lowerBounds (f '' S) = lowerBounds (range f) :=   hS.continuous_upperBounds (α := αᵒᵈ) hf ```

## pr33145_i02  [V2/duplication/adopted]
**ask**: Replace the bespoke `Dense.continuous_upperBounds`/`Dense.continuous_lowerBounds` additions with more general dense-set lemmas `Dense.ciSup` and `Dense.ciInf` (for `α` a `TopologicalSpace`), and derive the infimum statement by applying the supremum lemma to the order dual, i.e. prove the `ciInf` result via `hS.ciSup (α := αᵒᵈ) hf h` (e.g. `⨅ i, f i = ⨅ s : S, f s := hS.ciSup (α := αᵒᵈ) hf h`).
**why** (inferred): The reviewer proposes introducing symmetric `ciSup`/`ciInf` lemmas at the `Dense` level and using order duality to avoid duplicating parallel sup/inf developments (explicitly suggesting `ciInf` be obtained from `ciSup` with `α := αᵒᵈ`).
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup (α := αᵒᵈ) hf h ```

## pr33145_i03  [V2/duplication/adopted]
**ask**: Add dualized dense-set lemmas `Dense.ciSup'` and `Dense.ciInf'` (with binder `{α : Type*} [TopologicalSpace α]`) and refactor the `ciInf` statement/proof to use the `ciSup'` lemma on the order dual, i.e. prove `⨅ i, f i = ⨅ s : S, f s` by `hS.ciSup' (α := αᵒᵈ) hf`.
**why** (inferred): The maintainer is steering the development toward providing symmetric `ciSup`/`ciInf` API via order duality, and to avoid duplicating separate `ciInf` proofs when they can be obtained by applying the `ciSup` lemma to `αᵒᵈ` (as explicitly indicated by the suggested proof snippet).
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup' (α := αᵒᵈ) hf ```

## pr33145_i04  [V2/style/partially_adopted]
**ask**: Rewrite the proof of the dense-set `ciSup`/supremum lemma to start with `by_cases h : BddAbove (range (fun x : S ↦ f x))`, using `hS.ciSup hf (h.closure.mono …)` in the bounded case and, in the unbounded case, first derive `¬ BddAbove (range f)` and then finish by `simp [ciSup_of_not_bddAbove, this, h]` (with the indicated `contrapose`/`mono` step).
**why** (stated): The maintainer indicates the proof is simpler/clearer if it splits on boundedness of the range of the function restricted to the dense subtype, and then handles the unbounded case via `ciSup_of_not_bddAbove` and a monotonicity/contrapositive argument relating `BddAbove (range f)` to `BddAbove (range (fun x : S ↦ f x))`.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] It's easier if you case split on whether the range of the function from the subtype is bounded above or not. ```suggestion   by_cases h : BddAbove (range (fun x : S ↦ f x))   · refine hS.ciSup hf <| h.closure.mono ?_     simpa [← Function.comp_def, r

## pr33145_i05  [V3/style/dropped]
**ask**: Rewrite the `iSup`/`iInf` equalities so the dense-set supremum/infimum appears on the left-hand side and the `univ`/full-domain one on the right, i.e. change statements like `⨆ i, f i = ⨆ s : S, f s` to `⨆ s : S, f s = ⨆ i, f i` (and similarly for `iInf`).
**why** (inferred): The maintainer suggests flipping the sides of the `iSup`/`iInf` declarations so they read `⨆ s : S, f s = ⨆ i, f i := by` instead of the current orientation; this is a stylistic/readability preference about how the lemma statements are presented.
**anchors**:   (* = inferred)
> [V3] I suggest turning the declarations involving `iSup` and `iInf` around so that they read: ```lean     ⨆ s : S, f s = ⨆ i, f i := by ``` instead.

## pr33144_i01  [V2/duplication/unknown]
**ask**: Remove the redundant eta-expanded `fun_` lemmas (`fun_deriv` and `fun_iterated_deriv`) in `Analysis/Meromorphic/Basic` (both the `MeromorphicAt` and `MeromorphicOn` versions), relying instead on the existing `deriv` and `iterated_deriv` lemmas unless such `fun_` versions are later needed.
**why** (stated): Maintainer decision: only add `fun_` versions as needed; since these lemmas are unused and merely restate existing results with a trivial `fun _ => ...` wrapper, they should be removed to reduce redundancy.
**anchors**:   (* = inferred)
> [V4] This PR itself it straightforward; the main question is whether we want it.
> [V2] @kebekus Thanks for the explanation! Let's only add `fun_` versions as needed then --- as these lemmas are unused, let's remove them. bors r+

## pr33141_i01  [V2/style/adopted]
**ask**: Add `(relevant_arg := X)` to the `@[to_additive]` attributes on all declarations in this file (instances/lemmas like `instIsCocomm`, `counit_single`, `comul_single`), not just `instCoalgebra`.
**why** (inferred): The maintainer explicitly requests that every `to_additive`-generated declaration specify `relevant_arg := X`, likely to ensure the additive translation treats the `X` parameter as the relevant argument for name generation/translation consistency across the file.
**anchors**: MonoidAlgebra.lean:35  (* = inferred)
> [V2] I think you need the `(relevant_arg := X)` on all of the declarations in this file

## pr33137_i01  [V2/style/dropped]
**ask**: In the `mapDomainNonUnitalAlgHom` structure definition, replace the explicit lambda `map_mul' := fun x y => mapDomain_mul f x y` with the direct assignment `map_mul' := mapDomain_mul f`.
**why** (inferred): Style simplification: `mapDomain_mul f` already has the required arguments, so the extra `fun x y => ... x y` is unnecessary and can be eta-reduced.
**anchors**: Basic.lean:217  (* = inferred)
> [V2] ```suggestion   map_mul' := mapDomain_mul f ```

## pr33127_i01  [V2/docs/adopted]
**ask**: Remove the standalone `example` test code and instead add an explanatory comment at the top of the `pm_one` section (e.g. explaining why the `haveI` instances appear in the lemma statements).
**why** (stated): Maintainer identified the `example` as test code that should be removed, and suggested the surrounding explanation be turned into a comment at the top of the section for documentation/context.
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V2] I assume this is test code, and can be removed? ```suggestion ```
> [V3] This may be worth turning into a comment at the top of the section!

## pr33117_i01  [V2/duplication/dropped]
**ask**: Replace the duplicated `@[fun_prop]` lemmas (and corresponding `fun_*` variants) in `namespace Meromorphic` with versions annotated `@[to_fun (attr := fun_prop)]` (after importing `Mathlib.Tactic.ToFun`), so `fun_prop` can derive the `fun x ↦ …` forms automatically; apply this to lemmas like `neg`, `add`, `sum`, `sub`, `mul`, `prod`, `div`, `pow`, `zpow`, `deriv`, and `iterated_deriv`.
**why** (inferred): Maintainer notes that new metaprogramming (`to_fun` attribute) can generate the “function-lambda” lemma forms, avoiding manual duplication (`neg`/`fun_neg`, `add`/`fun_add`, etc.), and suggests adding the needed import `Mathlib.Tactic.ToFun`.
**anchors**: Basic.lean:631  (* = inferred)
> [V2] There is some new metaprogramming that can help here: the `to_fun` attribute. To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).  ```suggestion @[to_fun (attr := fun_prop)] lemma neg (hf : Meromorphic

## pr33111_i01  [V3/naming/dropped]
**ask**: Rename the newly introduced injectivity lemmas to keep the `injective_of_*` naming consistent: use `injective_of_eq_imp_le` (instead of `Function.Injective.of_eq_imp_le`) and rename the other new/related lemma(s) similarly rather than switching to the `Function.Injective.of_*` dot-notation style.
**why** (stated): Maintainer explicitly questions the new name (`why not call it injective_of_eq_imp_le?`) and then concludes they want consistency in naming across the family of lemmas (`keep things consistent and rename the others in a better way`).
**anchors**: Defs.lean:320*  (* = inferred)
> [V3] why not call it `injective_of_eq_imp_le`?
> [V3] You could deprecate it. Probably a good idea. ~~But I'd suggest keeping the theorem as is, just add the `@[deprecated Function.Injective.of_... (since := ...)]`.~~
> [V3] Meh, rename away. I only suggested it to keep things consistent. So let's keep things consistent and rename the others in a better way!

## pr33111_i02  [V2/proof-golf/partially_adopted]
**ask**: Reorder lemmas so the new `injective_of_eq_imp_le` (or `Function.Injective.of_eq_imp_le`) is defined before `injective_of_lt_imp_ne`, and then simplify the proof of `injective_of_lt_imp_ne` to a one-liner using `injective_of_eq_imp_le` (either `exact injective_of_eq_imp_le f ...` with the provided argument, or `grind [injective_of_eq_imp_le]`).
**why** (inferred): The maintainer suggests that if the new lemma is moved earlier, the existing injectivity lemma can be proved directly from it, yielding a shorter/cleaner proof (either by an explicit `exact ...` line or by `grind [injective_of_eq_imp_le]`).
**anchors**:   (* = inferred)
> [V2] if you move the new lemma before this one, you could do ```suggestion   exact injective_of_eq_imp_le f fun {x y} ↦     not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x) ``` or ```suggestion   grind [injective_of_eq_imp_le] ```

## pr33111_i03  [V4/naming/dropped | META]
**ask**: Revise the PR title to accurately reflect that the change is adding a more general injectivity lemma (rather than “weakening the hypothesis” of the existing one).
**why** (stated): Maintainer notes: “The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.” So the requested change is to correct misleading PR metadata.
**anchors**: Defs.lean:320*  (* = inferred)
> [V4] The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.

## pr33107_i01  [V4/scope/dropped | NOT JUDGEABLE]
**ask**: Refactor `LinearMap.ker` and `LinearMap.range` to take an explicit `LinearMap` argument (not a linear-map typeclass), so that `ContinuousLinearMap` inherits the desired simp/dot-notation behavior without adding ad-hoc simp lemmas like `ker_mk`, `range_mk`, `range_zero`, and `ker_zero`.
**why** (stated): Maintainers say the PR is “exposing a flaw” in the current library: `LinearMap.ker`/`LinearMap.range` are defined in terms of a linear map class, and they want them refactored to accept an actual linear map; then the simp lemmas for `ContinuousLinearMap` “come for free” and dot notation improves.
**anchors**:   (* = inferred)
> [V4] I think we should refactor the definitions of `LinearMap.range` and `LinearMap.ker` to take in an actual linear map and not a linear map class. That way, all of this comes for free. It'll also allow for dot notation, solve more of these issues, etc..
> [V4] @Timeroot yes, Monica is correct here. Unfortunately you are exposing a flaw that exists currently in the library. Help ripping it out is encouraged! For more information see the Zulip thread: [#mathlib4 > Mathlib's morphism hierarchy](https://leanpr

## pr33104_i01  [V3/naming/dropped]
**ask**: Rename the `Homeomorph` and `UniformEquiv` transfer abbrevs from `pseudometricSpace` to `pseudoMetricSpace` (capitalizing the `M`), i.e. change `protected abbrev pseudometricSpace ...` to `protected abbrev pseudoMetricSpace ...` in both namespaces.
**why** (inferred): Mathlib naming convention uses `PseudoMetricSpace`/`pseudoMetricSpace` with a capital `M` in the middle; the maintainer suggests the correct casing explicitly for the two new declarations.
**anchors**:   (* = inferred)
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ```
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ```

## pr33101_i01  [V3/scope/adopted]
**ask**: Wrap the earlier duplicated `variable` declarations in a `section`/`end` block and insert an `end` before the new `variable {K V₁ V₂ : Type*} ...` block so the variables don’t leak/duplicate unexpectedly.
**why** (stated): Maintainer notes the file now has duplicated `variable`s; enclosing the previous ones in a `section`/`end` avoids scope surprises from variables persisting past where they’re intended.
**anchors**: Lemmas.lean:781, Lemmas.lean:780, Lemmas.lean:722*, Lemmas.lean:721*  (* = inferred)
> [V3] It looks like this duplicates the `variable`s.  Could you enclose the previous one in a `section`/`end` block, to avoid "surprises"?

## pr33098_i01  [V2/style/adopted]
**ask**: Replace the manual `by_cases` proof of `minimalCover_subset` (and similarly `maximalSeparatedSet_subset` and nearby lemmas) with `grind` proofs, adding `attribute [grind .] finite_empty` and `attribute [grind .] IsSeparated.empty` so `grind [minimalCover]` / `grind [maximalSeparatedSet]` can solve `finite_minimalCover` and `isSeparated_maximalSeparatedSet`; also rename lemmas `encard_*` and `encard_le_of_isSeparated` to take an explicit non-`⊤` hypothesis parameter as in `lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) :` and `lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :` and `lemma encard_le_of_isSeparated (h_subset : C ⊆ A)`.
**why** (inferred): Maintainer indicates several lemmas can be proved automatically via `grind` if `finite_empty` and `IsSeparated.empty` are registered, and provides explicit suggested proofs; they also suggest standardizing lemma statements/arguments for `encard_*` and `encard_le_of_isSeparated` by explicitly naming the non-`⊤` and subset hypotheses in the binder.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add ```lean attribute [grind .] finite_empty ``` but I think we should do that anyway. ```suggestion lemma minimalCover_subset : min
> [V2] This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add ```lean attribute [grind .] IsSeparated.empty ``` but I think we should do that anyway.  ```suggestion lemma maximalSe
> [V2] ```suggestion lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_le_of_isSeparated (h_subset : C ⊆ A) ```

## pr33098_i02  [V2/proof-golf/partially_adopted]
**ask**: Rewrite the `by_contra` step in the maximal-separated-set argument by introducing `C := {x} ∪ maximalSeparatedSet ε A`, proving `C ⊆ A ∧ IsSeparated ε C` (using `Metric.isSeparated_insert_of_notMem` plus `hx_not_mem : x ∉ maximalSeparatedSet ε A`), and then deriving the contradiction via `encard_le_of_isSeparated` together with `simp` on `encard_insert_of_notMem` and `ENat.lt_add_one_iff`.
**why** (stated): The maintainer proposes a proof-golf refactor: “the main point is to use `Metric.isSeparated_insert_of_notMem`”, with some reshuffling to make the contradiction proof shorter/cleaner.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`. ```lean   intro x hxA   by_contra! h_dist   let C :=

## pr33098_i03  [V2/style/partially_adopted]
**ask**: In `coveringNumber_le_packingNumber`, replace the manual `by_cases` split and subsequent `card_maximalSeparatedSet`/`iInf`-based proof with the streamlined proof using `by_cases!` plus `encard_maximalSeparatedSet` and `IsCover.coveringNumber_le_encard` (with `maximalSeparatedSet_subset`), and simplify the `⊤` case via `simp [h_top]`.
**why** (stated): The maintainer points out newer tactics/lemmas: use `by_cases!` to automatically push negations in the second branch, and use the existing lemma `IsCover.coveringNumber_le_encard` together with `encard_maximalSeparatedSet` rather than reproving the inequality via `iInf`/`card_...` gymnastics.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley: ```suggestion   by_cases! h_top : packingNumber ε A ≠ ⊤   · rw [← 

## pr33098_i04  [V2/style/dropped]
**ask**: In the proof of `coveringNumber_two_mul_le_externalCoveringNumber`, replace the `rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty); · simp [h_empty]` pattern by `rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty); · simp`, i.e. destruct the empty-set case by rewriting `A` to `∅` directly.
**why** (inferred): The maintainer suggests simplifying the empty/nonempty split: using `rfl` in the empty case lets `simp` close the goal without carrying an explicit `h_empty : A = ∅` hypothesis and an extra `simp [h_empty]`.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] ```suggestion   rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)   · simp ```

## pr33098_i05  [V3/style/adopted]
**ask**: Rewrite the `calc` block in `coveringNumber_subset_le` so that the first line is on the same line as `:= calc`, i.e. start the proof with `coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc` and then put `coveringNumber ε A` as the first indented line, to satisfy calc indentation style guidelines.
**why** (stated): The maintainer notes that otherwise the style guidelines would require indenting all lines below the first `calc` line; restructuring the `calc` header avoids that extra indentation.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V3] otherwise style guidelines would require to indent all lines below the first `calc` line. ```suggestion     coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc   coveringNumber ε A ```

## pr33092_i01  [V3/docs/adopted]
**ask**: Add a docstring explanation for the private `walk_toSimpleGraph'` definition (or equivalent), stating why it exists and what important theorem below it is used to prove (e.g. that it is used in `reachable_toSimpleGraph`).
**why** (stated): Maintainer questions why a definition exists if it is private and requests that, if it is used to prove an important theorem below, the docstring should explicitly say so.
**anchors**: Connected.lean:643, Connected.lean:643, Connected.lean:653  (* = inferred)
> [V3] I don't undertand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.

## pr33090_i01  [V3/style/partially_adopted]
**ask**: Replace the `*_pos` lemmas stated with a `A.Nonempty → 0 < ...` hypothesis/conclusion by `*_pos_iff` lemmas giving an equivalence `0 < ... ↔ A.Nonempty` (so simp can use an iff lemma).
**why** (stated): The maintainer asked to "make this one an iff lemma" because "`simp` would be more efficient then", i.e. prefer a `0 < ... ↔ A.Nonempty` simp lemma over a one-way positivity lemma.
**anchors**: CoveringNumbers.lean:80, CoveringNumbers.lean:98  (* = inferred)
> [V3] Could you make this one an iff lemma? `simp` would be more efficient then.

## pr33086_i01  [V3/docs/adopted]
**ask**: Add documentation clarifying intended usage: `IsCofibrant`/`IsFibrant` should be used as Prop typeclasses, while `cofibrantObjects`/`fibrantObjects` (the `ObjectProperty` wrappers) are only introduced to form the corresponding full subcategories (`CofibrantObject`/`FibrantObject`) and otherwise should not be preferred.
**why** (stated): The maintainer requests a doc entry about the "intended usages" of the two parallel APIs, to prevent confusion: the Prop-class (`IsCofibrant`) is preferred for object properties, and the `ObjectProperty` version exists mainly to build full subcategories; same clarification is needed for fibrant objects.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] I think there should be a documentation entry here about the "intented usages" of the two APIs `cofibrantObjects`/`IsCofibrant`. As far as I understand, `IsCofibrant` is to be used as a Prop-Class, while the object property shouldn’t. This needs to b

## pr33086_i02  [V3/duplication/adopted]
**ask**: Add a missing simp lemma `weakEquivalence_homMk_iff` stating `WeakEquivalence (homMk f) ↔ WeakEquivalence f` for morphisms between bifibrant objects, proved by `simp only [weakEquivalence_iff]; rfl`.
**why** (inferred): Maintainer notes this simp lemma was absent compared to analogous lemmas for the other subcategories/constructors and provides the exact statement/proof to include.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] Was this one intentionally left out compared to the others?  ```suggestion  @[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}     [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :     We

## pr33081_i01  [V2/style/dropped | NOT JUDGEABLE]
**ask**: Replace the existing lambda/proof term with `fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl)` (i.e. use `Set.mem_iUnion_of_mem` and `Set.mem_setOf.mpr le_rfl` to construct the membership proof).
**why** (inferred): The maintainer suggests a more direct/idiomatic proof term for a function producing an `iUnion` membership, using standard lemmas (`Set.mem_iUnion_of_mem`, `Set.mem_setOf.mpr le_rfl`).
**anchors**:   (* = inferred)
> [V2] ```suggestion     fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl) ```

## pr33079_i01  [V3/naming/adopted]
**ask**: Replace the verbose helper lemma `neZero_of_exists` with a more idiomatic/short proof returning `NeZero n` from `i : Fin n`, and rename it to `Fin.neZero` to support dot notation (e.g. `i.neZero`).
**why** (stated): Maintainer asks for a shorter proof term ("Does something like ⟨i.2.ne⟩ work as a proof?") and suggests a dot-notation-friendly name ("what about calling this `Fin.neZero` for dot notation?").
**anchors**: Basic.lean:90, Basic.lean:90  (* = inferred)
> [V3] Does something like ⟨i.2.ne⟩ work as a proof? Also, what about calling this `Fin.neZero` for dot notation?

## pr33078_i01  [V2/style/partially_adopted]
**ask**: Replace the direct `simp`-based proof using `Multiset.prod_eq_one` and a constructed `NeZero (n : ℂ)` with a proof that (1) introduces `have : NeZero n := ⟨hn⟩`, (2) reduces the goal to proving `∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1` via `mahlerMeasure_eq_leadingCoeff_mul_prod_roots` and `roots_eq_primitiveRoots_val`, and (3) proves the product is 1 by showing `∀ x ∈ primitiveRoots n ℂ, ‖x‖ ≤ 1` and then applying `Multiset.prod_eq_one`, using `IsPrimitiveRoot.norm'_eq_one ... hn` to get the bound.
**why** (inferred): Maintainer indicates it suffices to assume `NeZero n` (rather than manually manufacturing `NeZero (n : ℂ)`), letting typeclass inference supply `NeZero (n : ℂ)`, and suggests a cleaner structured proof: reduce to a product over primitive roots with `max 1 ‖x‖`, then show each factor equals 1 using the norm-one lemma for primitive roots.
**anchors**: MahlerMeasure.lean:113, MahlerMeasure.lean:113  (* = inferred)
> [V2] I think it is enough to provide `NeZero n`, and then the typeclass system will find `have : NeZero (n : ℂ)`.
> [V2] ```suggestion   have : NeZero n := ⟨hn⟩   suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1 by     simpa [mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ,       Polynomial.cyclotomic.roots_eq_primitiveRoots_val]   suffices ∀ a ∈ pri

## pr33070_i01  [V2/style/adopted]
**ask**: Replace the manual option lookup `let ppDomain ← withAppArg do return getPPFunBinderTypes (← getOptionsAtCurrPos)` with `let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes` (in both the `Finset.prod` and `Finset.sum` delaborator/pretty-printer blocks).
**why** (inferred): The maintainer indicates the current code is equivalent to the standard idiom `withAppArg <| getPPOption ...`, which is shorter and uses the usual pretty-printer option API for reading `pp.funBinderTypes` in the correct argument context.
**anchors**: Defs.lean:296*  (* = inferred)
> [V2] I think this is the same as ```suggestion   let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes ```

## pr33067_i01  [V2/scope/adopted]
**ask**: Update `Mathlib/Util/AliasIn.lean` (the `alias_in` command) to follow the same info-reporting change as `recall`: stop relying on `addConstInfo` and instead use `addTermInfo'` (with appropriate binder metadata) so the defining-syntax location is reported correctly.
**why** (stated): The maintainer explicitly requests: "Can you also change `alias_in` please?" in the context of discussing `isBinder`/jump-to-definition behavior for syntax that introduces declarations, so they want the same fix applied to `alias_in` as well.
**anchors**: Recall.lean:44  (* = inferred)
> [V2] `isBinder` should be true only when this piece of syntax generates a declaration in the environment (so this point should be used as the "jump-to" location). That does not hold for `recall`, right?
> [V2] Can you also change `alias_in` please? Thanks!  I am surprised that without this, jump-to-definition still works. I thought the `isBinder` annotation was responsible for that (maybe jump-to-definition uses a non-binder location as fallback?)

## pr33066_i01  [V3/docs/adopted]
**ask**: Fix the docstring for `LinearIsometryEquiv.conjStarAlgEquiv` to say “An isometric linear equivalence …” (not “An isometry linear equivalence …”).
**why** (inferred): The maintainer’s suggestion block shows the corrected English phrasing for the definition doc-comment.
**anchors**: Adjoint.lean:683  (* = inferred)
> [V3] ```suggestion /-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of ```

## pr33066_i02  [V2/duplication/partially_adopted]
**ask**: Delete the custom `ContinuousAlgEquiv.ofAlgEquiv` definition and its accompanying simp/trans/symm lemmas, and instead construct continuous algebra equivalences from an `AlgEquiv` using the existing constructor `ContinuousAlgEquiv.mk` (with `continuous_toFun`/`continuous_invFun`, defaulting to `by fun_prop` as appropriate).
**why** (stated): The maintainer notes that `ofAlgEquiv` is "just the pre-existing constructor for `ContinuousAlgEquiv`" (up to definitional equalities), so the added definition/lemmas are redundant and should be removed in favor of `ContinuousAlgEquiv.mk`.
**anchors**: Equiv.lean:302  (* = inferred)
> [V2] This is just the pre-existing constructor for `ContinuousAlgEquiv`: ``` ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]   [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra

## pr33066_i03  [V2/style/partially_adopted]
**ask**: Refactor the auxiliary section to improve style: explicitly separate `section auxiliaryDefs` with blank lines, group the `variable` binder as `variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)` (moving `hα` onto the first line), and generally improve the naming of anonymous `have` facts; additionally, state surjectivity using an explicit type ascription `Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by` without manually filling the `_`.
**why** (inferred): Maintainer requests clearer, more idiomatic Lean style: (1) let Lean infer the codomain in the surjectivity statement via an explicit type ascription instead of supplying it; (2) reorganize variable declarations to be cleaner (put `hα` up front as suggested) and add whitespace; (3) improve readability/maintainability by giving better names to intermediate `have`s and interspersing commentary through the code rather than in a block.
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V2] You can still phrase this as: ```suggestion     Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ``` and I think Lean shouldn't need you to fill in the `_`.
> [V3] This is nice, but it would be even nicer if it were interspersed throughout the code.
> [V3] ```suggestion section auxiliaryDefs  variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0) ```
> [V3] The naming of your `have`s could use some work. Please improve them.

## pr33065_i01  [V3/naming/adopted]
**ask**: Fix the docstring wording to say “accumulation point” (not “accumulated point”), and rename `ContinuousWithinAt.of_not_accPt` (and similarly `ContinuousAt.of_not_accPt`) to non-dot-style names like `continuousWithinAt_of_not_accPt` / `continuousAt_of_not_accPt` to match existing naming conventions since these lemmas don’t take a `ContinuousWithinAt` hypothesis.
**why** (stated): Maintainer suggests (1) correcting the documentation phrase to “accumulation point”, and (2) using underscore lemma names for consistency with existing lemmas (e.g. `continuousWithinAt_of_notMem_closure`) because “the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used most of the time anyway”, applying to the second lemma too.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V3] ```suggestion /-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulation point of ```
> [V3] I think it would make sense to call this `continuousWithinAt_of_not_accPt` instead to stay consistent with e.g. `continuousWithinAt_of_notMem_closure` - since the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used m

## pr33065_i02  [V4/style/dropped | NOT JUDGEABLE]
**ask**: Decide whether to restate/simplify the hypothesis `AccPt x (𝓟 {x}ᶜ)` in `ContinuousAt.of_not_accPt` as the equivalent `AccPt x ⊤` (and use the preferred form consistently).
**why** (stated): The maintainer points out an equivalence `AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤` via simp, and explicitly raises the question of which form the library should prefer, implying the code should choose one representation (potentially rewriting `ContinuousAt.of_not_accPt`’s assumption accordingly).
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V4] Note that `AccPt x (𝓟 {x}ᶜ)` is equivalently just `AccPt x ⊤`: ``` import Mathlib  open Topology Filter Set  example {α : Type*} [TopologicalSpace α] {x : α} : AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤ := by   simp [← principal_univ, accPt_principal_iff_nh

## pr33057_i01  [V1/other/adopted | NOT JUDGEABLE]
**ask**: Fix the remaining CI/error so the PR builds cleanly (maintainer delegated with “fix the last error”).
**why** (stated): The maintainer approved (bors d+) but explicitly delegated the PR back to the author to address “the last error,” indicating there is still a failing check/build error that must be resolved before merge.
**anchors**: Expand.lean:33*  (* = inferred)
> [V1] Thanks! Delegating so you can fix the last error.   bors d+

## pr33056_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide (via community/Zulip vote) whether to avoid numerals in the new identifier for ℵ₁, and if so rename the proposed `aleph1` convention to a non-numeral form such as `alephOne` (rather than proceeding with `aleph1`).
**why** (stated): Maintainer expects the naming to follow Mathlib’s general convention of not using numerals in identifiers (e.g. `cos_pi_div_two`) and suggests a Zulip vote before standardizing; they indicate they would have expected a spelling like `alephOne` instead of `aleph1`/`aleph_one`.
**anchors**:   (* = inferred)
> [V4] I think there should be a Zulip vote for this. I would have expected that we go the *other* way, potentially with `alephOne` instead of `alepha_one`. The point being that we generally don't use numerals in identifiers (cf. `cos_pi_div_two` for exampl

## pr33048_i01  [V3/scope/adopted]
**ask**: Add a new simp lemma `@[simp] theorem mk_ofNat {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0` proved by `mod_cast mk_intCast` (using `NeZero.ne n`), complementing the existing `mk_natCast` lemma which requires an explicit `n ≠ 0` hypothesis.
**why** (inferred): The maintainer notes a missing simp lemma for `mk` applied to `ofNat(n)` when `n ≥ 2` (via `[n.AtLeastTwo]`), suggesting it should be derivable from `mk_intCast` via `mod_cast`. This makes rewriting/simp work without having to pass a manual `n ≠ 0` premise.
**anchors**: Archimedean.lean:181, Archimedean.lean:174  (* = inferred)
> [V3] Just realising: we do not have  ``` @[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 :=   mod_cast mk_intCast (n := n) ``` Mind adding?

## pr33048_i02  [V2/style/partially_adopted]
**ask**: Rename the simp lemmas about `FiniteElement.mk` interacting with operations/comparisons so their names make the `mk` arguments explicit, e.g. change `mk_add`/`mk_sub`/`mk_mul` to `mk_add_mk`/`mk_sub_mk`/`mk_mul_mk` and adjust the statement style similarly; additionally, change `mk_lt_mk_iff` (and similarly `mk_le_mk_iff`) to take `hx hy` as explicit arguments (not implicit `{hx} {hy}`) to support backwards rewriting.
**why** (stated): The maintainer asks to “make those explicit for backwards rewriting” and suggests lemma names like `mk_add_mk` and an explicit-argument form `theorem mk_lt_mk_iff {x y : K} (hx hy) : ...`, indicating they want clearer lemma names and explicit hypotheses to improve rewriting/simp usability (especially rewriting in the reverse direction).
**anchors**: StandardPart.lean:91  (* = inferred)
> [V2] ```suggestion theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ``` Same below
> [V3] I would make those explicit for backwards rewriting: ```suggestion theorem mk_lt_mk_iff {x y : K} (hx hy) : ```

## pr33048_i03  [V3/naming/adopted]
**ask**: Rename `mk_le_mk_iff` to `mk_le_mk` (dropping the `_iff` suffix) while keeping the statement/proof `FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y := .rfl`.
**why** (inferred): The maintainer questions the need for the `_iff` suffix here, suggesting the lemma should be named `mk_le_mk` since it is a straightforward `↔` lemma by rfl and the shorter name is preferable.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] Do we really need the `_iff` here? ```suggestion theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :     FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=   .rfl ```

## pr33048_i04  [V3/style/adopted]
**ask**: Replace the `instance : Coe ℚ (FiniteElement K)` with an instance `instance : RatCast (FiniteElement K)` (i.e., provide rational casting via the `RatCast` typeclass rather than `Coe`).
**why** (inferred): The maintainer suggests using the standard `RatCast` typeclass for coercions from `ℚ` into `FiniteElement K`, instead of defining a bare `Coe ℚ (FiniteElement K)` instance.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] ```suggestion instance : RatCast (FiniteElement K) where ``` no?

## pr33047_i01  [V4/naming/adopted | NOT JUDGEABLE]
**ask**: Decide and justify whether the refactor should prefer the longer spelling `smulRight (1 : R →L[R] R)` (or `smulRight (.id R R)`) versus using the dedicated name `toSpanSingleton R`, and adjust the PR accordingly (potentially reverting the preference if the longer spelling is not justified).
**why** (stated): Maintainer questions the motivation for the claimed preference: "Might I ask why the longer spelling should be the preferred one?" This requests a rationale/decision about which form should be standard.
**anchors**: LinearMap.lean:325*, LinearMap.lean:345*  (* = inferred)
> [V4] Might I ask why the longer spelling should be the preferred one?

## pr31342_i01  [V3/docs/dropped | META]
**ask**: Add a description to the PR message.
**why** (stated): The maintainer explicitly asks: “Could you add a description to the PR message?” indicating the PR metadata needs a descriptive summary.
**anchors**:   (* = inferred)
> [V3] Could you add a description to the PR message?
