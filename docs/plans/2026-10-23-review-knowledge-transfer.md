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

## 13. Theoretical grounding: companion assessment, 2026-10-23

[The grounding assessment](../research/review-knowledge-transfer-grounding-2026-10-23.md) connects
this draft to S, acceptance, comparative preference and request value. It distinguishes knowledge
size from procedural transfer and sharpens the uncertainty that A–B should resolve before a run.
It is an assessment for iteration; the connection does not establish the candidate mechanism.

---

## Response (Claude, 2026-10-23)

Read against `develop@165347f2`, the worktree heads in section 12 (all verified by `git worktree
list`), `docs/dead-ends.md`, `docs/questions.md`, `docs/todo/README.md`, the reconstruction
`RESULTS.md`, the grounds reading with its assessment, the additions triage with its review, and
the two retrieval modules. No model ran; nothing was spent.

### The verdict in four lines

1. **The goal is right and the control is right.** A fixed method that handles more situations as
   more cases are supplied is the only shape that escapes the census tail, and the paired "same
   producer, ordinary extra work" comparator is what the Phase A review found missing.
2. **The plan is a reopening, not a new direction, and should say so.** It reopens two recorded
   entries under their own conditions. It should also cite the July design it restates.
3. **The distinct input is already known from the record.** Part A does not need an inventory: five
   of the six steps in section 4 were delivered to the strongest reviewer at two decisions and it
   declined 6 of 6. What was never delivered is the maintainers' conditional ledger with the check
   each side names, and a repaired construction. Part A should state that as the premise and
   falsify it on the sessions and asks already on disk.
4. **Part C as drafted is 72 Opus sessions on the user's interactive account, with a retrieval
   step whose instrument has never been measured on the asks it must find.** Stage it behind two
   cheap readings and state the headroom and the rules now.

### 1. What the record already says about this proposal

**It was proposed in July under another name.**
[`research/precedent-retrieval-design.md`](../research/precedent-retrieval-design.md) (2026-07-02):
"maintainer judgment is case law, not statute ... the missing piece is which principle is active
here, which is exactly what a retrieved precedent supplies". Its first use, Mode A, is a dead end:
delivery worked (47% of primed findings echoed a precedent) and transfer failed (13 against 11
covered on 41 shared PRs). It **reopens only** "with a different use of the precedent (recognition
mode, ranking), not as prompt priming" (`docs/dead-ends.md`). Section 4's use, an applicability
argument plus a checked alternative, is a different use, so the reopening is legitimate. Section 3
should carry this row; it is the closest prior result and the plan does not name it.

**It is the library-knowledge entry's own reopen condition.** The 2026-10-13 premise check found
that of 41 asks no free-reviewer session reached, the library decides 7 and for **19** "the library
points to the change but a choice remains" among its options. It stopped because "what decides
these asks is maintainers' preference among the library's options, which the library does not
record", and **reopens if** "the library is paired with a record of which option maintainers prefer
... and that pairing is tested on the 19" (`docs/dead-ends.md`;
`results/pr_review_v5/probes/library-knowledge-2026-10-13/asks.jsonl`, rows with the
`library_partial` reading). That pairing is this plan. The 19 are its premise-check set and
section 7A should use them instead of "up to six saved development cases".

**Five of the six steps were delivered to Opus, and it declined.** Step 4's C and Cplus sections at
33117 held the mechanism, the dated base-commit uses, one sentence relating the attribute to the
PR's twins, and a compiled demonstration; at 33066 the constructor's elaborated signature and the
relation. Opus 5.5 related the source to the declaration in every assisted session and filed in
**1 of 6** at 33117 (C5 0 of 3, Cplus 1 of 3) and **0 of 3** at 33066; Sonnet filed 4 of 5 at
33117 and 0 of 5 at 33066 (`RESULTS.md`, step 4 and amendment 7). Two things in that reading are
the plan's real openings:
- the declines name one side only: at 33117 the mechanism's costs (a new import, the file's
  hand-written siblings, "used in only one other file") and no cost of the hand-written form; at
  33066 the wrapper's benefit asserted and nothing counted (grounds response, §"The next steps"
  item 2);
- 3 of the 5 declines at 33117 rested on an attempt that failed for a missing import line, and
  the one session that repaired it filed (amendment 7).

**Assertion carried every positive; verification carried none.** The exact brief said "these
conventions apply here" and Claude read 0.46 to 0.74 of in-census asks. The same sentence
pinpointed at the place with a check to run, stage G, read **+0.000**, and at the 10 asks only the
exact brief reached, G's reviewer filed a different change at 6; picked from the diff without the
asks, stage F, +0.03; "offered for verification rather than asserted as applying" +0.00 to +0.03
(`docs/questions.md`, conventions; `research/conventions-dossiers-review-2026-10.md` §2.4). Section
6 is right to forbid asserting the target's conclusion, but it then places the method exactly in
the regime where nothing on record has moved a reviewer. The plan has to say where its effect
comes from instead. The grounds response gives the candidate: the reviewer **performs the check
the reason names** (counts uses at 33066, tries the client call at 33117, repairs the import) and
decides on it. That is visible in a transcript without a matcher, and it is the prediction that
separates this from the ceiling test.

