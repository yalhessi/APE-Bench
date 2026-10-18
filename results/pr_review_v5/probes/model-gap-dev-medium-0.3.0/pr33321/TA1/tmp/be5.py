import json
F = "Mathlib/LinearAlgebra/RootSystem/BaseExists.lean"
new = """variable [CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)

/-- Given a linear form `f` that is nonzero on every root, distinct roots in `baseOf P.root f` have
non-positive pairing.

This is [serre1965](Ch. V, §9, Lemma 3). -/
lemma pairwise_baseOf_pairingIn_le_zero [CharZero R] [IsDomain R] [P.IsCrystallographic]
    {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)
    (hf : ∀ i, f (P.root i) ≠ 0) :
    (baseOf P.root f).Pairwise fun i j ↦ P.pairingIn ℤ i j ≤ 0 := by
  letI _i := P.indexNeg
  intro i hi j hj hne
  have := IsAddIndecomposable.pairwise_baseOf_sub_notMem P.root (by simp) f hf hi hj hne
  contrapose! this
  exact P.root_sub_root_mem_of_pairingIn_pos this hne

/-- Given a linear form `f` over an ordered ring `S` that is nonzero on every root, the roots in
`baseOf P.root f` are linearly independent over `S`. -/
lemma linearIndepOn_root_baseOf' [IsDomain R] {S : Type*}
    [LinearOrder S] [CommRing S] [IsStrictOrderedRing S] [Algebra S R] [FaithfulSMul S R]
    [Module S M] [IsScalarTower S R M] [Module S N] [IsScalarTower S R N]
    [P.IsValuedIn S] [P.IsCrystallographic]
    (f : Dual S M) (hf : ∀ i, f (P.root i) ≠ 0) :
    LinearIndepOn S P.root (baseOf P.root (f : M →+ S)) := by
  have : CharZero R := Algebra.charZero_of_charZero S R
  letI : Fintype ι := Fintype.ofFinite ι
  let M₀ := span S (range P.root)
  let v (i : baseOf P.root (f : M →+ S)) : M₀ := P.rootSpanMem S i
  change LinearIndependent S (M₀.subtype ∘ v)
  suffices LinearIndependent S v by
    rwa [LinearMap.linearIndependent_iff_of_disjoint M₀.subtype (by simp)]
  let f' : Dual S M₀ := f ∘ₗ M₀.subtype
  obtain ⟨B, hB⟩ : ∃ B : P.RootPositiveForm S, B.posForm.toQuadraticMap.PosDef :=
    ⟨P.posRootForm S, by simpa using P.posRootForm_rootFormIn_posDef S⟩
  have hp (i : baseOf P.root (f : M →+ S)) : 0 < f' (v i) := by
    obtain ⟨i, -, hi⟩ := i
    simpa
  have hn : Pairwise fun (i j : baseOf P.root (f : M →+ S)) ↦ B.posForm (v i) (v j) ≤ 0 := by
    rintro ⟨i, hi⟩ ⟨j, hj⟩ hij
    rw [B.posForm_apply_root_root_le_zero_iff, ← P.algebraMap_pairingIn' S ℤ]
    simpa using P.pairwise_baseOf_pairingIn_le_zero _ hf (by simpa) (by simpa)
      (fun h ↦ hij (Subtype.ext h))
  exact LinearMap.BilinForm.linearIndependent_of_pairwise_le_zero B.posForm hB f' v hp hn"""
spec = [("restructure CommRing section", {"path":F,"line_start":52,"line_end":93,"replacement":new})]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be5.json","w"))
