# The PR model for #33421 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(Algebra/Order/Floor): review API about `round`
- description: (not recoverable at review start)
- changed files: Mathlib/Algebra/AddConstMap/Basic.lean, Mathlib/Algebra/Order/Archimedean/Basic.lean, Mathlib/Algebra/Order/Floor/Ring.lean, Mathlib/Algebra/Order/Round.lean, Mathlib/Algebra/Order/ToIntervalMod.lean, Mathlib/Analysis/CStarAlgebra/ApproximateUnit.lean, Mathlib/Analysis/SpecialFunctions/Complex/Arctan.lean, Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean, Mathlib/GroupTheory/Archimedean.lean, Mathlib/MeasureTheory/Integral/IntervalIntegral/Basic.lean, Mathlib/MeasureTheory/Integral/IntervalIntegral/DerivIntegrable.lean, Mathlib/NumberTheory/Transcendental/Liouville/Basic.lean, Mathlib/Order/Filter/AtTopBot/Archimedean.lean, Mathlib/Topology/Algebra/Order/Floor.lean, Mathlib/Topology/Instances/AddCircle/Defs.lean

## Objects

### `import in Basic.lean` (import, modified) [993cfb208a]
- file: `Mathlib/Algebra/AddConstMap/Basic.lean`; changed: imports:added

### `import in Basic.lean` (import, modified) [d8dfada119]
- file: `Mathlib/Algebra/Order/Archimedean/Basic.lean`; changed: imports:added

### `Int.ceil_one_add` (theorem, added) [01631f49e4]
- file: `Mathlib/Algebra/Order/Floor/Ring.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem ceil_one_add (a : R) : ⌈1 + a⌉ = 1 + ⌈a⌉ :=
  mod_cast ceil_natCast_add 1 a
```

### `Int.two_mul_fract_eq_one_iff_exists_int` (theorem, added) [01e92e863a]
- file: `Mathlib/Algebra/Order/Floor/Ring.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem two_mul_fract_eq_one_iff_exists_int {x : R} :
    2 * fract x = 1 ↔ ∃ n : ℤ, 2 * x = 2 * n + 1 := by
  rw [fract, mul_sub, sub_eq_iff_eq_add']
  refine ⟨fun hx ↦ ⟨⌊x⌋, hx⟩, ?_⟩
  rintro ⟨n, hn⟩
  convert hn
  rw [floor_eq_iff, ← mul_le_mul_iff_right₀ two_pos, ← mul_lt_mul_iff_right₀ two_pos, hn]
  simp [mul_add]
```

### `Int.ceil_intCast_add` (theorem, added) [116affb7ad]
- file: `Mathlib/Algebra/Order/Floor/Ring.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem ceil_intCast_add (z : ℤ) (a : R) : ⌈z + a⌉ = z + ⌈a⌉ := by
  rw [add_comm, ceil_add_intCast, add_comm]
```

### `Int.ceil_natCast_add` (theorem, added) [452977369c]
- file: `Mathlib/Algebra/Order/Floor/Ring.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem ceil_natCast_add (n : ℕ) (a : R) : ⌈n + a⌉ = n + ⌈a⌉ :=
  mod_cast ceil_intCast_add n a
```

### `Int.ceil_ofNat_add` (theorem, added) [83b38f0f0a]
- file: `Mathlib/Algebra/Order/Floor/Ring.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[simp]
theorem ceil_ofNat_add (n : ℕ) [n.AtLeastTwo] (a : R) :
    ⌈ofNat(n) + a⌉ = ofNat(n) + ⌈a⌉ :=
  ceil_natCast_add n a
```

### `round_two_inv` (theorem, modified) [08368604d9]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem round_two_inv : round (2⁻¹ : α) = 1 := by
  simp only [round_eq, ← one_div, add_halves, floor_one]
```
- as the PR leaves it:
```lean
@[simp]
theorem round_two_inv : round (2⁻¹ : α) = 1 := by norm_num [round_eq_iff]
```

### `round_neg_two_inv` (theorem, modified) [48dd86b24e]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem round_neg_two_inv : round (-2⁻¹ : α) = 0 := by
  simp only [round_eq, ← one_div, neg_add_cancel, floor_zero]
```
- as the PR leaves it:
```lean
@[simp]
theorem round_neg_two_inv : round (-2⁻¹ : α) = 0 := by norm_num [round_eq_iff]
```

