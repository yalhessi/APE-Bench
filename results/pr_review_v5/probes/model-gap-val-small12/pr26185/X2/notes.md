# Review notes: PR #26185 (Peano curve)

Inputs read: brief.md, pr.md, model.md, diff.patch. Tools used via ./ptool (describe, file_read,
file_search, content_search, lean_verify_edit, naming_norm, precedent_search, zulip_search).
Baseline: `lean_verify_edit` with no edit on Counterexamples/PeanoCurve.lean -> compiles, no errors.
Zulip shows #26184 (the declared dependency) is the Hausdorff-Alexandroff PR, so the Mathlib-side
edits in this diff (`coe_restrict`, `liftCover_restrict`, `eq_closedBall`, the Tietze instance)
belong to this PR itself.

## `import in Counterexamples.lean`
Alphabetical position between Motzkin/OrderedCancel... and Phillips is correct. Nothing to ask.

## `module_doc in PeanoCurve.lean`
Typos "existsence", "sujrective"; missing blank line after heading; no main-results line. -> finding 1.

## `exists_long_peano_curve` (+ its doc comment)
- Docstring says "maps the Cantor set to the square" where the content is surjectivity -> finding 2.
- Continuity of `g'` by hand; `by fun_prop` verified -> finding 5.
- Generalization: nothing about `I × I` is used but compact + metrizable + nonempty + TietzeExtension.
  Verified a general version (metrizable, via `TopologicalSpace.metrizableSpaceMetric`) and that the
  Hilbert cube `ℕ → I` is then a corollary (the `[MetricSpace X]` version fails there: no
  `MetricSpace (ℕ → I)` instance) -> finding 3 (filed on `exists_peano_curve`, the headline result).
- Naming: `naming_norm` returned subject_unresolved; "long" is a slightly odd word but this is an
  auxiliary lemma in Counterexamples; not raised.
- Dependency on the `coe_restrict` change: the proof can be written without it -> part of finding 7.

## `exists_peano_curve` (+ doc comment)
- Golf to a term, `(by rfl)` -> `subset_rfl`; verified -> finding 4.
- Generalization -> finding 3.
- Doc comment "There is a continuous surjection from the interval to the square." is accurate.

## `namespace in PeanoCurve.lean` (`open scoped unitInterval`) / file
`open scoped unitInterval` is right. But the file has no namespace, unlike 24 of 27 existing
Counterexamples files -> finding 8.
Considered asking to move the theorem into Mathlib proper (it is a theorem, not a counterexample);
not raised, the author's placement is defensible and I found no evidence of a maintainer preference.

## `unitInterval.instTietzeExtension` (Mathlib/Analysis/Complex/Tietze.lean)
- Verified three alternatives: (a) `.of_retract` with `Set.projIcc` (like `NNReal.instTietzeExtension`);
  (b) a general instance for nonempty `OrdConnected` `t : Set ℝ` via
  `exists_restrict_eq_forall_mem_of_closed`, placed in Mathlib/Topology/TietzeExtension.lean (compiles
  there with no new imports; `inferInstance` then finds `TietzeExtension (Set.Icc 0 1)`), and
  (c) the same general instance in Complex/Tietze.lean with `inferInstance` for `unitInterval`.
  -> finding 6 (generalize and move; fallback: retract proof).
- Universe: unannotated, auto-generalized; used at universe 0 in PeanoCurve; fine.
- `naming_norm`: subject_unresolved. Name follows `NNReal.instTietzeExtension` / `Real.instTietzeExtension`.
- precedent_search: nothing applicable.

## `unitInterval.eq_closedBall` (Mathlib/Topology/UnitInterval.lean)
Statement and proof fine; name consistent with `Real.Icc_eq_closedBall` in the `unitInterval`
namespace (`naming_norm`: insufficient_evidence, `eq_` is a common prefix). With finding 6 it is
no longer needed for the instance, but it is a reasonable standalone lemma; not raised.

## `ContinuousMap.coe_restrict` / `ContinuousMap.liftCover_restrict` (family)
The RHS change to `s.restrict f` is valid (`Set.restrict_eq` is not simp, `Set.restrict_apply` is
simp, so it is simp-normal) and the `liftCover_restrict` edit is the forced follow-up. But it changes
a core simp normal form inside a Counterexamples PR, is inconsistent with
`BoundedContinuousFunction.coe_restrict` and with the definition's `toFun`, and is not needed by the
new file (verified proofs that do not rewrite with it) -> finding 7 (filed on `coe_restrict`;
`liftCover_restrict` is covered by it, no separate finding).

## Not raised
Correctness: everything compiles as the PR leaves it; no semantic error found. No duplication of an
existing Peano-curve result found (no such declaration in the base tree was expected; Zulip search
found none).
