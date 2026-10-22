# Making review experiments accumulate into a design

2026-10-22. Assessment and proposed changes; no runtime changes implemented.

The core recommendation is to retain APE's Task, scaffold, runtime and orchestration
abstractions, and make **a controlled comparison between executable designs** an explicit
object. A Task describes work to perform. It does not describe what a research intervention
changes, which other conditions must remain equal, or what its result establishes. Much of
that second contract currently lives in prose and study-specific scripts.

This is a continuation of the October 6 [codebase audit](codebase-redesign-2026-10.md), not a
replacement for it. Several of its recommendations are implemented. The remaining problem
is partly missing abstractions and partly failure to use the abstractions already built.
Better infrastructure can make experiments interpretable and inexpensive to compare; it
cannot guarantee that a proposed reviewing mechanism improves judgment.

## Scope and evidence

Inspected `develop` at `4695a1b1`, including the uncommitted research documents in this
checkout. Also inspected the newer `review-reconstruction` branch at `eecb7d18`, the
`route-search-symlinks` fix at `556052bf`, and relevant work on `demonstrated-change` at
`e9b9b6e0`. Those newer changes are not all integrated into `develop`. Branch results below
are readings of saved artifacts, not experiments rerun for this assessment.

The reading included the project-status, questions, dead-ends and todo registers; the
October 6 architecture audit and its implementation record; recent reconstruction
assessments and the newer branch's `RESULTS.md`; Task construction, nested execution,
review designs, producers, pipeline/stage schemas, run identity, comparison reporting,
output schemas, and tool-outcome readers. The September systems survey and its October 19
extension on `demonstrated-change` were also read. AutoCommenter and BitsAI-CR primary
papers were refreshed directly; this is not a new exhaustive literature survey.

147 existing targeted tests passed locally. Three small offline probes reproduced the
configuration, resume, and missing-tool-result behaviors described below. No generation,
semantic judging, or other paid model calls were made. Existing workspace edits were left
alone.

## What the experiments have taught us

These are bounded conclusions, not universal claims about models or reviewing.

| Observation | What it supports | Consequence for the codebase |
|---|---|---|
| The early selection-wall result counted a candidate at the maintainer's location; later readings distinguished the actual concern and requested transformation. | Site coverage is insufficient evidence that a useful alternative was generated. | Link artifacts through discovery, construction, submission, merge and evaluation; preserve the concern and the candidate, not just the location. |
| Fanout executed previously pruned arms without reliably recovering the missing asks; structured ledgers could be nearly all `no_issue` without improving recovery. | Executing more jobs or recording more dispositions does not establish better investigation. | Make decomposition optional; collect observable tool outcomes and artifacts independently of a design's self-reported ledger. |
| Filing-bar changes and stricter filing contracts produced different results across models and panels, often increasing volume. | Withholding exists, but is not a general explanation or cure. | Keep construction, verification, filing and finalization independently inspectable and replaceable. |
| Phase A's 56 new successful reviews used the intended packets and final serialized outputs, but neither reconstruction condition achieved its registered historical-ask gain. Concrete sketch proposals did transfer. | Transmission of a proposal is established; improved maintainer judgment and superiority to ordinary extra reviewing are not. | A comparison must distinguish intermediate capability, end-to-end quality and the cost of the producer. |
| Phase A assessed novel strategy findings for technical support, without establishing whether maintainers would want them. | A compiling, in-scope proposal and a desirable review request are different outcomes. | Keep technical validity, historical-ask recovery and independently assessed desirability as separate measurements. |
| The consumer brief prohibited questions, despite parts of the design and evaluation allowing them. | An unexercised output capability cannot be diagnosed as a failure to use that capability. | Validate output capabilities across instructions, submit tools, serialization and measurement. |
| Reconstruction amendment 7 repaired symlink search and supplied adoption evidence. At PR 33117, Opus recovered the ask in 0/3 baseline, 0/3 correspondence, and 1/3 correspondence-plus-adoption sessions. | The registered positive contrast did not occur. Evidence delivery alone did not reliably change the decision on this case. | Preserve a mechanism diagnostic separately from an improvement claim; retain the exact execution environment. |
| Three of five amendment-7 decliners also relied partly on failed constructions with a missing import or prerequisite; the successful filer repaired its attempt. | The latest result still mixes construction failure and preference. It does not isolate a pure judgment ceiling. | Record what the attempted check actually tested, prerequisites and repair history; a failed construction must not silently become a refutation of the intended change. |

