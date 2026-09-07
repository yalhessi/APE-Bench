# PR Review v4: Semantic Targets and Evidence-Backed Review

*Status: revision 0.3, stable development core implemented*
*Created: 2026-07-11*
*Dataset family: `pr_review_v4`*

## 1. Purpose

The current pipeline has produced useful measurements, but its central objects are no longer aligned:

- `pr_review_v2` records model a review-time PR plus comment- and revision-derived gold.
- `pr_review_v3` replaces comments with interventions, but its anchors still refer to broad diff
  hunks inherited from v2.
- The generation pipeline treats those hunks as review sites, candidate containers, output anchors,
  and sometimes retrieval queries.
- Evidence from code, repository search, compilation, policy, and historical reviews is presented as
  if it had the same meaning and strength.

This conflation caused the `gold.delta_total` future-state leak, silent site reduction, prompt
truncation, ambiguous location matching, and candidate floods that were difficult to distinguish
from final review findings.

PR Review v4 has two deliberately separate architectures. The benchmark foundation is:

```text
RawEventLedger -> ReviewEpisode -> ChangeGraph -> JudgmentGraph -> EvaluationView
```

Experimental reviewing systems consume an episode input and may use a derived change graph:

```text
EpisodeInput + ChangeGraph -> CandidateClaim -> EvidencePacket -> ReviewFinding
```

Experimental outputs are not part of the dataset release. The intervention is retained as one
versioned evaluation view over the judgment graph rather than becoming the permanent storage unit.
Atomic judgments, grouping relations, scope relations, and outcome observations remain available to
future views.

The intended end state is:

> Generate candidates broadly over a complete review-time change surface, acquire claim-specific
> supporting and contradicting evidence, and publish only candidates whose evidence clears an
> explicit selection policy.

## 2. Non-negotiable principles

1. **Review-time isolation.** Anything visible to the system under test is a pure function of the PR
   state available when the maintainer began the review. Gold comments, outcomes, and later
   revisions are evaluation-only.
2. **Semantic targets, not hunks.** Diff hunks provide changed ranges. Parsed declarations and
   file-level structures define review targets. Hunk boundaries are never treated as semantic truth.
3. **Location is not evidence.** A primary anchor tells a maintainer where to read. Evidence may
   live at that location, elsewhere in the repository, in a tool result, in policy, or in a
   historical review.
4. **Evidence is typed.** A compiling replacement, an exact repository declaration, a local naming
   pattern, and a historical precedent have different implications and must remain distinguishable.
5. **Precedent is normally a prior.** A past review comment supports a current finding only when a
   concrete transfer argument shows that the triggering pattern is present here.
6. **Candidate generation is not review publication.** Candidate agents do not issue merge verdicts.
   Unsupported candidates are retained for recall analysis but are not final findings.
7. **No silent loss.** Changed ranges, targets, work units, candidates, and evidence requests are
   either processed or carry an explicit exclusion reason.
8. **Exact production previews.** A prompt preview is emitted by the same code path, schemas, and
   inputs as execution. It includes system prompt, user prompt, tool schemas, hashes, and truncation
   metadata.
9. **Immutable versioned artifacts.** New generation never overwrites the v2 records or v3
   interventions. Every result names and hashes the dataset manifest that produced it.
10. **Physical input/gold separation.** Generation workers receive a release's `input/` bundle. Gold
    comments, judgment graphs, outcomes, and post-review revisions live under `gold/` and are not
    mounted into the generation process.
11. **Views, not permanent metrics.** Intervention grouping, adopted-only scoring, top-k, facets,
    and blocking policies are versioned evaluation or experiment views. Changing them does not
    require rebuilding the source episodes.
12. **Raw events are canonical.** The cached GitHub/Git source events are the dataset source of
    truth. V2 records and i5 interventions are migration and parity references, not runtime inputs
    for the final v4 release.

## 3. Version and compatibility policy

### 3.1 Dataset family bump

Benchmark releases and experimental runs live under separate roots:

```text
inputs/pr_review_v4/
data/pr_review_v4/
results/pr_review_v4/
src/mathlib_review/
```

The family bump is intentional. Existing v2 prediction records assume hunk-shaped sites and a flat
finding list; existing v3/i5 interventions do not identify change-graph entities or judgment
obligations.
They are not natively compatible with the v4 generation and evaluation contracts.

### 3.2 Schema versions

The initial schemas are:

| Benchmark artifact | Schema | Meaning |
|---|---|---|
| Dataset manifest | `pr4-manifest-1` | Immutable inputs, generators, hashes, split, and cutoffs |
| Raw source event | `event1` | Immutable GitHub/Git event or content-addressed source object |
| Review episode input | `episode1` | Physically isolated review-time state visible to a reviewer |
| Review episode gold | `episode-gold1` | Hidden feedback window and post-review observations |
| Change graph | `cg1` | Changed ranges plus versioned semantic-entity relations |
| Judgment graph | `jg1` | Atomic judgments, grouping, context, scope, and outcome observations |
| Evaluation view | `view1` | Versioned projection such as intervention issue/resolution scoring |

| Experimental artifact | Schema | Meaning |
|---|---|---|
| Candidate claim | `c1` | Concrete proposed review ask before evidence adjudication |
| Evidence artifact | `evidence-artifact1` | Immutable compiler, repository, policy, or precedent observation |
| Evidence assertion | `evidence-assertion1` | Versioned interpretation linking an artifact to a candidate proposition |
| Evidence packet | `ep1` | Complete evidence disposition for one candidate |
| Review finding | `f1` | Selected evidence-backed output shown as the review |
| Run manifest | `pr4-run-1` | Model, prompts, tools, work units, completion, and artifact hashes |

Schema versions change when field meaning or required structure changes. Additive optional metadata
may retain a schema version, but the generator version and content hash still change.

### 3.3 Relationship to existing data

- Raw bundles in `data/pr_review_v2/cache/bundles/`, cached Git compares, and Git objects are the
  migration source for the event ledger and episodes.
- `pr_review_v2` records are parity references for reconstructed first-review episodes.
- `pr_review_v3/interventions_v5.jsonl` (`i5`) is a migration reference for `jg1` and the initial
  intervention evaluation view.
