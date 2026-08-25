# PR Review v4: Inventory-driven investigation agenda

*Status: v0.1 design draft for iteration. Created 2026-07-17.*
*Scope: experimental reviewing treatment over the `0.9.0` stable core.*
*Companion: `pr-review-v4-coverage-ledger-spec.md`.*

## 1. Purpose

The current reviewer sees complete semantic change targets and is instructed to consider every
concern family, but its issue coverage is not reliable. Across three repetitions of the stable
three-work-unit smoke, issue recall was 3/6, 2/6, and 1/6. The union reached 4/6, but no obligation
was recovered in every repetition. This indicates that some investigations are within the model's
capability but are not consistently attempted.

Earlier inventory proposals focused on enumerating every changed location. That was not sufficient:
the v2 miss decomposition found that 81% of gold findings already had some prediction at the right
location, while the dominant residual was a different concern at that location. The useful role of
an inventory is therefore not to produce more locations or predict findings directly. Its role is
to schedule the right investigations.

This design separates four objects:

```text
ChangeGraph
    -> ModificationInventory      what changed
    -> InvestigationAgenda        what must be checked
    -> InvestigationRecord        what was inspected and concluded
    -> Candidate/Evidence/Finding existing v4 publication path
```

The modification inventory is the scheduler frontend. The investigation ledger is the accounting
backend. Neither object is itself a review finding.

## 2. Goals

1. Convert review coverage from a prompt instruction into a deterministic schedule.
2. Prevent an easy issue in one family from substituting for required investigations in another.
3. Match investigation methods to the semantic kind and component of the modification.
4. Distinguish checked absence, insufficient context, budget deferral, and skipped work.
5. Give repository-norm discovery a typed query and a precise insertion point.
6. Permit local investigations to expand to related targets without treating physical work units as
   semantic boundaries.
7. Preserve exact run accounting, review-time isolation, and the existing evidence gate.
8. Measure whether gains come from additional inference budget, specialist attention, scheduling,
   or norm information.

## 3. Non-goals

The first treatment does not attempt to:

- infer every concern a human could possibly raise;
- encode maintainer preference as a deterministic rule;
- build the final repository-norm retriever;
- solve sibling propagation or PR-level finding synthesis completely;
- change stable v4 episodes, change targets, judgments, or evaluation views;
- use gold comments, obligations, outcomes, or post-review revisions during generation.

One residual open-ended pass remains necessary because no finite template registry is exhaustive.

## 4. Design principles

### 4.1 Modification types schedule questions, not answers

An added theorem should trigger naming, API, statement, and proof investigations. It must not imply
that any of those investigations will produce a finding.

### 4.2 Classification is multi-dimensional

Exclusive labels such as `added_lemma` and `modified_proof` are too brittle. An added theorem has an
added statement, proof, attributes, and possibly documentation. One modification therefore carries
multiple facets.

### 4.3 Concern families are output metadata

The existing concern taxonomy remains useful for reporting and routing evidence. It is not the
primary scheduling ontology. A declaration-name investigation may legitimately emit a candidate
labeled `naming` even when a migrated gold judgment was historically labeled `style`.

### 4.4 Physical context chunks are not judgment scope

Work units remain bounded prompt-loading units. Agenda items and candidates may refer to any target
in the same review episode, provided every relation is validated against the change graph and its
discovery is recorded.

### 4.5 Automated checks are observations

A passing compile check proves only that the checked file or target produced no compiler diagnostic.
It does not close semantic correctness. A passing linter does not close style review. Automated
results are attached to investigations but never silently produce `checked_no_request` for an entire
concern family.

### 4.6 Unknown is preferable to fabricated precision

Every classifier and investigation may return an explicit unknown or inconclusive state. Unknown
classification activates conservative fallback templates and remains visible in audits.

## 5. Modification inventory

### 5.1 Inventory unit

The canonical inventory unit is one primary semantic change target plus a component delta. Structural
targets that overlap the same changed range are retained as context, but they do not create duplicate
inventory items unless they represent a separately reviewable operation such as an import or module
documentation edit.

