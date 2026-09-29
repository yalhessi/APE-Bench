import json
rep = "\nexample {β : Type*} : Membership β (Finset β) := Finset.instMembership\nexample := @Finset.instMembershipFinset\nexample := @Finset.instCoeSortFinsetType\nexample := @Finset.instSetLike\n"
print(json.dumps({"path":"Mathlib/Data/Finset/Defs.lean","line_start":105,"line_end":105,"replacement":rep}))
