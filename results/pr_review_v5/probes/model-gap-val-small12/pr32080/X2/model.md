# The PR model for #32080 (pass 0)

Built deterministically from the diff and the change graph, with no review text. Every entry is a **fact** unless marked `hypothesis`; a hypothesis is a question to check, not a premise. Not built, so not here: library candidates, the area's twin patterns and conventions, and other open PRs. Construct what you need of those with the tools.

## The PR

- title: feat(Topology): Completely Regular Space iff Uniformizable
- description: (not recoverable at review start)
- changed files: Mathlib.lean, Mathlib/Data/Rel.lean, Mathlib/Topology/UniformSpace/Uniformizable.lean

## Objects

### `import in Mathlib.lean` (import, modified) [b3b7a9c285]
- file: `Mathlib.lean`; changed: imports:added

### `SetRel.IsRefl.comp` (instance, added) [698b29e8d3]
- file: `Mathlib/Data/Rel.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
instance IsRefl.comp [R₁.IsRefl] [R₂.IsRefl] : (R₁.comp R₂).IsRefl where
  refl _ := ⟨_, R₁.rfl, R₂.rfl⟩
```

### `CompletelyRegularSpace.of_exists_uniformSpace` (theorem, added) [0bd7cf834b]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
public theorem CompletelyRegularSpace.of_exists_uniformSpace
    (h : ∃ (u : UniformSpace α), u.toTopologicalSpace = t) :
    CompletelyRegularSpace α := by
  obtain ⟨u, rfl⟩ := h
  infer_instance
```

### `section in Uniformizable.lean` (command, added) [0db0d4cc4b]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
end UniformSpace
```

### `section in Uniformizable.lean` (command, added) [2c2bcdcecb]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [UniformSpace α]
```

### `section in Uniformizable.lean` (command, added) [67ed9d82ff]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
section UniformSpace
```

