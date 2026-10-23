# Mathlib review: research questions, evidence and current direction

*Living research overview · reviewed 23 October 2026.*

This document starts from the [October supervisor update](../supervisor_update_2026-10/slides.md),
which remains unchanged. It explains what the project is trying to contribute, how its experiments
have changed the research question, and what would make the next piece of work worth pursuing.
It is written for a supervisor or collaborator entering the project, and for us when choosing work.

**The central question:** can a reviewing agent identify consequential changes to a Mathlib PR,
investigate the relevant alternatives, and make requests worth a maintainer's attention? Our
working hypothesis is that decomposing particular reviewing operations can improve on one agent
with tools. The experiments reviewed here have not established a deployable improvement over the
strongest solo reviewer at comparable total resources.

The clearest contributions so far concern the task and its measurement: technical validity,
agreement with recorded requests, and usefulness are different outcomes; supplied convention
knowledge can change reviewing, while selecting and applying it without the answer remains hard;
and several plausible explanations of that difficulty have failed their tests. A general convention
discovery method and an effective reviewing architecture remain open contributions.

**The immediate recommendation, from the latest branch discussion, is a bounded assessment of
useful additions already present in saved final reviews.** That should decide whether a particular
reviewing operation merits another experiment. A larger comparison pipeline does not follow
automatically from the completed engineering or grounds reading.

## 1. What reviewing asks for

### The task and the theoretical model

APE-Bench asks an agent to produce a change from an instruction and a pinned library state.
Review gives the agent a proposed change as well, and asks which improvements to request.
Both involve interpreting the contribution's purpose. Review adds a judgment about how that
purpose should be realized within a particular library and community.

Retain the supervisor update's notation, with explicit limits:

```text
C                 library state available at the review episode
p                 contribution purpose, to the extent recoverable from permitted inputs
S(C, p)           changes that compile and realize that purpose
A(C, p, t, k)     changes considered acceptable at time t in review context k
≽(C, p, t, k)     a possibly incomplete preference relation among viable changes
```

Acceptability and preference are distinct: an acceptable contribution can still receive an
optional improvement request. The context includes scope, review attention and reviewer; it need
not yield a single community-wide ordering. A stable library purpose is a useful simplifying
assumption in the slides, not a measured invariant. Purpose itself can also be disputed or missing.

The motivation is **quality beyond proof validity**. Kernel checking establishes that a term has
its stated type under the environment's assumptions. It does not establish that the statement is
the intended theorem, that new axioms are acceptable, or that an API belongs in Mathlib. Even the
premise that every reviewed head compiles needs checking: some historical episodes precede the
author's build repair ([workspace account](research/reviewed-workspaces.md)).

A request can often be represented as a condition on a revision. A concrete witness demonstrates
one way to satisfy it while preserving the task; compilation checks part of that claim. Some
requests instead seek clarification, motivation or a design decision. They need an output contract
that permits those responses, rather than an invented patch.

The slides' completeness condition—one emitted test must be passed by *every* acceptable revision—
is stronger than the operational task supports. Different acceptable repairs may satisfy different
requests, and advisory requests need not be necessary for acceptance. A preference relation alone
also does not define an acceptance threshold. We therefore use the model to distinguish outcomes,
without claiming that the current benchmark measures its full soundness or completeness.

### What we observe and what we can measure

The episode is the base, the submitted head and the permitted PR context at first review. Later
comments and revisions are evaluation evidence, excluded from prospective reviewer inputs. A
recorded comment shows what one reviewer requested under those conditions. A merge or author edit
does not identify all acceptable alternatives or the community's complete preference relation.

| Outcome | Evidence that bears on it | What that evidence does not establish |
|---|---|---|
| The alternative is technically valid | A check in the right environment; interface and client tests where relevant | That requesting it is worthwhile |
| The reviewer recovered a historical ask | A matching of the final finding to the recorded concern and requested change | Completeness of the historical gold or usefulness of other findings |
| The request is useful | A reasoned assessment of the exact request, scope, benefit and burden | A universal convention or causal benefit from the harness |
| The harness improves reviewing | A controlled comparison on fresh PRs, including gains, losses, undesirable requests and total resources | Established by any intermediate artifact alone |

