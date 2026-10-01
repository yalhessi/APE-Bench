@[simp]
lemma equivRange_symm_apply (hinj : Injective f) (hclo : IsClosed (range f))
    (x : E) : (f.equivRange hinj hclo).symm ⟨f x, by simp⟩ = x :=
  (f.equivRange hinj hclo).symm_apply_eq.mpr rfl
