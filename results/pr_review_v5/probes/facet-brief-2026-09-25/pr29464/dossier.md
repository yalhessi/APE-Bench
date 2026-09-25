# Dossier for PR #29464 (built deterministically from the diff; no review text)

Each changed object, with what changed, and the cells to check for its object kind (see the procedure).

## module_doc in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## theorem: `AkraBazziRecurrence.smoothingFn_mul_asympBound_isBigO_T` (lemma, modified)
- file: `Mathlib/Computability/AkraBazzi/AkraBazzi.lean`
- changed: documentation:modified, proof:modified
- header: `lemma smoothingFn_mul_asympBound_isBigO_T : (fun (n : ℕ) => (1 + ε n) * asympBound g a b n) =O[atTop] T`
- siblings in this PR sharing a name token: `AkraBazziRecurrence.T_isBigO_smoothingFn_mul_asympBound`

## module_doc in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (removed)
- changed: documentation:removed

## doc_comment in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## definition: `AkraBazziRecurrence` (structure, modified)
- file: `Mathlib/Computability/AkraBazzi/SumTransform.lean`
- changed: documentation:modified, value_or_body:modified
- header: `structure AkraBazziRecurrence {α : Type*} [Fintype α] [Nonempty α] (T : ℕ → ℝ) (g : ℝ → ℝ) (a : α → ℝ) (b : α → ℝ) (r : α → ℕ → ℕ) where /-- Point below which the recurrence is in the base case -/ n₀ : ℕ /-- `n₀` is positive. -/ n₀_gt_zero : 0 < n₀ /-- The coefficients `a i` are positive. -/ a_pos : ∀ i, 0 < a i /-- The coefficients `b i` are positive. -/ b_pos : ∀ i, 0 < b i /-- Each `b i` is les`
- siblings in this PR sharing a name token: none

## module_doc in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## theorem: `AkraBazziRecurrence.T_isBigO_smoothingFn_mul_asympBound` (lemma, modified)
- file: `Mathlib/Computability/AkraBazzi/AkraBazzi.lean`
- changed: documentation:modified, proof:modified
- header: `lemma T_isBigO_smoothingFn_mul_asympBound : T =O[atTop] (fun n => (1 - ε n) * asympBound g a b n)`
- siblings in this PR sharing a name token: `AkraBazziRecurrence.smoothingFn_mul_asympBound_isBigO_T`

## doc_comment in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/GrowsPolynomially.lean` (modified)
- changed: documentation:modified

## module_doc in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/SumTransform.lean` (modified)
- changed: documentation:modified

## doc_comment in `Mathlib/Computability/AkraBazzi/AkraBazzi.lean` (modified)
- changed: documentation:modified

## Removed declarations
none
