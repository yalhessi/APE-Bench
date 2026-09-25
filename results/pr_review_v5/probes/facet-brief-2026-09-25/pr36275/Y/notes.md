# PR #36275: reasoning notes, object by object

**`norm_def`**
- Norms cell: the RHS uses the projection `‖x.1 v‖`. The `DFunLike` instance and existing statements (lines 103, 131, 141, 160, 172 of the Dedekind file) use `x v`, so I filed a finding under a count warrant.
- Library cell: there was no existing finite-adele norm (grep over NumberTheory). The name matches `InfiniteAdeleRing.norm_def`.

**`unitEmbedding_norm_eq_inv_abs_norm`, `unitEmbedding_norm_apply_eq_finprod_finitePlace`, `unitEmbedding_norm_apply`**
- Siblings cell: the infinite analogue `coe_norm_eq_abs_norm` is stated with `algebraMap K K∞ x` for `x : K`, and `@[simp] unitEmbedding_apply` rewrites the PR's LHS away. Finding filed.
- Proof cell: `finprod_comp_equiv` exists and ProductFormula.lean:48 uses it for this exact reindexing. Filed a compile finding.
- Better version: a hypothesis-free `x : K` statement (0 has norm 0 and 0⁻¹ = 0) would need `Nontrivial 𝔸ᶠ[K]`. I found no such instance, so I recommended `x ≠ 0` instead.

**`tprod_norm_of_isUnit`, `tprod_norm_of_unit`, `tprod_eq_zero_of_not_isUnit`, `norm_def_unit`, `norm_eq_zero_of_not_isUnit`**
- Group/siblings: these are pairwise the same fact modulo the `rfl` lemma `norm_def` or `.isUnit`. The exhibit is the PR's own proof terms. Filed a group finding and folded `norm_def_unit`'s misleading `_def` suffix into it.
- `norm_eq_zero_of_not_isUnit` matches the infinite sibling's name. Nothing further.

**`hasProd_zero_of_not_isUnit`**
- It mixes `x v` and `x.1 v`; folded into the coercion finding.
- Dropped: a proof-shortening idea, for lack of a compile argument I could make confident. Dropped: grind robustness, which had no warrant beyond taste.

**`mulSupport_finite`**
- Library and norms cell: `FinitePlace.mulSupport_finite` was deprecated on 2026-03-03 in favour of `hasFiniteMulSupport` with `@[fun_prop]` (FinitePlace.lean:436-445). mlcount gives 15 `hasFiniteMulSupport` names and 0 other `mulSupport_finite` names. Filed as blocking.

**`hasProd_subset_valued_lt_one` / `hasProd_zero_subset_one_lt_valued` (private)**
- Norms cell: the names are swapped relative to their sets, and inconsistent with `finite_valued_one_lt`. Filed with the `one_lt_norm_iff` / `norm_lt_one_iff` exhibits.
- Proof cell (`have : Fintype`): I searched for a `HasProd … ∏ᶠ` lemma and found none. Dropped.

**`finite_valued_one_lt`**
- Naming was folded into the finding above.
- Library cell: it is analogous to `HeightOneSpectrum.Support.finite` for elements of `K`. That was not strong enough to ask for a rename to "support", so I dropped it.

**`cofinite_mem_adicCompletionIntegers`**
- Library cell: `RestrictedProduct.eventually` (Basic.lean:124) is exactly `x.2`.
- Norms cell: `eventually_mem` has 24 hits and `cofinite_mem` has 1. Filed as advisory. It remains a legitimate transfer lemma, since `FiniteAdeleRing` is a `def` with its own coercion.

**`Valued.toNormedField.norm_eq_one_iff`**
- Automation: all six neighbouring comparison lemmas are `@[simp]`, and the PR's use sites have to name this one explicitly. Filed.
- Proof: a term-mode `▸`, where `le_antisymm_iff` plus the two neighbouring simp lemmas would do. Filed as compile, to verify.
- Library: no existing duplicate (grep for `norm_eq_one_iff`).

**`two_le_absNorm_nnreal`**
- The proof via `mod_cast one_lt_absNorm` is fine.
- The missing docstring, where all three neighbours have one, is not something maintainers require for lemmas. Dropped.

**`FinitePlace.two_le_norm_of_one_lt_norm`**
- Better-version cell: the proof passes through the sharper `absNorm v.asIdeal ≤ ‖x‖` and then weakens it. Filed as compile, advisory.
- Robustness: I could not verify whether `.trans` from ℝ≥0 into the ℝ goal relies on defeq. Dropped.

**Instance `Norm 𝔸ᶠ[K]`**
- Typeclass layer: `FiniteAdeleRing` is a `def` (Dedekind file:94), and there is no `Norm` on `RestrictedProduct` (grep), so there is no diamond.
- Intent: a `Norm` that is not a norm has precedent in `Norm K∞`. The `tprod` value is 0 off units, which the PR proves. No finding.
- Docstring: the infinite sibling has one. Folded into the prose finding.

**Notation move (AdeleRing.lean removed / FiniteAdeleRing.lean added)**
- Module graph: `AdeleRing.lean` does not import the new file, so `𝔸ᶠ[K]` disappears for anyone importing only AdeleRing.
- `K∞` shows the intended layering (its own file, `scoped[NumberField.AdeleRing]`, imported by AdeleRing). Filed.
- Within Mathlib nothing else uses `𝔸ᶠ[K]` (grep), so CI cannot catch the breakage.

**Imports in the new file**
- ProductFormula → FinitePlace → NormedValued makes two of the four imports redundant. Filed with exhibit.

**Import changes in `Completion/FinitePlace.lean`**
- Three public imports were removed and one reordered, none needed by the feature. Filed as a process judgment, recommending a split.
- The stray blank line is whitespace, which CI settles, so I skipped it.

**Module doc (new file)**
- Intent: it mentions a Dedekind domain `R` that does not occur in the file, and it lists no main definitions or results.
- Sibling files have `## Main definitions` (3 exhibits). Filed together with the instance docstring.

**Namespace/section/command objects**
- These are only scaffolding: `variable {R K}` / `variable (R K)` toggles and namespace openings. Nothing checkable beyond style, so dropped.

**`Mathlib.lean`**
- The import is in the correct alphabetical position, and CI checks that. No finding.

**PR as a whole**
- The description is only "depends on #35820". It has no motivation, no design rationale for `tprod` or the value on non-units, and no AI disclosure. Filed as an advisory judgment.
- #35820's lemmas (`unitsEquiv_finite_valued_eq_one`, `infinite_valued_ne_one_of_not_isUnit`) are already at base, lines 166-175.
