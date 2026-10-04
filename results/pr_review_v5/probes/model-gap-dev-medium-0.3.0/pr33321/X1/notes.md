# Review notes: PR #33321 (linear independence of indecomposable roots)

I read `pr.md`, `model.md` and `diff.patch`, then read the changed files as the PR leaves them
through `ptool file_read`. I ran `lean_verify_edit` with no edit on `Indecomposable.lean` and
`BaseExists.lean`: both compile with no warnings. Every edit proposed in `findings.json` was checked
with `lean_verify_edit`. Temporary argument files are in `tmp/`.

## Mathlib.lean
- The new import `Mathlib.LinearAlgebra.RootSystem.BaseExists` is in sorted position (BaseChange < BaseExists < Basic). No finding.

## Mathlib/Algebra/Group/Hom/Basic.lean
- `coe_invMonoidHom` and `invMonoidHom_apply` now carry `to_additive`. `invMonoidHom` already has `@[to_additive]`, so the generated names are `coe_negAddMonoidHom` and `negAddMonoidHom_apply`. declaration_search found no prior declaration under either name, so there is no clash. No finding.
- `invMonoidHom_comp_invMonoidHom`: the statement is sound and it is a reasonable simp lemma; `ext; simp` is fine. No finding.

## Mathlib/Algebra/Group/Irreducible/Indecomposable.lean
- Imports: I tried dropping `Subgroup.Lattice` and `Order.Group.Defs`. That broke `simp` calls, so neither import is redundant. No finding.
- `variable` line (adds `G`, `S`, `[CommGroup G] [LinearOrder S]`): fine. I considered asking to weaken `baseOf` to `[LT S]`/`[Preorder S]`, but it has too little value to raise. No finding.
- `IsMulIndecomposable.subset`: `by aesop` can be the term `fun _ h ↦ h.1` (verified). **Finding (advisory).**
- `IsMulIndecomposable.baseOf`:
  - The docstring has the typo "crystallogrphic" and does not describe the set. **Finding.**
  - The definition uses a predicate as a `Set` (defeq abuse; this workspace deprecates `Set.mem_def` for exactly that reason). A set-builder version compiles. **Finding (advisory)**, which also covers the `hst` hypotheses of the pairwise lemmas.
- `baseOf_subset_one_lt`: fine. No finding.
- `image_baseOf_inv_comp_eq`: the statement is correct. The proof is a brittle rewrite chain. An index-level lemma `inv_mem_baseOf_iff` plus a short `ext` proof compiles, and the Subgroup lemma downstream still compiles. **Finding (advisory, lower confidence).**
- `Submonoid.closure_image_isMulIndecomposable_baseOf`:
  - This renames `Submonoid.closure_image_one_lt_and_isMulIndecomposable`, which exists at base, and adds no deprecated alias. The additive old name is `AddSubmonoid.closure_image_pos_and_isAddIndecomposable`, confirmed by the compiler's deprecation warning. Explicit aliases for both names compile cleanly. **Finding (blocking).**
  - I tried replacing the local `let t` with `baseOf v f`. `grind [IsMulIndecomposable]` then fails without also unfolding `baseOf`, so I dropped it.
- `Subgroup.closure_image_isMulIndecomposable_baseOf`: the statement and hypotheses are all needed (`hf` for the split of `univ`, `hv_inv` for the negative half). No finding.
- `pairwise_div_notMem_range`, `pairwise_div_notMem_range'`, `pairwise_baseOf_div_notMem`:
  - The primed lemma is `(pairwise_baseOf_div_notMem ..).mono hst`, and its only use is the unprimed baseOf lemma. Removing it, and also dropping `s` from the general lemma, compiles. **Finding (advisory).**
  - I considered renaming `pairwise_baseOf_div_notMem` to `..._notMem_range` for consistency, but the evidence was too weak, so no finding.
- `mem_or_inv_mem_closure_baseOf`: the statement matches the `Base.root_mem_or_neg_mem` axiom shape. The spacing that aligns the two `∈` follows the author's alignment in `Base.lean`, so I raised nothing. No finding.

## Mathlib/LinearAlgebra/RootSystem/BaseExists.lean (new)
- Module doc:
  - Garbled phrase ('existence ultimate statement').
  - The title promises existence, which the file does not prove.
  - No Main results section (the sibling `Base.lean` has one).
  **Finding (advisory).** The declarations named in the TODO all exist at base (checked `Module.exists_dual_forall_apply_ne_zero`, `RootPairing.linearIndepOn_coroot_iff`, `RootPairing.restrictScalarsRat`).
- Imports: `Mathlib.Algebra.Module.Submodule.Union` is unused (the file compiles without it); it is only referenced in the TODO. **Finding (advisory).** `OrzechProperty` is needed: removing it breaks `linearIndependent_iff_card_eq_finrank_span`.
- Section `CommRing` variables: `S` and `f` serve only the first lemma and are shadowed by `linearIndepOn_root_baseOf'`. Moving them into the first lemma's signature compiles. **Finding (advisory).**
- `baseOf_pairwise_pairing_le_zero`:
  - The name says `pairing` but the statement uses `pairingIn`, and the word order differs from `pairwise_baseOf_sub_notMem`. The rename compiles. **Finding (advisory).**
  - I checked whether `[CharZero R]` could go: it cannot, since `root_sub_root_mem_of_pairingIn_pos` needs it.
- `linearIndepOn_root_baseOf'`:
  - I checked whether `[Module S N] [IsScalarTower S R N]` could go: they are needed, by `posRootForm`.
  - The docstring is adequate. No finding.
- `linearIndepOn_root_baseOf`: the headline theorem has no docstring. **Finding (advisory).** The `[Module ℚ M]` hypothesis is fine (the ℚ-scalar tower is found by instance). `replace this` inside the `let b` block shadows the `Fintype` instance, which is confusing but trivial, so no finding.

## Mathlib/LinearAlgebra/RootSystem/IsValuedIn.lean
- `algebraMap_pairingIn'`: the tower lemma is correct, and simp-confluent with `pairingIn_rat` and the cast normal form. The primed name is acceptable next to `algebraMap_pairingIn`. No finding.
- `pairingIn_rat`: the new one-line proof is fine. No finding.

## Mathlib/LinearAlgebra/RootSystem/RootPositive.lean
- `posForm_apply_root_root_le_zero_iff`: correct, and its form mirrors the sibling `zero_lt_apply_root_root_iff`. The `posForm_` prefix differs from the sibling, but naming_norm was insufficient_evidence, so no finding.

## Tools used
- file_read, file_search, content_search, declaration_search, naming_norm, precedent_search (no applicable precedents), zulip_search (background only), and lean_verify_edit (about 15 runs).
