# The PR model for #36822 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Order/Interval/Set/Disjoint): use `to_dual`
- description: (not recoverable at review start)
- changed files: Mathlib/Order/Filter/AtTopBot/Disjoint.lean, Mathlib/Order/Interval/Set/Disjoint.lean

## Objects

### `Filter.disjoint_atBot_atTop` (theorem, modified) [2405e8a385]
- file: `Mathlib/Order/Filter/AtTopBot/Disjoint.lean`; changed: attributes:added, name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem disjoint_pure_atBot [Preorder α] [NoBotOrder α] (x : α) : Disjoint (pure x) atBot :=
  @disjoint_pure_atTop αᵒᵈ _ _ _
```
- as the PR leaves it:
```lean
@[to_dual disjoint_atTop_atBot]
theorem disjoint_atBot_atTop [PartialOrder α] [Nontrivial α] :
    Disjoint (atBot : Filter α) atTop := by
  rcases exists_pair_ne α with ⟨x, y, hne⟩
  by_cases hle : x ≤ y
  · refine disjoint_of_disjoint_of_mem ?_ (Iic_mem_atBot x) (Ici_mem_atTop y)
    exact Iic_disjoint_Ici.2 (hle.lt_of_ne hne).not_ge
  · refine disjoint_of_disjoint_of_mem ?_ (Iic_mem_atBot y) (Ici_mem_atTop x)
    exact Iic_disjoint_Ici.2 hle
```

### `Filter.disjoint_atTop_atBot` (theorem, removed) [59a999d858]
- file: `Mathlib/Order/Filter/AtTopBot/Disjoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem disjoint_atTop_atBot [PartialOrder α] [Nontrivial α] : Disjoint (atTop : Filter α) atBot :=
  disjoint_atBot_atTop.symm
```

### `Filter.disjoint_atTop_principal_Iic` (theorem, modified) [5f6b29cc7a]
- file: `Mathlib/Order/Filter/AtTopBot/Disjoint.lean`; changed: attributes:added, name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem disjoint_atTop_principal_Iio [Preorder α] (x : α) : Disjoint atTop (𝓟 (Iio x)) :=
  @disjoint_atBot_principal_Ioi αᵒᵈ _ _
```
- as the PR leaves it:
```lean
@[to_dual disjoint_atBot_principal_Ici]
theorem disjoint_atTop_principal_Iic [Preorder α] [NoTopOrder α] (x : α) :
    Disjoint atTop (𝓟 (Iic x)) :=
  disjoint_of_disjoint_of_mem (Iic_disjoint_Ioi le_rfl).symm (Ioi_mem_atTop x)
    (mem_principal_self _)
```

### `Filter.disjoint_pure_atTop` (theorem, modified) [a3e7e3e2b6]
- file: `Mathlib/Order/Filter/AtTopBot/Disjoint.lean`; changed: attributes:added, name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem disjoint_atBot_principal_Ici [Preorder α] [NoBotOrder α] (x : α) :
    Disjoint atBot (𝓟 (Ici x)) :=
  @disjoint_atTop_principal_Iic αᵒᵈ _ _ _
```
- as the PR leaves it:
```lean
@[to_dual disjoint_pure_atBot]
theorem disjoint_pure_atTop [Preorder α] [NoTopOrder α] (x : α) : Disjoint (pure x) atTop :=
  Disjoint.symm <| (disjoint_atTop_principal_Iic x).mono_right <| le_principal_iff.2 <|
    mem_pure.2 self_mem_Iic
```

### `Filter.disjoint_atBot_principal_Ioi` (theorem, added) [b2b7efe3ff]
- file: `Mathlib/Order/Filter/AtTopBot/Disjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_dual disjoint_atTop_principal_Iio]
theorem disjoint_atBot_principal_Ioi [Preorder α] (x : α) : Disjoint atBot (𝓟 (Ioi x)) :=
  disjoint_of_disjoint_of_mem (Iic_disjoint_Ioi le_rfl) (Iic_mem_atBot x) (mem_principal_self _)
```

### `Set.Ioi_disjoint_Iio_iff` (theorem, modified) [0259a53585]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem Ioi_disjoint_Iio_iff [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b :=
  ⟨fun h hab ↦ (exists_between hab).elim
    fun _ hc ↦ h.notMem_of_mem_left hc.left hc.right,
    Ioi_disjoint_Iio_of_not_lt⟩
```
- as the PR leaves it:
```lean
@[to_dual Iio_disjoint_Ioi_iff]
theorem Ioi_disjoint_Iio_iff [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b :=
  ⟨fun h hab ↦ (exists_between hab).elim
    fun _ hc ↦ h.notMem_of_mem_left hc.left hc.right,
    Ioi_disjoint_Iio_of_not_lt⟩
```

