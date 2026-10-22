# Second refactor: shared review operations and reproducible experiments

**Status: consolidated implementation plan, 2026-10-22. Runtime implementation has not started.**
This document replaces the successive proposals and review replies previously collected here.
It is the implementation handoff for the second round; earlier design documents supply
background rather than additional requirements.

**Immediate scope: increments 0–3, ending at the first foundation checkpoint.** A later
composition checkpoint adds a tool-using research Task and a prospective experiment recipe
once their live consumer is selected. Existing research can continue independently through
its supported paths. No new model experiment or optional construction study is scheduled
by this plan.

## 1. Outcome and design principles

The goal is a small foundation on which a maintainer can change a reviewing operation,
run a controlled experiment, and understand what produced the reported findings. Today,
obtaining review tools outside a reviewer requires a synthetic Task; research sessions
cannot yet acquire those tools through their ordinary Task lifecycle. These are concrete
maintenance and composition problems, independent of whether a particular reviewing
algorithm improves recall.

Build around **review operations over explicit data, with episode-scoped resources**:

1. **One implementation per capability.** Python calls, CLI commands, MCP tools and APE
   Tasks use the same domain operations. An adapter binds resources and translates the
   interface; it does not implement another retrieval or verification algorithm.
2. **Data connects operations.** Domain outputs describe evidence, checks, comparisons or
   findings. Existing observation references identify the particular execution and output
   consumed downstream. A type describes meaning; a reference identifies an occurrence.
3. **Tasks supply execution.** Substantial model operations use APE's Task/orchestrator
   lifecycle. Small deterministic transforms remain functions. Study-owned Python composes
   them using existing planning, lineage, storage and reporting APIs.
4. **Resource scope is explicit.** Source revision, permitted source view, retrieval cutoff,
   target-PR exclusion and verification environment belong to the operation's dependencies.
   They must not be hidden in an unrelated review-arm data model.
5. **Research and engineering have different acceptance criteria.** Shared code earns its
   place through adopted callers, removed mechanics and inspectable behavior. A new
   reviewing mechanism earns scientific support through an appropriate experiment; a
   positive reviewing result is not required to accept a useful extraction.

Every increment must have a named consumer and observable payoff: a newly supported
operation, less maintained duplication or a clearer account of a result. A new abstraction
must replace the active mechanics it supersedes in the same commit series. Net line count
is worth measuring, but deleting archived experiments is not a simplification metric.

## 2. Architecture and data handoffs

```text
Episode + permitted source view + scoped resources
                         |
              shared review operations
             /           |            \
       Python/CLI      MCP tools     APE Tasks
             \           |            /
              domain values / retained outputs
                         |
          study-owned composition and selection
                         |
          normal review -> final findings -> shared evaluation
```

| Responsibility | Owner |
|---|---|
| Domain meaning | Existing episode, source, finding and measurement types; small new product types only where a real consumer needs them |
| Resource acquisition and cleanup | Existing workspace/compiler/corpus owners, bound to an explicit review-domain context |
| Computation | Independently callable functions or small resource-owning objects |
| Interaction and execution | Registered APE Tasks, existing scaffolds and MCP support |
| Retained values and handoffs | Existing observations, selected output references and lineage |
| Scientific choices and interpretation | A study recipe and its existing protocol/result record |

The intended call shape is illustrative, not an instruction to introduce these exact names:

```python
async with open_review_resources(episode, source_view, grants, options, trace) as resources:
    evidence = await search_precedents(resources, query)
    check = await check_edit(resources, proposal)
    register_review_tools(mcp, resources, grants)
```

Pass narrow dependencies to each operation. A small record can bind them; it must not
become an APE-wide service locator, a full scaffold configuration object or a partially
initialized Task. Expensive resources are acquired only when needed and cleaned up by
one clear owner. A deterministic operation does not need a Task merely to be callable.

For a future convention experiment, the dataflow could be:

