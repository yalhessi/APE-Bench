-- see Note [lower instance priority]
/- TODO: Remove instance when we have `StarOrderedRing (V →L[𝕜] V)` since
this then becomes an instance from `StarRingEquivClass.instOrderIsoClass`. -/
public instance (priority := 100) ContinuousLinearMap.instOrderIsoClass {F : Type*}
    [EquivLike F (V →L[𝕜] V) (W →L[𝕜] W)]
    [NonUnitalAlgEquivClass F 𝕜 _ _] [StarHomClass F _ _] [ContinuousMapClass F _ _] :
    OrderIsoClass F _ _ where
  map_le_map_iff f x y := by
    obtain ⟨U, hU⟩ := StarAlgEquiv.eq_linearIsometryEquivConjStarAlgEquiv
      (StarAlgEquivClass.toStarAlgEquiv f : _ ≃⋆ₐ[𝕜] _) (map_continuous f)
    have this a : f a = U.conjStarAlgEquiv a := by simpa using congr($hU a)
    simp_rw [le_def, ← _root_.map_sub, ← isPositive_toLinearMap_iff, this]
    exact LinearMap.isPositive_linearIsometryEquiv_conj_iff U
