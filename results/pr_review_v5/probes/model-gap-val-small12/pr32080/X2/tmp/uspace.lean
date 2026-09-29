variable [t : TopologicalSpace α]

#check @UniformSpace.replaceTopology
#check @UniformSpace.comap

/-- A uniform structure inducing the topology of a completely regular space: the one pulled back
from the unique uniformity of its Stone-Čech compactification. -/
@[expose] public noncomputable def CompletelyRegularSpace.uniformSpace [CompletelyRegularSpace α] :
    UniformSpace α :=
  (uniformSpaceOfCompactR1.comap stoneCechUnit).replaceTopology
    isInducing_stoneCechUnit.eq_induced

public theorem CompletelyRegularSpace.uniformSpace_toTopologicalSpace [CompletelyRegularSpace α] :
    (CompletelyRegularSpace.uniformSpace (α := α)).toTopologicalSpace = t := rfl

public theorem CompletelyRegularSpace.exists_uniformSpace [CompletelyRegularSpace α] :
    ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨CompletelyRegularSpace.uniformSpace, rfl⟩

public theorem CompletelyRegularSpace.of_exists_uniformSpace
    (h : ∃ (u : UniformSpace α), u.toTopologicalSpace = t) :
    CompletelyRegularSpace α := by
  obtain ⟨u, rfl⟩ := h
  infer_instance

public theorem completelyRegularSpace_iff_exists_uniformSpace :
    CompletelyRegularSpace α ↔ ∃ (u : UniformSpace α), u.toTopologicalSpace = t :=
  ⟨fun _ ↦ CompletelyRegularSpace.exists_uniformSpace, .of_exists_uniformSpace⟩
