# PR Review v4 0.8.9 discovery and battery smoke3 verdict

## Verdict

Deterministic discovery passes. The explicit model facet battery fails. Do not expand to the
nine-PR pilot yet.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Execution and grounding | PASS | 3/3 work units succeeded; all model candidates passed grounded intake |
| Deterministic discovery | PASS | Exactly one deterministic candidate, for `PowerSeries.expand_apply`; no discovery failures or deterministic control candidates |
| Deterministic publication | PASS | Lean supported the PR 33057 claim and selection published one factual blocking finding with no unverified fix |
| Model semantic direction | FAIL | 0/3 visible PR 33098 atomic asks issue-match |
| Model register/grounding | PASS | All three model outputs are concrete, grounded requested changes with no neighboring-target claims |
| Control publication | PASS | Two raw model candidates on PR 33438 remained inconclusive; zero selected control findings |
| Volume interpretation | FAIL AS IMPROVEMENT | Model volume and semantic content are effectively unchanged from 0.8.8 |

## Output

- 4 candidates total: 1 deterministic and 3 model-generated.
- By PR: PR 33057 = 1 deterministic; PR 33098 = 1 model; PR 33438 = 2 model.
- Evidence: 1 supported, 3 inconclusive, 0 contradicted, no terminal failures.
- Selection: one blocking PR 33057 finding; zero PR 33098 or control findings.
- Candidate-generation cost: approximately $0.21, including approximately $0.14 reported as cached
  cost.

## Model comparison

The per-target checklist did not change the substantive behavior observed in 0.8.8:

- PR 33057: the model again emitted no candidate.
- PR 33098: the model again requested removing the unused `h_nonempty` binder from
  `coveringNumber_two_mul_le_externalCoveringNumber`. The maintainer asked to destruct the empty
  branch with `rfl`; this remains a different issue and transformation.
- PR 33438: the model again produced two requests to replace `all_goals` with explicit side-goal
  handling.

No candidate addressed the visible requests to restructure `isCover_maximalSeparatedSet`, rewrite
`coveringNumber_le_packingNumber` with the preferred API, or use the requested `rfl` case pattern.

## Interpretation

The architecture now reliably separates factual tool findings from model judgment. That is a real
success: the known compile failure is recovered by construction and control publication remains
clean.

The model bottleneck is not checklist coverage or output syntax. It can inspect the right target and
form a concrete request, but it chooses a different transformation from the maintainer. Repeating or
expanding facet instructions is not supported by this result.

## Next gate

1. Port the audited v7.1 issue/resolution judge to v4 obligations so subsequent generation
   experiments have automated semantic feedback with a standing human audit.
2. Test a small set of generic maintainer-ask exemplars as an isolated generation treatment. Do not
   add temporal retrieval in the same release.
3. Reuse these exact three work units and keep deterministic discovery, grounding, and strict
   publication fixed.
4. Require at least one of three PR 33098 issue matches across the treatment; report resolution
   separately and retain zero selected control findings.
