# Review notes: PR #33304, "doc(CategoryTheory): fix file refs"

This PR changes only documentation and comments in 13 files. For each object I checked two things: that every new file reference resolves in the reviewed workspace (`file_search` / `file_read`), and that the referenced file holds what the prose says it does. I also searched each touched file for remaining path references (`content_search` for `\.lean|X/Y`), and checked the declaration names in the edited paragraphs. I did not look at proof-golf, generalization or naming, because no Lean declaration changes. The only code-adjacent edits are the deprecation-message strings in BundledHom and UnbundledHom.

Convention context: `zulip_search` found the 2024-11 "Broken file references" thread, in which maintainers (Wieser, Dillies, Testa, Morrison) agree to spell module references as full `Mathlib/...lean` paths. The PR follows that convention.

## Object by object

- **StrictPseudofunctor.lean module doc (TODO).** `Mathlib/CategoryTheory/Bicategory/Functor/Strict.lean` exists and is a `deprecated_module (since := "2025-10-02")` stub that re-exports `Bicategory.Strict.Pseudofunctor`, so the TODO is accurate. No issue.
- **Bundled.lean module doc.** `ConcreteCategory/UnbundledHom.lean`, `ConcreteCategory/BundledHom.lean` and `ConcreteCategory/Basic.lean` all exist (the old `HasForget/` paths were stale). No issue.
- **`CategoryTheory.BundledHom` and `CategoryTheory.UnbundledHom` deprecation messages.** Only the path inside the string changes, and `ConcreteCategory/Basic.lean` exists. `since` is unchanged, which is correct. No issue.
- **Functor/Basic.lean comment before `Functor.map_comp_assoc`.** `Mathlib/Tactic/CategoryTheory/Reassoc.lean` exists and imports `Mathlib.CategoryTheory.Functor.Basic` (both `public import` and `public meta import`). The fix is correct. The tense ("we will import") is slightly dated, but that is not worth an ask. **Finding 2:** the same file still has a bare and stale `Whiskering.lean` reference at line 130. Three files have that name, and the unitors now live in `Functor/Category.lean`.
- **Subgroupoid.lean module doc.** `Mathlib/Algebra/Group/Subgroup/Basic.lean` and `Mathlib/Combinatorics/SimpleGraph/Subgraph.lean` exist. No issue.
- **FunctorCategory/Filtered.lean and FunctorCategory/Finite.lean module docs.** `Limits/FunctorCategory/Basic.lean`, `Limits/Filtered.lean` and `Limits/Shapes/FiniteProducts.lean` exist. FunctorCategory/Basic.lean imports only `Functor.Currying` and `Preserves.Limits`, so "shouldn't import" is accurate. No issue.
- **HasLimits.lean docstring before `colimit.ι_desc`.** `(see Mathlib/Tactic/CategoryTheory/Reassoc.lean)` replaces the long-dead `Tactic/reassoc_axiom.lean`, and is correct. I checked the file's other references: `Adjunction/Limits.lean` (l.447) and `Limits/ConeCategory.lean` with `hasLimitsOfShape_iff_isLeftAdjoint_const` (l.530-531) both resolve. **Finding 3:** l.446 names the Lean 3 identifiers `hasLimitCompEquivalence` / `hasLimitOfCompEquivalence`, which do not exist. The current names are `Adjunction.hasLimit_comp_equivalence` / `Adjunction.hasLimit_of_comp_equivalence`. This is outside the hunk and is a declaration reference rather than a file reference, so it is advisory only.
- **Preserves/Limits.lean module doc.** The directory `Mathlib/CategoryTheory/Limits/Preserves/Shapes/` exists, with BinaryProducts, Equalizers, Pullbacks, Products, Terminal and others. No issue.
- **Preserves/Over.lean module doc.** `Comma/Over/Pullback.lean` holds `Over.forgetAdjStar` and the `(forget X).IsLeftAdjoint` instance, so it is the right successor of the old `Adjunction/Over.lean`. The left-adjoint claim needs `[HasBinaryProducts C]`. I considered asking to point at `Limits/Over.lean` (`Over.createsColimitsOfSize`) instead. I did not file it: creation gives preservation only when the colimits exist, so the current text is a defensible fix and not a present error. The missing final period is pre-existing and not worth an ask.
- **Localization/Equivalence.lean module doc.** `Localization/Predicate.lean` exists and holds the target lemma. **Finding 1:** the paragraph the PR rewraps still names `Localization.of_equivalence_target`, `Localization.of_equivalence_source` and `Localization.of_equivalences`. None of these exist; the real names are `Functor.IsLocalization.*`. `Localization.isEquivalence` is correct.
- **Mon_.lean section doc (two edits).** `Monoidal/Braided/Basic.lean` defines `tensorμ` (l.597), `leftUnitor_monoidal`, `rightUnitor_monoidal` and `associator_monoidal` (l.723-751), so both edits are right. The file's other references, `Mathlib/Tactic/Attr/Register.lean` (which defines `mon_tauto`) and `Monoidal/Internal/Module.lean`, also resolve. No issue.

## Verification

I checked all three proposed edits with `lean_verify_edit` (line mode). Each returned `outcome: compiled` with no errors or warnings, and every new line is at most 93 characters. These are comment and doc edits, so compiling only shows that they do not break the file.

## Severity

All three findings are advisory, "while you're here" requests that fit the PR's stated purpose. The PR's own edits are all correct, and none is blocking.