**The decision-context packet is step 2 and step 3 without the alternative, and it moved nothing.**
Packets of library examples, uses, mechanisms and earlier review and Zulip decisions, gathered
without the asks, left the sketches' reach at 5/4 against 5/4 of 25 and "did not add reasons"; on
the free reviewer the packet alone lost one ask (`RESULTS.md`, decision-context round and Phase A).
Of the four target decisions, the ask-blind preparer found the deciding source at one (33066's
`mk`), missed the mechanism at one (`to_fun`), and at 43167 shipped the wrong pair of conventions
(the deciding family `inf_sup_left` was absent). So step 2 fails more often than it succeeds on
the only sample we have, and section 3's row 5 understates it.

**Retrieval of the comparable case is an unmeasured instrument.** The dense precedent index's hit@5
of 0.49 was measured on the bench's own corpus, never on census hunks
(`docs/todo/parked-corpora.md`; dossiers review §8). On the 43 agreed design-comparison asks a
name-token search from the PR's declarations found the analogue in the top ten for **0 of 43**;
unification by shape found 6 of 50 sites; **18 of 99** comparison asks have a plausible wrong
analogue, each a twin along one axis (`docs/todo/review-design-comparison.md`). The dossiers
review's step 1, retrieval as the selector over the shipped index, $0 of CPU, was registered and
**never run** (`probes/conventions-ladder-2026-10-08/README.md`: "skipped for now"). It is the
check section 7B needs before any producer searches for cases.

**What there is to transfer is bounded.** About 37% of asks state any ground; of 246 with one, a
technical fact 32%, a principle 27%, preference 16%, the scope's practice 11%
(`probes/stated-grounds-2026-10-16`). In the grounds reading, 154 in-scope asks hold 43 stated
reasons, 30 phrased to carry to another PR. The one supported reason is a cost-benefit with
conditions, not a priority: every library-side statement names a cost of the duplicate, every
local-side statement a benefit it keeps, with a checkable criterion on the benefit side (used as an
object, repeatedly: v1044, v1326, v0860). Step 3's "stated reason if present" will be absent for
most cases, and section 5 should say what the method does then.

**Headroom on the sets.** For Opus on the 93 asks of P14 and D12, the redundancy and generation
families hold 8 asks, 5 already reached, **3 remaining** (d0002, d0018, p0006), 3.2 points; the
generous envelope 4 of 93
(`research/review-design-decisions-revised-2026-10-19.md`, `audit.py`). The never-reached 37 of 93
are the population the method is for, and 34 of the free reviewer's 66 missed asks "lacked
nothing" (`probes/ask-reading-2026-10-12`). A positive Part C on six PRs can add a handful of
asks at most; the additions channel will carry most of its signal, and that channel's labels are
the ones the triage left pending.

### 2. Corrections to section 3

- Row 2, "GPT's stage W": the positive examples-and-precedence result is DeepSeek's stage D,
  +0.197 / +0.179 over three reps with the exact conventions (`conventions-ds41@18f7c3c1`);
  gpt-5.5 under the disposition paragraph filed 5 of 13 stated asks and 13 of 14 unasked facts,
  a pass-through, not a positive (`docs/dead-ends.md`, detectors).
- Add rows for: Mode A; the library-knowledge reopen condition; stage G's +0.000 and the
  assertion reading; the decision-context packet's null; the retrieval measurements above;
  "a second run of the same reviewer reaches the same asks, so resampling is not a lever"
  (`docs/questions.md`), which bounds the control; the stated-grounds shares.

### 3. Part A, rewritten as the premise check CLAUDE.md asks for

No spend, about half a day. The claim to falsify: *at the places the strongest reviewer declines
with the facts in hand, a dated maintainer reason for this kind of choice exists in the record,
the reviewer's reasoning never weighs the cost or benefit it names, and there is a check that would
settle it.* Data on disk:

| Set | Where | Already read |
|---|---|---|
| The 6 Opus C and Cplus sessions at 33117 and 33066 | `review-reconstruction` `step4/place_opus*/` | yes: one side of the ledger, no check |
| Claude's 10 exact-brief misses, 6 judged "a matter of taste" | `probes/conventions-ceiling-2026-10-04` | the grounds, not against the record's reasons |
| The 19 `library_partial` asks with the free reviewer's rows that named the topic | `probes/library-knowledge-2026-10-13/asks.jsonl`; `probes/ask-reading-2026-10-12` | no |

For each place: (i) is there a reason in the record for this kind of choice (the grounds
reading's 43; the stated-grounds probe's 246), dated before the target; (ii) did the reviewer weigh
it; (iii) does the reason name a check. **Threshold, stated now:** if a dated reason exists and was
absent from the weighing at fewer than a third of the 35 places, the knowledge is not there to
transfer, the mechanism is the decision itself, and Part C does not run. Output: the mechanism
table section 7A asks for, with the input difference named as the ledger and the repaired
construction, or the stop.

