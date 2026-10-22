# Goal brief

## 1. Kind of contribution

Proof changes only.

## 2. Capability

Shorter ("golfed") proofs of eight existing results, none of whose statements changes:

- `Finset.mem_map_equiv` (`Mathlib/Data/Finset/Image.lean`): for an equivalence f : α ≃ β, b lies in the image of s under f iff f⁻¹(b) ∈ s.
- `Rat.inv_intCast_den_of_pos` (`Mathlib/Data/Rat/Lemmas.lean`): for an integer a > 0, the denominator of 1/a, read as an integer, is a.
- `MeasureTheory.Measure.pi_map_piCongrLeft` (`Mathlib/MeasureTheory/Constructions/Pi.lean`): for e : ι ≃ ι' with ι' finite and σ-finite μⱼ, the pushforward of ⊗ᵢ μ_{e(i)} along the induced reindexing of product spaces is ⊗ⱼ μⱼ.
- `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'` (`Mathlib/MeasureTheory/Measure/Portmanteau.lean`): along a countably generated filter, probability measures μᵢ converge to μ if limsupᵢ μᵢ(F) ≤ μ(F), as real numbers, for every closed F.
- `limsup_finset_sup'` (`Mathlib/Order/LiminfLimsup.lean`): in a conditionally complete linear order, under its boundedness hypotheses, the limsup of a pointwise supremum over a nonempty finite set is the supremum of the limsups.
- The two `setLIntegral_condKernel_eq_measure_prod` lemmas (`Mathlib/Probability/Kernel/Disintegration/Integral.lean`, kernel and measure versions): for measurable s, t, integrating the conditional kernel's mass of t over s against the first marginal gives the mass of s × t.
- `Metric.exists_lt_mem_ball_of_mem_ball` (`Mathlib/Topology/MetricSpace/Pseudo/Defs.lean`): if x ∈ B(y, ε), then x ∈ B(y, ε') for some ε' < ε.

## 3. What must keep working

- Each of the eight declarations keeps its name, hypotheses, conclusion, attributes, docstring and comments, including the raised simp priority of `Finset.mem_map_equiv`.
- Every existing use still compiles, for instance `Rat.inv_natCast_den_of_pos`, whose proof rewrites with `Rat.inv_intCast_den_of_pos`.

## 4. Open questions

- Brevity or speed: the description reports each proof's elaboration time before and after. The inputs do not say whether the aim is shorter proofs, faster proofs or both, nor whether a shorter but slower proof is acceptable.
- Whether each proof is to be rewritten whole or in part.
- Which proof techniques are preferred, and whether new helper lemmas or imports are in scope.
- Whether the task stops at proofs, or may also turn a declaration into an alias, deprecate it or generalize it.
- Whether other proofs in the same files belong here. The description places this change in a series of size-limited golfing PRs.

## 5. Where the requirements come from

- The golfing aim: the title, which calls the change a golf (the current title, not verified to be the one at review time).
- The eight declarations: the change itself, which modifies exactly these proofs; the description's first paragraph names seven of them.
- Statements, attributes and docstrings preserved: the change itself, which alters no statement.
- The use in `Rat.inv_natCast_den_of_pos`: the change itself, where it appears as unchanged context.
- Elaboration time as a reported dimension: the description's first paragraph.
