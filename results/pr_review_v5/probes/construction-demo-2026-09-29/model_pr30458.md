# The PR model for #30458 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(Algebra): misc. generalizations
- description: All found by asking Codex to search for low-hanging generalization opportunities.

I have no intended use for these generalizations; they are proposed for their own sake.

I don't have the required maturity as a Lean developer to judge whether these generalizations are valuable or not, or whether they could be done in a better/cleaner way. Particularly, it is hard for me to judge whether the generalized results should be moved elsewhere, or whether assumptions could be expressed more concisely. Hopefully I can get some feedback on this during review.
- changed files: Mathlib/Algebra/Group/Basic.lean, Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean, Mathlib/Algebra/Group/Pointwise/Set/Finite.lean

## Objects

### `div_eq_inv_self` (theorem, added) [0b0e7e9bec]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem div_eq_inv_self : a / b = b⁻¹ ↔ a = 1 := by
  rw [div_eq_mul_inv, mul_eq_right]
```

### `div_left_inj` (theorem, added) [1bb735450b]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem div_left_inj : b / a = c / a ↔ b = c := by
  constructor
  · intro h
    have h' : b * a⁻¹ = c * a⁻¹ := by simpa [div_eq_mul_inv] using h
    simpa using (mul_right_cancel (a := b) (b := a⁻¹) (c := c) h')
  · rintro rfl; rfl
```

### `section in Basic.lean` (command, added) [1c26532923]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
section Group
```

### `section in Basic.lean` (command, modified) [2c07e71279]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
variable [Group G] {a b c d : G} {n : ℤ}
```
- as the PR leaves it:
```lean
section LeftCancelDivisionMonoid
```

### `div_left_injective` (theorem, added) [2dbdcc1c3b]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
theorem div_left_injective : Function.Injective fun a : G ↦ a / b := by
  intro a₁ a₂ h
  have h' : a₁ * b⁻¹ = a₂ * b⁻¹ := by simpa [div_eq_mul_inv] using h
  simpa using (mul_right_cancel (a := a₁) (b := b⁻¹) (c := a₂) h')
```

### `div_eq_inv_self` (theorem, removed) [4188e62d32]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive (attr := simp)]
theorem div_eq_inv_self : a / b = b⁻¹ ↔ a = 1 := by rw [div_eq_mul_inv, mul_eq_right]
```

### `section in Basic.lean` (command, modified) [4b5866dbae]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
section Group
```
- as the PR leaves it:
```lean
section RightCancelDivInvMonoid
```

### `section in Basic.lean` (command, modified) [732f3287cd]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
variable [Group G] {a b c d : G} {n : ℤ}
```
- as the PR leaves it:
```lean
end RightCancelDivInvMonoid
```

### `div_right_inj` (theorem, removed) [7a1225fcbd]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive (attr := simp)]
theorem div_right_inj : a / b = a / c ↔ b = c :=
  div_right_injective.eq_iff
```

### `section in Basic.lean` (command, added) [91d75aea23]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
end LeftCancelDivisionMonoid
```

### `div_eq_self` (theorem, added) [927b73e2d8]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem div_eq_self : a / b = a ↔ b = 1 := by
  rw [div_eq_mul_inv, mul_eq_left, inv_eq_one]
```

### `section in Basic.lean` (command, modified) [96fd38e8b5]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
variable [Group G] {a b c d : G} {n : ℤ}
```
- as the PR leaves it:
```lean
variable [DivInvMonoid G] [IsRightCancelMul G] {a b c : G}
```

### `div_left_injective` (theorem, removed) [a6cde422e8]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, documentation:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive]
theorem div_left_injective : Function.Injective fun a ↦ a / b := by
  -- FIXME this could be by `simpa`, but it fails. This is probably a bug in `simpa`.
  simp only [div_eq_mul_inv]
  exact fun a a' h ↦ mul_left_injective b⁻¹ h
```

### `div_eq_self` (theorem, removed) [b3f5e90865]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive (attr := simp)]
theorem div_eq_self : a / b = a ↔ b = 1 := by rw [div_eq_mul_inv, mul_eq_left, inv_eq_one]
```

### `div_right_inj` (theorem, added) [c9b4145971]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := simp)]
theorem div_right_inj : a / b = a / c ↔ b = c :=
  (div_right_injective (G := G) (b := a)).eq_iff
```

### `div_left_inj` (theorem, removed) [d1f34648a6]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive (attr := simp)]
theorem div_left_inj : b / a = c / a ↔ b = c := by
  rw [div_eq_mul_inv, div_eq_mul_inv]
  exact mul_left_inj _
```

### `section in Basic.lean` (command, added) [e00e1d0ea2]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
variable [Group G] {a b c d : G} {n : ℤ}
```

### `div_right_injective` (theorem, removed) [e23b757a9e]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:removed, documentation:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive]
theorem div_right_injective : Function.Injective fun a ↦ b / a := by
  -- FIXME see above
  simp only [div_eq_mul_inv]
  exact fun a a' h ↦ inv_injective (mul_right_injective b h)
```

### `section in Basic.lean` (command, modified) [e8c3bc59ce]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
variable [Group G] {a b c d : G} {n : ℤ}
```
- as the PR leaves it:
```lean
variable [DivisionMonoid G] [IsLeftCancelMul G] {a b c : G}
```

### `div_right_injective` (theorem, added) [fd255c286c]
- file: `Mathlib/Algebra/Group/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
theorem div_right_injective : Function.Injective fun x : G ↦ b / x := by
  simp only [div_eq_mul_inv]
  exact fun a a' h ↦ inv_injective (mul_right_injective b h)
```

### `section in Basic.lean` (command, modified) [326453eafb]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
end Group
```
- as the PR leaves it:
```lean
end DivisionMonoid
```

### `section in Basic.lean` (command, modified) [8a10f82185]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
section Group


variable [Group α] [DecidableEq α] {s t : Finset α}
```
- as the PR leaves it:
```lean
variable [DivisionMonoid α] [IsLeftCancelMul α] [DecidableEq α] {s t : Finset α}
```

### `section in Basic.lean` (command, added) [8caf5d2959]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
section RightCancel
```

### `section in Basic.lean` (command, modified) [986cb2fd3f]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
section Group


variable [Group α] [DecidableEq α] {s t : Finset α}
```
- as the PR leaves it:
```lean
section LeftCancel
```

### `Finset.card_le_card_div_right` (lemma, modified) [9ed5c79d20]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: proof:modified
- before the PR:
```lean
@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) :=
  have ⟨_, ha⟩ := ht; card_le_card_image₂_right _ ha div_left_injective
