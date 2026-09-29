import json
rep = '''lemma mul_sup : I * (J ⊔ K) = I * J ⊔ I * K := by ext U : 2; exact mul_add _ _ _
lemma sup_mul : (I ⊔ J) * K = I * K ⊔ J * K := by ext U : 2; exact add_mul _ _ _

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
  nsmul := nsmulRec
  left_distrib := mul_sup
  right_distrib := sup_mul
  npow_zero _ := by ext; rfl
  npow_succ _ _ := by ext; rfl
  bot_le _ := bot_le'''
print(json.dumps({"path": "Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean", "line_start": 423, "line_end": 442, "replacement": rep}))
