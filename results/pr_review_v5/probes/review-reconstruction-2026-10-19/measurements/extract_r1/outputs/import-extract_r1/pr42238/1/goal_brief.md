# Goal brief

## 1. Kind of contribution

Maintenance (variables and performance). No new mathematics; no statement is meant to change.

## 2. Capability

`Mathlib/Analysis/Normed/Operator/LinearIsometry.lean` opens with one file-wide `variable` block.
Besides the semirings R, R₂, R₃ and the seminormed modules E, E₂, E₃ over them, it declares a fourth
semiring R₄, a seminormed module E₄ over it, the six ring homomorphisms between R₄ and the other
rings (σ₁₄, σ₄₁, σ₂₄, σ₄₂, σ₃₄, σ₄₃), and 15 instance hypotheses on them: the structures on R₄ and
E₄, and the `RingHomInvPair` and `RingHomCompTriple` conditions involving R₄.

Only two declarations of the file use the fourth ring:
- `LinearIsometry.comp_assoc`: for semilinear isometries h : E → E₂, g : E₂ → E₃, f : E₃ → E₄,
  (f ∘ g) ∘ h = f ∘ (g ∘ h);
- `LinearIsometryEquiv.trans_assoc`: the same associativity for semilinear isometric equivalences
  E ≃ E₂, E₂ ≃ E₃, E₃ ≃ E₄.

Every other declaration is still elaborated with the fourth-ring data in its local context, so each
typeclass search there for `RingHomInvPair` or `RingHomCompTriple` has those local instances to
examine. The outcome sought: the fourth-ring data is in scope only where these two theorems need it,
and the module elaborates faster as a result.

## 3. What must keep working

- Every declaration of the file other than the two theorems keeps exactly its current type.
- `LinearIsometry.comp_assoc` and `LinearIsometryEquiv.trans_assoc` keep their names, statements,
  hypotheses and explicit arguments, at their current generality (four semirings linked by
  semilinear compatibility conditions).
- No declaration is removed or renamed; everything that uses the file keeps compiling.

## 4. Open questions

- Must the implicit and instance arguments of the two theorems keep their current order, or is it
  enough to keep their hypotheses and explicit arguments? Either reading is open.
- Should other rarely used variables of the file-wide block be scoped the same way? The inputs
  concern only the fourth ring.

## 5. Where the requirements come from

- Kind and capability: the title (the current title, not verified to be the one at review time),
  which marks a performance change and names the fourth-ring variables and their two users;
  description paragraph 1, which lists those variables, names the two theorems and states the cost
  to typeclass search; description paragraph 4, which measures the change by elaboration time.
- Exact types of the other declarations; hypotheses and explicit arguments of the two theorems:
  description paragraph 3.
- Nothing removed or renamed, one file only: the change itself, which touches only this file and
  adds no theorem.
- The description is present and verified to be the text at the start of review.
