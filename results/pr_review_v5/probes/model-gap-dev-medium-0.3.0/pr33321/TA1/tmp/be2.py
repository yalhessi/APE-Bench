import json
F = "Mathlib/LinearAlgebra/RootSystem/BaseExists.lean"
base = """lemma linearIndepOn_root_baseOf [Module ℚ M] [Module ℚ N]
    (f : Dual ℚ M) (hf : ∀ i, f (P.root i) ≠ 0) :
    LinearIndepOn R P.root (baseOf P.root (f : M →+ ℚ)) := by
  letI := P.indexNeg
  have : Fintype (baseOf P.root (f : M →+ ℚ)) := Fintype.ofFinite _
  let v (i : baseOf P.root (f : M →+ ℚ)) : P.rootSpan ℚ := P.rootSpanMem ℚ i
  change LinearIndependent R ((P.rootSpan ℚ).subtype ∘ v)
  have h_span : span ℚ (range v) = ⊤ := by
    suffices span ℚ (range v) = span ℚ (range (P.rootSpanMem ℚ)) by
      rw [this, eq_top_iff, ← LinearMap.map_le_map_iff' (f := (P.rootSpan ℚ).subtype) (by simp),
        map_span, ← image_univ, ← image_comp]
      simp
    apply le_antisymm (span_mono fun x i ↦ by aesop) (span_le.mpr ?_)
    rintro - ⟨i, rfl⟩
    suffices (P.rootSpanMem ℚ i : M) ∈ span ℚ (P.root '' baseOf P.root (f : M →+ ℚ)) by
      rw [← (injective_subtype (P.rootSpan ℚ)).mem_set_image, ← map_coe, SetLike.mem_coe, map_span,
        ← image_univ, ← image_comp]
      convert this
      aesop
    rw [← span_span_of_tower ℤ, ← Submodule.coe_toAddSubgroup, span_int_eq_addSubgroupClosure,
      AddSubgroup.closure_image_isAddIndecomposable_baseOf P.root (by simp) (f : M →+ ℚ) (by simpa)]
    exact subset_span <| AddSubgroup.subset_closure <| by simp
  have h_card : Nat.card (baseOf P.root (f : M →+ ℚ)) = finrank R M := by
    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := by
      replace this : LinearIndependent ℚ v :=
        .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf
      exact Basis.mk this (by rw [h_span])
    rw [← RootPairing.finrank_rootSpanIn ℚ P, finrank_eq_nat_card_basis b]
  have hv : span R (range <| (P.rootSpan ℚ).subtype ∘ v) = ⊤ := by
    rw [range_comp, ← span_span_of_tower ℚ, span_image, h_span]
    simp
  rw [linearIndependent_iff_card_eq_finrank_span, Set.finrank, hv, finrank_top, ← h_card,
    Fintype.card_eq_nat_card]"""
e1 = base.replace("have : Fintype (baseOf P.root (f : M →+ ℚ)) := Fintype.ofFinite _", "letI : Fintype (baseOf P.root (f : M →+ ℚ)) := Fintype.ofFinite _")
e2 = base.replace(" [Module ℚ N]\n", "\n")
e3 = base.replace("span_mono fun x i ↦ by aesop", "span_mono fun _ ⟨i, hi⟩ ↦ ⟨i, hi⟩")
e4 = base.replace("← RootPairing.finrank_rootSpanIn", "← finrank_rootSpanIn").replace("← Submodule.coe_toAddSubgroup", "← coe_toAddSubgroup")
e5 = base.replace("""    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := by
      replace this : LinearIndependent ℚ v :=
        .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf
      exact Basis.mk this (by rw [h_span])
""", """    have hli : LinearIndependent ℚ v :=
      .of_comp (P.rootSpan ℚ).subtype <| P.linearIndepOn_root_baseOf' f hf
    let b : Basis (baseOf P.root (f : M →+ ℚ)) ℚ (P.rootSpan ℚ) := Basis.mk hli (by rw [h_span])
""")
e6 = base.replace("      convert this\n      aesop\n", "      convert this\n      simp\n")
spec = [("letI fintype", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e1}),
        ("drop Module Q N", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e2}),
        ("span_mono term", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e3}),
        ("drop prefixes", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e4}),
        ("have hli + term basis", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e5}),
        ("convert; simp", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf","new_declaration":e6}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be2.json","w"))
