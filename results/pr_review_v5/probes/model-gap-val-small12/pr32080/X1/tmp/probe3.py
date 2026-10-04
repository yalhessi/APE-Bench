import json
rep = """  ⟨@CompletelyRegularSpace.exists_uniformSpace α t, CompletelyRegularSpace.of_exists_uniformSpace⟩

example {β : Type*} [UniformSpace β] [T0Space β] : T35Space β := inferInstance
"""
print(json.dumps({"path":"Mathlib/Topology/UniformSpace/Uniformizable.lean","line_start":125,"line_end":125,"replacement":rep}))