### `Set.iUnion_Ioi` (theorem, removed) [02d072efc5]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Ioi [NoMinOrder α] : ⋃ a : α, Ioi a = univ :=
  iUnion_eq_univ_iff.2 exists_lt
```

### `Set.iUnion_Iio` (theorem, modified) [08cb6ae923]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Iio [NoMaxOrder α] : ⋃ a : α, Iio a = univ :=
  iUnion_eq_univ_iff.2 exists_gt
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp)]
theorem iUnion_Iio [NoMaxOrder α] : ⋃ a : α, Iio a = univ :=
  iUnion_eq_univ_iff.2 exists_gt
```

### `Set.Iic_disjoint_Ioi` (theorem, modified) [284f011663]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem Iic_disjoint_Ioi (h : a ≤ b) : Disjoint (Iic a) (Ioi b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt hb).not_ge ha
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) Ici_disjoint_Iio]
theorem Iic_disjoint_Ioi (h : a ≤ b) : Disjoint (Iic a) (Ioi b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt hb).not_ge ha
```

### `Set.iUnion_Ioo_right` (theorem, modified) [38de570a63]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Ioo_right [NoMaxOrder α] (a : α) : ⋃ b, Ioo a b = Ioi a := by
  simp only [← Ioi_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) iUnion_Ioo_left]
theorem iUnion_Ioo_right [NoMaxOrder α] (a : α) : ⋃ b, Ioo a b = Ioi a := by
  simp only [← Ioi_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]
```

### `Set.iUnion_Icc_left` (theorem, removed) [39080af29b]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Icc_left (b : α) : ⋃ a, Icc a b = Iic b := by
  simp only [← Ici_inter_Iic, ← iUnion_inter, iUnion_Ici, univ_inter]
```

### `Set.iUnion_Iic` (theorem, modified) [47940cb1b6]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Iic : ⋃ a : α, Iic a = univ :=
  iUnion_eq_univ_iff.2 fun x => ⟨x, self_mem_Iic⟩
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp)]
theorem iUnion_Iic : ⋃ a : α, Iic a = univ :=
  iUnion_eq_univ_iff.2 fun x => ⟨x, self_mem_Iic⟩
```

### `Set.Iio_disjoint_Ioi_of_le` (theorem, removed) [5b9ff93d4e]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem Iio_disjoint_Ioi_of_le (h : a ≤ b) : Disjoint (Iio a) (Ioi b) :=
  disjoint_comm.mp (Ioi_disjoint_Iio_of_le h)
```

### `Set.iUnion_Ioc_right` (theorem, modified) [65fa4da2c0]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Ioc_right (a : α) : ⋃ b, Ioc a b = Ioi a := by
  simp only [← Ioi_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) iUnion_Ico_left]
theorem iUnion_Ioc_right (a : α) : ⋃ b, Ioc a b = Ioi a := by
  simp only [← Ioi_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]
```

### `Set.Iic_disjoint_Ici` (theorem, removed) [7584e116c1]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem Iic_disjoint_Ici : Disjoint (Iic a) (Ici b) ↔ ¬b ≤ a :=
  disjoint_comm.trans Ici_disjoint_Iic
```

### `Set.iUnion_Ioc_left` (theorem, removed) [79cf96fb2a]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Ioc_left [NoMinOrder α] (b : α) : ⋃ a, Ioc a b = Iic b := by
  simp only [← Ioi_inter_Iic, ← iUnion_inter, iUnion_Ioi, univ_inter]
```

### `Set.Ici_disjoint_Iic` (theorem, modified) [92e72f783e]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem Ici_disjoint_Iic : Disjoint (Ici a) (Iic b) ↔ ¬a ≤ b := by
  rw [Set.disjoint_iff_inter_eq_empty, Ici_inter_Iic, Icc_eq_empty_iff]
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) Iic_disjoint_Ici]
theorem Ici_disjoint_Iic : Disjoint (Ici a) (Iic b) ↔ ¬a ≤ b := by
  rw [Set.disjoint_iff_inter_eq_empty, Ici_inter_Iic, Icc_eq_empty_iff]
```

### `Set.Ioi_disjoint_Iio_same` (theorem, modified) [92ec318bbc]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem Ioi_disjoint_Iio_same : Disjoint (Ioi a) (Iio a) :=
  Ioi_disjoint_Iio_of_le le_rfl
```
- as the PR leaves it:
```lean
@[to_dual Iio_disjoint_Ioi_same]
theorem Ioi_disjoint_Iio_same : Disjoint (Ioi a) (Iio a) :=
  Ioi_disjoint_Iio_of_le le_rfl
```

