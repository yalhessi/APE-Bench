# Interventions review digest

113 interventions | judgeable 95 | outcomes {'adopted': 52, 'dropped': 32, 'unknown': 13, 'partially_adopted': 16}

## pr33421_i01  [V3/naming/adopted]
**ask**: Rename the theorem `round_eq'` to `round_eq_div`.
**why** (inferred): Maintainer asked “How about `round_eq_div`?”, indicating the existing lemma name `round_eq'` should be replaced with the more descriptive/conventional name `round_eq_div` for the division formula for `round`.
**anchors**: Round.lean:45  (* = inferred)
> [V3] How about `round_eq_div`?

## pr33421_i02  [V2/duplication/dropped]
**ask**: Factor out the repeated `Tendsto (2 * ·)` argument in the `tendsto_round_*` proofs into a general reusable lemma (i.e. add a lemma stating `Tendsto (k * ·) (𝓝[≥]/𝓝[<] x) (𝓝[≥]/𝓝[<] (k*x))`, and use it here instead of reproving it; same change for the next theorem).
**why** (stated): Maintainer notes the proof step is "something very general that should exist as a lemma" and says "Same in the next theorem", indicating the duplicated local `have : Tendsto (2 * ·) ...` should be replaced by a general lemma used in both theorems.
**anchors**: Floor.lean:195  (* = inferred)
> [V2] Is this not something very general that should exist as a lemma? Same in the next theorem

## pr33421_i03  [V2/generalization/adopted]
**ask**: Replace the specialized lemma `two_mul_fract_eq_one_iff_exists_int {x} : 2 * fract x = 1 ↔ ∃ n, 2 * x = 2 * n + 1` with a generalized version `mul_fract_eq_one_iff_exists_int {x} {k} (hk : 1 < k) : k * fract x = 1 ↔ ∃ n, k * x = k * n + 1`, adjusting the proof to use `hk` (derive `hk0 : 0 < k` and use `mul_le_mul_iff_right₀ hk0` / `mul_lt_mul_iff_right₀ hk0`) and simp with `[mul_add, hk]` instead of hardcoding `two_pos`.
**why** (inferred): The existing lemma hardcodes the constant factor `2`; the maintainer wants a more reusable API lemma parameterized by an arbitrary multiplier `k` (with `1 < k` to get positivity) and correspondingly a more general statement/proof rather than a `2`-specific one.
**anchors**: Ring.lean:267, Ring.lean:267  (* = inferred)
> [V2] Better I think as ```suggestion theorem mul_fract_eq_one_iff_exists_int {x : R} {k : R} (hk : 1 < k) :     k * fract x = 1 ↔ ∃ n : ℤ, k * x = k * n + 1 := by   rw [fract, mul_sub, sub_eq_iff_eq_add']   refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩   rintro ⟨

## pr33419_i01  [V3/naming/adopted]
**ask**: Rename the new lemma `eq_card_diff_of_sdiff` to `card_sub_card_eq` (keeping the statement `#t - #s = #(t \ s) - #(s \ t)`).
**why** (stated): The maintainer said they "couldn't parse the name" and provided `card_sub_card_eq` as the preferred, clearer lemma name for this statement.
**anchors**: Card.lean:574  (* = inferred)
> [V3] I couldn't parse the name you proposed. ```suggestion lemma card_sub_card_eq (s t : Finset α) : #t - #s = #(t \ s) - #(s \ t) := ```

## pr33413_i01  [V2/style/dropped]
**ask**: Optionally replace the pair of manually written deprecated aliases for the `to_dual`-generated lemmas with a single use of the `to_dual` attribute that generates both deprecated aliases at once (if compatible with automated deprecated-declaration removal).
**why** (stated): Maintainer notes you can use `to_dual` to generate both deprecated aliases simultaneously, instead of writing separate deprecated alias declarations; they’re unsure if the automated removal tooling works with this approach.
**anchors**:   (* = inferred)
> [V2] Thanks :tada:  maintainer merge  (You can also use the `to_dual` attribute to generate both deprecated aliases at once, if you want, but I don't know if the automated removal of deprecated declarations works with that)

## pr33401_i01  [V2/style/adopted]
**ask**: Rewrite the proof of `closure_pow_le` to use the suggested compact tactics: replace the `0` case proof with `by simp_all`, and replace the `n+1` case `calc` chain with `by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem]`.
**why** (inferred): The maintainer proposes simplifying the pattern-match branches by using `simp_all` for the base case and `grw` with the relevant lemmas instead of an explicit `calc` proof, making the proof shorter and more idiomatic.
**anchors**: Pointwise.lean:223, Pointwise.lean:223  (* = inferred)
> [V2] ```suggestion   | 0 => by simp_all ```
> [V2] ```suggestion   | n + 1 => by grw [pow_succ, closure_mul_le, closure_pow_le, sup_idem] ``` instead of the `calc ...`

## pr33400_i01  [V3/naming/dropped]
**ask**: Rename the theorem `smooth` to `contDiff` (i.e., use the `contDiff` name for the lemma stating every Schwartz function is `ContDiff`).
**why** (inferred): Maintainer comment: "I think we should also rename this to `contDiff`", referring to the lemma currently named `smooth` whose statement is `ContDiff ℝ n f`. In Mathlib, lemmas about `ContDiff` are conventionally named `contDiff` rather than `smooth`.
**anchors**:   (* = inferred)
> [V3] pre-existing: I think we should also rename this to `contDiff`

## pr33395_i01  [V4/naming/adopted]
**ask**: Rename the theorem `IntrinsicStar.starLinearEquiv_eq` to `IntrinsicStar.starLinearEquiv_eq_arrowCongr`.
**why** (stated): The maintainer prefers a more descriptive name indicating that the RHS is `arrowCongr`, and notes that without this verbosity it would be hard to guess the statement’s RHS from the name alone.
**anchors**: LinearMap.lean:126  (* = inferred)
> [V4] I like this the best. It's verbose, but I would have trouble guessing what you were going to write on the other side of `eq` without this. ```suggestion theorem IntrinsicStar.starLinearEquiv_eq_arrowCongr : ```

## pr33376_i01  [V2/scope/unknown]
**ask**: Decide whether to keep or remove the newly introduced lemma `rayleighQuotient_add` (it appears unused for the PR’s stated goal); either demonstrate its use in the PR or drop it from the diff.
**why** (inferred): Maintainer questions adding the lemma because it seems unrelated to the PR’s purpose: “This is a reasonable lemma, but you're not using it for this PR, right?”—implying it shouldn’t be introduced as extra API unless it is actually needed.
**anchors**:   (* = inferred)
> [V2] This is a reasonable lemma, but you're not using it for this PR, right?

## pr33373_i01  [V2/duplication/partially_adopted]
**ask**: Refactor `iteratedDeriv_comp_sub_const` to reuse the existing shift lemma by rewriting subtraction as addition of a negated constant and proving it via `simp [sub_eq_add_neg, iteratedDeriv_comp_add_const]` instead of a fresh induction/`deriv_comp_sub_const` proof.
**why** (inferred): The maintainer explicitly suggests proving the new `..._sub_const` lemma by rewriting `z - s` as `z + (-s)` and then applying the already-proved `iteratedDeriv_comp_add_const`, to avoid duplicating an inductive proof and to better reuse existing theorems.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simp [sub_eq_add_neg, iteratedDeriv_comp_add_const] ```
> [V2] Let's reuse the existing theorems:

## pr33373_i02  [V2/duplication/unknown]
**ask**: Replace the inductive proof of `iteratedDeriv_comp_const_sub` with a proof that reuses existing lemmas, specifically deriving it via `iteratedDeriv_comp_neg n (fun z => f (z + s))` and finishing by `simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const]` (i.e. avoid reproving it from scratch).
**why** (stated): The maintainer explicitly asks to “reuse the existing theorems” and provides a concrete proof sketch using `iteratedDeriv_comp_neg` together with `iteratedDeriv_comp_add_const` and simp rewrites, indicating the current from-scratch/induction approach should be replaced by this reuse-based proof.
**anchors**: Lemmas.lean:217, Lemmas.lean:217  (* = inferred)
> [V2] ```suggestion   simpa [funext_iff, neg_add_eq_sub, iteratedDeriv_comp_add_const] using     iteratedDeriv_comp_neg n (fun z => f (z + s)) ```
> [V2] Let's reuse the existing theorems:

## pr33362_i01  [V3/scope/adopted]
**ask**: Move the relevant declarations a few lines down so they are inside the `namespace Complex` (i.e. put `namespace Complex` before the lemmas so they live in the `Complex` namespace).
**why** (stated): The maintainer asks: "Why not move these a few lines below so that it's on the `Complex` namespace?"—i.e. ensure the new/edited lemma(s) are scoped under `Complex` rather than being at top level / using prefixed names.
**anchors**: Schwarz.lean:40, Schwarz.lean:40  (* = inferred)
> [V3] Why not move these a few lines below so that it's on the `Complex` namespace?

## pr33357_i01  [V3/docs/unknown | META]
**ask**: Fix the typo in the PR description.
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): Maintainer explicitly notes “there's a typo in your PR desc”, requesting a correction to the PR metadata text.
**anchors**:   (* = inferred)
> [V3] (there's a typo in your PR desc)

## pr33356_i01  [V2/style/adopted]
**ask**: Refactor the proof of `hasDetPlusMinusOne_iff_abs_det` to use `refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩`, i.e. express the forward direction via `h.abs_det` and set up the reverse direction by constructing `HasDetPlusMinusOne` with a placeholder goal.
**why** (inferred): The maintainer suggests a cleaner structured `refine ⟨..., ...⟩` proof that uses the existing lemma `abs_det` for the forward implication and sets up the backward implication via `⟨?_⟩`, likely for readability and leveraging existing API instead of more manual term/proof structure.
**anchors**: ArithmeticSubgroups.lean:43  (* = inferred)
> [V2] ```suggestion   refine ⟨fun h {g} hg ↦ h.abs_det hg, fun h ↦ ⟨?_⟩⟩ ```

## pr33349_i01  [V4/other/dropped | NOT JUDGEABLE]
**ask**: Resolve the lack of consensus on the proposed change (i.e., do not proceed without maintainer agreement / clarify and obtain consensus before making the style/indentation adjustment in the class declaration).
**why** (stated): The maintainer states: "I don't think there is consensus here?" indicating the change is contentious or not agreed upon and should not be merged/changed as-is without agreement.
**anchors**: AddGroupWithTop.lean:41  (* = inferred)
> [V4] I don't think there is consensus here?

## pr33349_i02  [V2/style/unknown]
**ask**: Reorder and rename the new `add_(le/lt)_add_iff_(left/right)_of_ne_top` lemmas to follow the usual Mathlib convention: give `[simp]` lemmas in the order `add_le_add_iff_left_of_ne_top`, `add_le_add_iff_right_of_ne_top`, `add_lt_add_iff_left_of_ne_top`, `add_lt_add_iff_right_of_ne_top`, each stated with argument order `{a b c} (h : a ≠ ⊤)` and proved via `(add_left_strictMono_of_ne_top _ h).le_iff_le` / `.lt_iff_lt` (and similarly for `add_right_strictMono_of_ne_top`).
**why** (stated): The maintainer indicates that the suggested lemma order is "the more usual order" (and "Same here" for the analogous group), i.e. align lemma ordering/structure with established Mathlib style conventions for `*_iff_left` before `*_iff_right` and `≤` before `<`, with simp tags.
**anchors**: AddGroupWithTop.lean:140  (* = inferred)
> [V2] ```suggestion @[simp] lemma add_le_add_iff_left_of_ne_top {a b c : α} (h : a ≠ ⊤) : b + a ≤ c + a ↔ b ≤ c :=   (add_left_strictMono_of_ne_top _ h).le_iff_le  @[simp] lemma add_le_add_iff_right_of_ne_top {a b c : α} (h : a ≠ ⊤) : a + b ≤ a + c ↔
> [V2] Same here