Sources: [questions register](../questions.md), [dead ends](../dead-ends.md),
[Phase A assessment](review-reconstruction-phase-a-review-2026-10-20.md), and
[`review-reconstruction` results](../../.claude/worktrees/review-reconstruction/results/pr_review_v5/probes/review-reconstruction-2026-10-19/RESULTS.md).
The last source is worktree-local; its authoritative revision is `eecb7d18`.

This record represents progress in measurement and diagnosis. What remains unestablished
is a broadly effective improvement over a strong solo reviewer. Infrastructure progress
and capability demonstrations should be reported as such, so they do not repeatedly become
unsupported claims of reviewer improvement.

## One core design, with room for competing review designs

The useful separation is by responsibility, not by experiment generation.

| Responsibility | Core owner | Review specialization |
|---|---|---|
| Typed inputs, legal tools, submission and result | APE `BaseTask` and task classes | Review, evidence collection, alternative construction, matching or assessment tasks |
| Executing one task with a model and tool interface | Existing scaffolds/providers | APE-Agent, Claude Code or Codex conditions |
| Workspace provisioning and access | Existing runtime/workspace machinery | Dated Mathlib base/reviewed state and Lean products |
| Attempts, samples, limits, child execution, persisted outcomes | Existing orchestrator and `run_subtasks` | Solo or delegated review execution |
| Composition and artifact handoffs | Existing design hooks and stage provenance, extended at demonstrated gaps | Competing programs that retrieve, construct, compare, criticize or review directly |
| Experimental contrast and reading | A small comparison specification over those programs | A hypothesis, changed factors, repetitions, panel, measurements and interpretation |

A review design can be one Task or a program composing Tasks and deterministic functions.
Its internal result types can differ. The review adapter projects its final output into the
shared findings representation for common downstream processing. Evidence collectors and
labeling tasks should retain their own typed outputs; they should not manufacture review
findings merely to enter the framework.

This supports a one-pass reviewer, per-file reviewers, evidence supplied as tools or packet
sections, alternative-first review and a critic without imposing any of those workflows as
the core architecture. The research question is which program works under which conditions.

## 1. Resolve each invocation once, and make ineffective configuration an error

**Confirmed current behavior:** `create_task_from_data` filters override keys before
constructing the strict task config. Consequently `extra='forbid'` never sees unknown keys.
It also builds the config from overrides without seeding it from `config.task_config`.

An offline probe using `SoloReviewTask` returned:

```text
configured task_config finding_budget=3 -> effective 20
misspelled override finding_budegt=3 -> effective 20
correct override finding_budget=3 -> effective 3
all three task global indices identical: True
```

The review YAML loader already translates its `task_config` block into overrides, so this
does not establish that ordinary YAML review runs suffered this exact loss. It does establish
an ambiguous public construction path, also documented for nested judges in
[`framework-defects`](../todo/framework-defects-2026-09.md).

**Change:** establish one effective task-resolution path shared by planning, local execution,
worker reconstruction and child tasks. It should produce a resolved task configuration and
a readable receipt: input identities, task/design version, effective task settings, scaffold,
model/route/effort, tool grant, external inputs and limits. Reuse the existing execution-spec
and configuration machinery. Explicitly define config precedence. Reject unconsumed keys;
if heterogeneous batches need broadcast overrides, make their targeting explicit.

Capability checks should reach the interface the model actually uses. The search defect
was in Claude Code's built-in Grep/Glob, while APE's own search followed symlinks. A registry
test for APE's tool could never prove the other route worked. Offline route fixtures should
check known search hits through symlinked directories, supported path spellings, final
submission and provider-message round trips. Per-episode checks should verify backing
stores and workspace readiness. Authentication and live-provider continuity remain a
separate operational pilot, not a hidden model call during read-only planning.

**First acceptance check:** a non-default task setting survives parent/worker/child
reconstruction; a misspelled setting fails before execution; a granted capability reaches
the actual scaffold interface and answers its known fixture.

Code: [`create_task_from_data`](../../src/ape/tasks/base.py),
[`load_run`](../../src/mathlib_review/run_config.py),
[`run_subtasks`](../../src/ape/orchestration/subtasks.py).

## 2. Separate execution identity from experimental comparability

**Confirmed current behavior:** `RESUMABLE_PLAN_FIELDS` includes the entire
`scaffold_config_sha256`, because retry and timeout changes must be resumable. The same
digest also covers task settings, scaffold behavior and model settings. A local probe
changed only that digest and was accepted as `run_plan_revision_2.json`.

Other plan fields protect the named model, agenda and several policies; the problem is
the remaining settings whose only protection is the resumable scaffold digest. In addition,
solo prompt/context files are read through task config at execution time, and their contents
are not carried in `SoloReviewData.global_index`. A path and a git revision are useful
provenance but insufficient identity for dirty or externally generated inputs.