- Existing intervention IDs remain stable inside that view where the grouping judgment is unchanged.
- Existing anchors are retained as audit metadata, then mapped to change-graph entities.
- No post-review field is copied into episode inputs, change graphs, prompts, retrieval queries, or
  candidate/evidence work units.

Legacy v2 predictions may be projected onto v4 targets for historical diagnostics. Such reports
must be labeled `legacy_projection: true`; they cannot serve as v4 headline results because the old
system did not receive the v4 task contract.

## 4. Artifact layout

```text
inputs/pr_review_v4/releases/<release>/
  manifest.json
  source/
    events.jsonl
    objects/
  input/
    episodes.jsonl
    patches/
  gold/
    episode_feedback.jsonl
    judgment_graph.jsonl
  derived/
    change_graph.jsonl
    views/
      intervention_issue_v1.jsonl

results/pr_review_v4/<run_id>/
    run_manifest.json
    work_units.jsonl
    prompts.jsonl
    candidates.jsonl
    evidence.jsonl
    evidence_packets.jsonl
    findings.jsonl
    predictions_by_pr.jsonl
    report.json
    audit.jsonl
```

Large repository indexes, parser products, and tool caches live under `data/pr_review_v4/` and are
referenced by hash, not copied into the benchmark release. Only exportable derived views needed to
reproduce a published evaluation belong under a release's `derived/` directory.

## 5. Dataset manifest and provenance

The dataset manifest is the root of reproducibility:

```jsonc
{
  "schema_version": "pr4-manifest-1",
  "dataset_id": "mathlib-pr-review-v4-dev",
  "release": "0.1.0-migration",
  "source_kind": "legacy_migration",
  "sources": [
    {
      "path": "data/pr_review_v2/cache/bundles/",
      "role": "raw_github_bundles",
      "sha256": "..."
    },
    {
      "path": "inputs/pr_review_v2/mathlib_pr_review_v2_annotated_20260612.jsonl",
      "role": "episode_parity_reference",
      "sha256": "..."
    },
    {
      "path": "inputs/pr_review_v3/interventions_v5.jsonl",
      "role": "judgment_migration_reference",
      "schema_version": "i5",
      "sha256": "..."
    }
  ],
  "input_artifacts": [{"path": "input/episodes.jsonl", "sha256": "..."}],
  "gold_artifacts": [],
  "corpus_cutoff_policy": "comment.submitted_at < PR review start",
  "pr_numbers": [33048, 33065],
  "split": "development",
  "generator_git_commit": "...",
  "generator_versions": {"events": "pending", "episodes": "legacy_adapter_v1"},
  "created_at": "..."
}
```

Every downstream run and report records the manifest path and SHA-256. Reports with different
manifest hashes are not directly pooled.

## 6. Review episodes and physical isolation

The final episode builder derives review rounds from the raw event ledger. During bootstrap, a
legacy adapter may reconstruct first-review episodes from v2 records, but such a release is labeled
`source_kind: legacy_migration` and cannot become the frozen benchmark release without parity against
the raw-event builder.

The reviewer-visible half of an episode is physically separate:

```jsonc
{
  "schema_version": "episode1",
  "episode_id": "leanprover-community/mathlib4:33421:round1:<reviewed-sha>",
  "repo": "leanprover-community/mathlib4",
  "pr_number": 33421,
  "round_index": 1,
  "title": "...",
  "description": {"text": "...", "provenance": "review_time_verified"},
  "base_sha": "...",
  "reviewed_head_sha": "...",
  "diff": "... base to reviewed head ...",
  "changed_files": ["Mathlib/Algebra/Order/Round.lean"],
  "patch_sha256": "...",
  "source_projection_sha256": "..."
}
```

The hidden half stores feedback-window boundaries, comments, later revisions, and outcome
observations under `gold/`, keyed by `episode_id`. Generation code accepts an input-release path and
has no API for opening the gold root.

The legacy adapter uses an allowlist rather than copying a record and deleting known gold fields.
Descriptions flagged as possibly post-edited are omitted until their review-time text can be
reconstructed from body-edit events. This makes newly added gold fields invisible by default and
prevents metadata edits from becoming a quieter version of the revision leak.

## 7. Change graph

### 7.1 Construction

1. Parse `episode.diff` into immutable old and reviewed changed ranges while preserving `+/-`
   markers.
2. Parse affected Lean files in the base and reviewed workspaces into declarations and structural
   regions.
3. Intersect each changed range with semantic regions.
4. Merge ranges that affect the same declaration into one target.
5. Split hunks spanning multiple declarations into separate targets.
6. Create explicit file-level targets for imports, module docs, namespace/section changes,
   whitespace-only changes, and unparsed ranges.
7. Represent deletions from the base state and additions from the reviewed state.
8. Emit a coverage map from every changed range to one or more targets.

Changed-range identity is content-addressed from the episode, path, coordinates, and diff content.
Semantic-entity identity is separately versioned by parser and content. Names, line numbers, window
numbers, and hunk order are aliases or coordinates rather than permanent identity.

### 7.2 Target schema

```jsonc
{
  "schema_version": "cg1",
  "change_id": "change:<content hash>",
  "entity_id": "lean-decl:<content hash>",
  "pr_number": 33421,
  "kind": "declaration",
  "path": "Mathlib/Algebra/Order/Round.lean",
  "declaration": {"name": "round_eq'", "kind": "theorem"},
  "base_span": null,
  "reviewed_span": {"line_start": 45, "line_end": 70},
  "changed_ranges": [{"old": [45, 45], "new": [45, 70]}],
  "diff_fragments": ["@@ ... with markers ..."],
  "base_code": null,
  "reviewed_code": "... complete declaration ...",
  "context_refs": ["previous declaration ID", "next declaration ID"],
  "parse_status": "semantic",
  "source_sha256": "..."
}
```

Stored targets are never truncated. Prompt rendering may omit context to meet a token budget, but
must record omitted byte ranges and preserve the complete artifact hash.

### 7.3 Location semantics

A final finding has one primary target and may have multiple evidence anchors:

- `primary_anchor`: where the PR author should act, normally a changed range inside the target.
- `related_targets`: other changed targets covered by the same ask.
- `evidence_anchors`: existing declarations, policy sections, tool outputs, or precedent IDs that
  support or contradict the claim.

