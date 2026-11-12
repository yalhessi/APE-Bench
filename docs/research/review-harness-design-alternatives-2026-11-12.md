# Alternative designs for the Mathlib reviewing harness

12 November 2026. Design proposals following the [project assessment](project-assessment-2026-11-12.md). Improving measurement is necessary for interpreting a design, but it is not a substitute for one. These alternatives specify different work units, sources of judgement and execution procedures. None is presented as an experimentally established improvement.

**The central design choice is where the proposed review judgement comes from, and what the harness does to establish its applicability.** The existing approaches often ask a general model to notice a problem, formulate an alternative and decide whether Mathlib would request it, with extra context or repeated prompts around that same decision. A more useful architecture should give these operations distinct inputs and preserve their results without assuming that separating them automatically improves them.

**Several important concepts currently have weaker operational representations than their names suggest.**

| Concept | Representation or behaviour inspected | Design consequence |
|---|---|---|
| Review work | `structured.py` requires six concern verdicts per declaration. The older lead routes concern-specific work units. | One decision spanning a theorem, its siblings, attributes and uses is divided across cells or jobs. A new category does not repair that fragmentation. |
| Open investigation | `InvestigationBrief` has a question, reason and prior checks, but its rendered instructions require dropping an answer that belongs to another concern. | Investigation can discover the right relationship and still lose ownership when the problem changes shape. |
| Coordination | The lead receives summaries; `coordination.py` refuses shared sibling state and redispatch policies that are not implemented. | This implementation coordinates assignments and findings, rather than accumulating a jointly investigated decision. It does not exhaust the possible benefits of coordination. |
| Project knowledge | The latest bank supplied six independently acquired compact or full text entries to ordinary review, which could use or ignore them. | The representation compresses historical choices before the target correspondence is known. More prose does not guarantee that the decisive distinction survives or governs application. |
| Verification | Lean can establish a construction or expose an interface difference. | Technical feasibility, preservation of the contribution's requirements and the historical preference for a change remain different claims. |

Sources: [structured reviewer](../../src/ape/tasks/lean_tasks/formal_math/review/structured.py), [investigation brief](../../src/ape/tasks/lean_tasks/formal_math/review/lead.py), [coordination policy and implementation refusals](../../src/mathlib_review/review/coordination.py), and [bank protocol](../../.claude/worktrees/reusable-review-knowledge/results/pr_review_v5/probes/reusable-review-knowledge-2026-10-24/PROTOCOL.md). These are specific design limitations, not a claim that the strongest solo reviewer internally reasons in six cells.

The [September work-structure analysis](review-work-structure-2026-09.md) and [shared-context proposal](review-coordination-design-2026-09.md) already identified much of this conceptual problem. The useful task now is to choose an operational design, including how it can fail, rather than rename those concepts.

**Alternative 1: review by transferring historical decisions.**

The primary object is a complete review episode, not a convention sentence. It contains the relevant code before review, the expert's actual request, surrounding discussion, any explicitly discussed alternatives and constraints, and the subsequent change when its connection to that request is supported. Date, library area and source identity remain attached. Missing rationale stays missing; an author's later edit is not automatically an expert instruction.

The online procedure is:

1. From the visible PR, identify candidate choices and relationships: an implication theorem's namespace, repeated specialization, manually maintained counterpart lemmas, a newly registered automation rule. These are questions, not presumed violations.
2. Retrieve earlier episodes using both the submitted code and the decision being considered. Index the review/action text as well as the pre-review code; code similarity alone is insufficient. Return the original episode so a compressed description cannot become the only authority.
3. Instantiate a correspondence: what played each mathematical or API role in the earlier episode, what plays it here, which circumstances differ, and which requested transformation could transfer. Produce a concrete target-specific proposal or an explicit failure to transfer.
4. Test the target-specific assumptions and consequences. Retrieve explicit contrary decisions where available; unasked code supplies context but is not a negative preference label.
5. Produce the review from the applicable, supported proposals and ordinary PR investigation. Retain the source-to-target correspondence in the record. Unsupported applicability is a reason to investigate or leave a proposal unresolved, not to assert a universal rule.

For the namespace case, the transferred object would distinguish the theorem's hypothesis predicate from its conclusion predicate and show which role governed the earlier name. “Use dot notation” is insufficient. The target operation must construct the proposed name, compare the relevant role correspondence and check use sites. If the source does not settle hypothesis-versus-conclusion priority, the system must preserve that ambiguity.

The hoped-for advantage is access to a project-specific decision that the solo model's prior does not supply, without first compressing it into a universal convention. The mechanism also suggests concrete engineering: an index over complete eligible episodes, a correspondence-producing operation, and source-linked target proposals. Acquisition can be reused across PRs instead of repeating a broad preparation session for each one.