## pr33345_i01  [V3/docs/adopted]
**ask**: Fix the typo in the docstring by changing `Multipilication in `R` transfers to Addition in `ArchimedeanClass R`.` to `Multiplication in `R` transfers to Addition in `ArchimedeanClass R`.`.
**why** (stated): Maintainer points out it’s probably a good idea to fix this simultaneously, and provides the corrected docstring text.
**anchors**: Archimedean.lean:72  (* = inferred)
> [V3] Probabily a good idea to fix that simultaneousily ```suggestion /-- Multiplication in `R` transfers to Addition in `ArchimedeanClass R`. -/ ```

## pr33343_i01  [V3/style/adopted]
**ask**: In the `stdPart_nonneg` proof, replace the `apply ...; assumption` tail with an explicit `exact` proof term (e.g. `exact map_nonneg _ h`) rather than relying on `assumption`.
**why** (inferred): The maintainer prefers being explicit when closing goals, especially when the expression is not syntactically identical to an available hypothesis; use `exact h`/an explicit term instead of `assumption`.
**anchors**: StandardPart.lean:402, StandardPart.lean:402  (* = inferred)
> [V3] ```suggestion     exact h ``` I think it is better to be explicit here, especially when it is not syntactically eq

## pr33337_i01  [V3/naming/adopted]
**ask**: Rename the lemma `orthogonalProjection_coe_eq_linearProjOfIsCompl` to `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl` (using the `toLinearMap_...` naming convention for equalities about the `E →ₗ[𝕜] K` coercion of `K.orthogonalProjection`).
**why** (inferred): The maintainer suggested the theorem name `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`, indicating the lemma should be named to reflect it is an equality about the `toLinearMap`/linear-map coercion of `orthogonalProjection`, rather than using `coe_...` or the previous name.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] : ```

## pr33337_i02  [V3/naming/adopted]
**ask**: Rename the lemma `coe_starProjection_eq_isComplProjection` (and similarly `coe_orthogonalProjection_eq_linearProjOfIsCompl`) to use the `toLinearMap_...` prefix, i.e. change it to `toLinearMap_starProjection_eq_isComplProjection` (and `toLinearMap_orthogonalProjection_eq_linearProjOfIsCompl`) to reflect that the statement is about `.toLinearMap`.
**why** (inferred): The maintainer explicitly suggests the lemma header `theorem toLinearMap_starProjection_eq_isComplProjection ...`, indicating the name should match the field `.toLinearMap` rather than using `coe_...`.
**anchors**: Submodule.lean:191  (* = inferred)
> [V3] ```suggestion theorem toLinearMap_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] : ```

## pr33333_i01  [V4/proof-golf/dropped]
**ask**: Rewrite `floor_pi_eq_three` to use `rw [Int.floor_eq_iff]` followed by `grind [pi_gt_three, pi_lt_four]` instead of the manual `refine ...; norm_num; exact ...` proof.
**why** (inferred): Maintainer suggests a shorter/more idiomatic proof style for the floor lemma: unfold `Int.floor_eq_iff` by rewriting and let `grind` solve the inequality goals from the existing bounds `pi_gt_three` and `pi_lt_four`.
**anchors**: Bounds.lean:223, Bounds.lean:223  (* = inferred)
> [V4] Thanks! I'm not sure if I prefer those, though (same with the other). I'll wait for another opinion.
> [V4] I don't have a strong preference. But would this be a middle ground? ```suggestion theorem floor_pi_eq_three : ⌊π⌋ = 3 := by   rw [Int.floor_eq_iff]   grind [pi_gt_three, pi_lt_four] ```

## pr33333_i02  [V2/scope/unknown | NOT JUDGEABLE]
**ask**: Remove or avoid adding any `exp 1`-bounds work to this PR; if you want bounds for `exp 1`, use the existing results in `Mathlib.Analysis.Complex.ExponentialBounds` (e.g. move that discussion/implementation there or reference that file instead).
**why** (stated): The maintainer notes that bounds for `exp 1` already exist elsewhere ("Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`"), implying this PR should not duplicate or expand into `exp 1` bounds in the π-bounds file/PR.
**anchors**: Bounds.lean:223*  (* = inferred)
> [V2] Bounds for `exp 1` are in `Mathlib.Analysis.Complex.ExponentialBounds`.

## pr33332_i01  [V1/style/partially_adopted]
**ask**: In the `adj_of_mem_walk_support` match/recursion over the walk, change the cons-case binder list from `| @cons u v w h p ih =>` to `| cons h p ih =>` (drop the unused explicit names `u v w` and the `@`).
**why** (stated): The reviewer notes that the names `u v w` are no longer used in the cons branch, so the pattern should be simplified to avoid unused binders.
**anchors**: Connected.lean:252  (* = inferred)
> [V1] The names aren't used anymore ```suggestion   | cons h p ih => ```

## pr33328_i01  [V4/style/partially_adopted]
**ask**: Replace the new `↦` lambda syntax with the older `=>` syntax in the refactored proof of `Ici_subset_Ici` (and the analogous simp lemma at line ~316), i.e. change `fun h ↦ ...` back to `fun h => ...` while keeping the other refactorings (like `self_mem_Ici`).
**why** (inferred): The revision shows the maintainer wanted a style adjustment in the proof term: avoid introducing `↦` and instead use the conventional `=>` lambda syntax in this file’s simp-lemma proofs.
**anchors**: Basic.lean:288, Basic.lean:316*  (* = inferred)
> [V4] Why this style change here and not in the other analogous places? (I'm neutral to the style changes, maybe they can be left to another PR)

## pr33321_i01  [V3/docs/adopted]
**ask**: Complete/fix the docstring for `IsMulIndecomposable.baseOf` so that the sentence “In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the …” is finished (and correct any typo such as “crystallogrphic”).
**why** (inferred): The maintainer points out an unfinished documentation sentence in the `to_additive` doc comment for `baseOf` (“In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ...”), indicating it should be completed/clarified.
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] ```suggestion In the case that `v` is the set of roots of a crystallographic root system, and `S = ℚ`, this is the ```

## pr33321_i02  [V3/style/dropped]
**ask**: Redefine `IsMulIndecomposable.baseOf` as a set comprehension `{j | IsMulIndecomposable v {i | 1 < f (v i)} j}` rather than using the predicate `IsMulIndecomposable v {i | 1 < f (v i)}` directly as a `Set ι` via definitional equality between predicates and sets.
**why** (stated): The maintainer flags that the original definition relies on the (defeq/coercion) identification of predicates with sets, and asks to make the set nature explicit to avoid "abusing the defeq between predicates and sets".
**anchors**: Indecomposable.lean:31  (* = inferred)
> [V3] Isn't this abusing the defeq between predicates and sets? ```suggestion def IsMulIndecomposable.baseOf [Monoid S] (v : ι → M) (f : M →* S) : Set ι :=   {j | IsMulIndecomposable v {i | 1 < f (v i)} j} ```

## pr33321_i03  [V3/docs/dropped]
**ask**: Revise the module-level documentation to explicitly account for the need for an ordered coefficient set in the proof (despite the final existence statement not needing it), by adding an “Implementation details” discussion outlining the approach taken to handle ordered coefficients.
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): The maintainer flags a mismatch between proof requirements (needs ordered coefficients) and the theorem statement (does not), and wants the file’s documentation to address this design choice explicitly.
**anchors**: BaseExists.lean:1  (* = inferred)
> [V3] ```suggestion The proof needs a set of ordered coefficients, even though the ultimate existence statement does ```

## pr33316_i01  [V3/naming/dropped]
**ask**: Reconsider the new non-ASCII declaration name `innerₛₗ` (and related naming) in favor of a more readable ASCII name (keeping de-duplication but avoiding introducing non-ASCII identifiers for this API).
**why** (stated): Maintainer says the duplication removal is fine but prefers the other name as more readable, and notes that using non-ASCII characters in declarations is generally discouraged.
**anchors**: Basic.lean:120*  (* = inferred)
> [V3] Getting rid of the duplication is fine, but the other name comes off as more readable to me. I thought using non-ASCII characters in declarations was generally discouraged.

## pr33310_i01  [V2/style/adopted]
**ask**: Refactor `quotientPEquiv` to avoid constructing the ring isomorphism via tactics and rewriting `Ideal.span {p}` into a kernel: instead, (1) add a lemma `ker_constantCoeff : RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)}` (with `ker` on the LHS), (2) add a surjectivity lemma `constantCoeff_surjective`, (3) define `quotientPEquiv` as `(Ideal.quotEquivOfEq ker_constantCoeff.symm).trans (RingHom.quotientKerEquivOfSurjective constantCoeff_surjective)`, and (4) add a simp lemma `quotientPEquiv_mk` stating the map on `Quot.mk` is `constantCoeff`.
**why** (stated): The maintainer notes that creating data (the isomorphism) using tactics is problematic for unfolding; using `Ideal.quotEquivOfEq` yields a definitional computation rule so that `quotientPEquiv_mk` can be proved by `rfl`, which would not work with the tactic-built definition. They also prefer keeping `RingHom.ker` on the LHS of `ker_constantCoeff` since the RHS is more basic.
**anchors**: Complete.lean:95, Complete.lean:95  (* = inferred)
> [V2] It would be useful to introduce auxiliary lemmas: ```lean lemma ker_constantCoeff :     RingHom.ker constantCoeff = Ideal.span {(p : 𝕎 k)} := by   ext   simp [mem_span_p_iff_coeff_zero_eq_zero]  -- this should be moved to the `Teichmuller` file lemma
> [V3] It seems more logical to me to keep `ker` in the LHS, as arguably the RHS is a "more basic term" as compared to the LHS.

## pr33305_i01  [V1/style/adopted]
**ask**: Wrap/split the overly long doc comment line in `Mathlib/GroupTheory/Submonoid/Inverses.lean` (around line 20) so it respects the project's maximum line length.
**why** (stated): The CI style/lint check reports "There's a line that's too long" for this PR; the maintainer is blocking merge until the long line is broken into shorter lines.
**anchors**: Inverses.lean:20*, Inverses.lean:20*  (* = inferred)
> [V1] bors r- bors d+  There's a line that's too long: https://github.com/leanprover-community/mathlib4/actions/runs/20522522089/job/58960134164?pr=33305#step:22:36

## pr33302_i01  [V2/style/adopted]
**ask**: Change `ShiftedHom` from a `def` to an `abbrev`, and consequently remove the `AddCommGroup` and `Module` instances currently defined on `ShiftedHom` (fixing any ensuing proof breaks, which should mostly become simpler via `dsimp` rather than needing explicit `erw [Iso.homToEquiv_apply]`).
**why** (stated): The maintainer reports having tried making `ShiftedHom` an `abbrev` and found it improves automation; with an `abbrev`, the additive/module structure should come from the underlying type so the explicit `AddCommGroup`/`Module` instances become unnecessary, and some manual rewriting steps should no longer be needed because definitional unfolding via `dsimp` will handle them.
**anchors**: ShiftedHom.lean:13*, ShiftedHom.lean:29*, ShiftedHom.lean:184*  (* = inferred)
> [V2] Could you also make `ShiftedHom` an abbrev instead of a `def`. Then, the `AddCommGroup` and `Module` instances on this type could be removed. I have tried this, and overall, it improves automation. A few proofs should break, but the fix should be eas

## pr33296_i01  [V2/generalization/dropped]
**ask**: Replace the lemma `Module.End.exists_apply_eq_smul` (which assumes `hf : f ∈ Subsemiring.center (End R M)`) with a more general “mem_center_iff” characterization for `Set.center (End R M)` and then derive specialized iff-lemmas for `Submonoid.center`, `Subsemigroup.center`, `Subsemiring.center`, and `Subalgebra.center`; additionally, strengthen `Mathlib/Algebra/Central/End.lean`’s imports by adding `Mathlib.Algebra.Central.Basic`.
**why** (stated): The maintainer provides “a cleaner proof” and explicitly asks for a “generalization for the instance”; their sketch introduces `Module.End.mem_center_iff` plus wrappers for the various `center` notions, and notes an import fix: “need to strengthen the import to `Mathlib.Algebra.Central.Basic` in the `Mathlib/Algebra/Central/End` file.”
**anchors**:   (* = inferred)
> [V2] I was just about to make this PR lol. Here is a cleaner proof. Along with a golf and a generalization for the instance. I can still make this PR, or you can just apply this, whatever :)  Note that you need to strengthen the import to `Mathlib.Algeb

