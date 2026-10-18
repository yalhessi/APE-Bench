import json, sys
D = sys.argv[1]
findings = [
 {
  "target": "Ordinal.mem_range_deriv",
  "claim": "The PR renames `Ordinal.IsNormal.mem_range_deriv` to `Ordinal.mem_range_deriv` but adds no deprecated alias for the old name. Every other renamed `IsNormal.*` lemma in FixedPoint.lean (`apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv`, `fp_iff_deriv`) gets one, so downstream code that uses `IsNormal.mem_range_deriv` / `H.mem_range_deriv` breaks without a deprecation cycle.",
  "requested_change": "Add `@[deprecated (since := \"2025-12-25\")] alias IsNormal.mem_range_deriv := mem_range_deriv` directly after `theorem mem_range_deriv` in Mathlib/SetTheory/Ordinal/FixedPoint.lean.",
  "severity": "blocking",
  "evidence": "declaration_search `Ordinal.IsNormal.mem_range_deriv` gives 'declared in Mathlib/SetTheory/Ordinal/FixedPoint.lean:360 (before this PR)' and no declaration in the PR's files. content_search for `mem_range_deriv\\b` over target/Mathlib finds only the new theorem (FixedPoint.lean:375), two deprecation attributes that point at it, and two call sites, with no `alias IsNormal.mem_range_deriv`. The diff shows `-theorem IsNormal.mem_range_deriv ...` removed with no replacement alias. lean_verify_edit on FixedPoint.lean lines 361-383, with the alias added (and the other fixes below), returned outcome `compiled` with no errors and no warnings."
 },
 {
  "target": "Mathlib/SetTheory/Ordinal/FixedPoint.lean",
  "claim": "Four of the new deprecations in this file carry `since := \"2025-10-25\"`: `IsNormal.deriv_fp`, `IsNormal.le_iff_deriv`, the new `fp_iff_deriv` and `IsNormal.fp_iff_deriv`. Every other deprecation this PR adds, including the sibling `IsNormal.apply_lt_nfp`/`nfp_le_apply`/`nfp_fp`/`apply_le_nfp` in the same file, uses `2025-12-25`. The October date looks copied from the pre-existing `deriv_id_of_nfp_id` alias, and it predates the PR, so these aliases would become eligible for deletion two months early.",
  "requested_change": "Change `since := \"2025-10-25\"` to `since := \"2025-12-25\"` on the deprecations of `IsNormal.deriv_fp`, `IsNormal.le_iff_deriv`, `fp_iff_deriv` and `IsNormal.fp_iff_deriv`. Leave the pre-existing `deriv_id_of_nfp_id` alias unchanged.",
  "severity": "blocking",
  "evidence": "content_search on target/Mathlib/SetTheory/Ordinal/FixedPoint.lean: lines 296, 302, 311 and 317 carry `2025-12-25`, while lines 364, 372, 378 and 382 (the new deprecations) carry `2025-10-25`. Line 358 (`deriv_id_of_nfp_id`, unchanged by the PR) also carries `2025-10-25`. zulip_search results are capped 'as_of 2025-12-26', which places the PR's push at about 2025-12-25. lean_verify_edit of the corrected block (lines 361-383) returned `compiled`, with no errors or warnings."
 },
 {
  "target": "Ordinal.fp_iff_deriv",
  "claim": "`Ordinal.fp_iff_deriv` is a new declaration (only `Ordinal.IsNormal.fp_iff_deriv` existed before), yet it is deprecated at birth. Its only role is to give the deprecated alias `IsNormal.fp_iff_deriv` something to point at. That adds a name to the library that never needed to exist.",
  "requested_change": "Delete `theorem fp_iff_deriv` and its alias. Make the old name the deprecated theorem: `@[deprecated Ordinal.mem_range_deriv (since := \"2025-12-25\")] theorem IsNormal.fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a := (Ordinal.mem_range_deriv H).symm`. The qualified `Ordinal.mem_range_deriv` is needed because inside `IsNormal.*` the bare name resolves to the deprecated `IsNormal.mem_range_deriv`.",
  "severity": "advisory",
  "evidence": "declaration_search shows only `Ordinal.IsNormal.fp_iff_deriv` existed in the base. model.md lists `Ordinal.fp_iff_deriv` as (theorem, added) with `@[deprecated mem_range_deriv (since := \"2025-10-25\")]`. lean_verify_edit replacing FixedPoint.lean lines 361-383 with the block that has the deprecated theorem `IsNormal.fp_iff_deriv` (and no `Ordinal.fp_iff_deriv`): first try with the bare `mem_range_deriv` warned '`Ordinal.IsNormal.mem_range_deriv` has been deprecated', and with `Ordinal.mem_range_deriv` it `compiled` with no errors and no warnings."
 },
 {
  "target": "Ordinal.IsNormal.monotone",
  "claim": "The deprecated `Ordinal.IsNormal.monotone` points users to `Order.IsNormal.strictMono`, but this same PR adds `Order.IsNormal.monotone` (Mathlib/Order/IsNormal.lean), which is the exact replacement with the same statement.",
  "requested_change": "Change the attribute to `@[deprecated Order.IsNormal.monotone (since := \"2025-12-25\")]`.",
  "severity": "advisory",
  "evidence": "Arithmetic.lean lines 374-377 (file_read): `@[deprecated Order.IsNormal.strictMono ...] theorem IsNormal.monotone ... : Monotone f`. The diff adds `protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f` to Order/IsNormal.lean. lean_verify_edit with line mode 374-377 and the retargeted attribute: outcome `compiled`, no errors, no warnings."
 },
 {
  "target": "Mathlib/Order/IsNormal.lean",
  "claim": "The module docstring still lists the TODO '* Replace `Ordinal.IsNormal` by this more general notion.' This PR does exactly that (`Ordinal.IsNormal` is now deprecated in favour of `Order.IsNormal`, and its own docstring's 'Todo: deprecate this' line was removed), so the TODO is stale.",
  "requested_change": "Delete the bullet `* Replace \\`Ordinal.IsNormal\\` by this more general notion.` from the `## TODO` section of Mathlib/Order/IsNormal.lean, keeping the remaining TODO item.",
  "severity": "advisory",
  "evidence": "file_read target/Mathlib/Order/IsNormal.lean lines 21-24: '## TODO / * Prove the equivalence with the standard definition (in some other file). / * Replace `Ordinal.IsNormal` by this more general notion.' content_search for `Ordinal\\.IsNormal` over Mathlib also hits this line. lean_verify_edit replacing lines 21-24 without the stale bullet: `compiled`, no warnings."
 },
 {
  "target": "Mathlib/SetTheory/Ordinal/Arithmetic.lean",
  "claim": "The reorganised module docstring drops the bullet for `pred o`, but `Ordinal.pred` is still defined in this file. It sits under its own `/-! ### The predecessor of an ordinal -/` section with `pred_succ`, `pred_le_iff_le_succ` and the rest, and unlike `Order.succ` it was not generalised. The 'Main definitions' list now omits one of the file's main definitions.",
  "requested_change": "Restore the bullet in the 'Main definitions and results' list, fixing the old typo: `* \\`pred o\\` is the predecessor of \\`o\\`. If \\`o\\` is not a successor, we set \\`pred o = o\\`.`",
  "severity": "advisory",
  "evidence": "Diff hunk @@ -29,20 +29,19 @@ removes '* `pred o` if the predecessor of `o`...' and adds no replacement. content_search shows `def pred (o : Ordinal) : Ordinal :=` at Arithmetic.lean:290 under '/-! ### The predecessor of an ordinal -/' (line 287). lean_verify_edit (line mode 30-33, bullet restored): `compiled`, no warnings."
 },
 {
  "target": "Ordinal.iSup_pow_natCast",
  "claim": "The new name `iSup_pow_natCast` says there is a `Nat.cast` in the statement, but there is none. `⨆ n : ℕ, o ^ n = o ^ ω` uses the monoid power `o ^ (n : ℕ)`, and the proof converts it to a cast with `simp_rw [← opow_natCast]`. This differs from the renamed siblings `iSup_add_natCast` / `iSup_mul_natCast`, whose statements really do contain `↑n`. The rename therefore makes the name inaccurate and adds a deprecated alias for no gain.",
  "requested_change": "Revert the rename: keep the theorem as `iSup_pow`, delete `@[deprecated] alias iSup_pow := iSup_pow_natCast`, and change the `nfp_mul_one` call site back to `iSup_pow ha`.",
  "severity": "advisory",
  "evidence": "lean_verify_edit on Exponential.lean adding two examples after the alias: `example ... : ⨆ n : ℕ, Monoid.npow n o = o ^ ω := iSup_pow_natCast ho` was accepted. `example ... : ⨆ n : ℕ, o ^ (n : Ordinal) = o ^ ω := iSup_pow_natCast ho` failed with 'Type mismatch ... has type ⨆ n, HPow.hPow.{u_1 + 1, 0, u_1 + 1} o n = o ^ ω but is expected ... HPow.hPow ... o ↑n', so the statement has no cast. lean_verify_edit restoring `theorem iSup_pow` (lines 520-529, no alias): `compiled`. naming_norm on the new name returned subject_unresolved (unmeasured)."
 },
 {
  "target": "Ordinal.opow_add",
  "claim": "The rewritten zero case of `opow_add` has a dead `have`. `have : b + c ≠ 0 := (hc.trans_le le_add_self).ne'` is never used: the following `rw [..., zero_opow, ...]` leaves the side goal, which is then closed by re-proving the same term with `exact (hc.trans_le le_add_self).ne'`. The proof also goes through `ha.ne'` twice where `ha : 0 < a` can be used directly: `one_le_iff_ne_zero.2 ha.ne'` is `one_le_iff_pos.2 ha`, and `opow_pos b (pos_iff_ne_zero.2 ha.ne')` is `opow_pos b ha`.",
  "requested_change": "Replace the zero case with `rw [zero_opow hc.ne', zero_opow (hc.trans_le le_add_self).ne', mul_zero]`, dropping the `have` and the trailing `exact`. Use `(one_le_iff_pos.2 ha).eq_or_lt` and `isNormal_mul_right <| opow_pos b ha`; the limit case's last term then fits on one line: `(((isNormal_mul_right <| opow_pos b ha).comp (isNormal_opow ha')).le_iff_forall_le l).symm`.",
  "severity": "advisory",
  "evidence": "file_read Exponential.lean lines 198-213 shows the `have` at line 201, the bare `zero_opow` at 202 and the duplicate `exact` at 203. lean_verify_edit (declaration_name `Ordinal.opow_add`) with the golfed proof: outcome `compiled`, no errors or warnings. A control edit with an unknown identifier was rejected, which confirms the tool really compiles."
 },
 {
  "target": "Ordinal.IsNormal.bsup",
  "claim": "Now that `H : Order.IsNormal f`, the rewrite spells out `Order.IsNormal.map_iSup H (bddAbove_of_small _)`. That pushes the line over the limit and splits a trailing `<;>\\n      rfl` onto its own line, while the other call sites in the PR (`nfpFamily_fp`, `derivFamily_fp`, `apply_omega0_of_isNormal`) use dot notation `H.map_iSup (bddAbove_of_small _)`.",
  "requested_change": "Write `rw [← iSup'_eq_bsup r, H.map_iSup (bddAbove_of_small _), ← iSup'_eq_bsup r] <;> rfl` on one line. Likewise use `h.map_iSup (bddAbove_of_small _)` in `enumOrd_isNormal_iff_isClosed` (Topology.lean).",
  "severity": "advisory",
  "evidence": "file_read Family.lean lines 379-384 shows the split `<;>` / `rfl`. lean_verify_edit (declaration_name `Ordinal.IsNormal.bsup`) with `H.map_iSup (bddAbove_of_small _)` on a single line: outcome `compiled`, no errors or warnings."
 },
 {
  "target": "Mathlib/SetTheory/Ordinal/Arithmetic.lean",
  "claim": "The PR deletes the `/-! ### Normal ordinal functions -/` section header, so the deprecated `Ordinal.IsNormal` and its 15 deprecated lemmas now sit under `/-! ### The predecessor of an ordinal -/` in the file and in the generated docs.",
  "requested_change": "Keep a section header before the deprecated block, e.g. `/-! ### Normal ordinal functions (deprecated) -/`, directly before the `Ordinal.IsNormal` docstring.",
  "severity": "advisory",
  "evidence": "file_read Arithmetic.lean lines 287-447: the header '### The predecessor of an ordinal' is at line 287, `lift_pred` ends at 348, and the `Ordinal.IsNormal` docstring follows at 350 with no header until '### Subtraction on ordinals' at 447. The diff shows `-/-! ### Normal ordinal functions -/`. lean_verify_edit inserting the header at line 349: `compiled`."
 }
]
json.dump(findings, open(f"{D}/findings.json", "w"), ensure_ascii=False, indent=1)
print(len(findings))
