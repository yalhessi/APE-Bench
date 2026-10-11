import json
F = "Mathlib/LinearAlgebra/RootSystem/BaseExists.lean"
prime_base = """lemma linearIndepOn_root_baseOf' [IsDomain R] {S : Type*}
    [LinearOrder S] [CommRing S] [IsStrictOrderedRing S] [Algebra S R] [FaithfulSMul S R]
    [Module S M] [IsScalarTower S R M] [Module S N] [IsScalarTower S R N]
    [P.IsValuedIn S] [P.IsCrystallographic]
    (f : Dual S M) (hf : ∀ i, f (P.root i) ≠ 0) :
    LinearIndepOn S P.root (baseOf P.root (f : M →+ S)) := by
  have : CharZero R := Algebra.charZero_of_charZero S R
  FINTYPE
  let M₀ := span S (range P.root)
  let v (i : baseOf P.root (f : M →+ S)) : M₀ := P.rootSpanMem S i
  change LinearIndependent S (M₀.subtype ∘ v)
  suffices LinearIndependent S v by
    rwa [LinearMap.linearIndependent_iff_of_disjoint M₀.subtype (by simp)]
  let f' : Dual S M₀ := f ∘ₗ M₀.subtype
  obtain ⟨B, hB⟩ : ∃ B : P.RootPositiveForm S, B.posForm.toQuadraticMap.PosDef :=
    ⟨P.posRootForm S, by simpa using P.posRootForm_rootFormIn_posDef S⟩
  HP
  have hn : Pairwise fun (i j : baseOf P.root (f : M →+ S)) ↦ B.posForm (v i) (v j) ≤ 0 := by
    rintro ⟨i, hi⟩ ⟨j, hj⟩ hij
    rw [B.posForm_apply_root_root_le_zero_iff, ← P.algebraMap_pairingIn' S ℤ]
    simpa using P.baseOf_pairwise_pairing_le_zero _ hf (by simpa) (by simpa) NEQ
  exact LinearMap.BilinForm.linearIndependent_of_pairwise_le_zero B.posForm hB f' v hp hn"""
HP0 = "have hp (i : baseOf P.root (f : M →+ S)) : 0 < f' (v i) := by obtain ⟨i, -, hi⟩ := i; simpa"
HP1 = "have hp (i : baseOf P.root (f : M →+ S)) : 0 < f' (v i) := by\n    obtain ⟨i, -, hi⟩ := i\n    simpa"
def mk(fintype="have : Fintype ι := Fintype.ofFinite ι", hp=HP0, neq="(by aesop : i ≠ j)"):
    return prime_base.replace("FINTYPE", fintype).replace("HP", hp, 1).replace("NEQ", neq)
spec = [
 ("prime: letI Fintype + split hp + Subtype.ext", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf'","new_declaration":mk("letI : Fintype ι := Fintype.ofFinite ι", HP1, "(fun h ↦ hij (Subtype.ext h))")}),
 ("prime: no Fintype at all", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf'","new_declaration":mk("", HP1, "(by aesop : i ≠ j)").replace("\n  \n","\n")}),
 ("prime: drop Module S N / IsScalarTower S R N", {"path":F,"declaration_name":"RootPairing.linearIndepOn_root_baseOf'","new_declaration":mk().replace(" [Module S N] [IsScalarTower S R N]","")}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be1.json","w"))
