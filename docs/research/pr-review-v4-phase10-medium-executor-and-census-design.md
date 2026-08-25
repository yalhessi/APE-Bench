# PR Review v4: Phase 10 medium opportunity executor and coverage census

*Status: v0.3 implementation in progress*
*Created: 2026-07-18*
*Parent design: `pr-review-v4-systematic-opportunity-pipeline-design.md`*
*Benchmark: `inputs/pr_review_v4/releases/dev-medium-0.1.0`*

## 1. Decision

Phase 10 should use the medium benchmark, but the paid medium experiment must wait until three gates
are satisfied:

1. a static C0-C2 reachability census shows that the frozen treatment can reach enough
   non-motivating medium obligations to make a paid run informative;
2. a generic opportunity executor runs every scheduled investigation to an explicit terminal state
   without PR- or declaration-specific dispatch; and
3. the C0-C6 census evaluator is validated and produces a complete report on the authorized paid
   smoke, distinguishing conceptual coverage, operator capability, discovery, construction, and
   semantic recovery.

The static census is the first published implementation increment. C0-C2 require only frozen method
contracts, the medium schedule, and deterministic capability predicates; they do not require an
executor or model calls. If the current arm fails the reachability gate, its paid smoke and
three-repetition medium run are skipped. The treatment-independent executor, replay, and dry-run
machinery should still be built for a later arm with adequate static reach.

This phase is an implementation and measurement correction, not an authorization to add methods
suggested by medium misses. Methods, implementation capabilities, policies, and thresholds are frozen
before the static census. Static or dynamic miss analysis may motivate a later treatment version, but
that version receives new registry hashes and a new pre-registration. Because such a version is
medium-adapted, its generalization claim requires confirmation on the temporal holdout.

## 2. Why the medium tier is appropriate

The medium release contains:

- 16 PRs: 13 intervention cases and three controls;
- 225 holistic work units;
- 33 judgments and 43 obligations, of which 40 are currently included for evaluation;
- all nine earlier pilot PRs plus seven additions covering correctness, scope, naming, documentation,
  duplication, proof-golf, dropped requests, relational judgments, and large-PR stress;
- 14 distinct base snapshots, all currently prebuilt.

It is substantially less dominated by PR 33098 than the nine-PR pilot and contains non-motivating
cases for the implemented methods. It remains development-contaminated and does not replace the
temporal holdout.

Running `configs/pr_review_v4_medium.yaml` directly is not Phase 10. That configuration invokes the
holistic reviewer over all 225 work units. Three repetitions would require 675 generator calls before
semantic judging and would not execute the systematic opportunity treatment.

## 3. Current implementation gap

The Phase 2 registry uses broad method identities:

- `baseline_failure.v1`;
- `canonical_api_search.v1`;
- `naming_contrast.v1`;
- `wrapper_composition.v1`.

The executable implementations are narrower:

| Method | Current implementation capability |
| --- | --- |
| `canonical_api_search.v1` | Retrieves broadly, but constructs an edit only for the inserted-set `IsSeparated` pattern |
| `naming_contrast.v1` | Classifies only direct-left-hand-side `Set.encard` conclusions and proposes `card_` to `encard_` |
| `wrapper_composition.v1` | Constructs only the `coveringNumber` / `packingNumber` / `maximalSeparatedSet` wrapper chain |
| `baseline_failure.v1` | Has reusable deterministic checks, but no medium-wide executor record path |

The broad method IDs are useful conceptual categories and should remain stable. The narrow executable
capabilities need their own identities. Otherwise a scheduled task can be mistaken for a task the
current implementation could genuinely investigate.

This mismatch is already visible in the non-motivating cases. The current naming implementation
cannot express the `toLinearMap_` or dot-notation renames in PRs 33337 and 33294; the canonical API
edit constructor is not a general duality or reuse operator for PR 33145; and the wrapper operator is
not a proof-golf operator for PR 33285. A static census may therefore find only a handful of supported
included obligations, concentrated in PR 33098. That is a hypothesis to measure, not a result to
assume.