```jsonc
{
  "schema_version": "modification-inventory1",
  "modification_id": "modification:<hash>",
  "episode_id": "leanprover-community/mathlib4:33098:round1:<sha>",
  "pr_number": 33098,
  "primary_change_id": "change:...",
  "context_change_ids": ["change:..."],
  "subject_kind": "theorem",
  "lifecycle": "modified",
  "visibility": "public",
  "component_deltas": [
    {
      "component": "proof",
      "status": "modified",
      "base_sha256": "...",
      "reviewed_sha256": "...",
      "classifier": "lean-component-diff/1"
    }
  ],
  "relation_flags": ["member_of_changed_declaration_family"],
  "classification_status": "complete",
  "unknown_reasons": [],
  "source_sha256": "..."
}
```

### 5.2 Normalized subject kinds

Initial kinds are:

- `theorem`
- `definition`
- `instance`
- `structure_or_class`
- `inductive`
- `abbreviation`
- `command`
- `import`
- `module_doc`
- `namespace_or_section`
- `non_lean`
- `unknown`

Lean `lemma`, `theorem`, and `axiom` declarations may retain their parser kind as metadata while
sharing the normalized theorem investigation templates.

### 5.3 Lifecycle facets

- `added`
- `removed`
- `modified`
- `renamed`
- `moved`
- `unchanged_context`
- `unknown`

Rename and move detection must be conservative. An unmatched deletion/addition pair is not declared
a rename solely because its code is similar.

### 5.4 Component facets

- `name`
- `binders`
- `statement_or_type`
- `attributes`
- `proof`
- `value_or_body`
- `documentation`
- `namespace`
- `imports`
- `layout`
- `unknown`

Each component has `added`, `removed`, `modified`, `unchanged`, or `unknown` status. The inventory
stores component hashes so unchanged statements and proof-only edits are mechanically verifiable.

### 5.5 Relation hints

Relation hints are generation-safe hypotheses derived from the current PR and repository state:

- `same_name_family`
- `same_type_shape`
- `changed_siblings`
- `generated_counterpart`
- `repeated_implementation_shape`
- `import_dependency`
- `declaration_dependency`
- `possible_replacement_pair`

Hints do not assert that a review problem exists. They schedule relational investigations.

### 5.6 Determinism and provenance

Inventory generation must be a pure function of:

- the hashed stable release manifest;
- episode inputs;
- change graphs;
- review-time repository snapshots;
- versioned parser and classifier code.

Gold poisoning must leave inventory bytes unchanged. Every unknown parse or pairing decision is
recorded rather than guessed.

## 6. Component differencing

The existing change graph already provides target kind, parser declaration kind, complete base and
reviewed code, and base/reviewed entity IDs. It can immediately classify coarse subject and lifecycle
facets. It does not yet robustly distinguish a proof-only edit from a statement or binder edit.

The component differencer should:

1. Parse base and reviewed declarations with a Lean-aware structured parser.
2. Normalize source spans for declaration name, binders, type/statement, attributes, proof or value,
   and attached documentation.
3. Hash components without normalizing away semantically relevant syntax.
4. Emit `unknown` when parsing or pairing is ambiguous.
5. Never use ad hoc delimiter splitting as the authoritative classifier.

The first implementation may support theorem, definition, and instance declarations and fall back to
coarse templates for other kinds. Parser expansion is driven by explicit unknown counts.

## 7. Investigation templates

### 7.1 Template schema

Templates are versioned structured data, not prompt prose embedded in code.

```jsonc
{
  "schema_version": "investigation-template1",
  "template_id": "theorem.proof.canonicalization.v1",
  "investigation_kind": "proof_canonicalization",
  "applies_when": {
    "subject_kinds": ["theorem"],
    "lifecycles": ["added", "modified"],
    "any_changed_components": ["proof"]
  },
  "question": "Can this proof be replaced by a canonical lemma, tactic, or shorter proof structure?",
  "concern_family_hints": ["proof-golf", "style"],
  "required_methods": ["local_read"],
  "optional_methods": ["repository_search", "lean_check"],
  "scope_strategy": "primary_then_siblings",
  "priority": "standard",
  "template_version": "1"
}
```

Applicability predicates use explicit fields and set membership. The initial implementation does not
introduce a general expression language.

### 7.2 Initial template library

The initial library should remain small enough to audit. Suggested templates are:

