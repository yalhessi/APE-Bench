import json
rep = """public instance (priority := 100) UniformSpace.toT35Space [T0Space α] : T35Space α where

end UniformSpace

example {β : Type*} [UniformSpace β] [T0Space β] : T35Space β := inferInstance
"""
print(json.dumps({"path":"Mathlib/Topology/UniformSpace/Uniformizable.lean","line_start":109,"line_end":109,"replacement":rep}))
