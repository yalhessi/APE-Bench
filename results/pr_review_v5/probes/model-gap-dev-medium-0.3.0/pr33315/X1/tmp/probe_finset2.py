import json
rep = "\nexample := @Finset.instSetLike\nexample {β : Type*} (s : Finset β) : Type _ := s\nexample := @Finset.instCoeSortFinsetType\n"
print(json.dumps({"path":"Mathlib/Data/Finset/Defs.lean","line_start":130,"line_end":130,"replacement":rep}))
