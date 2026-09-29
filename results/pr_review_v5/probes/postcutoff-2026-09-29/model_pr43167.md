# The PR model for #43167 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(GroupTheory/Commutator/Basic): prove `⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆` for `N` normal
- description: This PR proves distributivity `⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆` for `N` normal.

The idea is to compute `⁅H ⊔ K, N⁆` in the quotient `(H ⊔ K ⊔ N) ⧸ (⁅H, N⁆ ⊔ ⁅K, N⁆)`.

I also moved `normalizer_inf_normalizer_le_normalizer_sup` to an earlier file and renamed it to match `inf_normalizer_le_normalizer_inf`.
- changed files: Mathlib/Algebra/Group/Subgroup/Basic.lean, Mathlib/Algebra/Group/Subgroup/Pointwise.lean, Mathlib/GroupTheory/Commutator/Basic.lean

## Objects

### `attribute in Basic.lean` (command, added) [53d533b98c]
- file: `Mathlib/Algebra/Group/Subgroup/Basic.lean`; changed: unknown:added
- as the PR leaves it:
```lean
@[deprecated (since := "2026-08-27")]
alias _root_.AddSubgroup.normalizer_inf_normalizer_le_normalizer_sup :=
  AddSubgroup.inf_normalizer_le_normalizer_sup
```

### `Subgroup.inf_normalizer_le_normalizer_sup` (lemma, added) [d6599d1e95]
- file: `Mathlib/Algebra/Group/Subgroup/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
lemma inf_normalizer_le_normalizer_sup (H K : Subgroup G) :
    normalizer H ⊓ normalizer K ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) := by
  intro g hg
  simp_rw [mem_inf, mem_normalizer_iff_map_conj_eq, map_sup, hg.1, hg.2] at hg ⊢
```

### `attribute in Basic.lean` (command, added) [e474b2b644]
- file: `Mathlib/Algebra/Group/Subgroup/Basic.lean`; changed: unknown:added
- as the PR leaves it:
```lean
@[deprecated (since := "2026-08-27")] alias normalizer_inf_normalizer_le_normalizer_sup :=
  inf_normalizer_le_normalizer_sup
```

### `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` (lemma, modified) [46dc630ab4]
- file: `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`; changed: proof:modified
- before the PR:
```lean
@[to_additive]
lemma conj_mem_sup_of_mem_inf_normalizer_of_mem_inf
    {H K : Subgroup G} {s : G} (hs : s ∈ normalizer H ⊓ normalizer K) (g : G) (hg : g ∈ H ⊔ K) :
    s * g * s⁻¹ ∈ H ⊔ K :=
  (normalizer_inf_normalizer_le_normalizer_sup H K hs g).mp hg
```
- as the PR leaves it:
```lean
@[to_additive]
lemma conj_mem_sup_of_mem_inf_normalizer_of_mem_inf
    {H K : Subgroup G} {s : G} (hs : s ∈ normalizer H ⊓ normalizer K) (g : G) (hg : g ∈ H ⊔ K) :
    s * g * s⁻¹ ∈ H ⊔ K :=
  (inf_normalizer_le_normalizer_sup H K hs g).mp hg
```

### `import in Pointwise.lean` (import, modified) [795d089995]
- file: `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`; changed: imports:added

### `Subgroup.normalizer_inf_normalizer_le_normalizer_sup` (lemma, removed) [86450b97f6]
- file: `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`; changed: attributes:removed, name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
@[to_additive]
lemma normalizer_inf_normalizer_le_normalizer_sup (H K : Subgroup G) :
    normalizer H ⊓ normalizer K ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) := by
  intro g hg
  simp_rw [mem_inf, mem_normalizer_iff_map_conj_eq, map_sup, hg.1, hg.2] at hg ⊢
```

### `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` (lemma, modified) [a23af478d7]
- file: `Mathlib/Algebra/Group/Subgroup/Pointwise.lean`; changed: proof:modified
- before the PR:
```lean
@[to_additive]
lemma normalizer_le_normalizer_sup_of_normalizer_le_left
    {H K : Subgroup G} (hHnK : normalizer H ≤ normalizer (K : Set G)) :
    normalizer H ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) :=
  (inf_of_le_left hHnK).symm.trans_le (H.normalizer_inf_normalizer_le_normalizer_sup K)
