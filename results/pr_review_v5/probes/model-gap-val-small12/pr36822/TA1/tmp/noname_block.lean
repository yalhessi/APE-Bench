@[to_dual (attr := simp)]
theorem Iic_disjoint_Ioi (h : a ≤ b) : Disjoint (Iic a) (Ioi b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt hb).not_ge ha

@[to_dual (attr := simp)]
theorem Iio_disjoint_Ici (h : a ≤ b) : Disjoint (Iio a) (Ici b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt' ha).not_ge hb

@[simp]
theorem Iic_disjoint_Ioc (h : a ≤ b) : Disjoint (Iic a) (Ioc b c) :=
  (Iic_disjoint_Ioi h).mono le_rfl Ioc_subset_Ioi_self

@[simp]
theorem Ioc_disjoint_Ioc_of_le {d : α} (h : b ≤ c) : Disjoint (Ioc a b) (Ioc c d) :=
  (Iic_disjoint_Ioc h).mono Ioc_subset_Iic_self le_rfl

@[simp]
theorem Ico_disjoint_Ico_same : Disjoint (Ico a b) (Ico b c) :=
  disjoint_left.mpr fun _ hab hbc => hab.2.not_ge hbc.1

@[to_dual (attr := simp)]
theorem Ici_disjoint_Iic : Disjoint (Ici a) (Iic b) ↔ ¬a ≤ b := by
  rw [Set.disjoint_iff_inter_eq_empty, Ici_inter_Iic, Icc_eq_empty_iff]

@[simp]
theorem Ioc_disjoint_Ioi (h : b ≤ c) : Disjoint (Ioc a b) (Ioi c) :=
  disjoint_left.mpr (fun _ hx hy ↦ (hx.2.trans h).not_gt hy)

theorem Ioc_disjoint_Ioi_same : Disjoint (Ioc a b) (Ioi b) :=
  Ioc_disjoint_Ioi le_rfl

@[to_dual]
theorem Ioi_disjoint_Iio_of_not_lt (h : ¬a < b) : Disjoint (Ioi a) (Iio b) :=
  disjoint_left.mpr fun _ hx hy ↦ h (hx.trans hy)

@[to_dual]
theorem Ioi_disjoint_Iio_of_le (h : a ≤ b) : Disjoint (Ioi b) (Iio a) :=
  Ioi_disjoint_Iio_of_not_lt (not_lt_of_ge h)

@[to_dual]
theorem Ioi_disjoint_Iio_same : Disjoint (Ioi a) (Iio a) :=
  Ioi_disjoint_Iio_of_le le_rfl

@[to_dual]
theorem Ioi_disjoint_Iio_iff [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b :=
  ⟨fun h hab ↦ (exists_between hab).elim
    fun _ hc ↦ h.notMem_of_mem_left hc.left hc.right,
    Ioi_disjoint_Iio_of_not_lt⟩

@[to_dual (attr := simp)]
theorem iUnion_Iic : ⋃ a : α, Iic a = univ :=
  iUnion_eq_univ_iff.2 fun x => ⟨x, self_mem_Iic⟩

@[to_dual (attr := simp)]
theorem iUnion_Icc_right (a : α) : ⋃ b, Icc a b = Ici a := by
  simp only [← Ici_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]

@[to_dual (attr := simp)]
theorem iUnion_Ioc_right (a : α) : ⋃ b, Ioc a b = Ioi a := by
  simp only [← Ioi_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]

@[to_dual (attr := simp)]
theorem iUnion_Iio [NoMaxOrder α] : ⋃ a : α, Iio a = univ :=
  iUnion_eq_univ_iff.2 exists_gt

@[to_dual (attr := simp)]
theorem iUnion_Ico_right [NoMaxOrder α] (a : α) : ⋃ b, Ico a b = Ici a := by
  simp only [← Ici_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]

@[to_dual (attr := simp)]
theorem iUnion_Ioo_right [NoMaxOrder α] (a : α) : ⋃ b, Ioo a b = Ioi a := by
  simp only [← Ioi_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]

example := @Ici_disjoint_Iio
example := @Ioi_disjoint_Iic
example := @Iic_disjoint_Ici
example := @Iio_disjoint_Ioi_of_not_lt
example := @Iio_disjoint_Ioi_of_le
example := @Iio_disjoint_Ioi_same
example := @Iio_disjoint_Ioi_iff
example := @iUnion_Ici
example := @iUnion_Icc_left
example := @iUnion_Ico_left
example := @iUnion_Ioi
example := @iUnion_Ioc_left
example := @iUnion_Ioo_left
