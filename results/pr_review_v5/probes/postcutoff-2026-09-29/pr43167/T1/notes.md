# Review notes: PR #43167 (reviewer T1)

I read pr.md, model.md and diff.patch. I then used `ptool` to read the three changed files as the PR
leaves them, and checked every proposed edit with `lean_verify_edit`. To confirm that the verifier
really rejects bad code, I submitted a deliberately wrong `rfl` proof of `commutator_sup_right`; it
came back as `compile_errors`.

## Mathlib/Algebra/Group/Subgroup/Basic.lean
- `Subgroup.inf_normalizer_le_normalizer_sup` (moved and renamed). The statement and proof are
  unchanged from the Pointwise original. The new name matches its neighbours
  `inf_normalizer_le_normalizer_inf`, `iInf_normalizer_le_normalizer_iInf` and
  `iInf_normalizer_le_normalizer_iSup`. `naming_norm` gave only an "emerging" `normalizer_` lead with
  meaningless candidates, so I raised no naming ask. It differs slightly from its sibling (explicit
  `(H K)` and `(H ⊔ K : Subgroup G)` rather than `(H ⊔ K :)`). Changing that would break the explicit
  call sites, so no ask.
- Deprecated aliases. The date 2026-08-27 matches the push date (`as_of` in the precedent and Zulip
  tools). Searching `target/Mathlib` finds no remaining uses of the old name. Finding (advisory nit):
  collapse the two aliases into one `@[to_additive (attr := deprecated ...)] alias`. This was
  verified, including that the additive alias is generated and warns correctly.
- Scope finding (advisory): `iInf_normalizer_le_normalizer_iSup` stayed in Pointwise.lean. Moving it
  next to the binary lemma compiles in Basic.lean.

## Mathlib/Algebra/Group/Subgroup/Pointwise.lean
- New `public import Mathlib.GroupTheory.Commutator.Basic`. The file compiles without it and never
  mentions commutators. Finding: remove it (blocking).
- `conj_mem_sup_of_mem_inf_normalizer_of_mem_inf` and
  `normalizer_le_normalizer_sup_of_normalizer_le_left` only swap in the renamed lemma. They are
  correct, with nothing to ask.

## Mathlib/GroupTheory/Commutator/Basic.lean
- `commutator_mono_left` and `commutator_mono_right`. These are new; `declaration_search` finds no
  base duplicate. The names match the `smul_mono_left` and `mono_lie_left` pattern, so they are fine.
  Finding (advisory): put `gcongr` on the two-argument `commutator_mono` instead, following
  `LieSubmodule.mono_lie`. I verified that the PR's one-sided `grw` steps still work that way.
- `commutator_le_of_le`. This is new and has no base duplicate. `naming_norm` could not resolve its
  subject. I thought about asking for `_of_le_of_le` or for inlining it, but found no convention to
  cite, so I made no request. It is a fine one-liner.
- `commutator_sup_left'` (private) and `commutator_sup_left`. The maths is correct and the proof
  compiles. Finding (advisory proof-golf): a direct proof by `closure_induction` that removes the
  private helper and the `subgroupOf`/quotient transfer. It was verified, both with and without
  `@[to_additive]`. The name `commutator_sup_left` follows the file's `commutator_bot_left` and
  `commutator_center_left` convention (the suffix gives the position of the special argument), so
  no naming ask.
- `commutator_sup_right`. The proof by `commutator_comm` is fine.
- `@[to_additive]` is missing on `commutator_sup_left` and `commutator_sup_right`. Adding it compiles.
  Two advisory findings, one per declaration.
- Considered and not raised:
  - Generalization: weaken `[N.Normal]` to `H ≤ normalizer N`, `K ≤ normalizer N`. The elementwise
    proof only uses `L ≤ N`, but this is speculative API churn, so I did not raise it.
  - Docstrings for the new theorems: comparable theorems in this file carry none.
  - `@[simp]`, as on the Lie analogues `sup_lie` and `lie_sup`: not clearly wanted with an
    instance-hypothesis lemma.
  - An `iSup` version: not needed for this PR.
  - Redundant `Subgroup.` prefixes inside `namespace Subgroup` in the helper: these go away with the
    proof rewrite, and some may be needed for disambiguation.

## Tool calls
- `file_read`: Commutator/Basic.lean, Pointwise.lean (header and lines 310-375), Basic.lean (header
  and lines 500-560), and the headers of ConjAct, Centralizer and QuotientGroup.Defs.
- `declaration_search`: the new names, the induction principles and the helper lemmas.
- `naming_norm`: four of the new declarations.
- `content_search`: importers, `gcongr` conventions (Subgroup and Lie), deprecated-alias
  conventions, and uses of the old name.
- `precedent_search` on the quotient helper: nothing applicable.
- `zulip_search` on commutator/sup distributivity: nothing applicable.
- `lean_verify_edit`: seven edits, six compiled. The seventh was the deliberate `rfl` failure, used
  as the sanity check.