```
- as the PR leaves it:
```lean
@[to_additive]
lemma normalizer_le_normalizer_sup_of_normalizer_le_left
    {H K : Subgroup G} (hHnK : normalizer H ≤ normalizer (K : Set G)) :
    normalizer H ≤ normalizer ((H ⊔ K : Subgroup G) : Set G) :=
  (inf_of_le_left hHnK).symm.trans_le (H.inf_normalizer_le_normalizer_sup K)
```

### `Subgroup.commutator_sup_right` (theorem, added) [3cc3f4cfdc]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem commutator_sup_right (N H K : Subgroup G) [N.Normal] : ⁅N, H ⊔ K⁆ = ⁅N, H⁆ ⊔ ⁅N, K⁆ := by
  simp_rw [commutator_comm N, commutator_sup_left]
```

### `Subgroup.commutator_mono_left` (theorem, added) [4899ddcad1]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := gcongr)]
theorem commutator_mono_left (h : H₁ ≤ H₂) : ⁅H₁, K⁆ ≤ ⁅H₂, K⁆ :=
  commutator_mono h le_rfl
```

### `Subgroup.commutator_mono_right` (theorem, added) [5a580a7f38]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive (attr := gcongr)]
theorem commutator_mono_right (h : K₁ ≤ K₂) : ⁅H, K₁⁆ ≤ ⁅H, K₂⁆ :=
  commutator_mono le_rfl h
```

### `Subgroup.commutator_le_of_le` (theorem, added) [777ceb8490]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
@[to_additive]
theorem commutator_le_of_le (h₁ : K₁ ≤ K) (h₂ : K₂ ≤ K) : ⁅K₁, K₂⁆ ≤ K :=
  (commutator_le_sup K₁ K₂).trans (sup_le h₁ h₂)
```

### `Subgroup.commutator_sup_left'` (theorem, added) [ab27e55422]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
private theorem commutator_sup_left' (H K N : Subgroup G) [(⁅H, N⁆ ⊔ ⁅K, N⁆).Normal] :
    ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
  refine le_antisymm ?_
    (sup_le (commutator_mono_left le_sup_left) (commutator_mono_left le_sup_right))
  have hH : ⁅H, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_left
  have hK : ⁅K, N⁆ ≤ ⁅H, N⁆ ⊔ ⁅K, N⁆ := le_sup_right
  rw [← QuotientGroup.ker_mk' (⁅H, N⁆ ⊔ ⁅K, N⁆), ← Subgroup.map_eq_bot_iff,
    map_commutator, Subgroup.commutator_eq_bot_iff_le_centralizer] at hH hK ⊢
  rw [map_sup]
  exact sup_le hH hK
```

### `Subgroup.commutator_sup_left` (theorem, added) [cf8d057d6a]
- file: `Mathlib/GroupTheory/Commutator/Basic.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem commutator_sup_left (H K N : Subgroup G) [N.Normal] : ⁅H ⊔ K, N⁆ = ⁅H, N⁆ ⊔ ⁅K, N⁆ := by
  let M := H ⊔ K ⊔ N
  have hHM : H ≤ M := le_sup_of_le_left le_sup_left
  have hKM : K ≤ M := le_sup_of_le_left le_sup_right
  have hNM : N ≤ M := le_sup_right
  have hHNM : ⁅H, N⁆ ≤ M := commutator_le_of_le hHM hNM
  have hKNM : ⁅K, N⁆ ≤ M := commutator_le_of_le hKM hNM
  suffices (⁅H.subgroupOf M, N.subgroupOf M⁆ ⊔ ⁅K.subgroupOf M, N.subgroupOf M⁆).Normal by
    simpa [← map_subtype_inj, map_sup, map_commutator, hHM, hKM, hNM] using
      commutator_sup_left' (H.subgroupOf M) (K.subgroupOf M) (N.subgroupOf M)
  suffices M ≤ normalizer (⁅H, N⁆ ⊔ ⁅K, N⁆ : Subgroup G) by
    convert Subgroup.normal_subgroupOf_of_le_normalizer this
    simp [← map_subtype_inj, map_sup, map_commutator, hHM, hKM, hNM, hHNM, hKNM]
  have hHKN : ⁅H, N⁆ ⊔ ⁅K, N⁆ ≤ N := sup_le (commutator_le_right H N) (commutator_le_right K N)
  refine sup_le (sup_le ?_ ?_) ?_
  · grw [le_normalizer_iff_commutator_le_right, hHKN, ← le_sup_left]
  · grw [le_normalizer_iff_commutator_le_right, hHKN, ← le_sup_right]
  · grw [← inf_normalizer_le_normalizer_sup, ← normalizer_commutator_ge_right,
      ← normalizer_commutator_ge_right, inf_idem]
