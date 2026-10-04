# The PR model for #34091 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(SetTheory/Cardinal): generalize infinite pigeonhole principle
- description: (not recoverable at review start)
- changed files: Mathlib/LinearAlgebra/Basis/Cardinality.lean, Mathlib/LinearAlgebra/Dimension/StrongRankCondition.lean, Mathlib/SetTheory/Cardinal/Pigeonhole.lean

## Objects

### `infinite_basis_le_maximal_linearIndependent'` (theorem, modified) [8db5a596ac]
- file: `Mathlib/LinearAlgebra/Basis/Cardinality.lean`; changed: proof:modified
- before the PR:
```lean
theorem infinite_basis_le_maximal_linearIndependent' {ι : Type w} (b : Basis ι R M) [Infinite ι]
    {κ : Type w'} (v : κ → M) (i : LinearIndependent R v) (m : i.Maximal) :
    Cardinal.lift.{w'} #ι ≤ Cardinal.lift.{w} #κ := by
  let Φ := fun k : κ => (b.repr (v k)).support
  have w₁ : #ι ≤ #(Set.range Φ) := by
    apply Cardinal.le_range_of_union_finset_eq_top
    exact union_support_maximal_linearIndependent_eq_range_basis b v i m
  have w₂ : Cardinal.lift.{w'} #(Set.range Φ) ≤ Cardinal.lift.{w} #κ := Cardinal.mk_range_le_lift
  exact (Cardinal.lift_le.mpr w₁).trans w₂

-- (See `infinite_basis_le_maximal_linearIndependent'` for the more general version
-- where the index types can live in different universes.)
```
- as the PR leaves it:
```lean
theorem infinite_basis_le_maximal_linearIndependent' {ι : Type w} (b : Basis ι R M) [Infinite ι]
    {κ : Type w'} (v : κ → M) (i : LinearIndependent R v) (m : i.Maximal) :
    Cardinal.lift.{w'} #ι ≤ Cardinal.lift.{w} #κ := by
  let Φ := fun k : κ => (b.repr (v k)).support
  have w₁ : #ι ≤ #(Set.range Φ) := by
    apply Cardinal.le_range_of_union_finset_eq_univ
    exact union_support_maximal_linearIndependent_eq_range_basis b v i m
  have w₂ : Cardinal.lift.{w'} #(Set.range Φ) ≤ Cardinal.lift.{w} #κ := Cardinal.mk_range_le_lift
  exact (Cardinal.lift_le.mpr w₁).trans w₂

-- (See `infinite_basis_le_maximal_linearIndependent'` for the more general version
-- where the index types can live in different universes.)
```

### `linearIndependent_le_infinite_basis` (theorem, modified) [805d000f30]
- file: `Mathlib/LinearAlgebra/Dimension/StrongRankCondition.lean`; changed: proof:modified
- before the PR:
```lean
theorem linearIndependent_le_infinite_basis {ι : Type w} (b : Basis ι R M) [Infinite ι] {κ : Type w}
    (v : κ → M) (i : LinearIndependent R v) : #κ ≤ #ι := by
  classical
  by_contra h
  rw [not_le, ← Cardinal.mk_finset_of_infinite ι] at h
  let Φ := fun k : κ => (b.repr (v k)).support
  obtain ⟨s, w : Infinite ↑(Φ ⁻¹' {s})⟩ := Cardinal.exists_infinite_fiber Φ h (by infer_instance)
  let v' := fun k : Φ ⁻¹' {s} => v k
  have i' : LinearIndependent R v' := i.comp _ Subtype.val_injective
  have w' : Finite (Φ ⁻¹' {s}) := by
    apply i'.finite_of_le_span_finite v' (s.image b)
    rintro m ⟨⟨p, ⟨rfl⟩⟩, rfl⟩
    simp only [SetLike.mem_coe, Finset.coe_image]
    apply Basis.mem_span_repr_support
  exact w.false
```
- as the PR leaves it:
```lean
theorem linearIndependent_le_infinite_basis {ι : Type w} (b : Basis ι R M) [Infinite ι] {κ : Type w}
    (v : κ → M) (i : LinearIndependent R v) : #κ ≤ #ι := by
  classical
  by_contra h
  rw [not_le, ← Cardinal.mk_finset_of_infinite ι] at h
  let Φ := fun k : κ => (b.repr (v k)).support
  obtain ⟨s, w : Infinite ↑(Φ ⁻¹' {s})⟩ := Cardinal.exists_infinite_fiber' Φ h (by infer_instance)
  let v' := fun k : Φ ⁻¹' {s} => v k
  have i' : LinearIndependent R v' := i.comp _ Subtype.val_injective
  have w' : Finite (Φ ⁻¹' {s}) := by
    apply i'.finite_of_le_span_finite v' (s.image b)
    rintro m ⟨⟨p, ⟨rfl⟩⟩, rfl⟩
    simp only [SetLike.mem_coe, Finset.coe_image]
    apply Basis.mem_span_repr_support
  exact w.false
```

### `Cardinal.exists_infinite_fiber'` (theorem, added) [3c4ee1646a]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem exists_infinite_fiber' {β α : Type u} (f : β → α) (h : #α < #β) (hα : Infinite α) :
    ∃ a : α, Infinite (f ⁻¹' {a}) :=
  exists_infinite_fiber f h (by
    rw [Cardinal.infinite_iff] at hα ⊢
    exact hα.trans h.le)
```

### `Cardinal.le_range_of_union_finset_eq_univ` (theorem, modified) [556eb5c2fd]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: name:modified, proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem le_range_of_union_finset_eq_top {α β : Type*} [Infinite β] (f : α → Finset β)
    (w : ⋃ a, (f a : Set β) = ⊤) : #β ≤ #(range f) := by
  have k : _root_.Infinite (range f) := by
    rw [infinite_coe_iff]
    apply mt (union_finset_finite_of_range_finite f)
    rw [w]
    exact infinite_univ
  by_contra h
  simp only [not_le] at h
  let u : ∀ b, ∃ a, b ∈ f a := fun b => by simpa using (w.ge :) (Set.mem_univ b)
  let u' : β → range f := fun b => ⟨f (u b).choose, by simp⟩
  have v' : ∀ a, u' ⁻¹' {⟨f a, by simp⟩} ≤ f a := by
    rintro a p m
    have m : f (u p).choose = f a := by simpa [u'] using m
    rw [← m]
    apply fun b => (u b).choose_spec
  obtain ⟨⟨-, ⟨a, rfl⟩⟩, p⟩ := exists_infinite_fiber u' h k
  exact (@Infinite.of_injective _ _ p (inclusion (v' a)) (inclusion_injective _)).false
```
- as the PR leaves it:
```lean
theorem le_range_of_union_finset_eq_univ {α β : Type*} [Infinite β] (f : α → Finset β)
    (w : ⋃ a, (f a : Set β) = Set.univ) : #β ≤ #(range f) := by
  by_contra h
  simp only [not_le] at h
  let u : ∀ b, ∃ a, b ∈ f a := fun b => by simpa using (w.ge :) (Set.mem_univ b)
  let u' : β → range f := fun b => ⟨f (u b).choose, by simp⟩
  have v' : ∀ a, u' ⁻¹' {⟨f a, by simp⟩} ≤ f a := by
    rintro a p m
    have m : f (u p).choose = f a := by simpa [u'] using m
    rw [← m]
    apply fun b => (u b).choose_spec
  obtain ⟨⟨-, ⟨a, rfl⟩⟩, p⟩ := exists_infinite_fiber u' h (by infer_instance)
  exact (@Infinite.of_injective _ _ p (inclusion (v' a)) (inclusion_injective _)).false
```

### `doc_comment in Pigeonhole.lean` (command, modified) [55f6b41ef3]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: documentation:modified
- before the PR:
```lean
/-- A function whose codomain's cardinality is infinite but strictly smaller than its domain's
has a fiber with cardinality strictly great than the codomain. -/
```
- as the PR leaves it:
```lean
/-- A function whose domain's cardinality is infinite but strictly greater than its domain's
has a fiber with cardinality strictly great than the codomain. -/
```

### `Cardinal.le_range_of_union_finset_eq_top` (theorem, removed) [5c602ca003]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem le_range_of_union_finset_eq_top {α β : Type*} [Infinite β] (f : α → Finset β)
    (w : ⋃ a, (f a : Set β) = ⊤) : #β ≤ #(range f) := by
  have k : _root_.Infinite (range f) := by
    rw [infinite_coe_iff]
    apply mt (union_finset_finite_of_range_finite f)
    rw [w]
    exact infinite_univ
  by_contra h
  simp only [not_le] at h
  let u : ∀ b, ∃ a, b ∈ f a := fun b => by simpa using (w.ge :) (Set.mem_univ b)
  let u' : β → range f := fun b => ⟨f (u b).choose, by simp⟩
  have v' : ∀ a, u' ⁻¹' {⟨f a, by simp⟩} ≤ f a := by
    rintro a p m
    have m : f (u p).choose = f a := by simpa [u'] using m
    rw [← m]
    apply fun b => (u b).choose_spec
  obtain ⟨⟨-, ⟨a, rfl⟩⟩, p⟩ := exists_infinite_fiber u' h k
  exact (@Infinite.of_injective _ _ p (inclusion (v' a)) (inclusion_injective _)).false
```

### `doc_comment in Pigeonhole.lean` (command, removed) [6acbc8fa4b]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: documentation:modified
- before the PR:
```lean
/-- If an infinite type `β` can be expressed as a union of finite sets,
then the cardinality of the collection of those finite sets
must be at least the cardinality of `β`. -/
-- TODO: write `Set.univ` instead of `⊤` and rename the theorem accordingly.
```

### `Cardinal.infinite_pigeonhole_card_lt` (theorem, modified) [73e3cf4ffc]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem infinite_pigeonhole_card_lt {β α : Type u} (f : β → α) (w : #α < #β) (w' : ℵ₀ ≤ #α) :
    ∃ a : α, #α < #(f ⁻¹' {a}) := by
  simp_rw [← succ_le_iff]
  exact infinite_pigeonhole_card f (succ #α) (succ_le_of_lt w) (w'.trans (lt_succ _).le)
    ((lt_succ _).trans_le (isRegular_succ w').2.ge)
```
- as the PR leaves it:
```lean
theorem infinite_pigeonhole_card_lt {β α : Type u} (f : β → α) (h : #α < #β) (hβ : ℵ₀ ≤ #β) :
    ∃ a : α, #α < #(f ⁻¹' {a}) := by
  simp_rw [← succ_le_iff]
  rcases lt_or_ge #α ℵ₀ with hα | hα
  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])
    exact ⟨a, ha.trans' (succ_le_of_lt hα)⟩
  · exact infinite_pigeonhole_card f (succ #α) (succ_le_of_lt h) (hα.trans (le_succ _))
      ((lt_succ _).trans_le (isRegular_succ hα).2.ge)
```

### `Cardinal.exists_uncountable_fiber` (theorem, added) [7a10cadc9d]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem exists_uncountable_fiber {β α : Type u} (f : β → α) (h : #α < #β) (hβ : Uncountable β) :
    ∃ a : α, Uncountable (f ⁻¹' {a}) := by
  simp_rw [← Cardinal.aleph0_lt_mk_iff, ← Order.succ_le_iff, succ_aleph0] at hβ ⊢
  rcases lt_or_ge #α ℵ₀ with hα | hα
  · exact infinite_pigeonhole_card f ℵ₁ hβ aleph0_lt_aleph_one.le
      (by rw [isRegular_aleph_one.cof_eq]; exact hα.trans aleph0_lt_aleph_one)
  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h (hβ.trans' aleph0_lt_aleph_one.le)
    rw [← Order.succ_le_succ_iff, succ_aleph0] at hα
    exact ⟨a, hα.trans (succ_le_of_lt ha)⟩
```

### `Cardinal.exists_infinite_fiber` (theorem, modified) [88da165141]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: proof:modified, statement_or_type:modified
- before the PR:
```lean
theorem exists_infinite_fiber {β α : Type u} (f : β → α) (w : #α < #β) (w' : Infinite α) :
    ∃ a : α, Infinite (f ⁻¹' {a}) := by
  simp_rw [Cardinal.infinite_iff] at w' ⊢
  obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f w w'
  exact ⟨a, w'.trans ha.le⟩
```
- as the PR leaves it:
```lean
theorem exists_infinite_fiber {β α : Type u} (f : β → α) (h : #α < #β) (hβ : Infinite β) :
    ∃ a : α, Infinite (f ⁻¹' {a}) := by
  simp_rw [Cardinal.infinite_iff] at hβ ⊢
  rcases lt_or_ge #α ℵ₀ with hα | hα
  · exact infinite_pigeonhole_card f ℵ₀ hβ le_rfl (by rwa [isRegular_aleph0.cof_eq])
  · obtain ⟨a, ha⟩ := infinite_pigeonhole_card_lt f h hβ
    exact ⟨a, hα.trans ha.le⟩
```

### `doc_comment in Pigeonhole.lean` (command, added) [8dfd303c62]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: documentation:modified
- as the PR leaves it:
```lean
/-- A function whose domain's cardinality is uncountable but strictly greater than its domain's
has an uncountable fiber. -/
```

### `doc_comment in Pigeonhole.lean` (command, added) [a1bc7e09aa]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: documentation:modified
- as the PR leaves it:
```lean
/-- A weaker version of `exists_infinite_fiber` that requires codomain to be infinite. -/
```

### `attribute in Pigeonhole.lean` (command, added) [a51cee6900]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: unknown:added
- as the PR leaves it:
```lean
@[deprecated (since := "2026-01-17")] alias le_range_of_union_finset_eq_top :=
  le_range_of_union_finset_eq_univ
```

### `doc_comment in Pigeonhole.lean` (command, modified) [c550d24482]
- file: `Mathlib/SetTheory/Cardinal/Pigeonhole.lean`; changed: documentation:modified
- before the PR:
```lean
/-- A function whose codomain's cardinality is infinite but strictly smaller than its domain's
has an infinite fiber. -/
```
- as the PR leaves it:
```lean
/-- A function whose domain's cardinality is infinite but strictly greater than its domain's
has an infinite fiber. -/
```

## Removed or renamed

- `Cardinal.le_range_of_union_finset_eq_top`
- `doc_comment in Pigeonhole.lean`

## Families (declarations that may be one decision)

- [exact] `infinite_basis_le_maximal_linearIndependent'`, `linearIndependent_le_infinite_basis` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Cardinal.exists_infinite_fiber`, `Cardinal.exists_infinite_fiber'`, `Cardinal.infinite_pigeonhole_card_lt` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Cardinal.exists_infinite_fiber`, `Cardinal.exists_infinite_fiber'`, `Cardinal.exists_uncountable_fiber` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Cardinal.le_range_of_union_finset_eq_top`, `Cardinal.le_range_of_union_finset_eq_univ` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `Cardinal.exists_infinite_fiber` -> `Cardinal.infinite_pigeonhole_card_lt`
- direct_use_of_changed_declaration [exact]: `Cardinal.exists_infinite_fiber'` -> `Cardinal.exists_infinite_fiber`
- direct_use_of_changed_declaration [exact]: `Cardinal.exists_uncountable_fiber` -> `Cardinal.infinite_pigeonhole_card_lt`
- direct_use_of_changed_declaration [exact]: `Cardinal.le_range_of_union_finset_eq_top` -> `Cardinal.exists_infinite_fiber`
- direct_use_of_changed_declaration [exact]: `Cardinal.le_range_of_union_finset_eq_univ` -> `Cardinal.exists_infinite_fiber`
- direct_use_of_changed_declaration [exact]: `infinite_basis_le_maximal_linearIndependent'` -> `Cardinal.le_range_of_union_finset_eq_univ`
- direct_use_of_changed_declaration [exact]: `linearIndependent_le_infinite_basis` -> `Cardinal.exists_infinite_fiber'`
- name_family [high]: `Cardinal.exists_infinite_fiber` -> `Cardinal.infinite_pigeonhole_card_lt`
- name_family [high]: `Cardinal.exists_infinite_fiber` -> `Cardinal.exists_infinite_fiber'`
- name_family [high]: `Cardinal.exists_infinite_fiber'` -> `Cardinal.infinite_pigeonhole_card_lt`
- name_family [high]: `Cardinal.exists_infinite_fiber'` -> `Cardinal.exists_infinite_fiber`
- name_family [high]: `Cardinal.infinite_pigeonhole_card_lt` -> `Cardinal.exists_infinite_fiber`
- name_family [high]: `Cardinal.infinite_pigeonhole_card_lt` -> `Cardinal.exists_infinite_fiber'`
- name_family [high]: `infinite_basis_le_maximal_linearIndependent'` -> `linearIndependent_le_infinite_basis`
- name_family [high]: `linearIndependent_le_infinite_basis` -> `infinite_basis_le_maximal_linearIndependent'`
