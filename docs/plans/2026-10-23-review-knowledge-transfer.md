# Review knowledge transfer across the long tail

**Status: draft for iteration, 2026-10-23.** This proposes a research direction and a first
candidate mechanism. No new experiment, corpus construction or runtime implementation has
been performed for this plan. Model-backed generation, ingestion and judging remain user-run.

## 1. The decision this plan proposes

Prioritize a method that can improve reviewing across different concerns without requiring a
custom implementation for every convention. Keep the current Task/dataflow foundation stable.
Use small experiments to test the breadth of a mechanism before investing in its architecture.

The first candidate is **case-based transfer of review knowledge**: recover what made an earlier
review decision appropriate, determine whether that relationship holds in a new contribution,
and investigate the consequences of a concrete alternative. This is a hypothesis, not a validated
replacement for the strongest ordinary reviewer. Existing precedent retrieval already provides
part of this capability; changing its name or adding a longer prompt would not establish progress.

The immediate deliverable is a concrete, distinguishable intervention and an executable comparison.
Do not begin by building a convention platform, another reviewer hierarchy or a catalogue of checks.
Whole-PR reconstruction and the specialized comparison-session Task remain deferred as current
investments. Neither is a prerequisite for testing the candidate described here.

## 2. The problem we need to solve

The census spreads 1,833 asks over roughly 400 conventions at its chosen grain. Its top ten
entries cover about one fifth of asks and its top fifty about half. The four conventions behind
the deterministic-detector experiment cover about 3%. The exact counts vary with codebook and
classification; the practical lesson is that a few manually implemented rules have a low ceiling.

Our desired economy is different: additional historical examples should let a fixed method handle
additional situations. Acquiring another convention should usually change the knowledge supplied
to the system, rather than require another producer, prompt branch or execution path.

There may be fewer underlying capabilities than named concerns: recognizing a design role,
finding a relevant comparison, constructing an alternative, testing its consequences and assessing
whether its benefit warrants a request. That compression is plausible but unproven. Reusing the
same words or tools across cases does not demonstrate that the difficult reasoning transfers.

Success therefore has two requirements: better useful review, and evidence that the method extends
beyond the particular concerns used to develop it. A reliable check for one narrow convention can
still be useful engineering, but it does not satisfy this research objective by itself.

## 3. Already answered? Constraints from the record

| Observation | What it changes about this proposal |
|---|---|
| Exact convention supply substantially improves recovery on selected asks; ask-free shortlists and pinpointed delivery have not reliably carried that gain. | Knowledge matters, but relevance, applicability and use must be tested independently. Do not repeat the ceiling test. |
| Examples plus disposition instructions have some positive results, including GPT's stage W under exact convention supply. Later ask-free results are mixed or negative. | Do not claim prompting or examples never help. A positive result conditional on target knowledge is insufficient for autonomous transfer. |
| Reconstruction proposals reached consumer findings, including the compiling normalizer generalization. No registered stable historical-ask gain followed. | Transmission is feasible. Additional plausible edits are insufficient evidence of better review. Human usefulness labels on the latest additions panel remain pending. |
| At 33066, avoiding a constructor in a different proof did not establish redundancy in the submitted design. | Compare the role and value of the submitted object; difference from an independent solution is not itself an objection. |
| With search fixed at 33117, all six assisted Opus sessions connected `to_fun` to the handwritten twins, but only one filed the change. | Retrieval and an explicit correspondence can succeed while construction or judgment still fails. A comparison stage alone is not an established solution. |
| Generated interfaces at 33117 have real client-call differences; the grounds reading contains legitimate exceptions to avoiding duplication. | Retain costs and contrary examples. A generic preference for generation, reuse or fewer declarations would decide the question prematurely. |
| A proposed topology generalization compiled under stronger assumptions. Some trial edits failed because required imports were absent. | Check the relationship claimed by a proposal. Neither successful compilation nor a failed trial alone settles the comparison. |
| Forced filing, artifact-only selection and convention detectors have already encountered volume, judgment or coverage limits. | Do not replace the missing capability with more filings, confidence gates or one detector per concern. |

