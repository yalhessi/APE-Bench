import json, sys
out = sys.argv[1]
F = []
def add(target, claim, change, severity, evidence):
    F.append({"target": target, "claim": claim, "requested_change": change,
              "severity": severity, "evidence": evidence})

add("Submonoid.closure_image_isMulIndecomposable_baseOf",
    "This PR renames `Submonoid.closure_image_one_lt_and_isMulIndecomposable` (and, through `to_additive`, its additive counterpart) to `Submonoid.closure_image_isMulIndecomposable_baseOf` and leaves no deprecated alias. The old names are public declarations at the base commit, so removing them without deprecation breaks downstream code, which the deprecation policy forbids.",
    "Directly after the lemma, add deprecated aliases for both old names, e.g.\n\n@[deprecated (since := \"2025-12-26\")]\nalias Submonoid.closure_image_one_lt_and_isMulIndecomposable :=\n  Submonoid.closure_image_isMulIndecomposable_baseOf\n\n@[deprecated (since := \"2025-12-26\")]\nalias AddSubmonoid.closure_image_pos_and_isAddIndecomposable :=\n  AddSubmonoid.closure_image_isAddIndecomposable_baseOf\n\n(use the merge date and whatever additive name `to_additive` generated for the old lemma).",
    "blocking",
    "declaration_search: `Submonoid.closure_image_one_lt_and_isMulIndecomposable` is declared at the base commit and not in the PR's files, so it is removed with no alias. content_search over target/Mathlib finds no remaining uses of either old spelling. lean_verify_edit inserting the two plain `@[deprecated (since := ...)] alias` lines after the lemma (line 114): success, no warnings. The form `@[to_additive (attr := deprecated (since := ...))] alias` also compiles, but warns '`[deprecated]` attribute should specify either a new name or a deprecation message'.")

add("Subgroup.closure_image_isMulIndecomposable_baseOf",
    "The 15-line proof splits `univ` into the two half-spaces, introduces `f' := invMonoidHom.comp f`, and rewrites with `IsMulIndecomposable.image_baseOf_inv_comp_eq`, `coe_invMonoidHom`, `image_inv_eq_inv` and `closure_inv`. The PR's own `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` already says that each `v i` or `(v i)⁻¹` lies in `Submonoid.closure (v '' baseOf v f)`, and that settles the lemma at once. `image_baseOf_inv_comp_eq` (15 lines) is used only here, and the new `invMonoidHom_comp_invMonoidHom` is used only by that lemma.",
    "Move the lemma below `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf`, which depends only on the Submonoid lemma, and prove it with\n\n  refine le_antisymm (closure_mono (image_subset_range _ _)) ((closure_le _).mpr ?_)\n  rintro - ⟨i, rfl⟩\n  rcases IsMulIndecomposable.mem_or_inv_mem_closure_baseOf v hv_inv f hf i with h | h\n  · exact le_closure_toSubmonoid _ h\n  · simpa using (closure _).inv_mem (le_closure_toSubmonoid _ h)\n\nThen delete `IsMulIndecomposable.image_baseOf_inv_comp_eq`, and with it the reason for `invMonoidHom_comp_invMonoidHom`. If the reflection lemma is wanted as API, state it on index sets (`i⁻¹ ∈ baseOf v f ↔ i ∈ baseOf v (invMonoidHom.comp f)`), where it has a 7-line proof, and not as an equation of images through `invMonoidHom ∘ v`.",
    "advisory",
    "lean_verify_edit replacing lines 57-190 (delete `image_baseOf_inv_comp_eq`; keep the Submonoid lemma and the `IsMulIndecomposable` namespace block verbatim; put the Subgroup lemma after `end IsMulIndecomposable` with the 5-line proof above): success, and every `to_additive` counterpart builds too. The same restructure with the imports cut to `Subgroup.Lattice`, `Submonoid.Basic`, `Order.Group.Defs`, `Order.Monoid.Defs`, `Preorder.Finite` (no `Subgroup.Pointwise`, no `Order.Group.Basic`) also succeeds. The index-level variant (`inv_mem_baseOf_iff`, and `image_baseOf_inv_comp_eq` rederived from it in 6 lines) also compiled with the whole file, once `baseOf` is written as a set-builder (see the `baseOf` finding).")

