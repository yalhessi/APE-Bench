# PR Review v4 0.8.8 grounding smoke3 verdict

## Verdict

The grounded-ask contract landed, but the generation intervention failed. Do not expand this release
to the nine-PR pilot.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| Execution | PASS | 3/3 work units succeeded; three reviewed workspaces persisted |
| Contract | PASS | All three candidates passed primary change/entity/subject validation; evidence plans were derived after ingestion |
| Grounding | PASS | The PR 33098 candidate discusses its actual primary theorem; the prior neighboring-theorem attachment is gone |
| Maintainer-request register | PASS | All candidates state concrete requested transformations rather than questions or no-change observations |
| PR 33098 semantic direction | FAIL | 0/3 in-scope atomic maintainer asks issue-match |
| PR 33057 publication | FAIL | The generator emitted no candidate for the known target-local compile failure, so evidence-conditioned rendering was never reached |
| Control publication | PASS | Two raw PR 33438 style candidates were inconclusive; 0 selected findings |

## Output

- 3 accepted candidates: 0 on PR 33057, 1 on PR 33098, 2 on control PR 33438.
- Evidence packets: 0 supported, 3 inconclusive, 0 contradicted, no terminal failures.
- Selected findings: 0.
- Candidate run cost: approximately $0.20, including approximately $0.14 reported as cached cost.

## Semantic audit

The PR 33098 candidate is correctly grounded in
`Metric.coveringNumber_two_mul_le_externalCoveringNumber`, but it flags the unused `h_nonempty`
binder and requests `by_cases` or `_`. The maintainer requested destructing the empty branch with
`rfl` and then using `simp`. These touch the same case split but identify different specific aspects
and produce different transformations, so this is neither an issue nor resolution match.

No candidates were emitted for the other two visible atomic asks in the unit:

- restructure `isCover_maximalSeparatedSet` around `C := {x} union maximalSeparatedSet ...`;
- rewrite `coveringNumber_le_packingNumber` using `by_cases!`, `encard_maximalSeparatedSet`, and
  `IsCover.coveringNumber_le_encard`.

The control candidates request replacing `all_goals` with explicit branches. They are concrete and
grounded, but neither the repository policy checker nor comparison search supports publication.

## Interpretation

Version 0.8.8 fixed the neighboring-target bug and shifted prose into the desired maintainer-request
form. It also overcorrected candidate volume without improving semantic choice: 0.8.7 generated many
speculative observations, while 0.8.8 generated very few concrete but still non-matching asks.

Moving evidence planning after generation removed one source of bias, but it also makes universal
facts such as "the reviewed file fails Lean" dependent on voluntary model discovery. Baseline
compiler/linter checks should instead be a deterministic discovery channel, not only
candidate-conditioned evidence.

## Next gate

1. Add universal deterministic discovery for baseline compile and repository linters, capable of
   creating factual candidates before model generation. This should recover PR 33057 by construction.
2. Render the eight-family checklist explicitly for every target, with zero-or-more asks but visible
   coverage accountability. The one-paragraph instruction did not reproduce the v3 battery behavior.
3. Keep grounded intake and supported-only publication unchanged.
4. Repeat the same three work units. Require deterministic recovery of PR 33057, at least one of the
   three PR 33098 issue matches, and zero selected control findings.
