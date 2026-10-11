import json
D="/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/conventions-dossiers/results/pr_review_v5/probes/model-gap-dev-medium-0.3.0/pr33294/TA1"
F=[]
def add(target, claim, change, sev, ev):
    F.append({"target": target, "claim": claim, "requested_change": change, "severity": sev, "evidence": ev})

add("Ordinal.IsNormal.mem_range_deriv (Mathlib/SetTheory/Ordinal/FixedPoint.lean)",
 "The PR deletes `Ordinal.IsNormal.mem_range_deriv` outright. The diff replaces `theorem IsNormal.mem_range_deriv ... := H.fp_iff_deriv.symm` with `alias IsNormal.fp_iff_deriv := fp_iff_deriv`, and no deprecated alias for the old name is added. Every other renamed `IsNormal.*` lemma in FixedPoint.lean gets one, so downstream uses of `H.mem_range_deriv` / `IsNormal.mem_range_deriv` break with no deprecation warning.",
 "After `theorem mem_range_deriv`, add `@[deprecated (since := \"2025-12-25\")] alias IsNormal.mem_range_deriv := mem_range_deriv`.",
 "blocking",
 "declaration_search `Ordinal.IsNormal.mem_range_deriv`: declared before this PR at FixedPoint.lean:360, 0 declarations in this PR. content_search for `mem_range_deriv\\b` over target/Mathlib finds only `theorem mem_range_deriv` (l.375), its uses, and the `@[deprecated mem_range_deriv ...]` attributes, with no alias named `IsNormal.mem_range_deriv`. lean_verify_edit on FixedPoint.lean l.361-383 with the alias added compiles with no errors or warnings (outcome `compiled`).")

add("Ordinal.IsNormal.deriv_fp / IsNormal.le_iff_deriv / fp_iff_deriv / IsNormal.fp_iff_deriv (Mathlib/SetTheory/Ordinal/FixedPoint.lean:364-383)",
 "Four deprecations this PR adds in FixedPoint.lean carry `(since := \"2025-10-25\")`: the aliases `IsNormal.deriv_fp`, `IsNormal.le_iff_deriv` and `IsNormal.fp_iff_deriv`, and the theorem `fp_iff_deriv`. Every other deprecation in the PR uses `2025-12-25`, and these declarations were not deprecated before the PR. The date looks copied from the unrelated neighbouring `deriv_id_of_nfp_id` alias, and it would bring forward the removal schedule for these names by two months.",
 "Change the `since` field of these four deprecations to `\"2025-12-25\"`, the date of this PR's other deprecations.",
 "blocking",
 "file_read FixedPoint.lean l.358-383: `@[deprecated (since := \"2025-10-25\")] alias deriv_id_of_nfp_id` (pre-existing) is followed by the PR's `@[deprecated (since := \"2025-10-25\")] alias IsNormal.deriv_fp`, `... IsNormal.le_iff_deriv`, `@[deprecated mem_range_deriv (since := \"2025-10-25\")] theorem fp_iff_deriv` and `... alias IsNormal.fp_iff_deriv`. The model shows `theorem IsNormal.deriv_fp`, `IsNormal.le_iff_deriv` and `IsNormal.fp_iff_deriv` without any attribute before the PR. All other new deprecations in the diff (Arithmetic, Family, Cofinality, Exponential, Veblen, and FixedPoint l.296-318) use 2025-12-25. lean_verify_edit with the dates changed to 2025-12-25 compiles.")

