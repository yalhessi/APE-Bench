# Review notes: PR #33321 (linear independence of indecomposable roots)

Inputs read: `brief.md`, `pr.md`, `model.md`, `diff.patch`. The workspace files live under
`target/` in the tool sandbox. `lean_verify_edit` with no edit reports that
`Indecomposable.lean` compiles as the PR leaves it. Every proposed edit below was checked with
`lean_verify_edit` (whole-file recompilation, `to_additive` counterparts included). Scratch argument
files are in `tmp/`.

## Mathlib/Algebra/Group/Hom/Basic.lean

- `coe_invMonoidHom`, `invMonoidHom_apply` (`@[simp]` -> `@[to_additive (attr := simp)]`): these
  are fine. The additive names do not clash (content_search on `negAddMonoidHom`). No finding.
- `invMonoidHom_comp_invMonoidHom`: statement and proof (`ext; simp`) are fine and nothing like it
  already exists (content_search `invMonoidHom`). Its only consumer is
  `image_baseOf_inv_comp_eq`, which becomes unnecessary under the Subgroup reproof (finding 2), so
  I mention it there and did not file it separately.

## Mathlib/Algebra/Group/Irreducible/Indecomposable.lean

- Imports: I removed each added import one at a time. `Subgroup.Lattice` and `Order.Group.Basic`
  can go (together too). `Subgroup.Pointwise` and `Order.Group.Defs` are needed as the PR stands.
  After the Subgroup reproof, `Pointwise` can go and `Lattice` is needed. Filed as a finding.
- Module docstring is only a title. Filed as an advisory finding.
- Variable line `[CommGroup G]`: `[Group G]` fails only in `image_baseOf_inv_comp_eq` and the
  Subgroup lemma, which need `DivisionCommMonoid` for `invMonoidHom`. After the restructure,
  `[Group G]` compiles the whole file. Filed as a generalization finding.
- `IsMulIndecomposable.subset`: `by aesop` can be `fun _ h ↦ h.1` (compiles). Filed as a minor
  proof-golf finding.
- `IsMulIndecomposable.baseOf`: the body is a predicate used as a Set by defeq. I showed that simp
  gets stuck on membership with it (even with `mem_def`), and that the set-builder body compiles
  the whole file. Filed as a finding. Separately, the additive docstring has the typo
  "crystallogrphic" and the multiplicative docstring is uninformative (documentation finding).
- `IsMulIndecomposable.baseOf_subset_one_lt`: fine. Nothing to ask.
- `IsMulIndecomposable.image_baseOf_inv_comp_eq`: its sole use is the Subgroup lemma. I proved an
  index-level replacement `i⁻¹ ∈ baseOf v f ↔ i ∈ baseOf v (invMonoidHom.comp f)` (7 lines, needs
  the set-builder `baseOf`) and rederived the image form from it in 6 lines. Both compile. The
  better change is to delete it (finding 2). The fallback goes in finding 2's text.
- `Submonoid.closure_image_isMulIndecomposable_baseOf`: renamed with no deprecated alias. The old
  name exists at base and has no remaining uses. Both aliases compile without warnings. Filed as
  **blocking**. The proof change (`by aesop` -> `baseOf_subset_one_lt`) is fine. Its internal
  `let t` could be `baseOf v f`, but that is not worth asking.
- `Subgroup.closure_image_isMulIndecomposable_baseOf`: reproved in 5 lines from
  `mem_or_inv_mem_closure_baseOf` (moved after the namespace block). The whole file compiles.
  Filed as proof-golf/scope, subsuming the removal of `image_baseOf_inv_comp_eq`.
- `pairwise_div_notMem_range`: dropping `s`/`hst` and using a 5-line proof compiles. Filed.
- `pairwise_div_notMem_range'`: redundant (it is `.mono` of `pairwise_baseOf_div_notMem`) and
  used only once. Deleting it and proving `pairwise_baseOf_div_notMem` directly compiles. Filed.
- `pairwise_baseOf_div_notMem`: fine apart from the restructure above.
- `mem_or_inv_mem_closure_baseOf`: the maths and proof are fine. The statement has manual
  alignment padding, and the reformatted version compiles. Filed as a minor style finding.
  `lt_or_gt_of_ne` is not deprecated (it is `Order/Defs/LinearOrder.lean:124`). No finding.
- Naming: `naming_norm` gave `insufficient_evidence` for every new name here (mostly
  `subject_unresolved`), so I filed no naming findings for this file.

## Mathlib/LinearAlgebra/RootSystem/BaseExists.lean (new)

- Imports: `Submodule.Union` can be removed (it is only referenced from the TODO).
  `OrzechProperty` is needed (`linearIndependent_iff_card_eq_finrank_span`). Filed.
- `@[expose] public section`: Zulip (Nov 2025, Kim Morrison) recommends it for new files. No
  finding.
- Module docstring: the word-order typo "existence ultimate statement", and there is no
  main-results section. Filed. The declarations its TODO cites all exist at base
  (`Module.exists_dual_forall_apply_ne_zero`, `RootPairing.linearIndepOn_coroot_iff`,
  `RootPairing.restrictScalarsRat`). `IsAddIndecomposable.mem_or_neg_mem_closure_baseOf` is the
  `to_additive` name of the PR's lemma.
- The CommRing section's variables `S`/`f` are shadowed by the primed lemma's own `S`/`f`. Moving
  them into `baseOf_pairwise_pairing_le_zero` compiles. Filed.
- `baseOf_pairwise_pairing_le_zero`: `[CharZero R]` is needed (removing it fails in
  `root_sub_root_mem_of_pairingIn_pos`). The name says `pairing` although the lemma is about
  `pairingIn ℤ`, while the direct `Base` analogue is `Base.pairingIn_le_zero_of_ne`. Filed as an
  advisory naming finding. naming_norm had no population for the prefix.
- `linearIndepOn_root_baseOf'`: `[P.IsValuedIn S]` is derivable from `[P.IsCrystallographic]`, and
  dropping it compiles. Filed. `[Module S N] [IsScalarTower S R N]` and `Fintype ι` cannot be
  removed (`posRootForm S` needs them). The docstring is fine.
- `linearIndepOn_root_baseOf`: `[P.IsRootSystem]` is needed (`finrank_rootSpanIn`). There is no
  docstring on the file's main result (filed). The `replace this` inside `h_card` repurposes the
  `Fintype` instance's name, and a named `have hli` compiles (filed).

## Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean

- `algebraMap_pairingIn'`: a sound tower generalization of `algebraMap_pairingIn`, and fine as a
  simp lemma since `T` is determined by the LHS. The prime name is acceptable. naming_norm:
  insufficient evidence. No finding.
- `pairingIn_rat`: the golf to `simp [← P.algebraMap_pairingIn' ℚ ℤ]` is good. No finding.

## Mathlib/LinearAlgebra/RootSystem/RootPositive.lean

- `posForm_apply_root_root_le_zero_iff`: correct, and it mirrors `zero_lt_apply_root_root_iff`
  (same autoParam binders, same `@[simp]`). Its name includes `posForm_` where that sibling does
  not, but other siblings (`zero_lt_posForm_apply_root`) do include it, so the local convention
  is mixed. naming_norm: insufficient evidence. No finding.

## Mathlib.lean

- The import line is added in sorted position. No finding.

## Tools used

`file_read`, `file_search`, `content_search`, `declaration_search`, `naming_norm` (8
declarations), `zulip_search` (twice), `precedent_search` (once, nothing relevant), and
`lean_verify_edit` (about 30 runs).