The primary reading list and branch locations are in section 12. These are development findings,
not independent evidence for the new candidate. The historical asks also omit potentially useful
suggestions, so historical recovery and request-worthiness need separate measurements.

## 4. The hypothesis and its proposed mechanism

**Hypothesis:** a shared procedure can use prior review cases to recover conditional design
expectations, relate them to a new PR, and produce useful requests across different concern families.

The candidate changes what the preparatory investigation establishes. Instead of supplying only
"this convention may apply" or an independently reconstructed contribution, it supplies a sourced
relationship between the current design, relevant earlier decisions and a proposed alternative.
Its distinctive content is the applicability argument and the consequences that could defeat it.

The same procedure would:

1. Identify consequential choices in the visible PR at declaration, family, file or PR scope.
2. Query existing dated sources for comparable design roles, mechanisms and prior decisions.
3. Recover what the source actually supports: a requested change, stated reason, relevant context
   and any observed response. Separate quotation, technical fact and inferred rationale.
4. Explain the correspondence to the current choice and where that correspondence breaks down.
   Look for relevant competing evidence within the same investigation budget.
5. Investigate a concrete alternative with existing tools. Check the consequences relevant to the
   claim: for example, preserved client calls, changed automation or implication of assumptions.
6. Hand the ordinary reviewer the evidence, limitations and alternative. The reviewer may request
   a change or retain the submitted design under the same output contract as the control.

These are investigation steps, not mandatory ledger cells or a quota of objections. A source can
be relevant without settling the decision. Missing counterevidence is not evidence that none exists.
The method must discover its targets from the PR; a maintainer's target comment is never an input.

For a concrete development illustration, consider 33117's handwritten `fun_*` twins. The preparation
would search for prior handwritten/generated API decisions, rather than only the current lemma
names. A useful result would establish both the maintenance saving from generation and any changes
to existing client expressions such as `Meromorphic.fun_sum h`. The proposed transformation could
then preserve a useful wrapper, convert only compatible members, or retain the current form if the
cost dominates. These are possible outcomes to investigate, not recommendations established here.
The next different concern must work through the same procedure with different source evidence.
33117 itself is an already studied fixture and is not scheduled for more model runs by this plan.

## 5. What data moves through the method

Start with source excerpts and small retained notes using existing observation references. The
following is a content contract for the experiment, not a request to implement new schema classes.

| Value | Content required by its consumer |
|---|---|
| Historical case | Source identity/date; code and discussion sufficient to understand the choice; exact requested change; stated reason if present; observed outcome if actually available |
| Candidate expectation | A revisable account of the circumstances and benefit; known costs, scope and exceptions; supporting sources; explicit uncertainty |
| Target correspondence | Which choice in the new PR is related, why the relationship is relevant, and material differences from the historical case |
| Investigation result | Concrete alternative; checks performed and their exact outcomes; consequences established, contradicted or unresolved |
| Delivered review | Ordinary final findings, consumed by the shared evaluation path |

A past request is evidence of that decision, not a universal rule. An author's later edit is not
an independent usefulness label. Unasked code is not a negative example merely because it merged.
Cases that explicitly justify retaining a local form or rejecting a proposed change are especially
useful contrasts, but their availability must be reported rather than manufactured.

Derived notes may be computed now from eligible historical sources. Their information must still
respect each target's cutoff and exclusions. A codebook or summary prepared after reading a target's
asks is development material; removing its direct quotation does not make it independent again.

## 6. How the candidate differs from earlier designs

| Earlier design | Difference this candidate must actually demonstrate |
|---|---|
| Existing lexical/dense precedent retrieval | A useful relationship between retrieved evidence and the target, not merely a relevant comment or a new index |
| Selector-picked convention sentences and pinpointed rules | A supported account of applicability and competing consequences, without asserting the target's historical conclusion |
| Examples and proposed dossiers | Transfer to new PRs without being given the applicable rule or place; no convention-specific exam that supplies the missing target |
| Whole-PR reconstruction | Investigation of choices in the submitted contribution; no requirement to construct an independent contribution first |
| Demonstrated-change and compile-then-file proposals | Technical construction supplies evidence; it does not automatically establish that a change should be requested |
| Artifact-only finding selection | No new generic scorer or gate over the same candidates; the intended gain is better investigation and proposal content |

