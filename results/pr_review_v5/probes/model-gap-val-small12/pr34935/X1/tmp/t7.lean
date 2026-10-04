/-- Over affine schemes, ideal sheaves are in bijection with ideals of the global sections. -/
@[simps! apply symm_apply]
def equivOfIsAffine [IsAffine X] : IdealSheafData X ≃+*o Ideal Γ(X, ⊤) where
  toFun := (ideal · ⟨⊤, isAffineOpen_top X⟩)
  invFun := ofIdealTop
  left_inv I := ext_of_isAffine (by simp)
  right_inv I := by simp
  map_mul' := by simp
  map_add' := by simp
  map_le_map_iff' := ⟨le_of_isAffine, (· _)⟩

example [IsAffine X] (I : IdealSheafData X) :
    equivOfIsAffine I = I.ideal ⟨⊤, isAffineOpen_top X⟩ := by simp only [equivOfIsAffine_apply]
example [IsAffine X] (I : Ideal Γ(X, ⊤)) :
    equivOfIsAffine.symm I = ofIdealTop I := by simp only [equivOfIsAffine_symm_apply]
example : False := by
  have := @equivOfIsAffine_apply
  have := @equivOfIsAffine_symm_apply
  done
