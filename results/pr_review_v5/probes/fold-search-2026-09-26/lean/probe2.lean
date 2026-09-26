import Mathlib
import Fold
set_option maxHeartbeats 4000000

#fold_stats

section
variable {A : Type*} [Group A] (B : Subgroup A)
-- v2022: analogue Subgroup.FiniteIndex
#fold B.index ≠ 0
end

section
variable {R : Type*} [CommRing R] (I : Ideal R)
-- v2163: analogue Submodule.IsPrincipal (one-field class)
#check @Submodule.IsPrincipal.principal
#check @Submodule.isPrincipal_iff
#fold_cands ∃ x : R, I = Ideal.span {x}
#fold ∃ x : R, I = Ideal.span {x}
#fold ∃ x : R, I = Submodule.span R {x}
end

section
variable (k : ℤ)
-- v1547: analogue Pi.single, with the carrier family as decoys; expect the function-level fold
#fold fun n : ℤ => if n = k then (1 : ℂ) else 0
end

section
open scoped Pointwise
variable {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (x : R)
-- v0157: analogue QuotSMulTop (a definition body)
#fold M ⧸ x • (⊤ : Submodule R M)
end

section
variable {τ α : Type*} [AddMonoid τ] [TopologicalSpace τ] [ContinuousAdd τ] [TopologicalSpace α] (ϕ : Flow τ α) (x : α)
-- v0575: MulAction.orbit is a role analogue; expect no shape fold
#fold {y | ∃ t : τ, ϕ t x = y}
end

section
variable {E : Type*} [TopologicalSpace E] (A : Set E)
-- v2006, the guard exemplar: the sequential form must NOT fold into IsSeqCompact-as-the-answer silently; report what it folds to
#fold ∀ x : ℕ → E, (∀ n, x n ∈ A) → ∃ a ∈ A, MapClusterPt a Filter.atTop x
end


section
-- o0069: the hypothesis shape of `Antitone` on a predicate
variable {n : ℕ} (p : Fin n → Prop)
#fold ∀ i j : Fin n, j ≤ i → p i → p j
end

section
-- 34091: a hypothesis whose type is a class; and an un-simp that must not appear
variable {α : Type*} [Monoid α] (x : α) (k : ℕ)
#fold x ^ k
end
