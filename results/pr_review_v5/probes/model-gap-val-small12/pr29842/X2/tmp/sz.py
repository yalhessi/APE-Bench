import json
new = r'''@[deprecated (since := "2025-04-27")] alias tangentCone_inter_nhds := tangentConeAt_inter_nhds

theorem tangentConeAt_subset_zero_tvs_probe [T2Space E] (hx : ¬AccPt x (𝓟 s)) :
    tangentConeAt 𝕜 s x ⊆ 0 := by
  rintro y ⟨c, d, hds, hc, hcd⟩
  suffices ∀ᶠ n in .atTop, d n = 0 from
    tendsto_nhds_unique hcd <| tendsto_const_nhds.congr' <| this.mono fun n hn ↦ by simp [hn]
  simp only [accPt_iff_frequently, not_frequently, not_and', ne_eq, not_not] at hx
  have : Tendsto (x + d ·) atTop (𝓝 x) := by
    simpa using tendsto_const_nhds.add (tangentConeAt.lim_zero _ hc hcd)
  filter_upwards [this.eventually hx, hds] with n h₁ h₂
  simpa using h₁ h₂

end TVS'''
print(json.dumps({"path": "Mathlib/Analysis/Calculus/TangentCone.lean", "line_start": 145, "line_end": 147, "replacement": new}))