```text
acquisition Task -> selected evidence output
  -> decision/comparison Task -> selected comparison output
  -> deterministic context rendering -> ordinary review Task
  -> selected final findings -> common matcher and report
```

Each arrow selects the actual producer, sample and output. The observation reference
carries execution provenance and integrity; the domain value carries substantive content.
Do not duplicate run metadata in every domain schema. Preserve the exact rendered context
and any clipping or selection delivered to the reviewer. Do not infer handoffs from file
modification times or folder naming conventions.

Task subclasses establish legal inputs and outputs. Scientific comparability also depends
on the population, source visibility, output channel, instrument and actual configuration.
Two different Task classes may produce comparable findings; two runs of one class may
answer different questions. Use existing comparison reports to expose these differences.

### Existing guarantees to preserve

Keep independent stochastic observations independent, including when their bytes happen
to be identical. Resume continues a named invocation/sample under compatible settings;
a fresh draw is a new observation. Missing, failed and incomplete outputs remain visible.

Separate three concepts: content identity, execution continuation and optional study
commitment. Ordinary source search or edit verification must not require a globally sealed
study. Preserve the first refactor's output-integrity, executor-provenance and recovery
protections. Audit only restrictions encountered on the new call path; remove or relocate
an unrelated study gate if it obstructs an actual caller. A broad sealing/hash migration
is outside this round.

## 3. Delivery order and dependencies

| Increment | Depends on | Deliverable and consumers |
|---|---|---|
| 0. Integration baseline | Current branch/worktree inspection | One coherent implementation snapshot, explicit operation dependencies and named removals |
| 1. Context operations | 0 | Normal review and `cli tool` use shared source/retrieval operations |
| 2. Verification operation | 0 and the shared resource boundary from 1 | Normal review and `cli tool` use one edit-check implementation without a synthetic Task |
| 3. Assessment export/report | 0's relevant saved-data integration; independent of 1–2 | Reproducible 40-finding diagnostic panel, blind controls and inspectable label joins |
| First foundation checkpoint | 1, 2 and 3 | Adopted shared operations, removed replaced mechanics and working assessment path |
| 4. Tool-using research Task | Shared operations plus a selected live consumer | A review specialization of the existing folder-session Task on both supported scaffolds |
| 5. Prospective study recipe | 4 plus the selected experiment's protocol | Acquisition through final evaluation using shared execution, lineage and reports |
| Composition checkpoint | First checkpoint, 4 and 5 | One newly executed research chain with recorded route-specific operational checks |

After integration, 3 can run alongside 1–2. Conditional-convention readings and existing
`compiled_filed` work need neither checkpoint. Agree ownership of shared files: operation
extraction owns the verification backend; research prototypes contribute fixtures and
requirements instead of implementing a competing checker. This decomposition does not
require multiple agents or parallel edits to the same files.

A foundation-only handoff stops after increments 0–3 and their checks. Record 4–5 as planned,
with the specific consumer still to select. Their selection does not block the first checkpoint.

## 4. Increment 0 — integration and a bounded baseline

At consolidation, `develop@a9154196` contains the accepted first refactor
(`dataflow-refactor@e13343c8`). Related evidence and code remain on
`review-reconstruction@eecb7d18` and `demonstrated-change@e9b9b6e0`; both are unmerged.
Refresh these facts at implementation time.

- [ ] Start in an isolated implementation worktree. Inspect current worktrees and changes
  on the two relevant branches; preserve unrelated working-tree changes and shared data.
- [ ] Establish the integrated baseline before changing dependent callers or exporting
  their data: first the accepted refactor, then review-reconstruction, then demonstrated-change.
  The first step is already on the inspected `develop`. Include this handoff document.
  Compare colliding untracked configs, docs and probe files before resolving them; retain
  unique edits rather than clearing them blindly.
