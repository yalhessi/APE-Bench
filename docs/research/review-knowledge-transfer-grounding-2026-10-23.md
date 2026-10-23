# What the theoretical framing contributes to the knowledge-transfer plan

**Assessment, 2026-10-23.** Read against the original supervisor slides, the maintained project
overview, `ask-identify-resolve.md`, the knowledge-transfer draft and the recent experimental
assessments. No new model runs, technical replays or usefulness judgments were made.

**Conclusion:** the connection exists and is worth writing down. The framing distinguishes
problems that our experiments have sometimes treated as interchangeable: producing another valid
implementation, establishing a comparative benefit, and justifying a review request. It also
explains why many conventions could require a large knowledge resource without requiring many
separate harness implementations. It does not establish that case-based transfer, a particular
representation or another decomposition will improve reviewing.

The useful role of the theory is to constrain diagnoses and experimental claims. Recasting every
failed design in its notation would add little. The sections below identify consequences that
change what we would build, compare or infer.

## 1. Keep the central distinctions, with a small refinement

Use the maintained overview's notation:

```text
x = (C, p, t, k)     library state, contribution purpose, time and review context
S(C, p)             changes that compile and realize the contribution's purpose
A(x) ⊆ S(C, p)      changes acceptable in this review context
≽x                  comparative preference among viable changes
δ                   submitted change
δ′                  an alternative revised change
r                   a proposed review request
```

Purpose may be partly unknown or contested. Compilation checks only part of membership in S;
it does not establish that the theorem expresses the intended mathematics, that the contribution
realizes its purpose, or that its axioms and interface are appropriate. S is a modeling object,
not a set the current compiler can enumerate or decide completely.

One further distinction helps: whether **requesting r about δ is justified in x**. Call that
judgment Jx(r, δ), without assuming a new numeric score or implementation. It can depend on the
rest of the review, author burden, scope and the evidence available. It names the question our
existing request-worthiness rubric is trying to assess.

For a change request with a concrete repair, three claims can now be separated:

1. The proposed δ′ is feasible and preserves the relevant purpose and commitments.
2. There is a supported comparative reason to prefer δ′ over δ in this context.
3. The benefit and circumstances justify asking for the revision r.

The first does not establish the second; the second need not establish the third. A marginally
shorter proof can be a preferred alternative while providing too little benefit to interrupt the
author. A request to clarify a design can also be useful before a particular patch is available.

These distinctions describe obligations in our explanation and evaluation. They are not a claim
that maintainers reason in three sequential stages, nor a requirement for three agents or Tasks.

## 2. Where this explains the experiments

| Experiment or case | What improved or was established | What remained open |
|---|---|---|
| Independent reconstruction at 33066 | A different solution avoided the new constructor. | Whether that constructor in the submitted solution duplicated an existing API without enough benefit. Difference between solutions did not establish the objection. |
| The normalizer proposal at 43167 | A more general statement was proposed, realized in Lean and delivered in two sketch-assisted reviews. | Whether the extra declaration's reuse benefit justifies its API and naming burden. Human request-worthiness remains unlabelled. |
| Assisted `to_fun` review at 33117 | With fixed search, all six assisted Opus sessions related the mechanism to the twins. | Correct construction, client-interface effects and the contextual adoption decision. Only one filed the requested change. |
| The topology proposal | The alternative compiled. | The asserted comparison was false: the proposed assumptions were stronger. Feasibility did not establish generalization. |
| Convention detectors and forced filing | More departures or plausible changes became explicit. | Which proposals warranted requests, their volume and their limited coverage of the long tail. |

This gives a substantive interpretation of reconstruction's disappointing result: it was intended
to improve review by increasing access to counterfactual implementations. Its successful proposal
transmission did not reliably establish the comparisons and requests that matter. Further gains
in alternative production alone therefore have a weaker claim on effort.

It does not follow that alternative production is generally solved or irrelevant. The failed
`to_fun` trials show that construction can still be load-bearing. The framing requires locating
the missing claim in each observed failure instead of promoting one explanation to all misses.

The same reasoning limits the positive conclusion: the normalizer result is evidence of proposal
transmission and technical realization. It is not yet evidence that the system learned the right
preference or made a better request.

## 3. Acceptance, preference and requesting are different targets

The original slides describe A as the region that the preference relation does not require
leaving. That is insufficient as a definition. An ordering alone gives no acceptance threshold.
An acceptable implementation may admit many preferred improvements; two acceptable designs may
also be incomparable. Treat A and ≽ as separate contextual judgments, as the maintained overview
already does.

This matters for both generation and evaluation. A reviewer is not required to find a globally
best implementation. A contribution can be acceptable while still warranting a useful request,
and can admit technically preferable edits that are not worth requesting. Even accurate pairwise
preference judgments would leave discovery, feasibility and request value partly unresolved.

