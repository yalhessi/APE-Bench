## Kind of contribution
Proof changes only, as maintenance. The PR revises proofs of eight existing results; it does not add, remove, rename, or change the statements of results.

## Capability
No new mathematical result or API capability is asserted. The contribution is to revise the proof implementations while retaining the existing results. The affected results concern finset membership under an equivalence, a denominator identity for the inverse of a positive integer cast to the rationals, reindexing product measures, a closed-set criterion for convergence of probability measures, a limsup identity for finite suprema, conditional-kernel integrals over measurable rectangles (in both measure and kernel settings), and the existence of a smaller-radius metric ball containing a point already in a given ball.

## What must keep working
The statements and conclusions of `Finset.mem_map_equiv`, `Rat.inv_intCast_den_of_pos`, `MeasureTheory.Measure.pi_map_piCongrLeft`, `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'`, `limsup_finset_sup'`, `MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod`, `ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod`, and `Metric.exists_lt_mem_ball_of_mem_ball` must remain available and valid. Their current hypotheses and conclusions must be retained.

## Open questions
The inputs do not establish a required proof style, a target for proof length or compilation time, or a generalization beyond these existing statements. Before-and-after trace timings are supplied for some results, but they do not settle whether such timings are requirements or what tradeoff is acceptable. The intended scope beyond the listed proof revisions is not specified.

## Where the requirements come from
The maintenance/proof-only characterization and preservation of the existing claims come from the diff: it changes proofs of the listed declarations without changing their statements, and the model records no additions, removals, or renames. The current title, not verified to be the title at review time, also presents this as a chore. The description includes profiling data; it does not set a mathematical generality or a required performance target. The list of existing results above identifies the places whose proofs the diff modifies.
