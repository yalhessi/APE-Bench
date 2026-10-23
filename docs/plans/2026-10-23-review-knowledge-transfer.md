# Review knowledge transfer across the long tail

**Status: revised draft for iteration, 2026-10-23.** Incorporates the assessment of Claude's
response. The [review record](../research/review-knowledge-transfer-plan-review-2026-10-23.md)
preserves its text and explains the decisions. No new model runs, corpus construction or runtime
implementation have been performed for this plan. Model-backed generation, ingestion and judging
remain user-run. The immediate handoff is A-B below, not a full campaign.

## 1. The research decision

Prioritize a method that improves reviewing across different concerns without a custom
implementation for every convention. Keep the Task/dataflow foundation stable. Additional
knowledge should usually enter as data; the procedure should earn its complexity through better
review on situations beyond its development cases.

The first candidate is **case-based transfer of review knowledge**. Recover a
conditional reason from independent earlier decisions or library evidence, relate it to a choice
in the visible PR, and use it to decide what to investigate. The investigation can support a
revision, defeat the proposed revision, or leave the choice unresolved. Ordinary review still
decides whether a request is justified.

This reopens the July precedent direction and October library-knowledge question. It is not a new
solution by virtue of its name or representation. The proposed difference is that conditional
knowledge guides the investigation of consequences, rather than merely priming a reviewer with
similar comments. Whether this adds anything to ordinary source-grounded review is unproven.

The next deliverable is four worked choices and **one shared, executable comparison recipe**.
Use them to decide whether a small pilot is worth running. Whole-PR reconstruction remains parked;
a convention platform, a new hierarchy of reviewers and a detector catalogue are not prerequisites.

## 2. What the existing results permit us to believe

The census spreads 1,833 asks over roughly 400 conventions at its chosen grain. Its top ten cover
about one fifth and its top fifty about half; the deterministic-detector experiment's four
conventions cover about 3%. These are descriptive, codebook-dependent counts. They motivate a
method with broad reuse, without proving that the knowledge itself can fit in a short rule list.
A small stable codebase may need a large, evolving knowledge resource.

| Existing observation | Consequence for this plan |
|---|---|
| July Mode A delivered precedents and showed uptake, but its early gain did not replicate: 13 versus 11 covered on 41 shared PRs. | Name this predecessor. Another priming prompt needs a concrete difference and an appropriate repeated comparison. |
| Exact convention supply improves selected-ask recovery; ask-free shortlists, pinpointing and verification framing have not reliably carried that gain. | Do not repeat the ceiling test. The missing capability could be selection, applicability or use, and these need different tests. |
| GPT stage W improved under exact convention supply; DeepSeek examples/precedence also have positive conditional results. | Prompting is not categorically exhausted. These results do not establish autonomous transfer. Stage W is separate from the detector pass-through experiment. |
| Of 41 difficult free-reviewer misses, the library decided 7, or 5 on recheck; for 19 it exposed options while a choice remained. | Pair facts with conditional project knowledge as a candidate intervention. Use the 19 as a development pool, not a new mandatory campaign. |
| Ask-blind decision-context packets did not improve recovery in the reconstruction probe; some deciding sources were missed or misidentified. | Evidence gathering and its interpretation are both uncertain. Do not assume a useful source will be found. |
| At 33117 with search fixed, all six assisted Opus sessions related `to_fun` to the twins; one filed. Three of five declines involved a faulty trial. | A correspondence alone is insufficient. Repair incidental construction failures; distinguish technical failure from a reason to retain the design. |
| Generated `fun_sum`/`fun_prod` forms have real client-call differences. At 33066, an independent solution avoiding the wrapper did not establish its redundancy. | Compare the submitted object's role and interface. Compilation or a different solution does not establish preference or request value. |
| The grounds reading found a recurring reason and substantive exceptions, not a universal priority. Most asks do not state a reason. | Retain contrary cases and uncertainty; distinguish stated reasons from inference. Do not encode 'prefer generation/reuse' as the answer. |
| The compiling normalizer proposal reached final review; useful-addition labels remain pending. Forced filing and detectors encountered burden or coverage limits. | Score final findings, retain losses, and assess request-worthiness separately. More technically sound proposals alone are insufficient. |

These are development observations, not independent validation of the new candidate. The 3-4
remaining asks out of 93 for redundancy/generation bound those two families, not this broader
research goal. Repeated runs overlap substantially, which makes pure resampling a weak bet;
it does not remove the need for an ordinary additional-work control.

## 3. The mechanism, its predictions and its failure conditions

**Hypothesis:** a fixed procedure can use independently sourced conditional knowledge to choose
better investigations and make better requests across different concerns.

