/-- Interpret an algebra equivalence as a continuous algebra equivalence when it is continuous. -/
def ofAlgEquiv (e : A ≃ₐ[R] B) (he : Continuous e) (he' : Continuous e.symm) : A ≃A[R] B :=
  { e with continuous_toFun := he, continuous_invFun := he' }

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
