# Review notes: PR #43167 (reviewer E1)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools used through `./ptool`: file_read,
content_search, declaration_search, naming_norm, lean_verify_edit, precedent_search, zulip_search.
Every edit I propose was compiled with `lean_verify_edit` against the reviewed workspace.

## Mathlib/Algebra/Group/Subgroup/Pointwise.lean

- **import (added `Mathlib.GroupTheory.Commutator.Basic`)**: the file uses no commutator (a
  content_search for `commutator|⁅` finds nothing). With the import line removed, the file compiles
  cleanly. As a control, a bogus import gave an import error, so the tool really recompiles the
  header. -> finding (blocking).
- **`normalizer_inf_normalizer_le_normalizer_sup` (removed)**: moved to Subgroup/Basic under a new
  name, with deprecated aliases. Nothing wrong with the move itself.
- **`conj_mem_sup_of_mem_inf_normalizer_of_mem_inf`, `normalizer_le_normalizer_sup_of_normalizer_le_left`**:
  only the call is renamed to the new name. Both are fine.
- **`iInf_normalizer_le_normalizer_iSup` (unchanged, stays in Pointwise)**: it compiles verbatim
  in Subgroup/Basic beside the inf/iInf siblings, so moving only the binary version splits the
  family. -> advisory scope finding (targeted at the moved lemma).

## Mathlib/Algebra/Group/Subgroup/Basic.lean

- **`inf_normalizer_le_normalizer_sup`**: moved verbatim. The new name matches
  `inf_normalizer_le_normalizer_inf` and `iInf_normalizer_le_normalizer_iSup`. naming_norm says
  "emerging" for a `normalizer_` prefix (22 of 31), which is advisory at most. The rename brings the
  name in line with its direct siblings, so I do not ask for it to be undone. Explicit binders
  `(H K)` are kept because callers use them positionally and by dot notation. Fine.
- **deprecated aliases (multiplicative and `_root_.AddSubgroup` versions)**: correct. But one
  `@[to_additive (attr := deprecated (since := ...))] alias` generates both. This compiles, the
  additive alias is produced with the right deprecation message, and the pattern is in the base
  (e.g. Topology/Algebra/Group/Basic.lean). -> advisory style finding.

## Mathlib/GroupTheory/Commutator/Basic.lean

- **`commutator_mono_left` / `commutator_mono_right`**: the statements and names agree with
  `Ideal.mul_mono_left` and `Submodule.smul_mono_left` (vary the left argument), and they have
  `to_additive`. The `gcongr` tag is on the one-sided lemmas, though. Moving it to the two-sided
  `commutator_mono` compiles, and the file's `grw` steps still work. Mathlib's convention is to tag
  the two-sided lemma (`sup_le_sup` is tagged, `sup_le_sup_left` is not), and a 2025 maintainer
  announcement on Zulip says the one-sided tags are unnecessary. -> advisory finding.
- **`commutator_le_of_le`**: a correct one-liner (`commutator_le_sup.trans (sup_le h₁ h₂)`) with
  `to_additive`. declaration_search finds no existing equivalent. naming_norm could not resolve its
  subject. I found no sibling convention it clearly violates, so no finding.
- **`commutator_sup_left'` (private)**: the proof (via the quotient by `⁅H, N⁆ ⊔ ⁅K, N⁆` and
  `commutator_eq_bot_iff_le_centralizer`) is sound and short. The name has a prime where the
  differing hypothesis should be named, and it lacks `to_additive`, which the public lemma needs.
  -> advisory naming finding. Its `to_additive` is folded into the `commutator_sup_left` finding.
  The `Subgroup.` prefixes on `map_eq_bot_iff`, `commutator_eq_bot_iff_le_centralizer` (and
  `normal_subgroupOf_of_le_normalizer` in the main lemma) are redundant inside `namespace Subgroup`.
  Removing them compiles, but it is a minor nit and I did not file it.
- **`commutator_sup_left`**:
  - It has no `@[to_additive]`; adding it compiles and gives `AddSubgroup.addCommutator_sup_left`.
    -> blocking finding.
  - Normality of `N` is used only to get `⁅H, N⁆ ≤ N` and `⁅K, N⁆ ≤ N`.
    `le_normalizer_iff_commutator_le_right` gives these from `H, K ≤ normalizer N`. The
    generalized theorem compiles with a two-line change, and `commutator_sup_left` becomes a
    one-line corollary. precedent_search found PR #22650, where a reviewer asked for the same
    `[N.Normal]` -> `H ≤ N.normalizer` generalization. -> advisory generalization finding.
  - Naming: `commutator_X_left` matches the file's `commutator_bot_left` and
    `commutator_center_left`. The Lie analogue is `sup_lie`/`lie_sup`, but the local siblings
    decide, so no naming finding. declaration_search: no existing `commutator_sup`/`sup_commutator`,
    so it is not a duplicate.
  - I considered proof-golf and found no clearly shorter canonical route. No docstring request,
    since theorem docstrings are optional.
- **`commutator_sup_right`**: the one-line proof by `commutator_comm` is fine. It has no
  `@[to_additive]`; adding it compiles. -> blocking finding.

## Conventions checklist

- Unneeded import: the Pointwise import is flagged.
- Primes for variants: `commutator_sup_left'` is flagged.
- Names following siblings: checked `commutator_sup_left/right`, `commutator_mono_left/right`,
  `commutator_le_of_le` and `inf_normalizer_le_normalizer_sup`, and found no violation.
- Additive counterparts: `commutator_sup_left/right` are flagged. The other new declarations
  have `to_additive`.