## pr33294_i01  [V3/naming/adopted]
**ask**: Rename the theorem `isFundamentalSequence_of_isNormal` to use dot-notation as `isFundamentalSequence.of_isNormal` (i.e. make it an `IsFundamentalSequence.of_isNormal` theorem rather than a standalone `*_of_*` name).
**why** (inferred): The maintainer suggests a dot-style name `... .of_isNormal` for this construction lemma, following Mathlib naming conventions for lemmas that build an `IsFundamentalSequence` from an `IsNormal` hypothesis.
**anchors**: Cofinality.lean:532  (* = inferred)
> [V3] ```suggestion theorem isFundamentalSequence.of_isNormal {f : Ordinal.{u} → Ordinal.{u}} (hf : IsNormal f) ```

## pr33294_i02  [V2/style/adopted]
**ask**: Replace the rewrite `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]` with the method call `rw [h.map_iSup (bddAbove_of_small _)]`.
**why** (inferred): Use the dot-notation lemma `map_iSup` directly from the `Order.IsNormal` hypothesis `h` rather than referencing it via the namespace `Order.IsNormal`; the suggestion is explicitly `rw [h.map_iSup (bddAbove_of_small _)]`.
**anchors**: Topology.lean:178  (* = inferred)
> [V2] ```suggestion     rw [h.map_iSup (bddAbove_of_small _)] ``` no? 

## pr33287_i01  [V2/style/partially_adopted]
**ask**: (1) In the `Arrows.toCompatible` definition, replace the `property` proof body `dsimp; simp only [← FunctorToTypes.map_comp_apply, ← op_comp, h]` with `simp [← FunctorToTypes.map_comp_apply, ← op_comp, h]`. (2) In the lemma/proof about sheafness for presieves in an over-category, state the goal as `IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by` (i.e. explicitly use `Presieve.ofArrows` with the mapped arrows) instead of the current formulation.
**why** (inferred): (1) Use `simp` (not `simp only` plus a separate `dsimp`) to simplify the compatibility condition proof more idiomatically while still using the same rewrite lemmas. (2) Make the `IsSheafFor` statement refer to the concrete presieve built from the family of arrows after applying `(Over.map p).map`, clarifying the intended presieve and aligning the proof with the `ofArrows`-style sheaf condition setup.
**anchors**: IsSheafFor.lean:799  (* = inferred)
> [V2] ```suggestion   property i j Z gi gj h := by     simp [← FunctorToTypes.map_comp_apply, ← op_comp, h] ```
> [V2] ```suggestion       IsSheafFor P (Presieve.ofArrows _ (fun i ↦ (Over.map p).map (f i))) := by ```

## pr33285_i01  [V2/proof-golf/partially_adopted]
**ask**: Golf the proof of `comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q` to a direct lambda, i.e. replace the tactic-style `rw/intros/change/apply` (or `simp`-tactic block) with `fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2`.
**why** (stated): Maintainer proposes an "even better golf": express the `≤` proof as a function and use `mem_comap.mpr` plus `add_mem` directly, avoiding the more verbose `rw [SetLike.le_def]`/`intro`/`simp` proof.
**anchors**: Map.lean:595, Map.lean:597  (* = inferred)
> [V2] here's an even better golf ```suggestion     comap f₁ q ⊓ comap f₂ q ≤ comap (f₁ + f₂) q :=   fun _ h ↦ mem_comap.mpr <| add_mem h.1 h.2 ```

## pr33285_i02  [V2/proof-golf/adopted]
**ask**: In `cotangentEquivIdeal_symm_apply`, replace the manual injectivity/`ext`/`rfl` proof tail with a single `simp`-based proof, e.g. `simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff]` (alternatively using `exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _)`).
**why** (inferred): The maintainer suggests proof-golfing: instead of applying injectivity and then doing `ext; rfl`, use `simp` with the appropriate lemma (`symm_apply_eq`) and extensionality lemma (`Subtype.ext_iff`) to close the goal more idiomatically and concisely.
**anchors**: Cotangent.lean:151, Cotangent.lean:151  (* = inferred)
> [V2] or ```lean   simp [I.cotangentEquivIdeal.symm_apply_eq, Subtype.ext_iff] ``` or ```lean   exact I.cotangentEquivIdeal.injective (I.cotangentEquivIdeal.apply_symm_apply _) ```

## pr33283_i01  [V3/style/dropped]
**ask**: Rewrite the `linear_combination` call so that the lemma argument `h` is on the same line as the tactic invocation: `linear_combination (norm := (push_cast; ring_nf)) h` (rather than splitting after the norm and putting `h` on the next line).
**why** (stated): The maintainer suggests this formatting to avoid the “weird” line break, and indicates the same applies to other similar occurrences.
**anchors**: Chebyshev.lean:807, Chebyshev.lean:807  (* = inferred)
> [V3] ```suggestion   linear_combination (norm := (push_cast; ring_nf)) h ``` I personally find this line break a bit weird but if you are attached to this style I don't particular want to block this PR because of it.
> [V3] (and the other ones)

## pr33268_i01  [V3/style/unknown]
**ask**: Reorder the `max_left` and `max_right` lemmas so they appear adjacent (right after each other) in the file.
**why** (stated): Maintainer requests a “more natural ordering” by placing the paired lemmas `max_left` and `max_right` next to each other.
**anchors**: Lattice.lean:26  (* = inferred)
> [V3] I think a more natural ordering is to put the max_left and max_right lemmas right after eachother.

## pr33267_i01  [V2/naming/dropped | NOT JUDGEABLE]
**ask**: Use the standard dualization lemmas/names instead of applying an unrelated theorem: replace the proof step using that theorem by `toDual_symm`, and rename/replace the lemma to be `toDual_bot` where appropriate.
**why** (stated): Maintainer notes the current approach is unnecessary: “this theorem should not be applied; it can just be `toDual_symm`” and similarly suggests the lemma name should be `toDual_bot`, aligning with the `toDual`/`ofDual` machinery and naming conventions.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] I feel like this theorem should not be applied; it can just be `toDual_symm`. But that is outside the scope of this PR.
> [V3] And this could just be called `toDual_bot`.

## pr33267_i02  [V3/style/unknown]
**ask**: Remove the `WithBot.` qualifier when referencing names in the `WithBot` namespace, since the `WithBot` namespace is already open.
**why** (inferred): The maintainer notes that because `WithBot` is an open namespace here, writing `WithBot.` prefixes is redundant and should be avoided for style/readability.
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] Since the WithBot namespace is open, you can avoid the `WithBot.`

## pr33267_i03  [V3/style/unknown]
**ask**: Adjust formatting/indentation so that when a declaration’s statement fits on a single line, it is kept on one line (avoid splitting/extra indentation).
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): Maintainer preference: “indentation where the whole statement fits … one line is actually preferred.”
**anchors**: WithBot.lean:872  (* = inferred)
> [V3] I think the indentation where the whole statement fits one  one line is actually preferred.

## pr33267_i04  [V2/docs/partially_adopted]
**ask**: In the docstrings for the `WithBot.toDual`/`WithBot.ofDual` equivalences, update the referenced related order-iso names from `WithBot.toDual_top_equiv`/`WithBot.ofDual_top_equiv` to `WithBot.toDualTopEquiv`/`WithBot.ofDualTopEquiv`.
**why** (inferred): The maintainer notes the related lemma was renamed (“Looks like this was renamed at some point”) and points to the current docs entry `WithBot.toDualTopEquiv`, so the documentation references should use the updated names.
**anchors**: WithBot.lean:872  (* = inferred)
> [V2] ```suggestion See `WithBot.toDualTopEquiv` for the related order-iso. -/ ``` Looks like this was renamed at some point: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Order/Hom/WithTopBot.html#WithBot.toDualTopEquiv

## pr33232_i01  [V3/style/partially_adopted]
**ask**: Rewrite `fourierTransformInv_toTemperedDistributionCLM_eq` so the `calc` begins on the same line as the theorem statement (`:= calc`) and uses leading/trailing `_` placeholders for the initial and final expressions, matching the suggested formatting.
**why** (stated): Maintainer flagged a style nit: prefer the `:= calc` layout with `_` placeholders at the start/end of the calculation chain (and noted they didn't test elaboration but expected it to work).
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] style nit. I didn't actually test that it still elaborates properly with the starting and ending `_`, but I don't see which it shouldn't. ```suggestion     𝓕⁻ (f : 𝓢'(E, F)) = 𝓕⁻ f := calc   _ = 𝓕⁻ (toTemperedDistributionCLM E F volume (𝓕 (𝓕⁻ f))) :=

## pr33232_i02  [V3/docs/adopted]
**ask**: Add a docstring to `fourierTransformInv_toTemperedDistributionCLM_eq` stating that the distributional inverse Fourier transform coincides with the classical inverse Fourier transform on Schwartz space (replace the bare theorem statement with one preceded by `/-- ... -/`).
**why** (inferred): The maintainer supplied the exact intended documentation comment: “The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`.”, indicating the theorem should be documented accordingly (and aligned with the preceding lemma’s style).
**anchors**: TemperedDistribution.lean:241, TemperedDistribution.lean:241  (* = inferred)
> [V3] ```suggestion /-- The distributional inverse Fourier transform and the classical inverse Fourier transform coincide on `𝓢(ℝ, F)`. -/ theorem fourierTransformInv_toTemperedDistributionCLM_eq (f : 𝓢(E, F)) : ```

## pr33208_i01  [V2/docs/dropped]
**ask**: Change `IsMulIndecomposable_id_univ` to take `{x : M}` as an implicit argument (and correspondingly use `hx : x ≠ 1`), and improve documentation by replacing/expanding the docstring for `Submonoid.closure_image_one_lt_and_isMulIndecomposable` to include a clearer explanatory paragraph of the statement; additionally, add a docstring for the additive `to_additive` version.
**why** (stated): The maintainer found the existing statement hard to parse and requested a more informative docstring explaining the lemma’s meaning; they also suggested adjusting the lemma signature to use an implicit `{x : M}`. They note that the additive version is missing its own docstring.
**anchors**: Indecomposable.lean:1  (* = inferred)
> [V2] ```suggestion lemma isMulIndecomposable_id_univ [Subsingleton Mˣ] {x : M} (hx : x ≠ 1) : ```
> [V3] I found the statement a bit hard to parse, so I found myself wanting a more informative docstring. Please check that my interpretation is correct, or otherwise improve it.  ```suggestion /-- This is [serre1965](Ch. V, §9, Lemma 2) and may be used to 

