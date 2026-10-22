# Published reviewing systems: requirements for the refactor

2026-10-22. Targeted primary-source reading for the
[task/data refactor design](task-dataflow-refactor-design-2026-10-22.md).
This is a selection of contrasting architectures, not an exhaustive survey or a ranking.
It extends the [September systems survey](code-review-systems-survey-2026-09.md) and the
[open-code-review comparison](open-code-review-comparison-2026-09.md).

Primary paper sections, published source code, and the Bugbot engineering report below
were retrieved and read for this document. Published results belong to their authors and
populations; no system was executed here. Architectural consequences are our inferences,
not claims that the papers endorse the proposed APE implementation.

## Reading map

| ID | Primary source inspected | Evidence and scope |
|---|---|---|
| S1 | [AutoCommenter: AI-Assisted Assessment of Coding Practices in Modern Code Review](https://arxiv.org/html/2405.13565v1), especially §§3.1, 3.5, 4.1–4.3, 5.1, 6 | Industrial deployment paper, AIware 2024. Trained predictor of a source location and best-practice URL, calibrated and assessed in Google's environment |
| S2 | [BitsAI-CR: Automated Code Review via LLM in Practice](https://arxiv.org/html/2501.15134v1), especially §§3.2–3.5, 4, 5 | Industrial system paper, 2025. Fine-tuned rule checking and filtering, context preparation, aggregation, feedback and retraining |
| S3 | [RovoDev Code Reviewer](https://arxiv.org/html/2601.01129v1), especially §§3.1–3.3, 4.2, 5.1, 5.3, 6 | Industrial online-evaluation paper, 2026. Contextual generation, factual judge, trained actionability gate; several distinct outcome measures |
| S4 | [Building a better Bugbot](https://cursor.com/blog/building-bugbot), especially “Humble beginnings,” “Measuring what matters,” “Hill-climbing,” “Agentic architecture” | Vendor engineering report. Describes successive designs and evaluation; component claims are not an independently replicated ablation |
| S5 | [Tricorder: Building a Program Analysis Ecosystem](https://research.google/pubs/tricorder-building-a-program-analysis-ecosystem/), [paper PDF](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43322.pdf), especially §§III–IV | ICSE 2015 platform paper. Shared analysis API, heterogeneous analyzers, stage/resource prerequisites and developer feedback |
| S6 | [alibaba/open-code-review](https://github.com/alibaba/open-code-review/tree/55899906abc6381ad08f92a81ea2db50c56c7cba), pinned revision `55899906abc6381ad08f92a81ea2db50c56c7cba` | Released implementation. Inspected `agent.go`, `selection.go`, review-filter prompt, comment tool, coverage manifest and resume identity. Source establishes behavior, not component effectiveness |
| S7 | [CRScore: Grounding Automated Evaluation of Code Review Comments in Code Claims and Smells](https://arxiv.org/html/2409.19801v1), especially §§3, 5.4 and Limitations | Evaluation-method paper, initially 2024. Generated pseudo-references plus static analysis, semantic similarity, human comparison and failure analysis |

As a separate design reference, [PROV-DM, W3C Recommendation 2013-04-30](https://www.w3.org/TR/2013/REC-prov-dm-20130430/)
distinguishes entities, activities, generation, use and derivation. This supports separating
data from execution provenance conceptually. It is not evidence of reviewing quality, and
we do not propose implementing the complete PROV standard.

## S1 — AutoCommenter: an attributable prediction and its deployment policy are separate

The model predicts a location and best-practice URL, with an empty target for no violation
and an associated confidence. The paper describes roughly 800k best-practice training
examples inside a multi-task training corpus. A comment is a rendered, developer-facing
form of that prediction.

A global confidence threshold and then per-language thresholds were inadequate. The
deployment moved to per-URL thresholds. Outdated practices also required conditional
suppression independently of retraining. The paper separately discusses explicit user
feedback, independent ratings and estimated comment resolution.

**Adoptable requirement:** retain the prediction's subject and rule/source identity, the
exact output, the calibration policy, and the publication decision as separate data. A
policy change must be assessable on a fixed set of predictions without pretending the
generator changed. Publication/suppression is part of the deployed system's measured cost
and behavior.

**Question for this refactor:** can we recover exactly which policy and source version led
to a final finding, while preserving candidates that were suppressed? Can a calibration
change be scoped to a rule or population without rewriting the Task or raw outputs?

**Transfer limit:** confidence from a trained prediction model is not interchangeable
with a prompted reviewer's self-reported confidence. The paper's successful calibration
does not validate such confidence here. Its comment-resolution estimate includes a
manual check of the automated snapshot comparison; disappearance alone is not endorsement.

## S2 — BitsAI-CR: data and feedback are parts of the mechanism

The pipeline prepares context, uses a fine-tuned RuleChecker over a 219-rule taxonomy,
applies a separately fine-tuned ReviewFilter, and aggregates similar comments. The paper
also describes rule mining, annotation, retraining, and recurring online evaluation.

Its feedback channels have different meanings: likes/dislikes, manual precision annotation,
and “Outdated Rate,” the fraction of seen comments whose associated code becomes outdated
within the measurement window. Rules can have technically correct comments but low
adoption, and the authors describe decommissioning such rules.

**Adoptable requirement:** a generator, an assessor, a decision policy and an observed
feedback event need distinct contracts and versions. Store rule membership and available
training/annotation snapshots when a component is learned. A filter must record which
candidate it removed and under what authority.

**Question:** can the same candidate collection be evaluated with an alternative filter,
deduplication policy or human assessment without rerunning acquisition and generation?
Are changed wording and grouping visible, so a surviving candidate's old judgment cannot
be attributed to a rewritten final comment?

**Transfer limit:** the checker and filter are trained, and annotations are continuously
collected. A taxonomy plus a prompted second pass is a different intervention. Embedding
similarity and representative selection are lossy domain policies, not generic framework
defaults. Outdated Rate is an observed adoption proxy, not technical correctness or causal
proof that the comment caused the edit.

## S3 — RovoDev: distinguish outcome definitions precisely

RovoDev uses contextual generation, an LLM factual-correctness check, and a ModernBERT
actionability gate trained on more than 50,000 historical generated comments labelled by
resolution. It examines online resolution, developer feedback and offline human alignment.
The paper explicitly warns that lack of alignment with a human comment does not imply
that a generated comment is useless.

**Metric clarification relevant to our older summaries:** §5.3 reports the actionability
check's improvement of **20 percentage points in location-only human alignment and 15
points in location-plus-semantic human alignment**. These are not a measured 15–20 point
increase in online comment-resolution rate. The factual judge's minimal impact in this
comparison also concerns those measured alignment outcomes. Avoid quoting “the gate
improved quality by 15–20 points” without naming the outcome.

**Adoptable requirement:** every assessment names its target, context, protocol, population,
and outcome definition. Reports should preserve distinct validity, historical alignment,
desirability and observed-resolution columns. A structured label is still an instrument
whose validity must be checked.

**Question:** can an actionability model be trained or calibrated using only the proper
historical split, then evaluated against fresh findings? Can the system prevent its
evaluation references from entering generation context?

**Transfer limit:** historical resolution labels are feedback with selection effects;
they are not automatically maintainer-desirability ground truth. A trained gate's gains
do not establish the benefit of another general-purpose prompted judge.

## S4 — Bugbot: do not make a fixed review pipeline the framework

The report describes an earlier system with eight randomized passes, grouping, majority
selection, rewriting, category filtering, validation and deduplication across runs. It
then describes larger gains after adopting a tool-using agent that decides where to
investigate, and experiments with static versus dynamically retrieved context.

Its quality loop combines an offline curated bug benchmark with an AI-assessed online
resolution measure checked against authors. The report attributes improvements to many
iterations; it does not publish enough information to reproduce each component effect.

**Adoptable requirement:** a single Task may own a long interactive loop. A program may
also compose multiple Tasks, branches and repeated passes. Tools and context delivery
are part of the effective condition. The framework must accommodate both designs without
forcing the agent's internal investigation into a static phase graph.

**Question:** can we replace a fixed producer/consumer chain with a single tool-using
reviewer while keeping the same output and assessment contracts? Can we inspect the exact
tool interface and delivered context, not just the top-level prompt?

**Transfer limit:** randomized agreement is a candidate mechanism, not a reliable universal
selector. Our local agreement experiments include a later negative result in
[`questions.md`](../questions.md). The vendor's resolution rate is not directly comparable
to our historical-ask recovery, and the post does not establish that prompt aggressiveness
or agentic control will solve Mathlib's residual misses.

## S5 — Tricorder: the shared platform boundary is meaningful

Tricorder connects heterogeneous analyzers through a common, language-agnostic protocol
buffer API. Its analysis driver, workers, prerequisite stages and developer-facing result
delivery have different responsibilities. Analysis can require different resources or
build stages; expensive later stages do not have to prevent earlier analysis from working.
Developer feedback is connected to analyzers and influences which results are acceptable.

**Adoptable requirement:** standardize execution and result handoffs without standardizing
every analyzer's algorithm. Represent resource prerequisites and scope. Keep technical
validity distinct from whether a developer wanted the comment, even when both inform a
publication policy.

**Question:** can a deterministic detector, a model-backed collector and a human import
produce interoperable domain data without impersonating one another's execution? Can a
missing Lean environment be distinguished from a negative technical check?

**Transfer limit:** Google-scale RPC services and a universal analyzer-result format are
not a reason to build microservices or force every evidence type into a review finding.
The API lesson concerns a well-defined boundary; our boundary should be typed domain
products with a small common reference/provenance envelope.

## S6 — open-code-review: mechanical selection and coverage are executable contracts

At the pinned revision, `internal/agent/selection.go` contains one pure selection function
used by preview and execution. `agent.go` seals selected work and records failures, including
input failures. `session/manifest.go` distinguishes selected items, completion, reuse,
failure and waiver. `session/resume_identity.go` checks input/rule identities; it also
allows explicitly requested provider/model transitions, so it is not a universal
“everything must be byte-identical” resume policy.

The [filter prompt](https://github.com/alibaba/open-code-review/blob/55899906abc6381ad08f92a81ea2db50c56c7cba/internal/config/template/prompts/review_filter_task_user.md)
limits removal authority to comments the diff proves wrong. A filter with narrow authority
is a different operation from a desirability selector. The agent also owns a dynamic loop
within grouped review work.

**Adoptable requirement:** share resolved selection between preflight and execution;
record the expected collection before work starts; make failure and waiver explicit; give
assessors narrow, declared authority. A run's done predicate must check the requested
input/condition, not simply find an output file.

**Question:** when a file/case is missing, can we distinguish not selected, not scheduled,
execution failed, completed empty, and explicitly waived? Can another filter replay on
exact recorded candidate inputs?

**Transfer limit:** the source's behavior does not establish an improvement in recall or
precision. The previous local source-history review includes measurements, but this
reading did not rerun or independently verify their experiments. We should not adopt a
fixed file grouping, filter or multi-pass design as a framework requirement.

## S7 — CRScore: generated evaluation data needs provenance and challenge

CRScore generates low-level change claims and higher-level implications using a model,
combines these with static-analysis outputs, and compares review sentences to those
pseudo-references. It separates several quality dimensions and evaluates them against
human annotations.

Its failure analysis and limitations describe missing pseudo-references, semantic
similarity failures on short questions and inline code, moderate human correlation, and
the fact that annotators initially see the generated pseudo-references.

**Adoptable requirement:** references are typed, versioned data with an acquisition method
and epistemic status. Generated claims must not silently become gold. A reference-building
Task, a matching Task and independent human assessment must be independently inspectable.

**Question:** does the judge share unvalidated assumptions with the reference generator?
Can a new valid finding challenge the reference set without either being called false or
retroactively improving the benchmark used to tune that finding?

**Transfer limit:** similarity is not an evaluator of Mathlib maintainability or a substitute
for independent desirability labels. This paper is evidence that reference construction
and evaluation have failure modes, not proof that pseudo-reference generation solves ours.

## Consequences for the proposed design

| Requirement | Motivation | Design decision |
|---|---|---|
| Interchangeable domain products | S1, S2, S5 | Typed payloads and durable references, independent of producer result subclasses |
| Distinct generation, assessment and publication | S1–S3, S6 | Assessments are data; policies explicitly consume them and record decisions |
| Dynamic investigation and staged composition | S4, S6 | Ordinary Python composition plus APE Task invocation; no mandatory static review DAG |
| Exact population and missingness | S6 | Collection snapshots and per-member outcomes; shared preflight resolution |
| Scoped resources and context | S2, S4–S6 | Resource snapshots/grants plus actual delivered-content and access records |
| Separate measured outcomes and reference provenance | S1–S3, S7 | Versioned protocols and reports with named populations and estimands |
| Learning and feedback remain possible | S1–S3 | Feedback events and training/calibration snapshots can be ordinary domain artifacts |

The sources justify these capabilities. They do not justify fixing the number of agents,
always adding a critic, adopting majority voting, making every operation a rule checker,
or prioritizing a vendor's metric over the research question.

## Retrieval identity

All sources were accessed on 2026-10-22. Paper links pin the inspected arXiv version;
source-code links pin the commit. For mutable web pages, a hash identifies the retrieved
response, not a permanently retrievable edition. Relevant text and sections are described
above so a reviewer can inspect the primary source directly.

| Source | SHA-256 of inspected HTML/PDF/source response |
|---|---|
| S1 HTML | `54ab44c3c2324608563e203e22dc2c33f8ca95f3cc5d89e30937306590dc17c8` |
| S2 HTML | `de34b7233e2e28bbef69f2f2d9f4b92501110b81f06ff60c9e79d21688a3c424` |
| S3 HTML | `24a02dd58c1d0a63f22af800d91b7e22bf4bb7d1887fbfdfe4fe7e55d1e03810` |
| S4 HTML | `82acd0448f91e49c1684b2d818d4df163a6f983010fc5f82294d67b0afc4ae92` |
| S5 PDF | `6dd64721e7174d9d8818dd32135290e82e83f407ad3ea49e2694bfe37f92c3c1` |
| S6 `agent.go` | `bba22e963685e3d95deb1f5ef0da53d4e369057a36d1fb3e0726fce76b4cc734` |
| S7 HTML | `d9a620a1ac3ece38fff04ea6cd7344ef145ad8a79efffe1fcd8dea18d8d1210d` |
| PROV-DM HTML | `5c925c21bc96c285b25017c3b90d82cf74251d07713b71fcb81ca60f873c9e88` |

## Independent review (Claude, 2026-10-22)

The seven sources were not re-fetched; the hashes above are the author's. The reading is
reviewed on its internal logic and on its transfer to this tree at `develop` `4695a1b1`.

### What holds

- The transfer limits are stated correctly for all seven. The reading never uses a deployed
  system's gain to justify a prompted stage here, which is the error the September survey
  warned about.
- S3's correction is needed in the record. `code-review-systems-survey-2026-09.md` says the
  actionability gate moved "15-20pp" without naming the outcome, at lines 15, 43 and 186. The
  figure is human-alignment, not resolution rate. Fix those three lines or footnote them. The
  auto-memory on external framing does not carry the figure, so nothing to correct there.
- S6's observation that resume identity permits an explicitly requested provider change is
  the right precedent for `RESUMABLE_PLAN_FIELDS` and for the F2 discussion in the plan.

### What does not discriminate

The consequences table maps seven requirements to seven design decisions, and every decision
in the right-hand column is the direction the tree already took: typed payloads with
`schema_version` literals; assessments as sealed data (`EvaluationProtocol`, `PairManifest`);
`cli pipeline` plus Python composition; `coverage_gaps` and the `StageInput` refusal of a
partial run; sealed tool grants and the gold-free reviewer tree; versioned judge identity. So
the sources justify the status quo exactly as well as they justify the proposal. The useful
version of the table is shorter: what the sources would require that the tree does not have.

| Requirement | Nearest thing in the tree | Gap |
|---|---|---|
| Suppressed candidates kept with the policy version that suppressed them (S1, S2) | `CandidateRejection`, `SynthesisDecision`; the filing contract's `Cell` | the policy version is not on the rejection row |
| A report that names its population and estimand (S3) | `report conditions` refuses a mismatched judge identity and denominator | the estimand (conditional on completion, or end to end) is not a column |
| A filter with narrow, declared authority (S6) | `filing_contract.py`: filing follows evidence, worth is not a ground | built for one family of designs; not a shared assessor contract |
| References as versioned data with an acquisition method (S7) | gold obligations are sealed with provenance; raw asks live in probe `asks_*.tsv` files | raw asks have no schema or seal in `src/` |

Each gap is one field or one file, not an architecture.

### Missing

- None of the seven is about a research harness. All are deployed systems with a feedback loop
  this project does not have. The requirement they most strongly support, that one Task may own
  a long loop while a program composes several (S4, S6), is already how `DESIGNS` and
  `run_subtasks` work.
- The project's reference memory lists the harness-effect papers (Zhang, Harness-Bench,
  Arjmandi, AHE) as the precedent for model-by-harness factorials. The design's success
  criterion 3 and the standing rule "never build for one model" rest on that literature, not on
  these seven. Not verified here; cite them or say why not.
- `open-code-review-comparison-2026-09.md` reached the S6 conclusions in September. Cite it, so
  the record does not read as two independent discoveries of the same thing.

Added later the same day: the concrete instance of the S7 gap in this tree is the matcher
rubric, which the kernel imports from a probe directory (`analysis/probes.py:782`) and which
exists in eleven copies and variants under `results/`. The S1 and S2 requirement, a fixed set
of predictions re-scored under a changed policy, has the same prerequisite: one versioned
instrument in `src/`. See the design's §19.8.