Phase 9 also composes three target-specific smoke releases and hard-codes PR 33098 evaluation scope.
It is a valid regression fixture, not a medium execution engine.

## 4. Design principles

1. **Gold-free execution.** Inventory, scheduling, capability assessment, discovery, adjudication,
   and synthesis never read judgments, intervention views, maintainer comments, or outcomes.
2. **One terminal state per task.** Every scheduled investigation records success, bounded negative
   completion, unsupported capability, missing input, or execution failure.
3. **Methods are not implementations.** Method applicability describes a research strategy;
   implementation capability describes the exact shapes the current code can execute.
4. **No-op is evidence.** A completed search with no opportunity is retained and distinguished from
   an unsupported shape or failed search.
5. **Deterministic work is reused.** Inventory, relations, indexes, retrieval, capability checks, and
   deterministic opportunities run once. Only model adjudication or transformation stages repeat.
6. **Coverage is a ladder.** Location overlap is not issue recovery, and issue recovery is not
   resolution recovery.
7. **Medium misses cannot tune the current arm.** Any new capability motivated by medium results
   creates a new registry/treatment version and a new pre-registration.
8. **Per-PR reporting is mandatory.** Pooled metrics cannot hide domination by PR 33098.
9. **Reachability rejection is asymmetric.** Low C2 coverage can reject a paid arm, but high C2
   coverage only authorizes testing; it does not establish discovery or semantic recovery.

## 5. Artifact model

### 5.1 Implementation capability registry

Add a frozen registry that maps a broad method to one or more executable implementations:

```json
{
  "implementation_id": "canonical_api.insert_separation.v1",
  "method_id": "canonical_api_search.v1",
  "operator_version": "canonical-api-lexical-shape/1",
  "capability_predicate": "inserted_set_separation_shape.v1",
  "required_inputs": ["reviewed_declaration", "repository_declaration_index"],
  "terminal_outputs": ["opportunity", "checked_no_opportunity", "unsupported_shape"],
  "max_opportunities": 1
}
```

Initial implementation identities should make their existing scope explicit:

- `baseline_failure.target_compile.v1`;
- `canonical_api.insert_separation.v1`;
- `naming_contrast.encard_subject_prefix.v1`;
- `wrapper_composition.packing_cover_chain.v1`.

The implementation registry is frozen independently from the method registry. Adding a generalized
implementation later does not rewrite the meaning of prior runs.

### 5.2 Capability assessment

Every scheduled `(investigation, implementation)` pair produces one assessment:

```text
implementation_id
investigation_id
method_id
primary_change_id
status
reason_code
required_input_status
evidence_artifact_ids
source_sha256
```

Allowed statuses:

| Status | Meaning |
| --- | --- |
| `supported` | The implementation can execute on this target shape |
| `unsupported_shape` | The method is scheduled, but this implementation does not handle the shape |
| `missing_input` | A required review-time artifact is unavailable |
| `not_applicable` | A stricter implementation predicate rejects the task |
| `failed` | Capability assessment malfunctioned |

`unsupported_shape` and `not_applicable` are deterministic negative outcomes. They are not executor
failures and cannot be silently dropped.

### 5.3 Terminal investigation record

The existing `InvestigationRecord` remains the investigation-level terminal artifact. It should be
extended or accompanied by a phase-level ledger that records:

```text
scheduled
capability_assessed
operator_completed
source_discovered
transformation_constructed
technical_check_completed
worthiness_decided
candidate_emitted
finding_selected
terminal_stage
terminal_reason
```

This ledger is produced for every scheduled task, including methods with no opportunities.

## 6. Method-coverage census

### 6.1 Two physically separate views

The census has two layers:

1. **Generation-side capability census:** gold-free inventory, scheduled tasks, implementation
   capability assessments, operator outcomes, and opportunities. This may be stored with the
   treatment or run.
2. **Evaluation-side obligation census:** joins frozen generation artifacts to included obligations.
   This lives under `results/pr_review_v4/audits/` and must never be copied into prompts or execution
   releases.

The generation-side report also includes workload exposure by PR, method, implementation, and
control/intervention role. This reports how often capabilities accept changed code even when no gold
obligation exists, making potential false-positive pressure visible without using gold.

