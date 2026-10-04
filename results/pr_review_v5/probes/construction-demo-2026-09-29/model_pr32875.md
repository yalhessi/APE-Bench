# The PR model for #32875 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore: golf using `grind` and `simp`
- description: Trace profiling results (shown if ≥10 ms before or after):
* `Finset.mem_map_equiv`: <10 ms before, 25 ms after
* `Rat.inv_intCast_den_of_pos`: <10 ms before, 17 ms after
* `MeasureTheory.Measure.pi_map_piCongrLeft`: 55 ms before, 48 ms after  🎉
* `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'`: 268 ms before, <10 ms after  🎉
* `limsup_finset_sup'`: 64 ms before, 51 ms after  🎉
* `ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod`: 69 ms before, 17 ms after  🎉
* `Metric.exists_lt_mem_ball_of_mem_ball`: 81 ms before, <10 ms after  🎉

This golfing PR is batched under the following guidelines:
* Up to ~5 changed files per PR
* Up to ~25 changed declarations per PR
* Up to ~100 changed lines per PR
- changed files: Mathlib/Data/Finset/Image.lean, Mathlib/Data/Rat/Lemmas.lean, Mathlib/MeasureTheory/Constructions/Pi.lean, Mathlib/MeasureTheory/Measure/Portmanteau.lean, Mathlib/Order/LiminfLimsup.lean, Mathlib/Probability/Kernel/Disintegration/Integral.lean, Mathlib/Topology/MetricSpace/Pseudo/Defs.lean

## Objects

### `Finset.mem_map_equiv` (theorem, modified) [390616b4c3]
- file: `Mathlib/Data/Finset/Image.lean`; changed: proof:modified
- before the PR:
```lean
@[simp 1100]
theorem mem_map_equiv {f : α ≃ β} {b : β} : b ∈ s.map f.toEmbedding ↔ f.symm b ∈ s := by
  rw [mem_map]
  exact
    ⟨by
      rintro ⟨a, H, rfl⟩
      simpa, fun h => ⟨_, h, by simp⟩⟩
```
- as the PR leaves it:
```lean
@[simp 1100]
theorem mem_map_equiv {f : α ≃ β} {b : β} : b ∈ s.map f.toEmbedding ↔ f.symm b ∈ s := by
  simp only [mem_map, Equiv.coe_toEmbedding]
  grind
```

### `Rat.inv_intCast_den_of_pos` (theorem, modified) [3aca4557c6]
- file: `Mathlib/Data/Rat/Lemmas.lean`; changed: proof:modified
- before the PR:
```lean
theorem inv_intCast_den_of_pos {a : ℤ} (ha0 : 0 < a) : ((a : ℚ)⁻¹.den : ℤ) = a := by
  rw [← ofInt_eq_cast, ofInt, mk_eq_divInt, Rat.inv_divInt, divInt_eq_div, Nat.cast_one]
  apply den_div_eq_of_coprime ha0
  rw [Int.natAbs_one]
  exact Nat.coprime_one_left _
```
- as the PR leaves it:
```lean
theorem inv_intCast_den_of_pos {a : ℤ} (ha0 : 0 < a) : ((a : ℚ)⁻¹.den : ℤ) = a := by
  simp only [den_inv, num_intCast]
  grind
```

