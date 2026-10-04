import json,re
lines=open("tmp/orig.lean").read().split("\n")
block="\n".join(lines[44:107])  # lines 45..107
block=block.replace("def P (c : Set α) (u : Set α) :=", """/-- Auxiliary predicate for the Urysohn construction in `UniformSpace.toCompletelyRegularSpace`:
`c` is the closure of the ball `Prod.mk x ⁻¹' uc` for an open symmetric entourage `uc`, and `u` is
an open ball `Prod.mk x ⁻¹' uu` around the same point that contains the `s`-thickening
`s ○ uc ○ s` for some entourage `s`. -/
private def IsUrysohnBallPair (c u : Set α) : Prop :=""")
block=block.replace("theorem urysohns_main {c u : Set α} (Pcu : P c u) :\n    ∃ (v : Set α), IsOpen v ∧ c ⊆ v ∧ closure v ⊆ u ∧ P c v ∧ P (closure v) u",
 "private theorem IsUrysohnBallPair.exists_between {c u : Set α} (Pcu : IsUrysohnBallPair c u) :\n    ∃ (v : Set α), IsOpen v ∧ c ⊆ v ∧ closure v ⊆ u ∧ IsUrysohnBallPair c v ∧\n      IsUrysohnBallPair (closure v) u")
block=block.replace("Urysohns.CU P", "Urysohns.CU IsUrysohnBallPair").replace("urysohns_main Pcu","Pcu.exists_between")
assert "P c" not in block
print(json.dumps({"path":"Mathlib/Topology/UniformSpace/Uniformizable.lean","line_start":45,"line_end":107,"replacement":block}))
open("tmp/renamed_block.lean","w").write(block)