## pr33207_i01  [V4/scope/adopted | NOT JUDGEABLE]
**ask**: Connect the new `argmin` material to the existing `Minimal`/`MinimalFor` API (and optionally also to `List.argmin`).
**why** (stated): Maintainer asks that it "would be nice to connect the material here to the `Minimal`/`MinimalFor` API" so users can relate this new definition/lemmas to the established minimality framework; they also mention possibly connecting to `List.argmin`, but deem it less important.
**anchors**: Argmin.lean:1  (* = inferred)
> [V4] Is it definitely easier to use this definition rather than using choice/`obtain` on `Set.Finite.exists_minimal`?   It would be nice to connect the material here to the `Minimal`/`MinimalFor` API (the latter of which isn't quite complete at the mome

## pr33203_i01  [V3/naming/adopted]
**ask**: Rename/retitle `Rat.intEquiv` (and/or adjust its naming/docs) so it no longer misleadingly suggests an equivalence `ℚ ≃ ℤ`, but instead reflects that it is an isomorphism between an integral closure of `ℤ` in `ℚ` and `ℤ` (e.g. by moving it under `Rat.IsIntegralClosure` and updating the docstring accordingly).
**why** (stated): The maintainer remarks that a name like `Rat.intEquiv` is unexpected because they would read it as a bijection `ℚ ≃ ℤ`; the definition actually produces an isomorphism `R ≃+* ℤ` for suitable `R`, so the API should be named/documented to match that meaning.
**anchors**: HeightOneSpectrum.lean:62, HeightOneSpectrum.lean:70  (* = inferred)
> [V3] I'd just like to mention that this is not at all what I'd expect from something called `Rat.intEquiv`! I was expecting some sort of bijection `ℚ ≃ ℤ` instead.

## pr33201_i01  [V2/duplication/adopted]
**ask**: Replace the specialized proofs that `X.HomotopyCategory` has subsingleton homs and is terminal with the standard library route: set up `Unique (OneTruncation₂ X)` and `Subsingleton (x ⟶ y)` in `OneTruncation₂ X` (via `X.Edge`), then obtain `Subsingleton (x ⟶ y)` by `CategoryTheory.Quotient.instSubsingletonHom`; add `Unique X.HomotopyCategory` via `CategoryTheory.Quotient.instUnique`; and define `isTerminal` using `letI : IsDiscrete (X.HomotopyCategory) := { eq_of_hom := by subsingleton }` followed by `Cat.isTerminalOfUniqueOfIsDiscrete` (instead of `IsTerminal.ofUniqueHom` / ad hoc arguments).
**why** (stated): The maintainer says the existing proof is "too specialized for the homotopy category" and that Mathlib already has the relevant general instances for quotient categories and discrete/unique categories, so the proof should be the "morally correct" one by reusing those instances and `Cat.isTerminalOfUniqueOfIsDiscrete`.
**anchors**: HomotopyCat.lean:455, HomotopyCat.lean:455  (* = inferred)
> [V2] I feel like this proof is too specialized for the homotopy category. Mathlib arleady knows that quotient categories of categories with unique objects and subsingleton homs have subsingleton homs, and that free categories on quivers with unique object
> [V2] Same here: we already have `Cat.isTerminalOfUniqueOfIsDiscrete`: ```suggestion instance (X : Truncated.{u} 2) [Unique (X _⦋0⦌₂)] : Unique X.HomotopyCategory :=    letI : Unique (OneTruncation₂ X) := inferInstanceAs (Unique (X _⦋0⦌₂))   CategoryTh

## pr33201_i02  [V2/duplication/dropped]
**ask**: Remove the new `Monoidal` instance for `((Functor.whiskeringLeft J J' C).obj F)` in `Monoidal/Cartesian/FunctorCategory.lean` and use the existing `CategoryTheory.Functor.Monoidal.whiskeringLeft` construction instead (i.e. replace this duplicate, less general implementation by the library lemma/instance).
**why** (stated): The maintainer notes the added code "seems to be a (less general) duplicate of `CategoryTheory.Functor.Monoidal.whiskeringLeft`", so they want to avoid reintroducing an overlapping/duplicated instance and rely on the more general existing one in Mathlib.
**anchors**: FunctorCategory.lean:192  (* = inferred)
> [V2] This seems to be a (less general) duplicate of [CategoryTheory.Functor.Monoidal.whiskeringLeft](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/Monoidal/FunctorCategory.html#CategoryTheory.Functor.Monoidal.whiskeringLeft)

## pr33201_i03  [V3/style/adopted]
**ask**: After introducing `FullyFaithful` defs for the currying functors (`curry` and `curry₃`), also add the corresponding typeclass instances `Full` and `Faithful` (and likewise ensure `uncurry₃` has `Full`/`Faithful` instances) derived from those `FullyFaithful` proofs.
**why** (inferred): The maintainer explicitly requests adding `Full` and `Faithful` instances alongside the new `FullyFaithful` definitions so downstream code can use automation/typeclass search for `Full`/`Faithful` without manually projecting from `FullyFaithful` each time.
**anchors**: Currying.lean:110, Currying.lean:110, CurryingThree.lean:43, CurryingThree.lean:43  (* = inferred)
> [V3] Please add the corresponding `Full` and `Faithful` instances (we really need a way to automate adding those via an attribute we can put on a `FullyFaithful` definition!).
> [V3] Same  comment: please also add the `Full` and `Faithful` instances

## pr33200_i01  [V1/other/unknown | NOT JUDGEABLE]
**ask**: Do not merge this PR as-is: remove the introduced axioms and all `sorry`s (i.e. supply full proofs) and drastically reduce/split the contribution into reviewable pieces written in Mathlib style; otherwise close/withdraw the PR.
**why** (stated): Maintainers state the PR is "completely unsuitable" because it is "far too long to review" and it "has axioms" and "has sorries" and was "written by an AI" without understanding Mathlib code style. A second maintainer notes the PR introduced many axioms ("4 times as many axioms as we use in all of Mathlib"). These are presented as independently sufficient reasons to close the PR.
**anchors**:   (* = inferred)
> [V1] The issue is nothing to do with the code of conduct. This PR is completely unsuitable for mathlib for multiple reasons. (a) it is far too long to review (b) it has axioms (c) it has sorries (d) it was written by an AI which seems to have no understan
> [V1] > no axioms  I encourage you to learn how to use `grep`, as you have in one file introduced 4 times as many axioms as we use in *all* of Mathlib.  I won't be engaging further and wasting my time.

## pr33198_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Standardize the naming scheme so that if you rename `ω₁`/`ℵ₁` to `omega_one`/`aleph_one`, you should also rename `omega0`/`aleph0` to `omega_zero`/`aleph_zero` (i.e. use `_zero`/`_one` consistently rather than mixing digit-suffixed and word-suffixed forms).
**why** (stated): The maintainer objects to mixing styles ("`omega0` and `aleph0` and also `omega_one` and `aleph_one`"), and expects community preference would favor the word-based `omega_zero`/`aleph_zero` as well, for consistency.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] I'm confused, you want to write `omega0` and `aleph0` and also `omega_one` and `alepg_one`? I'm virtually certain that if you asked on Zulip, the poll would go in favor of `omega_zero` too and `aleph_zero` too (at least, assuming votes from the same 

## pr33198_i02  [V4/correctness/unknown | NOT JUDGEABLE]
**ask**: Do not remove or “symmetrize” the existing asymmetry in the lemma; keep the lemma statement asymmetric because that asymmetry is meaningful.
**why** (stated): Maintainer notes: “the asymmetry in that lemma is actually very important… indicates something meaningful about the difference between them,” so the refactor should preserve the asymmetric lemma statement rather than making it symmetric during renaming/cleanup.
**anchors**: Basic.lean:760*  (* = inferred)
> [V4] Oh I see! Then I think the asymmetry in that lemma is actually very important! It actually indicates something meaningful about the difference between them.

## pr33198_i03  [V1/correctness/dropped | NOT JUDGEABLE]
**ask**: Fix the PR so the build succeeds (resolve the CI failures) before merging.
**why** (stated): Maintainer explicitly notes “The build is failing” and sets `bors r-` / `bors d+`, indicating this is blocking until CI is green.
**anchors**: Basic.lean:760*  (* = inferred)
> [V1] The build is failing: https://github.com/leanprover-community/mathlib4/actions/runs/20436145675/job/58717788626#step:22:905 bors r- bors d+

## pr33190_i01  [V3/style/adopted]
**ask**: In `eq_of_natDegree_lt_card_of_eval_eq`, replace the `apply` call `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero (hf := hf)` with an explicit argument application `apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf`.
**why** (inferred): Make `hf` an explicit argument to `eq_zero_of_natDegree_lt_card_of_eval_eq_zero` in the `apply` line to avoid confusion about where `hf` is being supplied.
**anchors**: Roots.lean:630  (* = inferred)
> [V3] only because I was confused why `hf` wasn't an explicit argument, and then after looking above, I realized it is. ```suggestion   apply eq_zero_of_natDegree_lt_card_of_eval_eq_zero _ hf ```

## pr33183_i01  [V3/style/dropped]
**ask**: Rewrite the `MonoidalCategoryStruct` fields to use pointwise arguments directly (e.g. `tensorObj X Y i := X i ⊗ Y i`, `tensorHom f g i := f i ⊗ₘ g i`, `whiskerLeft X _ _ f i := X i ◁ f i`, `whiskerRight f Y i := f i ▷ Y i`, `tensorUnit i := 𝟙_ (C i)`), expand the docstring to start `/-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ...`, and define the `closed` structure using the concise record literal `closed X := { rightAdj := ihom X, adj.unit := closedUnit X, adj.counit := closedCounit X }`.
**why** (inferred): The maintainer provides concrete formatting/structure suggestions: prefer the pointwise `... i := ...` style over `fun ... ↦ ...`, improve the documentation header for the `Pi` monoidal instance, and use a compact record literal for the `closed`/adjunction data to match Mathlib style and improve readability.
**anchors**: Monoidal.lean:1  (* = inferred)
> [V3] ```suggestion   tensorObj X Y i := X i ⊗ Y i   tensorHom f g i := f i ⊗ₘ g i   whiskerLeft X _ _ f i := X i ◁ f i   whiskerRight f Y i := f i ▷ Y i   tensorUnit i := 𝟙_ (C i) ```
> [V3] ```suggestion /-- `Pi.monoidalCategory C` equips the product of an indexed family of categories with ```
> [V3] ```suggestion   closed X := {     rightAdj := ihom X     adj.unit := closedUnit X     adj.counit := closedCounit X } ```

## pr33169_i01  [V2/style/partially_adopted]
**ask**: Reformat the `| succ n hn =>` case so the branch arrow is on its own line and the `simpa only` arguments are line-broken/indented: use `(n : ℤ)` spacing and put `prop_red_T hS hT` on a new indented line after a trailing comma.
**why** (inferred): Maintainer prefers the suggested formatting/indentation for the `succ` case rather than the one-line `=> simpa ...` style; they explicitly provide the desired layout in a suggestion block.
**anchors**: FixedDetMatrices.lean:229, FixedDetMatrices.lean:228  (* = inferred)
> [V4] Please revert this one; I'm not convinced it's better.
> [V2] ```suggestion   | succ n hn =>     simpa only [add_comm (n : ℤ), zpow_add _ 1, ← smul_eq_mul, zpow_one, smul_assoc,       prop_red_T hS hT] ```

## pr33158_i01  [V4/other/unknown | NOT JUDGEABLE]
**ask**: No change requested (maintainer approves and merges as-is).
**why** (stated): Maintainer explicitly says the generalization to allow empty spaces “can't hurt” and then approves with “bors r+”, indicating acceptance without further modifications.
**anchors**:   (* = inferred)
> [V4] I'm not so sure that we will ever care about Stieltjes measures on the empty space, but in any case I agree this can't hurt. Thanks! bors r+

## pr33156_i01  [V3/docs/adopted]
**ask**: Add the missing doc-string for the newly introduced `optAttrArg` syntax in `Mathlib/Util/AddRelatedDecl.lean`.
**why** (inferred): Maintainer explicitly requests: "Please add the missing doc-string, though." Given the PR introduces `optAttrArg` as a new named syntax, it should be documented with a doc-string in its defining file.
**anchors**:   (* = inferred)
> [V3] (Please add the missing doc-string, though.)

## pr33154_i01  [V3/docs/dropped | NOT JUDGEABLE | META]
**ask**: Update the PR description/comments (around line 24 in the PR text) to explicitly mention `to_fun` as well (i.e. include `to_fun` in that line’s mention/list).
**why** (stated): Maintainer asks: “should line 24 also mention `to_fun`?”—indicating the PR text/documentation at that location should name `to_fun` for clarity/accuracy about what is being changed.
**anchors**:   (* = inferred)
> [V3] Pre-existing: should line 24 also mention `to_fun`?

## pr33153_i01  [V2/docs/dropped | NOT JUDGEABLE]
**ask**: Clarify/show the actual differences made in the PR (the maintainer cannot see what changed).
**why** (stated): Maintainer says: "I can't see the difference here.", indicating the diff as presented is unclear or appears to have no visible changes; the PR should make the changes discernible (or avoid no-op edits).
**anchors**:   (* = inferred)
> [V2] I can't see the difference here. 

## pr33152_i01  [V2/duplication/dropped]
**ask**: Remove the new lemma `Meromorphic.meromorphicOn_univ`; instead use the existing lemma `Meromorphic.meromorphicOn` (supplying `s := Set.univ` explicitly when needed), rather than adding a dedicated `univ` specialization (and do not add it unprotected).
**why** (stated): Maintainer says this `..._univ` specialization is not generally included; if it were, it would need to be `protected`, but it's unnecessary because `Meromorphic.meromorphicOn` already covers `s = univ` and `univ` can usually be inferred or provided manually.
**anchors**: Basic.lean:562*  (* = inferred)
> [V2] I don't think we generally include the new declaration `Meromorphic.meromorphicOn_univ`. It would need to be protected if we did, but you should also just be able to use `Meromorphic.meromorphicOn`. When Lean can infer `univ`, it works, and when it c

## pr33151_i01  [V2/naming/adopted]
**ask**: Update `Mathlib/Tactic/Translate/ToDual.lean`’s `GuessName.abbreviationDict` (or equivalently `fixAbbreviations`) to map the unwanted dual-name pieces so that `to_dual` produces `SuccLimit`/`PredLimit` rather than `succColimit`/`predColimit` (i.e. add abbreviation entries translating `succColimit → SuccLimit` and `predColimit → PredLimit`, and use the dictionary to ‘un-translate’ `colimit` back to `limit` in these succ/pred contexts).
**why** (stated): The maintainer points out that if every `limit` occurrence needing special handling is always preceded by `succ`/`pred`, then it’s simpler to fix name-guessing in the `to_dual` translation machinery: use the abbreviation/fixAbbreviations dictionary to prevent `limit` from being translated to `colimit` in these cases by explicitly mapping `succColimit` to `SuccLimit` (and similarly for `pred`).
**anchors**: ToDual.lean:153*  (* = inferred)
> [V2] Is it true that all instances of the word `limit` that need to be translated are preceded by either `succ` or `pred`? In that case it may be better to use the fixAbbreviations dictionary to un-translate `colimit` to`limit` in these cases.  (I agree w
> [V2] In `abbreviationDict`, add an entry for translating `succColimit` to `SuccLimit` and similarly for `pred`.

## pr33150_i01  [V2/naming/adopted]
**ask**: Change the `@[to_dual]` annotation on `pred_le_iff_le_succ` to explicitly set the correct dual lemma name, i.e. replace `@[to_dual]` with `@[to_dual le_succ_iff_pred_le]`.
**why** (stated): The maintainer notes the existing `@[to_dual]` generates the wrong dual name, so the dual lemma name must be specified explicitly in the attribute.
**anchors**: Basic.lean:828  (* = inferred)
> [V2] I think this generates the wrong dual name

## pr33149_i01  [V1/correctness/unknown]
**ask**: Remove the newly introduced `axiom` declarations (and any reliance on them), replacing them with proved lemmas or existing Mathlib results so the file adds no new axioms.
**why** (stated): The maintainer states that Mathlib has a no-axioms policy and asks not to introduce any new axioms; the file currently declares multiple axioms (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`, etc.).
**anchors**:   (* = inferred)
> [V1] Mathlib has a no-axioms policy. Please don't introduce any new axioms.

## pr33149_i02  [V2/duplication/dropped]
**ask**: Replace any custom/axiomatized Parseval-type identity used in the PR with the existing Parseval's identity lemma(s) from Mathlib; if a specialized version (e.g. for the standard basis in ℝⁿ) is genuinely needed, add that specialization in the appropriate existing Mathlib location instead of duplicating it in this new file.
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): Maintainer notes Mathlib already provides Parseval's identity and asks to use it rather than introducing a redundant custom version; specialized variants should be added where such lemmas belong (near the existing Parseval development) if required.
**anchors**:   (* = inferred)
> [V2] Mathlib already has Parseval's identity. Please use that instead (and if you really need a version specialised to e.g. the standard basis in R^n, add it there).

## pr33149_i03  [V3/correctness/dropped]
**ask**: Remove the newly introduced axioms (e.g. `cMoser`, `cGronwall`, `cSobolev`, `fourier_ortho_integral`, `fubini_torus3`, etc.) and replace them with actual definitions/lemmas proved from existing mathlib results; when introducing new definitions/structures, also add basic supporting lemmas so the additions are maintainable.
**why** (stated): Maintainer states: "Introducing additional axioms is a no go" and that the PR "introduces lots of new definitions without supporting lemmas (that is not maintainable; please add basic lemmas about them when adding them)."
**anchors**:   (* = inferred)
> [V3] Hi! It's good to hear that you want to contribute to mathlib. That said, your code raises a number of questions: did you use AI to generate it? (If so, which parts: all of it? what did you prompt it with? do you know the mathematics behind it? etc.) 

## pr33149_i04  [V4/correctness/dropped | NOT JUDGEABLE]
**ask**: Rewrite the file to meet mathlib standards by (1) eliminating all `axiom`s (replace with actual definitions/lemmas derived from Mathlib, or mark gaps with `sorry` during development), (2) removing/ inlining local wrapper definitions that merely rename existing Mathlib notions (optionally keep as `abbrev` only if truly needed), and (3) fixing definitions like `fourierDecay` and `spectralNSResidual` (and anything depending on them such as `SolvesNavierStokes`) so they are not vacuously true.
**why** (stated): The maintainer states the PR would need a complete rewrite: it currently uses axioms (unacceptable for Mathlib), introduces redundant renaming definitions, and contains definitions that are vacuously true, which is a major correctness red flag; the maintainer requests careful review of all definitions to avoid such pitfalls.
**anchors**:   (* = inferred)
> [V4] Actually, let me close this PR for now: as I see it, it would need to be completely rewritten to have a change of being acceptable to mathlib --- and the rewrite would bear almost no resemblance to this PR. As such, I don't think keeping this PR open
> [V4] Dear Jeff,  I'm happy to hear if my initial impression is wrong. (We are receiving a fair number of posts that are AI-generated with very little effort or understanding on the commenter's part, which is why I have a strong initial reaction about th

## pr33146_i01  [V3/docs/adopted]
**ask**: Capitalize the docstrings for the whiskering lemmas, changing “postcompose/precompose” to “Postcompose/Precompose” in the `/-- … -/` comments.
**why** (stated): Maintainer notes “Might as well fix some capitalization” and suggests `/-- Precompose an equation between morphisms by another morphism -/]`, indicating the doc comment should start with a capital letter.
**anchors**: Basic.lean:223  (* = inferred)
> [V3] Might as well fix some capitalization. ```suggestion /-- Precompose an equation between morphisms by another morphism -/] ```

## pr33145_i01  [V2/duplication/partially_adopted]
**ask**: Rename the lemmas `Dense.continuous_upperBounds` and `Dense.continuous_lowerBounds` to `Dense.upperBounds_image` and `Dense.lowerBounds_image`, and reprove the lower-bounds lemma by dualizing the upper-bounds lemma via `OrderDual` (i.e. `lowerBounds (f '' S) = lowerBounds (range f) := hS.continuous_upperBounds (α := αᵒᵈ) hf`).
**why** (inferred): The maintainer suggests alternative lemma names (`Dense.upperBounds_image`, `Dense.lowerBounds_image`) and points out a simplification: the lower-bounds statement can be obtained from the upper-bounds statement by applying it to `αᵒᵈ` (OrderDual) instead of duplicating a near-identical proof.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.upperBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] ```suggestion theorem Dense.lowerBounds_image {α : Type*} [TopologicalSpace α] [Preorder α] ```
> [V2] There's a trick you can use for this kind of thing by using the `OrderDual`. ```suggestion     lowerBounds (f '' S) = lowerBounds (range f) :=   hS.continuous_upperBounds (α := αᵒᵈ) hf ```

## pr33145_i02  [V2/duplication/adopted]
**ask**: Refactor the new dense-set supremum/infimum results into lemmas named `Dense.ciSup` and `Dense.ciInf` (with signature starting `theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ...`), and obtain the infimum statement by reusing the supremum lemma via order duality (e.g. prove `⨅ i, f i = ⨅ s : S, f s` by `hS.ciSup (α := αᵒᵈ) hf h`) rather than duplicating a separate lower-bounds argument.
**why** (inferred): The comments suggest introducing `Dense.ciSup`/`Dense.ciInf` as the main API and using `αᵒᵈ` to derive the infimum lemma from the supremum lemma, which avoids duplicating essentially symmetric proofs for sup/inf.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup (α := αᵒᵈ) hf h ```

## pr33145_i03  [V2/duplication/adopted]
**ask**: Refactor the dense-set boundedness/supremum/infimum lemmas into dualized `ciSup`/`ciInf` versions by (1) introducing lemmas `Dense.ciSup' {α : Type*} [TopologicalSpace α] ...` and `Dense.ciInf' {α : Type*} [TopologicalSpace α] ...` (rather than separate bespoke sup/inf lemmas), and (2) prove the `ciInf'` statement via order duality by rewriting it as a `ciSup'` on `αᵒᵈ` (e.g. `⨅ i, f i = ⨅ s : S, f s := hS.ciSup' (α := αᵒᵈ) hf`).
**why** (inferred): The maintainer is directing that the infimum result should be obtained from the supremum result using `αᵒᵈ` (as indicated by the explicit suggested proof line), and that the lemmas should be formulated as `ciSup'`/`ciInf'` variants with `{α : Type*} [TopologicalSpace α]` to align with Mathlib’s duality patterns and avoid duplicating parallel sup/inf arguments.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] ```suggestion theorem Dense.ciSup' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion theorem Dense.ciInf' {α : Type*} [TopologicalSpace α] ```
> [V2] ```suggestion     ⨅ i, f i = ⨅ s : S, f s :=   hS.ciSup' (α := αᵒᵈ) hf ```

## pr33145_i04  [V2/style/adopted]
**ask**: Refactor the `ciSup`/supremum proof to begin with a `by_cases` split on `BddAbove (range (fun x : S ↦ f x))`, using the bounded-above branch to apply the dense-set `ciSup` lemma via `h.closure.mono` and `hf.range_subset_closure_image_dense hS`, and using the unbounded branch to derive `¬ BddAbove (range f)` (by contraposition and monotonicity) and finish by simp with `ciSup_of_not_bddAbove`.
**why** (stated): The maintainer indicates the proof will be simpler and more robust if it explicitly handles the two cases “the subtype range is bounded above” vs “not bounded above”, and in the unbounded case reduces to the standard `ciSup_of_not_bddAbove` simp path after showing `range f` is also not bounded above.
**anchors**: IsLUB.lean:166  (* = inferred)
> [V2] It's easier if you case split on whether the range of the function from the subtype is bounded above or not. ```suggestion   by_cases h : BddAbove (range (fun x : S ↦ f x))   · refine hS.ciSup hf <| h.closure.mono ?_     simpa [← Function.comp_def, r

## pr33145_i05  [V3/style/dropped]
**ask**: Swap the sides of the `iSup`/`iInf` equalities so they are stated with the dense-set supremum/infimum on the left and the universe/index supremum/infimum on the right, e.g. change `⨆ i, f i = ⨆ s : S, f s` to `⨆ s : S, f s = ⨆ i, f i` (and similarly for `iInf`).
**why** (inferred): The maintainer suggests rewriting the declarations so the `iSup`/`iInf` statements “read `⨆ s : S, f s = ⨆ i, f i := by` instead”, i.e. presenting the dense-set side first for readability/consistency.
**anchors**:   (* = inferred)
> [V3] I suggest turning the declarations involving `iSup` and `iInf` around so that they read: ```lean     ⨆ s : S, f s = ⨆ i, f i := by ``` instead.

## pr33144_i01  [V2/duplication/dropped]
**ask**: Remove the redundant eta-expanded `fun_` lemmas `fun_deriv` and `fun_iterated_deriv` (both in the `MeromorphicAt` section and the `MeromorphicOn` section), keeping only the non-eta-expanded `deriv`/`iterated_deriv` lemmas.
**why** (stated): Maintainer decision: only add `fun_` versions when needed; since these lemmas are unused and merely restate existing lemmas with a trivial `fun _ => ...` wrapper, they should be removed to reduce redundancy.
**anchors**:   (* = inferred)
> [V4] This PR itself it straightforward; the main question is whether we want it.
> [V2] @kebekus Thanks for the explanation! Let's only add `fun_` versions as needed then --- as these lemmas are unused, let's remove them. bors r+

## pr33141_i01  [V2/correctness/adopted]
**ask**: Add `@[to_additive (relevant_arg := X)]` to all `to_additive`-annotated declarations in this file (not just `instCoalgebra`), so `instIsCocomm`, `counit_single`, and `comul_single` also specify `relevant_arg := X`.
**why** (inferred): Maintainer explicitly notes that `(relevant_arg := X)` is needed on all declarations, presumably to ensure `to_additive` chooses the intended parameter as the additive/multiplicative-relevant one and produces correctly named/translated additive analogues.
**anchors**: MonoidAlgebra.lean:35  (* = inferred)
> [V2] I think you need the `(relevant_arg := X)` on all of the declarations in this file

## pr33137_i01  [V2/style/dropped]
**ask**: In the `mapDomainNonUnitalAlgHom` structure definition, replace the lambda `map_mul' := fun x y => mapDomain_mul f x y` with the direct assignment `map_mul' := mapDomain_mul f`.
**why** (inferred): `mapDomain_mul f` already has the correct (curried) type for `map_mul'`, so the explicit `fun x y => ...` is unnecessary; using the lemma directly is cleaner and more idiomatic.
**anchors**: Basic.lean:217  (* = inferred)
> [V2] ```suggestion   map_mul' := mapDomain_mul f ```

## pr33127_i01  [V2/docs/adopted]
**ask**: Remove the stray `example {n : ℕ} [NeZero n] (hn : 2 ≤ n) : (1 : Fin n).val = 1 := ...` test code, and instead add a section-level comment explaining the need for `haveI := _.neZero` (or `NeZero n`) in the following lemmas about shifting endpoints by 1.
**why** (stated): The maintainer identifies the `example` as test code that should be removed, and suggests that the underlying point it was demonstrating (why the `haveI`s are present) should be documented as a comment at the top of the section.
**anchors**: Fin.lean:896, Fin.lean:896  (* = inferred)
> [V2] I assume this is test code, and can be removed? ```suggestion ```
> [V3] This may be worth turning into a comment at the top of the section!

## pr33117_i01  [V2/duplication/partially_adopted]
**ask**: Import `Mathlib.Tactic.ToFun` and replace the duplicated `fun_*` lemmas for `Meromorphic` closure properties with `@[to_fun (attr := fun_prop)]` on the main lemmas (`neg`, `add`, `sum`, `sub`, `mul`, `prod`, `div`, `pow`, `zpow`, `deriv`, `iterated_deriv`) so the corresponding `fun x ↦ …` versions are generated automatically.
**why** (inferred): The maintainer points out that new metaprogramming support (`to_fun` attribute) can auto-generate the `fun x ↦ …` variants while still registering `fun_prop`, avoiding manual duplication and extra lemmas like `fun_neg`, `fun_add`, `fun_sum`, etc.; this requires importing `Mathlib.Tactic.ToFun`.
**anchors**: Basic.lean:631, Basic.lean:8*  (* = inferred)
> [V2] There is some new metaprogramming that can help here: the `to_fun` attribute. To get access, you need to add `import Mathlib.Tactic.ToFun` to the imports (doesn't need `public`).  ```suggestion @[to_fun (attr := fun_prop)] lemma neg (hf : Meromorphic

## pr33111_i01  [V3/naming/partially_adopted]
**ask**: Rename the new dot-notation lemmas to use the existing `injective_of_*` naming convention for consistency (e.g. prefer `injective_of_eq_imp_le` over `Function.Injective.of_eq_imp_le`, and similarly rename the related `Function.Injective.of_lt_imp_ne`/others accordingly rather than mixing conventions).
**why** (stated): Maintainer asks “why not call it `injective_of_eq_imp_le`?” and then concludes to “keep things consistent and rename the others in a better way!”, indicating the goal is consistent lemma naming across this API rather than introducing a different `Function.Injective.of_...` convention.
**anchors**: Defs.lean:320*  (* = inferred)
> [V3] why not call it `injective_of_eq_imp_le`?
> [V3] You could deprecate it. Probably a good idea. ~~But I'd suggest keeping the theorem as is, just add the `@[deprecated Function.Injective.of_... (since := ...)]`.~~
> [V3] Meh, rename away. I only suggested it to keep things consistent. So let's keep things consistent and rename the others in a better way!

## pr33111_i02  [V2/style/partially_adopted]
**ask**: Reorder the new `injective_of_eq_imp_le` lemma to appear before `injective_of_lt_imp_ne`, and then rewrite the proof of `injective_of_lt_imp_ne` to be a short one-liner using `injective_of_eq_imp_le` (either via an explicit `exact ...` term proof or `grind [injective_of_eq_imp_le]`).
**why** (inferred): The maintainer suggests that if the new lemma is placed earlier, `injective_of_lt_imp_ne` can be proved directly from it with a compact proof (`exact injective_of_eq_imp_le ...`) or by automation (`grind [injective_of_eq_imp_le]`), improving brevity and leveraging the new API.
**anchors**:   (* = inferred)
> [V2] if you move the new lemma before this one, you could do ```suggestion   exact injective_of_eq_imp_le f fun {x y} ↦     not_lt (α := α) |>.eq ▸ imp_not_comm.mp (eq_comm.eq ▸ h y x) ``` or ```suggestion   grind [injective_of_eq_imp_le] ```

## pr33111_i03  [V4/naming/unknown | META]
**ask**: Revise the PR title to accurately reflect the change (it adds a new more general injectivity lemma / API, rather than “weakening the hypothesis” of the existing lemma).
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): The maintainer says the current title is confusing because the change is “not really weakening the hypothesis of that lemma” but instead “adding one that can work in a more general setting,” so the title should match that intent.
**anchors**: Defs.lean:320*  (* = inferred)
> [V4] The title kinda confused me. It's not really weakening the hypothesis of that lemma. It's more adding one that can work in a more general setting.

## pr33107_i01  [V4/scope/dropped | NOT JUDGEABLE]
**ask**: Refactor `LinearMap.range` and `LinearMap.ker` so they take an explicit `LinearMap` argument (not a linear-map typeclass), making the proposed `ContinuousLinearMap` simp lemmas unnecessary/automatic (and enabling dot-notation), and coordinate this change by asking on Zulip about objections before proceeding.
**why** (stated): Maintainers say the PR is working around a deeper library flaw: `LinearMap.range`/`ker` are currently defined via a linear map class rather than an actual `LinearMap`, and fixing that design would make these simp lemmas “come for free” and improve dot-notation/automation more generally. They explicitly encourage “ripping it out” and reference a Zulip thread on the morphism hierarchy.
**anchors**:   (* = inferred)
> [V4] I think we should refactor the definitions of `LinearMap.range` and `LinearMap.ker` to take in an actual linear map and not a linear map class. That way, all of this comes for free. It'll also allow for dot notation, solve more of these issues, etc..
> [V4] @Timeroot yes, Monica is correct here. Unfortunately you are exposing a flaw that exists currently in the library. Help ripping it out is encouraged! For more information see the Zulip thread: [#mathlib4 > Mathlib's morphism hierarchy](https://leanpr

## pr33104_i01  [V3/naming/dropped]
**ask**: Rename the two `Homeomorph`/`UniformEquiv` transfer abbreviations from `protected abbrev pseudometricSpace` to `protected abbrev pseudoMetricSpace` (capitalizing `Metric`) so the identifier matches the standard `PseudoMetricSpace` camel-case convention.
**why** (inferred): The maintainer’s suggestion blocks show the intended name `pseudoMetricSpace` for both the `α ≃ₜ β` and `α ≃ᵤ β` variants, replacing the existing `pseudometricSpace` spelling.
**anchors**:   (* = inferred)
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ₜ β) : PseudoMetricSpace α := ```
> [V3] ```suggestion protected abbrev pseudoMetricSpace [PseudoMetricSpace β] (e : α ≃ᵤ β) : PseudoMetricSpace α := ```

## pr33101_i01  [V3/scope/adopted]
**ask**: Wrap the earlier block of `variable` declarations in an explicit `section`/`end` so that the later repeated `variable {K V₁ V₂}` declarations after `end Module.Dual` are not duplicated/unscoped; concretely, insert an `end` before the new `variable` lines to close the prior section.
**why** (stated): The maintainer notes the new `variable`s duplicate existing ones and asks to enclose the previous ones in a `section`/`end` block to avoid unexpected scope leakage/"surprises" from variable declarations carrying further than intended.
**anchors**: Lemmas.lean:781, Lemmas.lean:780  (* = inferred)
> [V3] It looks like this duplicates the `variable`s.  Could you enclose the previous one in a `section`/`end` block, to avoid "surprises"?

## pr33098_i01  [V2/style/partially_adopted]
**ask**: Replace the case-split proof of `minimalCover_subset` with a one-liner `grind` proof (`by grind [minimalCover]`), adding `attribute [grind .] finite_empty` (and similarly `IsSeparated.empty` for the analogous maximal-separated-set lemmas) so `grind` can close the related lemmas; additionally adjust lemma headers to introduce an `encard_` prefix for the `minimalCover`/`maximalSeparatedSet` cardinality lemmas (e.g. `encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ...`).
**why** (inferred): The maintainer indicates these lemmas (and the “next few” siblings) can be automated via `grind` if base facts like `finite_empty`/`IsSeparated.empty` are registered, yielding shorter, more uniform proofs and consistent lemma naming for `encard` statements.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] This and the next three lemmas can be proven with this, although for it to work on `finite_minimalCover`, you have to add ```lean attribute [grind .] finite_empty ``` but I think we should do that anyway. ```suggestion lemma minimalCover_subset : min
> [V2] This and the next two lemmas can be proven with this, although for it to work on `isSeparated_maximalSeparatedSet`, you have to add ```lean attribute [grind .] IsSeparated.empty ``` but I think we should do that anyway.  ```suggestion lemma maximalSe
> [V2] ```suggestion lemma encard_minimalCover (h : coveringNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) : ```
> [V2] ```suggestion lemma encard_le_of_isSeparated (h_subset : C ⊆ A) ```

## pr33098_i02  [V2/proof-golf/partially_adopted]
**ask**: Refactor the proof of the key step about maximal separated sets by introducing `C := {x} ∪ maximalSeparatedSet ε A` and using `Metric.isSeparated_insert_of_notMem` (with `hx_not_mem : x ∉ maximalSeparatedSet ε A`) to build `C ⊆ A ∧ IsSeparated ε C`, then derive the contradiction via `encard_le_of_isSeparated` and `encard_insert_of_notMem`/`ENat.lt_add_one_iff`, instead of the existing more verbose argument.
**why** (stated): Maintainer provides a concrete “golf” and says the main point is to use `Metric.isSeparated_insert_of_notMem`, indicating they want the proof simplified/streamlined by restructuring around insertion into the maximal separated set and reusing existing lemmas rather than manual separation/encard reasoning.
**anchors**: CoveringNumbers.lean:228, CoveringNumbers.lean:228  (* = inferred)
> [V2] I'm having trouble selecting the whole proof for a suggestion in the GitHub interface, but here's a golf. There's some shuffling, but the main point is to use `Metric.isSeparated_insert_of_notMem`. ```lean   intro x hxA   by_contra! h_dist   let C :=

## pr33098_i03  [V2/style/adopted]
**ask**: In `coveringNumber_le_packingNumber`, replace the manual `by_cases` proof with the `by_cases!` pattern and use `encard_maximalSeparatedSet` together with `IsCover.coveringNumber_le_encard`: `by_cases! h_top : packingNumber ε A ≠ ⊤; · rw [← encard_maximalSeparatedSet h_top]; exact isCover_maximalSeparatedSet h_top |>.coveringNumber_le_encard maximalSeparatedSet_subset; · simp [h_top]` (removing the existing `card_maximalSeparatedSet`/`iInf_le`/`simp only`-based proof).
**why** (stated): The maintainer points out (1) `by_cases!` will automatically push negations in the second branch, and (2) there is already a lemma `IsCover.coveringNumber_le_encard` that should be used to streamline the argument; so the proof should be rewritten to use these newer/cleaner tools.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] We now have `by_cases!` to automatically push your negations in the alternate branch. And we have this nice `IsCover.coveringNumber_le_encard` lemma, we might as well use it. :smiley: ```suggestion   by_cases! h_top : packingNumber ε A ≠ ⊤   · rw [← 

## pr33098_i04  [V2/style/adopted]
**ask**: In `coveringNumber_two_mul_le_externalCoveringNumber`, replace the `rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)` split with `rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)` and then discharge the empty-set case by `simp` (i.e. use `rfl` for the empty branch instead of naming `h_empty`).
**why** (inferred): The maintainer suggests a more idiomatic empty/nonempty split: rewriting `A` to `∅` directly (`rfl`) makes the empty case solvable by a one-line `simp`, streamlining the proof.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V2] ```suggestion   rcases Set.eq_empty_or_nonempty A with (rfl | h_nonempty)   · simp ```

## pr33098_i05  [V3/style/adopted]
**ask**: Rewrite the `calc` proof in `coveringNumber_subset_le` so that the initial `calc` line includes the goal equality, i.e. change from starting with `calc coveringNumber ε A` to `coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc` (so subsequent lines are indented per style guidelines).
**why** (stated): Maintainer notes that otherwise Mathlib style guidelines would require indenting all lines below the first `calc` line; writing `... := calc` on the first line avoids the extra indentation requirement.
**anchors**: CoveringNumbers.lean:390  (* = inferred)
> [V3] otherwise style guidelines would require to indent all lines below the first `calc` line. ```suggestion     coveringNumber ε A ≤ coveringNumber (ε / 2) B := calc   coveringNumber ε A ```

## pr33092_i01  [V3/docs/adopted]
**ask**: Explain in the docstring of the private `walk_toSimpleGraph'` definition why it exists/what important downstream result it is used for (i.e. document its purpose despite being private).
**why** (stated): Maintainer questions the existence of a private def and says that if it is used to prove an important theorem below, "the docstring should explain that."
**anchors**: Connected.lean:643, Connected.lean:643, Connected.lean:653  (* = inferred)
> [V3] I don't undertand why this def exists if it is private. Is it used to prove an important theorem below? If so, I think the docstring should explain that.

