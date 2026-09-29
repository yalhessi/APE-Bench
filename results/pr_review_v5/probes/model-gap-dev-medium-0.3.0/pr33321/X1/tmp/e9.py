import json
rep = r'''variable [CommRing R] [Module R M] [Module R N] (P : RootPairing ι R M N)

/-- This is [serre1965](Ch. V, §9, Lemma 3). -/
lemma baseOf_pairwise_pairing_le_zero [CharZero R] [IsDomain R] [P.IsCrystallographic]
    {S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)
    (hf : ∀ i, f (P.root i) ≠ 0) :
    (baseOf P.root f).Pairwise fun i j ↦ P.pairingIn ℤ i j ≤ 0 := by'''
print(json.dumps({"path":"Mathlib/LinearAlgebra/RootSystem/BaseExists.lean","line_start":52,"line_end":58,"replacement":rep}))