### 6.2 Two publication stages

The obligation census is published in two stages:

1. **Static reachability report (C0-C2):** produced immediately after contracts, scheduling, and
   capability predicates are frozen. Its primary denominator is the 40 included obligations. The
   three excluded obligations are reported separately and cannot authorize a paid run.
2. **Execution effectiveness report (C0-C6):** produced after executor output and semantic judging
   exist. It preserves the frozen C0-C2 assignments and adds source, construction, issue, and
   resolution outcomes.

This split prevents executor completion from being mistaken for treatment reach. It also gives the
current arm an explicit off-ramp before any medium model calls.

### 6.3 Coverage ladder

Each included obligation receives the following independently reported levels:

| Level | Name | Required evidence |
| --- | --- | --- |
| C0 | location scheduled | An investigation overlaps an obligation change ID |
| C1 | method expressible | A pre-frozen method contract covers both the obligation's issue class and its requested-transformation class |
| C2 | implementation supported | At least one implementation capability accepts the target shape |
| C3 | source discovered | Required repository, PR-relation, diagnostic, or norm source is found |
| C4 | transformation constructed | A concrete requested transformation is produced |
| C5 | issue recovered | A candidate semantically matches the maintainer issue |
| C6 | resolution recovered | The candidate action matches an acceptable resolution |

Levels are monotone for each method path but are not inferred from target overlap. In particular, C0
does not imply C1, and a successful compile at C4 does not imply C5 or review-worthiness.

### 6.4 Frozen method-expression contracts

C1 needs a versioned, target-independent mapping from methods to issue and transformation classes.
For example:

```text
canonical_api_search.v1:
  issue_classes = [duplicate_implementation, missed_canonical_api]
  transformation_classes = [replace_with_repository_declaration]
```

The contract is frozen before looking at medium execution results. Evaluation may compare an
obligation's gold concern and requested-change class with the contract, but it may not add a mapping
because one would rescue a miss.

C1 is offline but not automatically objective. Medium obligations currently contain concern labels
and requested-change prose rather than a complete normalized method-class annotation. C1 assignments
therefore follow a frozen annotation protocol and receive one human audit before publication.
Ambiguous mappings remain `manual_audit_required` and do not count as C1 or C2 support for the static
reachability gate.

The implemented protocol is `obligation-expression-class/2` (`method_coverage_census.py`): two
independent frozen classifiers annotate each obligation — an issue-class rule over concern labels
and claim prose, and a requested-transformation rule over action kind and claim prose. C1 holds only
when one contract covers the resulting (issue class, transformation class) pair; if either
classifier abstains, the obligation is `manual_audit_required`. The conjunctive rule is deliberate:
a request for a shorter proof must not count as expressible by an API-replacement method merely
because both are proof-related. The human audit adjudicates abstentions; audited assignments are
then frozen, and the report carries `annotation_audit_status` until that pass completes.

### 6.5 Miss taxonomy

Every unrecovered obligation receives the earliest failed stage:

- `no_location_task`;
- `method_contract_gap`;
- `implementation_shape_gap`;
- `required_input_gap`;
- `source_retrieval_gap`;
- `transformation_construction_gap`;
- `technical_validation_gap`;
- `norm_or_worthiness_gap`;
- `candidate_semantics_gap`;
- `synthesis_or_selection_gap`;
- `semantic_judge_unstable`.

Ambiguous cases remain `manual_audit_required`; they are not forced into the most favorable stage.

### 6.6 Census reports

The static report must include:

- C0-C2 counts over the 40 included obligations, with the three excluded obligations separate;
- C2-supported obligations outside PR 33098, grouped by PR and implementation ID;
- the C2/C1 ratio outside PR 33098;
- generation-side supported-task exposure over every PR, including controls;
- a row-level explanation for every C0, C1, and C2 assignment;
- a manual-audit queue for uncertain C1 mappings.

The completed report must additionally include:

- C0-C6 counts and rates, pooled and macro-averaged by PR;
- coverage by method, implementation, concern family, and information requirement;
- counts of unsupported shapes versus completed no-op searches;
- earliest miss stage for every obligation;
- method and implementation overlap per obligation;
- controls and unpaired opportunities, reported separately;
- a manual-audit queue for semantic-judge disagreements.

## 7. Generic opportunity executor

### 7.1 Execution interface

Introduce an executor registry with a narrow common interface:

```text
method_id
  -> matching implementation capabilities
  -> capability assessment
  -> bounded operator execution
  -> evidence artifacts
  -> zero or more opportunities
  -> exactly one terminal investigation record
```

No dispatcher may contain PR numbers, obligation IDs, or declaration-name allowlists. Shape-specific
logic belongs in a versioned implementation capability and must return `unsupported_shape` when it
does not apply.

### 7.2 Execution order

For each scheduled task:

1. load its modification, target, episode, work unit, and validated PR relations;
2. resolve implementations registered for the task's method;
3. run and persist every capability assessment;
4. execute only supported implementations;
5. reuse snapshot/module indexes through a content-addressed cache;
6. persist every operator run and evidence artifact;
7. enforce implementation and method opportunity limits;
8. produce exactly one investigation terminal record;
9. continue after task-local failures while retaining them in the run-level failure gate.

### 7.3 Terminal dispositions

The executor must distinguish:

- `opportunities`;
- `checked_no_opportunity`;
- `unsupported_by_current_implementations`;
- `missing_required_input`;
- `failed`.

An investigation with multiple implementations reports `opportunities` if any implementation emits
one, but its ledger retains every implementation's result.

### 7.4 Shared indexes and economics

Expensive deterministic inputs are cached by immutable identity:

- repository declaration index: `(base_sha, target module, index version)`;
- naming population: `(base_sha, population version)`;
- PR relation graph: `(change_graph_sha256, relation version)`;
- compile baseline: `(base_sha, reviewed file hash, check version)`.

The executor report includes cache hit rates, wall time, task counts, and opportunity yield. A medium
run must not rescan the complete repository once per naming task.

## 8. Integrated execution release

Build a new immutable release after deterministic execution, tentatively:

```text
inputs/pr_review_v4/releases/dev-medium-0.2.0-systematic/
  manifest.json
  methods.jsonl
  implementations.jsonl
  input/episodes.jsonl
  derived/change_graphs.jsonl
  derived/work_units.jsonl
  derived/rendered_prompts.jsonl
  derived/investigation_tasks.jsonl
  derived/capability_assessments.jsonl
  derived/operator_runs.jsonl
  derived/investigation_records.jsonl
  derived/opportunities.jsonl
  derived/opportunity_evidence.jsonl
  derived/deterministic_candidates.jsonl
  derived/pipeline_ledger.jsonl
```

Only opportunities requiring model adjudication receive model work units. Deterministic requests and
no-request outcomes do not consume model calls. Gold and evaluation census artifacts are prohibited.

## 9. Validation strategy

### 9.1 Unit and contract tests

Add synthetic fixtures that establish:

- each implementation accepts its supported shape and rejects a nearby unsupported shape;
- no implementation dispatch depends on a PR number or obligation ID;
- every scheduled task obtains one terminal record;
- no-op, unsupported, missing-input, and failed outcomes remain distinct;
- method and implementation opportunity limits are enforced;
- cache identities change when snapshot or operator versions change;
- gold poisoning cannot change any generation artifact;
- census levels and earliest-failure attribution are correct on synthetic ladders.

### 9.2 Static medium reachability gate

After Steps 1-3, produce and publish the C0-C2 census before building or running the current arm on
medium. This report is deterministic and uses no model calls. Verify that:

- all 40 included obligations have explicit C0-C2 rows;
- the three excluded obligations are visible but absent from the decision denominator;
- all C1 assignments come from the frozen contract and audited annotation protocol;
- all C2 assignments are produced mechanically by frozen capability predicates;
- per-PR and per-implementation support counts reconcile with the row-level ledger;
- the generation-side exposure table covers all 16 PRs and labels controls without special dispatch;
- rerunning the census produces byte-identical artifacts.