### `MeasureTheory.Measure.pi_map_piCongrLeft` (lemma, modified) [d11aac133e]
- file: `Mathlib/MeasureTheory/Constructions/Pi.lean`; changed: proof:modified
- before the PR:
```lean
lemma pi_map_piCongrLeft [hι' : Fintype ι'] (e : ι ≃ ι') {β : ι' → Type*}
    [∀ i, MeasurableSpace (β i)] (μ : (i : ι') → Measure (β i)) [∀ i, SigmaFinite (μ i)] :
    (Measure.pi fun i ↦ μ (e i)).map (MeasurableEquiv.piCongrLeft (fun i ↦ β i) e)
      = Measure.pi μ := by
  let e_meas : ((b : ι) → β (e b)) ≃ᵐ ((a : ι') → β a) :=
    MeasurableEquiv.piCongrLeft (fun i ↦ β i) e
  refine Measure.pi_eq (fun s _ ↦ ?_) |>.symm
  rw [e_meas.measurableEmbedding.map_apply]
  let s' : (i : ι) → Set (β (e i)) := fun i ↦ s (e i)
  have : e_meas ⁻¹' pi univ s = pi univ s' := by
    ext x
    simp only [mem_preimage, Set.mem_pi, mem_univ, forall_true_left, s']
    refine (e.forall_congr ?_).symm
    intro i
    rw [MeasurableEquiv.piCongrLeft_apply_apply e x i]
  rw [this, pi_pi, Finset.prod_equiv e.symm]
  · simp only [Finset.mem_univ, implies_true]
  intro i _
  simp only [s']
  congr
  all_goals rw [e.apply_symm_apply]
```
- as the PR leaves it:
```lean
lemma pi_map_piCongrLeft [hι' : Fintype ι'] (e : ι ≃ ι') {β : ι' → Type*}
    [∀ i, MeasurableSpace (β i)] (μ : (i : ι') → Measure (β i)) [∀ i, SigmaFinite (μ i)] :
    (Measure.pi fun i ↦ μ (e i)).map (MeasurableEquiv.piCongrLeft (fun i ↦ β i) e)
      = Measure.pi μ := by
  let e_meas : ((b : ι) → β (e b)) ≃ᵐ ((a : ι') → β a) :=
    MeasurableEquiv.piCongrLeft (fun i ↦ β i) e
  refine Measure.pi_eq (fun s _ ↦ ?_) |>.symm
  rw [e_meas.measurableEmbedding.map_apply]
  let s' : (i : ι) → Set (β (e i)) := fun i ↦ s (e i)
  have : e_meas ⁻¹' pi univ s = pi univ s' := by
    ext x
    simp only [mem_preimage, Set.mem_pi, mem_univ, forall_true_left, s']
    refine (e.forall_congr ?_).symm
    intro i
    rw [MeasurableEquiv.piCongrLeft_apply_apply e x i]
  simp only [pi_pi, this]
  exact Fintype.prod_equiv _ _ _ (congrFun rfl)
```

### `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'` (lemma, modified) [be096002ef]
- file: `Mathlib/MeasureTheory/Measure/Portmanteau.lean`; changed: proof:modified
- before the PR:
```lean
lemma tendsto_of_forall_isClosed_limsup_real_le' {L : Filter ι} [L.IsCountablyGenerated]
    (h : ∀ F : Set Ω, IsClosed F →
      limsup (fun i ↦ (μs i : Measure Ω).real F) L ≤ (μ : Measure Ω).real F) :
    Tendsto μs L (𝓝 μ) := by
  refine tendsto_of_forall_isClosed_limsup_le' fun F hF ↦ ?_
  rcases L.eq_or_neBot with rfl | hne
  · simp
  specialize h F hF
  simp only [Measure.real_def] at h
  rwa [ENNReal.limsup_toReal_eq (b := 1) (by simp) (.of_forall fun i ↦ prob_le_one),
    ENNReal.toReal_le_toReal _ (by finiteness)] at h
  refine ne_top_of_le_ne_top (b := 1) (by simp) ?_
  refine limsup_le_of_le ?_ (.of_forall fun i ↦ prob_le_one)
  exact isCoboundedUnder_le_of_le L (x := 0) (by simp)
```
- as the PR leaves it:
```lean
lemma tendsto_of_forall_isClosed_limsup_real_le' {L : Filter ι} [L.IsCountablyGenerated]
    (h : ∀ F : Set Ω, IsClosed F →
      limsup (fun i ↦ (μs i : Measure Ω).real F) L ≤ (μ : Measure Ω).real F) :
    Tendsto μs L (𝓝 μ) := by
  simp only [ProbabilityMeasure.measureReal_eq_coe_coeFn, NNReal.toReal_limsup] at h
  exact tendsto_of_forall_isClosed_limsup_le h
```