The same procedure would:

1. Identify consequential choices in the visible PR. Do not start from a maintainer's target ask.
2. Search existing dated sources for comparable roles, mechanisms and decisions. Inspect source
   context, not just a retrieved comment or an embedding score.
3. Recover the reason the source supports and the circumstances limiting it. Separate a stated
   reason, an observed fact or outcome, and the investigator's inference.
4. Relate that reason to the target and identify the uncertainty that could change the comparison.
   Consider contrary evidence within the same budget. A purported benefit may be absent here.
5. Investigate that uncertainty with existing tools: inspect a family, compare naming practice,
   try client calls, test assumptions or automation, or construct an alternative. Repair incidental
   errors before treating a failed trial as evidence against the alternative.
6. Give ordinary review the comparison, actual checks and unresolved consequences. The final
   reviewer can request a change, retain the submitted form, or omit an insufficiently supported
   concern under the same contract as the control.

This is a method for allocating investigation, not a mandatory tradeoff ledger. Some reasons
remain matters of scope or judgment; no executable check is guaranteed to settle them. Counting
uses, successful compilation and a recorded earlier request are evidence, not universal policies.

| Predicted effect | What would distinguish it from an attractive explanation afterward |
|---|---|
| A source reason changes what is investigated. | Retained inputs and traces identify the eligible source, target correspondence and a relevant investigation that ordinary preparation missed or handled incorrectly. |
| The result changes the comparison appropriately. | The proposal responds to established costs or contrary evidence, including retaining a useful local form. Merely mentioning both sides is insufficient. |
| Better investigation improves review. | The delivered requests improve in historical recovery or assessed usefulness, without an offsetting pattern of unwanted demands or lost useful coverage. |
| The procedure extends through knowledge. | An untouched concern benefits from new eligible examples without a new prompt branch, trigger or checker. |

A trace showing a check was performed is a mechanism observation, not success by itself. If the
producer writes a more complete account but the comparisons and final requests do not improve,
the intervention has not earned expansion. If ordinary preparation does the same useful work,
prefer the simpler instructions. A positive result in one family supports that family first.

**Development illustration: 33117.** 'Prefer generated twins' is not the intervention. The
maintenance reason must be compared with the actual interface: handwritten
`Meromorphic.fun_sum h` works while the generated analogue exposes different parameters. The
investigation could support retaining a wrapper, converting compatible members, or retaining the
submitted form. Those are alternatives to investigate, not established recommendations. This PR
and 33066 remain fixtures; neither receives another model campaign by default.

## 4. Data and scope boundaries

Use source excerpts and small notes with existing observation references. These are content
requirements, not new schema classes or a second provenance ledger.

| Value | Required content |
|---|---|
| Source case | Identity/date, relevant code/discussion, requested change and stated reason when present; observed response only when actually available |
| Conditional knowledge | What favors a form in which circumstances; costs/exceptions; supporting sources; uncertainty and inferred elements |
| Target correspondence | The visible choice, the relevant relationship and material differences from the source |
| Investigation result | Alternative or comparison; checks and exact outcomes; consequences established, contradicted or unresolved |
| Delivered review | Ordinary finalized findings through shared evaluation |

When a reason is unstated, the method may infer one from code, discussion and contrasting practice,
but must mark that inference. It may look for better evidence or leave the comparison unresolved.
Do not invent maintainer authority, fill a compulsory ledger or treat lack of explicit rationale
as proof that there is no transferable knowledge.

The source policy is independent historical knowledge for generalizable conditions, not lookup
of the target's historical review. Exclude the target's asks, later fixes, discussion and summaries
of those outcomes, including cross-PR references caught by existing gates. Library evidence must
be available in the permitted episode view. Derived notes must respect the target's cutoff and
exclusions even when computed now. An ask-informed codebook remains development material.

A historical request is evidence about one decision. An author's edit is not an independent
usefulness judgment. Merged or unasked code is not automatically a negative example. Explicit
reasons for retaining a form are valuable contrasts even if they occur once. Model weights remain
fixed in this plan; training is outside this work rather than another dependency to resolve now.

## 5. The dependencies

```text
A. Bounded worked choices: what information/action would actually differ?
  -> B. One recipe, local source/tool checks, costed manual handoff
    -> C. Small paired pilot on two PRs, or one targeted diagnostic instead
      -> D. Diagnose the loss and decide whether to stop, revise or expand
        -> E. Untouched broader panel, new concern and second-model validation
```

The operations foundation is a shared engineering dependency of a tool-using producer. Source
expansion, another index, a convention ontology and a new generic experiment abstraction are not.
Do not turn the branches below into a sequence that must all be completed.