**Change:** resolve separate projections for:

- task/condition semantics: actual instructions, submission contract, input bytes, tool
  behavior and stores, design version, model/route/effort;
- execution attempts: retries, scheduling and operational revisions;
- evaluation: gold/ask seal, pairing, rubric, judge and output channel.

Content-address prompt and context inputs; preserve input snapshots or durable references,
not just absolute worktree paths. Keep `knob()` and its historical identity guarantees.
Use a versioned boundary for new identities rather than rehashing old runs.

Resuming to finish work and treating that work as the same experimental condition are
different decisions. Raising a cap can be operationally legitimate, but a study of performance
under fixed resources must record the amendment and cannot silently pool it with the original
budget condition. Tool timeout changes can similarly affect measured outcomes.

**First acceptance check:** unchanged input bytes preserve identity; editing context at the
same path or changing effort forks the condition; a retry revision preserves lineage; a
resource amendment remains visible to the comparison.

Code: [`seal_or_revise_plan`](../../src/mathlib_review/review/runner.py),
[`SoloReviewConfig` and prompt loading](../../src/ape/tasks/lean_tasks/formal_math/review/solo.py).

## 3. Add a comparison contract above runs

`report conditions` already checks the judge identity and exact obligation denominator and
reports mean, union, stable hits and cost. Keep it. However, callers can group runs as
repetitions by providing their names; the report does not verify their effective generation
conditions or the intended treatment difference.

**Change:** a small typed comparison specification should declare the hypothesis, baseline,
treatments, allowed differences, fixed factors, repetitions, panels, measurement identities
and reading rule. Resolve it to existing run configurations. Show a semantic diff before
execution and check actual receipts afterwards. A multi-factor comparison is legal when its
factors are declared; a model-and-route comparison should be labeled as a configuration
comparison. Do not force all studies to change exactly one field.

Include producer computation and earlier-stage failures in the resource account. A stronger
model's sketch supplied to a cheaper consumer needs an appropriate ordinary-extra-work
comparator. Equal ceilings alone do not establish equal computation.

Keep exploratory cases, retrospective/oracle diagnostics and fresh end-to-end evaluation
explicit. Track exposure by PR and, where relevant, campaign/family. Bootstrap or aggregate
at the PR or appropriate group level rather than pretending analogous asks are independent.
Preserve model-cutoff metadata without claiming it proves absence of memorization.

**First acceptance check:** passing differently configured runs under one repetition label
fails with the differing factors named. A declared model-route contrast succeeds with the
correct qualification. An oracle input cannot be reported as autonomous acquisition.

Code: [`conditions`](../../src/mathlib_review/analysis/report.py),
[`rep_summary`](../../src/mathlib_review/analysis/reports.py), existing probe seals and sets.

## 4. Make the recurring probe lifecycle use Task and artifact contracts

`DESIGNS`, producers, `StageInput`, `StageRecord` and shared nested execution are real seams
already in use. The remaining stage infrastructure is narrower than current research:
`PipelineNode.kind` names five commands, and `PipelineSpec` permits one generation run whose
outputs the other stages read. It does not express the reconstruction chain of extraction,
audit, acquisition, sketch, consumption, matching and human assessment. This is an intentional
current boundary, not a failure of that pipeline's implementation.

Consequently recurring operations live in study scripts. The current checkout has 149 Python
files outside `tmp` across 40 probe directories. Those files are not all duplication: bespoke
pre-registered analyses belong beside their results. Repeated packet execution, outcome
collection, anonymous export, auditing and matching should share implementations.

**Change:** make the next recurring producer/reader/matcher an ordinary APE Task or a
deterministic stage with typed artifact inputs/outputs, and reuse the existing provenance
ledger. Add an external-label waiting/import boundary with the same output validation for
human-produced artifacts. Compose these in a study-owned module or cell generator. APE's
orchestrator remains the executor; there is no need to replace it with a second workflow
engine or turn every study script into a plugin.

Task-native evidence collectors can be deterministic or model-backed. The existing
graph-only `Producer.facts(graph)` interface is useful for its four detectors, but does not
represent every historical-source or model-assisted acquisition task. Retain that simple
adapter while allowing other typed producers to use the same artifact handoff.

**First acceptance check:** a source-only/correspondence/full-review diagnostic can reuse its
unchanged upstream artifacts and common matcher path with one study module and configuration,
without adding a specialized branch to the review runner or a new probe CLI subcommand.
Nested versus chained execution remains an execution choice; a subscription route should not
be forced to hold a long child session inside an MCP call.