Evaluation matches claims to judgment scope relations through change and entity IDs first. Line
overlap is a fallback and audit signal, not the definition of issue identity.

## 8. Judgment graph and intervention view

The canonical gold stores atomic judgment claims and explicit relations. Source comments remain raw
events. Context markers such as "same here" refer to an existing judgment and extend its scope rather
than becoming vague standalone labels. Compound recommendations use obligation nodes so partial
adoption and partial prediction can be represented without making intervention grouping canonical.

```jsonc
{
  "schema_version": "jg1",
  "judgment_id": "judgment:<content hash>",
  "pr_number": 33149,
  "action": {"kind": "remove", "object": "new axiom"},
  "speech_act": "request",
  "blocking_force": "blocking",
  "scope_relations": [{"change_id": "...", "relation": "applies_to"}],
  "obligations": [
    {
      "obligation_id": "obligation:<content hash>",
      "claim": "Remove the newly introduced axiom.",
      "resolution_criteria": "No new axiom remains; the fact is derived or the gap is explicit."
    }
  ],
  "source_event_ids": ["github-review-comment:..."],
  "context_relations": [{"event_id": "...same-here...", "relation": "extends_scope"}],
  "outcome_observation_ids": ["..."],
  "annotation": {"producer": "human_confirmed_migration", "source_schema": "i5"}
}
```

An intervention evaluation view groups judgments and declares its aggregation policy:

- **obligation coverage:** fraction of atomic obligations matched;
- **full intervention coverage:** groups whose required obligations are all matched;
- **partial intervention coverage:** groups with at least one but not all obligations matched;
- **issue versus resolution:** same judgment with a different fix versus satisfaction of its
  resolution criteria.

Migration may propose judgments, grouping, context resolution, obligations, and scope relations with
an LLM. Every proposal retains source-event provenance and appears in a human-review digest before it
can enter a confirmed view. Alternative groupings or outcome policies create new `view1` artifacts,
not new source episodes.

## 9. Experimental candidate claims

Candidate generation asks what a maintainer might request. It does not decide whether to publish a
finding. Candidate, evidence, and finding schemas belong to run outputs under `results/`; changing
them does not alter the benchmark release.

