section LinearOrder

variable [LinearOrder α] {a₁ a₂ b₁ b₂ : α}

@[to_dual (attr := simp) Ioc_disjoint_Ioc]
theorem Ico_disjoint_Ico : Disjoint (Ico a₁ a₂) (Ico b₁ b₂) ↔ min a₂ b₂ ≤ max a₁ b₁ := by
  simp_rw [Set.disjoint_iff_inter_eq_empty, Ico_inter_Ico, Ico_eq_empty_iff, not_lt]

@[simp]
theorem Ioo_disjoint_Ioo [DenselyOrdered α] :
    Disjoint (Set.Ioo a₁ a₂) (Set.Ioo b₁ b₂) ↔ min a₂ b₂ ≤ max a₁ b₁ := by
  simp_rw [Set.disjoint_iff_inter_eq_empty, Ioo_inter_Ioo, Ioo_eq_empty_iff, not_lt]

/-- If two half-open intervals are disjoint and the endpoint of one lies in the other,
  then it must be equal to the endpoint of the other. -/
theorem eq_of_Ico_disjoint {x₁ x₂ y₁ y₂ : α} (h : Disjoint (Ico x₁ x₂) (Ico y₁ y₂)) (hx : x₁ < x₂)
    (h2 : x₂ ∈ Ico y₁ y₂) : y₁ = x₂ := by
  rw [Ico_disjoint_Ico, min_eq_left (le_of_lt h2.2), le_max_iff] at h
  apply le_antisymm h2.1
  exact h.elim (fun h => absurd hx (not_lt_of_ge h)) id

@[to_dual (attr := simp) iUnion_Ioc_eq_Ioi_self_iff]
theorem iUnion_Ico_eq_Iio_self_iff {f : ι → α} {a : α} :
    ⋃ i, Ico (f i) a = Iio a ↔ ∀ x < a, ∃ i, f i ≤ x := by
  simp [← Ici_inter_Iio, ← iUnion_inter, subset_def]

@[to_dual (attr := simp) biUnion_Ioc_eq_Ioi_self_iff]
theorem biUnion_Ico_eq_Iio_self_iff {p : ι → Prop} {f : ∀ i, p i → α} {a : α} :
    ⋃ (i) (hi : p i), Ico (f i hi) a = Iio a ↔ ∀ x < a, ∃ i hi, f i hi ≤ x := by
  simp [← Ici_inter_Iio, ← iUnion_inter, subset_def]

example {a₁ a₂ b₁ b₂ : α} : Disjoint (Ioc a₁ a₂) (Ioc b₁ b₂) ↔ min a₂ b₂ ≤ max a₁ b₁ :=
  Ioc_disjoint_Ioc
example {f : ι → α} {a : α} : ⋃ i, Ioc a (f i) = Ioi a ↔ ∀ x, a < x → ∃ i, x ≤ f i :=
  iUnion_Ioc_eq_Ioi_self_iff
example {p : ι → Prop} {f : ∀ i, p i → α} {a : α} :
    ⋃ (i) (hi : p i), Ioc a (f i hi) = Ioi a ↔ ∀ x, a < x → ∃ i hi, x ≤ f i hi :=
  biUnion_Ioc_eq_Ioi_self_iff

end LinearOrder

end Set

section UnionIxx

variable [LinearOrder α] {s : Set α} {a : α} {f : ι → α}

@[to_dual]
theorem IsGLB.biUnion_Ioi_eq (h : IsGLB s a) : ⋃ x ∈ s, Ioi x = Ioi a := by
  refine (iUnion₂_subset fun x hx => ?_).antisymm fun x hx => ?_
  · exact Ioi_subset_Ioi (h.1 hx)
  · rcases h.exists_between hx with ⟨y, hys, _, hyx⟩
    exact mem_biUnion hys hyx

@[to_dual]
theorem IsGLB.iUnion_Ioi_eq (h : IsGLB (range f) a) : ⋃ x, Ioi (f x) = Ioi a :=
  biUnion_range.symm.trans h.biUnion_Ioi_eq

