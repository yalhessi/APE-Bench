import json
D = "/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/pipeline-overfit-review/results/pr_review_v5/probes/model-gap-val-small12/pr34935/X1"
findings = [
 {
  "target": "instance : IdemCommSemiring X.IdealSheafData (Mathlib/AlgebraicGeometry/IdealSheaf/Basic.lean)",
  "claim": "The `IdemCommSemiring X.IdealSheafData` instance leaves out the `npow` field. It therefore falls back to the default `npowRec`, which is not defeq to the `Pow X.IdealSheafData ℕ` instance the PR declares just above (`mkOfMemSupportIff (I.ideal ^ n) ...`). This is a non-defeq instance diamond: `Monoid.toNatPow` and `instPowNat` disagree, so no generic monoid power lemma (`pow_succ`, `pow_le_pow_left₀`, ...) applies to `I ^ n` as users will write it. The `npow_zero`/`npow_succ` proofs `by ext; rfl` pass only because they are about `npowRec`, which hides the gap.",
  "requested_change": "Set the power field of the instance to the PR's own `Pow`, and prove the two laws against it, e.g.\n  npow n I := I ^ n\n  npow_zero _ := by ext; simp [show (1 : X.IdealSheafData) = ⊤ from rfl]\n  npow_succ n I := IdealSheafData.ext (pow_succ I.ideal n)\n(or move `one_eq_top` above the instance and use it). Then `Monoid.npow n I` and `I ^ n` agree by `rfl`.",
  "severity": "blocking",
  "evidence": "lean_verify_edit on the PR file. (1) In the PR as it stands, a run_tac probe unfolding at instance transparency shows `Monoid.npow n I` reduces to `npowRec n I`, while `I ^ n` reduces to `mkOfMemSupportIff (I.ideal ^ n) ⋯ (if n = 0 then ∅ else I.supportSet) ⋯`, and `isDefEq` between them returns false. (2) Again in the PR as it stands, `example (n : ℕ) : I ^ (n + 1) = I ^ n * I := pow_succ I n` fails with a type mismatch between `@instHPow _ _ Monoid.toNatPow` and `@instHPow _ _ instPowNat`. `by rw [pow_succ]` fails with 'did not find ?a ^ (?n + 1)', and `pow_le_pow_left₀ bot_le le_rfl n` fails the same way. (3) With the replacement above spliced over lines 426-442, the whole file compiles (success = true, no warnings), and the same three examples (`pow_succ I n`, `rw [pow_succ]`, `pow_le_pow_left₀ ...`) now check. zulip_search: Junyan Xu (maintainer) describes exactly this failure mode, 'data field available in ancestor instances are not picked up in descendent instances, resulting in those fields being filled by npowRec etc. causing a diamond'. Mathlib's own `Nat` instance sets `npow m n := n ^ m` explicitly for this reason."
 },
 {
  "target": "AlgebraicGeometry.Scheme.IdealSheafData.mul_inf",
  "claim": "`mul_inf` states `I * (J ⊔ K) = I * J ⊔ I * K`, which is left distributivity over `⊔` (sup), not `⊓` (inf). The name says the opposite of the statement. The same statement for ideals is called `Ideal.mul_sup` (and `Submodule.mul_sup`), and the PR's own simp normal form is `⊔`.",
  "requested_change": "Rename `mul_inf` to `mul_sup` (matching `Ideal.mul_sup`), and update its use `left_distrib := mul_sup` in the `IdemCommSemiring` instance.",
  "severity": "blocking",
  "evidence": "Checked the statement against the diff. content_search in Mathlib/RingTheory/Ideal/Operations.lean finds `theorem mul_sup : I * (J ⊔ K) = I * J ⊔ I * K` (line 335), and Mathlib/Algebra/Algebra/Operations.lean has `Submodule.mul_sup : M * (N ⊔ P) = M * N ⊔ M * P`. lean_verify_edit replacing lines 423-442 with the renamed lemmas `mul_sup`/`sup_mul`, and the instance fields `left_distrib := mul_sup` and `right_distrib := sup_mul`: success = true, no warnings. naming_norm only measures the leading prefix (`mul_`), which is unchanged, so it does not bear on the `inf`/`sup` token."
 },
 {
  "target": "AlgebraicGeometry.Scheme.IdealSheafData.inf_mul",
  "claim": "`inf_mul` states `(I ⊔ J) * K = I * K ⊔ J * K`, which is right distributivity over `⊔` (sup), not `⊓` (inf). The name is wrong. The same statement for ideals is called `Ideal.sup_mul` (and `Submodule.sup_mul`).",
  "requested_change": "Rename `inf_mul` to `sup_mul` (matching `Ideal.sup_mul`), and update its use `right_distrib := sup_mul` in the `IdemCommSemiring` instance.",
  "severity": "blocking",
  "evidence": "content_search in Mathlib/RingTheory/Ideal/Operations.lean finds `theorem sup_mul : (I ⊔ J) * K = I * K ⊔ J * K` (line 338), and Mathlib/Algebra/Algebra/Operations.lean has `Submodule.sup_mul`. lean_verify_edit with the rename, and the instance updated, over lines 423-442: success = true."
 },
 {
  "target": "AlgebraicGeometry.Scheme.IdealSheafData.support_pow",
  "claim": "`support_pow (n : ℕ) (hn : n ≠ 0)` takes `n` explicitly, although `hn : n ≠ 0` already determines it. The analogous `PrimeSpectrum.zeroLocus_pow (I : Ideal R) {n : ℕ} (hn : n ≠ 0)` takes `n` implicitly.",
  "requested_change": "Make `n` implicit: `lemma support_pow {n : ℕ} (hn : n ≠ 0) : (I ^ n).support = I.support := by cases n <;> simp_all`.",
  "severity": "advisory",
  "evidence": "content_search in Mathlib/RingTheory/Spectrum/Prime/Basic.lean line 353 shows `theorem zeroLocus_pow (I : Ideal R) {n : ℕ} (hn : n ≠ 0)`. lean_verify_edit replacing `support_pow` with the implicit-binder version: success = true, no warnings, and the rest of the file still compiles."
 }
]
json.dump(findings, open(f"{D}/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(json.load(open(f"{D}/findings.json"))))