```jsonc
{
  "schema_version": "c1",
  "candidate_id": "<content-addressed ID>",
  "run_id": "...",
  "pr_number": 33421,
  "primary_change_id": "...",
  "primary_entity_id": "...round_eq'...",
  "primary_subject": "Metric.round_eq'",
  "change_ids": ["..."],
  "entity_ids": ["...round_eq'..."],
  "concern_family": "naming",
  "concern_label": "name does not describe division behavior",
  "claim": "Rename `round_eq'` to `round_eq_div`.",
  "requested_change": "Rename `round_eq'` to `round_eq_div`.",
  "transformation": {"kind": "rename", "from": "round_eq'", "to": "round_eq_div"},
  "generator_rationale": "... optional diagnostic, not evidence ...",
  "generator_score": 0.63,
  "prompt_hash": "..."
}
```

Candidate-generation rules:

- `concern_family` is a small, versioned routing enum (`correctness`, `proof-golf`, `duplication`,
  `naming`, `generalization`, `documentation`, `style`, `scope`, or `other`). It determines which
  deterministic collectors may adjudicate a claim.
- `concern_label` remains free-form and extensible. Collector routing must never branch on it.
- Every candidate has one primary change/entity/subject tuple copied from the work-unit contract.
  Related targets may be attached, but the claim and requested transformation must name the primary
  declaration. Intake rejects mismatched IDs, entities, subjects, and neighboring-declaration claims.
- Candidate generation predicts the maintainer ask, not its evidence plan. Deterministic policy maps
  the accepted concern family and requested transformation to counterevidence-aware collectors.
- The model may emit zero candidates for a change or entity.
- Candidate limits are per work unit, not mandatory quotas per location.
- Claims name real identifiers and a concrete transformation or decision target.
- Candidate IDs are content-addressed so duplicate generation across windows can be detected.
- Model rationale and self-confidence are diagnostics, not supporting evidence.

## 10. Typed evidence

### 10.1 Evidence artifacts and assertions

The factual artifact is separate from an agent or policy's interpretation of it:

```jsonc
{
  "schema_version": "evidence-artifact1",
  "artifact_id": "<content-addressed ID>",
  "source_type": "compiler",
  "locator": {"path": "...", "declaration": "...", "tool_run_id": "..."},
  "content": {"summary": "Lean verification succeeded", "sha256": "..."},
  "collected_at_review_state": true,
  "collector_version": "proof_edit_v1"
}
```

```jsonc
{
  "schema_version": "evidence-assertion1",
  "assertion_id": "<content-addressed ID>",
  "candidate_id": "...",
  "artifact_id": "...",
  "assertion_scope": "claim | proposed_edit | context",
  "relation": "supports",
  "proposition": "the proposed replacement compiles",
  "producer": "evidence_policy_v1"
}
```

The artifact is immutable. Assertions may differ across collectors or adjudication policies. Every
collector searches for counterevidence as well as support. An evidence packet is complete only when
all required collectors succeeded or carry explicit failure dispositions.

Claim and repair validity are adjudicated separately. A target-local baseline failure can support a
correctness claim even when the candidate's proposed repair fails. In that case the finding may be
published without a suggested fix; failed repair evidence must never erase the valid diagnosis or
be presented as a verified resolution.

### 10.2 Evidence classes

| Source | Typical use | Default policy interpretation |
|---|---|---|
| Reviewed diff or local declaration | Shows the candidate refers to real changed code | Context |
| Compiler, linter, or executable check | Verifies a replacement or demonstrates a failure | Direct |
| Exact repository declaration/API | Duplication, replacement, compatibility, naming collision | Direct/comparative |
| Local sibling or namespace pattern | Naming, style, docs, API consistency | Comparative |
| Written project policy | Explicit policy and metadata requirements | Direct when applicable |
| Historical maintainer precedent | Reviewer preference and recurring convention | Prior/comparative |
| Model explanation without artifact | Candidate rationale only | Not evidence |

### 10.3 Extensible claim-obligation registry

The following is the initial experimental registry, not a fixed dataset taxonomy:

| Facet | Minimum evidence for publication |
|---|---|
| Proof golf | A compiling replacement plus a concrete simplicity/canonicity comparison |
| Generalization | A compiling generalized declaration and evidence that the original use is recovered |
| Duplication | An exact existing declaration and a type-checked replacement or equivalence argument |
| Naming | A local/repository naming pattern, exact proposed name, and collision check |
| Docs | A changed documentation target plus an explicit policy or strong sibling convention |
| Style | A concrete changed construct plus policy or repeated local convention |
| Scope | File/namespace ownership, dependency, usage, or PR-coherence evidence |
| Correctness | Failing check, counterexample, semantic contradiction, or explicit violated policy |

Some social or architectural findings cannot reach machine-verified strength. They remain eligible
when comparative or policy evidence is specific and the finding is marked advisory.

### 10.4 Precedent hygiene

The corpus query for PR `p` may only inspect comments submitted before `p.review_started_at` and must
exclude `p` itself. Each retrieved precedent stores corpus version, comment ID, timestamp, similarity
features, and the local pattern that is claimed to transfer. Precedent-only candidates are not
eligible for final selection.

## 11. Evidence packets and selection

An evidence packet summarizes assertions, contradictions, and collection failures under one named
adjudication policy:

```jsonc
{
  "schema_version": "ep1",
  "candidate_id": "...",
  "required_checks": ["..."],
  "completed_checks": ["..."],
  "supporting_assertion_ids": ["..."],
  "contradicting_assertion_ids": ["..."],
  "status": "supported",
  "evidence_tier": "A",
  "adjudication_policy": "evidence_policy_v1",
  "selection_features": {"specificity": 1.0, "verified_edit": true}
}
```

The initial experimental selection policy is deliberately simple and inspectable:

1. Reject incomplete, claim-contradicted, and precedent-only packets. Context and proposed-edit
   assertions do not override claim status.
2. Deduplicate equivalent claims and merge related target IDs.
3. Rank lexicographically by evidence tier, blocking severity, specificity, and stable candidate ID.
4. Produce a complete ranking; evaluation views may inspect top-k curves or policy thresholds.
5. Compute merge readiness from selected blocking findings; do not ask the candidate agent.
6. Omit a suggested fix whenever the associated structured edit is contradicted.

Self-confidence may break ties only in an explicitly labeled ablation. A learned selector is deferred
until enough evidence-packet outcomes exist to train and evaluate it on a temporal split.

## 12. Work units and prompts

Windows are execution details. A work unit contains stable change/entity IDs and a token budget,
never an ordinal slice whose numbering changes identity.

Candidate prompt inputs:

- PR title, description, and complete changed-file manifest;
- concise PR change summary derived only from the review episode input;
- target-local diff fragments with markers;
- complete changed semantic units and bounded neighboring context;
- repository tools;
- one global experiment rubric.

Evidence prompt inputs:

- one candidate claim and its linked changes/entities;
- the exact evidence obligations selected by the experiment's claim-obligation registry;
- tools appropriate to those obligations;
- instruction to collect support and counterevidence, without access to gold.

Each stored prompt record includes the system prompt, user prompt, tool schemas, model configuration,
token counts, source entity/change hashes, and all omissions. Preview generation reads the same work-unit
manifest and calls the same renderer as execution.

## 13. Runner and merge contract

The run manifest enumerates every expected work unit before execution. Completion is valid only if:

- every expected work-unit ID has exactly one terminal result;
- every eligible change/entity is covered by at least one candidate-generation work unit;
- every candidate has either a complete evidence packet or an explicit terminal failure;
- merged candidates preserve all change/entity IDs and evidence assertion/artifact IDs;
- final findings can be traced back through packet, candidate, change graph, and episode hashes.

Retries retain work-unit IDs and increment attempt numbers. Prediction merging never relies on file
order or duplicated per-window item numbers.

## 14. Evaluation contract

V4 reports a funnel rather than one fused score:

1. **Change coverage:** judgment obligations mapped to generated change-graph entities.
2. **Candidate recall:** a generated candidate issue-matches each obligation.
3. **Evidence support precision:** human-audited fraction of `supported` packets genuinely supported
   by their cited artifacts.
4. **Resolution recall:** candidate transformation satisfies the component's resolution criteria.
5. **Selection:** obligation and full-intervention recall over ranking/threshold views.
6. **Deployment precision:** selected finding precision over gold-bearing and control PRs.
7. **Abstention:** fraction of PRs and changed entities with no selected findings, split by controls and
   intervention-bearing PRs.

Required reporting axes include extensible labels, intervention-view outcome, evidence policy,
change/entity kind, PR size,
and whether retrieval contributed evidence. Confidence intervals use PR-level resampling.

Gold-bearing PRs are development data. Confirmation requires a frozen temporal holdout containing
both intervention-bearing and approved/no-revision controls. No-comment PRs are not automatically
labeled clean; control status and inclusion criteria must be explicit.

## 15. Regression invariants

These checks are release gates, not optional audits:

| ID | Status | Regression | Required invariant/test | Evidence |
|---|---|---|---|---|
| R1 | IN PROGRESS | Future-state leakage | Poison or remove all gold/post-review fields; episode inputs, change graphs, work units, and prompts remain byte-identical | Legacy gold-poison and i5 outcome-poison scope-projection tests pass; raw inputs are built directly from event/compare sources with gold physically separate |
| R2 | DONE | Gold-concentrated target shrinkage | Every textual changed range maps to a target or explicit exclusion; coverage report has zero unexplained ranges | `dev-change-graph-0.5.1` maps all 2,662 review-time ranges: 2,536 to parsed Lean regions and 126 to typed structural targets, with zero unparsed ranges |
| R3 | DONE | Silent truncation | Stored targets are complete; rendered omissions are explicit and hashed; no unterminated declaration snippet | Complete same-file targets are packed without splitting; `dev-pilot-0.8.10` has zero omitted IDs and a 10.5k estimated-token maximum including checklists and exemplar treatment |
| R4 | DONE | Preview/execution drift | Preview and execution renderer outputs have identical hashes for the same work unit | APE task data embeds the stored renderer output and hash; dry-run and regression test reproduce them exactly |
| R5 | DONE | Window loss or duplication | Expected and terminal work-unit ID sets are equal; target coverage is complete; IDs are globally stable | 184 targets occur exactly once in 74 stable units; response ingestion rejects missing, duplicate, unknown, or failed terminal units |
| R6 | DONE | Forced finding flood | Candidate generation permits zero; publication requires evidence; controls report findings per PR and false-finding rate | Empty candidate submission is valid; selector requires external supporting assertions; pilot includes three explicit approved/no-revision controls |
| R7 | DONE | Temporal corpus leakage | Every precedent timestamp predates review start and excludes the current PR | Retrieval filters and revalidates timestamps/current-PR exclusion; future-precedent regression test passes |
| R8 | DONE | Compound-intervention inflation | Obligation, partial-intervention, and full-intervention views are all reported | `dev-judgment-stable-0.9.0` applies nine reviewed decisions, replacing nine compound drafts with 25 source-event-linked atomic obligations; all are included through `all_required` views |
| R9 | DONE | Self-justifying evidence | Model rationale cannot populate evidence IDs; evidence collectors record external artifacts and counterevidence | Collector-created artifacts/assertions have independent hashes; local context and precedents cannot select a finding alone |
| R10 | IN PROGRESS | Positive-only precision | Every pilot and holdout includes explicit controls; deployment precision is reported separately | Development pilot has six intervention PRs and three explicit controls; temporal holdout remains to be sourced |
| R11 | DONE | Mutable provenance | Manifests and reports include SHA-256 hashes; existing versioned artifacts are never overwritten | Dataset manifests, pre-execution `pr4-run-plan-1`, terminal `pr4-run-1`, artifact hashes, and `write_once` invariants are implemented |
| R12 | IN PROGRESS | Anchor conflation | Primary target matching and evidence-anchor validity are evaluated separately | `i5-cg1-map1` stores each source cue, mapping method, confidence, contributing flag, and target relation separately; evidence-anchor evaluation remains |
| R13 | IN PROGRESS | Event/source divergence | Every event JSON pointer resolves in its hashed raw bundle; indexed source keys exactly cover the bundle collections | 8,161 events replay successfully across all 201 candidate bundles; self-contained Git object export pending |
| R14 | IN PROGRESS | Review-round collapse or fabrication | Reviewer decision groups are split only by intervening author pushes; indices are contiguous; every segment is either hydrated or carries an explicit exclusion | `dev-raw-multiround-0.4.0` reproduces the legacy 202-round distribution, preserves all 138 round-one episodes, and exposes four missing compares rather than dropping them |

## 16. Implementation modules

Proposed ownership boundaries:

```text
src/mathlib_review/
  schema.py                 # Pydantic/JSON schemas and stable IDs
  io.py                     # canonical hashes and immutable writes
  release.py                # immutable release manifests and builders
  events.py                 # raw bundle/Git objects -> event ledger
  episodes.py               # event episodes + temporary allowlisted v2 parity adapter
  change_graph.py           # changed ranges and semantic-entity relations
  change_graph_release.py   # immutable cg1 release packaging
  hydrate_change_sources.py # immutable base-file blob hydration for missing snapshots
  judgment_graph.py         # source comments -> judgments, obligations, context, outcomes
  judgment_release.py       # immutable gold-only jg1 draft packaging
  migrate_interventions.py  # i5 parity reference -> jg1 proposals and intervention view
  render_judgment_review.py # atomicity/decomposition review digest
  validate.py               # all release invariants
  work_units.py             # token-budgeted stable work-unit manifests
  render_prompts.py         # shared preview/execution renderer
  evidence.py               # evidence records and packet assembly
  select.py                 # deterministic initial selector
  evaluate.py               # v4 funnel and intervention-component metrics

