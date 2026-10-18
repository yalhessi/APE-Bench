# The PR model for #33337 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: chore(Analysis/InnerProductSpace/Projection/Submodule): rename lemmas
- description: (not recoverable at review start)
- changed files: Mathlib/Analysis/InnerProductSpace/Positive.lean, Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean

## Objects

### `Submodule.starProjection_le_starProjection_iff` (theorem, modified) [55a3ff7a8f]
- file: `Mathlib/Analysis/InnerProductSpace/Positive.lean`; changed: proof:modified
- before the PR:
```lean
theorem Submodule.starProjection_le_starProjection_iff {U V : Submodule 𝕜 E}
    [U.HasOrthogonalProjection] [V.HasOrthogonalProjection] :
    U.starProjection ≤ V.starProjection ↔ U ≤ V := by
  simp_rw [← coe_le_coe_iff, isSymmetricProjection_starProjection _
      |>.le_iff_range_le_range <| isSymmetricProjection_starProjection _,
    starProjection_coe_eq_isCompl_projection, IsCompl.projection_range]
```
- as the PR leaves it:
```lean
theorem Submodule.starProjection_le_starProjection_iff {U V : Submodule 𝕜 E}
    [U.HasOrthogonalProjection] [V.HasOrthogonalProjection] :
    U.starProjection ≤ V.starProjection ↔ U ≤ V := by
  simp_rw [← coe_le_coe_iff, isSymmetricProjection_starProjection _
      |>.le_iff_range_le_range <| isSymmetricProjection_starProjection _,
    coe_starProjection_eq_isComplProjection, IsCompl.projection_range]
```

### `LinearMap.IsSymmetricProjection.le_iff_range_le_range` (theorem, modified) [bd579ca6ae]
- file: `Mathlib/Analysis/InnerProductSpace/Positive.lean`; changed: proof:modified
- before the PR:
```lean
theorem IsSymmetricProjection.le_iff_range_le_range {p q : E →ₗ[𝕜] E}
    (hp : p.IsSymmetricProjection) (hq : q.IsSymmetricProjection) : p ≤ q ↔ range p ≤ range q := by
  refine ⟨fun ⟨h1, h2⟩ a ha ↦ ?_, fun hpq ↦ (hp.sub_of_range_le_range hq hpq).isPositive⟩
  specialize h2 a
  have hh {T : E →ₗ[𝕜] E} (hT : T.IsSymmetricProjection) : RCLike.re ⟪T a, a⟫_𝕜 = ‖T a‖ ^ 2 := by
    conv_lhs => rw [← hT.isIdempotentElem]
    rw [Module.End.mul_apply, hT.isSymmetric]
    exact inner_self_eq_norm_sq _
  simp_rw [sub_apply, inner_sub_left, map_sub, hh hq, hh hp,
    hp.isIdempotentElem.mem_range_iff.mp ha, sub_nonneg, sq_le_sq, abs_norm] at h2
  obtain ⟨U, _, rfl⟩ := isSymmetricProjection_iff_eq_coe_starProjection.mp hq
  simpa [Submodule.starProjection_coe_eq_isCompl_projection] using
    U.mem_iff_norm_starProjection _ |>.mpr <| le_antisymm (U.norm_starProjection_apply_le a) h2
```
- as the PR leaves it:
```lean
theorem IsSymmetricProjection.le_iff_range_le_range {p q : E →ₗ[𝕜] E}
    (hp : p.IsSymmetricProjection) (hq : q.IsSymmetricProjection) : p ≤ q ↔ range p ≤ range q := by
  refine ⟨fun ⟨h1, h2⟩ a ha ↦ ?_, fun hpq ↦ (hp.sub_of_range_le_range hq hpq).isPositive⟩
  specialize h2 a
  have hh {T : E →ₗ[𝕜] E} (hT : T.IsSymmetricProjection) : RCLike.re ⟪T a, a⟫_𝕜 = ‖T a‖ ^ 2 := by
    conv_lhs => rw [← hT.isIdempotentElem]
    rw [Module.End.mul_apply, hT.isSymmetric]
    exact inner_self_eq_norm_sq _
  simp_rw [sub_apply, inner_sub_left, map_sub, hh hq, hh hp,
    hp.isIdempotentElem.mem_range_iff.mp ha, sub_nonneg, sq_le_sq, abs_norm] at h2
  obtain ⟨U, _, rfl⟩ := isSymmetricProjection_iff_eq_coe_starProjection.mp hq
  simpa [Submodule.coe_starProjection_eq_isComplProjection] using
    U.mem_iff_norm_starProjection _ |>.mpr <| le_antisymm (U.norm_starProjection_apply_le a) h2
```