add("Ordinal.fp_iff_deriv (Mathlib/SetTheory/Ordinal/FixedPoint.lean:378-383)",
 "The PR adds a new root-level declaration, `Ordinal.fp_iff_deriv`, that is deprecated the moment it is created, and then makes the old `IsNormal.fp_iff_deriv` an alias of that deprecated declaration. It also leaves the sibling `fp_iff_derivFamily` undeprecated. So the PR adds a name nobody can have used, and points a deprecated alias at another deprecated declaration.",
 "Delete `Ordinal.fp_iff_deriv`. Keep `IsNormal.fp_iff_deriv` as the deprecated declaration, with its own statement, since it differs from `mem_range_deriv`: `@[deprecated mem_range_deriv \"use `(mem_range_deriv H).symm`\" (since := \"2025-12-25\")] theorem IsNormal.fp_iff_deriv (H : IsNormal f) {a} : f a = a ↔ ∃ o, deriv f o = a := (Ordinal.mem_range_deriv H).symm`. Alternatively, keep `fp_iff_deriv` undeprecated alongside `fp_iff_derivFamily`.",
 "advisory",
 "declaration_search `Ordinal.fp_iff_deriv`: 0 declarations before this PR, 1 in this PR. content_search shows no use of `fp_iff_deriv` anywhere in target/Mathlib besides its own alias. lean_verify_edit replacing FixedPoint.lean l.361-383 with the deprecated theorem `IsNormal.fp_iff_deriv` (body `(Ordinal.mem_range_deriv H).symm`, plus the `IsNormal.mem_range_deriv` alias) compiles with no errors or warnings. With an unqualified `mem_range_deriv` in the body, the name resolves to the `Ordinal.IsNormal.mem_range_deriv` alias and gives a deprecation warning, hence the qualified name. `fp_iff_derivFamily` (l.208) is not deprecated.")

add("Ordinal.IsNormal.monotone (Mathlib/SetTheory/Ordinal/Arithmetic.lean:374-377)",
 "`Ordinal.IsNormal.monotone` is deprecated with `Order.IsNormal.strictMono` as its replacement. That lemma does not state `Monotone f`. The PR itself adds the exact replacement, `Order.IsNormal.monotone`, in Mathlib/Order/IsNormal.lean.",
 "Change the attribute to `@[deprecated Order.IsNormal.monotone (since := \"2025-12-25\")]`, and the body to `Order.IsNormal.monotone H`.",
 "blocking",
 "Diff: `+protected theorem monotone {f : α → β} (hf : IsNormal f) : Monotone f` in Order/IsNormal.lean. Arithmetic.lean l.375: `@[deprecated Order.IsNormal.strictMono (since := \"2025-12-25\")] theorem IsNormal.monotone ... : Monotone f`. lean_verify_edit on l.374-377 with `@[deprecated Order.IsNormal.monotone ...]` and body `Order.IsNormal.monotone H` compiles with no errors or warnings.")

add("module docstring of Mathlib/Order/IsNormal.lean (## TODO)",
 "The module docstring still lists the TODO `* Replace Ordinal.IsNormal by this more general notion.` This PR does exactly that, so the TODO is now stale. Its other TODO, proving the equivalence with the standard definition, is already done in Mathlib/Topology/Order/IsNormal.lean (`Order.isNormal_iff_strictMono_and_continuous`).",
 "Remove the `Replace Ordinal.IsNormal ...` bullet from the `## TODO` section. Since the other bullet is also done, remove the whole `## TODO` section.",
 "advisory",
 "file_read target/Mathlib/Order/IsNormal.lean l.21-24 shows the TODO. The PR deprecates `Ordinal.IsNormal` (`@[deprecated Order.IsNormal (since := \"2025-12-25\")] protected def IsNormal`, Arithmetic.lean l.353). file_read target/Mathlib/Topology/Order/IsNormal.lean l.43-54 proves `isNormal_iff_strictMono_and_continuous`.")

add("module docstring of Mathlib/SetTheory/Ordinal/Arithmetic.lean",
 "The PR's rewrite of the module docstring drops the bullet `pred o` (\"the predecessor of o ... we set pred o = o\") from the main definitions. `Ordinal.pred` is still defined in this file, is not deprecated, and has its own API (`pred_succ`, `pred_le_iff_le_succ`, `pred_succ_gi`, `lift_pred`, ...). The docstring no longer covers a main definition the file contains.",
 "Restore the `pred` bullet in `## Main definitions and results`, e.g. `* pred o is the predecessor of o. If o is not a successor, we set pred o = o.`, which also fixes the old typo \"if\" → \"is\". Removing it belongs in a PR that deprecates `Ordinal.pred`.",
 "advisory",
 "content_search `pred` in target Arithmetic.lean: `def pred (o : Ordinal) : Ordinal` at l.290 under `/-! ### The predecessor of an ordinal -/`, followed by about 15 pred lemmas, none deprecated. file_read l.24-47: the PR's docstring lists +, -, *, /, limitRecOn, then Order.succ, Order.IsSuccLimit and Order.IsNormal, with no pred bullet.")

