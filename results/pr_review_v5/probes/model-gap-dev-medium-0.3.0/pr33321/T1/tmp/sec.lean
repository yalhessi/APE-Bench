variable [CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)

/-- This is [serre1965](Ch. V, §9, Lemma 3). -/
lemma baseOf_pairwise_pairing_le_zero {S : Type*} [LinearOrder S] [AddCommGroup S]
    [IsOrderedAddMonoid S] (f : M →+ S) [CharZero R] [IsDomain R] [P.IsCrystallographic]
    (hf : ∀ i, f (P.root i) ≠ 0) :
    (baseOf P.root f).Pairwise fun i j ↦ P.pairingIn ℤ i j ≤ 0 := by
  letI _i := P.indexNeg
  intro i hi j hj hne
  have := IsAddIndecomposable.pairwise_baseOf_sub_notMem P.root (by simp) f hf hi hj hne
  contrapose! this
  exact P.root_sub_root_mem_of_pairingIn_pos this hne