- [ ] Use the recorded integration trial as evidence, not a script to replay unquestioningly.
  Its conflict resolutions retain the lead-run log and reconstruction's `sample_limits`,
  all relevant Mathlib-review rule bullets, both plan rows and the intended todo entries.
  Recheck the resulting tree and update worktree-specific links to integrated paths.
- [ ] Write a small caller/dependency table in the implementation record: operation,
  current owner, actual inputs/resources, active callers, replacement and removal.
  Inspect `getattr` dependencies as well as direct attribute reads. This is not another
  repository-wide design audit.
- [ ] Select an available supported configuration for later operational checks. Record
  model, effort, bounds and exposed tools. Verify local serving/GPU availability before
  assuming DeepSeek is available. Luna/Sonnet routes are alternatives; a transport smoke
  establishes operation, not reviewer quality.

The [first implementation record](../research/task-dataflow-refactor-implementation-2026-10-22.md#closure-work-after-the-follow-up-review-2026-10-22)
contains the trial order and conflict resolutions. Its
[independent closure assessment](../research/task-dataflow-refactor-implementation-review-2026-10-22.md#final-independent-closure-assessment-2026-10-22)
defines the accepted starting guarantees. Neither a historical trial nor earlier smoke
results replace checks of the newly integrated implementation.

**Done when:** the baseline revision, required capabilities, caller ownership and removal
list are recorded, and dependent work can run from one coherent checkout.

## 5. Increment 1 — independently callable context operations

**Consumers:** normal review and `cli tool`. The current workbench obtains tools by
constructing `BasePRReviewTask` with `__new__`, filling `ReviewArmData` and capturing MCP
registrations. Replace this dependency direction while keeping the supported callers.

- [ ] Extract base-source read/search and dated Zulip/precedent operations first. Put
  cutoff and target-PR exclusion inside the shared operations. Validate paths, query
  bounds and source scope independently of transport.
- [ ] Make the remaining context operations use explicit dependencies too. Preserve
  reviewed overlays and `changed_files` for declaration lookup and naming operations;
  they do not all read only the base snapshot.
- [ ] Keep base-only acquisition distinct from submitted-code review. Bind episode/base
  revision, reviewed source when granted, changed paths, cutoff/exclusion, corpus identity
  and trace information without manufacturing review-arm routing/submission fields.
- [ ] Let retrieval-only callers work without a compiled Lean workspace. Source operations
  still require the requested source revision. An unavailable index or source is an explicit
  unavailable/error outcome, not an empty successful result.
- [ ] Migrate normal context-tool registration and `cli tool` to the same functions. Give
  each tool one owner for its request schema and description. Reuse MCP definitions and
  introspection rather than retaining a production capturing registrar for tool listing.
- [ ] Preserve cleanup and existing trace behavior. Intentional changes to visible tool
  semantics must be explicit in the interface/configuration and implementation record.

Do not add a standalone MCP startup command at this checkpoint. Shared definitions remain
usable by both APE scaffold routes. When independently launched Claude Code or another
client is selected as a real consumer, add a thin startup adapter using those definitions.
The external client must not require a rewrite of the domain tools.

**Acceptance:** direct Python, CLI and MCP calls on deterministic fixtures agree in domain
results, apart from transport envelopes and timestamps. Tests cover dated exclusion,
base-only versus reviewed-source behavior, reviewed changed-file lookup, missing resources,
invalid paths and unsupported grants. Ordinary review adopts the extracted code; there is
no parallel replacement toolbox.

Source visibility also depends on native scaffold tools and workspace setup. Domain-tool
restrictions alone cannot establish a base-only experimental condition if native read,
search or shell access exposes submitted implementation or historical feedback. Verify the
supported configuration's actual workspace/tool exposure; a prompt restriction is insufficient.

## 6. Increment 2 — independently callable edit verification

**Consumers:** normal review and `cli tool`, both already active. The optional demonstrated-
change study is an additional possible consumer; extraction does not depend on deciding
to run that study or obtaining a positive construction result.

- [ ] Extract the existing edit-check operation with its actual workspace, configuration,
  error-attribution and cache dependencies. Keep one compiler backend and resource owner.
- [ ] Preserve as-is versus edited-file checks, timeouts, incomplete results and error
  attribution. A check records the source revision, complete candidate/imports, toolchain,
  options and actual environment. Checking an unchanged file cannot validate a proposed edit.
- [ ] Preserve the preference for rebuilt reviewed dependencies where available and label
  source-only overlays honestly. Retain the PR 30458 regression: changed downstream files
  must not be checked against incompatible base-only build products.
- [ ] Keep proposal/scratch changes isolated. Reuse the existing patch contract, including
  multi-file scope where a caller needs it. Missing prerequisites remain unresolved rather
  than a refutation of an alternative; compilation does not imply a finding should be filed.
- [ ] Adopt the operation in normal review and `cli tool`. Remove the synthetic Task and
  `ReviewArmData` setup for standalone tools, production `_CapturingMCP` use, and duplicated
  restoration/setup replaced by the shared boundary. Retain the public workbench behavior
  through a direct adapter. Do not create a second filesystem/workspace implementation to
  replace the fake Task; reuse or narrowly extend the existing toolkit providers.

The [demonstrated-change plan](../../.claude/worktrees/demonstrated-change/docs/plans/2026-10-18-review-as-demonstrated-change.md)
section 4 identifies 37 maintainer suggestion blocks and a closer battery. These are named
prospective consumers and useful regression inputs. Running that empirical study remains
separate; acceptance here uses focused deterministic fixtures and existing callers, not a
new 37-case campaign.

**Acceptance:** direct/CLI/MCP parity holds on local fixtures, existing edit-check regressions
pass, and standalone tools no longer instantiate a stand-in review Task. Missing compilers,
failed builds and timeouts cannot produce a successful check. The migration removes the
replaced active mechanics in the same series.

## 7. Increment 3 — assessment export and readable outcomes

**Consumer:** the existing demonstrated-change proposal to read unasked verified findings.
This is saved-data work and can proceed independently of operation extraction.

- [ ] Export 40 verified solo findings at unasked places from the existing population,
  stratified before labels by available family/split/PR metadata. Mix in separately counted
  asked-suggestion controls in blind order. If the eligible population cannot supply the
  planned panel, report that explicitly rather than silently substituting other output.
- [ ] Publish the selection rule, eligible/selected counts and strata, missing metadata,
  seed, exact final finding bytes/digests and source references. Keep the blinding map
  separate from the reader's packet; freeze the panel before collecting human labels.
- [ ] Reuse the existing adjudication store and vocabulary with a clear human-facing rubric:
  `correct_ask` = a valid change worth requesting; `valid_not_an_ask` = true but not worth a
  review comment; `wrong` = technically unsupported/incorrect. Pending or unresolved
  judgments remain explicit in the reading, without being coerced into one of the labels.
- [ ] Document that `AdjudicationLabel` is already an off-gold judgment. It is separate from
  evidence that a maintainer actually asked for something. No new schema version is needed
  merely to clarify that distinction. Asked controls remain a separately reported subset;
  any different rubric or label semantics must receive an explicit adjudication version.
- [ ] Join labels to exact exemplars. A recurring site/kind key does not prove another
  finding makes the same claim; inspect inheritance before using it in a comparison.
  Missing labels remain missing. An asked place can also contain an unrelated suggestion.
- [ ] Provide a human-readable report of the selected findings, labels/disagreement,
  unresolved checks and exact references. Reuse existing loaders, adjudication and reports;
  this export is not a second result database or evaluation pipeline.

### Reading rule and limits

This is a selected diagnostic panel, potentially with several findings per PR. It is not
an estimate of population precision or of another harness's incremental output quality.
Before labeling, state its decision use: distinguish technical-error problems from correct
but unwanted suggestions and plausible useful additions, then choose what to investigate
or assess next. A taxonomy alone does not establish a harness improvement.

If unwanted/incorrect suggestions recur, use the examples to diagnose a mechanism and
choose a targeted intervention. If useful unasked findings recur, assess additions from
the particular competing design. If labels are unresolved or readers disagree, address
the rubric/evidence gap before treating them as a selection signal. Report what the panel
supports even when it does not settle a policy decision.

Changes to output-volume policy require the maintainer's chosen objective and evidence
about the affected design's output; this panel alone cannot set that policy. A later
balanced assessment should include baseline findings, additions, losses, declines
and technically valid alternatives to historical asks. Human labels never become historical
gold or extra recall credit; silence on a PR is not a certified negative label.

For the next within-study contrast, use one named instrument/version/rubric and explicit
evaluator configuration, subject set, output channel, denominator and repetitions. Report
missingness and judge disagreement. Old/new matcher calibration is needed for a claim of
measurement continuity, not merely to use one fixed instrument in a new comparison.

**Acceptance:** export and report reproduce from saved data; exact findings and controls
can be joined back to their sources; missing human labels are supported. Human annotation
and a positive usefulness result are not prerequisites for the engineering checkpoint.

## 8. First foundation checkpoint and handoff record

The immediate implementation is complete when increments 0–3 meet their acceptance criteria:

- [ ] Normal review and `cli tool` use shared context and verification operations.
- [ ] Standalone use no longer constructs a synthetic Task or captures registrations to
  recover callable operations. Replaced active setup has been removed.
- [ ] Source scope, dated retrieval and verification provenance have behavior-level checks.
- [ ] The assessment export/report works with explicit selection, controls and missingness.
- [ ] Focused regressions, the integrated suite and frozen verification have recorded outcomes.
- [ ] The implementation record identifies new/changed interfaces, actual callers, named
  deletions, production lines added/removed, limitations and any outstanding user-run checks.

Write one implementation record, updating it increment by increment. Include exact local
commands and saved-data reproductions. When a model-backed operational check is useful,
provide complete user-run commands and dry-run/preflight results. Do not run generation,
ingestion or semantic judging as part of this local implementation. Clearly distinguish
implemented, offline-verified, live-verified and still planned work.

Retire legacy `probe seal` / `match-inputs` / `unblind` command routes only after an audit
across the integrated active callers shows no prospective dependence. Keep shared functions
still used by common evaluation and readers needed for historical records. Archived probe
scripts, `ctxtool.template`, plans and run artifacts are not deletion targets for line savings.

The checkpoint demonstrates a stable engineering foundation, not an improvement in review
quality. Existing experiments can continue before or after it through supported routes.

## 9. Later composition checkpoint — increments 4 and 5

### Start condition

Select a new acquisition or comparison operation with a written question, concrete input/
output, source/tool needs, control and expected observable payoff. It must be a live consumer,
not a demand to rerun retired whole-PR reconstruction. Saved reconstruction data remains
useful for handoff regressions. Another justified consumer can replace the current candidate.

For the conditional-grounds candidate, the cheapest scientific sequence is: read the
existing grounds census, then test census-stated grounds as text through the existing
`context_with_sections` path on fresh decisions, then consider autonomous recovery if the
supplied grounds change decisions usefully. The first two steps need no new acquisition
Task. This candidate's sequence is not a universal gate on tool-using Task support for a
different selected experiment.

### Increment 4 — review session Task

- [ ] Specialize the existing folder-session Task with episode/resource binding. Reuse
  input materialization, declared-output validation and submission. Keep generic
  `PacketSessionTask` domain-free; avoid inheriting whole-PR finding submission merely to
  obtain retrieval tools.
- [ ] Declare an existing reviewer-visible episode reference, permitted source view,
  required capabilities, retained files and output specifications. Resolve cutoff and
  exclusion through existing episode rules, not an unchecked user-supplied cutoff.
- [ ] Extend shared session planning/payload construction and the existing Task registry;
  version changed plan semantics while preserving readers for old packet plans.
- [ ] Bind the same domain operations on ape_agent and Claude Code through existing MCP
  lifecycle support. Record effective tool exposure and source visibility in resolved inputs.
- [ ] Keep output selection, coverage, lineage and trace on existing session/observation
  APIs. Reject missing episode/capability prerequisites before model interaction.

**Acceptance:** offline checks cover source views, missing grants, independent samples,
resume and declared-output integrity. User-run checks on both supported scaffold routes
perform a source read and dated retrieval and publish the declared output. Inspect actual
tool exposure, serialized output and trace. Earlier folder-session smoke checks do not
establish this new binding; a particular stronger model is not required for a transport check.

### Increment 5 — one prospective recipe

- [ ] Compose the selected acquisition/decision operation, context derivation, ordinary
  review and common evaluation using existing APIs. A small study-owned Python recipe is
  sufficient; reuse the orchestrator instead of looping over `TaskRunner.run_task`.
- [ ] Provide a no-spend planning path that resolves available inputs/configuration and
  marks future model outputs pending. Specify conditions, intended differences, producers,
  repetitions, output channel and expected cases in study data.
- [ ] Select upstream observations explicitly. Distinguish reused fixed evidence from
  newly sampled acquisition, and consumer repetitions from independent harness repetitions.
- [ ] Check handoffs on saved data, then provide the user-run operational chain. Swapping
  an upstream producer must change downstream input references and delivered context as
  appropriate; stochastic output equality or difference is not an acceptance assertion.
- [ ] Interrupt/resume the chain and retain completed observations deliberately. Failed
  or missing upstream outputs cannot silently become empty evidence. Trace a final finding
  to the actual newly executed producer outputs and context.
- [ ] Make the selected active experiment adopt this route and remove its replaced private
  launch/tool/result-reading mechanics in the same series.

**Done when:** one new chain is operational on the supported paths, its interventions and
results are inspectable through shared reports, and changing a producer does not require
new transport, retry, storage or matching code. Report resource use including required
acquisition and failed attempts. Record study conclusions in the existing questions/todo/
dead-ends registers as warranted; do not create another research-results index.

## 10. Parallel research and deferred architecture

Research can advance independently of the foundation work. Continue the existing
[scope/conflict/maturity studies](../todo/conventions-nature.md) and the
[library-mechanism grounds question](../../.claude/worktrees/review-reconstruction/docs/todo/review-library-mechanism-over-local-precedent.md).
Keep convention synthesis and independent application/comparison separately replaceable.
Use dated supporting and contrary evidence; name eligible opportunities before making
prevalence claims. A supplied convention's success is not autonomous discovery.

The smallest optional new product is a comparison of alternatives: subject and alternatives,
requirements with provenance, supporting/contrary sources, exact checks, tradeoffs and a
justified or unresolved conclusion. Start with existing source/patch references and plain
renderings. Add a type when an actual consumer needs the structure; no document-wide AST
is required.

Development examples include 33117 (`to_fun`, prerequisites and sum/prod client-interface
costs), 33066 (redundant constructor versus useful API), 43167 (competing naming analogues)
and 32875 (proof form/automation registration). These are heavily inspected development
fixtures, not fresh tests. Preserve real tradeoffs rather than requiring historical compliance.

Select one contrast at a time: fixed facts versus facts plus census-stated grounds;
sources versus an explicit comparison over the same sources; structured comparison versus
the same content in ordinary text; eventually autonomous assistance versus contemporaneous
solo/comparable additional review on fresh cases. Do not repeat the already-run supplied-
source campaign under a new name. Use the saved Phase A, step 4 and amendment 7 readings
as evidence, with their limits, and state what a new contrast isolates.

| Deferred feature | Reopen when |
|---|---|
| Universal review AST or annotated document | Useful operations repeatedly need structural relations current spans/attachments/change graph cannot express clearly; show information loss or duplicated maintenance |
| New experiment/DAG/pass framework or artifact store | Two active consumers demonstrate a gap in existing APE composition/storage; ordinary recipes remain the default |
| Broad sealing or historical hash migration | A concrete supported caller remains obstructed after separating identity, continuation and optional study commitment |
| Standalone external MCP startup command | An independently launched client is selected for an actual portability test; reuse shared operations and definitions |
| Persistent Lean server or new verification backend | Profiling identifies a real bottleneck; preserve operation semantics |
| Learned selection or compulsory convention enforcement | Independent labels and an appropriate held-out test support the mechanism |
| Matcher calibration or full historical replay | A specific comparison needs continuity with historical measurements or faithful re-execution |
| Exhaustive model/scaffold matrix | A research question or configuration-specific defect requires it |

The [follow-up concepts](../research/task-dataflow-followup-concepts-2026-10-22.md#0-why-would-this-improve-reviewing)
and [systems reading](../research/review-refactor-systems-reading-2026-10-22.md) explain the
conditional research case. They do not enlarge this handoff's implementation scope.

## 11. Code owners and verification

Prefer existing owners over a parallel package layout. Generic framework capabilities
stay in `src/ape/`; review-domain bindings remain explicit. New Tasks belong under the
existing eagerly imported Task tree to avoid introducing import cycles.

| Work | Starting points |
|---|---|
| Context/standalone tools | `src/mathlib_review/review/toolbox.py`; `src/ape/tasks/lean_tasks/formal_math/review/context_tools.py`; review `base.py` in that directory |
| Resources and verification | `src/mathlib_review/agenda/cutoffs.py`; `src/mathlib_review/evidence/evidence.py`; `src/ape/tasks/lean_tasks/formal_math/pr_review/core.py`; `src/ape/toolkits/execute/lean/tools.py`; `src/ape/toolkits/mcp_manager.py` |
| Session execution and handoffs | `src/ape/tasks/packet_session.py`; `src/mathlib_review/analysis/sessions.py`; `src/mathlib_review/schema/runs.py`; `src/mathlib_review/review/inputs.py` |
| Recipe and existing execution | `src/mathlib_review/review/runner.py`; `pipeline.py`, `stage_adapters.py` and `cli.py` in the same directory |
| Assessment and common evaluation | `src/mathlib_review/judge/adjudicate.py`; `src/mathlib_review/schema/scoring.py`; `analysis/matching.py`, `analysis/trace.py`, `judge/ask_matching.py` and `judge/protocol.py` under `src/mathlib_review/` |

Run relevant existing checks as each boundary changes; add regressions for real failure
modes rather than tests that mirror delegation. The focused working set is:

```bash
TMPDIR=/dev/shm PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest -q \
  tests/datasets/test_context_tool_grants_survive.py \
  tests/datasets/test_pr_review_v5_context_tools.py \
  tests/datasets/test_pr_review_v5_toolbox.py \
  tests/mathlib_review/test_adjudication.py \
  tests/mathlib_review/test_sessions.py \
  tests/mathlib_review/test_run_inputs.py \
  tests/mathlib_review/test_compare.py \
  tests/ape/test_task_config_resolution.py \
  tests/orchestration/test_recovery_and_identity.py
```

At the integrated checkpoint, run the normal suite and frozen verification:

```bash
TMPDIR=/dev/shm PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest tests -q -n auto --dist loadfile
PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m src.mathlib_review.release.verify_frozen verify
```

Report environment-dependent skips or missing prebuilt workspaces explicitly. Shell Lean
checks use the project's `ELAN_HOME=/research/projects/proofedit/ya475/.elan`. Deterministic
parity tests establish the extraction; stochastic runs establish operational support;
controlled experiments and balanced assessment establish reviewing benefit. Keep those
claims separate in the implementation handoff and closing record.