### `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` (theorem, modified) [19b24c6c42]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: name:modified
- before the PR:
```lean
theorem orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] (x : E) :
    K.orthogonalProjection x =
      K.linearProjOfIsCompl _ Submodule.isCompl_orthogonal_of_hasOrthogonalProjection x := by
  have : IsCompl K Kᗮ := Submodule.isCompl_orthogonal_of_hasOrthogonalProjection
  conv_lhs => rw [← IsCompl.projection_add_projection_eq_self this x]
  simp_rw [IsCompl.projection_apply]
  rw [map_add, orthogonalProjection_mem_subspace_eq_self,
    orthogonalProjection_mem_subspace_orthogonalComplement_eq_zero (Submodule.coe_mem _), add_zero]
```
- as the PR leaves it:
```lean
theorem orthogonalProjection_apply_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] (x : E) :
    K.orthogonalProjection x =
      K.linearProjOfIsCompl _ Submodule.isCompl_orthogonal_of_hasOrthogonalProjection x := by
  have : IsCompl K Kᗮ := Submodule.isCompl_orthogonal_of_hasOrthogonalProjection
  conv_lhs => rw [← IsCompl.projection_add_projection_eq_self this x]
  simp_rw [IsCompl.projection_apply]
  rw [map_add, orthogonalProjection_mem_subspace_eq_self,
    orthogonalProjection_mem_subspace_orthogonalComplement_eq_zero (Submodule.coe_mem _), add_zero]
```

### `Submodule.coe_starProjection_eq_isComplProjection` (theorem, modified) [4da0a29709]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
theorem starProjection_coe_eq_isCompl_projection [K.HasOrthogonalProjection] :
    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by
  simp [starProjection, orthogonalProjection_coe_eq_linearProjOfIsCompl, IsCompl.projection]
```
- as the PR leaves it:
```lean
theorem coe_starProjection_eq_isComplProjection [K.HasOrthogonalProjection] :
    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by
  simp [starProjection, coe_orthogonalProjection_eq_linearProjOfIsCompl, IsCompl.projection]
```

### `command in Submodule.lean` (command, modified) [63c89a0456]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_eq_linear_proj :=
  orthogonalProjection_eq_linearProjOfIsCompl
```
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-26")] alias orthogonalProjection_eq_linearProjOfIsCompl :=
  orthogonalProjection_apply_eq_linearProjOfIsCompl
```

### `command in Submodule.lean` (command, modified) [8c7322d74f]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_coe_linearMap_eq_linearProj :=
  orthogonalProjection_coe_eq_linearProjOfIsCompl
```
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-26")] alias orthogonalProjection_coe_eq_linearProjOfIsCompl :=
  coe_orthogonalProjection_eq_linearProjOfIsCompl
```

### `command in Submodule.lean` (command, added) [9647dfc5cb]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: value_or_body:modified
- as the PR leaves it:
```lean
@[deprecated (since := "2025-12-26")] alias starProjection_coe_eq_isCompl_projection :=
  coe_starProjection_eq_isComplProjection
```

### `command in Submodule.lean` (command, modified) [b6195423be]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_coe_linearMap_eq_linearProj :=
  orthogonalProjection_coe_eq_linearProjOfIsCompl
```
- as the PR leaves it:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_coe_linearMap_eq_linearProj :=
  coe_orthogonalProjection_eq_linearProjOfIsCompl
```

### `command in Submodule.lean` (command, modified) [ca472725e5]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: value_or_body:modified
- before the PR:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_eq_linear_proj :=
  orthogonalProjection_eq_linearProjOfIsCompl
```
- as the PR leaves it:
```lean
@[deprecated (since := "2025-07-11")] alias orthogonalProjection_eq_linear_proj :=
  orthogonalProjection_apply_eq_linearProjOfIsCompl
```

### `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` (theorem, modified) [d2466bcc94]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: name:modified, proof:modified
- before the PR:
```lean
theorem orthogonalProjection_coe_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] :
    (K.orthogonalProjection : E →ₗ[𝕜] K) =
      K.linearProjOfIsCompl _ Submodule.isCompl_orthogonal_of_hasOrthogonalProjection :=
  LinearMap.ext <| orthogonalProjection_eq_linearProjOfIsCompl
```
- as the PR leaves it:
```lean
theorem coe_orthogonalProjection_eq_linearProjOfIsCompl [K.HasOrthogonalProjection] :
    (K.orthogonalProjection : E →ₗ[𝕜] K) =
      K.linearProjOfIsCompl _ Submodule.isCompl_orthogonal_of_hasOrthogonalProjection :=
  LinearMap.ext <| orthogonalProjection_apply_eq_linearProjOfIsCompl
```