add("Ordinal.cof_eq_of_isNormal (Mathlib/SetTheory/Cardinal/Cofinality.lean:565)",
 "The PR renames `IsNormal.cof_eq` to the root-level `cof_eq_of_isNormal`. Its main argument is `hf : IsNormal f`, so by convention it belongs in that namespace (`Order.IsNormal.cof_eq`) and is used as `hf.cof_eq ha`. The rename drops dot notation: the PR has to rewrite `cof_add`, `cof_preOmega` and `cof_omega` from `h.cof_eq` to `cof_eq_of_isNormal h`. Downstream, `h.cof_eq` now fails with an error rather than a deprecation warning, because `isNormal_*` lemmas now produce `Order.IsNormal` terms, and dot notation on those never finds the `Ordinal.IsNormal.cof_eq` alias.",
 "Declare it as `theorem _root_.Order.IsNormal.cof_eq {f} (hf : IsNormal f) {a} (ha : IsSuccLimit a) : cof (f a) = cof a`, retarget the deprecated alias to `alias IsNormal.cof_eq := Order.IsNormal.cof_eq`, and revert `cof_add`, `cof_preOmega` and `cof_omega` to their pre-PR dot-notation proofs (`(isNormal_add_right a).cof_eq hb`, `isNormal_preOmega.cof_eq ⟨h, ho⟩`, `isNormal_omega.cof_eq ho`).",
 "advisory",
 "lean_verify_edit replacing Cofinality.lean l.565-615 with `_root_.Order.IsNormal.cof_eq` / `_root_.Order.IsNormal.cof_le`, the retargeted aliases and the pre-PR dot-notation proofs of cof_add, cof_preOmega and cof_omega compiles with no errors or warnings (outcome `compiled`). naming_norm only measures the leading prefix (`cof_`, conforms), not the namespace.")

add("Ordinal.cof_le_of_isNormal (Mathlib/SetTheory/Cardinal/Cofinality.lean:572)",
 "`cof_le_of_isNormal (hf : IsNormal f) (a)` takes the normality hypothesis as its main argument but sits in the root `Ordinal` namespace with an `_of_isNormal` suffix. The pre-PR name, `IsNormal.cof_le`, allowed `hf.cof_le a`, and dot notation on `Order.IsNormal` terms cannot reach the deprecated `Ordinal.IsNormal.cof_le` alias.",
 "Rename to `theorem _root_.Order.IsNormal.cof_le {f} (hf : IsNormal f) (a) : cof a ≤ cof (f a)`, end the proof with `rw [hf.cof_eq ha]`, and point the deprecated alias at `Order.IsNormal.cof_le`.",
 "advisory",
 "Same lean_verify_edit as for cof_eq (Cofinality.lean l.565-615): `_root_.Order.IsNormal.cof_le` with `· rw [hf.cof_eq ha]` compiles with no errors or warnings.")

add("Ordinal.isFundamentalSequence_of_isNormal (Mathlib/SetTheory/Cardinal/Cofinality.lean:535)",
 "The PR turns `protected theorem IsNormal.isFundamentalSequence` into the root-level `isFundamentalSequence_of_isNormal`, although its main argument is `hf : IsNormal f`. The new deprecated alias `IsNormal.isFundamentalSequence` also drops the `protected` modifier the original had, whereas Veblen.lean keeps `protected` on its deprecated alias.",
 "Declare it as `protected theorem _root_.Order.IsNormal.isFundamentalSequence ...`, so it is used as `hf.isFundamentalSequence ha hg` (including in `cof_eq`), and keep the deprecated alias `protected`: `@[deprecated (since := \"2025-12-25\")] protected alias IsNormal.isFundamentalSequence := Order.IsNormal.isFundamentalSequence`.",
 "advisory",
 "lean_verify_edit replacing Cofinality.lean l.535-615 with `protected theorem _root_.Order.IsNormal.isFundamentalSequence` (proof unchanged), the protected deprecated alias, and `hf.isFundamentalSequence ha hg` in `Order.IsNormal.cof_eq` compiles with no errors or warnings.")

