/-- The continuous algebra equivalence given by an algebra equivalence `e` such that `e` and
`e.symm` are continuous. -/
def ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) : A ≃A[R] B where
  toAlgEquiv := e
  continuous_toFun := he
  continuous_invFun := he'

@[simp] lemma coe_ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) :
    ⇑(ofAlgEquiv e he he') = e := rfl

@[simp] lemma toAlgEquiv_ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e)
    (he' : Continuous e.symm) : (ofAlgEquiv e he he').toAlgEquiv = e := rfl

@[simp] lemma ofAlgEquiv_toAlgEquiv (e : A ≃A[R] B) :
    ofAlgEquiv e.toAlgEquiv e.continuous e.continuous_symm = e := rfl

@[simp] lemma symm_ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) :
    (ofAlgEquiv e he he').symm = ofAlgEquiv e.symm he' he := rfl

@[simp] lemma ofAlgEquiv_trans_ofAlgEquiv (f : A ≃ₐ[R] B) (g : B ≃ₐ[R] C) (hf : Continuous f)
    (hf' : Continuous f.symm) (hg : Continuous g) (hg' : Continuous g.symm) :
    (ofAlgEquiv f hf hf').trans (ofAlgEquiv g hg hg') =
      ofAlgEquiv (f.trans g) (hg.comp hf) (hf'.comp hg') := rfl

theorem _root_.AlgEquiv.isUniformEmbedding {E₁ E₂ : Type*} [UniformSpace E₁] [UniformSpace E₂]
    [Ring E₁] [IsUniformAddGroup E₁] [Algebra R E₁] [Ring E₂] [IsUniformAddGroup E₂] [Algebra R E₂]
    (e : E₁ ≃ₐ[R] E₂) (h₁ : Continuous e) (h₂ : Continuous e.symm) :
    IsUniformEmbedding e :=
  (ofAlgEquiv e h₁ h₂).isUniformEmbedding
