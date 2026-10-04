import json,sys
nd = '''lemma equivRange_symm_apply (hinj : Injective f) (hclo : IsClosed (range f))
    (x : E) : (f.equivRange hinj hclo).symm ⟨f x, by simp⟩ = x :=
  (f.equivRange hinj hclo).symm_apply_apply x'''
print(json.dumps({"path": "Mathlib/Analysis/Normed/Operator/Banach.lean", "declaration_name": "ContinuousLinearMap.equivRange_symm_apply", "new_declaration": nd}))