| Template | Trigger | Investigation |
|---|---|---|
| `theorem.statement.semantic` | added/changed theorem statement | Check that the statement expresses the intended result and has appropriate assumptions and conclusion |
| `theorem.statement.generality` | added/changed theorem statement | Test whether hypotheses or types can be generalized without weakening the intended result |
| `theorem.api.duplication` | added theorem | Search for an existing theorem or abstraction with the same role |
| `declaration.naming` | added/renamed public declaration | Compare the name and namespace with type, siblings, and repository conventions |
| `declaration.documentation` | added/changed public declaration | Check documentation presence and accuracy against the declaration |
| `theorem.proof.canonicalization` | added/changed proof | Search for canonical lemmas, tactics, and direct proof structure |
| `theorem.proof.robustness` | added/changed proof | Check compilation, fragile elaboration dependencies, and unnecessary implementation detail |
| `definition.api.shape` | added/changed definition | Check abstraction boundary, constructor/interface choice, and existing APIs |
| `definition.semantic_compatibility` | changed definition | Check behavior change, callers, and compatibility expectations |
| `instance.coherence` | added/changed instance | Check overlap, inference loops, priority, and existing instances |
| `import.layering` | added/changed imports | Check necessity, layering, and accidental transitive dependencies |
| `removal.compatibility` | removed public declaration | Check remaining uses and replacement or migration path |
| `family.consistency` | changed sibling relation | Compare naming, statement shape, attributes, proof treatment, and missing counterparts |
| `repetition.shared_abstraction` | repeated implementation hint | Determine whether repeated code should use a shared abstraction |
| `structural.layout` | command/doc/namespace/layout edits | Check repository structural and formatting conventions |

Compilation and registered linters run as check providers. They are not templates that close all
correctness or style investigations.

### 7.3 Conservative fallback

Unknown or unsupported inventory items receive:

- a local semantic review investigation;
- a repository-analogue search investigation for public code;
- the residual open-ended review pass.

No inventory item disappears because classification is incomplete.

## 8. Investigation agenda

### 8.1 Agenda item

The scheduler applies the frozen template registry to the inventory and emits agenda items.

```jsonc
{
  "schema_version": "investigation-agenda1",
  "agenda_item_id": "agenda:<hash>",
  "episode_id": "...",
  "pr_number": 33098,
  "template_id": "theorem.proof.canonicalization.v1",
  "investigation_kind": "proof_canonicalization",
  "modification_ids": ["modification:..."],
  "scope": {
    "primary_change_id": "change:...",
    "related_change_ids": []
  },
  "question": "Can this proof be replaced by a canonical lemma, tactic, or shorter proof structure?",
  "required_methods": ["local_read"],
  "optional_methods": ["repository_search", "lean_check"],
  "trigger_facts": ["subject_kind=theorem", "component.proof=modified"],
  "priority": "standard",
  "scheduler_version": "inventory-agenda/1",
  "source_sha256": "..."
}
```

### 8.2 Deduplication

The scheduler may merge agenda items only when they have the same investigation kind, compatible
methods, and semantically related scope. Every contributing modification ID and trigger remains in
the merged item. It must not merge merely because items share a concern family.

### 8.3 Prioritization

Priority determines execution order, never silent omission:

1. deterministic failures and public API compatibility;
2. statement semantics and typeclass coherence;
3. duplication, generality, family consistency, and canonical proof structure;
4. naming, documentation, layout, and residual checks.

All scheduled items receive a terminal investigation record. Lower priority work may be deferred to a
later batch but cannot disappear from a complete run.

### 8.4 Context assembly

Agenda prompts receive:

- a compact PR-level change inventory and changed-file manifest;
- complete code for primary targets;
- concise summaries and IDs for related changed targets;
- the exact investigation question and permitted methods;
- repository tools appropriate to the investigation;
- existing deterministic check results as observations.

The model may request scope expansion through a structured follow-up. It may not attach arbitrary
foreign targets without scheduler validation.

## 9. Investigation records

The coverage-ledger proposal is revised around agenda items rather than a Cartesian target-by-family
matrix.

```jsonc
{
  "schema_version": "investigation-record1",
  "agenda_item_id": "agenda:...",
  "disposition": "candidate | checked_no_request | not_applicable | inconclusive | needs_followup",
  "inspection_methods": ["local_read", "repository_search"],
  "inspected_change_ids": ["change:..."],
  "inspected_entity_ids": ["entity:..."],
  "artifact_refs": ["evidence-artifact:..."],
  "candidate_ids": ["candidate:..."],
  "followup_request_ids": [],
  "basis": "The proof duplicates the existing sibling pattern and can use ...",
  "producer": "model",
  "source_sha256": "..."
}
```

Disposition semantics:

