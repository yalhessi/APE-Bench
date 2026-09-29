@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl

#synth Pow X.IdealSheafData ℕ
#synth Monoid X.IdealSheafData
set_option pp.explicit true in
#check fun (n : ℕ) => I ^ n
set_option pp.explicit true in
#check fun (n : ℕ) => Monoid.npow n I
example (n : ℕ) : (Monoid.npow n I).ideal = I.ideal ^ n := rfl
example (n : ℕ) : (Monoid.npow n I).ideal = I.ideal ^ n := by induction n <;> simp_all [Monoid.npow, npowRec]
