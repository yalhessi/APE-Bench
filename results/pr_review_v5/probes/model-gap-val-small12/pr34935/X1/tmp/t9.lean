@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl

example : (⊥ : X.IdealSheafData) + I = I := by simp
example : (0 : X.IdealSheafData) * I = 0 := by simp
example : I ^ 0 = ⊤ := by simp
example (n : ℕ) : (I ^ (n + 2)).support = I.support := by simp
example : (I * J).radical = (J * I).radical := by simp [inf_comm]
example (n : ℕ) (hn : n ≠ 0) : (I ^ n).radical = I.radical := by simp [hn]
