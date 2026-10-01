import json
rep = ("set_option linter.style.longLine true\n\n/-!\n\n# Submonoid of inverses\n\n"
"Given a submonoid `N` of a monoid `M`, we define the submonoid `N.leftInv` as the submonoid of\n"
"left inverses of `N`. When `M` is commutative, we may define `fromCommLeftInv : N.leftInv →* N`\n"
"since the inverses are unique. When `N ≤ IsUnit.Submonoid M`, this is precisely\n"
"the pointwise inverse of `N`, and we may define `leftInvEquiv : S.leftInv ≃* S`.\n\n"
"For the pointwise inverse of submonoids of groups, please refer to the file\n"
"`Mathlib/Algebra/Group/Submonoid/Pointwise.lean`.\n\n"
"`N.leftInv` is distinct from `N.units`, which is the subgroup of `Mˣ` containing all units that are\n"
"in `N`. See the implementation notes of `Mathlib/Algebra/Group/Submonoid/Units.lean` for more\n"
"details on related constructions.\n\n"
"## TODO\n\n"
"Define the submonoid of right inverses and two-sided inverses.\n"
"See the comments of https://github.com/leanprover-community/mathlib4/pull/10679 for a possible\n"
"implementation.\n-/")
print(json.dumps({"path":"Mathlib/GroupTheory/Submonoid/Inverses.lean","line_start":10,"line_end":31,"replacement":rep}))