add("IsMulIndecomposable.baseOf",
    "`baseOf` is defined as `IsMulIndecomposable v {i | 1 < f (v i)}`, a predicate `ι → Prop` used as a `Set ι` through definitional unfolding. The binders `hst : s ⊆ IsMulIndecomposable v t` in `pairwise_div_notMem_range` and `hst : s ⊆ IsMulIndecomposable v {i | 1 < f (v i)}` in `pairwise_div_notMem_range'` do the same, while `IsMulIndecomposable.subset` in the same PR writes `{i | IsMulIndecomposable v s i}`. The abuse makes membership opaque to `simp`: after unfolding `baseOf`, `i ∈ baseOf v f` stays stuck as `i ∈ IsMulIndecomposable v {..}`.",
    "Define `baseOf v f := {i | IsMulIndecomposable v {j | 1 < f (v j)} i}` and write the `hst` hypotheses as `s ⊆ {i | IsMulIndecomposable v t i}`, or `s ⊆ baseOf v f` for the primed lemma, so that the Set/predicate conversion is explicit everywhere.",
    "advisory",
    "lean_verify_edit replacing the def body with the set-builder form: success, and the whole file (including the additive versions) still builds. With the PR's body, `simp only [baseOf, IsMulIndecomposable, mem_setOf_eq, ...]` left the goal `i⁻¹ ∈ IsMulIndecomposable v {i | 1 < f (v i)} ↔ i ∈ IsMulIndecomposable v {i | f (v i) < 1}`, and adding `mem_def` did not unfold it either (the next `refine` failed). With the set-builder body the same `simp only` unfolds fully, and the index-level lemma `inv_mem_baseOf_iff` is proved in 7 lines.")

add("IsMulIndecomposable.baseOf",
    "The `to_additive` docstring has a typo, \"crystallogrphic\". The multiplicative docstring (\"The \\\"base\\\" of a set of points of a monoid relative to a morphism `f`\") never says which set it is.",
    "Fix the spelling to \"crystallographic\". Make the multiplicative docstring say what the set is, e.g. \"the set of `i` such that `v i` is indecomposable among the points of `v` lying in the half-space `1 < f (v i)`\", and do the same for the additive docstring.",
    "advisory",
    "Read Indecomposable.lean lines 44-50 via file_read: line 47 reads 'crystallogrphic root system'.")

add("IsMulIndecomposable.pairwise_div_notMem_range'",
    "`pairwise_div_notMem_range'` (any `s ⊆ baseOf`) is exactly `pairwise_baseOf_div_notMem` followed by `Set.Pairwise.mono`. Its only use is to prove `pairwise_baseOf_div_notMem` with `s := baseOf v f`, so the PR adds two lemmas where one would do.",
    "Delete `pairwise_div_notMem_range'` (and its additive version) and prove `pairwise_baseOf_div_notMem` directly:\n\n  pairwise_div_notMem_range v (fun i h ↦ hf i (by simp [h])) hv_inv _ _ (.refl _)\n    fun i ↦ by simpa [hv_inv] using (hf i).symm",
    "advisory",
    "content_search: the primed lemma and `pairwise_sub_notMem_range'` are used nowhere but line 175. lean_verify_edit replacing lines 160-175 (the primed lemma plus `pairwise_baseOf_div_notMem`) with just `pairwise_baseOf_div_notMem`, proved as above: success; BaseExists uses only `IsAddIndecomposable.pairwise_baseOf_sub_notMem`, which is unchanged.")

add("IsMulIndecomposable.pairwise_div_notMem_range",
    "The `s` and `hst : s ⊆ IsMulIndecomposable v t` arguments add nothing that `Set.Pairwise.mono` does not already give. They also force a `h_sub` detour, and each case of the proof is a `suffices ¬ IsMulIndecomposable v t _` plus a 7-lemma `simp only` that unfolds the definition backwards.",
    "State the lemma for the maximal set, `{i | IsMulIndecomposable v t i}.Pairwise fun i j ↦ v i / v j ∉ range v`, with arguments `(v) (hv_one) (hv_inv) (t) (hv_t)`, and use the direct proof\n\n  intro i hi j hj hne\n  by_contra! ⟨k, hk⟩\n  rcases hv_t k with hk' | hk'\n  · simpa [hv_one] using hi.2 k hk' j hj.1 (by simp [hk])\n  · simpa [hv_one] using hj.2 k⁻¹ hk' i hi.1 (by simp [hv_inv, hk])",
    "advisory",
    "lean_verify_edit replacing lines 140-175 with this statement and proof, `pairwise_div_notMem_range'` removed and `pairwise_baseOf_div_notMem := pairwise_div_notMem_range v (fun i h ↦ hf i (by simp [h])) hv_inv _ fun i ↦ by simpa [hv_inv] using (hf i).symm`: success for the whole file, additive versions included.")