### `limsup_finset_sup'` (theorem, modified) [888933b6f9]
- file: `Mathlib/Order/LiminfLimsup.lean`; changed: proof:modified
- before the PR:
```lean
theorem limsup_finset_sup' [ConditionallyCompleteLinearOrder β] {f : Filter α}
    {F : ι → α → β} {s : Finset ι} (hs : s.Nonempty)
    (h₁ : ∀ i ∈ s, f.IsCoboundedUnder (· ≤ ·) (F i) := by exact fun _ _ ↦ by isBoundedDefault)
    (h₂ : ∀ i ∈ s, f.IsBoundedUnder (· ≤ ·) (F i) := by exact fun _ _ ↦ by isBoundedDefault) :
    limsup (fun a ↦ sup' s hs (fun i ↦ F i a)) f = sup' s hs (fun i ↦ limsup (F i) f) := by
  have bddsup := isBoundedUnder_le_finset_sup' hs h₂
  apply le_antisymm
  · have h₃ : ∃ i ∈ s, f.IsCoboundedUnder (· ≤ ·) (F i) := by
      rcases hs with ⟨i, i_s⟩
      use i, i_s
      exact h₁ i i_s
    have cobddsup := isCoboundedUnder_le_finset_sup' hs h₃
    refine (limsup_le_iff cobddsup bddsup).2 (fun b hb ↦ ?_)
    rw [eventually_iff_exists_mem]
    use ⋂ i ∈ s, {a | F i a < b}
    split_ands
    · rw [biInter_finset_mem]
      suffices key : ∀ i ∈ s, ∀ᶠ a in f, F i a < b from fun i i_s ↦ eventually_iff.1 (key i i_s)
      intro i i_s
      apply eventually_lt_of_limsup_lt _ (h₂ i i_s)
      exact lt_of_le_of_lt (Finset.le_sup' (f := fun i ↦ limsup (F i) f) i_s) hb
    · simp only [mem_iInter, mem_setOf_eq, sup'_lt_iff, imp_self, implies_true]
  · apply Finset.sup'_le hs (fun i ↦ limsup (F i) f)
    refine fun i i_s ↦ limsup_le_limsup (Eventually.of_forall (fun a ↦ ?_)) (h₁ i i_s) bddsup
    simp only [le_sup'_iff]
    use i, i_s
```
- as the PR leaves it:
```lean
theorem limsup_finset_sup' [ConditionallyCompleteLinearOrder β] {f : Filter α}
    {F : ι → α → β} {s : Finset ι} (hs : s.Nonempty)
    (h₁ : ∀ i ∈ s, f.IsCoboundedUnder (· ≤ ·) (F i) := by exact fun _ _ ↦ by isBoundedDefault)
    (h₂ : ∀ i ∈ s, f.IsBoundedUnder (· ≤ ·) (F i) := by exact fun _ _ ↦ by isBoundedDefault) :
    limsup (fun a ↦ sup' s hs (fun i ↦ F i a)) f = sup' s hs (fun i ↦ limsup (F i) f) := by
  have bddsup := isBoundedUnder_le_finset_sup' hs h₂
  apply le_antisymm
  · have h₃ : ∃ i ∈ s, f.IsCoboundedUnder (· ≤ ·) (F i) := by
      rcases hs with ⟨i, i_s⟩
      use i, i_s
      exact h₁ i i_s
    have cobddsup := isCoboundedUnder_le_finset_sup' hs h₃
    refine (limsup_le_iff cobddsup bddsup).2 (fun b hb ↦ ?_)
    simp only [gt_iff_lt, sup'_lt_iff, eventually_all_finset] at hb ⊢
    exact fun i i_s ↦ eventually_lt_of_limsup_lt (hb i i_s) (h₂ i i_s)
  · apply Finset.sup'_le hs (fun i ↦ limsup (F i) f)
    refine fun i i_s ↦ limsup_le_limsup (Eventually.of_forall (fun a ↦ ?_)) (h₁ i i_s) bddsup
    simp only [le_sup'_iff]
    use i, i_s
```