Apply the reachability decision in Section 11. A failed current arm does not block generic executor
implementation, Phase 9 replay, or deterministic medium dry runs. It blocks only medium model calls
for that arm.

### 9.3 Phase 9 replay gate

Before medium execution, the generic executor must reproduce the Phase 9 fixture:

- the same six opportunities;
- the same four deterministic terminal routes;
- the same two model-adjudication routes;
- the same three accepted opportunity IDs after adjudication;
- zero selected control findings;
- byte-identical deterministic artifacts across two builds.

This is a compatibility gate, not evidence that the implementations generalize.

### 9.4 Medium deterministic dry run

Run inventory, scheduling, capability assessment, and operators over all 16 PRs without model calls.
Inspect before authorizing paid work for an arm that passed the static reachability gate:

- scheduled and terminal task counts match exactly;
- execution failures are zero or individually explained;
- unsupported-shape counts are plausible and visible;
- opportunity counts respect bounds;
- indexes are reused;
- controls do not receive special dispatch;
- no generation artifact contains gold text or IDs.

### 9.5 Small paid smoke

Use PRs 33098, 33145, 33337, and 33438:

- PR 33098 checks motivating-case replay;
- PR 33145 checks relational/sibling behavior;
- PR 33337 checks non-motivating naming transfer;
- PR 33438 checks control pressure.

The smoke is run only for an arm that passed the static reachability gate. It passes only if all model
calls terminate, candidates preserve opportunity and verification lineage, no control finding is
selected, and semantic judging produces a complete report. Failure is attributed to executor,
capability, retrieval, construction, adjudication, or evaluation before any prompt or operator
changes are considered.

## 10. Medium experiment contract

After the static reachability, deterministic, and paid smoke gates pass:

1. freeze release, registry hashes, implementation hashes, prompts, policies, thresholds, semantic
   rubric, and comparator;
2. run deterministic discovery once over all 16 PRs;
3. run exactly three repetitions of stochastic adjudication/transformation work;
4. evaluate every repetition separately before aggregation;
5. report pooled and macro-per-PR metrics;
6. report per-obligation hit frequencies and semantic-judge disagreement;
7. report actual calls, tokens, dollar cost, and cost per recovered obligation;
8. preserve medium misses for a later treatment version rather than repairing the current arm.

The holistic comparator must be specified before the paid run. A 675-call full three-repetition
baseline is available but expensive. A cheaper comparator is acceptable only if its unit-selection
rule and call budget are frozen in advance and it is labeled call-matched rather than equivalent to
complete holistic review.

## 11. Phase 10 decision gates

### Static reachability gate

The current arm is authorized for a paid medium smoke only if its C0-C2 census contains:

- at least three C2-supported included obligations outside PR 33098;
- support across at least two PRs other than PR 33098; and
- support from at least two distinct implementation IDs outside PR 33098.

The report must also publish C2/C1 outside PR 33098, but this ratio is diagnostic rather than a hard
threshold until the C1 annotation audit establishes that its denominator is stable. The three hard
conditions are necessary consequences of the expansion claim: an arm cannot demonstrate gains across
new PRs and multiple implementations when its own capability predicates say those gains are
impossible.

If any condition fails:

1. publish the current arm as `static_reachability_rejected`;
2. skip its four-PR paid smoke and three-repetition medium run;
3. continue building the generic executor, replay gate, cache, and dry-run machinery;
4. define generalized capabilities under new implementation and treatment versions; and
5. rerun and freeze a new static census before pre-registering the replacement paid arm.

A replacement informed by this census is medium-adapted. Medium results for it are developmental;
temporal-holdout confirmation is required before claiming generalization.

### Implementation gate

- 100% scheduled-task terminal coverage;
- no unexplained execution failures;
- deterministic replay hashes stable;
- complete evidence and opportunity lineage;
- Phase 9 replay preserved;
- no gold access during generation.

### Expansion gate

- issue gains occur outside PR 33098;
- gains occur through more than one implementation or method;
- method-level paired-candidate precision remains acceptable;
- zero or pre-registered bounded selected-control pressure;
- cost per recovered obligation improves against the frozen comparator;
- the result survives macro-per-PR reporting;
- miss attribution shows whether the next bottleneck is method coverage, implementation breadth,
  retrieval, construction, worthiness, or synthesis.