- `candidate`: at least one grounded candidate is emitted.
- `checked_no_request`: the scheduled question was investigated and no request is warranted.
- `not_applicable`: trigger facts were insufficient or the template does not apply after inspection.
- `inconclusive`: the investigation was performed but available evidence does not support a decision.
- `needs_followup`: another target, method, or norm source is required.

`deferred` is execution state on the agenda schedule, not an epistemic disposition. A complete run has
no deferred agenda items, but it may honestly contain `inconclusive` records.

## 10. Follow-up requests and graph expansion

```jsonc
{
  "schema_version": "investigation-followup1",
  "followup_request_id": "followup:<hash>",
  "agenda_item_id": "agenda:...",
  "request_kind": "expand_scope | sibling_compare | repository_norm | specialist_review",
  "query": "Find sibling cardinality lemmas and their naming convention",
  "suggested_change_ids": ["change:..."],
  "status": "requested | scheduled | resolved | rejected",
  "source_sha256": "..."
}
```

The scheduler resolves suggested change IDs against the same episode. Repository queries may refer to
unchanged code, but unchanged locations are evidence anchors, not review targets.

This hook supports later sibling propagation and norm discovery without changing the first treatment's
core contracts.

## 11. Automated check results

Compiler, linter, and other deterministic tools produce a separate artifact:

```jsonc
{
  "schema_version": "investigation-check1",
  "check_id": "check:<hash>",
  "episode_id": "...",
  "change_ids": ["change:..."],
  "check_kind": "lean_compile",
  "outcome": "passed | failed | unavailable",
  "artifact_id": "evidence-artifact:...",
  "source_sha256": "..."
}
```

A failed target-local compile check can deterministically seed a candidate. A passed result is supplied
to correctness investigations but does not resolve them.

## 12. Candidate and evidence integration

Candidate claims retain the existing grounded ask contract. The treatment adds two requirements:

1. Every model candidate references the agenda item that produced it.
2. Candidate scope is validated against the episode change graph, not only the physical prompt work
   unit.

Concern family is assigned to the candidate and may differ from the template's hints. Evidence planning
continues after candidate creation, while discovery-time searches used by the investigation are retained
as provenance and may seed, but do not automatically satisfy, publication evidence.

The evidence gate and semantic judge remain logically separate:

- the investigation asks whether a candidate should exist;
- evidence adjudication asks whether its claim and proposed resolution are supported;
- semantic evaluation asks whether it matches a maintainer obligation.

## 13. Treatment artifacts

The stable `0.9.0` dataset release is unchanged. Experimental runs add:

```text
results/pr_review_v4/runs/<run-id>/
  treatment_manifest.json
  modification_inventory.jsonl
  inventory_report.json
  investigation_templates.json
  investigation_agenda.jsonl
  agenda_report.json
  investigation_checks.jsonl
  investigation_records.jsonl
  investigation_followups.jsonl
  candidates.jsonl
  evidence/
  findings.jsonl
  evaluation.json
  run_manifest.json
```

The run plan hashes the inventory, template registry, agenda, prompts, model configuration, and expected
agenda item IDs before execution. Terminal run sealing requires exactly one terminal investigation
record per expected agenda item and complete candidate/evidence lineage.

## 14. Offline-first acceptance gates

No model call is authorized until the deterministic inventory and agenda pass these gates.

### Gate A: inventory integrity

- every eligible change target is represented or has an explicit structural-context disposition;
- no changed range is silently lost;
- inventory IDs and component hashes regenerate byte-identically;
- gold poisoning leaves all inventory artifacts unchanged;
- unsupported parse cases are counted and receive fallback classification;
- overlapping structural targets do not create duplicate primary modifications.

### Gate B: template integrity

- every template has structured applicability predicates;
- no template or trigger references gold artifacts, comments, outcomes, or PR numbers;
- each template names methods that exist in the execution environment;
- template application is deterministic and fully covered by fixtures.

### Gate C: agenda opportunity audit

Using gold only after agenda generation, manually determine whether at least one scheduled agenda item
could plausibly discover each obligation.

Required reports:

- agenda-opportunity recall at obligation level;
- agenda items per target and per PR;
- unknown/fallback rate;
- duplicate agenda-item rate;
- agenda distribution by investigation kind;
- cross-work-unit scope requirements.

The six smoke obligations must have 6/6 opportunity coverage without gold-specific templates. Across the
nine-PR pilot, missed obligations must be explained before paid inference. This gate measures whether the
scheduler asks the right questions, not whether the model answers them correctly.

### Gate D: prompt and budget audit

