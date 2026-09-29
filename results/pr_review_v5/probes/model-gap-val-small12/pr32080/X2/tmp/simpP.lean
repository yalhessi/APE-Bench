def P (c : Set α) (u : Set α) :=
  ∃ (x : α) (uc uu s : SetRel α α),
    IsOpen uc ∧ c = closure (Prod.mk x ⁻¹' uc) ∧
    u = Prod.mk x ⁻¹' uu ∧ s ○ uc ○ s ⊆ uu ∧ s ∈ 𝓤 α

theorem urysohns_main {c u : Set α} (Pcu : P c u) :
    ∃ (v : Set α), IsOpen v ∧ c ⊆ v ∧ closure v ⊆ u ∧ P c v ∧ P (closure v) u := by
  obtain ⟨x, uc, uu, s, huc, rfl, rfl, hn, hs⟩ := Pcu
  obtain ⟨(ds : SetRel α α), hdsu, hdso, -, hdsd⟩ := comp_open_symm_mem_uniformity_sets hs
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
  constructor
  · exact ⟨x, uc, ds ○ uc ○ ds, ds, huc, rfl, rfl, subset_rfl, hdsu⟩
  · refine ⟨x, (ds ○ uc ○ ds), uu, ds, ho, rfl, rfl, ?_, hdsu⟩
    calc ds ○ (ds ○ uc ○ ds) ○ ds
      _ = (ds ○ ds) ○ uc ○ (ds ○ ds) := by simp [comp_assoc]
      _ ⊆ s ○ uc ○ s := comp_subset_comp (comp_subset_comp hdsd subset_rfl) hdsd
      _ ⊆ uu := hn

public instance UniformSpace.toCompletelyRegularSpace : CompletelyRegularSpace α where
  completely_regular x K hK hx := by
    obtain ⟨O, hOu, hOo, hbO⟩ := isOpen_iff_isOpen_ball_subset.mp hK.isOpen_compl x hx
    obtain ⟨C, hCu, hCc, hCO⟩ := mem_uniformity_isClosed hOu
    obtain ⟨(u3 : SetRel α α), hu3u, hu3C⟩ := comp3_mem_uniformity hCu
    obtain ⟨(ds : SetRel α α), hdsu, hdso, -, hdsd⟩ := comp_open_symm_mem_uniformity_sets hu3u
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
      P_C_U := ⟨x, ds, O, u3, hdso, rfl, rfl,
        ((comp_assoc u3 ds u3).trans_le (comp_subset_comp_right
          (comp_subset_comp_left hdsd))).trans (hu3C.trans hCO), hu3u⟩
    }
    exact ⟨fun x => ⟨c.lim x, c.lim_mem_Icc x⟩, c.continuous_lim.subtype_mk c.lim_mem_Icc,
      Subtype.ext (c.lim_of_mem_C x hxc), fun y hy => Subtype.ext (c.lim_of_notMem_U y (hyo hy))⟩