src/ape/tasks/lean_tasks/formal_math/pr_review_v4/
  candidates.py             # candidate-generation task
  evidence.py               # claim-specific evidence task and tools
```

The existing v2 diff parser, Lean declaration parser, workspace materialization, verification tools,
and v3 judge may be reused behind adapters. V4 code must not import helpers whose contract reads
`gold.*` during generation.

## 17. Iterative implementation plan

Status values: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`. A phase advances only after its gate passes.

Every empirical round closes with a `Commands to run` section containing executable commands,
explicit output paths, and the point at which results should be returned for interpretation. When no
external command remains, the summary states that explicitly.

| Phase | Status | Deliverable | Acceptance gate | Evidence |
|---|---|---|---|---|
| 0. Freeze and migration manifest | DONE | Hash raw bundles, v2/i5 references, and build `0.1.0-migration` | Immutable manifest validates and regenerates byte-identically | `inputs/pr_review_v4/releases/dev-migration-0.1.0/manifest.json` |
| 1. Foundation schemas and validators | DONE | Event, episode, manifest, change, judgment, view, and run schemas | Fixtures pass; incompatible/hidden input rejected loudly | Stable release validation and the v4 foundation/pipeline suite pass 38 tests |
| 2. Raw event ledger | IN PROGRESS | Content-addressed `event1` export from cached bundles and Git objects | Raw objects preserved; event IDs/timestamps deterministic; source coverage report complete | `dev-raw-0.3.0` indexes and replays 8,161 objects across all 201 GitHub bundles; self-contained Git object export pending |
| 3. Review episodes | IN PROGRESS | Raw-event multi-round `episode1` builder plus v2 first-round parity report | Physical input/gold split; gold-poison identity; raw/v2 first-round discrepancies audited | 202 review-round segments across 138 PRs; 198 hydrated episodes; all round-one episodes retain zero hard parity discrepancies; four later-round compare objects remain unavailable |
| 4. Change graph | DONE | `cg1` changed ranges and semantic entities | 100% explained changed ranges; anchored i5 judgments map or carry reviewed exceptions | `dev-change-graph-0.5.1` explains all 2,662 ranges; `dev-scope-map-0.6.1` resolves all 80 anchored, judgeable code interventions |
| 5. Judgment graph and views | DONE | `jg1`, outcome observations, intervention-view migration, review digest | Context links and obligations reviewed; i5 parity differences explained | `dev-judgment-stable-0.9.0` contains 113 judgments and 129 obligations; all nine pending compound acts have reviewed decompositions into 25 atomic obligations, with exact source-event provenance |
| 6. Exact prompt/work-unit path | DONE | Stable token-budgeted units and shared renderer | Preview/execution hash parity; no silent truncation; all eligible entities scheduled | Treatment-neutral `dev-pilot-0.9.0` schedules all 184 targets in 74 complete units with renderer `candidate-prompt/11`; prompt hashes are sealed in each run plan |
| 7. Candidate pilot | IN PROGRESS | No-retrieval `c1` generation on development pilot | Candidate recall reported separately from publication; control PRs included | Stable treatment-neutral release, APE task, runner, response validator, mixed pilot, and exact run contract are ready; the new three-unit smoke and full paid run remain |
| 8. Evidence collectors | IN PROGRESS | Compile, repository, and local-policy collectors | Each collector passes positive/negative fixtures and records counterevidence | Repository search, target-local baseline compile, structured-edit compile, elan recovery, and repository style-policy fixtures pass; broader policy sources and full-smoke audit remain |
| 9. Selector and evaluator views | IN PROGRESS | Evidence assertions/packets, ranked findings, v4 views | Manual support audit meets threshold; obligation/group metrics agree with fixtures | Integrated report now joins location, semantic issue/resolution, evidence disposition, selection, controls, and abstention; a human support-precision audit remains intentionally required |
| 10. Retrieval ablation | DONE | Temporally clean context-to-ask prompt retrieval plus precedent evidence assertions | Corpus leakage and attribution tests pass; no precedent-only finding is selected | Three paired samples found one issue-hit sample under retrieval versus zero under baseline, zero resolution hits in both, and high within-arm instability; lexical retrieval is rejected while temporal provenance infrastructure is retained |
| 11. Temporal holdout | TODO | Frozen mixed holdout and blinded report | No design changes after unblinding; deployment precision and CIs reported | - |