Code: [`DESIGNS`](../../src/ape/tasks/lean_tasks/formal_math/review/__init__.py),
[`PipelineSpec`](../../src/mathlib_review/schema/runs.py),
[`stage adapters`](../../src/mathlib_review/review/stage_adapters.py),
[`producers`](../../src/mathlib_review/producers/__init__.py).

## 5. Preserve evidence and operational events independently of review prompts

The current `Fact` is a located sentence with a convention identifier. Context sections are
title/text pairs. These are useful delivery formats, but insufficient as the only shared
representation for a historical source, a measured search, a relation hypothesis, a
construction or a claim-scoped verification result.

**Change:** extend the evidence types already present, using references rather than another
monolithic PR model. An acquired source needs commit/date, source location, content identity,
scope and acquisition method. A relation needs its endpoints and epistemic status. A
construction needs its exact patch/snippet, imports, workspace and prerequisites. A check
needs what it tested, the result, and its verification scope. Separate observed code facts,
inferred relationships and normative claims; a corpus count does not become a preference
merely by rendering it as prose.

Sections and tools should be views over that material where they deliver the same information.
Retain separate identities where wording or selection is itself the treatment. This makes
source acquisition, correspondence, construction and judgment independently replaceable
without asserting that the decomposition will improve review.

The observability layer also needs a small correction. **Confirmed current behavior:** a
synthetic transcript containing a `lean_verify_edit` call with no recorded result is emitted
by `tool_calls` with empty text and `is_error=False`; `classify` calls it `answered`. This
does not show that existing runs contain such calls, but it is an unsafe default for partial
or truncated traces. Add explicit missing/unknown results and incomplete coverage.

Reuse `report tools`, the execution index and stage ledger for normalized operational events:
call/result, artifact creation/consumption, submission rejection, finalization and matching.
Correlate exact candidate/check identities where available. Preserve native transcripts.
Optional post-hoc concern annotations can link these to missed asks, with `unknown` when
the trace does not expose a decision. A mandatory prose ledger is a reviewing intervention,
not neutral instrumentation and not proof that an investigation happened.

**First acceptance check:** an interrupted call is reported as missing, never answered;
a consumer can identify the precise supplied source and the check supporting a submitted
change. A failed check with omitted prerequisites remains a failure of that attempt, not a
verified refutation of the intended alternative.

Code: [`tool_outcomes`](../../src/mathlib_review/analysis/tool_outcomes.py),
[`Fact`](../../src/mathlib_review/producers/__init__.py), existing evidence schemas,
[`PatchSet`](../../src/mathlib_review/patchset.py). PatchSet support already exists; introducing
it again would repeat an outdated diagnosis.

## 6. Version output capabilities and keep distinct evaluation questions distinct

The question-channel conflict in Phase A is a concrete example of prose, submit contract and
measurement disagreeing. `DESIGNS` correctly lets designs own their submission contracts,
while the final findings adapter enables shared evaluation. Preserve that ownership.

**Change:** expose a small capability description for each design: concrete requests,
questions, coordinated patches and verification claims, as applicable. Validate that its
prompt template, submission implementation, final projection and evaluator support the
capabilities selected for an experiment. This is not a new registry enumerating every
cross-product of contract knobs. A prose semantic conflict may still need review; mechanical
capability checks can catch the structural conflicts and require an explicit aligned variant.

Keep historical concern recovery, exact-resolution recovery, technical validity and
independently assessed desirability separate. Score the final declared output channel and
preserve transformations from raw findings to final findings. Assess a strategy-blind sample
of unmatched findings from controls and treatments. A human label about an unasked finding
is assessment evidence, not a maintainer's historical ask and not new gold.

**First acceptance check:** a questions experiment cannot proceed under the request-only
contract. Reports cannot relabel technically supported findings as desired requests, or
no-agreed-ask PRs as certified false-positive controls.

## 7. Make lessons scoped, executable where possible, and dependent on evidence

There is already substantial research memory in `questions.md`, `dead-ends.md`, todos and
protocols, including tree lints requiring probes to be indexed and to discuss prior answers.
The failure is not an absence of documents. Broad conclusions can remain readable after
their supporting experiment is qualified, and finding the current qualification requires
following several documents and branches.

**Change:** add small structured metadata beside existing study records, rather than a
second narrative store: claim, population/condition, evidence references, status, limitations,
superseded-by links, reopening condition and the next discriminating observation. Literature
claims should also state the training, feedback and task assumptions that permit transfer.
Generate a current mechanism table from these records and link it from the existing indexes.
If a tool defect invalidates an assumption, mark dependent claims for reassessment; do not
automatically erase results or declare the scientific conclusion reversed.

