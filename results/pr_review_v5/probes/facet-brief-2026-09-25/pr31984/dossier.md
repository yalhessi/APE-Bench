# Dossier for PR #31984 (built deterministically from the diff; no review text)

Each changed object, with what changed, and the cells to check for its object kind (see the procedure).

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## definition: `FiniteProbability.single` (def, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `def single {ι : Type v} (i : ι) : FiniteProbability R ι where weights`
- siblings in this PR sharing a name token: none

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## definition: `FiniteProbability.comp` (def, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: documentation:added, name:added, statement_or_type:added, value_or_body:added
- header: `def comp (f : FiniteProbability R κ) (g : (k : κ) → FiniteProbability R (ι k)) : FiniteProbability R (Σ k, ι k) where weights`
- siblings in this PR sharing a name token: none

## attribute in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: unknown:added

## definition: `FiniteProbability.duple` (def, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `def duple {s t : R} (hs : 0 ≤ s) (ht : 0 ≤ t) (h : s + t = 1) : FiniteProbability R (Fin 2) where weights`
- siblings in this PR sharing a name token: none

## import in `Mathlib.lean` (modified)
- changed: imports:added

## definition: `convexCombo₂` (def, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: name:added, statement_or_type:added, value_or_body:added
- header: `def convexCombo₂ (s t : R) (hs : 0 ≤ s) (ht : 0 ≤ t) (h : s + t = 1) (x y : M) : M`
- siblings in this PR sharing a name token: none

## namespace in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## command in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: value_or_body:added

## module_doc in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## namespace in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## namespace in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## definition: `ConvexSpace` (class, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: documentation:added, name:added, statement_or_type:added, value_or_body:added
- header: `class ConvexSpace (R : Type u) (M : Type v) [PartialOrder R] [Semiring R] [IsStrictOrderedRing R] where /-- Take a convex combination of a family of points with the given probability distribution. -/ convexCombination {ι : Type v} (f : FiniteProbability R ι) (xs : ι → M) : M /-- Associativity of convex combination. -/ assoc {κ : Type v} (f₀ : FiniteProbability R κ) {ι : κ → Type v} (f₁ : (k : κ) →`
- siblings in this PR sharing a name token: none

## section in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## definition: `FiniteProbability` (structure, added)
- file: `Mathlib/LinearAlgebra/ConvexSpace.lean`
- changed: documentation:added, name:added, statement_or_type:added, value_or_body:added
- header: `structure FiniteProbability (R : Type u) [LE R] [AddCommMonoid R] [One R] (ι : Type v) extends weights : ι →₀ R where /-- All weights are non-negative. -/ nonneg : ∀ m, 0 ≤ weights m /-- The weights sum to 1. -/ total : weights.sum (fun _ r => r) = 1`
- siblings in this PR sharing a name token: none

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## doc_comment in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: documentation:added

## section in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## section in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: namespace:added

## command in `Mathlib/LinearAlgebra/ConvexSpace.lean` (added)
- changed: value_or_body:added

## Removed declarations
none