The original representation of a request as a test on revised PRs remains useful for concrete
requests. It separates the condition from one witness satisfying it. For example, a redundancy
concern can admit different repairs; one author's resolving patch does not uniquely identify the
condition that motivated the review. Questions, scope changes and advisory suggestions require
more interpretation than a Boolean test over patches.

The original completeness condition is correspondingly too strong as a general operational
contract: it asks for one emitted test that every acceptable revision passes. A concrete request
can legitimately choose one repair route while another acceptable route would avoid that exact
change. More importantly, our recorded-ask matcher does not measure completeness against the
unknown acceptance region. The maintained overview already qualifies this; the plan should carry
that qualification into its metrics rather than reuse the original formal claim.

There is no need to replace it immediately with a comprehensive formal specification. Keep the
concrete questions: was the concern valid, was the proposed resolution suitable, and was the
request worth making? Historical agreement measures a related but narrower target.

## 4. A convention can supply a conditional reason without deciding the request

The original convention diagram has useful ingredients: trigger, scope, time and absence of a
defeater. The implication should be interpreted cautiously:

```text
Relevant circumstances + eligible evidence + no established defeating consideration
    -> a reason favoring a form or transformation in this context
    -> comparison with competing consequences
    -> possible justified request
```

A syntactic trigger can establish that a question is worth investigating. It need not establish
that the code departs from a valid norm, that the alternative is better overall, or that a request
is warranted. Several acceptable forms also do not automatically require a question: the reviewer
can simply retain the submitted form. A question earns its place when the uncertainty matters.

For example, avoiding duplicate public API, avoiding handwritten implementation and preserving
an ergonomic interface are different considerations. They can favor different transformations.
The grounds reading supplies actual cases where these costs conflict. Compressing them into
"prefer the library mechanism" discards precisely the information needed to decide the case.

This makes the candidate knowledge object in the plan more specific: evidence for **when and why
a comparison holds**, including its limits. A convention sentence, occurrence count or old request
can contribute to that object, but none is automatically the complete object.

That is a modeling motivation for case-based transfer. It does not show that models can recover
these conditions from sparse cases, discover the right correspondence, or use them correctly.
Those are the empirical hypotheses, and earlier dossier and pinpointing results constrain them.

This is a renewed hypothesis. The July precedent design already proposed transferring the
principle active in a review situation; its prompt-priming implementation failed to establish
transfer despite visible uptake of precedents. The October revised design likewise leaves
economic transfer of contextual preference open. The theoretical connection sharpens that
question, but supplies no exemption from those results or evidence of a new solution.

## 5. The long tail: distinguish knowledge size from mechanism size

The theory does not imply that hundreds of conventions reduce to five principles or a small
collection of checks. General values such as clarity and maintainability can support opposite
local decisions. Listing shared values after seeing a result is weak evidence of compression.

A stable high-level library purpose P can motivate these values. It is a background modeling
assumption, not a specification that determines which value takes priority at each declaration.
Writing down P therefore does not remove the need to learn scope, tradeoffs and change over time.

There are at least three different claims we could make:

| Claim | Evidence it would need |
|---|---|
| Many asks can be described using a few rationales. | Stable explanatory categories; this is descriptive compression. |
| The same reasoning procedure can apply different local knowledge across concerns. | Better review on new concerns without concern-specific code or instructions. |
| A small knowledge resource can predict most useful requests. | Broad prospective coverage and useful discrimination, including competing forms. |

The first does not establish the second or third. Our main hypothesis is the second. It allows
a large, evolving set of local examples and mechanisms as data. A stable small codebase can still
need substantial learned or retrieved knowledge. That is a more realistic interpretation of
maintainability than assuming the community's expectations fit in a short universal checklist.

The relevant compression test is therefore whether adding independent historical knowledge
extends the method without adding a special execution path. Even then, assess final review:
running the same program on every concern is structural reuse, not demonstrated generalization.
The fresh-concern test in the plan is intended to distinguish those claims.

## 6. Recorded requests are incomplete observations of a decision process

A historical review reveals actions taken under particular information, attention, priorities
and constraints. It does not expose all feasible alternatives, all preferences, or all requests
the reviewer could reasonably have made. A merge supplies one outcome, not the boundary of A.

This is a problem of inferring contextual decisions from partial feedback. The same silence can
arise because the reviewer did not notice a departure, judged it acceptable, considered a fix too
costly, or prioritized another concern. The ask alone usually cannot distinguish these accounts.
Likewise, a revised patch might satisfy the request, repair an unrelated problem or reflect the
author's own choice. Its role must be established rather than assumed.

Consequences for the plan are concrete:

- Retain the source situation and stated reasons, not just the requested edit or final merged form.
- Separate explicit counterevidence from unasked examples. The latter can measure practice and
  burden, but are not automatically negative request labels.
- Keep historical recovery, technical support and human request-worthiness separate. None fully
  identifies ≽, A or J; no current metric establishes their complete soundness or completeness.
