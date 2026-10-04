# Review notes: PR #43167 (commutator distributes over sup when N is normal)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools used, all through `ptool`: file_read,
file_search, content_search, declaration_search, naming_norm, precedent_search, zulip_search and
lean_verify_edit. Scratch Lean snippets are in `tmp/`.

## Mathlib/Algebra/Group/Subgroup/Basic.lean

- `Subgroup.inf_normalizer_le_normalizer_sup` (moved here from Pointwise and renamed). The new name
  matches the neighbouring `inf_normalizer_le_normalizer_inf`. naming_norm says `emerging`, with
  `normalizer_` leading, but its candidate names are nonsense. There is no naming finding. The proof
  is moved verbatim and is fine. The explicit `(H K : Subgroup G)` binders are needed by the
  dot-notation callers in Pointwise.
  Finding (advisory, scope): the indexed counterpart `iInf_normalizer_le_normalizer_iSup` was left
  in Pointwise. It compiles unchanged in Basic, right after the binary lemma (lean_verify_edit:
  success).
- Deprecated aliases for the multiplicative and additive old names. Each has `since`, and the
  additive one uses `_root_.AddSubgroup...`, the usual safe pattern (separate aliases, not
  `to_additive` plus `deprecated`). Nothing to ask.

## Mathlib/Algebra/Group/Subgroup/Pointwise.lean

- New `public import Mathlib.GroupTheory.Commutator.Basic`. Pointwise.lean has no commutator
  usage (content_search: 0 matches). Removing the import compiles (lean_verify_edit: success). A
  control with a bogus import fails, so the verifier does check the header.
  Finding (blocking): drop the import.
- `conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` and
  `normalizer_le_normalizer_sup_of_normalizer_le_left` only follow the rename. Fine.
- Removal of `normalizer_inf_normalizer_le_normalizer_sup`. Covered by the deprecated aliases in
  Basic.

## Mathlib/GroupTheory/Commutator/Basic.lean

- `commutator_mono_left` / `commutator_mono_right`. The names match the analogous one-sided lemmas
  `Ideal.mul_mono_left`, `Submodule.smul_mono_left` and `LieSubmodule.mono_lie_left`. The
  `@[to_additive (attr := gcongr)]` attribute is right. Checked in the PR state: `gcongr` cannot
  prove `⁅A, C⁆ ≤ ⁅B, D⁆` ("did not make progress"). Tagging `commutator_mono` with gcongr as well
  fixes that (verified). Finding (advisory, style/attribute).
- `commutator_le_of_le`. It is correct, has `@[to_additive]`, and duplicates nothing
  (declaration_search: new). naming_norm could not measure the name (`subject_unresolved`). The
  `_of_le` suffix is vague, but I have no evidence for a preferred spelling, so there is no finding.
  If the direct proof below is adopted, the PR no longer uses it. It is harmless API either way.
- `commutator_sup_left'` (private helper) and `commutator_sup_left`. The statement is correct and
  new (declaration_search: no `commutator_sup*` / `sup_commutator` in base). The name matches local
  siblings (`commutator_bot_left`, `commutator_top_left_*`); Lie algebras use `sup_lie` / `lie_sup`,
  but the file's own convention wins.
  Finding (blocking): missing `@[to_additive]`. With it added to the helper and both lemmas, the
  file compiles and generates `AddSubgroup.addCommutator_sup_left`.
  Finding (advisory, proof-golf): a direct closure-induction proof over `H ⊔ K`. It uses the
  normaliser fact plus `commutatorElement_mul_left_eq_conj_mul` / `commutatorElement_inv_left`,
  compiles, and makes the private quotient helper, the `subgroupOf` / `convert` transport and the
  five containment `have`s unnecessary.
  In the private helper, the `Subgroup.` prefixes on `map_eq_bot_iff` and
  `commutator_eq_bot_iff_le_centralizer` are redundant inside `namespace Subgroup`; dropping them
  compiles. I did not file this separately, because the golf finding removes the helper entirely.
  Generalization considered but not filed: the proof only uses `[N.Normal]` to get
  `⁅H, N⁆ ≤ N` and `⁅K, N⁆ ≤ N`, so the result also holds when `H` and `K` normalise `N`, via
  `le_normalizer_iff_commutator_le_right`. The rest of the file states such lemmas with `Normal`
  instances, and I have no evidence a maintainer would ask, so I left it out.
- `commutator_sup_right`. The one-line proof via `commutator_comm` is fine.
  Finding (blocking): missing `@[to_additive]` (verified: `AddSubgroup.addCommutator_sup_right`).
- Docstrings: the new theorems have none. That is optional for theorems in Mathlib, so no finding.

Precedent and Zulip searches turned up nothing specific to this change.
