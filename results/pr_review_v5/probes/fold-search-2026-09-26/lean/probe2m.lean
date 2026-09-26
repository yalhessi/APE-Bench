module

public import Mathlib
import Fold

set_option maxHeartbeats 4000000

section
variable {A : Type*} [Group A] (B : Subgroup A)
#fold B.index ≠ 0
end

section
variable (k : ℤ)
#fold fun n : ℤ => if n = k then (1 : ℂ) else 0
end

section
variable {R : Type*} [CommRing R] (I : Ideal R)
#fold ∃ x : R, I = Ideal.span {x}
end
