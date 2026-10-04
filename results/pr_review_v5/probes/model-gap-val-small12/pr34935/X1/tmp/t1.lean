@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl

example (n : ℕ) : Monoid.npow n I = I ^ n := by with_reducible_and_instances rfl
example (n : ℕ) : Monoid.npow n I = I ^ n := rfl
example (n : ℕ) : @HPow.hPow _ _ _ (@instHPow _ _ Monoid.Pow) I n = I ^ n := by with_reducible_and_instances rfl
example : IsOrderedRing X.IdealSheafData := inferInstance
#synth IsOrderedRing X.IdealSheafData
