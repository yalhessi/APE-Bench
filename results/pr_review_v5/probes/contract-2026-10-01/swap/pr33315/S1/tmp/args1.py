import json
rep = """abbrev toSet (s : Finset α) : Set α := s

example : Membership α (Finset α) := Finset.instMembership
example : SetLike (Finset α) α := Finset.instSetLike
example (s : Finset α) : Type _ := s
#synth CoeSort (Finset α) (Type _)"""
print(json.dumps({"path": "Mathlib/Data/Finset/Defs.lean", "line_start": 133, "line_end": 133, "replacement": rep}))