### `MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod` (lemma, modified) [aa66f9a0ce]
- file: `Mathlib/Probability/Kernel/Disintegration/Integral.lean`; changed: proof:modified
- before the PR:
```lean
lemma setLIntegral_condKernel_eq_measure_prod {s : Set β} (hs : MeasurableSet s) {t : Set Ω}
    (ht : MeasurableSet t) :
    ∫⁻ b in s, ρ.condKernel b t ∂ρ.fst = ρ (s ×ˢ t) := by
  have : ρ (s ×ˢ t) = (ρ.fst ⊗ₘ ρ.condKernel) (s ×ˢ t) := by
    congr; exact (ρ.disintegrate _).symm
  rw [this, compProd_apply (hs.prod ht)]
  classical
  have : ∀ b, ρ.condKernel b (Prod.mk b ⁻¹' s ×ˢ t)
      = s.indicator (fun b ↦ ρ.condKernel b t) b := by
    intro b
    by_cases hb : b ∈ s <;> simp [hb]
  simp_rw [this]
  rw [lintegral_indicator hs]
```
- as the PR leaves it:
```lean
lemma setLIntegral_condKernel_eq_measure_prod {s : Set β} (hs : MeasurableSet s) {t : Set Ω}
    (ht : MeasurableSet t) :
    ∫⁻ b in s, ρ.condKernel b t ∂ρ.fst = ρ (s ×ˢ t) := by
  have : ρ (s ×ˢ t) = (ρ.fst ⊗ₘ ρ.condKernel) (s ×ˢ t) := by
    congr; exact (ρ.disintegrate _).symm
  simp only [this]
  exact (compProd_apply_prod hs ht).symm
```

### `ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod` (lemma, modified) [b80f10ea93]
- file: `Mathlib/Probability/Kernel/Disintegration/Integral.lean`; changed: proof:modified
- before the PR:
```lean
lemma setLIntegral_condKernel_eq_measure_prod (a : α) {s : Set β} (hs : MeasurableSet s)
    {t : Set Ω} (ht : MeasurableSet t) :
    ∫⁻ b in s, Kernel.condKernel κ (a, b) t ∂(Kernel.fst κ a) = κ a (s ×ˢ t) := by
  have : κ a (s ×ˢ t) = (Kernel.fst κ ⊗ₖ Kernel.condKernel κ) a (s ×ˢ t) := by
    congr; exact (κ.disintegrate _).symm
  rw [this, Kernel.compProd_apply (hs.prod ht)]
  classical
  have : ∀ b, Kernel.condKernel κ (a, b) {c | (b, c) ∈ s ×ˢ t}
      = s.indicator (fun b ↦ Kernel.condKernel κ (a, b) t) b := by
    intro b
    by_cases hb : b ∈ s <;> simp [hb]
  simp_rw [Set.preimage, this]
  rw [lintegral_indicator hs]
```
- as the PR leaves it:
```lean
lemma setLIntegral_condKernel_eq_measure_prod (a : α) {s : Set β} (hs : MeasurableSet s)
    {t : Set Ω} (ht : MeasurableSet t) :
    ∫⁻ b in s, Kernel.condKernel κ (a, b) t ∂(Kernel.fst κ a) = κ a (s ×ˢ t) := by
  have : κ a (s ×ˢ t) = (Kernel.fst κ ⊗ₖ Kernel.condKernel κ) a (s ×ˢ t) := by
    congr; exact (κ.disintegrate _).symm
  simp only [this]
  exact (Kernel.compProd_apply_prod hs ht).symm
```

### `Metric.exists_lt_mem_ball_of_mem_ball` (theorem, modified) [9395c1f31a]
- file: `Mathlib/Topology/MetricSpace/Pseudo/Defs.lean`; changed: proof:modified
- before the PR:
```lean
theorem exists_lt_mem_ball_of_mem_ball (h : x ∈ ball y ε) : ∃ ε' < ε, x ∈ ball y ε' := by
  simp only [mem_ball] at h ⊢
  exact ⟨(dist x y + ε) / 2, by linarith, by linarith⟩
```
- as the PR leaves it:
```lean
theorem exists_lt_mem_ball_of_mem_ball (h : x ∈ ball y ε) : ∃ ε' < ε, x ∈ ball y ε' :=
  exists_between' h
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- none
