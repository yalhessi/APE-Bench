variable {H : Type*} [NormedAddCommGroup H] [InnerProductSpace 𝕜 H] [CompleteSpace H]

section linearIsometryEquiv
variable {K : Type*} [NormedAddCommGroup K] [InnerProductSpace 𝕜 K] [CompleteSpace K]

namespace ContinuousLinearMap

theorem inner_map_map_iff_adjoint_comp_self (u : H →L[𝕜] K) :
    (∀ x y : H, ⟪u x, u y⟫_𝕜 = ⟪x, y⟫_𝕜) ↔ adjoint u ∘L u = 1 := by
  refine ⟨fun h ↦ ext fun x ↦ ?_, fun h ↦ ?_⟩
  · refine ext_inner_right 𝕜 fun y ↦ ?_
    simpa [star_eq_adjoint, adjoint_inner_left] using h x y
  · simp [← adjoint_inner_left, ← comp_apply, h]

theorem norm_map_iff_adjoint_comp_self (u : H →L[𝕜] K) :
    (∀ x : H, ‖u x‖ = ‖x‖) ↔ adjoint u ∘L u = 1 := by
  rw [LinearMap.norm_map_iff_inner_map_map u, u.inner_map_map_iff_adjoint_comp_self]

@[simp]
lemma _root_.LinearIsometryEquiv.adjoint_eq_symm (e : H ≃ₗᵢ[𝕜] K) :
    adjoint (e : H →L[𝕜] K) = e.symm :=
  calc
    _ = adjoint (e : H →L[𝕜] K) ∘L e ∘L (e.symm : K →L[𝕜] H) := by simp
    _ = e.symm := by
      rw [← comp_assoc, norm_map_iff_adjoint_comp_self _ |>.mp e.norm_map, one_def, id_comp]

@[simp]
lemma _root_.LinearIsometryEquiv.star_eq_symm (e : H ≃ₗᵢ[𝕜] H) :
    star (e : H →L[𝕜] H) = e.symm :=
  e.adjoint_eq_symm

theorem norm_map_of_mem_unitary {u : H →L[𝕜] H} (hu : u ∈ unitary (H →L[𝕜] H)) (x : H) :
    ‖u x‖ = ‖x‖ :=
  -- Elaborates faster with this broken out https://github.com/leanprover-community/mathlib4/issues/11299
  have := Unitary.star_mul_self_of_mem hu
  u.norm_map_iff_adjoint_comp_self.mpr this x

theorem inner_map_map_of_mem_unitary {u : H →L[𝕜] H} (hu : u ∈ unitary (H →L[𝕜] H)) (x y : H) :
    ⟪u x, u y⟫_𝕜 = ⟪x, y⟫_𝕜 :=
  -- Elaborates faster with this broken out https://github.com/leanprover-community/mathlib4/issues/11299
  have := Unitary.star_mul_self_of_mem hu
  u.inner_map_map_iff_adjoint_comp_self.mpr this x y

end ContinuousLinearMap

namespace LinearIsometryEquiv

open ContinuousLinearMap ContinuousLinearEquiv in
/-- An isometry linear equivalence of two Hilbert spaces induces an equivalence of
⋆-algebras of their endomorphisms. -/
def conjStarAlgEquiv (e : H ≃ₗᵢ[𝕜] K) : (H →L[𝕜] H) ≃⋆ₐ[𝕜] (K →L[𝕜] K) :=
  .ofAlgEquiv e.toContinuousLinearEquiv.conjContinuousAlgEquiv fun x ↦ by
    simp [star_eq_adjoint, conjContinuousAlgEquiv_apply, ← toContinuousLinearEquiv_symm, comp_assoc]

@[simp] lemma conjStarAlgEquiv_apply_apply (e : H ≃ₗᵢ[𝕜] K) (x : H →L[𝕜] H) (y : K) :
    e.conjStarAlgEquiv x y = e (x (e.symm y)) := rfl

theorem symm_conjStarAlgEquiv_apply_apply (e : H ≃ₗᵢ[𝕜] K) (f : K →L[𝕜] K) (x : H) :
    e.conjStarAlgEquiv.symm f x = e.symm (f (e x)) := rfl

lemma conjStarAlgEquiv_apply (e : H ≃ₗᵢ[𝕜] K) (x : H →L[𝕜] H) :
    e.conjStarAlgEquiv x = e ∘L x ∘L e.symm := rfl

@[simp] lemma symm_conjStarAlgEquiv (e : H ≃ₗᵢ[𝕜] K) :
    e.conjStarAlgEquiv.symm = e.symm.conjStarAlgEquiv := rfl

@[simp] theorem conjStarAlgEquiv_refl : conjStarAlgEquiv (.refl 𝕜 H) = .refl := rfl

theorem conjStarAlgEquiv_trans {G : Type*} [NormedAddCommGroup G] [InnerProductSpace 𝕜 G]
    [CompleteSpace G] (e : H ≃ₗᵢ[𝕜] K) (f : K ≃ₗᵢ[𝕜] G) :
    (e.trans f).conjStarAlgEquiv = e.conjStarAlgEquiv.trans f.conjStarAlgEquiv := rfl

end LinearIsometryEquiv
end linearIsometryEquiv