```
- as the PR leaves it:
```lean
@[to_additive] lemma card_le_card_div_right (ht : t.Nonempty) : #s ≤ #(s / t) := by
  obtain ⟨b, hb⟩ := ht
  exact card_le_card_image₂_right _ hb (div_left_injective (b := b))
```

### `Finset.card_le_card_div_left` (lemma, added) [a9d97dd999]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) := by
  obtain ⟨a, ha⟩ := hs
  exact card_le_card_image₂_left _ ha (div_right_injective (b := a))
```

### `section in Basic.lean` (command, added) [b12433639f]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
variable [DivisionMonoid α] [IsRightCancelMul α] [DecidableEq α] {s t : Finset α}
```

### `section in Basic.lean` (command, added) [b401ecd423]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
variable [DivisionMonoid α] [IsLeftCancelMul α] [DecidableEq α]
    {s t : Finset α}
```

### `section in Basic.lean` (command, modified) [c095d8baa9]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
section Group


variable [Group α] [DecidableEq α] {s t : Finset α}
```
- as the PR leaves it:
```lean
section DivisionMonoid
```

### `section in Basic.lean` (command, added) [ed112d934a]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- as the PR leaves it:
```lean
end RightCancel
```

### `section in Basic.lean` (command, modified) [ffc5560ec6]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: namespace:modified
- before the PR:
```lean
section Group


variable [Group α] [DecidableEq α] {s t : Finset α}
```
- as the PR leaves it:
```lean
end LeftCancel
```

### `Finset.card_le_card_div_left` (lemma, removed) [ffd9abb5e5]
- file: `Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive] lemma card_le_card_div_left (hs : s.Nonempty) : #t ≤ #(s / t) :=
  have ⟨_, ha⟩ := hs; card_le_card_image₂_left _ ha div_right_injective
```

### `section in Finite.lean` (command, modified) [0eac44c2b4]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Finite.lean`; changed: namespace:modified
- before the PR:
```lean
variable [Group α] {s t : Set α}
```
- as the PR leaves it:
```lean
variable [DivisionMonoid α] [IsLeftCancelMul α] [IsRightCancelMul α] {s t : Set α}
```

