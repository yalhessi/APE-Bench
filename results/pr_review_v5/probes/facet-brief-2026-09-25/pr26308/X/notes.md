# PR 26308 review notes (condition X)

## Mathlib.lean
- The new import line sits in alphabetical order (after `MultipliableUniformlyOn`, before `OperatorNorm.Asymptotics`). Nothing to ask here beyond updating it if the file moves (see the file-location finding).

## Mathlib/Analysis/NormedSpace/Normalized.lean (file level)
- Header: the copyright year is 2020, but the base tree has deprecations dated 2025-06, so I asked for 2025. The author line is fine.
- Imports: nothing from `RCLike` is used. `Analysis/NormedSpace/RCLike.lean` exists specifically so normed-space files avoid that import, and `SphereNormEquiv.lean` builds the same map from `Normed.Module.Basic` alone. So I asked for the lighter import.
- Location: `NormedSpace` is now defined in `Analysis/Normed/Module/Basic.lean`, and the unit-vector `SameRay` lemmas are in `Normed/Module/Ray.lean`. I asked, as advisory, for the file to move to `Normed/Module/Normalize.lean`. There is no `deprecated_module` evidence that the old directory is frozen, which is why it is advisory.
- Module docstring: it is ungrammatical and names nothing, so I asked for a rewrite plus a `Main definitions` entry. The three `variable` lines should become one.
- PR description is empty, so I asked for the motivation.

## normalized (def)
- Root namespace plus a generic name. The root already has `normalize`, `normalize_zero`, `normalize_idem` and `normalize_eq_zero` from GCDMonoid, so I asked for `namespace NormedSpace` (blocking). mlfind shows no existing `normalized`.
- Naming: other normalisation maps (`PMF.normalize`, `ProbabilityMeasure.normalize`) use the verb, so I asked for a rename to `normalize` (advisory).
- Generalization: `SeminormedAddCommGroup` would work for the def and some lemmas, but `norm_normalized_eq_one_iff` needs `NormedAddCommGroup`, so I did not ask. The `ℝ` scalars are enough, since complex spaces get an `ℝ`-structure. No existing def for `‖x‖⁻¹ • x` was found: only inline uses, `homeomorphUnitSphereProd`, and the `SameRay` lemmas. So there is no duplication finding. The missing basic API is requested instead: `eq_zero_iff`, `‖x‖ • normalized x = x`, and the norm bound.

## normalized_zero_eq_zero
- The proof is fine. The name breaks the `f_zero` convention (GCDMonoid sibling `normalize_zero`; 1315 against 8 by count), so I asked for a rename.

## norm_normalized_eq_one_iff
- The statement is correct and `@[simp]` fits. The proof is roundabout (constructor/contrapose! plus `show ‖x‖ ≠ 0 by simp [h]`), so I asked for an `eq_or_ne` case split and `norm_ne_zero_iff`. I was only moderately confident of the exact simp call, so it is advisory.

## normalized_eq_self_of_norm_eq_one
- This is a conditional `@[simp]` lemma whose hypothesis simp can discharge through `norm_normalized_eq_one_iff`. I found nothing to ask about the name, statement or proof.

## normalized_normalized
- The statement is correct. `normalize_idem` is the GCDMonoid sibling's name, but `f_f` names like `abs_abs` are also standard, so I did not ask for a rename. The proof rewrites the hypothesis backwards just to feed simp, so I asked for a direct composition of the two new simp lemmas.

## normalized_smul_of_pos
- The positivity hypothesis is needed because `r = 0` breaks the statement. The `by_cases` guards `field_simp`, which needs `‖x‖ ≠ 0`, and I could not confirm a shorter proof without a build, so there is no finding. A unified `SignType.sign r` version was considered and not requested.

## normalized_neg
- The `by_cases` is redundant because `norm_neg` and `smul_neg` close the goal outright, so I asked for `simp [normalized]`. I also asked for `-x` spacing and `@[simp]`.

## normalized_smul_of_neg
- The statement is correct. The proof uses `linarith` for `0 < -r` and `field_simp` to close `normalized (r • x) = normalized (-r • -x)`, so I asked for `neg_pos.2 hr` and `neg_smul_neg` (Algebra/Module/Defs.lean:138).
