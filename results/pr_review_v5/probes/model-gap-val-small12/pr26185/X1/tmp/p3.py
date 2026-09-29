import json
rep = """
/-- A nonempty order-connected subset of `ℝ` (e.g. an interval) is a `TietzeExtension` space. -/
instance Set.OrdConnected.instTietzeExtension {t : Set ℝ} [t.OrdConnected] [Nonempty t] :
    TietzeExtension t where
  exists_restrict_eq' s hs f := by
    obtain ⟨g, hgt, hgf⟩ := (ContinuousMap.mk (Subtype.val ∘ f) (by fun_prop))
      |>.exists_restrict_eq_forall_mem_of_closed (fun x ↦ (f x).2) (nonempty_coe_sort.mp ‹_›) hs
    exact ⟨⟨fun x ↦ ⟨g x, hgt x⟩, by fun_prop⟩, by ext x; exact congr($hgf x)⟩
"""
print(json.dumps({"path":"Mathlib/Topology/TietzeExtension.lean","line_start":514,"line_end":514,"replacement":rep}))
