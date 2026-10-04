variable [t : TopologicalSpace α]

public theorem CompletelyRegularSpace.exists_uniformSpace [CompletelyRegularSpace α] :
    ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨uniformSpaceOfCompactR1.comap stoneCechUnit, isInducing_stoneCechUnit.eq_induced.symm⟩

public theorem CompletelyRegularSpace.of_exists_uniformSpace
    (h : ∃ (u : UniformSpace α), u.toTopologicalSpace = t) :
    CompletelyRegularSpace α := by
  obtain ⟨u, rfl⟩ := h
  infer_instance

public theorem completelyRegularSpace_iff_exists_uniformSpace :
    CompletelyRegularSpace α ↔ ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨fun _ ↦ CompletelyRegularSpace.exists_uniformSpace, .of_exists_uniformSpace⟩

#check @CompletelyRegularSpace.of_exists_uniformSpace
#check @completelyRegularSpace_iff_exists_uniformSpace
