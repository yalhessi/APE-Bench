# Manual inventory-agenda probe 0.1.1 verdict

## Verdict

Fail. Do not repeat this prompt-only specialist treatment and do not treat it as evidence that a full
inventory/ledger implementation will improve judgment recall.

The six calls completed successfully, but the agenda split moved attention toward plausible control
criticisms rather than toward the maintainer obligations:

- PR 33098 produced two candidates;
- control PR 33438 produced six candidates;
- only two candidates overlapped any of the six obligation scopes, placing an absolute upper bound of
  2/6 on issue recall;
- manual application of the frozen rubric gives one issue match and zero resolution matches;
- only one evidence packet was supported, and it produced a selected finding on the control;
- no intervention candidate was selected.

The screen's pre-registered `fail_or_revise` range is 0-2 issue hits. The conclusion therefore does
not depend on the unavailable automated semantic-judge calls.

## Comparison

| Metric | Existing holistic baseline | Manual agenda probe |
|---|---:|---:|
| Calls per compared bundle | 3 per PR | 3 per PR |
| Mean issue recall | 2/6 | manual 1/6; upper bound 2/6 |
| Three-run union issue recall | 4/6 | manual 1/6; upper bound 2/6 |
| Candidate location recall | 6/6 in each stable baseline report | 2/6 |
| Raw intervention candidates | 1-3 semantic hits vary by run | 2 total candidates |
| Raw control candidates | 2 per baseline repetition | 6 |
| Selected control findings | 1 of 3 repetitions | 1 of 1 |
| Exact cross-pass duplicates | not applicable | 0 |

## Candidate audit

The proof pass identified that `Metric.isCover_maximalSeparatedSet` uses unnecessary manual case
analysis. This is the correct issue family for `pr33098_i02`, but it proposed a generic
`pairwise_insert` route rather than the maintainer's canonical `Metric.isSeparated_insert_of_notMem`
transformation and the complete requested proof structure. It is an issue match but not a resolution
match under the frozen rubric.

The statement/API pass repeated the known wrong-binder near miss in
`coveringNumber_two_mul_le_externalCoveringNumber`: it proposed removing the unused `h_nonempty`
branch, whereas the maintainer retained `h_nonempty` and replaced the empty branch's `h_empty` binder
with `rfl`. This is false/false.

The relational pass emitted no PR 33098 candidate. It emitted two candidates on the control. Across
all three control passes, the model generated six plausible but unrequested criticisms.

## Evidence audit

The corrected naming policy prevented raw naming similarity from selecting a finding. However, the
repository-search collector still treated the control's broad duplication claim as supported. The
selected finding asks to refactor two approved arctangent proofs through a shared proof pattern.

This exposes the analogous weakness for duplication: repository token hits are not sufficient to
establish semantic duplication or justify a shared abstraction. Comparative code evidence is needed
before a duplication candidate can be published.

## Interpretation

The cheap probe rejects the hypothesis that separating the existing generic concerns into three
specialist prompts is enough to stabilize coverage. It produced less obligation coverage and much
more pressure to find something on the control.

It does not fully reject a modification inventory. The probe omitted the mechanisms that could make
an inventory materially different:

- machine-validated investigation records for every scheduled item;
- explicit `checked_no_request` and `inconclusive` channels;
- tool/evidence requirements tied to each investigation;
- follow-up scheduling and cross-target scope expansion;
- repository-norm packets supplied before candidate generation.

But the result lowers the priority of implementing a large inventory/ledger solely to improve prompt
coverage. The one partial semantic success and two persistent never-hit obligations instead strengthen
the norm-discovery hypothesis: the model recognizes broad proof pressure but does not recover the
canonical repository transformation.

## Recommended next step

1. Do not run a second manual-agenda repetition.
2. Tighten duplication evidence so repository token matches are a prior, not independent support.
3. Build a very small oracle norm-packet diagnostic for the two never-hit obligations and the partial
   `isCover_maximalSeparatedSet` issue.
4. Test whether review-time repository declarations and sibling implementations convert those broad
   observations into exact issue and resolution matches.
5. Reconsider inventory implementation only as a scheduler for proven norm/tool investigations, not as
   another prompt-level coverage mechanism.

## Incomplete automated artifact

The frozen semantic judge could not run in the Codex process because its environment did not inherit
an OpenAI API key. It found exactly two candidate-obligation pairs before the provider call failed.
Running it from the configured user shell will complete the standard report, but cannot change the
pre-registered failure because even two accepted pairs remain in the 0-2 failure range.