Failure to improve recall does not by itself invalidate the executor. It can still establish that the
registered implementations are too narrow. It does invalidate claims that the current systematic
treatment generalizes beyond its motivating cases.

## 12. Implementation sequence

| Step | Deliverable | Validation gate | Status |
| --- | --- | --- | --- |
| 1 | Frozen method-expression contracts and implementation registry schema | Registry hashes and no target-specific entries | DONE 2026-07-18 (`implementation_registry.py`; `systematic-opportunities-v1-medium/{implementations,method_expression_contracts}.jsonl`) |
| 2 | Medium Phase 2 inventory, relations, and schedule treatment | Complete modification-method schedule | DONE 2026-07-18 (`phase10_medium.py`; pilot 33098 smoke-schedule audit: pass) |
| 3 | Capability assessment schemas and predicates | Positive and nearby-negative fixtures per implementation | DONE 2026-07-18 (`capability_assessments.jsonl`; fixtures in `test_pr_review_v4_implementation_registry.py`) |
| 4 | Static C0-C2 medium census and reachability decision | Published row-level report; off-ramp applied | DONE 2026-07-18 — **static_reachability_rejected**: C1v2 requires both issue and transformation class; included 40 obligations, C0 40/40, C1 15/40, C2 5/40 all in PR 33098; outside dev PR C2 = 0/26 (report: `results/pr_review_v4/audits/phase10-medium-static-census-c1v2/`; C1 human audit pending over 40-row queue) |
| 5 | Generic executor and terminal ledger | Every synthetic and smoke task terminates exactly once | DONE 2026-07-18 (`opportunity_executor.py`; synthetic terminal and cap tests plus one live smoke per initial implementation) |
| 6 | Shared deterministic index cache | Stable identities and demonstrated reuse | Partial: in-process reuse for compile, declaration-index, and naming-population work; persistent content-addressed cache remains TODO |
| 7 | Phase 9 executor replay adapter | Exact deterministic artifact replay | TODO |
| 8 | Integrated medium execution release builder | Gold-free validation and sealed dry run | TODO |
| 9 | Dynamic C3-C6 census evaluator | Synthetic ladder and earliest-miss fixture tests | TODO |
| 10 | Four-PR paid smoke for the authorized arm | Execution, control, lineage, and semantic gates pass | TODO |
| 11 | Medium pre-registration and three repetitions | Frozen comparison and complete reports | TODO |
| 12 | Temporal-holdout decision | No medium-driven rule changes in holdout arm | TODO |

The first implementation increment completes Steps 1 through 4 and publishes the static census. It
uses no paid models. If the current arm is rejected, Steps 5 through 9 continue because they are
treatment-version-independent, while Step 10 waits for a replacement arm whose frozen census passes.

## 13. Proposed modules

```text
src/datasets/pr_review_v4/
  implementation_registry.py
  opportunity_executor.py
  method_coverage_census.py
  phase10_medium.py

tests/datasets/
  test_pr_review_v4_implementation_registry.py
  test_pr_review_v4_opportunity_executor.py
  test_pr_review_v4_method_coverage_census.py
  test_pr_review_v4_phase10_medium.py
```

Existing operator modules remain the implementation bodies. Their current shape-specific functions
are wrapped by explicit capability predicates rather than copied into another pipeline.

## 14. Open decisions

1. Whether capability assessments extend `InvestigationRecord` or remain a separate immutable
   artifact referenced by the pipeline ledger.
2. Whether the first medium comparison uses a complete holistic arm, a call-matched stratified arm,
   or both.
3. Whether the residual PR-level pass belongs in the first systematic medium arm or is evaluated as
   a separate additive treatment.
4. What precision and selected-control thresholds authorize temporal-holdout execution.
5. The exact normalized annotation vocabulary used by the required C1 human audit.

These decisions must be resolved in the pre-registration. They must not be selected after observing
which choice produces the strongest medium result.
