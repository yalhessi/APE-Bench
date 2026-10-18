import json
F = []
def add(target, claim, change, sev, ev):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev, "evidence": ev})

add("Submonoid.closure_image_isMulIndecomposable_baseOf",
    "The PR renames `Submonoid.closure_image_one_lt_and_isMulIndecomposable` (and, via `to_additive`, its additive counterpart) to `Submonoid.closure_image_isMulIndecomposable_baseOf` without leaving a deprecated alias, so downstream code that uses the old name breaks without warning.",
    "Add a deprecated alias right after the lemma, e.g.\n```lean\n@[to_additive (attr := deprecated (since := \"<date>\"))]\nalias Submonoid.closure_image_one_lt_and_isMulIndecomposable :=\n  Submonoid.closure_image_isMulIndecomposable_baseOf\n```",
    "blocking",
    "declaration_search: `Submonoid.closure_image_one_lt_and_isMulIndecomposable` is declared at Indecomposable.lean:46 before this PR. content_search for `closure_image_one_lt_and_is|closure_image_zero_lt_and_is|deprecated` over the PR's tree finds no matches, so there is no alias. lean_verify_edit inserting the alias above after the lemma (line mode, lines 113-114): outcome `compiled`.")

add("IsMulIndecomposable.pairwise_div_notMem_range'",
    "`pairwise_div_notMem_range'` duplicates `pairwise_baseOf_div_notMem`: its hypothesis `hst : s ⊆ IsMulIndecomposable v {i | 1 < f (v i)}` says `s ⊆ baseOf v f`, so its conclusion is just `(pairwise_baseOf_div_notMem v hv_inv f hf).mono hst`. The only use is the one-line proof of `pairwise_baseOf_div_notMem`. It also adds a primed name to the API.",
    "Delete `pairwise_div_notMem_range'` and prove `pairwise_baseOf_div_notMem` directly from `pairwise_div_notMem_range`:\n```lean\n@[to_additive]\nlemma pairwise_baseOf_div_notMem [InvolutiveInv ι] [CommGroup S] [IsOrderedMonoid S]\n    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)\n    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :\n    (baseOf v f).Pairwise fun i j ↦ v i / v j ∉ range v :=\n  pairwise_div_notMem_range v (fun i h ↦ hf i (by simp [h])) hv_inv _ _ subset_rfl\n    fun i ↦ by simpa [hv_inv] using (hf i).symm\n```",
    "advisory",
    "lean_verify_edit replaced lines 160-175 (both lemmas) with the single lemma above. Outcome `compiled`, no new errors or warnings. BaseExists.lean uses only `IsAddIndecomposable.pairwise_baseOf_sub_notMem` (diff line `have := IsAddIndecomposable.pairwise_baseOf_sub_notMem ...`), never the primed lemma.")

add("IsMulIndecomposable.baseOf",
    "`baseOf` is declared as a `Set ι` but its body `IsMulIndecomposable v {i | 1 < f (v i)}` is a partially applied predicate `ι → Prop`. This relies on the definitional equality `Set ι = ι → Prop`, which Mathlib asks not to exploit. The same happens in `pairwise_div_notMem_range` (`hst : s ⊆ IsMulIndecomposable v t`) and `pairwise_div_notMem_range'`, while `IsMulIndecomposable.subset` in the same PR writes the set properly as `{i | IsMulIndecomposable v s i}`.",
    "Define `baseOf v f := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}`, and state the hypotheses as `hst : s ⊆ {i | IsMulIndecomposable v t i}` (or `s ⊆ baseOf v f` where that is what is meant).",
    "advisory",
    "lean_verify_edit with `def IsMulIndecomposable.baseOf ... : Set ι := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}`: outcome `compiled`, and every later lemma in the file still elaborates. lean_verify_edit replacing line 146 with `(hst : s ⊆ {i | IsMulIndecomposable v t i})`: outcome `compiled`.")