add("section in Indecomposable.lean",
    "The new variable line `variable {ι M G S : Type*} [Monoid M] [CommGroup G] [LinearOrder S]` makes every new `G`-lemma assume commutativity of `G`. Nothing in the statements needs it: the only uses are `invMonoidHom : G →* G` (which needs `DivisionCommMonoid`) in `image_baseOf_inv_comp_eq` and the Subgroup proof built on it.",
    "Once `image_baseOf_inv_comp_eq` is gone (see the `Subgroup.closure_image_isMulIndecomposable_baseOf` finding), weaken `[CommGroup G]` to `[Group G]`.",
    "advisory",
    "lean_verify_edit on the PR as is, with `[Group G]` on line 25: fails only in `image_baseOf_inv_comp_eq` and the Subgroup lemma ('failed to synthesize DivisionCommMonoid G'). With the Subgroup lemma reproved from `mem_or_inv_mem_closure_baseOf` and `image_baseOf_inv_comp_eq` deleted, `[Group G]` compiles the whole file: success.")

add("import in Indecomposable.lean",
    "Two of the four imports this PR adds are not needed. `Mathlib.Algebra.Order.Group.Basic` is unused, and `Mathlib.Algebra.Group.Subgroup.Lattice` is redundant next to `Mathlib.Algebra.Group.Subgroup.Pointwise`. `Algebra/Group/Irreducible/Indecomposable.lean` is a low-level file, so its imports should be minimal.",
    "Drop `public import Mathlib.Algebra.Order.Group.Basic` and `public import Mathlib.Algebra.Group.Subgroup.Lattice`. If the Subgroup lemma is reproved from `mem_or_inv_mem_closure_baseOf`, keep `Subgroup.Lattice` and drop `Subgroup.Pointwise` instead, since `image_inv_eq_inv` and `closure_inv` are then no longer used.",
    "advisory",
    "lean_verify_edit, one import removed at a time: removing line 9 (Subgroup.Lattice) succeeds; line 13 (Order.Group.Basic) succeeds; line 10 (Subgroup.Pointwise) fails ('Unknown identifier image_inv_eq_inv'); line 12 (Order.Group.Defs) fails (IsOrderedCancelMonoid S not synthesized). Removing lines 9 and 13 together: success. With the restructured Subgroup proof, the import set without Pointwise and Order.Group.Basic: success.")

add("IsMulIndecomposable.subset",
    "`IsMulIndecomposable.subset` is the first projection of the definition, but it is proved by `by aesop`, a general search.",
    "Replace the proof with the term `fun _ h ↦ h.1`.",
    "advisory",
    "lean_verify_edit on declaration `IsMulIndecomposable.subset`, with `@[to_additive]` kept and `:= fun _ h ↦ h.1`: success.")

add("IsMulIndecomposable.mem_or_inv_mem_closure_baseOf",
    "The statement is laid out with manual alignment: the first conclusion line has five leading spaces and padding (`     v i    ∈ ...`) so that the two `∈` line up. Mathlib style indents continuation lines by a fixed four (or six) spaces and does not pad for alignment.",
    "Reformat the conclusion as\n    v i ∈ Submonoid.closure (v '' baseOf v f) ∨\n      (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f) := by",
    "advisory",
    "file_read lines 181-182 show the padding. lean_verify_edit with the reformatted lines 181-182: success.")

add("module_doc in BaseExists.lean",
    "The module docstring has a word-order slip, \"even though the existence ultimate statement does not\". It also has no summary of what the file proves: it goes straight to implementation details and a TODO.",
    "Change it to \"even though the ultimate existence statement does not\", and add a short `## Main results` section listing `RootPairing.baseOf_pairwise_pairing_le_zero`, `RootPairing.linearIndepOn_root_baseOf'` and `RootPairing.linearIndepOn_root_baseOf`.",
    "advisory",
    "Read diff.patch lines 226-252 (module docstring of the new file).")

add("RootPairing.linearIndepOn_root_baseOf",
    "The main result of the new file has no docstring, although the primed lemma's docstring defers to it as the target statement.",
    "Add a docstring saying that, for a crystallographic root system over a characteristic-zero field, the roots indexed by `baseOf P.root f` (for `f` nonvanishing on the roots) are linearly independent over `R`, with a reference to the corresponding statement in [serre1965] Ch. V §9.",
    "advisory",
    "Read BaseExists.lean lines 97-134 via file_read: no `/-- ... -/` precedes the lemma.")

add("RootPairing.linearIndepOn_root_baseOf",
    "In the `h_card` block, `replace this : LinearIndependent ℚ v := ...` reuses the name `this`, which there refers to the `Fintype (baseOf ..)` instance introduced at the top of the proof. The block silently replaces an instance hypothesis with a linear-independence fact, which is hard to follow.",
    "Use a named hypothesis instead:\n    have hli : LinearIndependent ℚ v :=\n      .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf\n    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := Basis.mk hli (by rw [h_span])",
    "advisory",
    "lean_verify_edit replacing lines 124-129 with the `have hli` version: success.")