### `Set.finite_div` (lemma, modified) [4afb81fb26]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Finite.lean`; changed: proof:modified
- before the PR:
```lean
@[to_additive]
lemma finite_div : (s / t).Finite ↔ s.Finite ∧ t.Finite ∨ s = ∅ ∨ t = ∅ :=
  finite_image2 (fun _ _ ↦ div_left_injective.injOn) fun _ _ ↦ div_right_injective.injOn
```
- as the PR leaves it:
```lean
@[to_additive]
lemma finite_div : (s / t).Finite ↔ s.Finite ∧ t.Finite ∨ s = ∅ ∨ t = ∅ :=
  finite_image2 (fun b _ ↦ (div_left_injective (b := b)).injOn)
    fun a _ ↦ (div_right_injective (b := a)).injOn
```

### `section in Finite.lean` (command, modified) [531e617dfd]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Finite.lean`; changed: namespace:modified
- before the PR:
```lean
section Group
```
- as the PR leaves it:
```lean
section DivisionMonoid
```

### `section in Finite.lean` (command, modified) [b0bc3fa631]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Finite.lean`; changed: namespace:modified
- before the PR:
```lean
end Group
```
- as the PR leaves it:
```lean
end DivisionMonoid
```

### `Set.infinite_div` (lemma, modified) [cdef024677]
- file: `Mathlib/Algebra/Group/Pointwise/Set/Finite.lean`; changed: proof:modified
- before the PR:
```lean
@[to_additive]
lemma infinite_div : (s / t).Infinite ↔ s.Infinite ∧ t.Nonempty ∨ t.Infinite ∧ s.Nonempty :=
  infinite_image2 (fun _ _ ↦ div_left_injective.injOn) fun _ _ ↦ div_right_injective.injOn
```
- as the PR leaves it:
```lean
@[to_additive]
lemma infinite_div : (s / t).Infinite ↔ s.Infinite ∧ t.Nonempty ∨ t.Infinite ∧ s.Nonempty :=
  infinite_image2 (fun b _ ↦ (div_left_injective (b := b)).injOn)
    fun a _ ↦ (div_right_injective (b := a)).injOn
```

## Removed or renamed

- `div_eq_inv_self`
- `div_right_inj`
- `div_left_injective`
- `div_eq_self`
- `div_left_inj`
- `div_right_injective`
- `Finset.card_le_card_div_left`

## Families (declarations that may be one decision)

- [exact] `Set.finite_div`, `Set.infinite_div` -- 2 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `div_eq_inv_self`, `div_eq_self`, `div_left_inj`, `div_left_injective`, `div_right_inj`, `div_right_injective` -- 8 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Finset.card_le_card_div_left`, `Finset.card_le_card_div_right` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `Set.finite_div` -> `Set.infinite_div`
- changed_siblings [high]: `Set.infinite_div` -> `Set.finite_div`
- changed_siblings [high]: `div_eq_inv_self` -> `div_left_injective`
- changed_siblings [high]: `div_eq_self` -> `div_right_injective`
- changed_siblings [high]: `div_left_inj` -> `div_left_injective`
- changed_siblings [high]: `div_left_injective` -> `div_eq_inv_self`
- changed_siblings [high]: `div_left_injective` -> `div_left_inj`
- changed_siblings [high]: `div_right_inj` -> `div_right_injective`
- changed_siblings [high]: `div_right_injective` -> `div_eq_self`
- changed_siblings [high]: `div_right_injective` -> `div_right_inj`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_left` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_left` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_left` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_left` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_right` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `Finset.card_le_card_div_right` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `Set.finite_div` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Set.finite_div` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Set.finite_div` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `Set.finite_div` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `Set.infinite_div` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Set.infinite_div` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `Set.infinite_div` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `Set.infinite_div` -> `div_left_injective`
- direct_use_of_changed_declaration [exact]: `div_right_inj` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `div_right_inj` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `div_right_inj` -> `div_right_injective`
- direct_use_of_changed_declaration [exact]: `div_right_inj` -> `div_right_injective`
- name_family [high]: `div_left_injective` -> `div_left_injective`
- name_family [high]: `div_left_injective` -> `div_right_injective`
- name_family [high]: `div_left_injective` -> `div_left_injective`
- name_family [high]: `div_left_injective` -> `div_right_injective`
- name_family [high]: `div_left_injective` -> `div_right_injective`
- name_family [high]: `div_left_injective` -> `div_right_injective`
- name_family [high]: `div_right_injective` -> `div_left_injective`
- name_family [high]: `div_right_injective` -> `div_right_injective`
- name_family [high]: `div_right_injective` -> `div_left_injective`
- name_family [high]: `div_right_injective` -> `div_left_injective`
- name_family [high]: `div_right_injective` -> `div_right_injective`
- name_family [high]: `div_right_injective` -> `div_left_injective`