### `Set.iUnion_Ici` (theorem, removed) [994ced6121]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Ici : ⋃ a : α, Ici a = univ :=
  iUnion_eq_univ_iff.2 fun x => ⟨x, self_mem_Ici⟩
```

### `Set.iUnion_Icc_right` (theorem, modified) [a57ac0559a]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Icc_right (a : α) : ⋃ b, Icc a b = Ici a := by
  simp only [← Ici_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) iUnion_Icc_left]
theorem iUnion_Icc_right (a : α) : ⋃ b, Icc a b = Ici a := by
  simp only [← Ici_inter_Iic, ← inter_iUnion, iUnion_Iic, inter_univ]
```

### `Set.Iio_disjoint_Ioi_of_not_lt` (theorem, removed) [ac298f7fcc]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem Iio_disjoint_Ioi_of_not_lt (h : ¬a < b) : Disjoint (Iio b) (Ioi a) :=
  disjoint_comm.mp (Ioi_disjoint_Iio_of_not_lt h)
```

### `Set.Ioi_disjoint_Iio_of_le` (theorem, added) [b4e238720b]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_dual Iio_disjoint_Ioi_of_le]
theorem Ioi_disjoint_Iio_of_le (h : a ≤ b) : Disjoint (Ioi b) (Iio a) :=
  Ioi_disjoint_Iio_of_not_lt (not_lt_of_ge h)
```