If the actual input difference reduces to more examples, a generic principle, an authority paragraph
or extra computation, say so. Reuse the relevant earlier result or test that simpler explanation.
The proposal earns further work only if its new information and predicted effect can be stated
concretely. A more elaborate representation is not itself evidence of a new mechanism.

## 7. Dependency order and work packages

```text
A. Check the distinct mechanism and existing capabilities
  -> B. Prepare concrete development examples and one recipe
    -> C. Run a bounded autonomous comparison across concerns
      -> D. Resolve the uncertainty that changes the next decision
        -> E. Test transfer on a broader untouched panel
```

Runtime fixes can proceed independently when they have an active consumer. Corpus expansion,
learned adaptation and new Task classes are conditional branches, not prerequisites for A–C.

### A. Check the premise and choose the first implementation

Use the existing results and up to six saved development cases. Reuse their assessments; do not
repeat the additions triage, reconstruct the census or commission another broad failure taxonomy.
For each case, identify the missing information or relationship and whether the current record
already supplies it. Include a case where the relevant mechanism was known and still rejected.

Inventory the source views and retrieval operations available in the selected implementation
checkout. Inspect both existing precedent paths before proposing another retriever. The Task/data
refactor is on `develop`; the operations work and its implementation review are on `review-operations`
at this draft's writing. Verify integration status before executing anything based on that branch.

**Output:** one brief mechanism table and the chosen input difference. Stop or revise if the
candidate duplicates an old intervention or depends mainly on new scripts for individual concerns.

### B. Make the mechanism reviewable before building it

Prepare worked examples spanning at least four distinct concerns, such as API redundancy,
generation/interface design, naming organization, and assumptions or automation. Familiar PRs can
illustrate the mechanics, but cannot count as new evidence of benefit. Include contrary cases.

For each example show: the old source, what the baseline could already retrieve, the additional
relationship this method would establish, and what observation would change the recommendation.
The same procedure must handle the examples. A special prompt or trigger per concern is evidence
that the proposed compression has not yet been achieved.

Prepare one recipe with source eligibility, prompts, retained outputs, resource limits, controls
and measurement. Use existing source excerpts and session/context handoffs initially. Identify any
missing engineering as a concrete dependency, with a caller and a minimal acceptance check.

**Output:** executable preparation and review inputs, plus a short protocol beginning with
"Already answered?". Proposed planning budget for A–B together: one focused workday, revised
explicitly if the missing work warrants it. No model campaign or new knowledge store follows by default.

### C. Test the method across concerns without target asks

The first model-backed comparison should exercise autonomous target and source selection.
A suggested reconnaissance panel is six fresh PRs spanning at least four observable change
contexts, selected before reading their review outcomes. Include ordinary PRs, preserve AI-authored
PRs where present, and allow cases without agreed asks. Selection by changed-code characteristics
is allowed; selection by whether this method will recover a known ask is not.

Use the strongest intended reviewer on one fixed route. A cheaper model can establish operational
correctness, but its results cannot settle the benefit on the intended reviewer. Freeze these two
conditions before running:

| Condition | Preparation | Consumer |
|---|---|---|
| Ordinary additional work | The producer investigates the visible PR with the normal tools and records ordinary review notes | Ordinary final review with those notes |
| Case-based transfer | The same producer uses the procedure in section 4 and records the resulting evidence and proposals | The same final review with that material |

Both preparations have the same source access, model, route, investigation limits and output
allowance. Both consumers use the same contract, tools and limits. The treatment changes the
preparatory method. This comparison includes the producer's effort rather than treating an
expensive helper artifact as free assistance to a weaker reviewer.

Three independent preparation/consumer repetitions per PR give **36 final reviews and 36
preparatory sessions** on this suggested panel. Regenerate preparation per repetition; a fixed
sketch would estimate a different source of variability. An operational smoke precedes the batch.
The counts are adjustable reconnaissance bounds, not a claim of statistical power. Before launch,
estimate total tokens, wall time and account/quota use from the actual selected route; provide
complete manual commands and do not launch model work from this drafting task.

