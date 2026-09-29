import json
rep = """  ⟨@CompletelyRegularSpace.exists_uniformSpace α t, CompletelyRegularSpace.of_exists_uniformSpace⟩

example {β : Type*} [t' : TopologicalSpace β]
    (h : ∃ (u : UniformSpace β), u.toTopologicalSpace = t') :
    CompletelyRegularSpace β := CompletelyRegularSpace.of_exists_uniformSpace h

example {β : Type*} [t' : TopologicalSpace β] :
    CompletelyRegularSpace β ↔ ∃ (u : UniformSpace β), u.toTopologicalSpace = t' :=
  completelyRegularSpace_iff_exists_uniformSpace
"""
print(json.dumps({"path":"Mathlib/Topology/UniformSpace/Uniformizable.lean","line_start":125,"line_end":125,"replacement":rep}))