Close an experiment with the intended contrast, the contrast actually executed, its result,
which explanation remains unresolved and the resulting design constraint. An additional
number without that update is not yet a lesson.

Turn deterministic lessons into refusals or regression fixtures. Keep statistical and
scientific conclusions as bounded evidence records: a negative experiment does not justify
a test that forever forbids the direction. Calibration failures should narrow a detector's
scope or mark it unvalidated, not silently turn its emitted situations into departures.

**First acceptance check:** querying evidence delivery versus construction versus judgment
returns the current amendment-7 qualification and its predecessor, rather than only the
earlier phrase "had the facts and declined." Querying agreement-based selection shows the
later failed replication as well as the promising in-sample result in the older survey.

## What the literature contributes

[AutoCommenter](https://arxiv.org/html/2405.13565v1) couples a learned location/best-practice
predictor with deployment calibration and developer assessment.
[BitsAI-CR](https://arxiv.org/html/2501.15134v1) uses trained rule checking and filtering,
structured feedback and repeated evaluation. Their demonstrated success is not evidence
that placing the same taxonomy and another prompted judge in this repository will work.
The training and outcome data are part of their mechanisms.

The transferable architectural lesson is to preserve attributable rule/source outputs,
independent assessment and configuration-specific evaluation. Their adoption metrics answer
different questions from matching historical Mathlib asks; an unchanged or changed final
line is not automatically rejection or endorsement of our hypothetical comment.

The project's [systems survey](code-review-systems-survey-2026-09.md) is useful precisely
because it checks proposals against local failures. It also illustrates why conclusions need
versions: its initially promising agreement signal is followed by the later ensemble result
of AUC 0.48 in the questions register. Likewise, perspective-based reading motivates concrete
constructions, but its human-reader evidence does not validate our reconstruction pipeline.

## A bounded implementation order

1. **Repair the measurement substrate:** resolve task config without silent loss; split
   semantic identity from execution revisions; fix missing-result classification. These
   have deterministic offline checks and should be framework-fix commits separate from
   reviewing interventions.
2. **Add the comparison specification:** build on `report conditions` and existing plans.
   First exercise it on already completed same-condition runs and a deliberately mismatched
   pair. No new generation is needed to establish whether the checker works.
3. **Use one real diagnostic to complete stage reuse:** reuse existing reconstruction
   artifacts to exercise typed evidence, consumer and matching handoffs. Introduce only the
   seams that this use requires; leave its study-specific interpretation beside its results.
4. **Record the scientific update through existing indexes:** distinguish implemented
   plumbing, demonstrated intermediate capability and validated reviewer improvement. Use
   fresh evaluation only when a new intervention has survived its mechanism diagnostic.

The acceptance criterion for the architecture is behavioral: changing evidence delivery,
review composition or a design-owned contract should change that component and its study
configuration, while the shared execution, accounting and reading paths remain common.
Validate that against actual extensions, not the number of registries or interfaces.

Do not begin by splitting the 2,225-line runner, deleting legacy release producers, replacing
all tests, or rebuilding TaskOrchestrator. Those changes do not by themselves make the next
experiment more informative. Preserve frozen historical inputs/results and useful regression
tests. Introduce a seam where a real experiment demonstrates the need, and verify that the
baseline's rendered inputs and intended behavior remain comparable across the boundary.

## Local validation

The following existing test selections passed, 65 and 82 tests respectively:

```bash
PYTHONPATH=src ./ape/bin/python -m pytest -q \
  tests/datasets/test_pr_review_v5_preflight.py \
  tests/datasets/test_pr_review_v5_designs.py \
  tests/datasets/test_pr_review_v5_task_data_knobs.py \
  tests/datasets/test_context_tool_grants_survive.py \
  tests/ape/test_task_identity_knobs.py

PYTHONPATH=src ./ape/bin/python -m pytest -q \
  tests/mathlib_review/test_run_state.py \
  tests/mathlib_review/test_stage_ledger.py \
  tests/mathlib_review/test_producers.py \
  tests/mathlib_review/test_tool_outcomes.py \
  tests/ape/test_openai_responses_provider.py \
  tests/ape/test_task_result_contract.py
```

These establish the behavior covered by the existing tests. They do not validate the proposed
architecture or repair the three reproduced gaps. In particular, Responses phase preservation
is present in the current provider and its tests pass; the earlier memory of a dropped phase
is a historical defect, not a current implementation recommendation.