Equal limits do not ensure equal consumed resources. Report actual preparation and consumer use,
including index or corpus preparation costs. A large difference requires a further resource
comparison before claiming efficiency or superiority. Keep any ordinary one-pass results as a
separately identified reference, not a substitute for this additional-work control.

**Output:** a result by PR and concern, including failures, lost coverage and actual resources.
This small, deliberately varied panel can reject a candidate or motivate another test. It cannot
estimate population-wide yield or establish that a broad capability has been learned.

### D. Choose the next step from the observed failure

| Result | Next decision |
|---|---|
| Relevant source cases are not found | Examine query/role representation on these failures. Build a different retriever only if it adds missing evidence; do not expand the corpus automatically. |
| Relevant cases arrive, but applicability is inferred incorrectly | Test that relationship on saved contrasted cases. Consider learned adaptation if the fixed model repeatedly misuses sufficient evidence. More retrieved comments alone have not earned priority. |
| The correspondence is useful, but trial edits are misleading | Fix the shared construction/checking defect and test it across concerns. Avoid a separate verifier per convention. |
| Better supported proposals arrive, but consumers lose them | Isolate handoff with information held fixed. Do not add the missing answer and attribute the gain to communication. |
| The apparent gain is confined to one family or consists mostly of optional edits | Keep any cheap useful component, but stop claiming a general mechanism. Park or change the research bet. |
| Useful gains extend across different concerns without greater unwanted burden | Advance the fixed method to E; run a targeted ablation only if it could change the design. |

One possible ablation reuses the exact retrieved source set and compares raw cases with the
derived applicability/consequence notes under a common context allowance. That isolates the
interpretation contribution conditional on those sources. It does not test autonomous retrieval.
More examples, more context and the generic additional-review control are simpler explanations
to consider. Do not schedule every ablation regardless of the result.

### E. Test breadth and extension before expanding the architecture

Freeze the method, then evaluate on untouched PRs beyond the reconnaissance panel. Choose the
population and size from the claim and pilot variability before reading outcomes. Retain a broad
unselected component so a balanced development panel cannot masquerade as expected real-world yield.

Test two distinct claims: performance on new PRs under a fixed source policy, and extension to a
concern not used to tune the procedure. For the latter, earlier eligible examples of that concern
may be supplied as data; change neither the procedure nor its prompts. This is transfer through
additional knowledge, not zero-shot discovery of a convention with no evidence anywhere.

Report results by concern and PR as well as overall, and record any manual tailoring. One concern
dominating the gain, or needing an implementation patch for each new concern, weakens the broad
claim. Family labels are descriptive analysis, not a permanent ontology or runtime router.

## 8. What counts as better review

Use final delivered findings as the primary output. Retain preparation, submissions, anchoring
and finalization records to explain losses; never silently score a richer intermediate channel.

- **Historical recovery:** use the shared matcher or issue judge, naming its version, population,
  channel and repetitions. Preserve disagreements. Different matcher versions remain separate
  instruments unless calibrated; no new private matcher is part of this plan.
- **Useful additions:** distinguish new concerns from better repairs of already covered concerns.
  Assess exact findings with the shared human rubric, including control findings under the same
  presentation. Pending labels stay pending; model technical-support labels are not usefulness.
- **Costs and losses:** report wrong or excessive demands, unresolved proposals, useful baseline
  concerns missed by treatment, finding volume and resources. Unasked findings are not automatically wrong.
- **Breadth:** show which concerns improved, remained unchanged or worsened. Count repeated sibling
  findings and repeated PR sessions transparently; they are not independent discoveries.

Do not replace these dimensions with an arbitrary net score. Before the user-run pilot, state the
smallest improvement and maximum burden that would justify the next investment. A noisy result
may justify parking the method without establishing zero effect. If human reading is sampled,
define the sampling before reading and keep conclusions within what that sample supports.

## 9. Stable foundation and conditional engineering

Use APE Tasks and the standard orchestrator for model operations. Small deterministic rendering
and joins remain functions. Use shared observation/context lineage, matching, result readers,
retrieval and verification; Python and scaffold tools must reach the same domain implementations.

