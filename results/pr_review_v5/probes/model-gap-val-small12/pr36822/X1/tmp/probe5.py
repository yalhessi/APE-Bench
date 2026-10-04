import json
rep = '''@[to_dual (attr := simp) Ioc_disjoint_Ioc]
theorem Ico_disjoint_Ico : Disjoint (Ico a₁ a₂) (Ico b₁ b₂) ↔ min a₂ b₂ ≤ max a₁ b₁ := by
  simp_rw [Set.disjoint_iff_inter_eq_empty, Ico_inter_Ico, Ico_eq_empty_iff, not_lt]

#check @Ioc_disjoint_Ioc'''
print(json.dumps({"path":"Mathlib/Order/Interval/Set/Disjoint.lean","line_start":118,"line_end":125,"replacement":rep}))