### `Set.Iio_disjoint_Ici` (theorem, modified) [bd3b7ebf44]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem Iio_disjoint_Ici (h : a ≤ b) : Disjoint (Iio a) (Ici b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt' ha).not_ge hb
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) Ioi_disjoint_Iic]
theorem Iio_disjoint_Ici (h : a ≤ b) : Disjoint (Iio a) (Ici b) :=
  disjoint_left.mpr fun _ ha hb => (h.trans_lt' ha).not_ge hb
```

### `Set.iUnion_Ico_right` (theorem, modified) [bf7dbb3a4a]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:modified
- before the PR:
```lean
@[simp]
theorem iUnion_Ico_right [NoMaxOrder α] (a : α) : ⋃ b, Ico a b = Ici a := by
  simp only [← Ici_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]
```
- as the PR leaves it:
```lean
@[to_dual (attr := simp) iUnion_Ioc_left]
theorem iUnion_Ico_right [NoMaxOrder α] (a : α) : ⋃ b, Ico a b = Ici a := by
  simp only [← Ici_inter_Iio, ← inter_iUnion, iUnion_Iio, inter_univ]
```

### `Set.Ioi_disjoint_Iio_of_not_lt` (theorem, added) [c0b7b22f90]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_dual Iio_disjoint_Ioi_of_not_lt]
theorem Ioi_disjoint_Iio_of_not_lt (h : ¬a < b) : Disjoint (Ioi a) (Iio b) :=
  disjoint_left.mpr fun _ hx hy ↦ h (hx.trans hy)
```

### `Set.iUnion_Ioo_left` (theorem, removed) [c2bf4b2dfd]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Ioo_left [NoMinOrder α] (b : α) : ⋃ a, Ioo a b = Iio b := by
  simp only [← Ioi_inter_Iio, ← iUnion_inter, iUnion_Ioi, univ_inter]
```

### `Set.iUnion_Ico_left` (theorem, removed) [d63de983bd]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem iUnion_Ico_left (b : α) : ⋃ a, Ico a b = Iio b := by
  simp only [← Ici_inter_Iio, ← iUnion_inter, iUnion_Ici, univ_inter]
```

### `Set.Iio_disjoint_Ioi_iff` (theorem, removed) [e804e2070d]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem Iio_disjoint_Ioi_iff [DenselyOrdered α] : Disjoint (Iio a) (Ioi b) ↔ ¬b < a :=
  disjoint_comm.trans Ioi_disjoint_Iio_iff
```

### `Set.Iio_disjoint_Ioi_same` (theorem, removed) [e94d4733d9]
- file: `Mathlib/Order/Interval/Set/Disjoint.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[simp]
theorem Iio_disjoint_Ioi_same : Disjoint (Iio a) (Ioi a) :=
  Iio_disjoint_Ioi_of_le le_rfl
```

## Removed or renamed

- `Filter.disjoint_atTop_atBot`
- `Set.iUnion_Ioi`
- `Set.iUnion_Icc_left`
- `Set.Iio_disjoint_Ioi_of_le`
- `Set.Iic_disjoint_Ici`
- `Set.iUnion_Ioc_left`
- `Set.iUnion_Ici`
- `Set.Iio_disjoint_Ioi_of_not_lt`
- `Set.iUnion_Ioo_left`
- `Set.iUnion_Ico_left`
- `Set.Iio_disjoint_Ioi_iff`
- `Set.Iio_disjoint_Ioi_same`

## Families (declarations that may be one decision)

- [hypothesis] `Set.iUnion_Icc_left`, `Set.iUnion_Icc_right`, `Set.iUnion_Ici`, `Set.iUnion_Ico_left`, `Set.iUnion_Ico_right`, `Set.iUnion_Iic`, `Set.iUnion_Iio`, `Set.iUnion_Ioc_left`, `Set.iUnion_Ioc_right`, `Set.iUnion_Ioi`, `Set.iUnion_Ioo_left`, `Set.iUnion_Ioo_right` -- 12 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Set.Ici_disjoint_Iic`, `Set.Iic_disjoint_Ici`, `Set.Iic_disjoint_Ioi`, `Set.Iio_disjoint_Ici`, `Set.Iio_disjoint_Ioi_iff`, `Set.Iio_disjoint_Ioi_of_le`, `Set.Iio_disjoint_Ioi_of_not_lt`, `Set.Iio_disjoint_Ioi_same`, `Set.Ioi_disjoint_Iio_iff`, `Set.Ioi_disjoint_Iio_of_le`, `Set.Ioi_disjoint_Iio_of_not_lt`, `Set.Ioi_disjoint_Iio_same`, `Set.iUnion_Icc_right`, `Set.iUnion_Ico_right`, `Set.iUnion_Iic`, `Set.iUnion_Iio`, `Set.iUnion_Ioc_right`, `Set.iUnion_Ioo_right` -- 18 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Set.Iic_disjoint_Ici`, `Set.Iic_disjoint_Ioi` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Set.Iio_disjoint_Ici`, `Set.Iio_disjoint_Ioi_iff`, `Set.Iio_disjoint_Ioi_of_le`, `Set.Iio_disjoint_Ioi_of_not_lt`, `Set.Iio_disjoint_Ioi_same` -- 5 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Set.Ioi_disjoint_Iio_iff`, `Set.Ioi_disjoint_Iio_of_le`, `Set.Ioi_disjoint_Iio_of_not_lt`, `Set.Ioi_disjoint_Iio_same` -- 4 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Filter.disjoint_atBot_atTop`, `Filter.disjoint_atBot_principal_Ioi`, `Filter.disjoint_atTop_atBot`, `Filter.disjoint_atTop_principal_Iic`, `Filter.disjoint_pure_atTop` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Filter.disjoint_atBot_atTop` -> `Filter.disjoint_pure_atTop`
- changed_siblings [high]: `Filter.disjoint_atBot_principal_Ioi` -> `Filter.disjoint_atTop_principal_Iic`
- changed_siblings [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_pure_atTop`
- changed_siblings [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_atBot_principal_Ioi`
- changed_siblings [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atTop_principal_Iic`
- changed_siblings [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atBot_atTop`
- changed_siblings [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ici`
- changed_siblings [high]: `Set.Iio_disjoint_Ici` -> `Set.Iic_disjoint_Ioi`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.iUnion_Iic`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ioi_disjoint_Iio_same`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_same`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Ioi_disjoint_Iio_of_le`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_of_le`
- changed_siblings [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_iff`
- changed_siblings [high]: `Set.iUnion_Icc_right` -> `Set.iUnion_Iic`
- changed_siblings [high]: `Set.iUnion_Icc_right` -> `Set.iUnion_Ioc_right`
- changed_siblings [high]: `Set.iUnion_Ico_right` -> `Set.iUnion_Ioo_right`
- changed_siblings [high]: `Set.iUnion_Ico_right` -> `Set.iUnion_Iio`
- changed_siblings [high]: `Set.iUnion_Iic` -> `Set.iUnion_Icc_right`
- changed_siblings [high]: `Set.iUnion_Iic` -> `Set.Ioi_disjoint_Iio_iff`
- changed_siblings [high]: `Set.iUnion_Iio` -> `Set.iUnion_Ico_right`
- changed_siblings [high]: `Set.iUnion_Iio` -> `Set.iUnion_Ioc_right`
- changed_siblings [high]: `Set.iUnion_Ioc_right` -> `Set.iUnion_Iio`
- changed_siblings [high]: `Set.iUnion_Ioc_right` -> `Set.iUnion_Icc_right`
- changed_siblings [high]: `Set.iUnion_Ioo_right` -> `Set.iUnion_Ico_right`
- direct_use_of_changed_declaration [exact]: `Filter.disjoint_atBot_atTop` -> `Set.Iic_disjoint_Ici`
- direct_use_of_changed_declaration [exact]: `Filter.disjoint_atBot_principal_Ioi` -> `Set.Iic_disjoint_Ioi`
- direct_use_of_changed_declaration [exact]: `Filter.disjoint_atTop_atBot` -> `Filter.disjoint_atBot_atTop`
- direct_use_of_changed_declaration [exact]: `Filter.disjoint_atTop_principal_Iic` -> `Set.Iic_disjoint_Ioi`
- direct_use_of_changed_declaration [exact]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atTop_principal_Iic`
- direct_use_of_changed_declaration [exact]: `Set.Iic_disjoint_Ici` -> `Set.Ici_disjoint_Iic`
- direct_use_of_changed_declaration [exact]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ioi_disjoint_Iio_iff`
- direct_use_of_changed_declaration [exact]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ioi_disjoint_Iio_of_le`
- direct_use_of_changed_declaration [exact]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- direct_use_of_changed_declaration [exact]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iio_disjoint_Ioi_of_le`
- direct_use_of_changed_declaration [exact]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- direct_use_of_changed_declaration [exact]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- direct_use_of_changed_declaration [exact]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_of_le`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Icc_left` -> `Set.iUnion_Ici`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Icc_right` -> `Set.iUnion_Iic`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ico_left` -> `Set.iUnion_Ici`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ico_right` -> `Set.iUnion_Iio`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ioc_left` -> `Set.iUnion_Ioi`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ioc_right` -> `Set.iUnion_Iic`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ioo_left` -> `Set.iUnion_Ioi`
- direct_use_of_changed_declaration [exact]: `Set.iUnion_Ioo_right` -> `Set.iUnion_Iio`
- name_family [high]: `Filter.disjoint_atBot_atTop` -> `Filter.disjoint_pure_atTop`
- name_family [high]: `Filter.disjoint_atBot_atTop` -> `Filter.disjoint_atTop_principal_Iic`
- name_family [high]: `Filter.disjoint_atBot_atTop` -> `Filter.disjoint_atBot_principal_Ioi`
- name_family [high]: `Filter.disjoint_atBot_atTop` -> `Filter.disjoint_atTop_atBot`
- name_family [high]: `Filter.disjoint_atBot_principal_Ioi` -> `Filter.disjoint_atTop_principal_Iic`
- name_family [high]: `Filter.disjoint_atBot_principal_Ioi` -> `Filter.disjoint_pure_atTop`
- name_family [high]: `Filter.disjoint_atBot_principal_Ioi` -> `Filter.disjoint_atBot_atTop`
- name_family [high]: `Filter.disjoint_atBot_principal_Ioi` -> `Filter.disjoint_atTop_atBot`
- name_family [high]: `Filter.disjoint_atTop_atBot` -> `Filter.disjoint_pure_atTop`
- name_family [high]: `Filter.disjoint_atTop_atBot` -> `Filter.disjoint_atBot_principal_Ioi`
- name_family [high]: `Filter.disjoint_atTop_atBot` -> `Filter.disjoint_atBot_atTop`
- name_family [high]: `Filter.disjoint_atTop_atBot` -> `Filter.disjoint_atTop_principal_Iic`
- name_family [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_atBot_atTop`
- name_family [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_atBot_principal_Ioi`
- name_family [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_pure_atTop`
- name_family [high]: `Filter.disjoint_atTop_principal_Iic` -> `Filter.disjoint_atTop_atBot`
- name_family [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atBot_atTop`
- name_family [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atTop_principal_Iic`
- name_family [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atTop_atBot`
- name_family [high]: `Filter.disjoint_pure_atTop` -> `Filter.disjoint_atBot_principal_Ioi`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Ici_disjoint_Iic` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iic_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iic_disjoint_Ioi` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iio_disjoint_Ici` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_iff` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_le` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_of_not_lt` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Iio_disjoint_Ioi_same` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_iff` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_le` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Ioi_disjoint_Iio_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Ioi_disjoint_Iio_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Ioi_disjoint_Iio_of_not_lt` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iic_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iio_disjoint_Ioi_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iio_disjoint_Ici`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ici_disjoint_Iic`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_of_not_lt`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iio_disjoint_Ioi_of_le`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iio_disjoint_Ioi_iff`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iio_disjoint_Ioi_same`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Iic_disjoint_Ioi`
- name_family [high]: `Set.Ioi_disjoint_Iio_same` -> `Set.Ioi_disjoint_Iio_iff`
