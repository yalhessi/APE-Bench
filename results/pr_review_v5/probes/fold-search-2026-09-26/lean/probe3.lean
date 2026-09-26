import Mathlib
import Fold
set_option maxHeartbeats 4000000

section
variable {R : Type*} [CommRing R] (I : Ideal R)
#fold_try Submodule.isPrincipal_iff : "rhs" (∃ x : R, I = Ideal.span {x})
#fold_try Submodule.IsPrincipal.principal : "class" (∃ x : R, I = Ideal.span {x})
#fold_try Submodule.isPrincipal_iff : "rhs" (∃ x : R, I = Submodule.span R {x})
end

section
variable {E : Type*} [TopologicalSpace E] (A : Set E)
#fold_try IsSeqCompact : "def" (∀ x : ℕ → E, (∀ n, x n ∈ A) → ∃ a ∈ A, MapClusterPt a Filter.atTop x)
#fold_try IsCompact : "def" (∀ x : ℕ → E, (∀ n, x n ∈ A) → ∃ a ∈ A, MapClusterPt a Filter.atTop x)
end
