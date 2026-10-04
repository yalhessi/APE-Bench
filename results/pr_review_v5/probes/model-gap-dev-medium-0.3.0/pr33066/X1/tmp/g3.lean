/-- Interpret an algebra equivalence as a continuous algebra equivalence when it and its inverse
are continuous. -/
def ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) : A ≃A[R] B :=
  { e with continuous_toFun := he, continuous_invFun := he' }

@[simp] theorem coe_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') : ⇑(ofAlgEquiv e he he') = e := rfl

@[simp] theorem toAlgEquiv_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') :
    (ofAlgEquiv e he he').toAlgEquiv = e := rfl

@[simp] theorem ofAlgEquiv_toAlgEquiv (e : A ≃A[R] B) :
    ofAlgEquiv e.toAlgEquiv e.continuous e.continuous_symm = e := rfl

@[simp] theorem symm_ofAlgEquiv (e : A ≃ₐ[R] B) (he he') :
    (ofAlgEquiv e he he').symm = ofAlgEquiv e.symm he' he := rfl

theorem ofAlgEquiv_trans_ofAlgEquiv (f : A ≃ₐ[R] B) (g : B ≃ₐ[R] C) (hf hf' hg hg') :
    (ofAlgEquiv f hf hf').trans (ofAlgEquiv g hg hg') =
      ofAlgEquiv (f.trans g) (hg.comp hf) (hf'.comp hg') := rfl

theorem isUniformEmbedding {E₁ E₂ : Type*} [UniformSpace E₁] [UniformSpace E₂] [Ring E₁]
    [IsUniformAddGroup E₁] [Algebra R E₁] [Ring E₂] [IsUniformAddGroup E₂] [Algebra R E₂]
    (e : E₁ ≃A[R] E₂) : IsUniformEmbedding e :=
  e.toAlgEquiv.isUniformEmbedding e.toContinuousAlgHom.uniformContinuous
    e.symm.toContinuousAlgHom.uniformContinuous

theorem _root_.AlgEquiv.isUniformEmbedding {E₁ E₂ : Type*} [UniformSpace E₁] [UniformSpace E₂]
    [Ring E₁] [IsUniformAddGroup E₁] [Algebra R E₁] [Ring E₂] [IsUniformAddGroup E₂] [Algebra R E₂]
    (e : E₁ ≃ₐ[R] E₂) (h₁ : Continuous e) (h₂ : Continuous e.symm) :
    IsUniformEmbedding e :=
  (ofAlgEquiv e h₁ h₂).isUniformEmbedding