### `round_eq'` (theorem, added) [4dc53e2112]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem round_eq' (x : α) : round x = (⌊2 * x⌋ + 1) / 2 := by
  rw [← floor_add_fract x, round, fract_intCast_add, fract_fract, floor_intCast_add, mul_add,
    ← Int.cast_ofNat, ← Int.cast_mul, floor_intCast_add, ceil_intCast_add, add_assoc,
    Int.mul_add_ediv_left _ _ two_ne_zero, Int.cast_ofNat]
  split_ifs with h <;> congr 1
  · rw [Int.floor_eq_zero_iff.mpr, Int.floor_eq_zero_iff.mpr]
    · simp
    · simp [h]
    · suffices fract x < 1 by simpa
      refine lt_of_le_of_lt ?_ h
      apply le_mul_of_one_le_left <;> simp
  · have H : ⌊2 * fract x⌋ = 1 := by simpa [floor_eq_iff, ← two_mul, fract_lt_one] using h
    suffices 0 < fract x by simp [this, H, ceil_eq_iff, (fract_lt_one _).le]
    contrapose! h
    grw [h]
    simp
```

### `round_eq_half_ceil_two_mul` (theorem, added) [5342958971]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem round_eq_half_ceil_two_mul {x : α} (hx : 2 * fract x ≠ 1) : round x = ⌈2 * x⌉ / 2 := by
  rcases em (2 * x ∈ range Int.cast) with ⟨m, hm⟩ | hx'
  · rw [← hm, ceil_intCast]
    rcases m.even_or_odd with ⟨m, rfl⟩ | ⟨m, rfl⟩
    · obtain rfl : m = x := mul_left_cancel₀ two_ne_zero <| by simp [← hm, ← two_mul]
      rw [round_intCast, ← two_mul, Int.mul_ediv_cancel_left _ two_ne_zero]
    · refine absurd ?_ hx
      exact two_mul_fract_eq_one_iff_exists_int.mpr ⟨m, mod_cast hm.symm⟩
  · rw [round_eq', (ceil_eq_floor_add_one_iff_notMem _).mpr hx']
```

### `command in Round.lean` (command, added) [85f47721bc]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Formula for `round` in terms of `Int.floor`, a version that works over any ring.

