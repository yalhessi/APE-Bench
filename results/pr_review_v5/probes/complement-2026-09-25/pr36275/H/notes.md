# PR 36275 — reviewer H notes (one entry per dossier object)

Tool results that mattered most:
- InfiniteAdeleRing.lean:110-130. The K∞ sibling has the same `Norm`-instance design, `norm_def` in `x v` form, and `coe_norm_eq_abs_norm (x : K)` stated through algebraMap.
- CanonicalEmbedding/Basic.lean:415-458. `mixedEmbedding.norm` is bundled as `→*₀ ℝ` with `norm_eq_zero_iff` and `@[simp] norm_eq_norm (x : K)`.
- RingTheory/DedekindDomain/FiniteAdeleRing.lean:103-193. It has the DFunLike coe and `@[simp] unitEmbedding_apply`.
- Three compiles. A0: the PR form plus an example gives "simp argument unused: algebraMap_apply". A: the `x v` refactor plus `coe_norm_eq_inv_abs_norm` introduces no new errors. C: `@[simp] norm_eq_one_iff` compiles.

Compile caveat for the new file: the environment resolves imports against base build products. The new file therefore shows 8 pre-existing errors, all on names the PR adds in other files; none is on my edits.

1. **theorem `NumberField.FiniteAdeleRing.norm_def`**. Siblings: I compared it with K∞ `norm_def` (`x v`) and the DFunLike API. The PR uses `x.1 v`, and compiles A0/A show that simp lemmas miss this form. Filed (finding 2).
2. **theorem `unitEmbedding_norm_eq_inv_abs_norm`**. Library and generality: the LHS is not simp-normal (`unitEmbedding_apply` is @[simp]), and both siblings state this through the ring map on all of K. Compile A verified an algebraMap version with `x ≠ 0`. Filed (finding 1). I dropped the all-x version: it needs `Nonempty (HeightOneSpectrum (𝓞 K))`, and my search found no such instance.
3. **section (added), NF/FiniteAdeleRing.lean**. Structural only; nothing to ask.
4. **theorem `unitEmbedding_norm_apply_eq_finprod_finitePlace`**. Covered by finding 1 (restate in algebraMap form, or make private). It is a reasonable bridge to `FinitePlace.prod_eq_inv_abs_norm`, so I did not ask to delete it.
5. **theorem `tprod_norm_of_isUnit`**. Siblings: it duplicates `norm_def_unit`/`tprod_norm_of_unit` modulo the rfl `norm_def`. Filed (finding 3). Its `x.1 v` spelling is folded into finding 2.
6. **attribute (added), NF/FiniteAdeleRing.lean** (`@[expose] public section` / `open … in`). Matches the sibling files; nothing to ask.
7. **section (added), RingTheory/DedekindDomain/FiniteAdeleRing.lean** (`variable {R K}` … `variable (R K)`). Location looked fine next to the notation and before algebraMap. Nothing to ask.
8. **lemma `FinitePlace.two_le_norm_of_one_lt_norm`**. Generality: the proof actually shows `absNorm v ≤ ‖x‖`, a sharper statement. I considered asking for it but dropped it: the only consumer needs `2 ≤`, and the NNReal/ℝ coercion shape made a clean compile uncertain. Location in FinitePlace.lean is right.
9. **theorem `tprod_eq_zero_of_not_isUnit`**. It duplicates `norm_eq_zero_of_not_isUnit`, which is literally this term. Filed as part of finding 3.
10. **lemma `IsDedekindDomain.FiniteAdeleRing.cofinite_mem_adicCompletionIntegers`**. Library: it is `a.2`. I searched RestrictedProduct/Basic.lean for a named `eventually`/membership lemma and found only `exists_inclusion_eq_of_eventually`. The lemma fills a gap, so nothing to ask.
11. **import (modified), Completion/FinitePlace.lean**. PR as a whole: an unrelated import cleanup (three removals, a moved line, a double blank). Filed as advisory split/justify (finding 8).
12. **module_doc (added), NF/FiniteAdeleRing.lean**. Wording is the other reviewer's job. It has no "Main definitions/results" section while its siblings do, but that is docstring territory, so I dropped it.
13. **section (added), NF/FiniteAdeleRing.lean**. Structural; nothing.
14. **import in `Mathlib.lean`**. It correctly adds the new module; nothing.
15. **theorem `Valued.toNormedField.norm_eq_one_iff`**. Library: `declaration_search` shows no existing valued-field version (only the Complex and Zsqrtd namesakes). Siblings: all six neighbouring iffs are @[simp] and this one is not. Compile C ok. Filed (finding 5).
16. **section (added), RingTheory FiniteAdeleRing.lean**. Same block as item 7; nothing.
17. **namespace (added), NF/FiniteAdeleRing.lean** (`NumberField`). Nothing.
18. **namespace (added), NF/FiniteAdeleRing.lean** (`AdeleRing`, holding the notation). See item 19.
19. **command (added): scoped notation `𝔸ᶠ[K]` in the new file**. Location: moved out of AdeleRing.lean, whose file does not import the new one. A notation cannot be deprecated. Filed (finding 6).
20. **private theorem `hasProd_subset_valued_lt_one`**. It is a proof-internal helper and correctly private. Nothing.
21. **command (removed): notation in AdeleRing.lean**. Same issue as item 19 (finding 6). `content_search` found no in-tree users of `𝔸ᶠ[K]`, so the breakage would be downstream only.
22. **instance `Norm 𝔸ᶠ[K]`**. Typeclass: `FiniteAdeleRing` is a `def`, and RestrictedProduct has no Norm (I searched), so there is no diamond. It is consistent with the K∞ Norm instance. Encoding/API: there is no multiplicativity and no zero-iff; `mixedEmbedding.norm` is bundled `→*₀`. Filed advisory (finding 4), plus the `x.1 v` spelling (finding 2).
23. **theorem `hasProd_zero_of_not_isUnit`**. Uses `x v`, which is right; it is the evidence of the mixed spelling in finding 2. Nothing separate.
24–26. **namespace/namespace/section (added)**. Structural; nothing.
27. **theorem `mulSupport_finite`**. Stated for `𝔸ᶠ[K]ˣ` while its only caller passes `hx.unit`. It is a minor candidate for an IsUnit form, covered by the finding 3 consolidation. It needs `norm_eq_one_iff` in simp by hand, which finding 5 addresses.
28. **doc_comment (added): notation docstring**. Wording is the other reviewer's job. Nothing.
29. **lemma `two_le_absNorm_nnreal`**. Location: next to `one_lt_absNorm_nnreal`, which is right. The ℕ analogue is `one_lt_absNorm` itself (in ℕ, `1 < n` is `2 ≤ n`), so no sibling is missing. Nothing.
30. **private theorem `hasProd_zero_subset_one_lt_valued`**. A proof-internal helper and correctly private. Nothing.
31. **namespace (added)**. Nothing.
32. **theorem `unitEmbedding_norm_apply`**. Same simp-normal-form issue as item 2 (finding 1). It is also one of two finprod restatements; I kept it in finding 1 rather than asking for deletion.
33. **namespace (added)**. Nothing.
34. **doc_comment (removed), AdeleRing.lean**. It travelled with the notation (finding 6). Nothing separate.
35. **theorem `IsDedekindDomain.FiniteAdeleRing.finite_valued_one_lt`**. It is the adelic analogue of `HeightOneSpectrum.Support.finite`, in the right file. Its sibling `unitsEquiv_finite_valued_eq_one` is phrased with `∀ᶠ … cofinite` rather than `Set.Finite`, which is a mild inconsistency. I dropped it because both forms are used and it is not worth the churn.
36. **theorem `norm_eq_zero_of_not_isUnit`**. Consistent with the K∞ sibling's name and statement. The iff with `¬IsUnit` is missing and was raised in finding 4. The body duplicates `tprod_eq_zero_of_not_isUnit` (finding 3).
37. **theorem `tprod_norm_of_unit`**. It is `tprod_norm_of_isUnit x.isUnit`. Filed under finding 3.
38. **theorem `norm_def_unit`**. It is `tprod_norm_of_unit x`, the same statement in ‖·‖ form. Filed under finding 3.

**PR as a whole.** The description is only a dependency line: no motivation, no design rationale, no notation-move note, no AI disclosure. Filed as advisory (finding 9). The unrelated FinitePlace import reshuffle is finding 8. I dropped Zulip (no design discussion found for the finite-adele norm) and `precedent_search` (hits were unrelated normed-group comments).