The initial composition is: eligible source view -> preparation Task -> selected notes/evidence
output -> context rendering -> ordinary review Task -> finalized findings -> shared evaluation.
Retain the actual sources and rendered context, including truncation. Data identifies the content
and its occurrence; it does not need a new global experiment class or another execution ledger.

If a preparation Task genuinely needs episode-bound retrieval tools that the selected checkout
cannot provide, complete that part of the operations foundation on its shared path. A folder
session cannot be presumed to have tools it has not been granted. Do not work around that gap
with a private runner. A bounded fixed-source diagnostic may proceed meanwhile, labeled as such.

Add schema classes or an index only when repeated consumers need them. Specialized compiler-style
review representations, a blackboard and a convention-specific plugin catalogue are outside this
draft. Existing narrow checks can remain useful utilities; they are not the main coverage strategy.

## 10. Alternatives and adoption boundaries

Case-based transfer is the first candidate because the exact-knowledge gains motivate learning
from review decisions, while the failures expose a missing applicability/use capability. The
record does not establish that this representation will fix it.

If relevant evidence is repeatedly available but the fixed model cannot use it well, consider
learned adaptation from contrasting decisions rather than another instruction layer. That requires
a separate data/label feasibility check, an adaptation-capable model and independent evaluation;
historical requests alone do not supply clean negative labels. It is not a prerequisite here.

We can adopt only the source/content contract, a demonstrated cross-concern checking improvement,
or a successful preparation method. Each can use the existing foundation without committing to
the other parts. We can also reject case-based transfer while retaining the broader research goal.
No uncertainty in this plan makes completion of the census, dossiers or all human panels mandatory.

## 11. Immediate handoff and questions for iteration

The next work is **A–B**, not the full experiment sequence:

- [ ] Confirm the implementation checkout and reuse existing results to identify the distinct mechanism.
- [ ] Prepare worked inputs across four concerns, including contrary evidence and predicted failures.
- [ ] Decide whether the candidate adds information beyond existing precedent/example treatments.
- [ ] Specify the paired preparation/consumer recipe, eligible source view and evaluation channel.
- [ ] Produce a bounded user-run cost/command plan, or recommend stopping before implementation.

The main design questions to settle while iterating are whether case interpretation is the right
first intervention; what evidence would justify treating it as a shared capability; and how much
research effort to allocate before pivoting toward learned adaptation or another mechanism.
The working examples should make those decisions concrete. A polished architecture is not an
acceptance criterion for this phase.

## 12. Reading list and branch-aware evidence

Paths below are relative to the repository root unless linked. Planning inspected `develop` at
`4c759195` and the worktree heads listed here; check them again before implementation.

- [Questions already answered](../questions.md), especially conventions, knowledge and filing;
  [stopped designs](../dead-ends.md), especially detectors, selection and filing contracts.
- [Context and evidence needs](../todo/review-context-needs.md) and
  [convention discovery](../todo/conventions-nature.md): existing owners of these open questions.
- [Dossiers adversarial review](../research/conventions-dossiers-review-2026-10.md): what the
  proposed understanding test would and would not establish.
- Existing retrieval: `src/mathlib_review/retrieval/precedents.py` and `precedent_index.py`;
  existing session/context composition: `src/mathlib_review/analysis/sessions.py`.
- [Operations foundation](2026-10-22-review-operations-foundation.md), with implementation/review
  in `.claude/worktrees/review-operations/docs/research/` (`review-operations@01008813`).
- [Reconstruction results](../../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md)
  (`review-reconstruction@eecb7d18`): Phase A and the fixed-search follow-up.
- [Grounds reading and qualifications](../../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md)
  (`grounds-reading@b1b2d859`): conditional costs and legitimate exceptions.
- [Additions triage and independent review](../../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md)
  (`useful-additions-triage@f2e4ba95`): stopping decision, pending labels and output-channel corrections.
- `.claude/worktrees/generation-suppression/docs/plans/2026-10-06-generation-without-suppression.md`
  (`generation-suppression@d7c65fa6`): stage W's positive result under exact convention supply.
- `.claude/worktrees/demonstrated-change/docs/plans/2026-10-18-review-as-demonstrated-change.md`
  (`demonstrated-change@e9b9b6e0`): corrections to the compile-then-file diagnosis and its limited gains.