add("IsMulIndecomposable.image_baseOf_inv_comp_eq",
    "The lemma writes the pointwise inverse of `f : G →* S` as `invMonoidHom.comp f`, although Mathlib already has `f⁻¹` (the `Inv (M →* G)` instance, with simp lemma `MonoidHom.inv_apply`). Because of this the proof needs a four-step `rw` chain through the new `invMonoidHom_comp_invMonoidHom`, `MonoidHom.comp_assoc` and `MonoidHom.coe_comp` to get from `invMonoidHom.comp (invMonoidHom.comp f)` back to `f`.",
    "State it with `f⁻¹`, e.g. `lemma image_baseOf_inv_eq ... : v '' baseOf v f⁻¹ = (invMonoidHom ∘ v) '' baseOf v f`. Replace the symmetric step with `simpa [image_comp, image_image] using image_mono (f := invMonoidHom) <| this f⁻¹`, and use `let f' : G →* S := f⁻¹` in `Subgroup.closure_image_isMulIndecomposable_baseOf`. After this change the PR no longer needs `invMonoidHom_comp_invMonoidHom`.",
    "advisory",
    "Hom/Basic.lean:270-273 has `instance : Inv (M →* G)` and `@[to_additive (attr := simp)] lemma inv_apply (f : M →* G) (x : M) : f⁻¹ x = (f x)⁻¹`. lean_verify_edit (line mode, lines 57-136) replaced the image lemma with the `f⁻¹` version, whose first block is `refine subset_antisymm (this f) ?_; simpa [image_comp, image_image] using image_mono (f := invMonoidHom) <| this f⁻¹`, and in the Subgroup lemma replaced `invMonoidHom.comp f` with `f⁻¹` and the lemma name. Outcome `compiled`, no warnings.")

add("IsMulIndecomposable.baseOf",
    "The additive docstring has a typo, \"crystallogrphic\". The multiplicative docstring (\"The \\\"base\\\" of a set of points of a monoid relative to a morphism `f`.\") never says which set this is: the members of `v` with `1 < f (v i)` that are indecomposable within that half-space.",
    "Fix the spelling to \"crystallographic\". Expand both docstrings to state the definition, e.g. \"The set of indices `i` with `1 < f (v i)` such that `v i` is indecomposable with respect to the points of `v` in this half space.\"",
    "advisory",
    "Read from the PR's file at Indecomposable.lean:44-50: `In the case that `v` is the set of roots of a crystallogrphic root system, ...`.")

add("IsMulIndecomposable.mem_or_inv_mem_closure_baseOf",
    "The lemma asks for `hf : ∀ i, f (v i) ≠ 1` but the proof only uses `hf i` for the `i` in the conclusion (`lt_or_gt_of_ne (hf i)`), so the hypothesis is stronger than needed. The statement is also padded with alignment spaces (`     v i    ∈ ...`).",
    "Weaken the hypothesis to the one point, `(i : ι) (hf : f (v i) ≠ 1)`, and write the conclusion without the alignment padding: `v i ∈ Submonoid.closure (v '' baseOf v f) ∨ (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f)`. The case split can then be `rcases hf.lt_or_gt with hi | hi`.",
    "advisory",
    "lean_verify_edit with `(f : G →* S) {i : ι} (hf : f (v i) ≠ 1) : v i ∈ ... ∨ (v i)⁻¹ ∈ ...` and `rcases hf.lt_or_gt with hi | hi` (rest of the proof unchanged): outcome `compiled`. Nothing in the PR calls this lemma; the BaseExists TODO only mentions it.")

add("RootPairing.baseOf_pairwise_pairing_le_zero",
    "The name says `pairing`, but the statement is about `P.pairingIn ℤ i j`, and `RootPairing.pairing` is a different function in the same namespace. The word order (`baseOf_pairwise_...`) is also the reverse of the lemma it is proved from, `IsAddIndecomposable.pairwise_baseOf_sub_notMem`. The analogous lemma for a `Base`, `RootPairing.Base.pairingIn_le_zero_of_ne`, uses `pairingIn_le_zero`.",
    "Rename it to `pairwise_baseOf_pairingIn_le_zero` (and update the call in `linearIndepOn_root_baseOf'`).",
    "advisory",
    "Base.lean:275 `lemma pairingIn_le_zero_of_ne ... : P.pairingIn ℤ i j ≤ 0`. Indecomposable.lean:171 `pairwise_baseOf_div_notMem` (additive `pairwise_baseOf_sub_notMem`). naming_norm on this declaration: insufficient_evidence (no population for subject `baseOf`), so this rests on the siblings, not on a census.")