“Ask, identify, resolve” from [the early framing](ask-identify-resolve.md) remains a useful diagnostic,
not a claim about a fixed human cognitive sequence. For an encountered object, inspect whether the
reviewer considered the concern, found an alternative, constructed or checked it, compared its
consequences, decided to request it, and retained it in the final output. Finding the right line
alone is not issue identification. A missing final finding can arise at any of these steps.

Two instruments must stay separate: the **atomic-obligation semantic judge**, and the **raw-ask
matcher**. They use different reference units; a shared PR set does not make their scores
interchangeable. Report instrument/version, reference set and digest or seal, denominator,
replications, and output channel. Candidate, submitted, finalized and published findings are
different populations. The [measurement implementation](research/task-dataflow-refactor-implementation-2026-10-22.md)
records these identities and the route back to the underlying bytes.

Recorded asks are a lower bound. An unmatched finding is **unadjudicated**, not a demonstrated
false positive. Likewise, emission on a PR with no recorded asks measures burden, not a certified
error rate. Compilation does not supply request-level precision. These corrections supersede the
stronger precision and clean-negative interpretations in some older reports and the
[historical task specification](research/review-task-spec.md).

## 2. Where this sits in the literature

This is a positioning map based on the repository's [saved systems survey](research/code-review-systems-survey-2026-09.md)
and [open-code-review comparison](research/open-code-review-comparison-2026-09.md), including their
dated revisions. It is not a new systematic literature review; publication and product claims have
not been refreshed here. Papers, released prompts and vendor reports provide different evidence.