add("Ordinal.apply_omega0_of_isNormal (Mathlib/SetTheory/Ordinal/Family.lean:865)",
 "`IsNormal.apply_omega0` is renamed to the root-level `apply_omega0_of_isNormal (hf : IsNormal f)`, losing dot notation. Its call sites in `preOmega_omega0`, `iSup_pow`, `iSup_add_nat` and `iSup_mul_nat` all had to be rewritten from `h.apply_omega0` to `apply_omega0_of_isNormal h`.",
 "Declare it as `theorem _root_.Order.IsNormal.apply_omega0 {f : Ordinal.{u} → Ordinal.{v}} (hf : IsNormal f) : ⨆ n : ℕ, f n = f ω`, retarget the alias to `alias IsNormal.apply_omega0 := Order.IsNormal.apply_omega0`, and keep the pre-PR call sites `(isNormal_add_right o).apply_omega0`, `(isNormal_mul_right ho).apply_omega0`, `isNormal_preOmega.apply_omega0` and `(isNormal_opow ho₁).apply_omega0`.",
 "advisory",
 "lean_verify_edit replacing Family.lean l.865-887 with `_root_.Order.IsNormal.apply_omega0`, the retargeted alias, and `iSup_add_nat` / `iSup_mul_nat` with their original dot-notation proofs compiles with no errors or warnings. naming_norm on `Ordinal.apply_omega0_of_isNormal`: subject_unresolved (unmeasured).")

add("Ordinal.nfp_fp (Mathlib/SetTheory/Ordinal/FixedPoint.lean:291-318, also deriv_fp / le_iff_deriv / mem_range_deriv)",
 "The single-function fixed-point lemmas `apply_lt_nfp`, `nfp_le_apply`, `nfp_fp`, `apply_le_nfp`, `deriv_fp`, `le_iff_deriv` and `mem_range_deriv` all take `H : IsNormal f` as their main argument. The PR moves them out of the `IsNormal` namespace to root names. Dot-notation uses such as `(isNormal_mul_right ha).nfp_fp _`, `isNormal_veblen_zero.deriv_fp o` and `(isNormal_opow _).deriv_fp` had to be rewritten, and downstream ones break, because the `Ordinal.IsNormal.*` aliases are unreachable from `Order.IsNormal` terms.",
 "Declare them in the `Order.IsNormal` namespace (`theorem _root_.Order.IsNormal.nfp_fp (H : IsNormal f) ...`, and likewise for the others), point the deprecated `Ordinal.IsNormal.*` aliases at them, and keep the pre-PR dot-notation call sites (e.g. `(isNormal_mul_right ha).nfp_fp (a ^ ω * b + c)` in `nfp_mul_opow_omega0_add`, `deriv_fp` uses in Veblen.lean).",
 "advisory",
 "lean_verify_edit replacing FixedPoint.lean l.291-529: `_root_.Order.IsNormal.apply_lt_nfp`, `.nfp_le_apply`, `.nfp_fp` and `.apply_le_nfp`, with `nfp_mul_opow_omega0_add` back to `(isNormal_mul_right ha).nfp_fp (a ^ ω * b + c)`, compiles with no errors or warnings. Without restoring that call site, the only error is `Unknown identifier nfp_fp` there.")

add("Ordinal.iSup_pow_natCast (Mathlib/SetTheory/Ordinal/Exponential.lean:520)",
 "`iSup_pow` is renamed to `iSup_pow_natCast`, but its statement `⨆ n : ℕ, o ^ n = o ^ ω` has no `Nat.cast`: `o ^ n` is the monoid power with exponent `n : ℕ`, and the proof begins by rewriting it into `o ^ (n : Ordinal)`. The name contains a declaration that does not appear in the statement. This differs from `iSup_add_natCast`/`iSup_mul_natCast`, where `o + n` and `o * n` do contain a cast.",
 "Keep the name `iSup_pow`, and drop the rename and the `@[deprecated] alias iSup_pow := iSup_pow_natCast`.",
 "advisory",
 "lean_verify_edit replacing `Ordinal.iSup_pow_natCast` with the statement `⨆ n : ℕ, o ^ (n : Ordinal) = o ^ ω` fails at `simp_rw [← opow_natCast]` with \"`simp` made no progress\". So the PR's statement uses the ℕ-power, not a cast. declaration_search `iSup_pow`: `Ordinal.iSup_pow` (base) and `NNReal.iSup_pow`, so no root-level clash forces a rename.")