### 17.1 Stable-core boundary

The `0.9.0` development core freezes the parts whose meaning should not change across judgment
experiments:

- raw review-time episodes and complete semantic change targets;
- source-event-linked atomic obligations plus independently versioned intervention views;
- treatment-neutral work units, prompts, and grounded candidate claims;
- typed evidence artifacts, assertions, packets, and deterministic finding lineage;
- separate location, issue, resolution, evidence, selection, control, and abstention reporting;
- immutable dataset manifests, pre-execution run plans, and terminal run manifests.

Expansion experiments may add prompt treatments, retrieval corpora, evidence collectors, or selector
policies. Shrink experiments may remove the facet checklist, structured edits, deterministic discovery,
repository tools, or particular evidence tiers. Neither kind may mutate episodes, targets, obligations,
or run accounting. Any experiment that needs different gold meaning must create a new reviewed view or
dataset release rather than silently changing the stable core.

### 17.2 First pilot

The first executable smoke set uses nine PRs:

- six intervention-bearing PRs spanning correctness, proof-golf, duplication, naming,
  generalization, documentation, style, blocking force, and multi-obligation aggregation;
- three approved/no-revision controls with explicit negative-pressure semantics;
- one theorem control and two documentation controls, so abstention is not tested on one shape only.

Run candidate generation first without precedents. Evidence acquisition initially covers proof-golf,
duplication, and naming because they have the clearest repository/tool obligations. Unsupported
claim types remain candidates but cannot become findings until their collector policy exists.

### 17.3 Executable development smoke run

The canonical smoke release is `inputs/pr_review_v4/releases/dev-pilot-0.9.0`. It contains six
intervention-bearing PRs and three approved/no-revision controls. Generation reads only `input/`
and `derived/`; `gold/` is opened only by evaluation. The release is treatment-neutral: historical
review retrieval and synthetic exemplars are optional experimental prompt treatments, not benchmark
content.

```bash
./ape/bin/python -m src.mathlib_review.release.prebuild \
  --config configs/pr_review_v4_pilot.yaml \
  --out data/pr_review_v4/dev-pilot-0.9.0-base-commits.jsonl
export PATH=/research/projects/proofedit/ya475/.elan/bin:$PATH
./ape/bin/python -m ape.toolkits.execute.lean.build \
  --input_file data/pr_review_v4/dev-pilot-0.9.0-base-commits.jsonl --num_processes 2

./ape/bin/python -m src.mathlib_review.opportunities.runner \
  --config configs/pr_review_v4_pilot.yaml dataset.dry_run=true

./ape/bin/python -m src.mathlib_review.opportunities.runner \
  --config configs/pr_review_v4_pilot.yaml dataset.dry_run=false

./ape/bin/python -m src.mathlib_review.review.candidates \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/work_units.jsonl \
  --responses results/pr_review_v4/runs/dev-pilot-0.9.0/candidate_responses.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/dev-pilot-0.9.0/candidate_responses_workspace_map.json \
  --deterministic-discovery \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0/candidates.jsonl

./ape/bin/python -m src.mathlib_review.judge.semantic_judge \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0/candidates.jsonl \
  --work-units inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/work_units.jsonl \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.9.0/semantic-judge-v1

./ape/bin/python -m src.mathlib_review.evidence.evidence \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0/candidates.jsonl \
  --graphs inputs/pr_review_v4/releases/dev-pilot-0.9.0/derived/change_graphs.jsonl \
  --workspace-map results/pr_review_v4/runs/dev-pilot-0.9.0/candidate_responses_workspace_map.json \
  --boundaries inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/episode_boundaries.jsonl \
  --events inputs/pr_review_v4/releases/dev-pilot-0.9.0/source/events.jsonl \
  --out-dir results/pr_review_v4/runs/dev-pilot-0.9.0/evidence

./ape/bin/python -m src.mathlib_review.opportunities.select \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0/candidates.jsonl \
  --packets results/pr_review_v4/runs/dev-pilot-0.9.0/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/dev-pilot-0.9.0/evidence/assertions.jsonl \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0/findings.jsonl

./ape/bin/python -m src.mathlib_review.analysis.evaluate \
  --judgments inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/judgments.jsonl \
  --views inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/intervention_views.jsonl \
  --pilot-cases inputs/pr_review_v4/releases/dev-pilot-0.9.0/gold/pilot_cases.jsonl \
  --candidates results/pr_review_v4/runs/dev-pilot-0.9.0/candidates.jsonl \
  --findings results/pr_review_v4/runs/dev-pilot-0.9.0/findings.jsonl \
  --semantic-matches results/pr_review_v4/runs/dev-pilot-0.9.0/semantic-judge-v1/matches.jsonl \
  --packets results/pr_review_v4/runs/dev-pilot-0.9.0/evidence/packets.jsonl \
  --assertions results/pr_review_v4/runs/dev-pilot-0.9.0/evidence/assertions.jsonl \
  --out results/pr_review_v4/runs/dev-pilot-0.9.0/evaluation.json

./ape/bin/python -m src.mathlib_review.release.run_contract seal \
  --run-dir results/pr_review_v4/runs/dev-pilot-0.9.0
```

