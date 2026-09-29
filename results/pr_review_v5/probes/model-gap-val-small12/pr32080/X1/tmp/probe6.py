import json
decl = """public instance (priority := 100) UniformSpace.toCompletelyRegularSpace :
    CompletelyRegularSpace α where
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
    let c : Urysohns.CU P := {
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
    exact ⟨fun z ↦ ⟨c.lim z, c.lim_mem_Icc z⟩, c.continuous_lim.subtype_mk c.lim_mem_Icc,
      Subtype.ext (c.lim_of_mem_C x hxc), fun y hy ↦ Subtype.ext (c.lim_of_notMem_U y (hyo hy))⟩"""
print(json.dumps({"path":"Mathlib/Topology/UniformSpace/Uniformizable.lean","declaration_name":"UniformSpace.toCompletelyRegularSpace","new_declaration":decl}))