add("Ordinal.iSup_add_natCast (Mathlib/SetTheory/Ordinal/Family.lean:873; also iSup_mul_natCast, iSup_pow_natCast)",
 "The renames `iSup_add_nat → iSup_add_natCast`, `iSup_mul_nat → iSup_mul_natCast` and `iSup_pow → iSup_pow_natCast`, with their three deprecated aliases and the call-site updates in FixedPoint.lean, are unrelated to deprecating `Ordinal.IsNormal`. The PR title and description do not mention them. With `Order.IsNormal.apply_omega0` the old proofs work unchanged.",
 "Remove these renames from this PR, keeping `iSup_add_nat`, `iSup_mul_nat` and `iSup_pow` with their current proofs, and propose them in a separate PR if wanted.",
 "advisory",
 "Diff, Family.lean l.569-587 and Exponential.lean l.463-474: renames plus `@[deprecated (since := \"2025-12-25\")]` aliases. lean_verify_edit on Family.lean l.865-887 with the original `iSup_add_nat` / `iSup_mul_nat` (dot-notation `apply_omega0`) compiles with no errors or warnings.")

add("Mathlib/SetTheory/Ordinal/Exponential.lean (opow_add, opow_mul, module docstring)",
 "In `opow_add` and `opow_mul`, the IsNormal migration only requires replacing `.trans` with `.comp` and `.limit_le` with `.le_iff_forall_le` in the limit case. The PR also rewrites the zero and one cases of both proofs (`rcases eq_or_ne` → `obtain ... eq_zero_or_pos`, `by_cases ... simp_all`) and reflows the module docstring header. These are incidental changes to code the PR does not need to touch.",
 "Limit the Exponential.lean changes to the `IsNormal` API migration in the limit cases, and move the golfing of the base cases and the docstring reflow to a separate PR.",
 "advisory",
 "Diff Exponential.lean hunks @@ -7,7 and @@ -188,34 / -230,28: the base-case rewrites do not mention IsNormal. Only the `limit` branches use `isNormal_opow`, `.comp` and `.le_iff_forall_le`.")

add("Ordinal.opow_add (Mathlib/SetTheory/Ordinal/Exponential.lean:198)",
 "In the rewritten `opow_add`, `have : b + c ≠ 0 := (hc.trans_le le_add_self).ne'` is never used: the next line leaves `zero_opow`'s side goal open and closes it with an `exact` that repeats the same proof term. `opow_pos b (pos_iff_ne_zero.2 ha.ne')` round-trips `ha : 0 < a` through `≠ 0`. Two lines join `obtain ...` and `· simp` with `;`.",
 "Remove the `have` and write `rw [zero_opow hc.ne', zero_opow (hc.trans_le le_add_self).ne', mul_zero]`. Use `isNormal_mul_right (opow_pos b ha)`. Put `· simp` on its own line after each `obtain`.",
 "advisory",
 "lean_verify_edit of `Ordinal.opow_add` with these changes (`obtain rfl | hc := eq_zero_or_pos c` / `· simp` / `rw [zero_opow hc.ne', zero_opow (hc.trans_le le_add_self).ne', mul_zero]`, `obtain rfl | ha' := ...` / `· simp`, and `(((isNormal_mul_right (opow_pos b ha)).comp (isNormal_opow ha')).le_iff_forall_le l).symm`) compiles with no errors or warnings.")

add("Ordinal.opow_mul (Mathlib/SetTheory/Ordinal/Exponential.lean:227)",
 "`opow_mul` puts two tactics on one line with `;`: `obtain rfl | hb := eq_zero_or_pos b; · simp` and `obtain rfl | ha' := (one_le_iff_ne_zero.2 ha).eq_or_lt; · simp`.",
 "Split each into two lines: `obtain rfl | hb := eq_zero_or_pos b` followed by `· simp`, and the same for the `ha'` case.",
 "advisory",
 "lean_verify_edit of `Ordinal.opow_mul` with both `· simp` cases on their own lines compiles with no errors or warnings.")

