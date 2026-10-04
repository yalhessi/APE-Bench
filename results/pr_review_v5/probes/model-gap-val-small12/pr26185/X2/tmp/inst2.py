import json
nd = r'''/-- **Tietze extension theorem** for maps into a nonempty interval of `ℝ`: every nonempty
`OrdConnected` subset of `ℝ` is a `TietzeExtension` space. -/
instance Set.OrdConnected.instTietzeExtension {t : Set ℝ} [t.OrdConnected] [Nonempty t] :
    TietzeExtension t where
  exists_restrict_eq' s hs f := by
    obtain ⟨g, hg, hgf⟩ := (ContinuousMap.comp ⟨Subtype.val, continuous_subtype_val⟩ f)
      |>.exists_restrict_eq_forall_mem_of_closed
      (fun x ↦ (f x).2) (Set.nonempty_coe_sort.mp ‹_›) hs
    exact ⟨⟨_, (map_continuous g).codRestrict hg⟩, by ext x; exact congr($hgf x)⟩

example : TietzeExtension unitInterval := inferInstance'''
print(json.dumps({"path":"Mathlib/Analysis/Complex/Tietze.lean","declaration_name":"unitInterval.instTietzeExtension","new_declaration":nd}))
