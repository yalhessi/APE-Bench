import json, sys
which = sys.argv[1]
lines = {"union": "public import Mathlib.Algebra.Module.Submodule.Union", "orzech": "public import Mathlib.LinearAlgebra.Dimension.OrzechProperty"}
start = {"union": 9, "orzech": 10}[which]
print(json.dumps({"path":"Mathlib/LinearAlgebra/RootSystem/BaseExists.lean","line_start":start,"line_end":start,"replacement":""}))