add("Ordinal.IsNormal.le_iff_eq (Mathlib/SetTheory/Ordinal/Arithmetic.lean:410-413)",
 "`IsNormal.le_iff_eq : f a ≤ a ↔ f a = a` is deprecated with `StrictMono.le_apply : a ≤ f a` as its replacement. That lemma states something different and does not apply to `H` directly; the PR's own replacements use `H.strictMono.le_apply.ge_iff_eq'` (in `add_le_right_iff_mul_omega0_le`, `mul_le_right_iff_opow_omega0_dvd` and `fp_iff_derivFamily`). The deprecation warning gives no hint of how to substitute.",
 "Add a usage message: `@[deprecated StrictMono.le_apply \"use `hf.strictMono.le_apply.ge_iff_eq'`\" (since := \"2025-12-25\")]`.",
 "advisory",
 "lean_verify_edit on Arithmetic.lean l.410-413 with this attribute compiles with no errors or warnings. Diff: the PR replaces `(isNormal_add_right a).le_iff_eq` with `(isNormal_add_right a).strictMono.le_apply.ge_iff_eq'`.")

add("Ordinal.IsNormal.lt_iff (Mathlib/SetTheory/Ordinal/Arithmetic.lean:385-408; also le_iff, id_le, le_apply)",
 "`IsNormal.lt_iff`, `IsNormal.le_iff`, `IsNormal.id_le` and `IsNormal.le_apply` are deprecated with `StrictMono.lt_iff_lt`, `StrictMono.le_iff_le`, `StrictMono.id_le` and `StrictMono.le_apply` as replacements. These are not drop-in substitutes for `H.lt_iff` and the rest: a user must insert `.strictMono`, as the PR does at every call site (`(isNormal_opow a1).strictMono.lt_iff_lt`). The deprecations do not say so.",
 "Add a usage message to each, e.g. `@[deprecated StrictMono.lt_iff_lt \"use `hf.strictMono.lt_iff_lt`\" (since := \"2025-12-25\")]`, and likewise `hf.strictMono.le_iff_le`, `hf.strictMono.id_le` and `hf.strictMono.le_apply`.",
 "advisory",
 "file_read Arithmetic.lean l.385-408 shows the four attributes with no message. Diff, Exponential.lean: `(isNormal_opow a1).lt_iff` → `.strictMono.lt_iff_lt`, `.le_iff` → `.strictMono.le_iff_le`, `.le_apply` → `.strictMono.le_apply`. The message syntax was checked on `IsNormal.le_iff_eq` (compiles).")

add("Ordinal.IsNormal.inj (Mathlib/SetTheory/Ordinal/Arithmetic.lean:395-398)",
 "`IsNormal.inj` is deprecated with `Injective.eq_iff` as its replacement, which needs `H.strictMono.injective` first. The bare name gives no indication of how to get an `Injective` hypothesis from a normal function.",
 "Use `@[deprecated Function.Injective.eq_iff \"use `hf.strictMono.injective.eq_iff`\" (since := \"2025-12-25\")]`.",
 "advisory",
 "Diff, Exponential.lean: `(isNormal_opow a1).inj` → `(isNormal_opow a1).strictMono.injective.eq_iff`. Arithmetic.lean l.396 has no message.")

add("Ordinal.IsNormal.le_set (Mathlib/SetTheory/Ordinal/Arithmetic.lean:415-428; also le_set')",
 "`IsNormal.le_set` and `IsNormal.le_set'` are deprecated with `IsNormal.map_isLUB` as the replacement. That lemma has a quite different statement (`IsLUB s a → s.Nonempty → IsLUB (f '' s) (f a)`), and the deprecation gives no guidance on the translation.",
 "Add a message describing the substitute, e.g. `@[deprecated IsNormal.map_isLUB \"use `hf.map_isLUB` with `IsLUB p b` and unfold `isLUB_le_iff`\" (since := \"2025-12-25\")]`, on both lemmas.",
 "advisory",
 "file_read Arithmetic.lean l.415-428: the PR's own proof of `le_set` needs three lines to derive it from `map_isLUB`. Order/IsNormal.lean l.84 gives the `map_isLUB` statement.")