**Relation to prior attempts.** This is a revision of the July precedent direction and the [October 23 case-based transfer plan](../plans/2026-10-23-review-knowledge-transfer.md), not a newly discovered research idea. That plan already required correspondence and conditional reasons. Its [pilot](review-knowledge-transfer-pilot-assessment-2026-10-23.md) found no historical-recovery gain from a preparation procedure that delivered a prose account to ordinary review. The later bank also failed its primary test. The proposed differences here are retrieval of original decision episodes at review time and explicit instantiation into target proposals, rather than another richer preparatory note. If the implementation merely supplies examples followed by “review this PR,” it has reverted to an already tested treatment.

This can still fail because the relevant episodes are not retrieved, the analogy is wrong, the historical decision is too context-specific, or the same model declines the resulting proposal. It cannot be credited with solving that last problem by construction. Compare structured transfer against ordinary review supplied with the same retrieved episodes and comparable resources. That tests the transfer operation separately from simply adding information.

**Alternative 2: review by resolving design choices across their dependencies.**

The primary object is an unresolved review question with a semantic scope. Its scope can include a theorem family, a definition and its accessors, or an interface and its consumers. Concern labels are useful descriptions; they do not determine ownership or forbid following the investigation into another concern.

A minimal working record is:

```text
Question
  subject and related declarations
  why the question arose from the visible PR or eligible evidence
  requirements, with sources; author choices kept separate
  current design and concrete alternatives
  facts that would distinguish those alternatives
  evidence and check results, including contradictions
  unresolved dependencies
  disposition and the delivered request, if any
```

The harness performs operations on this record. It opens a question, expands its relevant scope, constructs an alternative, tests a distinguishing claim, brings in project evidence, and revises or resolves the comparison. It does not require every declaration to fill every concern cell. It starts with the questions raised by an ordinary whole-PR reading and by visible relationships, and has a bounded investigation budget.

The next action depends on the unresolved claim:

| Unresolved claim | Useful operation |
|---|---|
| The more general statement holds and preserves the original theorem | Construct it and derive the original as a corollary. |
| Generated lemmas preserve the handwritten interface | Compare types, binder inference and representative existing client calls. |
| Two declarations are genuinely counterparts | Check the claimed relation before transferring an edit between them. |
| One namespace or naming orientation is preferred in this situation | Seek comparable dated expert decisions; compilation alone cannot answer it. |
| A proof rewrite depends on registration elsewhere | Expand the scope, test the coordinated change and retain the dependency. |
| The PR's chosen restriction is a requirement | Trace it to the description or established interface; do not promote an implementation detail into a requirement. |

For PR 33098, the natural question concerns a definition, the family of accessor proofs and the supporting registrations needed for a proof route. Asking separate “proof” and “attributes” reviewers can lose that dependency. For PR 33117, generation via `to_fun` and preservation of client calls belong in the same comparison: successful generation alone does not settle the interface question. For generality, the record must distinguish “the existing application uses 2” from “the contribution requires restricting the theorem to 2.” Neither statement independently settles the project preference.

Findings are rendered from the investigated questions, preserving scope. If one supported change applies to siblings, the system checks and extends that request rather than treating each sibling as a new independent discovery. If the investigation changes category, the question survives. A question can be unresolved without forcing a comment, and a clear identified issue can be communicated without pretending that its complete fix is known, under a consistently defined output contract.

This design naturally supports one principal reviewer with tools that perform specific operations. It does not require a team of simulated reviewers. Where a child task is useful, it receives an unresolved question and the relevant evidence, and returns a construction or checked claim to that same record. A reusable state object is valuable only if subsequent actions consume it; another mandatory narrative ledger would not implement the design.

**Relation to prior attempts.** The September shared-PR proposal is a direct predecessor. The [reconstruction experiment](review-reconstruction-phase-a-review-2026-10-20.md) weakens mandatory independent whole-contribution sketches; it does not establish that maintaining a concrete comparison across dependent checks is useless. The October 23 conditional-preparation null also applies: merely instructing a preparer to search and compare did not add the desired capability. This alternative changes the live unit of investigation and its handoffs. That is a substantive implementation difference, but not evidence of effectiveness.

The [focused generality result](review-harness-next-question-2026-10-27.md) is a particularly strong limit: a reviewer already constructed the expert's alternative and declined it. Better construction and state management alone should not be expected to fix that disagreement. This design needs relevant project knowledge for preference questions, and may still fail with it. Its distinct prediction is improved recovery where scope, alternative choice or comparison consequences are currently lost—not a universal solution to maintainer judgement.

**Alternative 3: learn a project-specific proposal policy from actual feedback.**

This design changes the source of the proposal distribution rather than relying on a general model to apply retrieved prose. A learned component proposes review questions or requests that resemble the choices Mathlib experts actually make; the frontier model investigates their applicability and technical consequences using the reviewed library.