## pr33090_i01  [V3/style/adopted]
**ask**: Replace the one-way positivity lemma `coveringNumber_pos (hA : A.Nonempty) : 0 < coveringNumber ε A` (and similarly `externalCoveringNumber_pos`, `packingNumber_pos`) with an `iff` lemma `0 < ... ↔ A.Nonempty` so that `simp` can use it more efficiently.
**why** (stated): Maintainer requested: “Could you make this one an iff lemma? `simp` would be more efficient then.” Turning positivity into an iff with `A.Nonempty` lets `simp` rewrite both directions and avoid having to synthesize a `Nonempty` argument.
**anchors**: CoveringNumbers.lean:80, CoveringNumbers.lean:98  (* = inferred)
> [V3] Could you make this one an iff lemma? `simp` would be more efficient then.

## pr33086_i01  [V3/docs/adopted]
**ask**: Add documentation clarifying the intended usage distinction between the `cofibrantObjects`/`fibrantObjects` `ObjectProperty` APIs and the `IsCofibrant`/`IsFibrant` typeclass Props: namely, `IsCofibrant`/`IsFibrant` should be used as Prop typeclasses in practice, while `cofibrantObjects`/`fibrantObjects` exist mainly to define the corresponding full subcategories.
**why** (stated): Maintainer requests an explicit doc entry explaining the “intended usages” of the two APIs: `IsCofibrant` as a Prop-class, and the `ObjectProperty` form not as the primary interface (same for fibrant).
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] I think there should be a documentation entry here about the "intented usages" of the two APIs `cofibrantObjects`/`IsCofibrant`. As far as I understand, `IsCofibrant` is to be used as a Prop-Class, while the object property shouldn’t. This needs to b