- Test conditional explanations on independent cases before observing their outcomes. An account
  that can explain any decision afterward offers little guidance for the next PR.

The statement in the older slides that evidence can be reconstructed and therefore the harness
should gather it rather than learn a preference goes beyond the framing. Facts and judgment
interact. Conditional preference learning from cases can use the very same evidence. Explicit
reasoning, retrieval, in-context learning and learned adaptation remain competing or complementary
implementations; the theory does not select one.

Here learning can mean inference from cases by a fixed model or improvement of the knowledge it
receives. Training model weights is a separate scope and feasibility decision. Neither the
notation nor this assessment calls for training a model as the next step.

## 7. How this refines the plan before more runs

The knowledge-transfer draft already has much of the appropriate dataflow and measurement. The
framing adds a sharper requirement for A–B: identify **which missing relation the intervention is
predicted to improve**, and what result would distinguish that claim from neighboring explanations.

| Proposed advance | Discriminating question |
|---|---|
| Discover a missing alternative | With target asks hidden, does the method surface consequential alternatives ordinary additional review misses? |
| Use conditional comparison knowledge | With alternatives and technical facts fixed, do independently sourced conditions change the judgment appropriately on contrasted cases? |
| Translate a supported comparison into a worthwhile request | Does the final review add useful requests while retaining baseline coverage and controlling unwanted burden? |
| Extend across the long tail | Does the fixed method use new eligible examples in a concern outside its tuning set, without custom instructions or code? |

These are distinguishable research questions, not four mandatory new campaigns. Reuse existing
answers first. If the uncertainty is about using evidence already supplied, an autonomous
retrieval experiment is an expensive indirect test. If the uncertainty is finding that evidence,
an exam that supplies the applicable convention removes the very difficulty being studied.

The plan's paired preparation/consumer comparison can test the complete candidate method. It
changes discovery, interpretation and potentially construction together, so its result alone
would not identify which capability improved. Before its suggested 72 model sessions, A–B should
make the predicted intermediate change concrete. Use a cheaper fixed-input contrast only when
it resolves the actual uncertainty; label it as conditional evidence rather than autonomous review.

The case-based method remains revisable. If relevant facts and cases repeatedly arrive but do
not improve the comparison, that lowers the priority of more ingestion. It may motivate learned
adaptation, a different formulation of the judgment, or parking the approach. It does not by
itself show that all missing knowledge has been supplied or that learning will solve the problem.

## 8. Relation to ask–identify–resolve, and the appropriate scope of this note

Ask–identify–resolve describes observable failure locations: select the relevant question,
recognize the concern, and propose a suitable resolution. The theoretical framing describes
what those activities need to establish. They are complementary, with no exact one-to-one mapping.
For example, seeing a duplicate can identify a concern while leaving both the appropriate remedy
and whether to request it unresolved. Resolution can in turn reveal that the original objection
was mistaken. Do not infer a strictly sequential cognitive process from either description.

The early funnel remains useful evidence from its particular runs. It should not be used to
declare attention solved generally, equate correct location with meaningful coverage, or collapse
all later failures into retrieval. The maintained overview's finer loss stages already address this.

Keep this as a conceptual companion to the draft, with three practical consequences: distinguish
feasibility, comparison and request value; test procedural transfer separately from a small rule
set; and match experiments to the uncertainty they can actually resolve. The theory does not
justify another foundation refactor, require new domain classes, or validate a preferred architecture.

## Sources and status of the claims

- [Original theoretical formulation](../../supervisor_update_2026-10/slides.md), especially
  "The shared pieces", "Reviewing", "A convention, in the formulation" and the final design claim.
- [Maintained formulation and qualifications](../project-research-overview.md), especially the
  grounding, requests, measurement, loss-stage and long-term research slides and their notes.
- [Ask–identify–resolve](../ask-identify-resolve.md): the earlier task decomposition and small-run funnel.
- [Knowledge-transfer draft](../plans/2026-10-23-review-knowledge-transfer.md): the candidate mechanism,
  work packages A–E and proposed controlled comparison.
- [July precedent design](precedent-retrieval-design.md), its stopped Mode A in
  [the record of stopped designs](../dead-ends.md), and
  [the October revised design](review-design-decisions-revised-2026-10-19.md): earlier forms of
  the transfer hypothesis and their experimental constraints.
- [Phase A review](../../.claude/worktrees/useful-additions-triage/docs/research/review-reconstruction-phase-a-review-2026-10-20.md)
  and [latest triage assessment](../../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md):
  technical examples, output channels and limits of the positive result.
- [Fixed-search follow-up](../../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md),
  amendment 7; [grounds reading and qualifications](../../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md).

The distinctions above are modeling choices and elementary implications, not new experimental
results or a novelty claim. The claim that contextual knowledge can transfer through a small shared
method is the hypothesis to test. The source cases explain its motivation and limitations.
