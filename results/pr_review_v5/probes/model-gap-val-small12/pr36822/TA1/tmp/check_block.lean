  simp only [← Ioi_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]

example {a b : α} (h : ¬a < b) : Disjoint (Iio b) (Ioi a) := Iio_disjoint_Ioi_of_not_lt h
example {a b : α} (h : a ≤ b) : Disjoint (Iio a) (Ioi b) := Iio_disjoint_Ioi_of_le h
example {a b : α} : Disjoint (Iic a) (Ici b) ↔ ¬b ≤ a := Iic_disjoint_Ici
example {a b : α} [DenselyOrdered α] : Disjoint (Iio a) (Ioi b) ↔ ¬b < a := Iio_disjoint_Ioi_iff
example {a b : α} (h : b ≤ a) : Disjoint (Ici a) (Iio b) := Ici_disjoint_Iio h
example (b : α) : ⋃ a, Icc a b = Iic b := iUnion_Icc_left b
example (b : α) : ⋃ a, Ico a b = Iio b := iUnion_Ico_left b
example [NoMinOrder α] (b : α) : ⋃ a, Ioc a b = Iic b := iUnion_Ioc_left b
example [NoMinOrder α] (b : α) : ⋃ a, Ioo a b = Iio b := iUnion_Ioo_left b
example (a : α) : Disjoint (Ioi a) (Iio a) := by simp
example (a : α) : Disjoint (Iio a) (Ioi a) := by simp
example [DenselyOrdered α] (a b : α) : Disjoint (Ioi a) (Iio b) ↔ ¬a < b := by simp
example [DenselyOrdered α] (a b : α) : Disjoint (Iio a) (Ioi b) ↔ ¬b < a := by simp
