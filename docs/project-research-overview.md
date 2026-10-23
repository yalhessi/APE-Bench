---
marp: true
theme: default
paginate: true
size: "16:9"
math: katex
title: "Reviewing Mathlib: questions, evidence and opportunities"
description: "A living project map: grounding, literature, results, near-term opportunities and long-term research questions."
style: |
  section { font-size: 27px; padding: 48px 62px 82px; line-height: 1.32; color: #243047; }
  h1 { font-size: 39px; color: #1d2b53; margin-bottom: 20px; }
  h2 { font-size: 29px; color: #1d2b53; }
  a { color: #245ca6; }
  strong { color: #1d2b53; }
  section.lead h1 { font-size: 52px; }
  section.lead h2 { font-size: 29px; font-weight: normal; }
  section.lead { background: #f3f5fa; }
  section.dense { font-size: 24px; }
  section.dense h1 { font-size: 36px; }
  table { font-size: 23px; line-height: 1.28; width: 100%; }
  section.dense table { font-size: 21px; }
  th { background: #edf1f8; }
  pre { font-size: 22px; line-height: 1.38; }
  section.formulation pre { font-size: 21px; }
  blockquote { border-left: 6px solid #e0a020; background: #fff8e6; padding: 10px 18px; font-style: normal; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 26px; }
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 24px; }
  .card { border: 2px solid #d6dcea; border-radius: 10px; padding: 13px 18px; background: #f8f9fc; }
  .card h2 { font-size: 26px; margin: 0 0 6px; }
  .card p { font-size: 23px; margin: 0; }
  .take { border-left: 6px solid #1d2b53; background: #f3f5fa; padding: 11px 18px; margin-top: 18px; font-size: 25px; }
  .source { position: absolute; left: 62px; right: 62px; bottom: 48px; font-size: 15px; color: #667085; }
  .muted { color: #667085; font-size: 22px; }
  footer { font-size: 16px; color: #667085; }
  footer a { color: #245ca6; }
footer: "Mathlib review · 23 Oct 2026 · [Map](#2) · [Choices](#4) · [Long term](#25)"
---

<!-- slide: title -->
<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Reviewing Mathlib

## Questions, evidence and opportunities

A living project map · 23 October 2026

**What have we learned? What could pay off next? What needs sustained research?**

[Open the map →](#2) · [Current choices →](#4) · [Long-term questions →](#25)

<!--
This is the maintained successor to supervisor_update_2026-10/slides.md. The original is
unchanged. The previous prose overview is preserved in Git at 8ee20776. This deck is for
supervisors, collaborators and our own prioritization; it is a reference atlas, not a timed talk.

Each question has its own slide. Use the map and footer links to enter anywhere. The grounding,
literature and evidence sections support the opportunity cards, which state a motivating
observation, a bounded next check, a payoff and a stopping condition. Speaker notes hold
qualifications and source provenance. Proposed opportunities below are not authorizations to run
experiments, and no model-backed run was launched to prepare this deck.
-->

---

<!-- slide: map -->

# Choose a question

<div class="cards">
<div class="card">

## [What is the task?](#5)

Validity, acceptability, preference and requests.

</div>
<div class="card">

## [What is already established?](#9)

Related work and the contribution we could add.

</div>
<div class="card">

## [Why are we working on this?](#11)

Experiments since late September, and what each changed.

</div>
<div class="card">

## [What could pay off soon?](#19)

Release effort, fix known losses, test bounded candidates.

</div>
<div class="card">

## [What needs longer research?](#25)

Conventions, comparison, retrieval, evaluation and AI PRs.

</div>
<div class="card">

## [What is live, and how do we update?](#32)

Branch status, evidence and maintenance of this map.

</div>
</div>

<!--
The links use Marp's exported slide numbers. When inserting or moving slides, update the map,
footer and cross-links together. Each slide has a logical `slide:` key to make that check easy.
These are ordinary Marp slides and links; there is no separate navigation application.
-->

---

<!-- slide: contributions -->
<!-- _class: dense -->

# What can we claim as contributions?

| Contribution | Evidence now | What remains open |
|---|---|---|
| **An account of Mathlib review** | Larger task audit; exploratory convention census; failure-stage readings | Stable categories, valid opportunities, transfer across areas and dates |
| **Controlled knowledge interventions** | Exact conventions help; tested delivery without target asks is fragile | A prospective, useful improvement over strong solo review |
| **Reconstruction and comparison** | Concrete proposals can reach an AI consumer; technical comparisons expose real costs | Whether those proposals improve requests enough to justify the work |
| **Reproducible experiments** | Pinned episodes, dated retrieval, retained outputs, named instruments | Reliability in actual consumers; engineering success is separate from review benefit |

<div class="take">

The task characterization is substantive. A superior reviewing architecture remains a research goal.

</div>

<!--
These are contribution candidates, not a novelty certification. The conceptual distinctions
also appear in established review/actionability work. Multi-agent review, a taxonomy, retrieval,
and a verification stage are not novel by themselves. The potential research contribution is
what the controlled Mathlib evidence establishes, and any subsequent useful improvement.

Sources: docs/research/pipeline-overfit-2026-09-replication.md;
docs/research/conventions-dossiers-review-2026-10/factsheet.txt;
docs/questions.md; docs/research/task-dataflow-refactor-implementation-2026-10-22.md;
grounds-reading@b1b2d859:docs/research/review-reconstruction-phase-a-review-2026-10-20.md.
-->

---

<!-- slide: choices -->
<!-- _class: dense -->

# Where could the next effort pay off?

| Candidate | First bounded step | Potential payoff | Priority |
|---|---|---|---|
| [Close reconstruction investment](#19) | Park the pipeline; label only for a live decision | Release effort from an expensive research line | **Now: decision value** |
| [Generalization direction](#20) | Check implication on saved good/bad proposals | Prevent false claims of weaker assumptions | **Small correctness check** |
| [Submission → final output](#21) | Reconcile lost findings with the scope policy | Reliable measurement; perhaps retained useful review | **Small audit** |
| [Inventory lifecycle](#22) | Confirm and version the known defect | Restore visibility of edits and retirement pairs | **Conditional engineering** |
| [Persistent Lean checking](#23) | Recheck parity through the current verifier | Faster investigation and experiments | **Strong throughput candidate** |
| [One mechanical sweep](#24) | Measure blind yield before integrating | Recover missed opportunities to test an edit | **Signal first** |

**A priority judgment, not a forecast of recall gain.** Research questions are on the [long-term map](#25).

<!--
“High yield” needs an outcome: a decision that saves effort, fewer wrong demands, recovered useful
review, or faster experiments. None of these candidates has an established prospective recall
benefit. Do not add their historical counts: they concern different populations and loss stages.

This ranking extends the earlier overview's focus on triage. Its independent review now supports
parking the pipeline without making all human labels a prerequisite. It makes other independently
motivated opportunities visible without scheduling all of them. The current record does not
justify a numerical ROI score. Engineering candidates must have a live consumer and a bounded
acceptance check; the presence of an old todo alone does not establish priority.
-->

---

<!-- slide: grounding -->
<!-- _class: formulation -->

# Grounding · what does review add?

```text
C                 library state at the review episode
p                 contribution purpose, where recoverable
S(C, p)           changes that compile and realize p
A(C, p, t, k)     changes acceptable at time t in context k
≽(C, p, t, k)     preference among viable changes
```

**APE-Bench:** produce a change for a stated task.
**Review:** given a proposed change, decide which further changes to request.

<div class="take">

A valid contribution can be acceptable and still admit worthwhile improvements.

</div>

<!--
This retains the original supervisor update's useful separation of task solutions and community
judgment, with limits explicit. Acceptance is not defined by a preference relation without an
acceptance threshold. A stable library purpose P is a simplifying assumption, not a measured
invariant. Preferences can be incomplete and reviewer-, scope- and time-dependent. Context k
includes the review situation. Purpose may be missing or disputed.

Kernel checking establishes a term's stated type under the environment's assumptions. It does
not establish intended semantics, acceptable axioms or API value. Nor does every historical
reviewed head compile: some episodes precede build repair. See
docs/research/reviewed-workspaces.md and docs/research/review-task-spec.md.
-->

---

<!-- slide: requests -->

# What makes a request worthwhile?

<div class="cols">
<div>

## What it asks for

A revision condition: rename, generalize, reuse, relocate, document—or clarify a choice.

A concrete alternative can witness feasibility. A compile checks part of that witness.

</div>
<div>

## Why to ask for it

The benefit to this contribution and library, weighed against interface costs, maintenance, scope and author burden.

This judgment remains after technical checking.

</div>
</div>

<div class="take">

Valid alternative → comparative benefit → worthwhile request: each needs evidence.

</div>

<!--
The sequence is a diagnostic, not a cognitive theory of maintainers. Some requests seek a
question or rationale rather than a patch; the output contract must permit that response.

The original formal completeness condition required one emitted test passed by every acceptable
revision. Different acceptable repair routes and advisory requests make that too strong for the
operational task. Historical matching measures recovery of recorded requests, not full
soundness/completeness of an inferred acceptance region. An author edit or merge is not the
complete community preference relation. Stable purpose, universal ordering, and the claim
“taste is a small residual” remain hypotheses or modeling assumptions.
-->

---

<!-- slide: measurement -->
<!-- _class: dense -->

# What do our measurements establish?

| We observe | We can assess | Still separate |
|---|---|---|
| A checked edit | Technical support in that environment | Whether it is worth requesting |
| A final finding and a recorded ask | Agreement about the concern and requested change | Useful suggestions absent from the record |
| A reasoned human assessment | Request-worthiness of that exact finding | A universal rule or a measured harness advantage |
| A controlled fresh comparison | Gains, losses, burden and total resources | Intermediate artifacts alone cannot establish this |

**Two instruments:** atomic-obligation semantic judge; raw-ask matcher.
**Four channels:** candidate, submitted, finalized, published.

<div class="take">

Unmatched means unadjudicated. Emission on a PR with no recorded asks measures burden, not a certified error rate.

</div>

<!--
Every reported number names instrument/version, reference population and seal/digest,
denominator, replications, aggregation and output channel. Never subtract across seals or
instruments. Gold is a lower bound. Compilation does not establish request-level precision;
older task-specification and clean-negative claims are superseded on this point.

Sources: CLAUDE.md, reporting results;
docs/research/task-dataflow-refactor-implementation-2026-10-22.md;
docs/research/one-reviewer-table-review-2026-10.md.
-->

---

<!-- slide: loss-stages -->

# Diagnose the loss before changing the harness

| At an encountered object | Ask of the saved record |
|---|---|
| **Discovery** | Was the relevant mechanism or analogue considered? |
| **Construction and checking** | Was the intended alternative actually tested? |
| **Comparison** | Were benefits, interfaces and costs understood? |
| **Request and delivery** | Was the useful concern expressed and retained? |

**Same visible miss, different interventions.** Finding the right line is insufficient.

<div class="take">

Before a new run: show the loss in existing bytes, then name the smallest intervention that could change it.

</div>

<!--
“Ask, identify, resolve” in docs/ask-identify-resolve.md remains a useful early diagnostic.
The finer distinctions here prevent filing, tooling and knowledge explanations from replacing
one another without evidence. In the 67-ask residual study, only four asks were never attempted;
other labels overlap. This is not a statement that all missing comparison evidence was in
context, or that attention is solved for arbitrary PRs and workloads.
-->

---

<!-- slide: literature -->
<!-- _class: dense -->

# Literature · which question is already answered?

| Work | Task or mechanism | What remains for this project |
|---|---|---|
| **APE-Bench** | Generate a purpose-realizing change | Critique a submitted contribution |
| **MathlibPR** | PR-level merge readiness | Identify a particular concern and suitable request |
| **ProofJudge** | Compare supplied before/after implementations | Discover and construct the consequential alternative |
| **BitsAI-CR, AutoCommenter, Tricorder** | Rule-conditioned checking and calibration | Learn conditional Mathlib conventions with sparse supervision |
| **SWR-Bench, SWE-PRBench, c-CRAB, AACR-Bench** | Review generation, matching, response, broader assessment | Separate historical recovery from useful additional review |

<div class="take">

Our distinction must be an empirical result or demonstrated capability, beyond the presence of agents, rules or tools.

</div>

<div class="source">Sources: <a href="research/code-review-systems-survey-2026-09.md">saved survey</a> · <a href="research/open-code-review-comparison-2026-09.md">OCR / AACR-Bench comparison</a></div>

<!--
Positioning uses the repository's saved primary-source reading, not a new systematic search.
Publication/product claims have not been refreshed. References: APE-Bench arXiv:2504.19110;
MathlibPR 2605.07147; ProofJudge 2608.20432; BitsAI-CR 2501.15134;
AutoCommenter 2405.13565; SWR-Bench 2509.01494. Papers, open prompts and vendor reports
supply different strengths of evidence. Pair preference does not by itself solve discovery,
and Mathlib review is not wholly outside established review formulations.
-->

---

<!-- slide: literature-mechanisms -->

# What to borrow—and what must transfer

| Related evidence | Motivated question here |
|---|---|
| **RovoDev:** factual filtering and actionability filtering differ | Does the evidence make the request worthwhile? |
| **Bugbot / ensembles:** repeated passes and aggregation | What useful coverage survives at comparable cost and burden? |
| **Rule systems:** category-specific feedback and suppression | Is a candidate convention valid at independent opportunities? |
| **ProofJudge / library-aware assessment** | Can the same alternatives be weighed conditionally? |

**Overlap is useful. It does not establish that the mechanism will work here.**

<div class="source">Source: <a href="research/code-review-systems-survey-2026-09.md">systems, primary links and dated reassessments</a></div>

<!--
The earlier slides' “the standard cannot be told as text” and “never vote” were too general.
Guideline injection, an exact answer-informed brief and a supervised rule checker are different
interventions. Bugbot's vendor report includes voting; our weak agreement signals do not refute
voting universally. RovoDev's reported actionability gains motivate a distinction; they do not
validate our selector. Outcome feedback, acted-on signals and author revisions also have
confounds and cannot automatically become Mathlib gold.
-->

---

<!-- slide: evidence-map -->
<!-- _class: dense -->

# Evidence · why did the question change?

| Question | Observation that moved us | Follow-up |
|---|---|---|
| Does decomposition help? | Complementarity, extra cost, few specialist matches | [Locate the loss](#12) |
| Is it reasoning or model? | Transport fixes did not close the gap | [Inspect comparisons](#13) |
| Is it convention knowledge? | Exact supply helps; transfer is fragile | [Separate selection and use](#14) |
| Is enforcement unpredictable? | Flagged situations were not all departures | [Repair the denominator](#15) |
| Does reconstruction help? | Proposal transmission; no registered ask gain | [Assess useful additions](#16) |
| Do sources or grounds decide it? | Mechanisms have costs; reasons have exceptions | [Compare conditionally](#17) |

**Historical “held-out” sets became development evidence after inspection.**

<!--
This is an index of the evidence cards, not a pooled result or causal chain established by a
single experiment. Dates, populations and instruments differ. The late-September to
October sequence is used to explain motivation rather than to imply that every earlier thread
has been completed. See docs/questions.md, docs/dead-ends.md and docs/todo/README.md for
the detailed result, reopening and open-hypothesis registers.
-->

---

<!-- slide: decomposition -->
<!-- _class: dense -->

# Decomposition: stability, coverage and cost

| Historical dev comparison | Lead + arms | Solo |
|---|---|---|
| Issue hits, three reps, of 23 | 7, 5, 6 | 4, 4, 1 |
| Billed per rep | $14.59 | $1.90 |
| Interpretation | More stable; mostly generalist matches | Less costly; complementary hits |

**Neither established superiority.** These are pre-publication results, without equal resources.

The larger task audit realized **973 PRs / 1,833 asks**. Four of seven claims from the smaller audit failed; API design and PR-level review were substantial gaps.

<div class="source">Sources: <a href="research/ab-heldout12-obligation-spine.md">A/B comparison</a> · <a href="research/pipeline-overfit-2026-09-replication.md">24 September replication</a></div>

<!--
A/B: same model GPT-5.2 with reasoning off, semantic judge v4-semantic-v3-v9-rubric,
12 PRs / 23 obligations, three repetitions. Lead/arm issue hits are not all published requests,
and the experiment is not resource-matched. Do not call the solo condition more precise solely
because it has fewer no-ask-PR findings.

Replication: val1000-2025-06-2026-03-v1, seal c311568d; 973 realized PRs,
759 with round-1 feedback. Two model readers with rubric v2; same-model agreement is not
human validation. About 21% of asks lacked an arm owner. This is a concrete contribution:
a larger study changed the proposed decomposition rather than just adding examples.
-->

---

<!-- slide: model -->

# Reasoning transport improved process, not the frontier

**Late September → early October**

- Keeping reasoning between turns improved completion and efficiency.
- The GPT gap persisted; both the model and its harness mattered.
- In the residual reading, **4 of 67 asks** were never attempted.
- Other failures included missing mechanisms, untried edits, wrong comparisons and requests withheld.

<div class="take">

More coverage, compiles or ledger cells do not by themselves repair what the reviewer concludes.

</div>

<div class="source">Source: <a href="questions.md#model-and-harness">model/harness results</a> and <a href="questions.md#the-reviewers-output-and-what-it-reaches">residual readings</a></div>

<!--
The residual labels overlap; 63 of 67 encountered does not mean that the reviewer had the
needed evidence. GPT-5.2 carried reasoning filed 55/56 compiled edits, so a general
withholding diagnosis is particularly weak there. Newer GPT models withheld more.
Prompt/contract swaps and model/harness comparisons are only interpretable with their source
views, tool configuration and reasoning transport stated. Historical symlink-search defects
remain part of the configurations the old runs measured.
-->

---

<!-- slide: conventions -->
<!-- _class: dense -->

# Convention knowledge helps when selected with the answer

**Descriptive resource:** roughly 400 principles at the chosen codebook grain, with a long tail.
One saved summary puts 22% of assigned principled asks in the top ten, 55% in the top fifty.

**Ceiling:** 39 of 46 asks on 14 ask-bearing PRs were assigned entries. Claude's in-census reach was roughly **0.46 → 0.74** with exact supply.

**Missing capability:** selecting and using the right knowledge without target asks. Shortlists, pinpointed checks and precedence text did not consistently transfer.

<div class="take">

The ceiling supplies target information even without locations. It is not a deployable reviewer result.

</div>

<div class="source">Sources: <a href="../results/pr_review_v5/probes/conventions-ceiling-2026-10-04/README.md">ceiling and delivery</a> · <a href="research/conventions-dossiers-review-2026-10/factsheet.txt">census summary</a></div>

<!--
The roughly 0.46/0.74 figure is the later raw-ask in-census summary over 39 asks, two Claude
reviewer repetitions, not all-46 reach or atomic judge recall. Seals and matcher readings are
separate. Codebook totals differ by version and by counting used versus all entries. The
census used a rubric, seeded ordering, separate readers and saturation analysis; those controls
make it inspectable, but do not prove stable taxonomy or valid applicability at new opportunities.

Dossiers/exams have not earned a new campaign. A rule/location supplied in an exam removes
precisely the selection problem review still faces. Any new content needs to address a specific
remaining information gap rather than repeat exact convention-sentence injection.
-->

---

<!-- slide: departures -->

# Applicability is not an enforcement denominator

**The earlier “≤5% of places” reading changed after reinspection.**

```text
A situation occurs
    → the proposed rule actually applies
        → the code departs from it
            → the maintainer notices it
                → a request is worth making
```

Later audits found overly broad texts, wrong namespace precedence, missed asks and uneven attention. Some real departures also survived.

<div class="take">

A low ask rate can mix construct error, lack of attention and tolerated variation. Test which one.

</div>

<div class="source">Source: <a href="questions.md#conventions-and-knowledge">16–17 October denominator, practice and attention corrections</a></div>

<!--
Do not retain the universal ≤5% enforcement claim from the supervisor slides. Namespace flags
were largely not departures under the correct convention; primed-name texts failed their own
checks; counting actual asks changed the numerator. Rules of form also sometimes described
something broader than maintainers' own practice. “Unchanged by merge” and “changed near a
comment” confound rewriting and rule-specific action. This motivates long-term convention
validation, not an immediate general demand predictor.
-->

---

<!-- slide: reconstruction -->

# Reconstruction transfers proposals; value remains unsettled

**19–20 October:** eight selected development PRs, 25 asks; three strategy repetitions.

- Neither context nor context + sketch met the registered multi-PR ask-gain rule on both matchers.
- Concrete proposals did enter the consumer's review.
- “Supported” meant technically supported and in scope, not worth requesting.
- A new repair can concern an issue controls already found.

<div class="take">

The prepared triage and independent review support parking this pipeline. Pending human labels need not delay that decision.

</div>

<div class="source">Sources: <a href="../.claude/worktrees/grounds-reading/docs/research/review-reconstruction-phase-a-review-2026-10-20.md">Phase A assessment</a> · <a href="../.claude/worktrees/useful-additions-triage/results/pr_review_v5/adjudications/phase-a-additions-2026-10-23/README.md">prepared panel</a></div>

<!--
Consumer: DeepSeek-V4.1-Flash high; producer: Opus 5.5. Existing and fresh controls, context,
and context+sketch were matched within the study's seals, with substantial disagreement on a
proof family. This does not prove exactly zero benefit or compare equal total resources.

The latest triage is useful-additions-triage@f2e4ba95, building on grounds-reading@b1b2d859.
Its frozen panel has 14 items: eight family exemplars and six controls on the same six PRs.
Human judgments remain pending. Do not reveal neutral-id mappings or provisional usefulness
verdicts in this deck. The preparer's recommendation is not a completed human assessment.

The later channel audit also found submitted/finalized differences; the earlier “final output”
interpretation requires the qualification on slide 21. A future comparison must bind its actual
consumer-facing channel explicitly. Two dropped findings received partial ask credit on both
saved matchers; none received full reached credit. The independent review also qualifies textual
proposal tracing: context can influence investigation without supplying the final proposal.
-->

---

<!-- slide: mechanism -->
<!-- _class: dense -->

# One mechanism: `to_fun` has benefits and costs

**PR 33117, after search was fixed**

| Supplied evidence | Target ask, three sessions |
|---|---|
| Ordinary review | 0/3 |
| Sources and correspondence | 0/3 |
| Plus adoption evidence | 1/3 |

Assisted sessions considered the generator. The full-family replacement compiles, but generated sum/prod forms change client arguments.

<div class="take">

Discovery, construction and requesting adoption are separate. Neg/add-only checking misses a family-level API cost.

</div>

<div class="source">Source: <a href="../.claude/worktrees/grounds-reading/results/pr_review_v5/probes/review-reconstruction-search-audit-2026-10-21/README.md">search-fix and interface audit</a></div>

<!--
Two matchers agree on the nine target-ask labels. The positive survives final serialized output
with diagnostic admission, not published admission. This is one heavily inspected PR; 1/3
against 0/3 is unresolved. All six assisted sessions related the generator to the handwritten
twins; unassisted sessions did not encounter it. The old configuration missed symlinked
unchanged directories, so earlier searches are not model-only knowledge tests.

The technical check used the actual predicate and correct import. Handwritten
Meromorphic.fun_sum h works; the generated analogue exposes anonymous explicit type,
instance, family and finset parameters. Supplying them works. This does not refute the
maintainer recommendation. Mixed generation is an alternative to investigate, not a tested
review policy. Compilation is evidence for a comparison, not an automatic filing rule.
-->

---

<!-- slide: grounds -->

# Grounds supply considerations, not a priority rule

**22–23 October:** a bounded reading of 258 selected asks, 154 in scope.

Maintainers repeatedly object to duplication that adds insufficient value. They also explain benefits that can justify local or apparently redundant forms:

**Usable statements · discoverability · interface freedom · automation · maintenance**

<div class="take">

Preserve the conditional costs and benefits. Close the bounded reading; a larger census or “prefer the library mechanism” rule does not follow.

</div>

<div class="source">Source: <a href="../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md">grounds reading, independent assessment and response</a></div>

<!--
One pooled reason met the preregistered recurrence threshold at the margin: 9 PRs, 8 maintainers,
6 before December 2025. The grouping grain matters; splitting duplicate shapes removes the
headline support, pooling local benefits makes them close to the same bar. Most supporting
rows concern redundant public API; handwritten versus generated implementation is a different
consideration. The claim that this settles both 33066 and 33117 was withdrawn.

A single well-explained exception can constrain a general recommendation. Lack of explicit
file-precedent reasoning in a selected sample does not make file precedent illegitimate.
Usage counts inform expected value, but cannot alone decide a newly introduced interface.
Stated reasons are not established causes of the decision, and recurrence does not show
that supplying them improves a reviewer. A later grounds test needs fixed alternatives/facts,
conditional additional content and exceptions, sources before the target, and fresh cases.
-->

---

<!-- slide: triage-opportunity -->

# A1 · Release effort from whole-PR reconstruction

**Evidence now:** the 14-item packet and independent review support parking the expensive pipeline. Human request-worthiness labels remain uncollected.

**Next action:** keep whole-PR reconstruction and the comparison Task deferred. Seek an exact-finding label only if it could change a separate, focused investment.

**Potential payoff:** release effort while retaining concrete generalization, automation and verification cases for future questions.

<div class="take">

Stop at the investment decision. Do not enlarge the panel or make all labels a condition for parking the pipeline.

</div>

<div class="source">Sources: <a href="../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md#independent-review-codex-2026-10-23">independent investment review</a> · <a href="../.claude/worktrees/useful-additions-triage/results/pr_review_v5/adjudications/phase-a-additions-2026-10-23/README.md">packet and rubric</a></div>

<!--
This is a decision-value opportunity, not a promise of recall gain. The independent review at
useful-additions-triage@f2e4ba95 supports shelving mandatory whole-PR reconstruction and leaving
increment 4 deferred, even without all labels. It does not close comparison or convention research
as general questions. Trace copying is evidence of one transmission path, not a complete causal
account; context can cue an operation without spelling out the eventual proposal.

Keep the preparer's technical facts and trace attribution separate from human labels. If a live
choice needs a label, reuse correct_ask, valid_not_an_ask, wrong, unresolved; an agent cannot invent
a human label. Completing the separate 50-item solo panel is not a prerequisite or a substitute
resource comparator. The small, purposeful selection means no frequency estimate follows.
The recorded rule is qualitative: useful behavior, a plausible intervention mechanism, and a
feasible contrast. There is no automatic two-positive gate.
-->

---

<!-- slide: direction-opportunity -->
<!-- _class: formulation -->

# A2 · Check the direction of a generalization

**Observed failure:** a proposal compiled under `OrderTopology` and was called a weakening of `OrderClosedTopology`. It strengthens the assumptions.

```text
Old assumption H          Proposed assumption H′
For weakening, check:     H ⇒ H′
Then check:               proposed theorem under H′
```

**Cheap next test:** replay the mistaken proposal and valid generalizations with this obligation. Include equivalent assumptions and unsupported implications.

<div class="take">

Compilation under H′ alone cannot establish weakening. First target fewer wrong demands; broader yield is unmeasured.

</div>

<div class="source">Source: <a href="../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md#independent-review-codex-2026-10-23">technical counterexample and corrected implication</a></div>

<!--
Motivating evidence: useful-additions-triage@f2e4ba95:
docs/research/phase-a-additions-triage-2026-10-23.md, technical-support reading.
This card avoids neutral panel item ids and usefulness judgments.

The direction is essential. OrderTopology implies OrderClosedTopology, so showing only
H′ ⇒ H can validate the stronger proposed context while failing to preserve old clients.
A weakening needs old assumptions to imply proposed assumptions, together with the new theorem
checking there. If both directions hold, call it an equivalent reformulation rather than a
strict weakening. A failed implication search is unresolved, not proof of non-implication.
Dependent binders and alternative instances may need more than a one-line class witness.

This is a candidate technical validation step for any reviewer, not evidence for whole-PR
reconstruction. Use the current shared verifier and retained check records. Do not build a
new subsystem until a few saved positive/negative cases show that the obligation discriminates.
-->

---

<!-- slide: finalization-opportunity -->

# A3 · Audit what survives to the delivered review

**New saved-data observation:** 33 of 255 Phase A submissions lost their anchor as `unresolved_line`. Two occurrences of a stale-reference proposal did not finalize.

**Next check:** reproduce the channel join and classify each loss against the intended scope policy. Keep inputs and finding text fixed.

**Potential payoff:** correct evaluation and reporting; retain useful findings if the policy is unnecessarily restrictive.

<div class="take">

Two losses received partial ask credit; none had full reach. Useful unasked findings may also be lost. Decide the scope policy explicitly.

</div>

<div class="source">Source: <a href="../.claude/worktrees/useful-additions-triage/docs/research/phase-a-additions-triage-2026-10-23.md#independent-review-codex-2026-10-23">reproduced channel counts and qualifications</a></div>

<!--
Source: useful-additions-triage@f2e4ba95:
docs/research/phase-a-additions-triage-2026-10-23.md, “Lost at finalization”. Counts are
12/77 historical controls, 2/25 fresh control, 7/72 context, 12/81 context+sketch.
Do not add published/diagnostic admission as though it were the same boundary.
The independent review reproduces the counts and finds two partial matches on both saved
Phase A matchers, with no full reached matches. Zero full reach is not zero matcher credit
or zero usefulness loss. Do not disclose the blind packet's neutral-id mappings here.

This qualifies the earlier interpretation of Phase A findings as uniformly final serialized
output. The current task/dataflow measurement identity can represent submitted and finalized
channels; adopting that identity does not retroactively make historical inputs finalized.

The example concerns an unchanged line in a touched file. This could be intentional scope
policy rather than a bug. Audit first; do not broaden anchors automatically, change the
wording/evidence and attribute improvement to finalization, or claim historical recall gains.
A finding's usefulness still needs assessment. Nothing here edits frozen runs or gold.
-->

---

<!-- slide: inventory-opportunity -->
<!-- _class: dense -->

# B1 · Correct inventory lifecycle before retirement checks

**Known defect:** 344 of 912 “removed” declarations survived in the same file. For 135, that was the only target, hiding the edit from arm scheduling.

**Still present:** current `modification-inventory/1` infers removal from base-only target text.

**Bounded build:** distinguish a deletion inside a surviving declaration; pair moves/renames with their prior form. Then assess mechanical retirement checks.

**Acceptance:** the existing classifier's hidden-survivor count **135 → 0**, without increasing unexplained retirements; preserve frozen versions.

<div class="take">

A concrete coverage repair. It benefits inventory-driven consumers; it does not establish better whole-PR judgment.

</div>

<div class="source">Sources: <a href="todo/inventory-lifecycle.md">lifecycle defect</a> · <a href="todo/removed-declarations.md">completed study and build conditions</a></div>

<!--
Confirmed in this turn: src/mathlib_review/release/modification_inventory.py::_lifecycle and
INVENTORY_VERSION remain the simple base/reviewed-presence classifier and version 1.
The counts are the September saved-data study, not a freshly recomputed corpus estimate.
Lifecycle enters identities, so use a new inventory version and keep frozen releases intact.
Do not regenerate shared data stores from a topic branch before integration.

The completed retirement study identified 29 mechanical asks among 65 retirement asks. Its
build criterion is at least 20/29 at the right declaration and reading would-fire/no-ask PRs.
That is a ceiling/technical target, not expected general recall. The inventory correction is a
prerequisite; it does not justify a new “removed” specialist. Choose this engineering work only
if an active inventory-driven consumer needs it. Pairing by name and conclusion has ambiguity.
-->

---

<!-- slide: checker-opportunity -->
<!-- _class: dense -->

# B2 · Persistent Lean checking has measured leverage

**Observed cost:** Lean was 20–51% of wall time in sampled sessions.

| Strict saved-edit replay | Cold median | Persistent median |
|---|---|---|
| 56 edits | 9.6 s | 1.23 s |
| 54 edits | 10.3 s | 0.70 s |

A mixed-call, whole-session replay reduced **Lean time 2.1×**. This is not a measured end-to-end reviewer speedup.

**Next gate:** parity through today's shared verifier, preserving versioned diagnostics, paths, imports, axioms and fallback; then measure a real consumer.

<div class="take">

Strong throughput potential; integration is substantial enough to need a live workload.

</div>

<div class="source">Sources: <a href="../results/pr_review_v5/probes/lean-build-2026-10-03/README.md">corrected replay</a> · <a href="todo/lean-persistent-checker.md">integration acceptance</a></div>

<!--
The same-day correction is part of the result: leanclient's default completion could return
stale diagnostics. Strict results wait for the exact document version. One remaining replay
disagreement was the engine's axiom post-check, which must be preserved. Keep full-file
checks where later declarations can be affected; import changes can restart the environment.
Reviewed workspace paths must not resolve to the wrong base through symlinks.

The 2.1x mixed replay covers 146 calls in 12 recorded sessions: 2071s to 994s of Lean time.
Whole-file edit totals were 3.8x and 4.8x, not the speedup of the whole reviewer. Memory and
startup costs matter. Current main verification still uses the cold path; review-operations
extracts the common verifier but does not establish a persistent backend. New models may
spend a different share on Lean, so profile a current consumer before committing integration.
-->

---

<!-- slide: sweeps-opportunity -->

# B3 · Measure one mechanical sweep without target asks

**Signal:** ask-targeted edit procedures reproduced eight of fifteen selected missed asks. Many residual cases involved a check never tried.

**Smallest useful test:** choose one procedure—such as old-proof replay—and run it at every eligible object on a bounded, previously uninspected PR set.

**Read:** eligible objects, valid alternatives, relevant requests, unwanted changes, runtime and existing-review overlap.

<div class="take">

Stop if the valid output is mainly optional noise or duplicates existing review. The targeted 8/15 is not a yield estimate.

</div>

<div class="source">Sources: <a href="../results/pr_review_v5/probes/closer-battery-2026-09-26/README.md">targeted battery</a> · <a href="todo/review-mechanical-sweeps.md">bounded sweep</a></div>

<!--
This narrows an existing open hypothesis rather than reviving a generic detector campaign.
The battery's statement that a compiling transformation has “no false-positive mode” only
addresses technical validity; a technically valid edit may still be an unwanted request.
Three maintainer questions were answered “no”, showing another limit of literal ask recall.

The standard linter pass alone reached one exact ask of 23 on 15 PRs. The four convention
detector families held only 2.9% of census asks and were closed as a broad recall lever.
This card does not reverse that result. It asks for the blind yield of one eligible transform
before integration, with no automatic filing policy. Reuse existing operations. If the cheap
technical screen is promising, usefulness and a consumer comparison are still required.
-->

---

<!-- slide: longterm-map -->
<!-- _class: dense -->

# Long-term research: five unresolved capabilities

| Question | Missing object or capability | First independent evidence |
|---|---|---|
| [L1 · Discover conventions](#26) | Scoped, dated expectations with exceptions | Predict at unrequested opportunities |
| [L2 · Compare valid designs](#27) | Conditional benefits and costs that support a request | Fixed alternatives and facts; independent grounds improve choices |
| [L3 · Retrieve by role](#28) | Find a relevant mechanism without its name | Ask-blind sources that lead to useful final findings |
| [L4 · Measure useful review](#29) | Net useful coverage and burden beyond incomplete gold | Exact-finding assessment plus a resource-matched comparison |
| [L5 · Review AI contributions](#30) | Purpose, necessity and coherence at PR scale | Transfer to realistic AI-authored PRs |

**These are research problems. None requires building all five systems first.**

<!--
Long-term means the central question is unsettled, not that the next test must be large.
The near-term cards can expose a tractable part of these problems. Each contribution needs a
falsifiable object, source evidence and independent evaluation, rather than proxy success such
as a longer codebook, more searches, more compiles or a more detailed comparison document.
-->

---

<!-- slide: convention-research -->

# L1 · What is a convention, and where does it hold?

**Problem:** an ask-derived sentence can describe too much, too little, or the wrong precedence. Similar-sized codebooks need not encode the same conventions.

**Research object:** a candidate expectation with scope, date, rationale, trigger, alternative forms, defeaters and counterexamples.

**Discriminating test:** fix one candidate and its prediction, then inspect independent opportunities—including conforming code and unasked departures—before observing the target requests.

<div class="take">

Success is calibrated transfer. Codebook size, recurrence and a rule-following exam are insufficient alone.

</div>

<div class="source">Sources: <a href="todo/conventions-nature.md">open question</a> · <a href="questions.md#conventions-and-knowledge">practice and denominator results</a></div>

<!--
Separate explicitly stated reasons, inferred principles, measured practice and historical asks.
Sensitivity to ordering, batching, model and revisions matters. Preserve dates and area scope;
legacy code is not automatically subject to a new convention. Typeclass versus ordinary
hypothesis, naming priorities and emerging automation practices are examples, not a prevalidated
ontology. Do not expand the whole census just to fill a taxonomy. A bounded independent test
can decide whether one candidate is usable.

Related work to investigate, not newly reviewed here: NATURALIZE-style statistical convention
learning, learned rule checkers, rules/standards and explicit exception handling. Frequency is
evidence of practice, not a universal normative priority.
-->

---

<!-- slide: comparison-research -->

# L2 · Which valid alternative is worth requesting?

**Problem:** removing duplicated source, removing redundant API and preserving a useful interface are different decisions.

**Candidate comparison:** client calls, automation, imports, scope, expected use, implementation commitment and maintenance.

**Discriminating test:** fixed checked alternatives and facts, with or without independently recovered conditional grounds. Include cases where keeping the local form is justified.

<div class="take">

A justified “keep it” or mixed solution is a valid outcome. Prefer-library directives would decide the experiment in advance.

</div>

<div class="source">Source: <a href="../.claude/worktrees/grounds-reading/docs/research/library-mechanism-grounds-2026-10-22.md">grounds and interface qualifications</a></div>

<!--
ProofJudge supplies pairwise judgment as related work; our open task also includes finding
and constructing alternatives. A later controlled grounds test must keep factual evidence and
alternatives fixed, use sources predating the target, hide the target conclusion, include
exceptions, account for overlap with parent census/codebooks and assess final useful/undesirable
requests. Repeating a “do not duplicate” sentence is the old convention-supply test.

33066 and 33117 are development fixtures, not fresh tests. More detailed explanations there
can debug an operation but cannot establish general improvement. Building the specialized
comparison Task is deferred until a consumer experiment actually needs it.
-->

---

<!-- slide: retrieval-research -->

# L3 · Find the mechanism without knowing its name

**Problem:** identifier search finds what the PR calls an object. It may miss what should generate it, what concept it implements, or the analogous API it should resemble.

**Candidate operation:** retrieve by mathematical role, statement/hypothesis shape, generator capability or actual use; expose contrary analogues too.

**First test:** ask-blind source selection on contrasted cases, checked at the base and cutoff. Measure useful alternatives considered, tested and retained in final review.

<div class="take">

More searches or a relevant file in the packet are intermediate outcomes. They must change a consequential comparison.

</div>

<div class="source">Sources: <a href="todo/review-context-needs.md">information gaps</a> · <a href="../results/pr_review_v5/probes/closer-battery-2026-09-26/README.md">shape/name versus unification examples</a></div>

<!--
Examples include generated twins, Parseval behind custom definitions, a pigeonhole lemma
with matching hypotheses, and design analogues such as PMF/convex-space APIs. These motivate
role/shape retrieval; they do not establish a generic retrieval architecture. Existing fold
search covers a narrow class and returns many synonyms. Test its useful yield before extending it.
Use existing dated retrieval operations and source visibility restrictions. A source selected
after reading the target ask is an oracle diagnostic and must remain labeled as such.
-->

---

<!-- slide: usefulness-research -->

# L4 · Measure net useful review beyond historical asks

**Problem:** historical gold omits plausible findings. Reader agreement and compilation do not establish request-worthiness; author edits do not provide clean preference labels.

**Needed measurement:** exact requests, newly covered concerns versus better repairs, technical support, undesirable demands, lost useful coverage and reviewer burden.

**First experiment after a signal:** a narrow intervention versus ordinary additional work by the same producer, with comparable total resources and fresh PRs.

<div class="take">

A useful example motivates a test. A selected panel or higher volume cannot establish a harness advantage.

</div>

<div class="source">Sources: <a href="todo/adjudication-rubric.md">assessment question</a> · <a href="research/open-code-review-comparison-2026-09.md">evaluation precedents</a></div>

<!--
Use the shared human rubric and distinguish unresolved from pending. Model-only judgments
are not independent evidence of maintainer value. A human label is also a judgment, distinct
from an observed historical request. Blinding must preserve technical facts required to judge.

Compare the Opus producer as well as the DeepSeek consumer. Gains must be read alongside
lost requests, wrong demands, costs and the exact delivered output. Three replications are a
repository floor, not a guarantee of power; cluster uncertainty by PR and avoid treating sibling
asks as independent. Report all asks with diagnostic subsets, not only the intervention's
in-census or recoverable subset. Human usefulness/time savings are separate future claims.
-->

---

<!-- slide: ai-pr-research -->

# L5 · Review the contribution's purpose and scope

**Eventual target:** AI-authored PRs, including large changes with locally valid code.

**Observed difference:** in the validation audit, PR-level asks were **16.1% on the AI slice versus 5.1% on other PRs**. This is a sampled association, not an authorship effect.

**Question:** is the contribution needed, coherent, appropriately scoped and integrated with the library—not just a collection of valid declarations?

**First test:** a bounded, stratified set of real AI PRs; compare a purpose/scope pass with equal additional whole-PR review. Keep missing historical intent visible.

<div class="take">

Local mechanical wins may help. They do not cover whether this contribution should exist in this form.

</div>

<div class="source">Source: <a href="research/pipeline-overfit-2026-09-replication.md">validation audit and AI slice</a></div>

<!--
The original 1,000-PR draw realized 973, including an AI stratum; authoredness and available
flags have caveats in the source report. Retain/filter the AI slice rather than exclude it.
Use the historical title/description with provenance flags: later edited descriptions can leak
outcomes. A purpose extracted from the submitted design can turn an implementation choice into
a requirement, as the reconstruction briefs demonstrated. AI versus other PRs is descriptive
here, not randomized and not proof of causal authorship differences. Sources on PR-level briefs
also show some asks require history or information outside the code.
-->

---

<!-- slide: stopping -->
<!-- _class: dense -->

# What should stop, and what would reopen it?

| Thread | Do not spend on this alone | Evidence that could reopen it |
|---|---|---|
| Whole-contribution reconstruction | More plausible alternatives or familiar-fixture explanations | Useful producer-specific behavior plus a feasible resource comparator |
| Dossiers and exams | Better scores with rule/location supplied | A demonstrated understanding gap and transfer without target-ask selection |
| General convention detectors | More correct facts from a tiny part of the tail | A larger useful opportunity class or an explicit precision-focused objective |
| More specialists, critics or gates | More jobs, cells, filings or agreement | A specific observed loss and new discriminating information |
| Tool-using comparison Task | The next numbered architecture milestone | A selected consumer that needs the capability |

**Park a thread when it cannot change an investment decision. Preserve what would reopen it.**

<div class="source">Sources: <a href="dead-ends.md">stopped designs and retractions</a> · <a href="todo/README.md">open hypotheses</a></div>

<!--
These are bounded statements about tested designs and current priorities, not universal
impossibility claims. General mechanical checks may have engineering or precision value even
when they are not broad recall levers. Uncertainty does not obligate a larger campaign.
Reweighting artifact-only selection signals already near chance is not new information.
Do not erase abandoned threads or change a historical plan to make it match today's judgment.
-->

---

<!-- slide: status -->
<!-- _class: dense -->

# What is live—and how this map stays current

| Work | Snapshot read here |
|---|---|
| Shared sessions, matchings and handoffs | Accepted and merged; `develop` includes `a9154196` |
| Context/checking operations and assessment export | Implemented, offline-verified; unmerged `review-operations@01008813` |
| Grounds reading | Complete with accepted qualifications; `grounds-reading@b1b2d859` |
| Additions triage | Independently reviewed: park pipeline; labels pending; `useful-additions-triage@f2e4ba95` |

**Update when evidence changes a claim or a priority.** Each live thread keeps: motivation → question → cheapest discriminating check → payoff → stopping condition.

Details stay in [questions](questions.md), [todos](todo/README.md), [dead ends](dead-ends.md) and linked experiment records. Historical plans remain dated.

[Back to the map](#2) · [Near-term choices](#4) · [Long-term questions](#25)

<!--
Initial source: supervisor_update_2026-10/slides.md, unchanged, hash
4ee0a0fcaf3fde1177f8e04495e46179f4e78a47. The prose version is 8ee20776.
This revision converts the maintained overview into Marp, adds nonlinear navigation and an
opportunity portfolio, and refreshes the additions-triage status. No experiment is run here.

Source locators for worktree links (replace with repository links when integrated):
- grounds-reading@b1b2d859:docs/research/review-reconstruction-phase-a-review-2026-10-20.md
- grounds-reading@b1b2d859:results/pr_review_v5/probes/review-reconstruction-search-audit-2026-10-21/README.md
- grounds-reading@b1b2d859:docs/research/library-mechanism-grounds-2026-10-22.md
- review-operations@01008813:docs/research/review-operations-implementation-2026-10-22.md
- useful-additions-triage@f2e4ba95:docs/research/phase-a-additions-triage-2026-10-23.md
- useful-additions-triage@f2e4ba95:results/pr_review_v5/adjudications/phase-a-additions-2026-10-23/README.md

For each future result, edit the synthesis here, record the exact measurement in questions.md,
and close/revise its todo or dead-end entry. Separate observation, interpretation and proposed
test. Name the closest literature overlap when making a novelty claim. Read branch work before
starting a duplicate thread. Regenerate exported HTML after changing this source, and update
numeric navigation links if slides move. Source paths and claims must stay date-gated.

Rendering, from the repository root:
  /common/home/ya475/.local/opt/node-v24.21.0/bin/node /common/home/ya475/.local/bin/marp \
    --html docs/project-research-overview.md -o docs/project-research-overview.html
The absolute executable paths are local tooling, not project prerequisites; elsewhere use marp.
The source is the maintained artifact; generated HTML is a local preview.
-->
