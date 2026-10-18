import json, re
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp"
c = json.load(open(D + "/ind_full.json"))["content"]
lines = {}
for l in c.split("\n"):
    m = re.match(r"\s*(\d+)\|(.*)$", l)
    if m: lines[int(m.group(1))] = m.group(2)
L = lambda a, b: "\n".join(lines[i] for i in range(a, b + 1))
F = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
sub_new = """@[to_additive]
lemma Subgroup.closure_image_isMulIndecomposable_baseOf [Finite ι] [InvolutiveInv ι]
    [CommGroup S] [IsOrderedMonoid S]
    (v : ι → G) (hv_inv : ∀ i, v i⁻¹ = (v i)⁻¹)
    (f : G →* S) (hf : ∀ i, f (v i) ≠ 1) :
    closure (v '' IsMulIndecomposable.baseOf v f) = closure (range v) := by
  refine le_antisymm (closure_mono (image_subset_range _ _)) ((closure_le _).mpr ?_)
  rintro - ⟨i, rfl⟩
  rcases IsMulIndecomposable.mem_or_inv_mem_closure_baseOf v hv_inv f hf i with h | h
  · exact le_closure_toSubmonoid _ h
  · exact inv_mem_iff.mp (le_closure_toSubmonoid _ h)"""
# drop image_baseOf_inv_comp_eq (57-78), keep Submonoid docstring+lemma (79-114), drop old Subgroup (115-137), keep namespace block (138-190)
tail = L(79, 114) + "\n" + L(138, 190) + "\n\n" + sub_new
spec = [("Subgroup via mem_or_inv; drop image_baseOf_inv_comp_eq", {"path":F, "line_start":57, "line_end":190, "replacement":tail})]
json.dump(spec, open(D + "/ind4.json", "w"))
print(tail[-1500:])