## pr33086_i02  [V3/style/adopted]
**ask**: Add a simp lemma `weakEquivalence_homMk_iff` stating that for cofibrant/fibrant objects `X Y`, `WeakEquivalence (homMk f) ↔ WeakEquivalence f`, proved via `simp only [weakEquivalence_iff]; rfl`.
**why** (inferred): The file defines `homMk` constructors for morphisms in the full subcategories; the maintainer notes this simp lemma was missing "compared to the others" and wants the corresponding `WeakEquivalence` characterization for `homMk` to simplify rewriting.
**anchors**: Bifibrant.lean:1, Bifibrant.lean:1  (* = inferred)
> [V3] Was this one intentionally left out compared to the others?  ```suggestion  @[simp] lemma weakEquivalence_homMk_iff [CategoryWithWeakEquivalences C] {X Y : C}     [IsCofibrant X] [IsFibrant X] [IsCofibrant Y] [IsFibrant Y] (f : X ⟶ Y) :     We

## pr33081_i01  [V2/proof-golf/dropped | NOT JUDGEABLE]
**ask**: Replace the existing lambda proof term with `fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl)`.
**why** (inferred): The maintainer proposes a more direct/idiomatic term-style proof for an `iUnion` membership goal, using `Set.mem_iUnion_of_mem` and `Set.mem_setOf.mpr le_rfl` to avoid a more verbose construction.
**anchors**:   (* = inferred)
> [V2] ```suggestion     fun i _ ↦ Set.mem_iUnion_of_mem i (Set.mem_setOf.mpr le_rfl) ```

## pr33079_i01  [V3/naming/adopted]
**ask**: Replace the lemma `neZero_of_exists` with a shorter dot-notation-friendly lemma named `Fin.neZero` (i.e. `lemma neZero {n} (i : Fin n) : NeZero n := ⟨Nat.ne_zero_of_lt i.isLt⟩` or equivalent such as `⟨i.2.ne⟩`).
**why** (stated): The maintainer suggests using a more direct proof term (e.g. `⟨i.2.ne⟩`) and asks about naming it `Fin.neZero` to support dot notation, instead of the longer `neZero_of_exists` proof via rewriting to `n=0` and `elim0`.
**anchors**: Basic.lean:90, Basic.lean:90  (* = inferred)
> [V3] Does something like ⟨i.2.ne⟩ work as a proof? Also, what about calling this `Fin.neZero` for dot notation?

## pr33078_i01  [V2/style/adopted]
**ask**: Replace the direct simp/prod-of-roots proof that constructs `NeZero (n : ℂ)` with a proof that (1) introduces `have : NeZero n := ⟨hn⟩`, (2) reduces Mahler measure to the product over `primitiveRoots n ℂ` of `max 1 ‖x‖`, and (3) shows this product is `1` by proving `∀ x ∈ primitiveRoots n ℂ, ‖x‖ ≤ 1` and applying `Multiset.prod_eq_one` (using `IsPrimitiveRoot.norm'_eq_one ... hn`).
**why** (inferred): The maintainer indicates it suffices to assume/provide `NeZero n` (letting typeclass inference obtain the needed nonzeroness in `ℂ`), and suggests restructuring the proof via `primitiveRoots` and a bound `‖x‖ ≤ 1` to conclude the product of `max 1 ‖x‖` is `1`, rather than building `NeZero (n : ℂ)` explicitly and using `le_of_eq` pointwise.
**anchors**: MahlerMeasure.lean:113, MahlerMeasure.lean:113  (* = inferred)
> [V2] I think it is enough to provide `NeZero n`, and then the typeclass system will find `have : NeZero (n : ℂ)`.
> [V2] ```suggestion   have : NeZero n := ⟨hn⟩   suffices ∏ x ∈ primitiveRoots n ℂ, max 1 ‖x‖ = 1 by     simpa [mahlerMeasure_eq_leadingCoeff_mul_prod_roots, cyclotomic.monic n ℂ,       Polynomial.cyclotomic.roots_eq_primitiveRoots_val]   suffices ∀ a ∈ pri

## pr33070_i01  [V2/style/adopted]
**ask**: Replace `let ppDomain ← withAppArg do return getPPFunBinderTypes (← getOptionsAtCurrPos)` with `let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes` (for the `Finset.sum` pretty-printer, and likewise for the analogous `Finset.prod` code).
**why** (inferred): The maintainer suggests the existing code is equivalent to, and should be written using, the standard `getPPOption` helper under `withAppArg`, rather than manually fetching options at the current position and applying `getPPFunBinderTypes` directly. This is a style/simplification toward idiomatic pretty-printer option access in the correct binder context.
**anchors**: Defs.lean:296*  (* = inferred)
> [V2] I think this is the same as ```suggestion   let ppDomain ← withAppArg <| getPPOption getPPFunBinderTypes ```

## pr33067_i01  [V2/correctness/dropped]
**ask**: Reconsider marking the `recall` identifier as a binder: avoid setting `(isBinder := true)` for `recall`’s syntax info unless that syntax actually generates a declaration in the environment, and additionally apply the same info-reporting fix to the `alias_in` command as well.
**why** (stated): The maintainer notes that `isBinder` should only be true when the syntax produces an environment declaration and should be the jump-to location, which they believe does not hold for `recall`; they also explicitly request making the analogous change in `alias_in`.
**anchors**: Recall.lean:44, AliasIn.lean:55*  (* = inferred)
> [V2] `isBinder` should be true only when this piece of syntax generates a declaration in the environment (so this point should be used as the "jump-to" location). That does not hold for `recall`, right?
> [V2] Can you also change `alias_in` please? Thanks!  I am surprised that without this, jump-to-definition still works. I thought the `isBinder` annotation was responsible for that (maybe jump-to-definition uses a non-binder location as fallback?)

## pr33066_i01  [V3/docs/adopted]
**ask**: Fix the docstring typo by changing “An isometry linear equivalence …” to “An isometric linear equivalence …” in the documentation comment for `LinearIsometryEquiv.conjStarAlgEquiv`.
**why** (inferred): The maintainer’s suggestion block shows the intended wording “An isometric linear equivalence …”, correcting the grammatical error “An isometry linear equivalence …” in the existing doc comment.
**anchors**: Adjoint.lean:683  (* = inferred)
> [V3] ```suggestion /-- An isometric linear equivalence of two Hilbert spaces induces an equivalence of ```

## pr33066_i02  [V2/duplication/adopted]
**ask**: Delete the custom `ContinuousAlgEquiv.ofAlgEquiv` definition and its accompanying simp lemmas (`coe_ofAlgEquiv`, `toAlgEquiv_ofAlgEquiv`, `ofAlgEquiv_toAlgEquiv`, `symm_ofAlgEquiv`, `ofAlgEquiv_trans_ofAlgEquiv`), and instead construct continuous algebra equivalences from an `AlgEquiv` using the existing constructor `ContinuousAlgEquiv.mk` (with `continuous_toFun`/`continuous_invFun` fields).
**why** (stated): The maintainer points out that `ofAlgEquiv` is defeq to the pre-existing `ContinuousAlgEquiv.mk` constructor (up to definitional equalities involving `invFun`/`symm`/`DFunLike.coe`), so the new definition and lemmas are unnecessary duplication and should be removed in favor of `mk`.
**anchors**: Equiv.lean:302  (* = inferred)
> [V2] This is just the pre-existing constructor for `ContinuousAlgEquiv`: ``` ContinuousAlgEquiv.mk.{u_1, u_2, u_3} {R : Type u_1} {A : Type u_2} {B : Type u_3} [CommSemiring R] [Semiring A]   [TopologicalSpace A] [Semiring B] [TopologicalSpace B] [Algebra

## pr33066_i03  [V2/style/adopted]
**ask**: Insert a blank line after `section auxiliaryDefs` and move the subsequent `variable` declaration to start after that blank line (i.e., format as `section auxiliaryDefs` then an empty line then `variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0)` …).
**why** (stated): The maintainer explicitly suggested the preferred section/variable formatting, indicating a style improvement: `section auxiliaryDefs` followed by a blank line and then the `variable` line (with `hα` on that line).
**anchors**: ContinuousAlgEquiv.lean:85, ContinuousAlgEquiv.lean:85  (* = inferred)
> [V2] You can still phrase this as: ```suggestion     Function.Surjective (LinearIsometryEquiv.conjStarAlgEquiv : (V ≃ₗᵢ[𝕜] W) → _) := by ``` and I think Lean shouldn't need you to fill in the `_`.
> [V3] This is nice, but it would be even nicer if it were interspersed throughout the code.
> [V3] ```suggestion section auxiliaryDefs  variable (e : V ≃L[𝕜] W) {α α' : 𝕜} (hα : α ≠ 0) ```
> [V3] The naming of your `have`s could use some work. Please improve them.

## pr33065_i01  [V3/naming/partially_adopted]
**ask**: Fix the docstring typo “accumulated point” to “accumulation point”, and rename the new lemmas from dot-notation `ContinuousWithinAt.of_not_accPt` / `ContinuousAt.of_not_accPt` to snake_case `continuousWithinAt_of_not_accPt` (and likewise for the second lemma) to match naming conventions since they don’t take a `ContinuousWithinAt` hypothesis.
**why** (stated): Maintainer suggests the docstring wording and argues the lemma should be named `continuousWithinAt_of_not_accPt` for consistency with existing lemmas like `continuousWithinAt_of_notMem_closure`, noting dot notation is usually unusable here because there is no `ContinuousWithinAt` hypothesis to attach it to; “This also applies to the second lemma”.
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V3] ```suggestion /-- A function is continuous at a point `x` within a set `s` if `x` is not an accumulation point of ```
> [V3] I think it would make sense to call this `continuousWithinAt_of_not_accPt` instead to stay consistent with e.g. `continuousWithinAt_of_notMem_closure` - since the lemma doesn't take in any `ContinuousWithinAt` hypothesis, dot notation can't be used m