add("Mathlib/LinearAlgebra/RootSystem/BaseExists.lean",
    "The `CommRing` section declares `{S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)` as section variables. Only `baseOf_pairwise_pairing_le_zero` uses them; the next lemma, `linearIndepOn_root_baseOf'`, rebinds `{S : Type*}` with different instances and `(f : Dual S M)`, shadowing the section's `S` and `f`.",
    "Leave only `[CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)` in the section `variable`. Move `{S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)` into the signature of `baseOf_pairwise_pairing_le_zero` (or use `variable ... in`).",
    "advisory",
    "lean_verify_edit (line mode, lines 52-63) with the section variable reduced to `P` and the `S`/`f` binders moved into `baseOf_pairwise_pairing_le_zero {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S) [CharZero R] ...`: outcome `compiled`, and the call `P.baseOf_pairwise_pairing_le_zero _ hf ...` in `linearIndepOn_root_baseOf'` still elaborates.")

add("Mathlib/LinearAlgebra/RootSystem/BaseExists.lean",
    "The import `Mathlib.Algebra.Module.Submodule.Union` is unused. Its only connection to the file is the TODO's mention of `Module.exists_dual_forall_apply_ne_zero`, and nothing in the file needs it to compile.",
    "Remove `public import Mathlib.Algebra.Module.Submodule.Union`. Add it back when the TODO that uses `Module.exists_dual_forall_apply_ne_zero` is done.",
    "advisory",
    "lean_verify_edit deleting line 9 (`public import Mathlib.Algebra.Module.Submodule.Union`): outcome `compiled`. Deleting line 10 (OrzechProperty) or line 11 (QuadraticForm.Dual) instead fails (`Unknown identifier linearIndependent_iff_card_eq_finrank_span`, `Unknown constant LinearMap.BilinForm.linearIndependent_of_pairwise_le_zero`), so those two are needed. declaration_search puts `Module.exists_dual_forall_apply_ne_zero` in Mathlib/Algebra/Module/Submodule/Union.lean:113.")

add("Mathlib/Algebra/Group/Irreducible/Indecomposable.lean",
    "Two of the imports this PR adds to a low-level algebra file are redundant: `Mathlib.Algebra.Group.Subgroup.Lattice` (already available through `Subgroup.Pointwise`) and `Mathlib.Algebra.Order.Group.Basic`.",
    "Drop `public import Mathlib.Algebra.Group.Subgroup.Lattice` and `public import Mathlib.Algebra.Order.Group.Basic`. Keep `Subgroup.Pointwise` and `Order.Group.Defs`.",
    "advisory",
    "lean_verify_edit (line mode, lines 9-13) leaving only `Subgroup.Pointwise`, `Submonoid.Basic`, `Order.Group.Defs`: outcome `compiled`, no warnings. Deleting `Order.Group.Defs` (line 12) alone fails with unsolved goals in `Subgroup.closure_image_isMulIndecomposable_baseOf`, so that import is needed.")

add("Mathlib/LinearAlgebra/RootSystem/BaseExists.lean",
    "The module docstring has the title \"Existence of bases for crystallographic root systems\", but it does not say what the file actually proves. The file does not prove existence: it proves `baseOf_pairwise_pairing_le_zero`, `linearIndepOn_root_baseOf'` and `linearIndepOn_root_baseOf`, and existence is only in the TODO. The docstring also has a garbled phrase, \"even though the existence ultimate statement does not\".",
    "Add a short summary or `## Main results` section listing `RootPairing.baseOf_pairwise_pairing_le_zero` and `RootPairing.linearIndepOn_root_baseOf`, and say that existence of a base is left as the TODO. Reword the phrase to \"even though the ultimate existence statement does not\".",
    "advisory",
    "Read from the module docstring in diff.patch (BaseExists.lean lines 14-40): sections `Implementation details` and `TODO` only; the sentence is `The proof needs a set of ordered coefficients, even though the existence ultimate statement does not.`")

add("IsMulIndecomposable.subset",
    "`aesop` is used to prove a statement that is just the first projection of the definition `IsMulIndecomposable v s i := i ∈ s ∧ ...`.",
    "Replace the proof with the term `fun _ h ↦ h.1`.",
    "advisory",
    "lean_verify_edit with `@[to_additive] protected lemma IsMulIndecomposable.subset (v : ι → M) (s : Set ι) : {i | IsMulIndecomposable v s i} ⊆ s := fun _ h ↦ h.1`: outcome `compiled`, no warnings.")

json.dump(F, open('findings.json','w'), ensure_ascii=False, indent=1)
print(len(F))
