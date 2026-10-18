import json
F = "Mathlib/LinearAlgebra/RootSystem/BaseExists.lean"
spec = [("drop open Function", {"path":F,"line_start":44,"line_end":44,"replacement":"open IsAddIndecomposable Module Set Submodule"}),
        ("public section without expose", {"path":F,"line_start":42,"line_end":42,"replacement":"public section"}),
        ("posForm golf simp", {"path":"Mathlib/LinearAlgebra/RootSystem/RootPositive.lean","declaration_name":"RootPairing.RootPositiveForm.posForm_apply_root_root_le_zero_iff","new_declaration":"@[simp]\nlemma posForm_apply_root_root_le_zero_iff [IsStrictOrderedRing S]\n    (hi : P.root i ∈ span S (range P.root) := subset_span (mem_range_self i))\n    (hj : P.root j ∈ span S (range P.root) := subset_span (mem_range_self j)) :\n    B.posForm ⟨P.root i, hi⟩ ⟨P.root j, hj⟩ ≤ 0 ↔ P.pairingIn S i j ≤ 0 := by\n  simp [← not_lt]"}),
]
json.dump(spec, open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33321/TA1/tmp/be6.json","w"))