## pr33065_i02  [V4/style/dropped | NOT JUDGEABLE]
**ask**: Decide whether to state/use `¬ AccPt x (𝓟 {x}ᶜ)` or the equivalent `¬ AccPt x ⊤` (since `AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤`) in the `ContinuousAt.of_not_accPt` lemma (and related statements), and adjust the lemma statement/proof accordingly.
**why** (stated): The maintainer points out an equivalence `AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤` and explicitly raises the question of which form should be preferred, indicating the code should pick one of these equivalent hypotheses for the isolated-point continuity lemma(s).
**anchors**: ContinuousOn.lean:296  (* = inferred)
> [V4] Note that `AccPt x (𝓟 {x}ᶜ)` is equivalently just `AccPt x ⊤`: ``` import Mathlib  open Topology Filter Set  example {α : Type*} [TopologicalSpace α] {x : α} : AccPt x (𝓟 {x}ᶜ) ↔ AccPt x ⊤ := by   simp [← principal_univ, accPt_principal_iff_nh

## pr33057_i01  [V1/correctness/adopted | NOT JUDGEABLE]
**ask**: Fix the remaining error(s) in the PR so that it builds/CI passes, then merge (bors d+).
**why** (stated): The maintainer says they are delegating so the author can fix “the last error”, implying the PR still has a failing proof/build issue that must be resolved before approval/merge.
**anchors**: Expand.lean:33*  (* = inferred)
> [V1] Thanks! Delegating so you can fix the last error.   bors d+

## pr33056_i01  [V4/naming/dropped | NOT JUDGEABLE]
**ask**: Decide the naming convention for the first uncountable aleph via a Zulip vote, and (depending on the outcome) rename the identifier accordingly—maintainer expects avoiding numerals, e.g. prefer a word-based form like `alephOne`/`aleph_one` rather than `aleph1`.
**why** (stated): Maintainer requests broader community decision (“there should be a Zulip vote”) and notes Mathlib generally avoids numerals in identifiers (“we generally don't use numerals in identifiers”, citing `cos_pi_div_two`), so the PR’s `aleph1` spelling may be the wrong direction.
**anchors**:   (* = inferred)
> [V4] I think there should be a Zulip vote for this. I would have expected that we go the *other* way, potentially with `alephOne` instead of `alepha_one`. The point being that we generally don't use numerals in identifiers (cf. `cos_pi_div_two` for exampl

## pr33048_i01  [V3/scope/adopted]
**ask**: Add a new simp lemma for `ofNat` casts: introduce `@[simp] theorem mk_ofNat {n : ℕ} [n.AtLeastTwo] : mk (ofNat n : S) = 0` proved via `mod_cast mk_intCast` (using `NeZero.ne n`), in addition to the existing `mk_natCast` lemma.
**why** (inferred): Maintainer noticed a missing simp lemma for the common `ofNat` form when `n ≥ 2` (via `[n.AtLeastTwo]`), analogous to `mk_natCast`/`mk_intCast`, and asked to add it so simp can close goals like `mk (ofNat n : S) = 0` without manually providing `n ≠ 0`.
**anchors**: Archimedean.lean:181, Archimedean.lean:174  (* = inferred)
> [V3] Just realising: we do not have  ``` @[simp] theorem mk_natCast {n : ℕ} [n.AtLeastTwo] : mk (ofNat(n) : S) = 0 :=   mod_cast mk_intCast (n := n) ``` Mind adding?

## pr33048_i02  [V2/style/partially_adopted]
**ask**: Change the `FiniteElement.mk_*` lemmas so the nonnegativity proofs are explicit arguments (not implicit), to improve rewriting: rename `mk_add`/`mk_sub`/`mk_mul` to `mk_add_mk`/`mk_sub_mk`/`mk_mul_mk` with signature `theorem ... {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ...`, and similarly change `mk_lt_mk_iff` (and the analogous `mk_le_mk_iff`) to take `hx hy` as explicit parameters rather than implicit `{hx} {hy}`.
**why** (stated): Maintainer requests making the hypotheses explicit “for backwards rewriting”, i.e. so the lemmas can be used more easily with `rw`/`simp` in either direction without implicit argument inference issues; also indicates applying the same change to the similar lemmas (“Same below”).
**anchors**: StandardPart.lean:91  (* = inferred)
> [V2] ```suggestion theorem mk_add_mk {x y : K} (hx : 0 ≤ mk x) (hy : 0 ≤ mk y) : ``` Same below
> [V3] I would make those explicit for backwards rewriting: ```suggestion theorem mk_lt_mk_iff {x y : K} (hx hy) : ```

## pr33048_i03  [V3/naming/adopted]
**ask**: Replace the lemma `mk_le_mk_iff` with a lemma named `mk_le_mk` stating the same equivalence `FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y` (proved by `rfl`), i.e. drop the `_iff` suffix in this name.
**why** (inferred): The maintainer questions the necessity of the `_iff` suffix for a lemma whose statement is already an `↔`, and suggests using the shorter name `mk_le_mk` instead.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] Do we really need the `_iff` here? ```suggestion theorem mk_le_mk {x y : K} {hx : 0 ≤ mk x} {hy : 0 ≤ mk y} :     FiniteElement.mk x hx ≤ .mk y hy ↔ x ≤ y :=   .rfl ```

## pr33048_i04  [V3/style/adopted]
**ask**: Replace the `instance : Coe ℚ (FiniteElement K)` with an instance `RatCast (FiniteElement K)` (i.e. provide rational casting via the `RatCast` typeclass rather than a `Coe` instance).
**why** (inferred): The maintainer suggests defining rational coercions using the standard `RatCast` typeclass (`instance : RatCast (FiniteElement K) where`) instead of a `Coe ℚ` instance, aligning with Mathlib conventions for numerals/rationals casting.
**anchors**: StandardPart.lean:91  (* = inferred)
> [V3] ```suggestion instance : RatCast (FiniteElement K) where ``` no?

## pr33047_i01  [V4/style/adopted | NOT JUDGEABLE]
**ask**: Decide/justify whether the “longer spelling” (`smulRight (1 : R →L[R] R)` / `smulRight (.id R R)`) should be preferred over the dedicated name `toSpanSingleton R` (i.e., clarify or reconsider the choice of preferred form).
**why** (stated): Maintainer questions the preference choice: “Might I ask why the longer spelling should be the preferred one?”—requesting an explanation or a change in which spelling is preferred.
**anchors**: LinearMap.lean:325*  (* = inferred)
> [V4] Might I ask why the longer spelling should be the preferred one?

## pr31342_i01  [V3/docs/dropped | META]
**ask**: Add a description to the PR message (i.e., update the PR metadata/body to include a description of the change).
**⚠ LINT**: judgeable ask names no backticked identifier (weak referents)
**why** (stated): Maintainer explicitly requested: "Could you add a description to the PR message?"
**anchors**:   (* = inferred)
> [V3] Could you add a description to the PR message?