add("RootPairing.linearIndepOn_root_baseOf'",
    "The instance argument `[P.IsValuedIn S]` is redundant: it follows from `[P.IsCrystallographic]` through `IsValuedIn.trans` along `ℤ → S → R`, and `IsValuedIn` is a `Prop`. Requiring it makes callers supply an instance that only exists globally for `S = ℚ`.",
    "Drop `[P.IsValuedIn S]` from the signature and add `have : P.IsValuedIn S := .trans P (S := S) ℤ` at the start of the proof.",
    "advisory",
    "lean_verify_edit on declaration `RootPairing.linearIndepOn_root_baseOf'` with the binder removed and that `have` added after `have : CharZero R := ...`: success. For contrast, removing `[Module S N] [IsScalarTower S R N]` or the `Fintype ι` line fails, because `posRootForm S` needs them.")

add("section in BaseExists.lean",
    "The `CommRing` section declares `{S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)` as variables. The next lemma, `linearIndepOn_root_baseOf'`, rebinds `{S : Type*}` with a different structure (`CommRing S`, `IsStrictOrderedRing S`) and `(f : Dual S M)`, shadowing both section variables. Only `baseOf_pairwise_pairing_le_zero` uses them.",
    "Remove `S`, its instances and `f` from the section `variable` line and put them in the binders of `baseOf_pairwise_pairing_le_zero`, e.g. `lemma baseOf_pairwise_pairing_le_zero [CharZero R] [IsDomain R] [P.IsCrystallographic] {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S) (hf : ...)`.",
    "advisory",
    "lean_verify_edit replacing lines 52-57 this way: success; the call `P.baseOf_pairwise_pairing_le_zero _ hf ...` in the primed lemma is unaffected.")

add("RootPairing.baseOf_pairwise_pairing_le_zero",
    "The lemma is about `P.pairingIn ℤ i j`, but its name says `pairing`. The root-system library consistently separates `pairing` from `pairingIn` in names (`Base.pairingIn_le_zero_of_ne`, the direct `Base` analogue of this lemma; `pairingIn_le_zero_of_root_add_mem`; `pairingIn_le_zero_iff`). The word order also differs from the lemma it applies, `IsAddIndecomposable.pairwise_baseOf_sub_notMem`.",
    "Rename it to use `pairingIn`, ordered like its sibling, e.g. `RootPairing.pairwise_baseOf_pairingIn_le_zero`, and update the call in `linearIndepOn_root_baseOf'`.",
    "advisory",
    "content_search in Mathlib/LinearAlgebra/RootSystem: `Base.lean:275 lemma pairingIn_le_zero_of_ne ... : P.pairingIn ℤ i j ≤ 0` (same conclusion for `b.support`), `Finite/G2.lean:159 pairingIn_le_zero_of_root_add_mem`, `Finite/CanonicalBilinear.lean:392 pairingIn_le_zero_iff`. naming_norm: subject `baseOf`, no population, so the leading prefix is unmeasured; this finding is about the `pairing`/`pairingIn` token, which naming_norm does not measure.")

add("import in BaseExists.lean",
    "`public import Mathlib.Algebra.Module.Submodule.Union` is not needed. Its only connection to the file is that the TODO in the module docstring mentions `Module.exists_dual_forall_apply_ne_zero`, which lives there.",
    "Drop the import; add it in the follow-up PR that actually uses `Module.exists_dual_forall_apply_ne_zero`.",
    "advisory",
    "declaration_search: `Module.exists_dual_forall_apply_ne_zero` is declared in `Mathlib/Algebra/Module/Submodule/Union.lean` and is referenced only in the TODO text. lean_verify_edit removing line 9 of BaseExists.lean: success. Removing line 10 (OrzechProperty) instead fails ('Unknown identifier linearIndependent_iff_card_eq_finrank_span'), so that import is genuinely used.")

add("module_doc in Indecomposable.lean",
    "The module docstring is just the title `# Indecomposable elements of monoids`, but the file now also holds `IsMulIndecomposable.baseOf` and the Submonoid/Subgroup closure theorems that the root-system development builds on.",
    "Extend the module docstring with a short description of the main definitions (`IsMulIndecomposable`, `IsMulIndecomposable.baseOf`) and results (`Submonoid.closure_image_isMulIndecomposable_baseOf`, `Subgroup.closure_image_isMulIndecomposable_baseOf`, `IsMulIndecomposable.pairwise_baseOf_div_notMem`).",
    "advisory",
    "file_read Indecomposable.lean lines 17-19: the docstring is only the title line.")

json.dump(F, open(out, "w"), ensure_ascii=False, indent=1)
print(len(F))
