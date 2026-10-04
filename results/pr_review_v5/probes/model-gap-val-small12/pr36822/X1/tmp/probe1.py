import json
rep = '''@[to_dual Iio_disjoint_Ioi_iff]
theorem Ioi_disjoint_Iio_iff [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b :=
  ⟨fun h hab ↦ (exists_between hab).elim
    fun _ hc ↦ h.notMem_of_mem_left hc.left hc.right,
    Ioi_disjoint_Iio_of_not_lt⟩

example : Disjoint (Ioi a) (Iio a) := by simp
example : Disjoint (Iio a) (Ioi a) := by simp
example [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b := by simp
example [DenselyOrdered α] : Disjoint (Iio a) (Ioi b) ↔ ¬b < a := by simp'''
print(json.dumps({"path":"Mathlib/Order/Interval/Set/Disjoint.lean","line_start":82,"line_end":86,"replacement":rep}))