### 4. Part B, two additions

- **The retrieval check first**, the dossiers review's step 1: for each of the 43 agreed
  comparison asks and the 9 supporting PRs of the grounds reading, query the shipped index with its
  dated gate (`PrecedentIndex.eligible_mask(as_of, exclude_pr)`,
  `src/mathlib_review/retrieval/precedent_index.py:406`) from the target's hunk, and ask whether the
  maintainer's case is in the top 5; beside it, the design-comparison todo's routes (siblings,
  shape, neighbourhood, role). Threshold: recall at or above 0.5 on the 43 by any single route, or
  section 7D's first row applies before Part C, not after it.
- **The mechanism reading on the fixtures, three sessions a cell, before any fresh PR.** Replay
  C at 33117 and 33066 with the ledger and its checks added, Opus on the existing route, and read
  only whether the session performs the named check and decides on it. This is development
  material and proves no benefit; it is the cheapest falsifier of the prediction in §1, about 1-2
  five-hour windows against Part C's 6-10. If no session runs the check, Part C has no mechanism.

A-B by hand is about two days, or one with subagents at about 1-2M tokens (Probe 0's eight
briefs with audits cost 2.72M).

### 5. Part C, what to fix before it is costed

- **Cost from the record.** Six Opus C sessions were about 20M processed tokens; a dev run of 12-15
  ordinary sessions is 19-24M, about one five-hour window. Thirty-six investigating producers are
  therefore 60-120M and thirty-six consumers 50-70M: **6-10 five-hour windows on the primary token**,
  which is the user's interactive account and the only one that runs. Stage it: two PRs by three
  reps (24 sessions) first, the rest only if the mechanism reading in §4 passed.
- **State the rules now, not "before the pilot".** Registered gain: an ask reached in 0 of 3
  control sessions and at least 2 of 3 treatment sessions on both matchers, on two PRs of
  different kinds (Phase A's gate). Burden: finalized findings on no-ask PRs at most the control's
  plus one a PR (the revised decisions' guard). Mechanism: the transcript-visible check. Report
  submitted, anchored and finalized counts apart; Phase A lost 33 of 255 submissions at anchoring,
  including both occurrences of its best documentation fix.
- **Say what the control will do.** Two runs of one Opus configuration reach the same asks (7
  and 7 of 23; the misses are systematic), while four passes unioned reach 12 against 7-9 at 7.0
  findings on a control PR. So the ordinary-extra-work control gains on volume and little on asks;
  the treatment is read against it on both.
- **Second model.** The user's standing rule is model-by-harness, never one model. Sonnet is not an
  instrument here: it filed on the stated relation where Opus declined, so a Sonnet gain says
  nothing about the weighing. The free reviewer is, at $0 when `first` is free, and the same
  recipe should run there as the second cell.
- **Infrastructure, named.** The producer needs base-commit search (the route's own tools, with
  amendment 7's symlink fix), dated review and Zulip sources through the index's gate, and Lean
  checks, which `review-operations@0123f43a` serves through an MCP server. That producer is
  increment 4's live consumer, which the comparison-session handoff
  (`review-operations`, `docs/plans/2026-10-22-review-comparison-next-step.md`) already selected;
  the plan should say Part C is that increment with ask-free targets, not a parallel line. The
  reconstruction probe's subagent route is the project's route and not a private runner, if
  increment 4 is not ready.
- **Output channel.** Finalized findings, as section 8 says; the producer's notes are retained and
  never scored.

### 6. Three things for the user to rule on

- **Section 10's "learned adaptation"** is training a model, which the project's framing has
  excluded (2026-09-24, leakage proportionate to not training). Keep it as a user decision, not as
  a branch of section 7D.
- **The review corpus as the reviewer's knowledge.** On 2026-09-26 the user said asks should
  "reflect a general taste or design choice the community follows, not repeat historically asked
  reviews", and that the corpus's legitimate use is "the taxonomy of what matters, not a lookup"
  (`docs/todo/review-design-comparison.md`). Sections 4 and 5 use dated prior decisions as the
  reviewer's evidence. The guards are there (sources predate the target, the target's thread is
  excluded, the finding names its case so a wrong one is refutable), and the 2026-10-13 reopen
  condition points the same way, but the ruling is the user's.
- **The five-hour windows.** Part C's full size is a week or more of the interactive account.

### 7. The order I would run

1. Part A as the premise check in §3, with its threshold. Half a day, $0.
2. The retrieval check in §4. Minutes of CPU, $0.
3. The mechanism reading on the two fixtures, Opus, three sessions a cell. 1-2 windows.
4. Part B's four worked examples and the protocol, opening with "Already answered?" and the rows
   in §2.
5. Part C on two PRs by three reps, then the rest. 6-10 windows in all, staged.
6. Parts D and E as written, with the tuning concerns (API redundancy, generation) listed before
   C so E's held-out concern is fixed in advance.