add("Ordinal.IsNormal.map_iSup (Mathlib/SetTheory/Ordinal/Family.lean:241-265; also map_iSup_of_bddAbove, map_sSup, map_sSup_of_bddAbove)",
 "The deprecated `IsNormal.map_iSup`, `map_iSup_of_bddAbove`, `map_sSup` and `map_sSup_of_bddAbove` point to `Order.IsNormal.map_iSup` / `map_sSup`, which are not drop-in. They need an extra `(bddAbove_of_small _)` argument, `g` becomes implicit, and the `map_sSup` hypotheses come in the opposite order (`hn hs` instead of `hs hn`). The deprecations give no message, though the PR's own call sites had to change to `H.map_iSup (bddAbove_of_small _)`.",
 "Add usage messages, e.g. `@[deprecated Order.IsNormal.map_iSup \"use `hf.map_iSup (bddAbove_of_small _)`\" (since := \"2025-12-25\")]` on `map_iSup`, `\"use `hf.map_sSup hn (bddAbove_of_small _)`\"` on `map_sSup`, and note the swapped `hn hs` order on `map_sSup_of_bddAbove`.",
 "advisory",
 "file_read Family.lean l.241-265 and Order/IsNormal.lean l.158-167 (`map_sSup (hf) (hs : s.Nonempty) (hs' : BddAbove s)`, `map_iSup {g} (hf) (hg : BddAbove (range g))`). Diff: FixedPoint `H.map_iSup` → `H.map_iSup (bddAbove_of_small _)` at three sites.")

add("Ordinal.IsNormal.eq_iff_zero_and_succ (Mathlib/SetTheory/Ordinal/Family.lean:812)",
 "`IsNormal.eq_iff_zero_and_succ` (stated with `f 0 = g 0`) is deprecated to `IsNormal.ext`, which is stated with `f ⊥ = g ⊥`. Users must add `bot_eq_zero`, as the PR does in `deriv_add_eq_mul_omega0_add` and `deriv_mul_eq_opow_omega0_mul` (`rw [bot_eq_zero, ...]`). The deprecation gives no message.",
 "Add a message: `@[deprecated IsNormal.ext \"use `IsNormal.ext` together with `bot_eq_zero`\" (since := \"2025-12-25\")]`.",
 "advisory",
 "Order/IsNormal.lean l.138-139: `IsNormal.ext ... : f = g ↔ f ⊥ = g ⊥ ∧ ...`. Diff, FixedPoint: `· rw [bot_eq_zero, deriv_zero_right, add_zero]` was added after switching to `IsNormal.ext`.")

add("Ordinal.IsNormal.map_sSup (Mathlib/SetTheory/Ordinal/Family.lean:261-265)",
 "`set_option linter.deprecated false in` before `IsNormal.map_sSup` silences nothing. This lemma's hypothesis is written `(H : IsNormal f)`, i.e. `Order.IsNormal`, not the deprecated `Ordinal.IsNormal`, so no deprecated constant is referenced. The siblings write `Ordinal.IsNormal f`, so the block is also inconsistent.",
 "Delete the `set_option linter.deprecated false in` line before `IsNormal.map_sSup`, or state the hypothesis the same way as its siblings.",
 "advisory",
 "lean_verify_edit on Family.lean l.261-265 without the set_option line compiles with no errors and no warnings (`warnings: []`).")

add("Ordinal.IsNormal.limit_le (Mathlib/SetTheory/Ordinal/Arithmetic.lean:357-445 and Family.lean:241-271)",
 "Each deprecated `Ordinal.IsNormal.*` lemma is wrapped in `set_option linter.deprecated false in`: 16 in Arithmetic.lean and 5 in Family.lean. The exemption is only needed because the hypotheses are spelled `H : Ordinal.IsNormal f`. Writing them as `H : IsNormal f` (for `f : Ordinal → Ordinal`) removes the warning at its source. These lemmas are reached only by explicit name or by dot notation on `Ordinal.IsNormal` terms, and both still work, since `Ordinal.IsNormal f` unfolds to `Order.IsNormal f`.",
 "State the deprecated lemmas' hypotheses (and `IsNormal.refl`'s / `isNormal_iff_strictMono_limit`'s statements) with `IsNormal f` instead of `Ordinal.IsNormal f`, and delete the `set_option linter.deprecated false in` lines.",
 "advisory",
 "lean_verify_edit on Arithmetic.lean l.441-445: dropping only the set_option gives the warning \"`Ordinal.IsNormal` has been deprecated\" at `(H : Ordinal.IsNormal f)`. Rewriting it as `theorem IsNormal.isSuccLimit {f : Ordinal → Ordinal} (H : IsNormal f) ...` without the set_option compiles with no errors and no warnings.")

