import json, sys
D = sys.argv[1]
F = []
F.append({
 "target": "Dense.continuous_lowerBounds",
 "claim": "`Dense.continuous_lowerBounds` repeats the proof of `Dense.continuous_upperBounds` line by line with `Ici`/`lowerBounds` in place of `Iic`/`upperBounds`. The file proves every GLB lemma from its LUB twin through `OrderDual` (`isGLB_iff_of_subset_of_subset_closure`, `Dense.isGLB_inter_iff`, `IsGLB.frequently_mem`, ...), so this copy is duplicated code.",
 "requested_change": "Replace the tactic proof with the dual term `hS.continuous_upperBounds (α := αᵒᵈ) hf`.",
 "severity": "advisory",
 "evidence": "Read the file at lines 40-167. Each GLB lemma there is proved as `... (α := αᵒᵈ) ...` from its LUB version. `lean_verify_edit` on `Dense.continuous_lowerBounds` with body `hS.continuous_upperBounds (α := αᵒᵈ) hf` returned success with no errors or warnings. precedent_search found a similar earlier review (PR #11200, ADedecker) that suggested exactly this `(α := αᵒᵈ)` dual proof for a copied lemma."
})
F.append({
 "target": "Dense.continuous_inf",
 "claim": "`Dense.continuous_inf` is a hand-dualised copy of `Dense.continuous_sup` (`sInf_range`/`isGLB_csInf`/`isGLB_ciInf_set` replacing the sup names). It does not use the `OrderDual` pattern the rest of the file follows.",
 "requested_change": "Prove it as `hS.continuous_sup (α := αᵒᵈ) hf h`.",
 "severity": "advisory",
 "evidence": "`lean_verify_edit` on `Dense.continuous_inf` with body `hS.continuous_sup (α := αᵒᵈ) hf h` returned success with no errors or warnings."
})
F.append({
 "target": "Dense.continuous_inf'",
 "claim": "`Dense.continuous_inf'` is a 15-line copy of `Dense.continuous_sup'` with every lemma replaced by its dual. That includes the fragile `h2` block (`range_comp'`, non-terminal `simp_all only`, `image_closure_subset_closure_image`).",
 "requested_change": "Prove it as `hS.continuous_sup' (α := αᵒᵈ) hf`.",
 "severity": "advisory",
 "evidence": "`lean_verify_edit` on `Dense.continuous_inf'` with body `hS.continuous_sup' (α := αᵒᵈ) hf` returned success with no errors or warnings."
})
F.append({
 "target": "Dense.continuous_sup'",
 "claim": "`Dense.continuous_sup'` duplicates code in two ways. In the `BddAbove` branch it re-runs the whole proof of `Dense.continuous_sup` (and the empty-type split) instead of calling it. In the unbounded branch, `h2` re-derives, via `range_comp'`, a non-terminal `simp_all only`, `BddAbove.closure` and `image_closure_subset_closure_image`, a fact that `Dense.continuous_upperBounds` already gives, because `BddAbove s` is by definition `(upperBounds s).Nonempty`.",
 "requested_change": "Replace the proof by:\n```\n  by_cases h : BddAbove (range f)\n  · exact hS.continuous_sup hf h\n  have h' : ¬BddAbove (range fun s : S ↦ f s) := by\n    rwa [← image_eq_range, BddAbove, hS.continuous_upperBounds hf]\n  rw [iSup, iSup, csSup_of_not_bddAbove h, csSup_of_not_bddAbove h']\n```",
 "severity": "advisory",
 "evidence": "`lean_verify_edit` on `Dense.continuous_sup'` with exactly this proof returned success with no errors or warnings. The empty-type case is no longer needed: the bounded branch delegates to `continuous_sup`, and the unbounded branch never needs nonemptiness. `Set.image_eq_range : f '' s = range fun x : s => f x` is in `Mathlib/Data/Set/Image.lean` (declaration_search / content_search)."
})
F.append({
 "target": "Dense.continuous_upperBounds",
 "claim": "The proof of `Dense.continuous_upperBounds` unfolds closure membership by hand (`mem_closure_iff_frequently`, `Frequently.mem_of_closed isClosed_Iic`) and uses `upperBounds_mono _ le_rfl` where `upperBounds_mono_set` is meant. The same argument already exists as `upperBounds_closure` (simp lemma in `Topology/Order/OrderClosed.lean`). The neighbouring `isLUB_iff_of_subset_of_subset_closure` uses that lemma for exactly this sandwich `s ⊆ t ⊆ closure s`.",
 "requested_change": "Replace the tactic proof by the term\n```\n  (upperBounds_closure (f '' S) ▸\n    upperBounds_mono_set (hf.range_subset_closure_image_dense hS)).antisymm <|\n    upperBounds_mono_set (image_subset_range f S)\n```\n(dropping the redundant `Set.` prefix, since `Set` is open).",
 "severity": "advisory",
 "evidence": "declaration_search: `upperBounds_closure` and `upperBounds_mono_set` exist at base (OrderClosed.lean:135, Order/Bounds/Basic.lean). The file's `isLUB_iff_of_subset_of_subset_closure` (line 151) has the same `upperBounds_closure ▸ upperBounds_mono_set` shape. `lean_verify_edit` with this term proof returned success with no errors or warnings. All lines are under 100 characters."
})
F.append({
 "target": "Dense.continuous_sup",
 "claim": "`Dense.continuous_sup` rewrites both sides with `← sSup_range` so it can apply `isLUB_csSup (range_nonempty f) h`, which is exactly `isLUB_ciSup h`. It then closes `f '' S ⊆ range f` with `by grind` where `image_subset_range f S` is the lemma.",
 "requested_change": "Drop the `sSup_range` rewrites and the `grind` call:\n```\n  cases isEmpty_or_nonempty γ\n  · simp [iSup_of_empty']\n  exact (isLUB_ciSup h).unique <| (isLUB_congr (hS.continuous_upperBounds hf)).mp <|\n    isLUB_ciSup_set (h.mono (image_subset_range f S)) hS.nonempty\n```",
 "severity": "advisory",
 "evidence": "`isLUB_ciSup [Nonempty ι] (H : BddAbove (range f)) : IsLUB (range f) (⨆ i, f i) := isLUB_csSup (range_nonempty f) H` (Order/ConditionallyCompleteLattice/Indexed.lean:90), and `isLUB_ciSup_set` (line 94) already concludes about `⨆ i : s, f i`. `lean_verify_edit` on `Dense.continuous_sup` with this proof returned success with no errors or warnings."
})
F.append({
 "target": "Dense.continuous_upperBounds",
 "claim": "The name `Dense.continuous_upperBounds` leads with `continuous_`, which names a hypothesis, not the conclusion. The conclusion is the equality `upperBounds (f '' S) = upperBounds (range f)`, and the library's lemmas about `upperBounds` all start with `upperBounds_`.",
 "requested_change": "Rename to `Dense.upperBounds_image`, and the twin `Dense.continuous_lowerBounds` to `Dense.lowerBounds_image`. Update the uses in the `sup`/`inf` lemmas.",
 "severity": "blocking",
 "evidence": "naming_norm(`Dense.continuous_upperBounds`): verdict `established`, subject `upperBounds`, 27/27 base declarations use the `upperBounds_` prefix and 0 use `continuous_`. Candidate names were `Dense.upperBounds_image` and `Dense.upperBounds_upperBounds`. A line-mode `lean_verify_edit` replacing lines 169-261 with the renamed block (both bounds lemmas renamed, callers updated) returned success."
})
F.append({
 "target": "Dense.continuous_sup",
 "claim": "`Dense.continuous_sup` (and `Dense.continuous_inf`, `Dense.continuous_sup'`, `Dense.continuous_inf'`) is named as if it concerned continuity of the binary `⊔`/`⊓`. `continuous_sup`/`continuous_inf` are existing root lemmas (`Continuous fun p : L × L => p.1 ⊔ p.2`, Topology/Order/Lattice.lean), and `sup` in Mathlib names binary `⊔`. The statement is actually an equality of conditionally complete indexed suprema `⨆ i, f i = ⨆ s : S, f s`, which the library spells `ciSup`/`ciInf`.",
 "requested_change": "Rename the four lemmas to use `ciSup`/`ciInf` and drop the hypothesis-naming `continuous_` prefix. For example: `Dense.ciSup_eq_ciSup_subtype`, `Dense.ciInf_eq_ciInf_subtype`, `Dense.ciSup_eq_ciSup_subtype'`, `Dense.ciInf_eq_ciInf_subtype'`. Update the PR description to match.",
 "severity": "blocking",
 "evidence": "declaration_search(`continuous_sup`): declared at base in `Mathlib/Topology/Order/Lattice.lean` (`theorem continuous_sup [Max L] [ContinuousSup L] : Continuous fun p : L × L => p.1 ⊔ p.2`), and also matched by this PR's `Dense.continuous_sup`. Likewise for `continuous_inf`. The conditionally complete lemmas used in the proof are all `ciSup`-named (`isLUB_ciSup`, `isLUB_ciSup_set`, `ciSup_subtype`). naming_norm could not resolve a subject for these declarations (`subject_unresolved`), so the specific replacement name is my judgement. A line-mode `lean_verify_edit` of the whole block with these names returned success."
})
F.append({
 "target": "Dense.continuous_upperBounds",
 "claim": "The docstring of `Dense.continuous_upperBounds` (and its `lowerBounds` twin) is ungrammatical and misleading. It says \"The upper bounds ... is equal to\", and \"the upper bounds of the range of the universe\" conflates range and image: `range f` is already over the whole domain. The `sup`/`inf` docstrings likewise say \"supremum on the universe\".",
 "requested_change": "Reword, e.g. \"If `f` is continuous and `S` is dense, then `f '' S` and `range f` have the same upper bounds.\" (dually for lower bounds). Reword the `sup`/`inf` docstrings as \"The supremum of a continuous function that is bounded above equals its supremum over any dense set.\" (dually for infimum).",
 "severity": "advisory",
 "evidence": "Docstrings read from diff.patch, lines 169-170, 181-182, 193-194 and 206-207 of the reviewed file. The reworded docstrings were part of the block that compiled in the line-mode `lean_verify_edit` (success)."
})
F.append({
 "target": "Dense.continuous_sup",
 "claim": "`Dense.continuous_sup` and `Dense.continuous_upperBounds` are stated only for the inclusion of a dense subset. The argument works unchanged for any map `g : β → γ` with `DenseRange g`, which is the reusable form in which Mathlib states such results (compare `Function.Surjective.iSup_comp`). The `Dense S` statement is then the special case `hS.denseRange_val`.",
 "requested_change": "State the core results for `DenseRange g`: `DenseRange.upperBounds_range_comp : upperBounds (range (f ∘ g)) = upperBounds (range f)` and `DenseRange.ciSup_comp : ⨆ b, f (g b) = ⨆ i, f i` (under `BddAbove (range f)`). Derive the `Dense S` versions as one-liners via `Dense.denseRange_val`, e.g. `(hS.denseRange_val.ciSup_comp hf h).symm`.",
 "severity": "advisory",
 "evidence": "declaration_search: `Dense.denseRange_val` exists (Topology/Continuous.lean), `Function.Surjective.iSup_comp` exists (Order/CompleteLattice/Basic.lean), and `DenseRange.ciSup_comp` does not exist. A line-mode `lean_verify_edit` inserted after the PR's block: `DenseRange.upperBounds_range_comp` (proof `rw [range_comp]; exact Dense.continuous_upperBounds hg hf`), `DenseRange.ciSup_comp` (empty case via `IsEmpty β`, then `(isLUB_ciSup (h.mono (range_comp_subset_range g f))).unique <| (isLUB_congr (hg.upperBounds_range_comp hf)).mpr (isLUB_ciSup h)`), and an `example` recovering `Dense.continuous_sup` as `(hS.denseRange_val.ciSup_comp hf h).symm`. The first attempt failed on an empty-case lemma name; the corrected version returned success with no errors or warnings."
})
json.dump(F, open(D + "/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(F))