### A. Make four choices concrete from existing evidence

Prepare four worked choices across at least three concern families. Reuse existing readings and
traces. The 19 `library_partial` asks provide candidates beyond 33066/33117; do not reread all 19
or pool sessions and asks into a prevalence estimate. Include a justified retention or contrary
case and at least one concern outside redundancy/generation, such as naming, assumptions or docs.

For each show:

- What ordinary review already knew, retrieved, attempted and delivered, citing the saved record.
- A missing or misused relationship, or an explicit finding that the record already supplies it.
- An independently eligible source and the conditional reason it supports. Mark ask-informed
  source selection as development assistance, not evidence of autonomous retrieval.
- What that reason would lead the session to investigate and what result could defeat the revision.
- The exact addition relative to prior priming, dossiers, decision-context or demonstrated-change
  inputs. If there is no addition, say so rather than declare a new mechanism.

**Deliverable:** one short worked-example file and a common procedure. This is not a new taxonomy,
a 35-place audit, or another additions panel. If a focused pass produces only restated rules,
authority or per-concern instructions, revise or park this candidate before building it. Failure
to find a stated reason in this small set does not settle all knowledge-transfer designs.

### B. Prepare one executable recipe and check its real dependencies

Use the selected checkout's existing retrieval and session paths. On the worked cases, inspect
what a query derived from visible code returns under the actual cutoff and exclusions. Distinguish:
no eligible evidence identified; an eligible source missed by retrieval; a misleading analogue;
and a useful source whose relevance the model may still misuse. Retain queries and returned excerpts.

This is a bounded feasibility check, not a new retrieval benchmark. The 43 library/sibling analogue
asks and the old dense-index benchmark answer related but different questions. The relevant
historical case need not be the exact analogue named in the target's review. Do not require a
universal hit@5 threshold, rebuild the corpus/index, or assume semantic relevance can be judged
with CPU alone. Local deterministic queries and manual reading suffice for this handoff.

Specify one producer prompt, source policy, Task inputs, note allowance, context rendering,
consumer and resource limits. Ordinary and treatment preparation must have the same opportunities
to use evidence. State which inference the pilot tests and which source/model/route is held fixed.
Before reading pilot outcomes, state what improvement in delivered requests would justify another
batch, what burden would stop it, and the maximum resource allocation. These are investment
criteria for this pilot, not universal numerical laws for reviewing.

**Deliverable:** a `PROTOCOL.md` opening with 'Already answered?', no-spend preflight results,
complete verified manual commands and a route-specific cost estimate. No model work launches
from plan drafting. A-B together should take one focused workday; if they need substantial new
infrastructure or corpus work, report the concrete obstacle and reconsider the investment.
Cost any judging, transport smokes and retry allowance separately from the main generation count.

### C. Run one small test that answers the remaining question

**Default: a two-PR autonomous pilot.** Select both PRs before reading their review outcomes,
using visible change characteristics to cover different contexts. Keep AI-authored contributions
eligible and allow PRs without agreed asks. Record whether the selected targets are genuinely
unseen by the method's development process; a fresh pair cannot be manufactured from old fixtures.

Use the strongest intended reviewer on one fixed route. Freeze these two conditions:

| Condition | Preparation | Consumer |
|---|---|---|
| Ordinary additional work | Investigate the visible PR normally with all permitted sources/tools; record ordinary review notes | Ordinary final review using those notes |
| Investigation using conditional reasons | Use section 3's shared procedure with the same source access/tools and note allowance | The same final review using that material |

Match model, route, producer/consumer limits, source policy and final output contract. The baseline
is allowed to compare alternatives and cite precedent; do not weaken it to make the intervention
distinct. Regenerate preparation and review for each independent repetition. Three repetitions
per PR and condition give **12 preparation sessions + 12 final reviews = at most 24 main sessions**.
This is the first batch, not the first installment of an automatically authorized 72-session run.

Use existing transport evidence where sufficient. Any additional live smoke is separately named
and costed before the batch; a cheap model establishes operation, not intended-reviewer benefit.
Estimate processed tokens, actual subscription/account impact, wall time and billed spend from
the selected route. Historical usage warns that this can consume substantial interactive capacity;
it is not a verified current schedule or assurance that a zero-billing model is available.

**Alternative: one fixed-evidence diagnostic.** Choose this instead when A-B locate the uncertainty
in use of already supplied evidence, or source/tool availability prevents an informative autonomous
pilot. Give both conditions the same eligible source set and visible target; change the preparation
method. Use the same paired composition and repetition accounting, with no more main sessions than
the default. It tests investigation/use conditional on supplied evidence, not source discovery or
autonomous transfer. Do not handcraft the treatment's final recommendation. Do not routinely run
this diagnostic, fixture replays and the autonomous pilot in sequence.

