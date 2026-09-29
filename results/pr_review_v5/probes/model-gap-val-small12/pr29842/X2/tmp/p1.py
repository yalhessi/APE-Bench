import json
code = r'''  have : ∀ᶠ n in l, (c n)⁻¹ • c n • d n = d n :=
    (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn ↦ inv_smul_smul₀ hn (d n)
  apply Tendsto.congr' this
  rw [tendsto_norm_atTop_iff_cobounded] at hc
  simpa using (tendsto_inv₀_cobounded.comp hc).smul hd'''
print(json.dumps({"code": code, "limit": 8}))
