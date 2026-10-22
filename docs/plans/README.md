# Plans

The two plans this branch was built from, kept verbatim, plus a status walk.

| | |
|---|---|
| [`STATUS.md`](STATUS.md) | **Start here.** Every numbered item, marked built / partial / not built, checked against the tree rather than against memory. |
| [`2026-09-06-ape-native-review-system.md`](2026-09-06-ape-native-review-system.md) | The original. Four stages against the four problems named in the request. |
| [`2026-09-07-remaining-work.md`](2026-09-07-remaining-work.md) | The remainder, reordered by what unblocks what, written once Stages 0 and 3 had largely landed. |

The plans are unedited on purpose. Annotating them in place would lose the distinction
between what was decided and what was built, and that distinction is the only thing that makes
a plan worth keeping afterwards.

## The plans written since

Newest last. Historical plans are kept verbatim; the second-round October 22 plan is the
consolidated implementation handoff. `STATUS.md` walks the first two only; later plans and
their linked implementation records describe their own completion status.

| | |
|---|---|
| [`2026-09-08-review-digestion-and-oracle-ladder.md`](2026-09-08-review-digestion-and-oracle-ladder.md) | Find the missing resource before building anything. Converged from six rounds of audit. |
| [`2026-09-10-convention-drift-mechanics.md`](2026-09-10-convention-drift-mechanics.md) | Convention drift, captured and treated as one design. |
| [`2026-09-11-pull-request-store.md`](2026-09-11-pull-request-store.md) | One PR store, many projections — written as built. |
| [`2026-09-14-selection-over-coverage.md`](2026-09-14-selection-over-coverage.md) | Selection, not coverage: what the September runs did to the talk. |
| [`2026-09-21-typed-handoffs.md`](2026-09-21-typed-handoffs.md) | The task↔subtask contract, stage provenance, and a declared stage graph. |
| [`2026-09-22-coordinated-emission.md`](2026-09-22-coordinated-emission.md) | Where generation fails to align with maintainer obligations: five audits, four candidate holes, and the one worth building — a fix that spans declarations. |
| [`2026-09-21-specialist-silences.md`](2026-09-21-specialist-silences.md) | Why specialists are silent at gold sites, which silences are worth paying to change, and how to test each one. |
| [`2026-09-23-work-enumeration.md`](2026-09-23-work-enumeration.md) | Enumerate the review work maintainers do from the PR store, ask every question at every place it applies with a verdict per target, and measure the ceiling of doing all of it before designing the belief-updating scheduler. |
| [`2026-09-23-one-run-to-move-the-wall.md`](2026-09-23-one-run-to-move-the-wall.md) | The arms hold the answers and the contract tells them to withhold: ask without a compiling fix, account for every target, file advisory asks -- one judged run against a threshold fixed before spending. |
| [`2026-09-23-unify-the-contract-branches.md`](2026-09-23-unify-the-contract-branches.md) | Two sessions built the same per-target contract in parallel; one mechanism survives (`target_verdicts`), the prompt-side text is ported onto it as opt-in knobs, and the next spend is one change at a time against a control already paid for. |
| [`2026-10-06-consolidate-worktrees.md`](2026-10-06-consolidate-worktrees.md) | Written as built: 14 topic worktrees read before the clean-up round; eight merged whole, four landed in part, the rest parked on `parked/*` tags with dead-ends entries. |
| [`2026-10-22-task-native-evaluation-and-exploration.md`](2026-10-22-task-native-evaluation-and-exploration.md) | Original requirements inventory; the subsequent task/dataflow design's first refactor is implemented, accepted and merged. Read its implementation record and review for the completed scope. |
| [`2026-10-22-review-operations-foundation.md`](2026-10-22-review-operations-foundation.md) | Consolidated implementation handoff: integration, shared context/verification operations and assessment export first; a selected tool-using experiment at a later composition checkpoint. Includes dependencies, named removals and acceptance checks. |

The October 22 first refactor has a [target architecture](../research/task-dataflow-refactor-design-2026-10-22.md),
with [primary-source systems reading](../research/review-refactor-systems-reading-2026-10-22.md)
and an [author-conducted adversarial pass](../research/task-dataflow-refactor-adversarial-review-2026-10-22.md).
Its [implementation record](../research/task-dataflow-refactor-implementation-2026-10-22.md)
and [independent acceptance](../research/task-dataflow-refactor-implementation-review-2026-10-22.md#final-independent-closure-assessment-2026-10-22)
describe what was built and verified; `develop@a9154196` merges that work. Earlier proposal
documents retain their original status text. The second-round plan above starts from the
accepted implementation and identifies the additional work needed for new experiments.
The architecture's v0.3 incorporates Claude's appended review; its
[disposition table](../research/task-dataflow-refactor-design-2026-10-22.md#20-disposition-of-claudes-review)
separates adopted corrections from the scope judgments the proposal revises.
