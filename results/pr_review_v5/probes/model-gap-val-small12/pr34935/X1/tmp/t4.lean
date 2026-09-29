@[simp] lemma add_eq_sup : I + J = I ⊔ J := rfl

example (n : ℕ) : I ^ (n + 1) = I ^ n * I := pow_succ I n
example (n : ℕ) : I ^ (n + 1) = I ^ n * I := by rw [pow_succ]
example : I ^ 2 = I * I := by rw [sq]
example (n : ℕ) : (I ^ n).ideal = I.ideal ^ n := by simp
example (n : ℕ) : I ^ n ≤ I ^ n := pow_le_pow_left₀ bot_le le_rfl n