| Related work | Overlap with this project | Question our experiments add |
|---|---|---|
| [APE-Bench](https://arxiv.org/abs/2504.19110) | Pinned Lean environments, contribution purpose, execution and semantic assessment | Given a working proposed contribution, which further changes are worth requesting? |
| [MathlibPR](https://arxiv.org/abs/2605.07147) | Merge readiness beyond a passing build | Can the reviewer identify the particular concern and a suitable request, beyond a PR verdict? |
| [ProofJudge](https://arxiv.org/abs/2608.20432) | Library-aware judgment between mathematical implementations | Can an agent discover and construct the consequential alternative before comparing it? A supplied before/after pair leaves that work out. |
| [BitsAI-CR](https://arxiv.org/abs/2501.15134), [AutoCommenter](https://arxiv.org/abs/2405.13565), Tricorder | Rule-conditioned checking, locating departures, calibration of unwanted comments | Which parts transfer to inferred, conditional Mathlib conventions with sparse outcome supervision? A prompted census is different from a trained checker. |
| [RovoDev](https://arxiv.org/abs/2601.01129), uReview, Bugbot | Generation, grounding, actionability, aggregation and feedback | Which loss stage matters here? Does evidence change the comparison or merely increase filings? Their deployment outcomes do not settle our controlled comparisons. |
| [SWR-Bench](https://arxiv.org/abs/2509.01494), SWE-PRBench, c-CRAB, AACR-Bench | Review generation, matching, author response and assessment beyond recorded comments | How do historical-ask recovery and useful additional review differ when proof validity can be checked? How should both be evaluated without treating author edits as gold? |

Several central ideas are established: rule-conditioned reviewing, separate verification, feedback
calibration, incomplete gold, and the difference between truth and actionability. Multi-agent
reviewing or a convention catalogue is not by itself our novelty. The potential contribution is
the Mathlib-specific empirical account, the controlled separation of these capabilities, and any
operation that subsequently demonstrates a useful improvement.

The literature should constrain particular hypotheses rather than dictate a whole architecture.
RovoDev's reported distinction between factual and actionability filtering motivates assessing
whether a suggestion is wanted; it does not validate our selector. Bugbot's reported use of voting
also prevents turning our weak agreement signals into a universal “never vote” rule. The local
question is whether an aggregation policy improves useful coverage at acceptable burden and cost.
Similarly, weak prompt-side guidelines do not establish that standards cannot be communicated in
text: supervised rule systems, exact briefs and generic guidance are different interventions.

## 3. How the research question changed since late September

The table records why one question led to the next. Its evidence is local to the tested models,
sets and contracts. These sets became development evidence after inspection, even where their
historical names still say “held-out”.

| Period and question | Result that changed the view | Consequence for the next question |
|---|---|---|
| **Late September: does dividing review by concern help?** | Lead/arms and solo runs were complementary, with different stability and burden. The lead spent much more; most matches came from its generalist. Neither design established superiority. [Comparison](research/ab-heldout12-obligation-spine.md) | Diagnose what happens at encountered objects before investing in more routing or specialist roles. |
| **24–25 September: does our decomposition represent maintainer work?** | The nominal 1,000-PR validation audit realized 973 PRs and 1,833 asks; four of seven preregistered claims from the smaller audit failed. About a fifth of asks lacked an arm owner; API design and PR-level work mattered. [Replication](research/pipeline-overfit-2026-09-replication.md) | Treat small-set family proportions and routing remits as hypotheses. Preserve AI-authored PRs as a distinct slice, with more PR-level asks. |
| **29 September–early October: is the wall reasoning, harness or model?** | Correct reasoning transport improved completion and efficiency without closing the GPT gap. Model and harness both mattered. A residual reading found only four of 67 asks never attempted; other labels overlapped. [Record](questions.md#model-and-harness) | Reading the object is insufficient. Separate missing facts, untried alternatives, mistaken comparison and withholding; avoid attributing every miss to filing. |
| **Early October: is convention knowledge useful when supplied?** | Briefs selected using the target's historical asks improved several models; 39 of 46 asks on 14 ask-bearing PRs were assigned census entries. The entries were supplied without locations, but their selection conveyed target information. [Ceiling](../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md) | Knowledge supply is a diagnostic lever. Test selection and use without target asks before treating it as a deployable method. |
| **4–13 October: can we deliver that knowledge without the answer?** | Generic guides, shortlists, pinpointed checks, precedence text and detectors had different, limited results. Gains on selected PRs did not consistently transfer. A no-withholding contract increased burden and failed its registered bar. [Knowledge and filing results](questions.md#conventions-and-knowledge) | More applicable rules or more filings are insufficient. Dossiers and exams need a demonstrated information gap beyond the tested sentence interventions. |
| **16–17 October: is low enforcement evidence of unpredictable demand?** | Rechecking flagged places found construct errors, overly broad convention texts, missed asks and uneven attention. Some real departures survived, but “applicable situation”, “departure” and “noticed departure” were different denominators. [Corrections](questions.md#conventions-and-knowledge) | Do not interpret the slides' ≤5% figure as a universal enforcement probability. Validate the proposed convention and opportunity set before modeling demand. |
| **19–20 October: does independent design reconstruction expose better choices?** | Hiding the submitted design changed alternatives but did not establish better historical-ask recovery. Audits found a brief that froze attributes and a packet missing the relevant naming family. Giving DeepSeek context/sketches transferred concrete proposals into final reviews without meeting the registered ask-gain rule. [Results][reconstruction-results] | Full reconstruction has not earned scale-up. Assess whether transmitted additions were useful and identify the particular operation responsible. |
| **20–21 October: can supplied mechanism evidence settle a hard case?** | After fixing search visibility, assisted Opus sessions considered `to_fun`; filing remained sparse. A full-family check found a real client-interface cost in generated sum/prod lemmas. [Audit][search-audit] | Discovery, correct construction and requesting adoption are distinct. Compilation of an easy subset cannot settle a family-level comparison. |
| **22–23 October: are transferable project grounds available?** | A bounded reading found recurring objections to duplication, plus legitimate interface and usability exceptions. The apparent strength depended on category grain; the broad priority claim was withdrawn. [Reading and responses][grounds] | Retain a conditional comparison of costs and benefits. Close the reading; recurrence alone does not justify another grounds campaign or an automatic implementation milestone. |

The convention census also contributes a descriptive resource: codebooks with roughly 400
principles and a long tail, built with a written rubric, seeded ordering, separate readers and
saturation analysis. One [saved reader-A summary](research/conventions-dossiers-review-2026-10/factsheet.txt)
puts about 22% of assigned principled asks in the top ten entries and 55% in the top fifty.
Those are codebook-specific concentrations, not counts of universal rules. The controls make
the synthesis inspectable; stability under different discovery choices and applicability at
unrequested opportunities still need testing.

Three numerical examples help locate the limits of those conclusions:

- **Decomposition:** the historical judge-v9 comparison on 12 PRs / 23 obligations, three reps,
  reported lead issue hits of 7, 5, 6 against solo's 4, 4, 1, at $14.59 against $1.90 billed per
  run. Those are pre-publication finding results, not evidence that all those asks reached a
  maintainer. The experiment was not resource-matched; the difference did not establish a winner.
- **Knowledge:** the later record reports Claude in-census reach of roughly 0.46 → 0.74 under
  exact convention supply. This is a raw-ask matcher result on the 39 in-census asks, with two
  reviewer repetitions; it is not the all-46 score or the atomic judge's recall. The ceiling
  report contains the separate seals and matcher readings. Generalization without the target's
  asks remains the missing result.
- **Reconstruction consumer:** on eight selected PRs / 25 asks, three strategy repetitions,
  neither context nor context-plus-sketch met the registered multi-PR gain on both matchers.
  Reader-supported additions were technically supported and in scope, not adjudicated as worth
  requesting. Repeated occurrences and alternative repairs must not be counted as independent
  discoveries. The [final-output assessment][phase-a-review] checks those distinctions.

The post-fix `to_fun` diagnostic is narrower still: the two matchers agree on the target ask at
0/3 for ordinary review, 0/3 with source/correspondence evidence, and 1/3 with added adoption
evidence. The positive survives in final serialized **diagnostic** output, not published output.
These nine sessions on one inspected PR do not estimate general reviewing benefit. Earlier
Claude search traces also used a configuration that missed symlinked unchanged directories;
they remain evidence about that configuration, not clean tests of model-only knowledge.

## 4. What we can claim as contributions

These are contribution candidates with different evidence status. “Supported” means supported in
the named studies, not published novelty, population-wide validity or demonstrated user benefit.

| Contribution | Present status | Remaining obligation |
|---|---|---|
| **Task account:** distinguish technical validity, acceptable contribution, preferred implementation and worthwhile request | Useful conceptual framing, tied to recorded cases; overlaps with existing review/actionability work | Operationalize each construct without equating it to a merge, compile or match score. The formal model remains provisional. |
| **Empirical account of Mathlib review:** kinds, scope and evidence needs; convention head/tail; model failure stages | Supported descriptive results, including a larger replication and explicit retractions | Establish sensitivity to sampling, reader/model and coding grain; separate AI-authored PRs. Roughly equal codebook sizes do not establish an equivalent taxonomy. |
| **Controlled knowledge interventions:** separate supplied target knowledge from selecting, checking and filing without it | Positive ceiling results and bounded transfer failures for the tested designs | A genuinely prospective improvement on fresh PRs with usefulness and burden assessed. Do not collapse all failures into “taste”. |
| **Reconstruction and comparison:** proposals can reach a consumer's final review; technical consequences can overturn a simple reuse story | Transmission and diagnostic mechanisms observed; usefulness and architectural advantage unresolved | Assess actual additions, then test one identifiable operation against ordinary additional work with comparable resources. |
| **Reproducible experimental infrastructure:** episode provenance, dated retrieval, retained task outputs and named measurement identities | Implemented engineering, with merged and unmerged portions distinguished below | Show that actual consumers use it reliably. Reusability is an engineering contribution; superior reviewing requires its own experiment. |

The gaps are substantive: **principled convention discovery**, **autonomous discovery of relevant
alternatives**, **conditional comparison that improves requests**, and **usefulness evaluation beyond
historical gold** remain open. A running codebook is evidence for investigating these, not a stable
specification that resolves them. Review usefulness to human maintainers and saved maintainer time
have not been established by AI-consumer experiments.

## 5. Current work and investment decisions

### What exists versus what is proposed

This snapshot reads `develop@0d5a5e70`, `review-operations@01008813` and
`grounds-reading@b1b2d859`. The latter two branches contain work absent from the main checkout's
tracked history. Their links below point into current worktrees; the Git locators remain the
source identifiers if those directories move. This is a reading of saved records, not a fresh
execution or acceptance of their model runs.

| Thread | Status in this snapshot | Research purpose and boundary |
|---|---|---|
| Common sessions, matchings, handoffs and measurement reporting | First refactor accepted and merged at `a9154196`; [implementation record](research/task-dataflow-refactor-implementation-2026-10-22.md) includes saved-data reproduction and a recorded Claude-route smoke | Make comparisons inspectable and reproducible. This does not show a better reviewer. |
| Shared context/edit-verification operations and human-assessment export | Implemented and offline-verified on unmerged `review-operations`; [record][operations-record] | Remove duplicated execution paths and prepare assessments. Tool-using comparison sessions and the prospective composition checkpoint remain unbuilt. |
| Library-mechanism grounds reading | Bounded reading complete on `grounds-reading`, with qualifications accepted | Preserve stated reasons and contrary evidence. Do not expand the census just to strengthen a recurrence headline. |
| Useful-addition triage | Latest **proposal**, not a completed assessment; [handoff and responses][triage] | Read saved final additions and their controls before deciding whether reconstruction/comparison deserves more work. |
| Specialized comparison-session Task (“increment 4”) | Earlier handoff exists; latest proposal defers it | Resume only for a selected experiment or repeated consumer that actually needs tool-using sessions. A polished comparison on familiar fixtures is not sufficient. |
| Broader convention-discovery redesign and autonomous grounds acquisition | Open/deferred | Needs an observable convention object, scope/date, valid opportunity denominator and independent transfer test. It is not a prerequisite for every narrow reviewer experiment. |

### The next decision: are the saved additions worth pursuing?

The unresolved positive from Phase A is concrete transmission: an Opus-produced proposal can
change a DeepSeek consumer's final findings. Its unresolved value is whether those findings add
useful coverage or better repairs. The [latest proposal][triage] takes up that pending assessment
before further architecture work.

Use its bounded first pass: at most one focused workday, up to six promising change families and
two unfavorable ones, spanning kinds and PRs. Record selection before reassessing; inspect exact
final findings and the controls on the same PRs. Distinguish a new concern from another repair of
a concern the controls already raised. The inventory's `control_match` field does not establish
that distinction by itself.

For any human labels, reuse the existing panel helpers and rubric: `correct_ask`,
`valid_not_an_ask`, `wrong`, `unresolved`. Preserve the technical evidence needed to judge the
request while hiding originating condition and previous evaluative verdicts where practical.
An agent can prepare evidence and an attributed priority recommendation; it cannot supply a
human label. Completing the separate 50-item solo panel is not a dependency, and its selected
population cannot substitute for a matched resource comparator.

| What the bounded reading shows | Investment decision |
|---|---|
| Strongest leads are optional, unsupported, burdensome or already covered by controls | Park this line; record what new evidence would reopen it. |
| A useful behavior, a plausible intervention mechanism and a feasible comparator are identifiable | Specify one narrow experiment. Include ordinary additional work and the producer's resources. |
| Critical usefulness judgments remain unresolved | Record uncertainty and park, unless one cheap check could change the decision. |
| Useful content is demonstrably lost in transmission/finalization | Test that loss with the same information; adding stronger evidence would test something else. |

There is no automatic “two positives” gate. A small, deliberately promising sample supports a
priority decision, not a usefulness rate or superiority claim. A later experiment needs fresh PRs
outside discovery/development, all relevant gains and losses, final serialized outputs, matched
information/resources, and an assessment of undesirable requests. Three repetitions are the
repository's floor, not a guarantee of power; uncertainty must account for clustering by PR.
Model-backed generation and semantic judging remain user-run.

### What would reopen other threads?

- **Convention dossiers/exams:** a specific failure of understanding that additional content could
  resolve, followed by transfer without target-ask selection. Passing an exam that supplies the
  rule and location cannot establish autonomous review.
- **A supplied-grounds test:** a distinct conditional addition to fixed facts/alternatives,
  including relevant exceptions, from sources predating the target review. State the predicted
  change in investigation or choice. A “do not duplicate” sentence would repeat an old intervention.
- **More decomposition or aggregation:** an observed operation or loss that the proposed structure
  addresses, plus a resource comparator. More jobs, higher union recall or a filled ledger alone
  are insufficient.
- **Selection/gating:** new, independently assessed information about request value. Reweighting
  artifact-only signals already found weak, or calling unmatched comments false positives, does
  not reopen the result.

The detailed boundaries and reopening evidence remain in [dead ends](dead-ends.md) and the
[open-hypothesis register](todo/README.md). This overview explains their connection to the question;
it does not replace either register or declare every unprioritized item dead.

## 6. Keeping this document useful

Update this overview when evidence changes a contribution claim, the next decision, or a thread's
priority. Routine implementation detail belongs in the linked record. Keep the supervisor slides
and historical plans as dated artifacts; revise the synthesis here instead of appending competing
recommendations indefinitely. When branch work merges, replace its worktree links with repository
links and update the snapshot; retain the source commit for the historical reading.

Every active thread should have five things, expressed in ordinary prose:

1. The prior observation that motivated it, with a source.
2. The unresolved question and the explanation being tested.
3. The cheapest observation that would distinguish that explanation from an alternative.
4. The investment decision each outcome would change, including a stopping or parking condition.
5. Its current status and next deliverable, with branch/commit where it is not merged.

When a result arrives, edit the relevant synthesis and contribution status; put the exact result
in [questions](questions.md), and close or revise its todo. Preserve retractions and reopening
conditions in the appropriate record. Do not keep a thread open merely because its next
architectural increment is easy to name. When adding a claim of novelty, name the closest related
work and the actual distinction; a similar system architecture is overlap to explain.

Before comparing numbers, check instrument/version, reference population, seal, denominator,
output channel, repetitions, discovery overlap and total resources. Keep three statements
separate: **what happened**, **what it suggests**, and **what remains to be tested**.

### Review of the original supervisor update

The slides provide a strong organizing sequence: formulate the task, locate it among related work,
then explain the experiments as answers to successive questions. Keep that structure. For a living
account, the main corrections are:

- Treat stable purpose, a single preference relation and acceptance completeness as modeling
  assumptions; do not imply that ask matching measures the full formal object.
- Replace “the standard cannot be told as text” and “never vote” with claims about the particular
  interventions tested. Related work contains successful text-conditioned and voting systems.
- Keep exact-convention gains explicitly answer-informed. Neither knowing a convention nor acting
  on an assertion that it applies establishes a general reviewing capability.
- Retire the universal ≤5% enforcement reading. Later audits changed both the numerator and the
  meaning of the denominator; silence also mixes lack of attention with a decision to accept.
- Treat “taste is a small residual” and “evidence can reconstruct the decision” as hypotheses.
  Stated reasons in a selected sample do not identify latent decision causes or prove sufficiency.
- Date claims about cost, recall and status; name their instruments and output channels. Add the
  reconstruction, interface-audit and grounds qualifications, and distinguish branch proposals
  from completed research. The current recommendation is the bounded triage above.

*Update record: 23 October 2026 — initial synthesis of the October 14 supervisor update and later
saved results/branch discussions. No source document or experiment artifact was changed, and no
model-backed experiment was run for this review.*

[reconstruction-results]: ../.claude/worktrees/grounds-reading/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md
[phase-a-review]: ../.claude/worktrees/grounds-reading/docs/research/review-reconstruction-phase-a-review-2026-10-20.md
[search-audit]: ../.claude/worktrees/grounds-reading/results/pr_review_v5/probes/review-reconstruction-search-audit-2026-10-21/README.md
[grounds]: ../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md
[operations-record]: ../.claude/worktrees/review-operations/docs/research/review-operations-implementation-2026-10-22.md
[triage]: ../.claude/worktrees/grounds-reading/docs/plans/2026-10-23-review-useful-additions-next-step.md
