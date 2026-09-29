# The PR model for #41280 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Geometry/Manifold): C^n smoothness of the inverse of a bundle trivialization
- description: Adds `Bundle.Trivialization.contMDiffAt_symmL`: For a trivialization `e` of a `C^n` vector bundle `E₁ → B` and a point `x ∈ e.baseSet` the section `m ↦ e.symmL 𝕜 m` defines a `C^n` section of the hom bundle `Hom(F₁, E₁)`.

We also provide a `contMDiffOn` version.

This PR was prepared with assistance from Claude.
- changed files: Mathlib/Geometry/Manifold/VectorBundle/Hom.lean

## Objects

### `Bundle.Trivialization.contMDiffOn_symmL` (lemma, added) [033b58dcd9]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma Bundle.Trivialization.contMDiffOn_symmL [IsManifold IB n B] [ContMDiffVectorBundle n F₁ E₁ IB]
    (e : Trivialization F₁ (TotalSpace.proj : TotalSpace F₁ E₁ → B)) [MemTrivializationAtlas e] :
    ContMDiffOn IB (IB.prod 𝓘(𝕜, F₁ →L[𝕜] F₁)) n
      (fun m ↦ TotalSpace.mk' (F₁ →L[𝕜] F₁) m (e.symmL 𝕜 m)) e.baseSet :=
  fun _ hx ↦ (e.contMDiffAt_symmL hx).contMDiffWithinAt
```

### `section in Hom.lean` (command, added) [29aa882098]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section symmL
```

### `doc_comment in Hom.lean` (command, added) [2bc398d53d]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Let `e` be a trivialization of a `C^n` vector bundle `E₁` over `B`. Then `m ↦ e.symmL 𝕜 m`
defines a section of the bundle of continuous linear maps `F₁ →L[𝕜] E₁` over `B`, and this section
is `C^n` on `e.baseSet`. -/
```

### `section in Hom.lean` (command, added) [5ac86454eb]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {𝕜 B F₁ : Type*} [NontriviallyNormedField 𝕜] {n : WithTop ℕ∞}
  {EB : Type*} [NormedAddCommGroup EB] [NormedSpace 𝕜 EB] {HB : Type*} [TopologicalSpace HB]
  {IB : ModelWithCorners 𝕜 EB HB} [TopologicalSpace B] [ChartedSpace HB B]
  {E₁ : B → Type*} [∀ x, AddCommGroup (E₁ x)] [∀ x, Module 𝕜 (E₁ x)]
  [NormedAddCommGroup F₁] [NormedSpace 𝕜 F₁]
  [TopologicalSpace (TotalSpace F₁ E₁)] [∀ x, TopologicalSpace (E₁ x)]
  [∀ x, IsTopologicalAddGroup (E₁ x)] [∀ x, ContinuousSMul 𝕜 (E₁ x)]
  [FiberBundle F₁ E₁] [VectorBundle 𝕜 F₁ E₁]
```

### `section in Hom.lean` (command, added) [7cad96f1e2]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end symmL
```

### `Bundle.Trivialization.contMDiffAt_symmL` (lemma, added) [90c80d2571]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
lemma Bundle.Trivialization.contMDiffAt_symmL [IsManifold IB n B] [ContMDiffVectorBundle n F₁ E₁ IB]
    (e : Trivialization F₁ (TotalSpace.proj : TotalSpace F₁ E₁ → B)) [MemTrivializationAtlas e]
    {x : B} (hx : x ∈ e.baseSet) :
    ContMDiffAt IB (IB.prod 𝓘(𝕜, F₁ →L[𝕜] F₁)) n
      (fun m ↦ TotalSpace.mk' (F₁ →L[𝕜] F₁) m (e.symmL 𝕜 m)) x := by
  have hx' : x ∈ (trivializationAt F₁ E₁ x).baseSet := mem_baseSet_trivializationAt F₁ E₁ x
  refine contMDiffAt_totalSpace.mpr ⟨contMDiffAt_id, ?_⟩
  apply (contMDiffAt_coordChangeL hx hx').congr_of_eventuallyEq
  filter_upwards [e.open_baseSet.mem_nhds hx,
    (trivializationAt F₁ E₁ x).open_baseSet.mem_nhds hx'] with b hb hb'
  ext v
  simp [hom_trivializationAt_apply, ContinuousLinearMap.inCoordinates,
    coordChangeL_apply' e _ ⟨hb, hb'⟩, coe_linearMapAt_of_mem _ hb',
    e.symmL_apply hb, e.mk_symm hb]
```

### `doc_comment in Hom.lean` (command, added) [d36cdb8bb8]
- file: `Mathlib/Geometry/Manifold/VectorBundle/Hom.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-- Let `e` be a trivialization of a `C^n` vector bundle `E₁` over `B`. Then `m ↦ e.symmL 𝕜 m`
defines a section of the bundle of continuous linear maps `F₁ →L[𝕜] E₁` over `B`, and this section
is `C^n` at any point in `e.baseSet`. -/
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- none found by the change graph

## Relations between changed declarations

- direct_use_of_changed_declaration [exact]: `Bundle.Trivialization.contMDiffOn_symmL` -> `Bundle.Trivialization.contMDiffAt_symmL`