add("Ordinal.IsNormal.bsup (Mathlib/SetTheory/Ordinal/Family.lean:383)",
 "In `IsNormal.bsup`, `H : IsNormal f` is an `Order.IsNormal` term, but the proof calls `Order.IsNormal.map_iSup H (bddAbove_of_small _)` by its fully qualified name. That forces a line break, leaving `<;>` with `rfl` alone on the next line.",
 "Use dot notation: `rw [← iSup'_eq_bsup r, H.map_iSup (bddAbove_of_small _), ← iSup'_eq_bsup r] <;> rfl` on one line.",
 "advisory",
 "lean_verify_edit of `Ordinal.IsNormal.bsup` with `H.map_iSup (bddAbove_of_small _)` and `<;> rfl` on the same line compiles with no errors or warnings.")

add("Ordinal.enumOrd_isNormal_iff_isClosed (Mathlib/SetTheory/Ordinal/Topology.lean:186)",
 "The PR writes `rw [Order.IsNormal.map_iSup h (bddAbove_of_small _)]`, applying the namespaced lemma to `h : IsNormal (enumOrd s)` by its fully qualified name instead of dot notation.",
 "Write `rw [h.map_iSup (bddAbove_of_small _)]`.",
 "advisory",
 "lean_verify_edit replacing Topology.lean l.186 with `    rw [h.map_iSup (bddAbove_of_small _)]` compiles with no errors or warnings.")

add("Mathlib/SetTheory/Ordinal/Arithmetic.lean (section header before the deprecated IsNormal block)",
 "The PR deletes the section header `/-! ### Normal ordinal functions -/` but keeps the whole deprecated `IsNormal` block (about 100 lines) in place. That block now sits under `/-! ### The predecessor of an ordinal -/`, which misdescribes it.",
 "Keep a section header before the block, e.g. `/-! ### Normal ordinal functions (deprecated) -/`, or `/-! ### Deprecated lemmas about Ordinal.IsNormal -/`.",
 "advisory",
 "Diff, Arithmetic.lean @@ -348: `-/-! ### Normal ordinal functions -/`. file_read l.287-356: the `### The predecessor of an ordinal` header at l.287 is followed directly by the pred lemmas and then the deprecated `Ordinal.IsNormal` def at l.353.")

add("PR #33294 (title and description)",
 "The description is only \"See issue #17033. Moved from #28743.\" Besides deprecating `Ordinal.IsNormal`, the PR renames a number of lemmas: `IsNormal.cof_eq/cof_le/isFundamentalSequence` → `*_of_isNormal`; `IsNormal.apply_omega0` → `apply_omega0_of_isNormal`; `IsNormal.nfp_fp/apply_lt_nfp/nfp_le_apply/apply_le_nfp/deriv_fp/le_iff_deriv/mem_range_deriv` → root names; `IsNormal.veblenWith_zero` → `isNormal_veblenWith_zero`; `iSup_add_nat/iSup_mul_nat/iSup_pow` → `*_natCast`. It also deprecates `IsNormal.veblenWith` and `fp_iff_deriv`, adds `Order.IsNormal.monotone`, and golfs `opow_add`/`opow_mul`. None of this is stated.",
 "Expand the PR description to list what is deprecated, each rename (old → new), the new `Order.IsNormal.monotone`, and any incidental proof changes, so reviewers and the deprecation log can follow the change.",
 "advisory",
 "pr.md description text. Diff and model.md 'Removed or renamed' list, which shows ten removed or renamed declarations plus the aliases added.")

json.dump(F, open(D+"/findings.json","w"), ensure_ascii=False, indent=1)
print(len(F))
