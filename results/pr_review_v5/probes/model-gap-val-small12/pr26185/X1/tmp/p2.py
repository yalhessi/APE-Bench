import json
nd = """theorem exists_peano_curve :
    ∃ f : C(I, I × I), Function.Surjective f :=
  let ⟨f, hf⟩ := exists_long_peano_curve
  ⟨f.restrict I, Set.surjOn_iff_surjective.mp (hf.mono cantorSet_subset_unitInterval subset_rfl)⟩"""
print(json.dumps({"path":"Counterexamples/PeanoCurve.lean","declaration_name":"exists_peano_curve","new_declaration":nd}))
