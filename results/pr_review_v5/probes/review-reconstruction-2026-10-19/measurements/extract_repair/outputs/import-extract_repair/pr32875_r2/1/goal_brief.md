# Goal brief

## 1. Kind of contribution

Proof changes only. The proofs of eight existing declarations, spread over seven existing files, are
rewritten; no declaration is added, removed or restated.

## 2. Capability

Shorter, simpler proofs (a "golf") of these existing results:

- `Finset.mem_map_equiv`: for an equivalence f : α ≃ β, b lies in the image of a finset s under f
  iff f⁻¹(b) ∈ s.
- `Rat.inv_intCast_den_of_pos`: for an integer a > 0, the denominator of the rational 1/a is a.
- `MeasureTheory.Measure.pi_map_piCongrLeft`: reindexing along an equivalence e : ι ≃ ι' carries
  the finite product measure ∏ᵢ μ_{e(i)} to ∏ⱼ μⱼ.
- `MeasureTheory.tendsto_of_forall_isClosed_limsup_real_le'`: probability measures μᵢ converge to μ
  along a countably generated filter if limsup μᵢ(F) ≤ μ(F), as real numbers, for every closed F.
- `limsup_finset_sup'`: in a conditionally complete linear order, under the stated boundedness
  hypotheses, the limsup of a pointwise sup over a nonempty finset is the sup of the limsups.
- `ProbabilityTheory.setLIntegral_condKernel_eq_measure_prod` and
  `MeasureTheory.Measure.setLIntegral_condKernel_eq_measure_prod`: integrating the conditional
  kernel's mass of t over s against the first marginal gives the mass of s × t (kernel and measure
  versions).
- `Metric.exists_lt_mem_ball_of_mem_ball`: if x ∈ B(y, ε), then x ∈ B(y, ε') for some ε' < ε.

## 3. What must keep working

- The statements of all eight declarations: their names, hypotheses and conclusions.
- Every existing use of them keeps compiling, for example the proof of
  `Rat.inv_natCast_den_of_pos`, which rewrites with `Rat.inv_intCast_den_of_pos`.

## 4. Open questions

- What counts as better: shorter proofs, with elaboration time merely reported; faster elaboration
  as a goal too; or shorter proofs provided none becomes noticeably slower. The inputs report
  timings without saying which.
- How far to rewrite each proof, wholesale or in part. The inputs do not constrain the proof
  methods or which library results a proof may use.
- Scope: the contribution is one batch of a golfing series with size guidelines. Whether these
  eight proofs belong together, or more or fewer should be included, is open.
- Whether anything beyond the proofs may change (say, a hypothesis a new proof no longer needs, or
  an attribute) is not stated.

## 5. Where the requirements come from

- Kind, the eight declarations, unchanged statements: the change itself (it modifies only the
  proofs of these existing declarations).
- "Golf": the title, which is the current title, not verified to be the one at review time.
- Timings: the description's first paragraph (trace profiling of these declarations before and
  after); the description is verified as the text at the start of review.
- Batching and size guidelines: the description's second paragraph.
- Uses keep compiling: the change itself, which leaves untouched the proof of
  `Rat.inv_natCast_den_of_pos` that follows the changed lemma.