- every agenda item appears in exactly one scheduled batch;
- preview and execution prompts are byte-identical;
- no batch silently truncates targets, methods, or related-target context;
- expected calls and token budgets are reported before execution;
- comparison arms use the same call and token budget.

## 15. Causal experiment

### 15.1 Arms

Run three repetitions of each arm on the same stable smoke work units:

1. **Original baseline:** retained as the historical reference.
2. **Budget-matched generic specialists:** the same number of calls and family/method groupings as the
   agenda treatment, but investigations are assigned uniformly rather than from modification facets.
3. **Inventory-driven agenda:** deterministic inventory, template scheduling, and investigation ledger.
4. **Agenda plus oracle norm packets:** diagnostic only, initially restricted to the two obligations
   never recovered by baseline repetitions.

A cost-matched union of independent baseline samples is reported as an efficiency comparison. It is not
silently treated as a single production run.

### 15.2 Primary metrics

- mean issue recall and resolution recall;
- obligations recovered in at least two of three repetitions;
- obligations recovered in all repetitions;
- per-obligation hit frequency;
- candidate issue precision;
- false `checked_no_request` rate on recoverable obligations;
- inconclusive and follow-up rates;
- raw and selected control findings;
- duplicate and conflicting candidates;
- calls, tokens, cost, and latency per recovered obligation.

### 15.3 Success criteria

Before seeing treatment results, freeze concrete thresholds. The initial proposed gate is:

- agenda-opportunity recall is 6/6 on the smoke;
- mean issue recall exceeds the budget-matched generic-specialist arm;
- at least two obligations are recovered in at least two of three repetitions;
- paired candidate issue precision does not decline materially;
- no selected control finding survives the corrected selector;
- no agenda item is missing, deferred, or represented only by an ungrounded basis;
- the two never-hit obligations remain explicitly separated as the norm-knowledge frontier unless
  oracle norm packets recover them.

The experiment is a mechanism test on a development smoke, not a benchmark claim.

## 16. Norm-discovery integration

Norm discovery is introduced only after an oracle diagnostic demonstrates that appropriate review-time
repository information changes issue or resolution recovery.

An oracle norm packet may contain:

- relevant unchanged declarations;
- sibling naming or statement patterns;
- canonical constructors or lemmas;
- analogous implementations;
- review-time-valid historical context, request, and adopted resolution triples.

It may not contain the target PR's maintainer comment, gold obligation, outcome, or post-review revision.

If oracle packets help, the production retriever is evaluated on two separate gates:

1. norm-source retrieval: did it find the useful repository evidence?
2. norm application: given that evidence, did the investigator derive the appropriate request?

This prevents retrieval and reasoning failures from being fused into one score.

## 17. Implementation plan

Status values are `TODO`, `IN PROGRESS`, `BLOCKED`, and `DONE`.

| Phase | Status | Deliverable | Acceptance gate |
|---|---|---|---|
| 0. Freeze design and baselines | TODO | Versioned spec, baseline hashes, corrected selector applied to comparison reports | Existing three repetitions replay with frozen semantic outputs |
| 1. Coarse inventory | TODO | Deterministic subject and lifecycle inventory from `cg1` | Gate A passes; distribution report reviewed |
| 2. Component differencer | TODO | Statement/proof/body/docs/attribute component deltas | Supported declarations pass positive/negative fixtures; unknowns explicit |
| 3. Template registry | TODO | 10-15 structured investigation templates | Gate B passes; no gold-dependent predicates |
| 4. Agenda scheduler | TODO | Deterministic agenda, deduplication, priorities, batch plan | Gates C and D pass offline |
| 5. Ledger and follow-ups | TODO | Investigation records, checks, follow-up schemas, completeness validator | Missing/duplicate/invalid lineage fixtures fail loudly |
| 6. Execution adapter | TODO | Specialist prompts, task adapter, runner integration, treatment manifest | Preview/execution hash parity and dry-run sealing pass |
| 7. Evidence and candidate integration | TODO | Agenda-linked candidates, episode-scope validation, discovery provenance | Existing evidence/selection tests plus new cross-unit fixtures pass |
| 8. Smoke experiment | TODO | Three repetitions of budget-matched arms | Pre-registered report produced without changing thresholds |
| 9. Oracle norm diagnostic | TODO | Hand-audited review-time norm packets for never-hit obligations | Retrieval-input isolation audit passes; effect reported separately |
| 10. Broader pilot decision | TODO | Proceed, revise, or reject treatment | Decision follows smoke mechanism evidence |

