@[to_dual (attr := simp) Iio_disjoint_Ioi_same]
theorem Ioi_disjoint_Iio_same : Disjoint (Ioi a) (Iio a) :=
  Ioi_disjoint_Iio_of_le le_rfl

@[to_dual (attr := simp) Iio_disjoint_Ioi_iff]
theorem Ioi_disjoint_Iio_iff [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b :=
  ⟨fun h hab ↦ (exists_between hab).elim
    fun _ hc ↦ h.notMem_of_mem_left hc.left hc.right,
    Ioi_disjoint_Iio_of_not_lt⟩

example (a : α) : Disjoint (Ioi a) (Iio a) := by simp
example (a : α) : Disjoint (Iio a) (Ioi a) := by simp
example [DenselyOrdered α] (a b : α) : Disjoint (Ioi a) (Iio b) ↔ ¬a < b := by simp
example [DenselyOrdered α] (a b : α) : Disjoint (Iio a) (Ioi b) ↔ ¬b < a := by simp