### `Submodule.starProjection_coe_eq_isCompl_projection` (theorem, removed) [ecd39404c9]
- file: `Mathlib/Analysis/InnerProductSpace/Projection/Submodule.lean`; changed: name:removed, proof:removed, statement_or_type:removed
- before the PR:
```lean
theorem starProjection_coe_eq_isCompl_projection [K.HasOrthogonalProjection] :
    K.starProjection.toLinearMap = K.isCompl_orthogonal_of_hasOrthogonalProjection.projection := by
  simp [starProjection, orthogonalProjection_coe_eq_linearProjOfIsCompl, IsCompl.projection]
```

## Removed or renamed

- `Submodule.starProjection_coe_eq_isCompl_projection`

## Families (declarations that may be one decision)

- [hypothesis] `Submodule.starProjection_coe_eq_isCompl_projection`, `Submodule.starProjection_le_starProjection_iff` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [hypothesis] `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`, `Submodule.coe_starProjection_eq_isComplProjection` -- 2 declarations share a namespace and leading name token, so they MAY be one API — a rename, a dualisation or a missing counterpart would be one decision about all of them. This is a suspicion from their names, not an established relation: check the statements before relying on it
- [exact] `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`, `Submodule.coe_starProjection_eq_isComplProjection`, `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`, `Submodule.starProjection_coe_eq_isCompl_projection`, `Submodule.starProjection_le_starProjection_iff` -- 5 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `LinearMap.IsSymmetricProjection.le_iff_range_le_range` -> `Submodule.coe_starProjection_eq_isComplProjection`
- direct_use_of_changed_declaration [exact]: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` -> `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`
- direct_use_of_changed_declaration [exact]: `Submodule.coe_starProjection_eq_isComplProjection` -> `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`
- direct_use_of_changed_declaration [exact]: `Submodule.starProjection_le_starProjection_iff` -> `Submodule.coe_starProjection_eq_isComplProjection`
- direct_use_of_changed_declaration [exact]: `Submodule.starProjection_le_starProjection_iff` -> `LinearMap.IsSymmetricProjection.le_iff_range_le_range`
- name_family [high]: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` -> `Submodule.coe_starProjection_eq_isComplProjection`
- name_family [high]: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` -> `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` -> `Submodule.starProjection_coe_eq_isCompl_projection`
- name_family [high]: `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl` -> `Submodule.starProjection_le_starProjection_iff`
- name_family [high]: `Submodule.coe_starProjection_eq_isComplProjection` -> `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.coe_starProjection_eq_isComplProjection` -> `Submodule.starProjection_coe_eq_isCompl_projection`
- name_family [high]: `Submodule.coe_starProjection_eq_isComplProjection` -> `Submodule.starProjection_le_starProjection_iff`
- name_family [high]: `Submodule.coe_starProjection_eq_isComplProjection` -> `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` -> `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` -> `Submodule.starProjection_coe_eq_isCompl_projection`
- name_family [high]: `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` -> `Submodule.coe_starProjection_eq_isComplProjection`
- name_family [high]: `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl` -> `Submodule.starProjection_le_starProjection_iff`
- name_family [high]: `Submodule.starProjection_coe_eq_isCompl_projection` -> `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.starProjection_coe_eq_isCompl_projection` -> `Submodule.coe_starProjection_eq_isComplProjection`
- name_family [high]: `Submodule.starProjection_coe_eq_isCompl_projection` -> `Submodule.starProjection_le_starProjection_iff`
- name_family [high]: `Submodule.starProjection_coe_eq_isCompl_projection` -> `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.starProjection_le_starProjection_iff` -> `Submodule.coe_starProjection_eq_isComplProjection`
- name_family [high]: `Submodule.starProjection_le_starProjection_iff` -> `Submodule.starProjection_coe_eq_isCompl_projection`
- name_family [high]: `Submodule.starProjection_le_starProjection_iff` -> `Submodule.orthogonalProjection_apply_eq_linearProjOfIsCompl`
- name_family [high]: `Submodule.starProjection_le_starProjection_iff` -> `Submodule.coe_orthogonalProjection_eq_linearProjOfIsCompl`