Training examples use the code and context available before an expert request as input, and the actual expert request as the target. Linked requested edits can supply a richer target when the attribution is established. Training can predict requests or structured actions directly. It need not label arbitrary model reviews as good or bad, and unasked sites must not be converted into negative examples. Silence and completeness would require a separate modelling decision; initially this is a proposal model, not a calibrated declaration that a PR is clean.

At review time:

```text
reviewed PR + eligible project history
    -> learned proposals with target and suggested action
    -> frontier investigation of applicability, alternatives and consequences
    -> delivered review, retaining source and verification distinctions
```

The learned proposal is a hypothesis, not expert authority. A technical refutation must survive; a proposal does not become warranted merely because the learned model emitted it. The consumer's disposition is part of the design too: if it discards every proposal using its original generic taste, the learned component has no influence. The experiment must establish whether the historical signal changes final expert-relative recovery, including losses.

This addresses the user's central observation directly: the frontier model's general prior can differ from the project's conditional review behaviour. Instead of repeatedly trying to communicate that behaviour through a short prompt, the historical feedback changes which specific alternatives the system proposes. A parameter-adapted model is one implementation; a retrieved-episode predictor provides a less expensive initial comparison. These should be named as different implementations, not assumed equivalent.

This is not the old selector over a flooded candidate pool. Its objective is generating expert-like concerns and actions from pre-review context; it does not assign normative quality scores to arbitrary reviews. Nevertheless, it can overfit the familiar maintainers, epochs and frequent concern families, produce unsupported requests, or merely imitate wording. Temporal and PR-level separation, source deduplication and final issue/resolution recovery are essential. The available data and training resources may be insufficient. This is the larger investment, not a recommendation to begin fine-tuning immediately or a claim that a small model will outperform a frontier one.

**My design recommendation is a reviewer that investigates explicit choices, with historical episodes supplying concrete proposals.** Alternative 2 gives the review process a coherent unit of work; Alternative 1 supplies a potential source of information beyond the solo model's prior. Alternative 3 is the distinct longer-term option if in-context transfer remains the bottleneck. I would not build all three mechanisms at once or treat a failed retrieval pilot as evidence for training without examining what it failed to supply.

The proposed end-to-end process is:

```mermaid
flowchart LR
    P[Reviewed PR and library] --> Q[Questions about choices and relationships]
    H[Eligible historical review episodes] --> T[Transfer a prior decision]
    Q --> T
    T --> I[Investigate a concrete comparison]
    Q --> I
    I --> Q
    I --> R[Render supported review requests]
```

Keep ordinary whole-PR investigation available: historical retrieval will miss novel issues, and not every documentation or process request requires alternative construction. The design's distinctive path must add something beyond ordinary review, rather than replace reliable solo behaviour with a sparse case library.

**The implementation can be small while the design remains general.** The existing [`DESIGNS` registry](../../src/ape/tasks/lean_tasks/formal_math/review/__init__.py) already supports a new per-PR task returning the same final findings. Use the existing change graph and [`ReviewComponent`](../../src/mathlib_review/agenda/components.py) for scope candidates, with hypotheses distinguished from established relations. Reuse session observations, source gating and the operations branch's `ReviewScope` and `EditVerifier`. Keep source episodes as data, target correspondences as observations, and the investigation procedure inside the new task. Avoid a new scheduler, a universal ontology, a separate evidence store or one custom agent per convention.

A useful first implementation would expose three concrete operations—retrieve an eligible episode, instantiate a target proposal, and investigate a comparison—within one reviewer task. Preserve the frozen solo route. Do not implement all the coordination-policy options just to obtain a shared question record.

The relevant comparisons follow from the mechanisms:

- Same historical episodes, ordinary consumption versus explicit target transfer: does the transfer operation add issue or resolution recovery?
- Same proposals and sources, ordinary investigation versus persistent comparisons with expanding scope: does the live design prevent a specific loss?
- For a learned proposer, the same frontier consumer and budget with historical-learning proposals versus its own proposals: does learning the project prior add anything?

Matched information tests isolate procedure; autonomous whole-PR tests also include retrieval and question discovery. A supplied target or ask-selected source remains a conditional diagnostic. All use actual expert references for issue and resolution recovery, with output volume and resource accounting; none requires arbitrary review-quality labels. Intermediate artifacts locate a failure, but final reviews establish whether the harness improved.

The architecture should be judged by whether it produces a different, better-grounded investigation or expert-aligned request. Populating the records correctly, citing more sources or compiling more alternatives is not sufficient. That limitation belongs inside the design, alongside its intended source of improvement.

Local basis: inspected the current design registry, structured reviewer, investigation brief, coordination refusals and component representation; read the September shared-context design, October reconstruction and conditional-preparation results, and the bank protocol. No new harness, model call, training run or semantic judgement was executed.
