# The PR model for #33098 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat: minimal covers and maximal separated sets
- description: Define a minimal cover of a set by closed balls, and a maximal separated set.
Use the maximal separated set to prove comparisons between covering and packing numbers.
- changed files: Mathlib/Topology/MetricSpace/CoveringNumbers.lean

## Objects

### `Metric.maximalSeparatedSet` (def, added) [0adc9a11d9]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable
def maximalSeparatedSet (ε : ℝ≥0) (A : Set X) : Set X :=
  if h : packingNumber ε A ≠ ⊤ then (exists_set_encard_eq_packingNumber h).choose else ∅
```

### `section in CoveringNumbers.lean` (command, added) [193ff3d1c1]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end MinimalCover
```

### `Metric.exists_set_encard_eq_packingNumber` (lemma, added) [1fb113759e]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma exists_set_encard_eq_packingNumber (h : packingNumber ε A ≠ ⊤) :
    ∃ C, C ⊆ A ∧ C.Finite ∧ IsSeparated ε C ∧ C.encard = packingNumber ε A := by
  rcases Set.eq_empty_or_nonempty A with hA | hA
  · simp [hA, packingNumber]
  have : Nonempty { s : Set X // s ⊆ A ∧ IsSeparated ε s } := by
    obtain ⟨a, ha⟩ := hA
    exact ⟨⟨{a}, by simp [ha], by simp⟩⟩
  let h_exists := ENat.exists_eq_iSup_of_lt_top
    (f := fun C : { s : Set X // s ⊆ A ∧ IsSeparated ε s } ↦ (C : Set X).encard)
  simp_rw [packingNumber] at h ⊢
  simp_rw [iSup_subtype, iSup_and] at h_exists
  specialize h_exists h.lt_top
  obtain ⟨C, hC⟩ := h_exists
  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
  · refine Set.encard_ne_top_iff.mp ?_
    rwa [hC]
  · rw [hC]
```

### `command in CoveringNumbers.lean` (command, added) [2dd14830a6]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- A finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
It is defined as the empty set if no such finite cover exists. -/
```

### `command in CoveringNumbers.lean` (command, added) [372017cde9]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- A finite `ε`-separated subset of a set `A` with maximal cardinality.
It is defined as the empty set if no such finite subset exists. -/
```

### `Metric.minimalCover_subset` (lemma, added) [390f4748cc]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma minimalCover_subset : minimalCover ε A ⊆ A := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h).choose_spec.1
  · simp [minimalCover, h]
```

### `module_doc in CoveringNumbers.lean` (module_doc, modified) [3cd3c7d279]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: documentation:modified
- before the PR:
```lean
/-!
# Covering numbers

We define covering numbers of sets in a pseudo-metric space, which are minimal cardinalities of
`ε`-covers of sets by closed balls.
We also define the packing number, which is the maximal cardinality of an `ε`-separated set.

We prove inequalities between these covering and packing numbers.

## Main definitions

* `externalCoveringNumber`: the extenal covering number of a set `A` for radius `ε` is the minimal
  cardinality (in `ℕ∞`) of an `ε`-cover.
* `coveringNumber`: the covering number (or internal covering number) of a set `A` for radius `ε` is
  the minimal cardinality (in `ℕ∞`) of an `ε`-cover contained in `A`.
* `packingNumber`: the packing number of a set `A` for radius `ε` is the maximal cardinality of
  an `ε`-separated set in `A`.

## Main statements

* `externalCoveringNumber_le_coveringNumber`: the external covering number is less than or equal to
  the covering number.
* `packingNumber_two_mul_le_externalCoveringNumber`: the packing number with radius `2 * ε` is
  less than or equal to the external covering number for `ε`.

## References

* [R. Vershynin, *High-dimensional probability*][vershynin2018high]

-/
```
- as the PR leaves it:
```lean
/-!
# Covering numbers

We define covering numbers of sets in a pseudo-metric space, which are minimal cardinalities of
`ε`-covers of sets by closed balls.
We also define the packing number, which is the maximal cardinality of an `ε`-separated set.

We prove inequalities between these covering and packing numbers.

## Main definitions

* `externalCoveringNumber`: the extenal covering number of a set `A` for radius `ε` is the minimal
  cardinality (in `ℕ∞`) of an `ε`-cover.
* `coveringNumber`: the covering number (or internal covering number) of a set `A` for radius `ε` is
  the minimal cardinality (in `ℕ∞`) of an `ε`-cover contained in `A`.
* `packingNumber`: the packing number of a set `A` for radius `ε` is the maximal cardinality of
  an `ε`-separated set in `A`.

We define sets achieving these minimal/maximal cardinalities when they exist:
* `minimalCover`: a finite internal `ε`-cover of a set `A` by closed balls with minimal cardinality.
* `maximalSeparatedSet`: a finite `ε`-separated subset of a set `A` with maximal cardinality.

## Main statements

We have the following inequalities between covering and packing numbers:
* `externalCoveringNumber_le_coveringNumber`: external covering number ≤ covering number.
* `packingNumber_two_mul_le_externalCoveringNumber`: packing number for `2 * ε` ≤ external covering
  number for `ε`.
* `coveringNumber_le_packingNumber`: covering number ≤ packing number.
* `coveringNumber_two_mul_le_externalCoveringNumber`: covering number for `2 * ε` ≤ external
  covering number for `ε`.

The covering number is not monotone for set inclusion (because the cover must be contained
in the set), but we have the following inequality:
* `coveringNumber_subset_le`: if `A ⊆ B`, then `coveringNumber ε A ≤ coveringNumber (ε / 2) B`.

## References

* [R. Vershynin, *High-dimensional probability*][vershynin2018high]

-/
```

### `Metric.finite_minimalCover` (lemma, added) [43382beac9]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma finite_minimalCover :
    (minimalCover ε A).Finite := by
  by_cases h : coveringNumber ε A ≠ ⊤
  · simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.1
  · simp [minimalCover, h]
```

### `Metric.coveringNumber_le_packingNumber` (theorem, added) [45cf88bca6]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem coveringNumber_le_packingNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber ε A ≤ packingNumber ε A := by
  by_cases h_top : packingNumber ε A ≠ ⊤
  · rw [← card_maximalSeparatedSet h_top]
    refine (iInf_le _ (maximalSeparatedSet ε A)).trans (le_of_eq ?_)
    simp [maximalSeparatedSet_subset, iInf_pos, isCover_maximalSeparatedSet h_top]
  · simp only [ne_eq, Decidable.not_not] at h_top
    simp [h_top]
```

### `Metric.coveringNumber_subset_le` (lemma, added) [74954e45a6]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma coveringNumber_subset_le (h : A ⊆ B) :
    coveringNumber ε A ≤ coveringNumber (ε / 2) B := by
  calc coveringNumber ε A
  _ ≤ packingNumber ε A := coveringNumber_le_packingNumber ε A
  _ = packingNumber (2 * (ε / 2)) A := by ring_nf
  _ ≤ externalCoveringNumber (ε / 2) A :=
    packingNumber_two_mul_le_externalCoveringNumber (ε / 2) A
  _ ≤ externalCoveringNumber (ε / 2) B := externalCoveringNumber_mono_set h
  _ ≤ coveringNumber (ε / 2) B :=
    externalCoveringNumber_le_coveringNumber (ε / 2) B
```

### `Metric.minimalCover` (def, added) [8238b5e187]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
noncomputable
def minimalCover (ε : ℝ≥0) (A : Set X) : Set X :=
  if h : coveringNumber ε A ≠ ⊤ then (exists_set_encard_eq_coveringNumber h).choose else ∅
```

### `Metric.exists_set_encard_eq_coveringNumber` (lemma, added) [834d7f62bd]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma exists_set_encard_eq_coveringNumber (h : coveringNumber ε A ≠ ⊤) :
    ∃ C, C ⊆ A ∧ C.Finite ∧ IsCover ε A C ∧ C.encard = coveringNumber ε A := by
  simp only [coveringNumber, ne_eq, iInf_eq_top, encard_eq_top_iff, not_forall, not_infinite] at h
  obtain ⟨C', hC'_subset, hC'_cover, hC'_fin⟩ := h
  have : Nonempty { s : Set X // s ⊆ A ∧ IsCover ε A s } := ⟨C', hC'_subset, hC'_cover⟩
  let h := ENat.exists_eq_iInf (fun C : {s : Set X // s ⊆ A ∧ IsCover ε A s} ↦ (C : Set X).encard)
  obtain ⟨C, hC⟩ := h
  refine ⟨C, C.2.1, ?_, C.2.2, ?_⟩
  · refine Set.encard_lt_top_iff.mp ?_
    simp only [hC, iInf_lt_top, encard_lt_top_iff, Subtype.exists, exists_prop]
    exact ⟨C', ⟨hC'_subset, hC'_cover⟩, hC'_fin⟩
  · rw [hC]
    simp_rw [iInf_subtype, iInf_and]
    rfl

open Classical in
```

### `Metric.isCover_minimalCover` (lemma, added) [b9df032196]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma isCover_minimalCover (h : coveringNumber ε A ≠ ⊤) :
    IsCover ε A (minimalCover ε A) := by
  simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
  exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.2.1
```

### `command in CoveringNumbers.lean` (command, added) [c24e2f5b50]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: value_or_body:added
- as the PR leaves it:
```lean
/-- The maximal separated set is a cover. -/
```

### `Metric.card_maximalSeparatedSet` (lemma, added) [c5c9da88f1]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma card_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    (maximalSeparatedSet ε A).encard = packingNumber ε A := by
  simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
  exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.2
```

### `Metric.coveringNumber_two_mul_le_externalCoveringNumber` (theorem, added) [c79e40846a]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem coveringNumber_two_mul_le_externalCoveringNumber (ε : ℝ≥0) (A : Set X) :
    coveringNumber (2 * ε) A ≤ externalCoveringNumber ε A := by
  rcases Set.eq_empty_or_nonempty A with (h_empty | h_nonempty)
  · simp [h_empty]
  refine (coveringNumber_le_packingNumber _ A).trans ?_
  exact packingNumber_two_mul_le_externalCoveringNumber ε A
```

### `Metric.maximalSeparatedSet_subset` (lemma, added) [c7ef58137f]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma maximalSeparatedSet_subset : maximalSeparatedSet ε A ⊆ A := by
  by_cases h : packingNumber ε A ≠ ⊤
  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_packingNumber h).choose_spec.1
  · simp only [maximalSeparatedSet, h, dite_false, Set.empty_subset]
```

### `Metric.isCover_maximalSeparatedSet` (lemma, added) [d483f48d7e]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma isCover_maximalSeparatedSet (h : packingNumber ε A ≠ ⊤) :
    IsCover ε A (maximalSeparatedSet ε A) := by
  intro x hxA
  by_contra h_dist
  push_neg at h_dist
  have hx_not_mem : x ∉ maximalSeparatedSet ε A := by
    intro hx_mem
    specialize h_dist x hx_mem
    simp at h_dist
  classical
  let C := {x} ∪ maximalSeparatedSet ε A
  have hC_subset : C ⊆ A := by
    simp [C, hxA, maximalSeparatedSet_subset, Set.insert_subset]
  have hC_separated : IsSeparated ε C := by
    intro a ha b hb hab
    by_cases hax : a = x
    · subst hax
      have hb' : b ∈ maximalSeparatedSet ε A := by simpa [C, hab.symm] using hb
      simpa using h_dist b hb'
    by_cases hbx : b = x
    · subst hbx
      have ha' : a ∈ maximalSeparatedSet ε A := by simpa [C, hab] using ha
      have h := h_dist a ha'
      simp only [mem_setOf_eq, not_le] at h
      rwa [edist_comm] at h
    simp only [singleton_union, mem_insert_iff, hax, false_or, hbx, C] at ha hb
    exact isSeparated_maximalSeparatedSet ha hb hab
  refine absurd (card_le_of_isSeparated hC_subset hC_separated h) ?_
  simp only [singleton_union, not_le, C]
  rw [encard_insert_of_notMem hx_not_mem, ENat.lt_add_one_iff]
  rwa [card_maximalSeparatedSet h]
```

### `section in CoveringNumbers.lean` (command, added) [d7faddf74f]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section MaximalSeparatedSet
```

### `Metric.card_minimalCover` (lemma, added) [dcb9537a71]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma card_minimalCover (h : coveringNumber ε A ≠ ⊤) :
    (minimalCover ε A).encard = coveringNumber ε A := by
  simp only [minimalCover, ne_eq, h, not_false_eq_true, ↓reduceDIte]
  exact (exists_set_encard_eq_coveringNumber h).choose_spec.2.2.2
```

### `Metric.isSeparated_maximalSeparatedSet` (lemma, added) [e4abffbd52]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma isSeparated_maximalSeparatedSet :
    IsSeparated ε (maximalSeparatedSet ε A : Set X) := by
  by_cases h : packingNumber ε A ≠ ⊤
  · simp only [maximalSeparatedSet, ne_eq, h, not_false_eq_true, ↓reduceDIte]
    exact (exists_set_encard_eq_packingNumber h).choose_spec.2.2.1
  · simp only [maximalSeparatedSet, h, dite_false, IsSeparated.empty]
```

### `section in CoveringNumbers.lean` (command, added) [efe8e9b10d]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section MinimalCover
```

### `Metric.card_le_of_isSeparated` (lemma, added) [f36711f889]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma card_le_of_isSeparated (h_subset : C ⊆ A)
    (h_sep : IsSeparated ε C) (h : packingNumber ε A ≠ ⊤) :
    C.encard ≤ (maximalSeparatedSet ε A).encard := by
  rw [card_maximalSeparatedSet h]
  exact le_iSup_of_le C <| le_iSup_of_le h_subset <| le_iSup_of_le h_sep (by simp)
```

### `section in CoveringNumbers.lean` (command, added) [f9509dc083]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section Comparisons
```

### `section in CoveringNumbers.lean` (command, added) [fb967ebf6a]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end Comparisons
```

### `section in CoveringNumbers.lean` (command, added) [fc293f3f7c]
- file: `Mathlib/Topology/MetricSpace/CoveringNumbers.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end MaximalSeparatedSet
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `Metric.coveringNumber_le_packingNumber`, `Metric.coveringNumber_subset_le`, `Metric.coveringNumber_two_mul_le_externalCoveringNumber`, `Metric.exists_set_encard_eq_coveringNumber`, `Metric.exists_set_encard_eq_packingNumber` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Metric.coveringNumber_le_packingNumber`, `Metric.coveringNumber_subset_le`, `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Metric.card_le_of_isSeparated`, `Metric.card_maximalSeparatedSet`, `Metric.isCover_maximalSeparatedSet`, `Metric.isSeparated_maximalSeparatedSet`, `Metric.maximalSeparatedSet`, `Metric.maximalSeparatedSet_subset` -- 6 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [exact] `Metric.card_minimalCover`, `Metric.finite_minimalCover`, `Metric.isCover_minimalCover`, `Metric.minimalCover`, `Metric.minimalCover_subset` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Metric.isCover_maximalSeparatedSet`, `Metric.isCover_minimalCover` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Metric.exists_set_encard_eq_coveringNumber`, `Metric.exists_set_encard_eq_packingNumber` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Metric.maximalSeparatedSet`, `Metric.maximalSeparatedSet_subset` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Metric.minimalCover`, `Metric.minimalCover_subset` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Metric.card_le_of_isSeparated`, `Metric.card_maximalSeparatedSet`, `Metric.card_minimalCover` -- 3 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it

## Relations between changed declarations

- changed_siblings [high]: `Metric.card_le_of_isSeparated` -> `Metric.card_maximalSeparatedSet`
- changed_siblings [high]: `Metric.card_maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- changed_siblings [high]: `Metric.card_maximalSeparatedSet` -> `Metric.isSeparated_maximalSeparatedSet`
- changed_siblings [high]: `Metric.card_minimalCover` -> `Metric.isCover_minimalCover`
- changed_siblings [high]: `Metric.coveringNumber_le_packingNumber` -> `Metric.coveringNumber_two_mul_le_externalCoveringNumber`
- changed_siblings [high]: `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -> `Metric.coveringNumber_le_packingNumber`
- changed_siblings [high]: `Metric.finite_minimalCover` -> `Metric.minimalCover_subset`
- changed_siblings [high]: `Metric.finite_minimalCover` -> `Metric.isCover_minimalCover`
- changed_siblings [high]: `Metric.isCover_minimalCover` -> `Metric.card_minimalCover`
- changed_siblings [high]: `Metric.isCover_minimalCover` -> `Metric.finite_minimalCover`
- changed_siblings [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- changed_siblings [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.card_maximalSeparatedSet`
- changed_siblings [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.isSeparated_maximalSeparatedSet`
- changed_siblings [high]: `Metric.minimalCover_subset` -> `Metric.finite_minimalCover`
- declaration_dependency [exact]: `Metric.card_le_of_isSeparated` -> `Metric.maximalSeparatedSet`
- declaration_dependency [exact]: `Metric.card_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- declaration_dependency [exact]: `Metric.card_minimalCover` -> `Metric.minimalCover`
- declaration_dependency [exact]: `Metric.finite_minimalCover` -> `Metric.minimalCover`
- declaration_dependency [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- declaration_dependency [exact]: `Metric.isCover_minimalCover` -> `Metric.minimalCover`
- declaration_dependency [exact]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- declaration_dependency [exact]: `Metric.maximalSeparatedSet_subset` -> `Metric.maximalSeparatedSet`
- declaration_dependency [exact]: `Metric.minimalCover_subset` -> `Metric.minimalCover`
- direct_use_of_changed_declaration [exact]: `Metric.card_le_of_isSeparated` -> `Metric.card_maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.card_maximalSeparatedSet` -> `Metric.exists_set_encard_eq_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.card_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.card_minimalCover` -> `Metric.minimalCover`
- direct_use_of_changed_declaration [exact]: `Metric.card_minimalCover` -> `Metric.exists_set_encard_eq_coveringNumber`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_le_packingNumber` -> `Metric.maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_le_packingNumber` -> `Metric.maximalSeparatedSet_subset`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_le_packingNumber` -> `Metric.card_maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_le_packingNumber` -> `Metric.isCover_maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_subset_le` -> `Metric.coveringNumber_le_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -> `Metric.coveringNumber_le_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.finite_minimalCover` -> `Metric.minimalCover`
- direct_use_of_changed_declaration [exact]: `Metric.finite_minimalCover` -> `Metric.exists_set_encard_eq_coveringNumber`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.card_maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.isSeparated_maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_minimalCover` -> `Metric.exists_set_encard_eq_coveringNumber`
- direct_use_of_changed_declaration [exact]: `Metric.isCover_minimalCover` -> `Metric.minimalCover`
- direct_use_of_changed_declaration [exact]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.exists_set_encard_eq_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.maximalSeparatedSet` -> `Metric.exists_set_encard_eq_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.maximalSeparatedSet_subset` -> `Metric.maximalSeparatedSet`
- direct_use_of_changed_declaration [exact]: `Metric.maximalSeparatedSet_subset` -> `Metric.exists_set_encard_eq_packingNumber`
- direct_use_of_changed_declaration [exact]: `Metric.minimalCover` -> `Metric.exists_set_encard_eq_coveringNumber`
- direct_use_of_changed_declaration [exact]: `Metric.minimalCover_subset` -> `Metric.exists_set_encard_eq_coveringNumber`
- direct_use_of_changed_declaration [exact]: `Metric.minimalCover_subset` -> `Metric.minimalCover`
- name_family [high]: `Metric.card_le_of_isSeparated` -> `Metric.isCover_maximalSeparatedSet`
- name_family [high]: `Metric.card_le_of_isSeparated` -> `Metric.isSeparated_maximalSeparatedSet`
- name_family [high]: `Metric.card_le_of_isSeparated` -> `Metric.maximalSeparatedSet`
- name_family [high]: `Metric.card_le_of_isSeparated` -> `Metric.card_maximalSeparatedSet`
- name_family [high]: `Metric.card_le_of_isSeparated` -> `Metric.maximalSeparatedSet_subset`
- name_family [high]: `Metric.card_maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- name_family [high]: `Metric.card_maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- name_family [high]: `Metric.card_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- name_family [high]: `Metric.card_maximalSeparatedSet` -> `Metric.isCover_maximalSeparatedSet`
- name_family [high]: `Metric.card_maximalSeparatedSet` -> `Metric.isSeparated_maximalSeparatedSet`
- name_family [high]: `Metric.card_minimalCover` -> `Metric.isCover_minimalCover`
- name_family [high]: `Metric.card_minimalCover` -> `Metric.minimalCover_subset`
- name_family [high]: `Metric.card_minimalCover` -> `Metric.finite_minimalCover`
- name_family [high]: `Metric.card_minimalCover` -> `Metric.minimalCover`
- name_family [high]: `Metric.coveringNumber_le_packingNumber` -> `Metric.coveringNumber_subset_le`
- name_family [high]: `Metric.coveringNumber_le_packingNumber` -> `Metric.exists_set_encard_eq_packingNumber`
- name_family [high]: `Metric.coveringNumber_le_packingNumber` -> `Metric.coveringNumber_two_mul_le_externalCoveringNumber`
- name_family [high]: `Metric.coveringNumber_le_packingNumber` -> `Metric.exists_set_encard_eq_coveringNumber`
- name_family [high]: `Metric.coveringNumber_subset_le` -> `Metric.coveringNumber_two_mul_le_externalCoveringNumber`
- name_family [high]: `Metric.coveringNumber_subset_le` -> `Metric.exists_set_encard_eq_coveringNumber`
- name_family [high]: `Metric.coveringNumber_subset_le` -> `Metric.coveringNumber_le_packingNumber`
- name_family [high]: `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -> `Metric.coveringNumber_subset_le`
- name_family [high]: `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -> `Metric.coveringNumber_le_packingNumber`
- name_family [high]: `Metric.coveringNumber_two_mul_le_externalCoveringNumber` -> `Metric.exists_set_encard_eq_coveringNumber`
- name_family [high]: `Metric.exists_set_encard_eq_coveringNumber` -> `Metric.coveringNumber_subset_le`
- name_family [high]: `Metric.exists_set_encard_eq_coveringNumber` -> `Metric.coveringNumber_two_mul_le_externalCoveringNumber`
- name_family [high]: `Metric.exists_set_encard_eq_coveringNumber` -> `Metric.coveringNumber_le_packingNumber`
- name_family [high]: `Metric.exists_set_encard_eq_packingNumber` -> `Metric.coveringNumber_le_packingNumber`
- name_family [high]: `Metric.finite_minimalCover` -> `Metric.card_minimalCover`
- name_family [high]: `Metric.finite_minimalCover` -> `Metric.isCover_minimalCover`
- name_family [high]: `Metric.finite_minimalCover` -> `Metric.minimalCover_subset`
- name_family [high]: `Metric.finite_minimalCover` -> `Metric.minimalCover`
- name_family [high]: `Metric.isCover_maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- name_family [high]: `Metric.isCover_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- name_family [high]: `Metric.isCover_maximalSeparatedSet` -> `Metric.card_maximalSeparatedSet`
- name_family [high]: `Metric.isCover_maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- name_family [high]: `Metric.isCover_maximalSeparatedSet` -> `Metric.isSeparated_maximalSeparatedSet`
- name_family [high]: `Metric.isCover_minimalCover` -> `Metric.minimalCover`
- name_family [high]: `Metric.isCover_minimalCover` -> `Metric.finite_minimalCover`
- name_family [high]: `Metric.isCover_minimalCover` -> `Metric.minimalCover_subset`
- name_family [high]: `Metric.isCover_minimalCover` -> `Metric.card_minimalCover`
- name_family [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.card_maximalSeparatedSet`
- name_family [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.isCover_maximalSeparatedSet`
- name_family [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- name_family [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.maximalSeparatedSet`
- name_family [high]: `Metric.isSeparated_maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- name_family [high]: `Metric.maximalSeparatedSet` -> `Metric.isSeparated_maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet` -> `Metric.card_maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet` -> `Metric.isCover_maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet` -> `Metric.card_le_of_isSeparated`
- name_family [high]: `Metric.maximalSeparatedSet` -> `Metric.maximalSeparatedSet_subset`
- name_family [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.card_le_of_isSeparated`
- name_family [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.isCover_maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.card_maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.maximalSeparatedSet`
- name_family [high]: `Metric.maximalSeparatedSet_subset` -> `Metric.isSeparated_maximalSeparatedSet`
- name_family [high]: `Metric.minimalCover` -> `Metric.finite_minimalCover`
- name_family [high]: `Metric.minimalCover` -> `Metric.minimalCover_subset`
- name_family [high]: `Metric.minimalCover` -> `Metric.card_minimalCover`
- name_family [high]: `Metric.minimalCover` -> `Metric.isCover_minimalCover`
- name_family [high]: `Metric.minimalCover_subset` -> `Metric.isCover_minimalCover`
- name_family [high]: `Metric.minimalCover_subset` -> `Metric.finite_minimalCover`
- name_family [high]: `Metric.minimalCover_subset` -> `Metric.minimalCover`
- name_family [high]: `Metric.minimalCover_subset` -> `Metric.card_minimalCover`