**Deliverable:** retained sources, prepared notes, rendered contexts, delivered findings and a
short result by PR with actual resources. Equal limits do not imply equal consumption. Neither
two PRs nor three repetitions estimates population-wide yield or demonstrates broad transfer.
Record any one-time knowledge preparation and manual curation separately from session usage.

### D. Spend only on the failure that matters next

| Observed result | Next decision |
|---|---|
| No useful eligible sources arrive. | Separate source availability from query/selection failure. A fixed-source diagnostic is justified only if such evidence actually exists and testing its use would change the next decision. |
| Useful sources arrive, but correspondence or judgment is wrong. | Inspect the exact comparison. More retrieval or a compulsory ledger has no demonstrated benefit; test a concrete interpretation change or park the candidate. |
| Relevant investigations fail for incidental construction defects. | Repair the shared defect and test the claimed relation, including interface or assumption consequences. No verifier per convention. |
| Better proposals disappear during handoff/finalization. | Hold information fixed and repair that shared path. Do not silently score richer intermediate proposals. |
| The method performs checks but final review does not improve. | Do not expand for mechanism compliance alone. Decide whether one identified fix is worth another bounded test; otherwise stop. |
| Useful improvement appears across different choices with acceptable burden. | Consider the next tranche or independent validation. A targeted ablation is optional when it could change the implementation. |

For a historical-recovery claim, 0/3 control versus at least 2/3 treatment on different PR kinds
is a particularly clear pilot pattern. It is not the only legitimate outcome: better useful
additions or fewer unjustified requests can matter. Conversely, one attractive optional edit or
one noisy matcher gain does not justify a large campaign. Read the exact delivered findings before
choosing the next spend, and leave unresolved human usefulness judgments pending.

One possible ablation holds retrieved sources fixed and compares ordinary preparation with the
derived comparison under a common context allowance. This isolates use of those sources; it does
not validate retrieval. Do not schedule every conceivable ablation before seeing a result.

### E. Test breadth before scaling the architecture

Only after an informative pilot, freeze the method and choose an untouched broader panel for the
claim being made. Six PRs across four contexts remain a possible reconnaissance expansion, not a
requirement. If the first two were run unchanged, adding four uses at most 48 more main sessions;
if prompts or source policy changed, analyze the new version separately. Include a broad unselected
component before claiming real-world yield, and choose size from pilot variation and the claim.

Test extension to a concern outside the tuning examples. Earlier eligible examples may be added
as data; neither prompts nor code acquire a tailored path. Record the development concerns before
running, and select the held-out concern without choosing it for an observed treatment success.
Report gains, losses and manual tailoring by concern; family labels are analysis, not a runtime router.

Include a second model before claiming general harness benefit. Its first cell can be a small
matched replication. Record model-by-method results rather than assuming a gain or failure transfers.
Sonnet's different fixture behavior is a reason to measure an interaction, not to disqualify it.
Do not assume DeepSeek serving capacity is available. Cross-route tool smoke tests and cross-model
reviewing validation answer different questions.

## 6. What counts as better reviewing

Use **final delivered findings** as the primary output. Retain submitted, anchored and finalized
counts and content to locate losses. Preparation is explanatory evidence, never silently scored
as if the reviewer delivered it.

- **Historical recovery:** use shared matching/judging, identifying instrument/version, population,
  final channel and repetitions. Report disagreements. Uncalibrated matcher versions stay separate;
  do not introduce a private matcher or require agreement as a substitute for inspecting a dispute.
- **Useful requests:** assess the exact pilot findings, including controls, under the same human
  rubric and blinded condition labels where feasible. Distinguish new concerns and better repairs.
  A small pilot reading does not require completion of every older triage panel. Pending is pending;
  technical support is not a usefulness label.
- **Burden and losses:** inspect wrong, excessive or poorly supported demands; useful control
  concerns lost by treatment; finding volume and author effort. No historical ask is not proof of
  a false positive, and one extra finding is not a universal failure threshold.
- **Mechanism and cost:** identify source use, correspondence, relevant checks, changed comparisons,
  finalization losses and actual resources. Repetitions and sibling findings are not independent
  discoveries; retained traces do not make every causal claim identifiable.

Do not collapse these into a new net score. The next-investment decision considers whether a useful
change survived finalization, whether the pattern extends beyond one tailored example, what was
lost, and what it cost. A noisy small result can justify parking the bet without proving zero effect.
A cross-family positive pilot warrants validation, not a claim that the long tail is solved.