If an older run contains setup failures, retry only those work units under a fresh run name:

```bash
./ape/bin/python -m src.mathlib_review.opportunities.runner \
  --config configs/pr_review_v4_pilot.yaml \
  dataset.dry_run=false \
  dataset.retry_failed_from=.ape/runs/pr_review_v4_pilot_0811_candidates \
  dataset.run_name=pr_review_v4_pilot_0811_retry1 \
  dataset.output_file=results/pr_review_v4/runs/dev-pilot-0.8.11/retry1_responses.jsonl
```

Pass both response files to `candidates --responses`; ingestion requires exactly one successful
terminal response per work unit and ignores the superseded failed row. Likewise, pass the original
and retry `*_workspace_map.json` files together to `evidence --workspace-map`.

## 18. Progress and decision log

Update this section whenever a phase status changes or an empirical result changes the design.

| Date | Decision/result | Consequence |
|---|---|---|
| 2026-07-11 | Existing allv2 worklists were found to prefer `gold.delta_total`; raw `input.diff` has 374 sites versus 300 mixed sites on the 57-PR development set | All mixed-site runs are oracle-site diagnostics; R1 and R2 are release gates |
| 2026-07-11 | Raw hunk spans cover all 82 anchored interventions represented in the current worklist PRs | Change-graph construction starts from a viable review-time surface, but must preserve this coverage |
| 2026-07-11 | The pilot preview truncated diffs/descriptions and omitted changed files, understating prompt size by about 2.2x | Shared production preview renderer is required by R3/R4 |
| 2026-07-11 | Full facet/counterfactual generation improved recall under leaked sites, while self-confidence and retrieval gating were unstable or weak | Preserve broad candidate generation as a hypothesis; require external evidence for selection |
| 2026-07-11 | V4 foundation split into raw events, review episodes, change graph, judgment graph, and evaluation views; runs moved outside releases | Judgment and selector experiments no longer require rebuilding the benchmark dataset |
| 2026-07-11 | Built `dev-migration-0.1.0`: 138 isolated first-round inputs; 12 descriptions with post-edit risk omitted | Provides a safe parity artifact while the raw-event episode builder is implemented |
| 2026-07-11 | Built `dev-events-0.2.1`: 5,756 deterministic events over 138 PRs, with every source pointer and payload hash replay-validated | Raw GitHub bundle indexing is usable; Git compare objects and raw multi-round episode derivation remain |
| 2026-07-11 | Built `dev-raw-0.3.0` directly from 201 raw bundles, the hashed reviewer roster, and compare caches | Exactly reproduces the 138-PR funnel and all review-time first-round fields; 12 unsafe descriptions remain intentionally omitted |
| 2026-07-11 | Built `dev-raw-multiround-0.4.0` with maximal reviewer-event groups separated by author pushes | The 92/31/13/1/1 PR distribution over one through five rounds matches the legacy rule; 198 of 202 segments hydrate, while four missing compares are retained as explicit segment exclusions |
| 2026-07-11 | Built diagnostic `dev-change-graph-0.5.0`; it exposed 200 files without local base snapshots and 343 unparsed structural targets | Kept the artifact immutable and treated its misses as source/parser defects rather than benchmark exclusions |
| 2026-07-11 | Hydrated 178 immutable base-file blobs and built `dev-change-graph-0.5.1` with complete declaration and top-level command regions | All 854 changed-file references and 2,662 textual ranges are accounted for; 2,536 ranges map semantically, 126 are structural-only, and zero remain unparsed |
| 2026-07-11 | Built `dev-scope-map-0.6.1`, joining i5 source comments to review-time v2 anchors, hashed v4 source events, and stable cg1 targets | All 154 comment references resolve to source events; all 80 anchored judgeable code interventions map; 3 unanchored interventions remain explicit unresolved proposals and 14 mappings are queued for human review |
| 2026-07-11 | Built `dev-judgment-draft-0.7.0` with physically separate `jg1`, `obligation1`, outcome-observation, and `view1` records | 80 presumed-atomic views are eligible, nine potentially compound asks are held for review, 17 non-judgeable and four metadata records remain explicit, and outcome poisoning changes only the observation artifact |
| 2026-07-13 | Built `dev-pilot-0.8.4` with 9 PRs, 184 complete targets, 74 stable work units, 14 judgments, and 3 explicit controls | First execution exposed missing workspace preflight and an actual-conversation prompt-contract omission; 0.8.4 is retained as an invalid negative execution test |
| 2026-07-13 | The complete 0.8.4 run recorded 74 empty terminal lists despite 65 units first attempting non-empty submissions | The APE scaffold omitted the task system contract, unconstrained tool calls were rejected, and agents learned to terminate empty; no 0.8.4 recall/precision result is reportable |
| 2026-07-13 | Built canonical `dev-pilot-0.8.5` with renderer `candidate-prompt/4` | The complete contract is embedded in the actual user prompt and the MCP tool exposes required typed candidate fields; workspace preflight fails before fan-out when a base is unavailable |
| 2026-07-13 | The 0.8.5 smoke3 run completed 10/10 units but recorded empty terminal lists after 42 typed objects were rejected | Every object supplied the exact hash suffix but omitted the visually ambiguous `change:` prefix; the full run remains blocked and 0.8.5 is not scored |
| 2026-07-13 | Built canonical `dev-pilot-0.8.6` with renderer `candidate-prompt/5` | Prompts label copy-exact IDs explicitly, unambiguous bare hashes canonicalize to stable IDs, and validation errors identify the failed field |
| 2026-07-13 | Implemented external repository search, structured Lean compile, and temporally filtered precedent artifacts | Local rationale and precedent similarity cannot independently publish a finding; proof-golf support requires a shorter edit that actually compiles |
| 2026-07-13 | Added deterministic selection and a funnel evaluator that labels scope hits separately from semantic issue/resolution matching | Candidate recall, evidence support, selection, and control pressure can be audited independently; a paid pilot and manual semantic audit remain empirical gates |
| 2026-07-14 | The 0.8.6 smoke generated 17 accepted candidates but all evidence packets were inconclusive | Free-form concern labels could not route deterministic collectors; compile verification lacked a persistent toolchain contract; policy evidence was unregistered |
| 2026-07-14 | Built `dev-pilot-0.8.7` with renderer `candidate-prompt/6` and evidence collectors v2 | Typed concern families now route collectors while free-form labels retain nuance; baseline and edited Lean states are distinct artifacts; elan is recovered from workspace ancestors; repository style checks are registered |
| 2026-07-14 | Replayed PR 33057 against its persisted reviewed workspace | The baseline correctness claim is supported by a target-local Lean error, while the model's proposed edit is separately contradicted and its suggested fix is withheld |
| 2026-07-14 | The 0.8.7 smoke passed evidence plumbing but missed all four eligible PR 33098 asks | Candidate generation was producing speculative code observations rather than concrete maintainer transformations; one claim was attached to a neighboring declaration and the selected compile failure retained hedged candidate wording |
| 2026-07-14 | Built `dev-pilot-0.8.8` with renderer `candidate-prompt/7` and grounded-ask contract v1 | Generation scans every family for concrete maintainer requests; primary subjects are mechanically validated; evidence planning moved after generation; direct compiler findings are rendered from evidence and normalized to blocking |
| 2026-07-14 | The 0.8.8 grounding smoke produced three grounded concrete asks but missed the known compiler failure and all three visible PR 33098 obligations | Grounding/register form passed; voluntary model discovery and the paragraph-level facet instruction failed |
| 2026-07-14 | Replayed deterministic discovery on the persisted 0.8.8 workspaces | It created exactly one PR 33057 correctness candidate, which Lean supported and the selector published as blocking; it created no control candidate |
| 2026-07-14 | Built `dev-pilot-0.8.9` with renderer `candidate-prompt/8` and deterministic discovery `compile-style/1` | Baseline compiler/style failures are universal candidates; every model target receives a visible eight-family checklist with no finding quota |
| 2026-07-14 | The 0.8.9 smoke reproduced the 0.8.8 model outputs while deterministic discovery recovered PR 33057 exactly | Universal checks are retained; the explicit facet battery is rejected as a semantic-recall intervention |
| 2026-07-14 | Ported the audited v7.1 issue/resolution rubric to `semantic-match1` and `v4-semantic-report1` | Stable change IDs establish location pairing only; cached gold-only judging now automates semantic candidate recall and emits a standing human audit artifact |
| 2026-07-14 | The one-pair semantic judge smoke rejected the unused-`h_nonempty` candidate as both issue and resolution mismatch | Automated reason matched manual judgment; cache replay had zero uncached pairs and byte-identical outputs |
| 2026-07-14 | Built `dev-pilot-0.8.10` with renderer `candidate-prompt/9` and synthetic exemplar prior v1 | The only behavioral difference from 0.8.9 is one prompt block containing three unrelated examples of concrete maintainer transformations; retrieval and all frozen channels are unchanged |
| 2026-07-14 | Built `dev-pilot-0.8.11` with renderer `candidate-prompt/10` and temporal context-to-ask retrieval | Rostered maintainer comments are matched from target-local code to prior diff context under a minimal review-start cutoff; replies and unresolved cross-comment anaphora are excluded, stripping retrieval restores 0.8.9 prompts, and all downstream channels remain frozen |
| 2026-07-14 | The 0.8.11 retrieval smoke reached 0.75 overall location recall, zero raw control candidates, and one judge-confirmed strict issue match among three included PR 33098 obligations | Treat retrieval as a confirmed directional pass pending replication; decompose `pr33098_i01`, whose excluded composite gold contains an independently recovered `encard_` naming request |
| 2026-07-14 | The identical 0.8.11 replication fell to 0.25 overall location recall and zero expected issue matches, while raw candidates changed on all three units | Do not expand or claim a stable retrieval effect; freeze both arms and run a three-sample paired 0.8.9-versus-0.8.11 ablation, while decomposing `pr33098_i01` only as a separate dataset correction |
| 2026-07-14 | Across three fully judged samples, 0.8.9 baseline had zero issue-hit samples and 0.8.11 retrieval had one, with zero resolution matches in both arms | Reject the current lexical context-to-ask policy as unstable; retain its temporal/provenance infrastructure, require three-sample development screens, and next test separately hashed historical context, ask, and adopted resolution triples |
| 2026-07-14 | Reviewed all nine compound judgment drafts and built `dev-judgment-stable-0.9.0` | The benchmark now scores 129 atomic obligations; 25 obligations retain exact source-event provenance from the nine reviewed decompositions, and none remain pending |
| 2026-07-14 | Built treatment-neutral `dev-pilot-0.9.0`, immutable run plans/manifests, and one integrated evaluator | Prompt treatments can now expand or shrink independently of the stable benchmark; every real run must prove prompt, terminal-result, candidate, evidence-packet, and finding lineage coverage |

Open decisions:

1. What exact evidence tier is sufficient for advisory scope and architecture findings?
2. Should component splits be mandatory for every conjunction or only independently satisfiable asks?
3. What control labels are defensible for approved/no-revision PRs without treating silence as proof
   of cleanliness?
4. After the first evidence audit, should the selector remain lexicographic or be calibrated from
   evidence features?

## 19. Definition of done

PR Review v4 is ready for a full run only when:

- the manifest, event, episode, change graph, judgment graph, view, and experimental run schemas
  are versioned and validated;
- all R1-R14 invariants pass;
- the change graph explains the complete review-time change surface;
- judgment obligations and intervention views map to changes/entities and have completed human review;
- prompt previews are production-identical;
- candidate recall, evidence validity, and final selection are reported separately;
- at least one mixed pilot demonstrates that evidence-backed selection improves precision over raw
  candidate confidence without an unacceptable loss of component recall;
- the temporal holdout is frozen before any confirmation run.

Until those conditions hold, v4 outputs are development diagnostics rather than benchmark claims.