TODO: decide if we want to use this as a definition. It may be slightly faster over `ℚ`. -/
```

### `round_eq` (theorem, modified) [94ea28758e]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: proof:modified
- before the PR:
```lean
theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
  simp_rw [round, (by simp only [lt_div_iff₀', two_pos] : 2 * fract x < 1 ↔ fract x < 1 / 2)]
  rcases lt_or_ge (fract x) (1 / 2) with hx | hx
  · conv_rhs => rw [← fract_add_floor x, add_assoc, add_left_comm, floor_intCast_add]
    rw [if_pos hx, left_eq_add, floor_eq_iff, cast_zero, zero_add]
    constructor
    · linarith [fract_nonneg x]
    · linarith
  · have : ⌊fract x + 1 / 2⌋ = 1 := by
      rw [floor_eq_iff]
      constructor
      · norm_num
        linarith
      · norm_num
        linarith [fract_lt_one x]
    rw [if_neg (not_lt.mpr hx), ← fract_add_floor x, add_assoc, add_left_comm, floor_intCast_add,
      ceil_add_intCast, add_comm _ ⌊x⌋, add_right_inj, ceil_eq_iff, this, cast_one, sub_self]
    constructor
    · linarith
    · linarith [fract_lt_one x]
```
- as the PR leaves it:
```lean
theorem round_eq (x : α) : round x = ⌊x + 1 / 2⌋ := by
  rw [← cast_mul_floor_div_cancel_of_pos two_pos, round_eq']
  simp [mul_add]
```

### `round_eq_iff` (theorem, added) [bdbe328e92]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem round_eq_iff {x : α} {n : ℤ} : round x = n ↔ x ∈ Ico (n - 1 / 2 : α) (n + 1 / 2) := by
  norm_num [round_eq, floor_eq_iff, ← lt_sub_iff_add_lt, add_sub_assoc]
```

### `import in Round.lean` (import, modified) [c6016be7ce]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: imports:modified

### `round_eq_zero_iff` (theorem, modified) [c9074a90dc]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: proof:modified
- before the PR:
```lean
@[simp]
theorem round_eq_zero_iff {x : α} : round x = 0 ↔ x ∈ Ico (-(1 / 2)) ((1 : α) / 2) := by
  rw [round_eq, floor_eq_zero_iff, add_mem_Ico_iff_left]
  norm_num
```
- as the PR leaves it:
```lean
@[simp]
theorem round_eq_zero_iff {x : α} : round x = 0 ↔ x ∈ Ico (-(1 / 2)) ((1 : α) / 2) := by
  simp [round_eq_iff]
```

### `command in Round.lean` (command, added) [f537b795eb]
- file: `Mathlib/Algebra/Order/Round.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- Away from the points with fractional part `1 / 2`, `round x = ⌈2 * x⌉ / 2`. -/
```

### `import in ToIntervalMod.lean` (import, modified) [80dd71c892]
- file: `Mathlib/Algebra/Order/ToIntervalMod.lean`; changed: imports:added

### `import in ApproximateUnit.lean` (import, modified) [0557c61d7e]
- file: `Mathlib/Analysis/CStarAlgebra/ApproximateUnit.lean`; changed: imports:added

### `import in Arctan.lean` (import, modified) [a0381bce3c]
- file: `Mathlib/Analysis/SpecialFunctions/Complex/Arctan.lean`; changed: imports:added

### `import in GrowsPolynomially.lean` (import, modified) [b45a8e7a0a]
- file: `Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean`; changed: imports:added

### `import in Archimedean.lean` (import, modified) [504b22865e]
- file: `Mathlib/GroupTheory/Archimedean.lean`; changed: imports:added

### `import in Basic.lean` (import, modified) [cb4aa6b0f5]
- file: `Mathlib/MeasureTheory/Integral/IntervalIntegral/Basic.lean`; changed: imports:added

### `import in DerivIntegrable.lean` (import, modified) [337f3e0e4c]
- file: `Mathlib/MeasureTheory/Integral/IntervalIntegral/DerivIntegrable.lean`; changed: imports:added

### `import in Basic.lean` (import, modified) [8feeb4bd74]
- file: `Mathlib/NumberTheory/Transcendental/Liouville/Basic.lean`; changed: imports:added

### `import in Archimedean.lean` (import, modified) [d9545d6432]
- file: `Mathlib/Order/Filter/AtTopBot/Archimedean.lean`; changed: imports:added

### `import in Floor.lean` (import, modified) [271d169c31]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: imports:added

### `tendsto_round_nhdsGE_pure` (theorem, added) [2bce3a14f3]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem tendsto_round_nhdsGE_pure [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]
    (x : α) : Tendsto round (𝓝[≥] x) (pure (round x)) := by
  rw [funext round_eq']
  have : Tendsto (2 * ·) (𝓝[≥] x) (𝓝[≥] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_le_add ha ha
  exact (tendsto_pure_pure (fun n ↦ (n + 1) / 2) _).comp <|
    (tendsto_floor_right_pure_floor (2 * x)).comp this
```

### `tendsto_round_nhdsLT_pure_half_ceil` (theorem, added) [358ee7067b]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem tendsto_round_nhdsLT_pure_half_ceil [IsStrictOrderedRing α] [OrderClosedTopology α]
    [ContinuousAdd α] (x : α) : Tendsto round (𝓝[<] x) (pure (⌈2 * x⌉ / 2)) := by
  rw [funext round_eq', tendsto_pure]
  have : Tendsto (2 * ·) (𝓝[<] x) (𝓝[<] (2 * x)) := by
    simp only [two_mul]
    refine (tendsto_id.add tendsto_id).inf (tendsto_principal_principal.2 ?_)
    exact fun a ha ↦ add_lt_add ha ha
  filter_upwards [tendsto_pure.mp ((tendsto_floor_left_pure_ceil_sub_one (2 * x)).comp this)]
    using by simp +contextual
```

### `section in Floor.lean` (command, modified) [3cdfea9051]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: namespace:modified
- before the PR:
```lean
variable [IsStrictOrderedRing α] [OrderClosedTopology α]

omit [IsStrictOrderedRing α] in
```
- as the PR leaves it:
```lean
variable [OrderClosedTopology α]
```

### `continuousOn_fract` (theorem, modified) [3db96f3646]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: proof:modified
- before the PR:
```lean
theorem continuousOn_fract [IsTopologicalAddGroup α] (n : ℤ) :
    ContinuousOn (fract : α → α) (Ico n (n + 1) : Set α) :=
  continuousOn_id.sub (continuousOn_floor n)
```
- as the PR leaves it:
```lean
theorem continuousOn_fract [IsTopologicalAddGroup α] (n : ℤ) :
    ContinuousOn (fract : α → α) (Ico n (n + 1) : Set α) :=
  continuousOn_id.sub (continuous_of_discreteTopology.comp_continuousOn (continuousOn_floor n))
```

### `continuousOn_floor` (theorem, modified) [3eb6666ff6]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem continuousOn_floor (n : ℤ) :
    ContinuousOn (fun x => floor x : α → α) (Ico n (n + 1) : Set α) :=
  (continuousOn_congr <| floor_eq_on_Ico' n).mpr continuousOn_const
```
- as the PR leaves it:
```lean
theorem continuousOn_floor (n : ℤ) :
    ContinuousOn (fun x => floor x : α → ℤ) (Ico n (n + 1) : Set α) :=
  (continuousOn_congr <| floor_eq_on_Ico n).mpr continuousOn_const
```

### `continuousOn_round` (theorem, added) [43cf32d8c0]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem continuousOn_round [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α] :
    ContinuousOn round {x : α | 2 * fract x ≠ 1} :=
  fun _x hx ↦ (continuousAt_round hx).continuousWithinAt
```

### `section in Floor.lean` (command, removed) [6141c2be45]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: namespace:removed
- before the PR:
```lean
variable [IsStrictOrderedRing α] [OrderClosedTopology α]

omit [IsStrictOrderedRing α] in
```

### `continuousAt_round` (theorem, added) [9380c669f0]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem continuousAt_round [IsStrictOrderedRing α] [OrderClosedTopology α] [ContinuousAdd α]
    {x : α} (hx : 2 * fract x ≠ 1) : ContinuousAt round x := by
  rw [continuousAt_iff_continuous_left'_right']
  refine ⟨(tendsto_round_nhdsLT_pure_half_ceil x).mono_right (pure_le_nhds_iff.mpr ?_),
    (tendsto_round_nhdsGE_pure x).mono_left ?_ |>.mono_right (pure_le_nhds _)⟩
  · rw [round_eq_half_ceil_two_mul hx]
  · gcongr
    apply Ioi_subset_Ici_self
```

### `continuousOn_floor_compl_range` (theorem, added) [9ad642fa7b]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem continuousOn_floor_compl_range : ContinuousOn (floor : α → ℤ) (range Int.cast)ᶜ := by
  intro x hx
  refine (continuousAt_floor ?_).continuousWithinAt
  simp_all [eq_comm]
```

### `continuousAt_floor` (theorem, added) [a58150966f]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem continuousAt_floor {x : α} (hx : x ≠ ⌊x⌋) : ContinuousAt floor x :=
  (continuousOn_floor ⌊x⌋).continuousAt <|
    Ico_mem_nhds ((floor_le x).lt_of_ne hx.symm) (lt_floor_add_one x)
```

### `ContinuousOn.comp_fract''` (theorem, added) [af9a1cc8be]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem ContinuousOn.comp_fract'' {f : α → β} (h : ContinuousOn f I) (hf : f 0 = f 1) :
    Continuous (f ∘ fract) :=
  ContinuousOn.comp_fract (h.comp continuousOn_snd fun _x hx => (mem_prod.mp hx).2) continuous_id
    fun _ => hf
```

### `continuousAt_ceil` (theorem, added) [b072f20729]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem continuousAt_ceil {x : α} (hx : x ≠ ⌊x⌋) : ContinuousAt ceil x :=
  (continuousOn_ceil ⌈x⌉).continuousAt <|
    Ioc_mem_nhds (sub_lt_iff_lt_add.mpr <| ceil_lt_add_one _) <| (le_ceil x).lt_of_ne fun h ↦
      hx <| by rw [h, floor_intCast]
```

### `section in Floor.lean` (command, added) [b1393ad66f]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [IsStrictOrderedRing α]
```

### `continuousAt_fract` (theorem, modified) [c4f30391be]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: proof:modified
- before the PR:
```lean
theorem continuousAt_fract [OrderClosedTopology α] [IsTopologicalAddGroup α]
    {x : α} (h : x ≠ ⌊x⌋) : ContinuousAt fract x :=
  (continuousOn_fract ⌊x⌋).continuousAt <|
    Ico_mem_nhds ((floor_le _).lt_of_ne h.symm) (lt_floor_add_one _)
```
- as the PR leaves it:
```lean
theorem continuousAt_fract [OrderClosedTopology α] [IsTopologicalAddGroup α]
    {x : α} (h : x ≠ ⌊x⌋) : ContinuousAt fract x :=
  continuousAt_id.sub <| continuous_of_discreteTopology.continuousAt.comp <|
    continuousAt_floor h
```

### `section in Floor.lean` (command, added) [d0806eab9e]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Ring
```

### `continuousOn_ceil_compl_range` (theorem, added) [e40933514e]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[fun_prop]
theorem continuousOn_ceil_compl_range : ContinuousOn (ceil : α → ℤ) (range Int.cast)ᶜ := by
  intro x hx
  refine (continuousAt_ceil ?_).continuousWithinAt
  simp_all [eq_comm]
```

### `section in Floor.lean` (command, added) [ecdb95dec2]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Ring
```

### `continuousOn_ceil` (theorem, modified) [fade5bb6f3]
- file: `Mathlib/Topology/Algebra/Order/Floor.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem continuousOn_ceil [IsStrictOrderedRing α] (n : ℤ) :
    ContinuousOn (fun x => ceil x : α → α) (Ioc (n - 1) n : Set α) :=
  (continuousOn_congr <| ceil_eq_on_Ioc' n).mpr continuousOn_const
```
- as the PR leaves it:
```lean
theorem continuousOn_ceil (n : ℤ) :
    ContinuousOn (fun x => ceil x : α → ℤ) (Ioc (n - 1) n : Set α) :=
  (continuousOn_congr <| ceil_eq_on_Ioc n).mpr continuousOn_const
```

### `import in Defs.lean` (import, modified) [97003adff6]
- file: `Mathlib/Topology/Instances/AddCircle/Defs.lean`; changed: imports:added

## Removed or renamed

- `section in Floor.lean`

## Families (declarations that may be one decision)

- [exact] `round_eq`, `round_eq_iff`, `round_eq_zero_iff`, `round_neg_two_inv`, `round_two_inv` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Int.ceil_intCast_add`, `Int.ceil_natCast_add`, `Int.ceil_ofNat_add`, `Int.ceil_one_add` -- 4 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `continuousAt_ceil`, `continuousOn_ceil_compl_range` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `continuousOn_ceil`, `continuousOn_floor` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `continuousAt_fract`, `continuousAt_round`, `continuousOn_fract`, `continuousOn_round`, `tendsto_round_nhdsGE_pure`, `tendsto_round_nhdsLT_pure_half_ceil` -- 6 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `continuousAt_floor`, `continuousOn_floor_compl_range` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `continuousAt_ceil` -> `continuousOn_ceil_compl_range`
- changed_siblings [high]: `continuousAt_floor` -> `continuousOn_floor_compl_range`
- changed_siblings [high]: `continuousAt_fract` -> `continuousOn_fract`
- changed_siblings [high]: `continuousAt_fract` -> `tendsto_round_nhdsGE_pure`
- changed_siblings [high]: `continuousAt_round` -> `tendsto_round_nhdsLT_pure_half_ceil`
- changed_siblings [high]: `continuousAt_round` -> `continuousOn_round`
- changed_siblings [high]: `continuousOn_ceil` -> `continuousOn_floor`
- changed_siblings [high]: `continuousOn_ceil_compl_range` -> `continuousAt_ceil`
- changed_siblings [high]: `continuousOn_floor` -> `continuousOn_ceil`
- changed_siblings [high]: `continuousOn_floor_compl_range` -> `continuousAt_floor`
- changed_siblings [high]: `continuousOn_fract` -> `continuousAt_fract`
- changed_siblings [high]: `continuousOn_round` -> `continuousAt_round`
- changed_siblings [high]: `round_eq` -> `round_eq_iff`
- changed_siblings [high]: `round_eq_iff` -> `round_two_inv`
- changed_siblings [high]: `round_eq_iff` -> `round_eq`
- changed_siblings [high]: `round_eq_zero_iff` -> `round_neg_two_inv`
- changed_siblings [high]: `round_neg_two_inv` -> `round_two_inv`
- changed_siblings [high]: `round_neg_two_inv` -> `round_eq_zero_iff`
- changed_siblings [high]: `round_two_inv` -> `round_eq_iff`
- changed_siblings [high]: `round_two_inv` -> `round_neg_two_inv`
- changed_siblings [high]: `tendsto_round_nhdsGE_pure` -> `tendsto_round_nhdsLT_pure_half_ceil`
- changed_siblings [high]: `tendsto_round_nhdsGE_pure` -> `continuousAt_fract`
- changed_siblings [high]: `tendsto_round_nhdsLT_pure_half_ceil` -> `tendsto_round_nhdsGE_pure`
- changed_siblings [high]: `tendsto_round_nhdsLT_pure_half_ceil` -> `continuousAt_round`
- direct_use_of_changed_declaration [exact]: `Int.ceil_natCast_add` -> `Int.ceil_intCast_add`
- direct_use_of_changed_declaration [exact]: `Int.ceil_ofNat_add` -> `Int.ceil_natCast_add`
- direct_use_of_changed_declaration [exact]: `Int.ceil_one_add` -> `Int.ceil_natCast_add`
- direct_use_of_changed_declaration [exact]: `continuousAt_ceil` -> `continuousOn_ceil`
- direct_use_of_changed_declaration [exact]: `continuousAt_floor` -> `continuousOn_floor`
- direct_use_of_changed_declaration [exact]: `continuousAt_fract` -> `continuousAt_floor`
- direct_use_of_changed_declaration [exact]: `continuousAt_round` -> `round_eq_half_ceil_two_mul`
- direct_use_of_changed_declaration [exact]: `continuousAt_round` -> `tendsto_round_nhdsGE_pure`
- direct_use_of_changed_declaration [exact]: `continuousAt_round` -> `tendsto_round_nhdsLT_pure_half_ceil`
- direct_use_of_changed_declaration [exact]: `continuousOn_ceil_compl_range` -> `continuousAt_ceil`
- direct_use_of_changed_declaration [exact]: `continuousOn_floor_compl_range` -> `continuousAt_floor`
- direct_use_of_changed_declaration [exact]: `continuousOn_fract` -> `continuousOn_floor`
- direct_use_of_changed_declaration [exact]: `continuousOn_round` -> `continuousAt_round`
- direct_use_of_changed_declaration [exact]: `round_eq` -> `round_eq'`
- direct_use_of_changed_declaration [exact]: `round_eq'` -> `Int.ceil_intCast_add`
- direct_use_of_changed_declaration [exact]: `round_eq_half_ceil_two_mul` -> `Int.two_mul_fract_eq_one_iff_exists_int`
- direct_use_of_changed_declaration [exact]: `round_eq_half_ceil_two_mul` -> `round_eq'`
- direct_use_of_changed_declaration [exact]: `round_eq_iff` -> `round_eq`
- direct_use_of_changed_declaration [exact]: `round_eq_zero_iff` -> `round_eq_iff`
- direct_use_of_changed_declaration [exact]: `round_neg_two_inv` -> `round_eq_iff`
- direct_use_of_changed_declaration [exact]: `round_two_inv` -> `round_eq_iff`
- direct_use_of_changed_declaration [exact]: `tendsto_round_nhdsGE_pure` -> `round_eq'`
- direct_use_of_changed_declaration [exact]: `tendsto_round_nhdsLT_pure_half_ceil` -> `round_eq'`
- name_family [high]: `tendsto_round_nhdsGE_pure` -> `tendsto_round_nhdsLT_pure_half_ceil`
- name_family [high]: `tendsto_round_nhdsLT_pure_half_ceil` -> `tendsto_round_nhdsGE_pure`
