# Review notes: PR #26185 (Peano curve)

I read `pr.md`, `model.md` and `diff.patch`, ran `ptool describe`, and then went through the targets
one at a time. All tool calls went through `./ptool`. Scratch argument files are in `tmp/`.

As the PR leaves it, `Counterexamples/PeanoCurve.lean` compiles (`lean_verify_edit` with no edit:
compiles, no errors, no warnings).

## `import in Counterexamples.lean`
`import Counterexamples.PeanoCurve` sits between `OrderedCancelAddCommMonoidWithBounds` and
`Phillips`, which is alphabetical. No finding.

## `module_doc in PeanoCurve.lean`
It has typos ("existsence", "sujrective"), a missing article, no blank line after the title and no
Main results list. The sibling `Counterexamples/TopologistsSineCurve.lean` has both. Finding 1. The
corrected text compiled as part of a combined lines 9-38 edit.

## `open scoped unitInterval` / file-level namespace
Both declarations are at the root. 23 of the 28 Counterexamples files open a namespace, including
the topology sibling `TopologistsSineCurve`. Finding 7 (advisory). Wrapping in
`namespace PeanoCurve` compiles.

## `exists_long_peano_curve`
- Documentation: "maps the Cantor set to the square" understates `SurjOn`, so it should say "onto".
  Finding 2.
- Proof: the `let g'`/`have hg'` scaffolding and the closing `← coe_restrict` simp can go. The
  continuity goal is `by fun_prop`, surjectivity is `hg'.comp cantorSetHomeomorphNatToBool.surjective`,
  and a `change` to `f.restrict cantorSet` followed by `rw [hf]` finishes. Verified. Finding 6.
- Naming: `naming_norm` returned `subject_unresolved`, so naming was not measured. The qualifier
  "long" is not descriptive (and "long" has a separate meaning in topology, as in the long line).
  I had no corpus or precedent evidence for a particular replacement name, so I filed no naming
  finding.
- Checked `exists_nat_bool_continuous_surjective_of_compact` (HausdorffAlexandroff: needs
  `Nonempty`, `MetricSpace`, `CompactSpace`; `I × I` satisfies all three),
  `cantorSetHomeomorphNatToBool : cantorSet ≃ₜ (ℕ → Bool)` and `isClosed_cantorSet`. They are used
  correctly.

## `exists_peano_curve`
The statement is right: `C(I, I × I)` and `Function.Surjective`. The proof can be a term,
`⟨f.restrict I, Set.surjOn_iff_surjective.mp (hf.mono cantorSet_subset_unitInterval subset_rfl)⟩`,
which drops the rewrite through the changed simp lemma and the `(by rfl)`. Verified. Finding 5.
`naming_norm`: `subject_unresolved`. The name `exists_peano_curve` reads fine, so there is no
finding.

## `unitInterval.instTietzeExtension`
`TietzeExtension` is a `Prop` class, so building the instance with `rw` is harmless.
`Mathlib/Topology/TietzeExtension.lean` already has
`ContinuousMap.exists_restrict_eq_forall_mem_of_closed` for nonempty `OrdConnected` subsets of ℝ,
next to `Real`/`NNReal` instances proved by retraction. I checked three alternatives with
`lean_verify_edit`:
- a general `Set.OrdConnected.instTietzeExtension {t : Set ℝ} [t.OrdConnected] [Nonempty t]`
  inserted in `Mathlib/Topology/TietzeExtension.lean`: success;
- the same instance in place of the PR's instance in `Mathlib/Analysis/Complex/Tietze.lean`, with
  `inferInstance` examples for `unitInterval` and `unitInterval × unitInterval`: success;
- a unit-interval-only `.of_retract` proof via `Set.projIcc`: success.

Finding 3: generalize it, move it to the Topology file, and drop the closed-ball detour. The
`precedent_search` hits were unrelated.

## `unitInterval.eq_closedBall`
It is correct (`norm_num [unitInterval, Real.Icc_eq_closedBall]`). `naming_norm` returned
`insufficient_evidence`, so there is no naming ask. Its only user is the instance, so under
finding 3 it becomes dead code. I folded that into finding 3 rather than filing it separately. I
found no other problem.

## `ContinuousMap.coe_restrict` and `ContinuousMap.liftCover_restrict` (one family)
The PR changes the RHS of a global simp lemma to `s.restrict f`. The sibling
`BoundedContinuousFunction.coe_restrict` still reads `f ∘ (↑)`, and `Set.restrict_eq` is not simp.
On Zulip, Eric Wieser remarked that `restrict` is not the simp normal form when eta-expanded
functions are wanted. Neither counterexample proof needs the change: my verified proofs never
mention `coe_restrict`. Reverting `coe_restrict` to the old statement compiles in its file, and
`liftCover_restrict`'s new proof (`simp only [restrict_apply, liftCover_coe]`) works under either
statement. Finding 4 (scope, advisory): revert, or split into its own PR that also covers the
bounded-continuous sibling. The `liftCover_restrict` edit itself is fine and is covered by that
same finding.

## Not raised
- The file's placement in Counterexamples (instead of Mathlib proper): it is plausible either way,
  and I had no evidence that would support an ask.
- `lemma` vs `theorem`: both are accepted.
- Statement shape `Set.SurjOn f cantorSet Set.univ`: idiomatic.