@[to_dual]
theorem IsGLB.biUnion_Ici_eq_Ioi (a_glb : IsGLB s a) (a_notMem : a ∉ s) :
    ⋃ x ∈ s, Ici x = Ioi a := by
  refine (iUnion₂_subset fun x hx => ?_).antisymm fun x hx => ?_
  · exact Ici_subset_Ioi.mpr (lt_of_le_of_ne (a_glb.1 hx) fun h => (h ▸ a_notMem) hx)
  · rcases a_glb.exists_between hx with ⟨y, hys, _, hyx⟩
    rw [mem_iUnion₂]
    exact ⟨y, hys, hyx.le⟩

@[to_dual]
theorem IsGLB.biUnion_Ici_eq_Ici (a_glb : IsGLB s a) (a_mem : a ∈ s) :
    ⋃ x ∈ s, Ici x = Ici a := by
  refine (iUnion₂_subset fun x hx => ?_).antisymm fun x hx => ?_
  · exact Ici_subset_Ici.mpr (mem_lowerBounds.mp a_glb.1 x hx)
  · exact mem_iUnion₂.mpr ⟨a, a_mem, hx⟩

@[to_dual]
theorem iUnion_Ici_eq_Ioi_iInf {R : Type*} [CompleteLinearOrder R] {f : ι → R}
    (no_least_elem : ⨅ i, f i ∉ range f) : ⋃ i : ι, Ici (f i) = Ioi (⨅ i, f i) := by
  simp only [← IsGLB.biUnion_Ici_eq_Ioi (@isGLB_iInf _ _ _ f) no_least_elem, mem_range,
    iUnion_exists, iUnion_iUnion_eq']

@[to_dual]
theorem iUnion_Ici_eq_Ici_iInf {R : Type*} [CompleteLinearOrder R] {f : ι → R}
    (has_least_elem : (⨅ i, f i) ∈ range f) : ⋃ i : ι, Ici (f i) = Ici (⨅ i, f i) := by
  simp only [← IsGLB.biUnion_Ici_eq_Ici (@isGLB_iInf _ _ _ f) has_least_elem, mem_range,
    iUnion_exists, iUnion_iUnion_eq']

example (h : IsLUB s a) : ⋃ x ∈ s, Iio x = Iio a := h.biUnion_Iio_eq
example (h : IsLUB (range f) a) : ⋃ x, Iio (f x) = Iio a := h.iUnion_Iio_eq
example (a_lub : IsLUB s a) (a_notMem : a ∉ s) : ⋃ x ∈ s, Iic x = Iio a :=
  a_lub.biUnion_Iic_eq_Iio a_notMem
example (a_lub : IsLUB s a) (a_mem : a ∈ s) : ⋃ x ∈ s, Iic x = Iic a := a_lub.biUnion_Iic_eq_Iic a_mem
example {R : Type*} [CompleteLinearOrder R] {f : ι → R}
    (h : (⨆ i, f i) ∉ range f) : ⋃ i : ι, Iic (f i) = Iio (⨆ i, f i) := iUnion_Iic_eq_Iio_iSup h
example {R : Type*} [CompleteLinearOrder R] {f : ι → R}
    (h : (⨆ i, f i) ∈ range f) : ⋃ i : ι, Iic (f i) = Iic (⨆ i, f i) := iUnion_Iic_eq_Iic_iSup h

theorem iUnion_Iio_eq_univ_iff : ⋃ i, Iio (f i) = univ ↔ (¬ BddAbove (range f)) := by
  simp [not_bddAbove_iff, Set.eq_univ_iff_forall]

theorem iUnion_Iic_of_not_bddAbove_range (hf : ¬ BddAbove (range f)) : ⋃ i, Iic (f i) = univ := by
  refine Set.eq_univ_of_subset ?_ (iUnion_Iio_eq_univ_iff.mpr hf)
  gcongr
  exact Iio_subset_Iic_self

theorem iInter_Iic_eq_empty_iff : ⋂ i, Iic (f i) = ∅ ↔ ¬ BddBelow (range f) := by
  simp [not_bddBelow_iff, Set.eq_empty_iff_forall_notMem]

theorem iInter_Iio_of_not_bddBelow_range (hf : ¬ BddBelow (range f)) : ⋂ i, Iio (f i) = ∅ := by
  refine eq_empty_of_subset_empty ?_
  rw [← iInter_Iic_eq_empty_iff.mpr hf]
  gcongr
  exact Iio_subset_Iic_self

end UnionIxx