## 7. Stable engineering foundation

Reuse APE Tasks, the standard orchestrator, observation/context lineage, existing retrieval,
verification, result readers and evaluation. Deterministic rendering and joins remain functions.
Python and scaffold tools must call the same domain operations.

```text
eligible source view -> preparation Task -> retained notes/evidence observation
  -> ordinary context rendering -> ordinary review Task -> final findings -> shared evaluation
```

The tool-using producer is a consumer of operations increment 4, with this experiment's recipe as
the increment 5 consumer. Reuse the existing comparison-session handoff's resource binding and
publication design. Its original scope supplies a decision and alternatives; autonomous selection
in this study must come from the producer's visible-PR investigation. Neither a specialized
comparison Task nor a new runner is required if the shared episode-bound session can do the work.

At this revision, the foundation is on `review-operations@01008813`; the comparison-session handoff
is written there and increment 4 is still planned. `develop@72bff55e` has the Task/dataflow refactor
but not that branch's operations foundation. Verify integration before implementation. A generic
folder-session Task cannot be assumed to have episode-bound retrieval or Lean tools. Complete the
minimal shared binding when the recipe needs it; a fixed-source diagnostic can be prepared meanwhile.

Do not add a new knowledge store, global experiment class, execution ledger, compiler-style review
representation or convention plugin catalogue for this pilot. Add structured schemas only when
repeated real consumers need them. A component can be retained independently if it proves useful;
rejecting the candidate need not discard the foundation or the broader research objective.

## 8. Immediate handoff

The next work is A-B, with no model campaign implied:

- [ ] Prepare the four worked choices using existing sources/traces, with the common procedure and
  the exact difference from old inputs. Include contrary evidence and a concern beyond generation.
- [ ] Check the chosen source/tool path locally without rebuilding shared stores or launching judges.
- [ ] Choose one test: autonomous pilot by default, fixed-evidence diagnostic only for a stated reason.
- [ ] Provide the shared Task recipe, no-spend preflight, evaluation export and costed manual commands.
- [ ] End with a go/revise/park recommendation grounded in those examples and dependencies.

The criterion for this handoff is a testable intervention at a tolerable cost, not a polished new
architecture. Another review round, a 35-case audit, a retrieval benchmark and old-fixture replays
are not automatic prerequisites. Future convention discovery and learned adaptation can be planned
separately; neither is implementation work authorized by this plan.

## 9. Reading list and review history

Paths are repository-relative. Worktree heads were verified when revising this plan; recheck them
before implementation. Worktree files are evidence locations, not dependencies to copy wholesale.

- [Questions already answered](../questions.md), [stopped designs](../dead-ends.md),
  [context needs](../todo/review-context-needs.md) and [design comparison](../todo/review-design-comparison.md).
- [July precedent design](../research/precedent-retrieval-design.md) and its Mode A stop entry.
- [Dossiers adversarial review](../research/conventions-dossiers-review-2026-10.md): oracle versus
  transfer, retrieval and supplied-applicability limits.
- [Operations foundation](2026-10-22-review-operations-foundation.md) and the
  [comparison-session handoff](../../.claude/worktrees/review-operations/docs/plans/2026-10-22-review-comparison-next-step.md)
  (`review-operations@01008813`).
- Existing owners: `src/mathlib_review/retrieval/precedents.py`, `precedent_index.py`,
  `src/mathlib_review/analysis/sessions.py` and the operations branch's shared domain functions.
- [Reconstruction results](../../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md)
  (`review-reconstruction@eecb7d18`), especially decision-context, Phase A and amendment 7.
- [Grounds reading and qualifications](../../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md)
  (`grounds-reading@b1b2d859`).
- [Additions triage and independent review](../../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md)
  (`useful-additions-triage@f2e4ba95`): pending labels and output-channel corrections.
- [GPT stage W record](../../.claude/worktrees/generation-suppression/docs/plans/2026-10-06-generation-without-suppression.md)
  (`generation-suppression@d7c65fa6`); the detector experiment is a different measurement.
- [Demonstrated-change corrections](../../.claude/worktrees/demonstrated-change/docs/plans/2026-10-18-review-as-demonstrated-change.md)
  (`demonstrated-change@e9b9b6e0`).
- [Theoretical companion](../research/review-knowledge-transfer-grounding-2026-10-23.md): feasibility,
  conditional preference and justified request are separate. It motivates no particular architecture.
- [Claude's response and disposition](../research/review-knowledge-transfer-plan-review-2026-10-23.md).
  The original draft remains in `165347f2`; its appended review in `a7138cf5`.
