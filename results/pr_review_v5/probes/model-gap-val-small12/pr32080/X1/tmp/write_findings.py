import json
F = []
F.append({
 "target": "CompletelyRegularSpace.of_exists_uniformSpace",
 "claim": "The section line `variable [t : TopologicalSpace α] [CompletelyRegularSpace α]` is auto-included in every following theorem, because its instance argument depends only on `α` and `t`, which each statement mentions. So `CompletelyRegularSpace.of_exists_uniformSpace` takes `[CompletelyRegularSpace α]` as a hypothesis while concluding `CompletelyRegularSpace α`, which makes it circular. `completelyRegularSpace_iff_exists_uniformSpace` has the same extra hypothesis, so the headline iff says nothing: neither can be applied to a space that is not already known to be completely regular.",
 "requested_change": "Change the section line to `variable [t : TopologicalSpace α]` and put the instance binder only on the forward direction, as `public theorem CompletelyRegularSpace.exists_uniformSpace [CompletelyRegularSpace α] : ∃ (u : UniformSpace α), u.toTopologicalSpace = t`. Then prove the iff as `⟨fun _ ↦ CompletelyRegularSpace.exists_uniformSpace, .of_exists_uniformSpace⟩` (the `@... α t` is no longer needed).",
 "severity": "blocking",
 "evidence": "lean_verify_edit (line mode, appended after line 125): `example {β : Type*} [t' : TopologicalSpace β] (h : ∃ (u : UniformSpace β), u.toTopologicalSpace = t') : CompletelyRegularSpace β := CompletelyRegularSpace.of_exists_uniformSpace h` fails with `failed to synthesize CompletelyRegularSpace β`. The same example using `completelyRegularSpace_iff_exists_uniformSpace` fails the same way. After replacing lines 111-125 with the requested version, lean_verify_edit succeeds with both examples appended and no errors or warnings. So the fixed statements no longer need the instance, and the file compiles."
})
F.append({
 "target": "P",
 "claim": "The auxiliary predicate for the Urysohn construction is a root-namespace `def P` with no docstring. The single-letter name says nothing about what it states: `c` is the closure of an entourage ball around `x`, and `u` is an open ball around `x` that contains its `s`-thickening. It is also indistinguishable from the bound variable `P` of `Urysohns.CU`, whose argument it is passed as.",
 "requested_change": "Give it a descriptive name, mark it `private`, and add a docstring stating what the predicate says, e.g. `/-- Auxiliary predicate for the Urysohn construction in UniformSpace.toCompletelyRegularSpace: ... -/ private def IsUrysohnBallPair (c u : Set α) : Prop := ...`. Update `Urysohns.CU P` and `urysohns_main` to use the new name.",
 "severity": "advisory",
 "evidence": "Read the diff (lines 45-48 of Uniformizable.lean). `P` has no docstring and no namespace. In UrysohnsLemma.lean, `Urysohns.CU` takes its predicate as a bound variable named `P`. lean_verify_edit with lines 45-107 replaced, renaming `P` to `private def IsUrysohnBallPair` with a docstring and updating its uses, compiled successfully with no warnings."
})
F.append({
 "target": "urysohns_main",
 "claim": "`urysohns_main` is a root-namespace auxiliary theorem whose name gives neither what it proves nor that it is internal. It proves the interpolation step (`hP` field of `Urysohns.CU`) for the ball-pair predicate `P`: from `P c u` there is an open `v` with `c ⊆ v`, `closure v ⊆ u`, `P c v` and `P (closure v) u`.",
 "requested_change": "Rename it after its statement and tie it to the predicate, and mark it `private`. For example, make it `private theorem IsUrysohnBallPair.exists_between {c u : Set α} (Pcu : IsUrysohnBallPair c u) : ∃ v, IsOpen v ∧ c ⊆ v ∧ closure v ⊆ u ∧ IsUrysohnBallPair c v ∧ IsUrysohnBallPair (closure v) u`, and write the `hP` field as `hP _ Pcu _ _ := Pcu.exists_between`.",
 "severity": "advisory",
 "evidence": "Read the diff (lines 50-80). Its only use is in `hP _ Pcu _ _ := urysohns_main Pcu` inside `UniformSpace.toCompletelyRegularSpace`. With exactly this rename (and the `P` rename), lean_verify_edit replacing lines 45-107 succeeded with no errors or warnings."
})
F.append({
 "target": "module_doc in Uniformizable.lean",
 "claim": "The Implementation Details section says Urysohn's lemma is reused in the proof of `UniformSpace.completelyRegularSpace`. No declaration has that name: the instance this PR adds is `UniformSpace.toCompletelyRegularSpace`, and the Main Results list in the same docstring uses that name.",
 "requested_change": "Replace `UniformSpace.completelyRegularSpace` with `UniformSpace.toCompletelyRegularSpace` in the Implementation Details section.",
 "severity": "advisory",
 "evidence": "lean_verify_edit with `#check @UniformSpace.completelyRegularSpace` appended to the file fails with `Unknown constant UniformSpace.completelyRegularSpace`. content_search finds no `UniformSpace` mention in Mathlib/Topology/Separation/CompletelyRegular.lean. declaration_search reported a hit there, but it was a fuzzy match on the suffix (`Topology.IsInducing.completelyRegularSpace`)."
})
F.append({
 "target": "module_doc in Uniformizable.lean",
 "claim": "The module docstring still contains the placeholder `TODO: Explain proofs`. As submitted it does not explain either direction: the Urysohn-style construction via `Urysohns.CU` on entourage-ball pairs for uniform ⇒ completely regular, and the pull-back of the unique uniformity of the compact Hausdorff Stone-Čech compactification along `stoneCechUnit` for the converse.",
 "requested_change": "Replace `TODO: Explain proofs` with a short proof sketch of both directions. Uniform spaces: run the `Urysohns.CU` construction with the predicate on pairs (closure of ball `x` `uc`, ball `x` `uu`), using `comp_open_symm_mem_uniformity_sets` for the interpolation step. Completely regular spaces: `stoneCechUnit` is inducing (`isInducing_stoneCechUnit`), so `uniformSpaceOfCompactR1.comap stoneCechUnit` induces the topology. Otherwise delete the TODO line.",
 "severity": "advisory",
 "evidence": "content_search for `TODO` in Mathlib/Topology/UniformSpace/Uniformizable.lean: line 19 is `TODO: Explain proofs`. The proofs it should describe were read in the diff (lines 82-107 and 113-115)."
})
F.append({
 "target": "module_doc in Uniformizable.lean",
 "claim": "The only reference is a bare URL to a course problem set PDF (`math.wm.edu/~vinroot/PadicGroups/519probset1.pdf`). That is not a stable citation. The sibling file Mathlib/Topology/Separation/CompletelyRegular.lean cites a book through a `docs/references.bib` key (`[Russell C. Walker, *The Stone-Čech Compactification*][russell1974]`).",
 "requested_change": "Replace the URL with a standard textbook reference for 'uniformizable iff completely regular' (e.g. Willard, *General Topology*, §38, or Engelking, *General Topology*, Ch. 8). Add it to `docs/references.bib` and cite it in the `[Author, *Title*][key]` form used by CompletelyRegular.lean.",
 "severity": "advisory",
 "evidence": "Read the References section of the new module doc and the References section of target/Mathlib/Topology/Separation/CompletelyRegular.lean (lines 50-53), which uses the bib-key form."
})
F.append({
 "target": "SetRel.IsRefl.comp",
 "claim": "The new instance is called `IsRefl.comp` and states `(R₁.comp R₂).IsRefl`. Every sibling instance in this block is named `isRefl_<op>` (`isRefl_univ`, `isRefl_inter`, `isRefl_iInter`, `isRefl_preimage`), and the composition instances nearby write `○` (`isSymm_comp_self : (R ○ R).IsSymm`, `isSymm_comp_inv`). Under the current name it also reads like a dot-notation lemma on `IsRefl`.",
 "requested_change": "Rename it to `isRefl_comp` and state it with the notation: `instance isRefl_comp [R₁.IsRefl] [R₂.IsRefl] : (R₁ ○ R₂).IsRefl where refl _ := ⟨_, R₁.rfl, R₂.rfl⟩`.",
 "severity": "advisory",
 "evidence": "Read Mathlib/Data/Rel.lean lines 346-463 (the sibling instance names quoted above). lean_verify_edit on Mathlib/Data/Rel.lean replacing `SetRel.IsRefl.comp` with the renamed `○` form succeeded. The instance is needed: with `attribute [-instance] SetRel.IsRefl.comp`, Uniformizable.lean fails at `(hdsd.trans left_subset_comp).trans hu3C` with `failed to synthesize (u3 ○ u3).IsRefl`. It is found by instance search, not by name, so the rename does not affect that file. naming_norm could not resolve a subject (unmeasured)."
})
F.append({
 "target": "UniformSpace.toCompletelyRegularSpace",
 "claim": "The instance `[UniformSpace α] → CompletelyRegularSpace α` applies to every type, so every `CompletelyRegularSpace` search will try it by looking for a `UniformSpace` instance. Yet it has default priority. Its direct sibling `UniformSpace.to_regularSpace` in Mathlib/Topology/UniformSpace/Separation.lean is declared `instance (priority := 100)`, following the lower-instance-priority convention for such always-applicable instances.",
 "requested_change": "Declare it as `public instance (priority := 100) UniformSpace.toCompletelyRegularSpace : CompletelyRegularSpace α where ...`.",
 "severity": "advisory",
 "evidence": "content_search on Mathlib/Topology/UniformSpace: `instance (priority := 100) UniformSpace.to_regularSpace : RegularSpace α` at Separation.lean:115. lean_verify_edit replacing the instance with the `(priority := 100)` version (together with the style edits in the next finding) succeeded with no errors or warnings."
})
F.append({
 "target": "UniformSpace.toCompletelyRegularSpace",
 "claim": "The tail of the proof departs from Mathlib style in several places. `set c : Urysohns.CU P := { ... }` uses `set` where nothing needs abstracting. The structure literal puts `{` at the end of the line and `}` on a line of its own. The final term uses `fun x =>` and `fun y hy =>`, and the `fun x` shadows the point `x` that the same term then uses in `c.lim_of_mem_C x hxc`.",
 "requested_change": "Use `let c : Urysohns.CU P :=` in place of `set`. Lay the literal out Mathlib-style, opening with `{ C := ...` and closing `}` at the end of the last field. Write the final term with `↦` and a fresh binder: `exact ⟨fun z ↦ ⟨c.lim z, c.lim_mem_Icc z⟩, c.continuous_lim.subtype_mk c.lim_mem_Icc, Subtype.ext (c.lim_of_mem_C x hxc), fun y hy ↦ Subtype.ext (c.lim_of_notMem_U y (hyo hy))⟩`.",
 "severity": "advisory",
 "evidence": "Read the diff lines 92-107. lean_verify_edit replacing the whole instance with the `let`/`↦`/`z` version (plus `(priority := 100)`) succeeded with no errors or warnings."
})
F.append({
 "target": "UniformSpace.toCompletelyRegularSpace",
 "claim": "With this PR a T0 uniform space is both `T0Space` and `CompletelyRegularSpace`, yet `T35Space` is still not inferred for it. `T35Space` is a class extending both, and its only generic instance comes from `T4Space`. So lemmas stated for `[T35Space X]` in CompletelyRegular.lean (`isEmbedding_stoneCechUnit`, `separatesPoints_continuous_of_t35Space`, ...) cannot be used on Hausdorff uniform spaces without a manual instance.",
 "requested_change": "Add, next to the new instance, `public instance (priority := 100) UniformSpace.toT35Space [T0Space α] : T35Space α where`.",
 "severity": "advisory",
 "evidence": "lean_verify_edit with `example {β : Type*} [UniformSpace β] [T0Space β] : T35Space β := inferInstance` appended fails with `failed to synthesize T35Space β`. Adding `public instance (priority := 100) UniformSpace.toT35Space [T0Space α] : T35Space α where` before `end UniformSpace` makes that same example compile (lean_verify_edit success). Read CompletelyRegular.lean lines 217-272 for `T35Space` and its instances."
})
json.dump(F, open("findings.json","w"), ensure_ascii=False, indent=1)
print(len(F))