```

## Removed or renamed

- `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`

## Families (declarations that may be one decision)

- [exact] `Subgroup.commutator_le_of_le`, `Subgroup.commutator_mono_left`, `Subgroup.commutator_mono_right`, `Subgroup.commutator_sup_left`, `Subgroup.commutator_sup_left'`, `Subgroup.commutator_sup_right` -- 6 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings
- [hypothesis] `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`, `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`, `Subgroup.inf_normalizer_le_normalizer_sup`, `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`, `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -- 4 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_mono_right`
- changed_siblings [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_mono_left`
- changed_siblings [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_sup_right`
- changed_siblings [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_sup_left'`
- changed_siblings [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_sup_left`
- changed_siblings [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_sup_left`
- changed_siblings [high]: `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` -> `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left`
- changed_siblings [high]: `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -> `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`
- direct_use_of_changed_declaration [exact]: `Subgroup.commutator_sup_left` -> `Subgroup.inf_normalizer_le_normalizer_sup`
- direct_use_of_changed_declaration [exact]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_sup_left'`
- direct_use_of_changed_declaration [exact]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_le_of_le`
- direct_use_of_changed_declaration [exact]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_mono_left`
- direct_use_of_changed_declaration [exact]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_sup_left`
- direct_use_of_changed_declaration [exact]: `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` -> `Subgroup.inf_normalizer_le_normalizer_sup`
- direct_use_of_changed_declaration [exact]: `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -> `Subgroup.inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.commutator_le_of_le` -> `Subgroup.commutator_sup_right`
- name_family [high]: `Subgroup.commutator_le_of_le` -> `Subgroup.commutator_sup_left'`
- name_family [high]: `Subgroup.commutator_le_of_le` -> `Subgroup.commutator_mono_left`
- name_family [high]: `Subgroup.commutator_le_of_le` -> `Subgroup.commutator_sup_left`
- name_family [high]: `Subgroup.commutator_le_of_le` -> `Subgroup.commutator_mono_right`
- name_family [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_sup_left`
- name_family [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_sup_right`
- name_family [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_le_of_le`
- name_family [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_mono_right`
- name_family [high]: `Subgroup.commutator_mono_left` -> `Subgroup.commutator_sup_left'`
- name_family [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_sup_left'`
- name_family [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_sup_left`
- name_family [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_sup_right`
- name_family [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_le_of_le`
- name_family [high]: `Subgroup.commutator_mono_right` -> `Subgroup.commutator_mono_left`
- name_family [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_sup_left'`
- name_family [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_mono_right`
- name_family [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_mono_left`
- name_family [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_sup_right`
- name_family [high]: `Subgroup.commutator_sup_left` -> `Subgroup.commutator_le_of_le`
- name_family [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_le_of_le`
- name_family [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_sup_right`
- name_family [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_mono_right`
- name_family [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_mono_left`
- name_family [high]: `Subgroup.commutator_sup_left'` -> `Subgroup.commutator_sup_left`
- name_family [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_sup_left'`
- name_family [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_mono_left`
- name_family [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_le_of_le`
- name_family [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_mono_right`
- name_family [high]: `Subgroup.commutator_sup_right` -> `Subgroup.commutator_sup_left`
- name_family [high]: `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` -> `Subgroup.inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` -> `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left`
- name_family [high]: `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` -> `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.inf_normalizer_le_normalizer_sup` -> `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left`
- name_family [high]: `Subgroup.inf_normalizer_le_normalizer_sup` -> `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.inf_normalizer_le_normalizer_sup` -> `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`
- name_family [high]: `Subgroup.normalizer_inf_normalizer_le_normalizer_sup` -> `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`
- name_family [high]: `Subgroup.normalizer_inf_normalizer_le_normalizer_sup` -> `Subgroup.inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.normalizer_inf_normalizer_le_normalizer_sup` -> `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left`
- name_family [high]: `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -> `Subgroup.normalizer_inf_normalizer_le_normalizer_sup`
- name_family [high]: `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -> `Subgroup.conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`
- name_family [high]: `Subgroup.normalizer_le_normalizer_sup_of_normalizer_le_left` -> `Subgroup.inf_normalizer_le_normalizer_sup`
