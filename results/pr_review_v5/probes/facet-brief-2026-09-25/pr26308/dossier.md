# Dossier for PR #26308 (built deterministically from the diff; no review text)

Each changed object, with what changed, and the cells to check for its object kind (see the procedure).

## section in `Mathlib/Analysis/NormedSpace/Normalized.lean` (added)
- changed: namespace:added

## section in `Mathlib/Analysis/NormedSpace/Normalized.lean` (added)
- changed: namespace:added

## theorem: `normalized_smul_of_pos` (theorem, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem normalized_smul_of_pos {r : ℝ} (hr : 0 < r) (x : V) : normalized (r • x) = normalized x`
- siblings in this PR sharing a name token: `normalized_normalized`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## doc_comment in `Mathlib/Analysis/NormedSpace/Normalized.lean` (added)
- changed: documentation:added

## module_doc in `Mathlib/Analysis/NormedSpace/Normalized.lean` (added)
- changed: documentation:added

## theorem: `normalized_normalized` (theorem, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem normalized_normalized (x : V) : normalized (normalized x) = normalized x`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## theorem: `normalized_neg` (theorem, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem normalized_neg (x : V) : normalized (- x) = - normalized x`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## theorem: `normalized_eq_self_of_norm_eq_one` (lemma, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] lemma normalized_eq_self_of_norm_eq_one {x : V} (h : ‖x‖ = 1) : normalized x = x`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_neg`, `normalized_zero_eq_zero`, `normalized`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## section in `Mathlib/Analysis/NormedSpace/Normalized.lean` (added)
- changed: namespace:added

## theorem: `normalized_zero_eq_zero` (theorem, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] theorem normalized_zero_eq_zero : normalized (0 : V) = 0`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## import in `Mathlib.lean` (modified)
- changed: imports:added

## definition: `normalized` (def, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: attributes:added, name:added, statement_or_type:added, value_or_body:added
- header: `noncomputable def normalized (x : V) : V`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized_smul_of_neg`, `norm_normalized_eq_one_iff`

## theorem: `normalized_smul_of_neg` (theorem, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: name:added, proof:added, statement_or_type:added
- header: `theorem normalized_smul_of_neg {r : ℝ} (hr : r < 0) (x : V) : normalized (r • x) = - normalized x`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized`, `norm_normalized_eq_one_iff`

## theorem: `norm_normalized_eq_one_iff` (lemma, added)
- file: `Mathlib/Analysis/NormedSpace/Normalized.lean`
- changed: attributes:added, name:added, proof:added, statement_or_type:added
- header: `@[simp] lemma norm_normalized_eq_one_iff {x : V} : ‖normalized x‖ = 1 ↔ x ≠ 0`
- siblings in this PR sharing a name token: `normalized_smul_of_pos`, `normalized_normalized`, `normalized_neg`, `normalized_eq_self_of_norm_eq_one`, `normalized_zero_eq_zero`, `normalized`, `normalized_smul_of_neg`

## Removed declarations
none
