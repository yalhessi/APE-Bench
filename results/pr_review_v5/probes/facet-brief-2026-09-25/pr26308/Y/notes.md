# PR 26308 review notes (condition Y)

## section x3 (namespace:added; these are the `variable` blocks, which have no `section` or `namespace` keyword)
- the library / norms: everything is declared at root. This fed the namespace finding on `normalized`; see below.
- a better version: the `variable [NormedAddCommGroup V]` block can be split so that a Seminormed section holds the unconditional lemmas. Warrant met by compile, with the precedent NormedSpace/Real.lean:33-37, so I kept it as a finding.

## definition `normalized`
- the library: I searched for an existing named normalisation (mlfind normalize/normalized, `def (sign|toSphere|normalize)`). There is no named normed-space version. `‖x‖⁻¹ • x` appears inline 18 times, including SphereNormEquiv, Ray.lean and a local `g` in Complex/Tietze.lean. So there is no duplicate, which moved to the PR-level motivation finding instead. `Real.sign` is the 1-D case and served only as the API analogue.
- norms / namespace: root `normalize` (GCDMonoid) and its `normalize_zero` and `normalize_idem` clash in spirit, and the namespaced `FiniteMeasure.normalize` and `PMF.normalize` are precedents. Finding: namespace it and consider the verb form. The `lowerCamelCase` check passes.
- its API: exhibited against Real.sign's lemmas and against the hand proof in `homeomorphUnitSphereProd.left_inv`. Finding: add a reconstruction lemma, `eq_zero_iff`, sphere membership and a SameRay bridge.
- a better version, generality: Seminormed is a finding, via compile. RCLike 𝕜 generality is dropped: the ℝ version already covers ℂ-spaces through the `complexToReal` instance, and I could not argue a user consequence strong enough. `gramSchmidtNormed` (RCLike) is noted only.
- intent: the docstring "`normalized 0 = 0`, otherwise unit length" is accurate for NormedAddCommGroup. No finding.

## theorem `normalized_zero_eq_zero`
- norms: mlcount gives `_zero` 3825 against `_zero_eq_zero` 8, and sibling `normalize_zero` exists. Rename finding, warrant count.
- proof `simp [normalized]` is minimal; automation `@[simp]` is right. No other cell met.

## theorem `norm_normalized_eq_one_iff`
- library: `norm_smul_inv_norm` (NormedSpace/RCLike.lean:40) closes the reverse direction, but it lives in a module the PR does not import, and adding it would conflict with the import-slimming finding. Dropped.
- norms and automation: the iff form with an `x ≠ 0` RHS as a simp lemma is fine, and the name follows its conclusion. No finding.

## lemma `normalized_eq_self_of_norm_eq_one`
- norms: I considered `normalized_of_norm_eq_one`, after `abs_of_nonneg`. Both patterns exist and I had no clean count separating them. Dropped.
- seminormed: its proof `simp [normalized, h]` needs only `inv_one` and `one_smul`, so it is included in the Seminormed finding.

## theorem `normalized_normalized`
- proof: short, using the iff lemma. I found no shorter proof I could vouch for without compiling.
- automation: `@[simp]` is right, and the name follows the `closure_closure` pattern; GCDMonoid's sibling is `normalize_idem`, but that is not enough for a count. No finding.

## theorem `normalized_smul_of_pos`
- a better version: no weaker hypothesis exists, since r = 0 fails. A unified `normalized_smul` with `Real.sign r` would subsume both `_of_pos` and `_of_neg`, but I could not show a user need, so I dropped it (idea only).
- proof: the `x = 0` split looks necessary for `field_simp`'s `‖x‖ ≠ 0`. I did not propose an alternative I could not verify. Dropped.

## theorem `normalized_neg`
- proof, a better version: the case split is redundant, since `norm_neg` and `smul_neg` are simp and unconditional. Compile finding.
- automation: should be `@[simp]`, for the same direction as `smul_neg` and `norm_neg`. Judgment finding.

## theorem `normalized_smul_of_neg`
- proof: `by linarith` becomes `neg_pos.2 hr` (exhibit Real/Sign.lean:74), and a `field_simp` on a goal with no fractions becomes `simpa [normalized_neg] using ...`. Compile finding, which also removes the linarith dependency cited in the import finding.

## doc_comment (on `normalized`)
- intent: accurate. Norms: backticks are used. No finding.

## module_doc
- intent: accurate, though its wording is clumsy. Norms: it has no "## Main definitions" and does not name `normalized`. mlcount gives only 105 such headings against 1178 module docs in Analysis, so there is no norm to cite. Dropped.
- The copyright header says 2020 while the tree has 2024-12 deprecations. Advisory judgment finding.

## import in `Mathlib.lean`
- The line is sorted correctly for the chosen location. The location cell puts the file under `Normed/Module/`, where Basic.lean and Ray.lean with `sameRay_iff_inv_norm_smul_eq` live. Exhibit finding, advisory; the evidence is mixed, since NormedSpace/Real.lean and SphereNormEquiv.lean are still in NormedSpace/.
- The file's own import `Mathlib.Analysis.RCLike.Basic` is heavy and unused (exhibit: Real.lean and SphereNormEquiv.lean do this with Normed.Module.Basic). Finding.

## declarations as a group
- siblings: no two statements coincide, and the fixes are applied consistently apart from the redundant case splits noted above. to_additive and simps do not apply. No instances, so there is no typeclass-layer cell.

## PR as a whole
- process: no description, no motivation, no AI disclosure, and no link to the 18 inline call sites (Tietze's "I didn't find this retract in Mathlib"). Advisory judgment finding.
