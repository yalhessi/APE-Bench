instance : IdemCommSemiring X.IdealSheafData where
  add_assoc := sup_assoc
  zero_add := bot_sup_eq
  add_zero := sup_bot_eq
  add_comm := sup_comm
  mul_assoc _ _ _ := IdealSheafData.ext (mul_assoc _ _ _)
  mul_comm _ _ := IdealSheafData.ext (mul_comm _ _)
  zero_mul := bot_mul
  mul_zero := mul_bot
  one_mul := top_mul
  mul_one := mul_top
  left_distrib := mul_inf
  right_distrib := inf_mul
  npow n I := I ^ n
  npow_zero _ := by ext; simp [show (1 : X.IdealSheafData) = ⊤ from rfl]
  npow_succ n I := IdealSheafData.ext (pow_succ I.ideal n)
  bot_le _ := bot_le
