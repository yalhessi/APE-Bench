import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-val-small12/pr36822/X1"
findings = [
 {
  "target": "Set.Ioi_disjoint_Iio_same",
  "claim": "The conversion to `to_dual` drops `@[simp]` from `Set.Ioi_disjoint_Iio_same`. Before the PR both it and its dual `Set.Iio_disjoint_Ioi_same` were `@[simp]`. The PR writes `@[to_dual Iio_disjoint_Ioi_same]` with no `(attr := simp)`, so after the PR neither lemma is a simp lemma. Every other lemma this PR converts from a `@[simp]` pair uses `to_dual (attr := simp)`. So this looks like an accidental regression in simp behaviour, not a deliberate change.",
  "requested_change": "Restore the simp attribute through `to_dual`: replace `@[to_dual Iio_disjoint_Ioi_same]` with `@[to_dual (attr := simp) Iio_disjoint_Ioi_same]` on `Set.Ioi_disjoint_Iio_same`, so that both it and the generated `Set.Iio_disjoint_Ioi_same` are `@[simp]` again.",
  "severity": "blocking",
  "evidence": "diff.patch: `-@[simp]` / `+@[to_dual Iio_disjoint_Ioi_same]` on `Ioi_disjoint_Iio_same`, and the removed `Iio_disjoint_Ioi_same` carried `@[simp]`. lean_verify_edit (line mode, PR state plus probe examples): `example : Disjoint (Ioi a) (Iio a) := by simp` and `example : Disjoint (Iio a) (Ioi a) := by simp` both fail with '`simp` made no progress'. So simp no longer closes these goals after the PR. lean_verify_edit with `@[to_dual (attr := simp) Iio_disjoint_Ioi_same]` (and the same fix on `Ioi_disjoint_Iio_iff`): the file compiles and the same `by simp` examples pass (success: true, no warnings). content_search over target/Mathlib: no explicit uses of either name outside this file. So nothing downstream names them directly, and any simp calls that relied on them fail silently."
 },
 {
  "target": "Set.Ioi_disjoint_Iio_iff",
  "claim": "The conversion to `to_dual` drops `@[simp]` from `Set.Ioi_disjoint_Iio_iff`. Before the PR both it and its dual `Set.Iio_disjoint_Ioi_iff` were `@[simp]`. The PR writes `@[to_dual Iio_disjoint_Ioi_iff]` with no `(attr := simp)`, so after the PR neither iff lemma is used by simp.",
  "requested_change": "Replace `@[to_dual Iio_disjoint_Ioi_iff]` with `@[to_dual (attr := simp) Iio_disjoint_Ioi_iff]` on `Set.Ioi_disjoint_Iio_iff`, so that both it and the generated `Set.Iio_disjoint_Ioi_iff` stay `@[simp]` as they were before the PR.",
  "severity": "blocking",
  "evidence": "diff.patch: `-@[simp]` / `+@[to_dual Iio_disjoint_Ioi_iff]` on `Ioi_disjoint_Iio_iff`, and the removed `Iio_disjoint_Ioi_iff` carried `@[simp]`. lean_verify_edit on the PR state: `example [DenselyOrdered α] : Disjoint (Ioi a) (Iio b) ↔ ¬a < b := by simp` and `example [DenselyOrdered α] : Disjoint (Iio a) (Ioi b) ↔ ¬b < a := by simp` both fail with '`simp` made no progress'. lean_verify_edit with `@[to_dual (attr := simp) Iio_disjoint_Ioi_iff]`: the file compiles and both examples pass (success: true). `#check @Set.Iio_disjoint_Ioi_iff` shows that the generated statement `Disjoint (Iio a) (Ioi b) ↔ ¬b < a` is exactly the removed one, so restoring the attribute restores the pre-PR API."
 }
]
json.dump(findings, open(f"{D}/findings.json","w"), ensure_ascii=False, indent=1)
json.load(open(f"{D}/findings.json"))
print(len(findings))