### `P` (def, added) [6eea1b41fe]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
def P (c : Set α) (u : Set α) :=
  ∃ (x : α) (uc uu s : SetRel α α),
    IsOpen uc ∧ uc.IsSymm ∧ uc ∈ 𝓤 α ∧ c = closure (Prod.mk x ⁻¹' uc) ∧
    IsOpen uu ∧ u = Prod.mk x ⁻¹' uu ∧ s ○ uc ○ s ⊆ uu ∧ s ∈ 𝓤 α
```

### `completelyRegularSpace_iff_exists_uniformSpace` (theorem, added) [7a58e3b315]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
public theorem completelyRegularSpace_iff_exists_uniformSpace :
    CompletelyRegularSpace α ↔ ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨@CompletelyRegularSpace.exists_uniformSpace α t, CompletelyRegularSpace.of_exists_uniformSpace⟩
```

### `UniformSpace.toCompletelyRegularSpace` (instance, added) [8aaf69a3c7]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- as the PR leaves it:
```lean
public instance UniformSpace.toCompletelyRegularSpace : CompletelyRegularSpace α where
  completely_regular x K hK hx := by
    obtain ⟨O, hOu, hOo, hbO⟩ := isOpen_iff_isOpen_ball_subset.mp hK.isOpen_compl x hx
    obtain ⟨C, hCu, hCc, hCO⟩ := mem_uniformity_isClosed hOu
    obtain ⟨(u3 : SetRel α α), hu3u, hu3C⟩ := comp3_mem_uniformity hCu
    obtain ⟨(ds : SetRel α α), hdsu, hdso, hdss, hdsd⟩ := comp_open_symm_mem_uniformity_sets hu3u
    have : u3.IsRefl := id_subset_iff.1 (refl_le_uniformity hu3u)
    have : ds.IsRefl := id_subset_iff.1 (refl_le_uniformity hdsu)
    replace hdsd : ds ⊆ u3 := left_subset_comp.trans hdsd
    have hxc : x ∈ closure (Prod.mk x ⁻¹' ds) := subset_closure (refl_mem_uniformity hdsu)
    have hyo : K ⊆ (Prod.mk x ⁻¹' O)ᶜ := subset_compl_comm.mpr hbO
    set c : Urysohns.CU P := {
      C := closure (Prod.mk x ⁻¹' ds)
      U := Prod.mk x ⁻¹' O
      closed_C := isClosed_closure
      open_U := hOo.preimage (Continuous.prodMk_right x)
      subset := (closure_minimal (Set.preimage_mono
        ((hdsd.trans left_subset_comp).trans hu3C))
          (hCc.preimage (.prodMk_right x))).trans (preimage_mono hCO)
      hP _ Pcu _ _ := urysohns_main Pcu
      P_C_U := ⟨x, ds, O, u3, hdso, hdss, hdsu, rfl, hOo, rfl,
        ((comp_assoc u3 ds u3).trans_le (comp_subset_comp_right
          (comp_subset_comp_left hdsd))).trans (hu3C.trans hCO), hu3u⟩
    }
    exact ⟨fun x => ⟨c.lim x, c.lim_mem_Icc x⟩, c.continuous_lim.subtype_mk c.lim_mem_Icc,
      Subtype.ext (c.lim_of_mem_C x hxc), fun y hy => Subtype.ext (c.lim_of_notMem_U y (hyo hy))⟩
```

### `section in Uniformizable.lean` (command, added) [8af6758e22]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable {α : Type*}
```

### `module_doc in Uniformizable.lean` (module_doc, added) [9e5688985d]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: documentation:added
- as the PR leaves it:
```lean
/-!
# Uniformizable Spaces

A topological space is uniformizable (there exists a uniformity that
generates the same topology) iff it is completely regular.

TODO: Explain proofs

## Main Results

* `UniformSpace.toCompletelyRegularSpace`: Uniform spaces are completely regular
* `CompletelyRegularSpace.exists_uniformSpace`: Completely regular spaces are uniformizable
* `CompletelyRegularSpace.of_exists_uniformSpace`: Uniformizable spaces are completely regular
* `completelyRegularSpace_iff_exists_uniformSpace`: A space is completely regular
  iff it is uniformizable

## Implementation Details

Urysohn's lemma is reused in the proof of `UniformSpace.completelyRegularSpace`.

## References

* <https://www.math.wm.edu/~vinroot/PadicGroups/519probset1.pdf>
-/
```

### `CompletelyRegularSpace.exists_uniformSpace` (theorem, added) [b2e5649b50]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: attributes:added, name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
public theorem CompletelyRegularSpace.exists_uniformSpace :
    ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨uniformSpaceOfCompactR1.comap stoneCechUnit, isInducing_stoneCechUnit.eq_induced.symm⟩
```

### `urysohns_main` (theorem, added) [b39d2d1f35]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: name:added, proof:added, statement_or_type:added
- as the PR leaves it:
```lean
theorem urysohns_main {c u : Set α} (Pcu : P c u) :
    ∃ (v : Set α), IsOpen v ∧ c ⊆ v ∧ closure v ⊆ u ∧ P c v ∧ P (closure v) u := by
  obtain ⟨x, uc, uu, s, huc, symmuc, ucu, rfl, huu, rfl, hn, hs⟩ := Pcu
  obtain ⟨(ds : SetRel α α), hdsu, hdso, hdss, hdsd⟩ := comp_open_symm_mem_uniformity_sets hs
  have ho : IsOpen (ds ○ uc ○ ds) := (hdso.relComp huc).relComp hdso
  use Prod.mk x ⁻¹' (ds ○ uc ○ ds), ho.preimage (Continuous.prodMk_right x)
  constructor
  · apply ((Continuous.prodMk_right x).closure_preimage_subset _).trans
    apply Set.preimage_mono
    rw [closure_eq_inter_uniformity, comp_assoc]
    exact iInter₂_subset ds hdsu
  constructor
  · apply ((Continuous.prodMk_right x).closure_preimage_subset _).trans
    apply Set.preimage_mono
    apply hn.trans'
    rw [closure_eq_inter_uniformity]
    apply iInter₂_subset_of_subset ds hdsu
    exact Eq.trans_subset (by simp_rw [comp_assoc])
      (comp_subset_comp (comp_subset_comp hdsd subset_rfl) hdsd)
  have : ds.IsRefl := id_subset_iff.1 (refl_le_uniformity hdsu)
  have hucd : ds ○ uc ○ ds ∈ 𝓤 α :=
    mem_of_superset ucu (right_subset_comp.trans left_subset_comp)
  constructor
  · exact ⟨x, uc, ds ○ uc ○ ds, ds, huc, symmuc, ucu, rfl, ho, rfl, subset_rfl, hdsu⟩
  · have hos : (ds ○ uc ○ ds).IsSymm := by
      rw [← inv_eq_self_iff, inv_comp, inv_comp, inv_eq_self, inv_eq_self, comp_assoc]
    refine ⟨x, (ds ○ uc ○ ds), uu, ds, ho, hos, hucd, rfl, huu, rfl, ?_, hdsu⟩
    calc ds ○ (ds ○ uc ○ ds) ○ ds
      _ = (ds ○ ds) ○ uc ○ (ds ○ ds) := by simp [comp_assoc]
      _ ⊆ s ○ uc ○ s := comp_subset_comp (comp_subset_comp hdsd subset_rfl) hdsd
      _ ⊆ uu := hn
```

### `section in Uniformizable.lean` (command, added) [ba33f79643]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
variable [t : TopologicalSpace α] [CompletelyRegularSpace α]
```

### `namespace in Uniformizable.lean` (command, added) [bb3a038443]
- file: `Mathlib/Topology/UniformSpace/Uniformizable.lean`; changed: namespace:added
- as the PR leaves it:
```lean
open Filter Set Uniformity SetRel
```

## Removed or renamed

- none

## Families (declarations that may be one decision)

- [exact] `CompletelyRegularSpace.exists_uniformSpace`, `CompletelyRegularSpace.of_exists_uniformSpace`, `completelyRegularSpace_iff_exists_uniformSpace` -- 3 declarations the change graph relates directly — a shared name family, or adjacency as changed siblings

## Relations between changed declarations

- changed_siblings [high]: `CompletelyRegularSpace.exists_uniformSpace` -> `CompletelyRegularSpace.of_exists_uniformSpace`
- changed_siblings [high]: `CompletelyRegularSpace.of_exists_uniformSpace` -> `completelyRegularSpace_iff_exists_uniformSpace`
- changed_siblings [high]: `CompletelyRegularSpace.of_exists_uniformSpace` -> `CompletelyRegularSpace.exists_uniformSpace`
- changed_siblings [high]: `completelyRegularSpace_iff_exists_uniformSpace` -> `CompletelyRegularSpace.of_exists_uniformSpace`
- declaration_dependency [exact]: `urysohns_main` -> `P`
- direct_use_of_changed_declaration [exact]: `UniformSpace.toCompletelyRegularSpace` -> `P`
- direct_use_of_changed_declaration [exact]: `UniformSpace.toCompletelyRegularSpace` -> `urysohns_main`
- direct_use_of_changed_declaration [exact]: `completelyRegularSpace_iff_exists_uniformSpace` -> `CompletelyRegularSpace.of_exists_uniformSpace`
- direct_use_of_changed_declaration [exact]: `completelyRegularSpace_iff_exists_uniformSpace` -> `CompletelyRegularSpace.exists_uniformSpace`
- name_family [high]: `CompletelyRegularSpace.exists_uniformSpace` -> `CompletelyRegularSpace.of_exists_uniformSpace`
- name_family [high]: `CompletelyRegularSpace.of_exists_uniformSpace` -> `CompletelyRegularSpace.exists_uniformSpace`
