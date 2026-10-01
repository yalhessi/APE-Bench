import json
IND = "Mathlib/Algebra/Group/Irreducible/Indecomposable.lean"
BE = "Mathlib/LinearAlgebra/RootSystem/BaseExists.lean"
RP = "Mathlib/LinearAlgebra/RootSystem/RootPositive.lean"
findings = [
 {"path": IND, "line_start": 90, "severity": "blocking",
  "claim": "`Submonoid.closure_image_isMulIndecomposable_baseOf` renames `Submonoid.closure_image_one_lt_and_isMulIndecomposable`, which exists at the base commit (declaration_search: Indecomposable.lean:46), along with its `to_additive` counterpart. The old names are deleted with no deprecated alias, so downstream users break without warning.",
  "suggested_fix": "After the lemma, add `@[to_additive (attr := deprecated (since := \"<date>\"))] alias Submonoid.closure_image_one_lt_and_isMulIndecomposable := Submonoid.closure_image_isMulIndecomposable_baseOf`, so that both the multiplicative and the additive old names stay available as deprecated aliases."},
 {"path": IND, "line_start": 49, "severity": "advisory",
  "claim": "The docstrings of `IsMulIndecomposable.baseOf` are uninformative and contain a typo. The multiplicative one (\"The \\\"base\\\" of a set of points of a monoid relative to a morphism `f`\") never says which set this is. The additive one misspells \"crystallogrphic\".",
  "suggested_fix": "Fix the spelling to \"crystallographic\". Make the multiplicative docstring state the definition: the indices `i` with `1 < f (v i)` such that `v i` is indecomposable with respect to that half space. Keep the root-system remark in the additive docstring."},
 {"path": IND, "line_start": 49, "severity": "advisory",
  "claim": "`IsMulIndecomposable.baseOf` is declared as `Set ι`, but its body is `IsMulIndecomposable v {i | 1 < f (v i)}`, which is a predicate `ι → Prop`. It relies on the `Set ι = ι → Prop` defeq. The neighbouring `IsMulIndecomposable.subset` correctly writes `{i | IsMulIndecomposable v s i}`.",
  "suggested_fix": "Define it as `{i | IsMulIndecomposable v {j | 1 < f (v j)} i}`. This compiles with the whole file unchanged (checked with lean_verify_edit)."},
 {"path": IND, "line_start": 141, "severity": "advisory",
  "claim": "`IsMulIndecomposable.pairwise_div_notMem_range` states `hst : s ⊆ IsMulIndecomposable v t`, using the predicate `IsMulIndecomposable v t` as a set by defeq abuse. The primed variant does the same with `IsMulIndecomposable v {i | 1 < f (v i)}`.",
  "suggested_fix": "State the hypothesis as `hst : s ⊆ {i | IsMulIndecomposable v t i}`, matching `IsMulIndecomposable.subset`. The proof is unchanged and compiles (checked)."},
 {"path": IND, "line_start": 58, "severity": "advisory",
  "claim": "`IsMulIndecomposable.image_baseOf_inv_comp_eq` assumes `[IsOrderedMonoid S]`, but its proof never uses it. Membership in `baseOf v (invMonoidHom.comp f)` and in `baseOf v f` match through `hv_inv` and `map_inv` alone.",
  "suggested_fix": "Drop `[IsOrderedMonoid S]` from the signature. The unchanged proof compiles, and so does the rest of the file (checked)."},
 {"path": IND, "line_start": 116, "severity": "advisory",
  "claim": "`Subgroup.closure_image_isMulIndecomposable_baseOf` has a long proof. It splits `univ`, builds `f' := invMonoidHom.comp f` and needs `image_baseOf_inv_comp_eq`. The result follows pointwise from `Submonoid.closure_image_isMulIndecomposable_baseOf`: each `v i` with `1 < f (v i)` lies in the submonoid closure, and otherwise `(v i)⁻¹ = v i⁻¹` does.",
  "suggested_fix": "Replace the proof with: `refine le_antisymm (closure_mono (image_subset_range _ _)) ((closure_le _).mpr ?_)`; `rintro - ⟨i, rfl⟩`; `have key (j : ι) (hj : 1 < f (v j)) : v j ∈ closure (v '' IsMulIndecomposable.baseOf v f) := by apply le_closure_toSubmonoid; rw [Submonoid.closure_image_isMulIndecomposable_baseOf]; exact Submonoid.subset_closure ⟨j, hj, rfl⟩`; `rcases lt_or_gt_of_ne (hf i) with hi | hi`; `· simpa [hv_inv] using inv_mem (key i⁻¹ (by simpa [hv_inv]))`; `· exact key i hi` (checked: it compiles). `image_baseOf_inv_comp_eq` is then unused, so drop it from this PR. The same goes for `invMonoidHom_comp_invMonoidHom`, unless it is wanted on its own merits."},
 {"path": IND, "line_start": 161, "severity": "advisory",
  "claim": "`IsMulIndecomposable.pairwise_div_notMem_range'` is redundant. Its only use is `pairwise_baseOf_div_notMem` with `s := baseOf v f`, and its general-`s` form is `(pairwise_baseOf_div_notMem v hv_inv f hf).mono hst`. It also adds a primed name to the API.",
  "suggested_fix": "Delete `pairwise_div_notMem_range'` and prove `pairwise_baseOf_div_notMem` directly: `have hv_one : ∀ i, v i ≠ 1 := fun i ↦ by contrapose! hf; exact ⟨i, by simp [hf]⟩`; `refine pairwise_div_notMem_range v hv_one hv_inv _ {i | 1 < f (v i)} subset_rfl fun i ↦ ?_`; `simpa [hv_inv] using (hf i).symm` (checked: it compiles)."},
 {"path": IND, "line_start": 178, "severity": "advisory",
  "claim": "`IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` assumes `hf : ∀ i, f (v i) ≠ 1`, but the proof only uses `hf i` for the index `i` in the statement. The global hypothesis is stronger than needed.",
  "suggested_fix": "Weaken it to `{i : ι} (hf : f (v i) ≠ 1)` (or keep `i` explicit before `hf`) and use `lt_or_gt_of_ne hf` in the proof. This compiles (checked), and nothing else in the PR uses the lemma."},
 {"path": IND, "line_start": 181, "severity": "advisory",
  "claim": "The statement of `IsMulIndecomposable.mem_or_inv_mem_closure_baseOf` pads `     v i    ∈ ...` with alignment spaces. That is not Mathlib formatting.",
  "suggested_fix": "Write it as `v i ∈ Submonoid.closure (v '' baseOf v f) ∨\\n      (v i)⁻¹ ∈ Submonoid.closure (v '' baseOf v f)`, with single spaces and the usual continuation indent."},
 {"path": BE, "line_start": 53, "severity": "advisory",
  "claim": "In `section CommRing`, the variables `{S : Type*} [LinearOrder S] [AddCommGroup S] [IsOrderedAddMonoid S] (f : M →+ S)` serve only `baseOf_pairwise_pairing_le_zero`. `RootPairing.linearIndepOn_root_baseOf'` then rebinds `{S : Type*}` and `(f : Dual S M)`, shadowing both section variables with different meanings, which is confusing to read.",
  "suggested_fix": "Remove `S` and `f` (and their instances) from the `variable` line and put them in the binders of `baseOf_pairwise_pairing_le_zero`. This compiles as is, including the existing call `P.baseOf_pairwise_pairing_le_zero _ hf ...` (checked)."},
 {"path": BE, "line_start": 56, "severity": "advisory",
  "claim": "The name `RootPairing.baseOf_pairwise_pairing_le_zero` says `pairing`, but the statement is about `P.pairingIn ℤ i j`. Its word order also differs from the sibling it is proved from, `IsAddIndecomposable.pairwise_baseOf_sub_notMem`.",
  "suggested_fix": "Rename it to `RootPairing.pairwise_baseOf_pairingIn_le_zero` and update the use in `linearIndepOn_root_baseOf'`."},
 {"path": RP, "line_start": 208, "severity": "advisory",
  "claim": "`RootPairing.RootPositiveForm.posForm_apply_root_root_le_zero_iff` is the negation of the adjacent `zero_lt_apply_root_root_iff`, whose proof it rewrites with. It is the same statement shape with `≤ 0` for `0 <`, but the sibling has no `posForm_` prefix, so the pair is named inconsistently.",
  "suggested_fix": "Rename it to `apply_root_root_le_zero_iff`, matching `zero_lt_apply_root_root_iff`, and update the use in `RootPairing.linearIndepOn_root_baseOf'`."},
 {"path": BE, "line_start": 19, "severity": "advisory",
  "claim": "The module docstring of `Mathlib/LinearAlgebra/RootSystem/BaseExists.lean` has a garbled phrase (\"even though the existence ultimate statement does not\"). It also never says what the file proves: there is no main-results list, and the title promises existence of bases, which the file does not yet prove.",
  "suggested_fix": "Reword the phrase to \"even though the ultimate existence statement does not\". Add a `## Main results` section listing `RootPairing.baseOf_pairwise_pairing_le_zero`, `RootPairing.linearIndepOn_root_baseOf'` and `RootPairing.linearIndepOn_root_baseOf`, and say that existence itself is the TODO."},
]
notes = """Review of PR #33321, by changed object. Edits were checked with lean_verify_edit against the reviewed workspace.

- Mathlib.lean import: the new module is registered in sorted position. Nothing to ask.
- coe_invMonoidHom, invMonoidHom_apply (to_additive added), invMonoidHom_comp_invMonoidHom (new): the additive names `coe_negAddMonoidHom` and similar are not declared elsewhere, so there is no duplication. The new lemma's statement and simp attribute are fine, and `ext; simp` is acceptable. If the shorter Subgroup proof (finding 6) is adopted, these are no longer needed by the PR, but the attributes are harmless. Nothing to ask beyond finding 6.
- IsMulIndecomposable.subset: the statement is properly written with setOf, and `protected` is appropriate. `aesop` could be `fun _ h => h.1`, but it is not worth asking. Nothing to ask.
- IsMulIndecomposable.baseOf: the docstring is vague and the additive one misspells \"crystallographic\" (finding 2). The body uses a predicate as a `Set` (finding 3; the setOf form compiles). `[LinearOrder S]` from the section variable is more than the definition needs, but that is not worth an ask. The name and namespace are fine.
- IsMulIndecomposable.baseOf_subset_one_lt: fine. Nothing to ask.
- IsMulIndecomposable.image_baseOf_inv_comp_eq: `[IsOrderedMonoid S]` is unused (finding 5; compiled without it). It also becomes unnecessary once the Subgroup proof is simplified (finding 6).
- Submonoid.closure_image_isMulIndecomposable_baseOf: the rename needs a deprecated alias (finding 1, blocking; the old name exists at base). The proof still spells out `t` as the definition of `baseOf`, which is minor and not asked. The docstring is unchanged and still accurate.
- Subgroup.closure_image_isMulIndecomposable_baseOf: correct, but it has a much shorter pointwise proof via the Submonoid lemma (finding 6, compiled).
- Section variable change `{ι M G S} [CommGroup G] [LinearOrder S]` and the namespace IsMulIndecomposable block: fine.
- IsMulIndecomposable.pairwise_div_notMem_range: the hypothesis uses a predicate as a set (finding 4, compiled). The hypotheses are otherwise needed. The name is acceptable.
- IsMulIndecomposable.pairwise_div_notMem_range': redundant intermediate with a primed name (finding 7; the direct proof of pairwise_baseOf_div_notMem compiles).
- IsMulIndecomposable.pairwise_baseOf_div_notMem: the statement and name are fine. The proof is folded in per finding 7.
- IsMulIndecomposable.mem_or_inv_mem_closure_baseOf: the global `hf` is stronger than needed (finding 8, compiled), and there are alignment spaces in the statement (finding 9).
- Indecomposable.lean imports: the four new imports are not directly redundant (Order.Group.Basic does not import Order.Group.Defs directly, and Subgroup.Pointwise does not import Subgroup.Lattice directly). Nothing to ask.
- BaseExists.lean module doc: a garbled phrase and no main results (finding 13). Whether `@[expose]` belongs on a file with no definitions is unsettled on Zulip, so not asked.
- RootPairing.baseOf_pairwise_pairing_le_zero: `[CharZero R]` is needed (removing it fails at root_sub_root_mem_of_pairingIn_pos). The proof mirrors `Base.pairingIn_le_zero_of_ne` and is fine. The name says `pairing` for `pairingIn` and has inconsistent word order (finding 11). A citation-only docstring is acceptable.
- RootPairing.linearIndepOn_root_baseOf': the `[Module S N] [IsScalarTower S R N]` binders and the local `Fintype ι` are needed (removing them fails at posRootForm_rootFormIn_posDef). The docstring is good. The section variables `S`/`f` are shadowed (finding 10; moving them into the sibling lemma compiles).
- RootPairing.linearIndepOn_root_baseOf: `[Module ℚ N]` is needed by the primed lemma at `S = ℚ`. The proof is long but I found no concrete shortening. Nothing to ask.
- RootPairing.algebraMap_pairingIn': a tower version of `algebraMap_pairingIn`. The simp attribute is fine since `T` appears in the LHS. The naming census is inconclusive about the prime. Nothing to ask.
- RootPairing.pairingIn_rat: the new one-line proof via algebraMap_pairingIn' is a good golf. Nothing to ask.
- RootPairing.RootPositiveForm.posForm_apply_root_root_le_zero_iff: the proof and simp attribute mirror `zero_lt_apply_root_root_iff`. The name is inconsistent with that sibling (finding 12)."""
out = {"notes": notes, "findings": findings}
with open("/research/projects/proofedit/ya475/APE-Bench/.claude/worktrees/post-carryover-replan/results/pr_review_v5/probes/contract-2026-10-01/swap/pr33321/S1/submission.json", "w") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
