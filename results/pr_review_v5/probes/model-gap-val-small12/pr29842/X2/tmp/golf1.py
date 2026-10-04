import json
decl = r'''theorem tangentConeAt.lim_zero {α : Type*} (l : Filter α) {c : α → 𝕜} {d : α → E}
    (hc : Tendsto (fun n => ‖c n‖) l atTop) (hd : Tendsto (fun n => c n • d n) l (𝓝 y)) :
    Tendsto d l (𝓝 0) := by
  have : ∀ᶠ n in l, (c n)⁻¹ • c n • d n = d n :=
    (eventually_ne_of_tendsto_norm_atTop hc 0).mono fun n hn ↦ inv_smul_smul₀ hn (d n)
  simpa using ((tendsto_inv₀_cobounded.comp (tendsto_norm_atTop_iff_cobounded.1 hc)).smul
    hd).congr' this'''
print(json.dumps({"path": "Mathlib/Analysis/Calculus/TangentCone.lean", "declaration_name": "tangentConeAt.lim_zero", "new_declaration": decl}))