## 18. Proposed modules

```text
src/datasets/pr_review_v4/
  modification_inventory.py
  component_diff.py
  investigation_templates.py
  investigation_agenda.py
  investigation_ledger.py
  render_investigation_prompts.py
  evaluate_investigations.py

inputs/pr_review_v4/treatments/inventory_agenda_v1/
  templates.json

tests/datasets/
  test_pr_review_v4_inventory.py
  test_pr_review_v4_agenda.py
  test_pr_review_v4_investigation_ledger.py
```

The implementation should reuse stable v4 I/O, hashing, manifest, target, evidence, and semantic-judge
utilities rather than introducing a parallel pipeline.

## 19. Test strategy

### 19.1 Unit tests

- lifecycle classification for added, removed, modified, and ambiguous targets;
- component differencing for proof-only, statement-only, binder, attribute, body, and documentation edits;
- conservative unknown behavior on unsupported syntax;
- deterministic template applicability;
- agenda deduplication without lost trigger provenance;
- check results cannot close broad concern investigations;
- candidate and follow-up scope validation;
- investigation disposition invariants;
- run completeness over expected agenda IDs.

### 19.2 Metamorphic tests

- poison every gold artifact and verify inventory, agenda, and prompts are unchanged;
- reorder source JSONL rows and verify stable output ordering and hashes;
- add an unrelated target and verify existing modification and agenda IDs remain stable;
- change only a proof and verify statement/type component hashes remain unchanged;
- force parser failure and verify fallback agenda items appear rather than disappearing.

### 19.3 Integration tests

- one added theorem schedules statement, API, naming, documentation, and proof investigations;
- one proof-only edit avoids irrelevant constructor/API-shape investigations;
- a changed sibling family schedules a relational consistency investigation;
- a passing compile check remains an observation while semantic correctness is investigated;
- a follow-up expands to another target in the episode and preserves lineage;
- a complete empty-review control produces terminal records without filler findings.

## 20. Risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Ontology explosion | Template registry becomes another unmaintainable benchmark | Start with 10-15 templates; add only from audited miss classes |
| Classifier error | Relevant investigation is not scheduled | Explicit unknowns, conservative fallback, offline opportunity audit |
| Output bureaucracy | Model emits plausible ledger prose without investigation | Structured methods and references; specialist passes; audit gold-intersecting records |
| Budget confounding | Extra calls are mistaken for scheduling gains | Budget-matched specialist arm and cost-matched union comparison |
| Gold overfitting | Templates encode development comments | Structured generic predicates, no PR IDs, freeze before holdout |
| Taxonomy mismatch | Correct candidate is assigned to a different family than gold | Schedule by investigation kind; evaluate semantically with acceptable family mappings |
| Work-unit confinement | Cross-target judgments remain impossible | Episode-scope validation and structured follow-up expansion |
| Norm absence | Agenda reliably concludes against unknown repository preferences | Inconclusive/needs-followup states and oracle norm diagnostic |
| Early shared-state error | One mistaken relation propagates widely | Relation hints remain hypotheses; every propagated application is independently checked |

## 21. Open questions

1. Which Lean parser API can expose statement, binder, attribute, and proof spans robustly enough for
   deterministic component hashing?
2. Should public API visibility be syntax-derived, repository-policy-derived, or left unknown in v0.1?
3. Which relation hints can be derived deterministically without introducing noisy semantic matching?
4. Should generic-specialist comparison prompts contain the same compact PR inventory while withholding
   only template applicability decisions?
5. How should call and token budgets be equalized when agenda sizes differ across PRs?
6. Which investigation kinds require repository search before `checked_no_request` is permitted?
7. Should the residual open-ended pass run once per PR or once per changed file?
8. What minimum human agreement is required for the offline agenda-opportunity audit?

## 22. Immediate next steps

1. Review and revise this specification.
2. Freeze the corrected baseline selector and three-run reports.
3. Implement only coarse inventory generation and its audit report.
4. Render a human-readable inventory preview for the three smoke units and nine pilot PRs.
5. Draft the initial template registry as data.
6. Generate agendas offline and conduct the 6/6 smoke opportunity audit.
7. Decide whether component differencing and agenda quality justify implementing model execution.

No paid model runs are required before Step 7.

## 23. Commands to run

No commands yet. The design and template registry must be reviewed before implementation begins.
