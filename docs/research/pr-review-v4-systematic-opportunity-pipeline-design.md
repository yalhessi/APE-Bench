# PR Review v4: Systematic opportunity recovery pipeline

*Status: v0.1 design proposal for review*
*Created: 2026-07-17*
*Scope: experimental treatment over the `dev-pilot-0.9.0` stable core*
*Amends: `pr-review-v4-inventory-driven-agenda-spec.md` and
`pr-review-v4-coverage-ledger-spec.md`*

## 1. Decision

The next implementation should be a **method-routed opportunity pipeline**, not a larger holistic
prompt, a Cartesian target-by-concern ledger, or a monolithic repository norm index.

The pipeline has six stages:

```text
review-time episode + change graph
    -> modification inventory and PR relation map
    -> applicable investigation methods
    -> method-specific opportunity discovery
    -> technical and norm evidence
    -> review-worthiness decision
    -> PR-level synthesis and evidence-backed findings
```

The inventory is routing infrastructure. The research hypothesis is stronger and narrower:

> A fixed, auditable set of method-specific discovery procedures can recover concrete review
> opportunities more consistently than voluntary holistic generation, while typed evidence and
> explicit abstention prevent forced coverage from becoming a finding flood.

This is the best-supported next direction because the two oracle probes established that exact API,
wrapper-composition, and naming evidence can recover obligations the stable reviewer missed. They did
not establish that production retrieval can discover those opportunities, that all opportunity
classes benefit equally, or that a compiling alternative is enough to predict a maintainer comment.
The design therefore makes discovery, technical validity, norm applicability, review-worthiness, and
publication independently measurable.

## 2. Evidence reviewed before this proposal

This proposal was checked against the following design and result history:

- the v4 episode, change-graph, judgment-graph, evidence, and evaluation foundation in
  `pr-review-v4-evidence-pipeline-design.md`;
- the intervention and atomic-obligation measurement correction in
  `intervention-benchmark-redesign.md`;
- the investigation-accountability proposal and its review in
  `pr-review-v4-coverage-ledger-spec.md`;
- the modification inventory, agenda, follow-up, and offline-gate proposal in
  `pr-review-v4-inventory-driven-agenda-spec.md`;
- the historical retrieval assumptions in `precedent-retrieval-design.md`;
- the v2 miss decomposition, selector upper-bound, baseline, and leaked-site apply-all diagnostics;
- v4 smoke verdicts from grounded candidates through deterministic discovery, exemplars, temporal
  retrieval, the stable three-repetition baseline, the manual agenda probe, and both oracle probes.

The old apply-all measurements are used only as oracle-site mechanism diagnostics. Their worklists
were later shown to depend on post-review `gold.delta_total`; they are not deployable recall results.

## 3. Lessons ledger

### 3.1 Findings the new design must preserve

| Evidence | Lesson | Design consequence |
|---|---|---|
| V4 stable core | Review-time isolation, complete semantic targets, atomic obligations, and separate issue/resolution scoring are working infrastructure | Do not rebuild or mutate the benchmark release |
| V2 metric corrections | Location overlap can flatter a system; loose gold and judges materially change conclusions | Keep semantic issue and resolution judging, standing audits, and exact denominators |
| V2 miss decomposition | Most misses already had activity near the human anchor; easy findings displaced the relevant concern | Inventory schedules investigation methods, not merely locations |
| Grounded-ask smoke | Correct target IDs and concrete request form removed attachment errors but did not improve judgment | Grounding is an intake invariant, not a discovery mechanism |
| Deterministic discovery | Universal compile checks recovered the known factual failure exactly and stably | Keep universal factual checks outside voluntary model generation |
| Facet battery | Telling one agent to inspect every concern did not change its behavior | Coverage must be represented by executable tasks and artifacts |
| Apply-all diagnostics | Removing voluntary skip increased coverage but also produced filler and a severe precision cost | Every task needs `no_request`, `inconclusive`, and follow-up outcomes; no finding quota |
| Manual agenda probe | Generic specialist prompts reduced obligation coverage and increased control criticism | Specialists must be differentiated by actual methods and evidence, not labels alone |
| Selector studies | Validity, tools, centrality, and legibility did not reliably predict which valid V2 edit a maintainer would mention | Technical merit and review-worthiness must be separate decisions |
| Generic exemplars | More location coverage did not improve semantic issue recovery | Do not use candidate count or location recall as a treatment success gate |
| Temporal lexical retrieval | Context-to-comment retrieval produced one non-replicating issue hit and no resolution hits | Retain temporal provenance, but replace lexical transfer with typed source and transformation retrieval |
| Retrieval postmortem | A historical request without its adopted resolution under-specifies the transformation | Historical evidence uses trigger, request, and adopted-resolution triples |
| Stable three repetitions | Identical prompts produced different candidates; union recall exceeded every single run and no obligation was stable | Report per-obligation frequency and use at least three repetitions for every LLM treatment claim |
| Coverage-ledger review | A completed JSON cell does not prove an investigation happened; passing compilation does not close correctness | Require method execution artifacts; checks are observations rather than broad dispositions |
| Work-unit analysis | Some judgments cross work-unit boundaries, but most do not | PR relations and episode scope are necessary infrastructure, not the main accuracy claim |
| Oracle opportunity probe | Supplying the exact canonical API recovered a never-hit issue and resolution with a clean control | Canonical API discovery is the first production operator |
| Oracle evidence probe | Compile-backed wrapper composition and subject-conditioned naming statistics changed rejections into requests; controls stayed clean; both issue-match, but only naming resolution-matches | Implement wrapper/API and naming operators separately and measure transformation construction after issue discovery |
| Oracle evidence probe | Compiling `grind` and `rfl` alternatives remained too optional to request | Compilation proves validity, not maintainer preference; test historical selection evidence separately |
| Evidence audits | Token matches and one sibling pattern can falsely support naming or duplication | Comparative evidence must include exact objects, scope, prevalence, and counterexamples |

### 3.2 Assumptions this proposal rejects

1. **A complete location inventory is sufficient.** It is useful for accounting, but the demonstrated
   gap is often the selected aspect or transformation at an already inspected target.
2. **One general reviewer can be made systematic by prompt language.** The battery and generic
   specialist experiments reject this implementation strategy.
3. **All concern families deserve a Cartesian pass over all targets.** This wastes budget and invites
   shallow completion. Applicability is determined by modification facets and method preconditions.
4. **A valid or compiling improvement is a review finding.** The proof-compression and `rfl` oracle
   cases directly reject this.
5. **Repository frequency is a norm.** Counts are evidence only when conditioned on the semantic
   subject and accompanied by meaningful counterexamples and scope.
6. **A similar historical comment is enough.** Transfer needs the triggering pattern, the requested
   change, the adopted resolution, temporal validity, and current-case applicability.
7. **Approved or uncommented code proves a criticism false.** Silence is a weak negative signal, not
   a semantic label. Control interpretation must remain conservative.
8. **A PR graph alone will move the accuracy floor.** It repairs scope and composition expressivity;
   it does not supply missing norms or choose among valid local improvements.
9. **The oracle probes measured end-to-end recovery.** Their opportunities and alternatives were
   hand selected using development knowledge. They measured application and evidence sufficiency,
   not automatic source discovery.

### 3.3 Still-unproven hypotheses

The implementation must not silently promote these hypotheses to facts:

- type- and dependency-aware retrieval will find the canonical APIs that the oracle supplied;
- a production naming query can infer the correct semantic subject and comparison population;
- intra-PR composition can propose the correct wrapper edit without seeing the maintainer outcome;
- adopted historical transformations will make proof-golf and syntax preferences predictable;
- method saturation will improve single-run stability beyond a cost-matched sample union;
- PR-level synthesis will improve coherence without deleting distinct valid findings;
- the six-obligation smoke generalizes beyond one PR and its matched control.

### 3.4 Changes to the existing proposals

This document does not discard the inventory or ledger designs. It changes their role and order:

| Existing proposal | Retained | Changed here |
|---|---|---|
| Coverage ledger | terminal accounting, abstention, explicit unknowns, complete run sealing | replace target-by-concern cells with applicable method tasks; require operator artifacts rather than prose bases |
| Inventory agenda | multi-dimensional modification records, structured applicability, follow-ups, episode scope | keep the first inventory coarse; implement proven discovery operators before a broad template library |
| PR graph | relation-aware context and cross-target scope | use it for composition and synthesis, without treating it as the primary judgment mechanism |
| Evidence pipeline | typed artifacts, counterevidence, supported-only publication, separate diagnosis and repair | add discovery-stage provenance and separate technical, norm, and worthiness decisions |
| Precedent retrieval | temporal cutoff, target-PR exclusion, review-situation unit, recency | replace generic lexical transfer with method-specific trigger/request/adopted-resolution records |
| Oracle opportunity task | explicit opportunity, evidence, and abstention contract | retain as a diagnostic adapter only; production opportunities must be automatically discovered |

The implementation order also changes. The inventory agenda proposed building a broad registry and
ledger before norm discovery. The oracle evidence now supports a narrower route: build only enough
inventory to route canonical API, naming, and wrapper-composition methods; test each with a real smoke;
then expand the registry. This reduces the risk of constructing a large accounting system around
methods that do not improve recovery.

## 4. Goals and non-goals

### 4.1 Goals

1. Turn candidate discovery into a fixed, inspectable schedule of applicable methods.
2. Make every method execution end in a typed terminal record without forcing a candidate.
3. Recover candidate transformations from review-time sources rather than model recall alone.
4. Separate technical validity, norm applicability, and review-worthiness.
5. Preserve PR-level intent and cross-target relations while keeping local investigations bounded.
6. Make single-run behavior more reliable through deterministic search and fixed orchestration.
7. Attribute every gain or failure to scheduling, source retrieval, transformation construction,
   norm inference, adjudication, synthesis, or selection.
8. Keep controls, cost, stochasticity, and temporal leakage visible at every gate.

### 4.2 Non-goals

The first implementation will not:

- build an exhaustive Mathlib rulebook;
- claim that maintainer comments enumerate every valid criticism;
- replace atomic obligations or intervention views;
- train a learned reviewer-worthiness model;
- solve all architectural and social review judgments;
- run every operator on every declaration;
- use repeated sampling as an unreported production fallback;
- infer norms from the target PR's comments, later revisions, or outcome.

## 5. Architecture

### 5.1 Stable benchmark boundary

The following remain frozen from `dev-pilot-0.9.0`:

- episode inputs and review-time snapshots;
- change graphs and stable change/entity IDs;
- judgment graphs, obligations, and evaluation views;
- grounded candidate, evidence, finding, and run-lineage contracts;
- semantic issue/resolution judge and its standing audit protocol.

New artifacts live in a treatment or run directory. They do not enter `gold/` and do not require a
new benchmark release.

### 5.2 PR map and modification inventory

The inventory remains multi-dimensional:

- subject kind and lifecycle;
- changed components such as name, binders, statement, proof, body, attributes, docs, namespace,
  imports, and layout;
- visibility and parser confidence;
- current-PR relations such as declaration dependencies, changed siblings, naming families,
  repeated implementation shape, and possible wrapper/replacement pairs.

The PR map is an episode-scoped relation graph over changed declarations and relevant unchanged
anchors. It serves three bounded purposes:

1. assemble enough PR context for a local investigation;
2. schedule relational methods such as sibling consistency and wrapper composition;
3. synthesize duplicate, propagated, or conflicting candidate asks.

Every relation is a hypothesis with provenance. No relation makes a finding true, and every
cross-target application is independently checked.

### 5.3 Method registry

Scheduling is based on **investigation methods**, not concern labels. Each method specification is
versioned data:

```jsonc
{
  "method_id": "canonical_api_search.v1",
  "applies_when": {
    "subject_kinds": ["theorem", "definition"],
    "lifecycles": ["added", "modified"],
    "any_changed_components": ["proof", "value_or_body"]
  },
  "required_inputs": ["reviewed_declaration", "repository_declaration_index"],
  "operators": ["type_shape_retrieval", "dependency_neighborhood", "applicability_check"],
  "max_opportunities": 5,
  "technical_checks": ["lean_compile"],
  "norm_sources": ["canonical_api_status", "local_usage"],
  "selection_policy": "canonical_replacement.v1"
}
```

The initial registry is deliberately small:

| Method | Primary trigger | Discovery source | Status |
|---|---|---|---|
| `baseline_failure` | any changed Lean target | compile/lint diagnostics | proven infrastructure |
| `canonical_api_search` | changed proof/body reconstructs a known operation | declaration types, names, dependencies, local uses | first implementation |
| `wrapper_composition` | PR introduces or changes related helper/API declarations | PR relation graph plus repository APIs | first implementation |
| `naming_contrast` | added/renamed public declaration or statement/name mismatch | semantic-subject-conditioned name statistics | first implementation |
| `proof_compression` | added/changed proof | bounded proof search plus compile and structural comparison | later, validity shown but worthiness unresolved |
| `structural_rewrite` | explicit cases/binders/rewrites | local AST pattern and historical adopted transformations | later |
| `family_consistency` | changed siblings/counterparts | PR and repository family graph | later |
| `open_review` | one per PR | holistic review over compact inventory and method outputs | residual novelty channel |

Concern families remain candidate metadata and evidence-routing hints. They are not the scheduling
ontology and are not used as exact gold cells.

### 5.4 Investigation task and execution record

The scheduler emits one task per applicable `(method, scoped modification set)`. The executor must
return exactly one terminal record:

```jsonc
{
  "investigation_id": "investigation:<hash>",
  "method_id": "canonical_api_search.v1",
  "modification_ids": ["modification:..."],
  "primary_change_id": "change:...",
  "related_change_ids": [],
  "execution_status": "completed",
  "disposition": "opportunities | checked_no_opportunity | inconclusive | needs_followup | not_applicable",
  "operator_run_ids": ["operator-run:..."],
  "artifact_refs": ["evidence-artifact:..."],
  "opportunity_ids": ["opportunity:..."],
  "followup_ids": [],
  "basis": "..."
}
```

`basis` is explanatory only. Completion requires operator-run or inspected-source artifacts. A model
cannot satisfy the ledger by writing prose. `deferred` is an execution state and is illegal in a
sealed run. `inconclusive` remains a valid epistemic result.

### 5.5 Opportunity discovery

An opportunity is a pre-candidate hypothesis produced by a named method:

```jsonc
{
  "opportunity_id": "opportunity:<hash>",
  "method_id": "wrapper_composition.v1",
  "primary_change_id": "change:...",
  "related_change_ids": ["change:..."],
  "observed_pattern": "The proof unfolds an infimum after constructing a covering witness.",
  "proposed_transformation": {
    "kind": "compose_existing_api",
    "symbols": ["IsCover.coveringNumber_le_encard", "isCover_maximalSeparatedSet"]
  },
  "source_artifact_ids": ["evidence-artifact:..."],
  "discovery_rank": 1,
  "discovery_score": 0.91,
  "source_provenance": "automatic",
  "source_sha256": "..."
}
```

Production opportunities must be reproducible from review-time inputs. Oracle opportunities retain
`source_provenance: oracle_development` and can never enter a production result.

The design distinguishes three source-recovery outcomes:

- **source miss:** the useful API, pattern, or precedent was not retrieved;
- **construction miss:** useful sources were retrieved but no appropriate transformation was formed;
- **ranking miss:** the correct opportunity existed below the bounded delivery cutoff.

This is essential because the oracle probes bypassed all three.

### 5.6 Evidence and norm records

Every opportunity receives separate evidence bundles.

**Technical evidence** asks whether the diagnosis and proposed edit are valid:

- exact declaration/type matches;
- successful application or compilation;
- removed dependencies or implementation steps;
- collision, compatibility, and usage checks;
- contradictions and failed edits.

**Norm evidence** asks whether the transformation is expected in this context:

- explicit policy or canonical API status;
- scoped local/repository prevalence and counterexamples;
- sibling/family consistency;
- temporally prior maintainer trigger/request/adopted-resolution triples;
- evidence about exceptions and the norm's domain.

A norm record is not a free-text snippet:

```jsonc
{
  "norm_id": "norm:<hash>",
  "norm_kind": "naming_pattern | canonical_api | adopted_transformation | local_family",
  "trigger_predicate": "statement head is Set.encard",
  "recommended_action": "use encard in the declaration name",
  "scope": {"namespace": "Metric", "subject": "Set.encard", "snapshot_sha": "..."},
  "support_count": 31,
  "counterexample_count": 4,
  "counterexample_refs": ["..."],
  "effective_before": "review-start timestamp",
  "source_artifact_ids": ["..."],
  "strength": "canonical | strong_convention | recurring_preference | weak_prior"
}
```

The implementation uses method-specific stores rather than one universal vector index:

- a declaration/type/dependency index for APIs;
- a semantic-subject naming statistics table;
- a temporal adopted-transformation store for preferences.

All stores are content-addressed to the exact repository snapshot or corpus cutoff. The target PR and
all post-review data are excluded.

### 5.7 Three-axis adjudication

The current oracle adjudication should be decomposed. For each opportunity, record:

1. **Technical status:** `valid | invalid | uncertain`.
2. **Norm status:** `applicable | contradicted | weak_prior | unknown`.
3. **Review-worthiness:** `request | advisory_option | no_request | defer`.

When worthiness is `request`, the decision separately records
`request_force: blocking | advisory`. An `advisory_option` is a valid suggestion that may be useful
to the author but does not clear the publication threshold for a maintainer-style finding. This
preserves the judgment graph's speech-act and blocking-force distinctions instead of treating every
technically useful observation as a required change.

These axes cannot substitute for one another. A compiling edit may be technically valid but only an
advisory option. A strong canonical API can support a request even when the existing code compiles.
A correctness diagnosis can be valid when its proposed repair fails.

Initial publication policy should be deterministic for the evidence classes already supported:

| Condition | Default result |
|---|---|
| target-local compile/policy failure with direct artifact | request |
| valid replacement using an exact canonical API and removing a reconstructed implementation | request |
| valid wrapper composition with a concrete abstraction/dependency reduction | request |
| collision-free rename with strong subject-conditioned convention and bounded counterexamples | advisory request |
| compiling proof compression with no historical selection evidence | advisory option, not published |
| syntax rewrite supported only by prevalence | advisory option, not published |
| weak precedent or token similarity alone | no publication |

LLM adjudication is reserved for transfer applicability and ambiguous comparisons. It cannot invent
evidence facts. Every factual claim in its decision must cite an artifact ID. Unsupported dynamic tool
observations are rejected at ingestion.

### 5.8 Reliability within one run

"One run" means one fixed orchestration, not one unconstrained model sample. Reliability comes from:

1. deterministic inventory, scheduling, retrieval queries, and bounded top-k results;
2. one terminal record for every applicable method task;
3. deterministic technical checks wherever possible;
4. explicit policies for strong evidence classes;
5. selective redundancy only for ambiguous norm-transfer decisions;
6. deterministic merge, conflict, and synthesis rules.

For ambiguous adjudication, use two independent votes only when the first decision is low-confidence
or the evidence axes conflict. Disagreement produces `defer`, not a randomly selected finding. This
adds redundancy where stochasticity matters without paying for three samples of every deterministic
task.

### 5.9 Context assembly and PR-level synthesis

Local tasks receive bounded packets:

- complete primary declaration;
- compact PR inventory and stated PR purpose;
- typed summaries of related changed declarations;
- only the sources retrieved by the current method;
- prior method outcomes relevant to the same target.

The full diff is not repeated in every packet. Omitted context and hashes remain auditable.

After local adjudication, a PR-level synthesizer:

- groups the same transformation across siblings into one finding with multiple anchors;
- resolves `same here`-shaped propagation over validated relations;
- detects conflicting alternatives and keeps the best-supported one or defers;
- removes exact duplicates without suppressing distinct obligations;
- orders blocking factual failures before advisory norm requests;
- emits a coherent finding set under an explicit volume policy.

Synthesis may combine or suppress candidates but may not create a new unsupported issue. Every final
finding preserves opportunity, evidence, and investigation lineage.

The residual `open_review` pass runs after method outputs are available. It can identify novel concern
families, but its candidates pass the same evidence and publication gates.

## 6. Evaluation contract

### 6.1 Funnel metrics

Report the following separately, by obligation and method:

1. **Schedule opportunity:** did an applicable method task exist?
2. **Source recall@k:** did the method retrieve the source needed for the human transformation?
3. **Transformation recall:** did an opportunity express the relevant issue or resolution?
4. **Technical validity:** was the proposed edit or diagnosis supported?
5. **Norm applicability:** did evidence establish a current repository expectation?
6. **Review-worthiness:** did adjudication request, abstain, or defer?
7. **Candidate issue/resolution recall and precision.**
8. **Selected finding issue/resolution recall and precision.**
9. **Synthesis retention:** were supported issue matches preserved after grouping and conflict handling?
10. **Cost, latency, and stability per recovered obligation.**

Location recall remains a diagnostic and never substitutes for steps 3, 7, or 8.

### 6.2 Stability metrics

For every LLM-containing treatment, run at least three repetitions and report:

- per-obligation hit frequency;
- obligations hit in at least two of three and all three runs;
- variance in opportunity, candidate, and finding counts;
- adjudication agreement and defer rate;
- union recall only as a capability diagnostic, never as single-run performance.

Deterministic inventory, schedule, retrieval, and check artifacts must be byte-identical across
repetitions. Any variation before LLM transformation/adjudication is an implementation bug.

### 6.3 Controls

Use multiple negative pressures rather than treating silence as truth:

- the existing approved/no-revision PR control for publication pressure;
- method-specific counterexamples where an apparent pattern already follows the canonical API;
- compiling alternatives that remove no semantic step;
- naming populations where the current name matches the conditioned pattern;
- deliberately weak or stale precedents that should not transfer.

Report raw opportunities and candidates on controls even when selection filters them. A clean selected
control rate can coexist with a discovery or calibration problem.

### 6.4 Causal comparisons

Every paid smoke includes:

1. the frozen `0.9.0` holistic reference;
2. a cost-matched union of independent holistic samples;
3. the method pipeline with identical stable downstream evidence/selection;
4. method ablations such as API only, naming only, and historical preference only.

Call count, input tokens, output tokens, and latency must be matched or explicitly normalized. This
prevents family isolation or extra sampling from being misreported as inventory gain.

### 6.5 Development and holdout discipline

- The six obligations on PR 33098 and the matched control are development diagnostics.
- Oracle-targeted opportunities never count as production results.
- Method rules are generic and frozen before the nine-PR pilot.
- A mixed temporal holdout is frozen before broad tuning.
- Gold is used only after schedule and opportunity generation to classify misses.
- Every semantic judge run retains a standing accepted/rejected pair audit.

## 7. Implementation plan

Status values are `TODO`, `IN PROGRESS`, `BLOCKED`, and `DONE`. No paid phase begins until its offline
gate passes. Each paid phase uses the smallest real PR smoke capable of falsifying the change.

### Phase 0: Freeze the evidence baseline

**Status:** DONE

The baseline lock and claim matrix are implemented under
`results/pr_review_v4/audits/systematic-opportunities-v1-baseline-lock/`. Frozen semantic judging of
`oracle-evidence-probe-0.2.0` confirms two issue matches and one resolution match: naming recovers the
full resolution, while wrapper composition recovers the issue and broad API direction but not the
maintainer's exact `by_cases!` transformation.

**Implement**

- Record hashes for `dev-pilot-0.9.0`, its three stable smoke runs, the oracle opportunities, oracle
  evidence packets, adjudications, and semantic reports.
- Update the oracle evidence verdict after frozen semantic judging is available.
- Create a machine-readable lesson/claim matrix with `proven`, `suggested`, and `unproven` status.
- Freeze development obligations and matched controls; do not alter their gold to improve the method.

**Gate**

- Historical reports replay from immutable inputs.
- Every oracle artifact is explicitly marked diagnostic and non-production.
- No unresolved semantic result is described as confirmed.

### Phase 1: Contracts and method registry

**Status:** DONE

Production-only schemas, the minimal four-method registry, registry hashing, investigation-aware run
plans, and complete operator/opportunity lineage sealing are implemented. Oracle provenance is
rejected by the production opportunity schema. The registry is frozen at
`inputs/pr_review_v4/treatments/systematic-opportunities-v1/methods.jsonl`.

**Implement**

- Add schemas for `ModificationRecord`, `PRRelation`, `InvestigationMethod`, `InvestigationTask`,
  `OperatorRun`, `Opportunity`, `TechnicalAssessment`, `NormRecord`, `WorthinessDecision`, and
  `SynthesisDecision`.
- Add a versioned JSON method registry and validation rules.
- Extend run plans and sealing to cover expected investigation IDs and full lineage.
- Preserve the existing oracle schema through a diagnostic adapter rather than making it production.

**Offline gate**

- Invalid or missing method runs fail loudly.
- `no_opportunity`, `inconclusive`, and `needs_followup` require real operator artifacts.
- Gold poisoning and JSONL reorder tests leave production artifacts byte-identical.

### Phase 2: Coarse inventory and PR relation map

**Status:** DONE

The frozen treatment contains 184 complete modification records, 283 evidence-backed PR relations,
and 421 applicable method tasks over all nine pilot PRs. All targets classify without unknowns. The
schedule-opportunity audit covers all three obligations assigned to active methods and records the
two proof-compression obligations plus the structural rewrite as explicit future method gaps.

**Implement**

- Generate subject, lifecycle, and coarse component facets from existing `cg1` data.
- Add proof/statement/body/name/docs component differencing for supported declarations.
- Emit explicit unknowns and fallback tasks for unsupported syntax.
- Build only high-precision relations initially: declaration dependency, changed siblings, name
  family, and direct use of a newly changed declaration.

**Offline gate**

- Every changed range remains represented.
- Proof-only and statement-only fixtures classify correctly.
- Relation edges cite parser or repository artifacts and never rely on an LLM assertion alone.
- The smoke agenda routes all obligations assigned to active methods without PR-specific production
  rules: canonical API, wrapper composition, and naming are 3/3. The two proof-compression obligations
  and one structural rewrite remain explicit `method_gap` records until those methods are implemented;
  they are not routed through a generic fallback to manufacture 6/6 coverage.

### Phase 3: Canonical API discovery operator

**Status:** DONE

The first production slice is implemented in `operators/canonical_api.py` and frozen as
`dev-pilot-0.9.1-canonical-smoke`. It builds a temporally safe declaration index over the target
module and its direct imports, focuses retrieval on the largest locally reconstructed proposition,
records a complete top-20 ranking, suppresses already-used APIs, and constructs a replacement only
for a supported high-confidence operation shape. Generation reads no gold files.

On the frozen two-target smoke, `Metric.isSeparated_insert_of_notMem` ranks first for
`isCover_maximalSeparatedSet` with score 28 and is absent from the target. The control ranks its
already-used `Real.arctan_tan` first with score 19 and produces no transformation. The source
retrieval gate therefore passes. Local offline applicability remained explicitly `unavailable`
because the implementation environment did not expose `lake`. In the subsequent real smoke, each
adjudication agent independently invoked `lean_verify_edit` and successfully compiled its replacement
before requesting it. All three repetitions produced the correct issue and resolution match; all
three controls produced `no_request`. The pre-registered real gate therefore passed 3/3, exceeding
its 2/3 threshold.

This closes the canonical-API mechanism for the demonstrated insert/separation operation. It does
not establish repository-wide canonical API recall: generalization beyond this operation remains a
nine-PR pilot and temporal-holdout question. The smoke also exposed and fixed workspace-prefixed
`proposed_edit.path` values, which are now normalized and validated before task completion and again
during ingestion.

**Implement**

- Build a review-snapshot declaration index containing name, namespace, type shape, declaration kind,
  direct dependencies, and local usage examples.
- Retrieve by operation/type shape plus dependency neighborhood, then check applicability in the
  reviewed workspace.
- Construct candidate replacements with exact source declaration IDs and compile when an edit can be
  instantiated.
- Add method-specific negative controls where the current proof already uses the canonical API.

**Real smoke gate**

- Run only `isCover_maximalSeparatedSet` and one control target.
- The source-retrieval report must find `Metric.isSeparated_insert_of_notMem` without oracle text.
- At least two of three repetitions must produce the correct issue opportunity; controls produce no
  selected finding.
- Separately report retrieval, transformation, adjudication, and semantic outcomes.

### Phase 4: Naming contrast operator

**Status:** DONE

The production naming slice is implemented in `operators/naming_contrast.py` and frozen as
`dev-pilot-0.9.2-naming-smoke`. It extracts the outer declaration conclusion, distinguishes direct
left-hand semantic subjects from existential and other role-conditioned mentions, and computes a
complete naming population over the review-time base snapshot. Global token frequency is not used
as an independent rename signal.

For the `Set.encard` smoke, 7,409 review-base Mathlib files parse without failure. The declared
direct-subject population contains 91 theorem or lemma conclusions: 87 leaf names use an `encard_`
prefix, four contain `encard` under another meaningful name role, and none use `card_` or an unrelated
leaf name. `Metric.card_maximalSeparatedSet` is inferred as a high-confidence direct-subject conflict;
`Metric.encard_maximalSeparatedSet` has no repository or current-PR collision. The control
`Metric.exists_set_encard_eq_packingNumber` is correctly classified as role-conditioned and receives
no rename. Exact obligation scoping was added to the semantic judge because the positive declaration
also carries an unrelated proof-compression obligation.

The real smoke passed 3/3. Every positive adjudication requested the exact
`Metric.encard_maximalSeparatedSet` rename and matched both the frozen issue and resolution rubric;
every role-conditioned control returned `no_request` with no candidate. One positive candidate
mentioned `card_minimalCover` only as an explicitly out-of-scope follow-up. This did not affect the
gate, but later synthesis should suppress side suggestions that are not represented by the
opportunity's change IDs.

**Implement**

- Infer semantic subjects from declaration types and bodies, beginning with high-confidence heads such
  as `Set.encard`.
- Compute snapshot-scoped naming distributions over a declared comparison population.
- Return support counts, counterexamples, collision results, namespace scope, and uncertainty.
- Prohibit global raw-token frequency from independently supporting a rename.

**Real smoke gate**

- Run the `encard_maximalSeparatedSet` case plus a name-consistent control.
- The source population and every counted declaration are auditable.
- At least two of three repetitions produce the correct rename opportunity and no control finding.

### Phase 5: Wrapper and intra-PR composition operator

**Status:** DONE (offline and 3-repetition real smoke passed)

The production operator now recovers the exact review-base wrapper
`Metric.IsCover.coveringNumber_le_encard` and composes it with the current-PR cardinality, cover, and
subset witnesses for `coveringNumber_le_packingNumber`. The plan preserves all three related change
IDs even though the adjudication work unit contains only the target declaration. Its dependency delta
removes `iInf_le`, `iInf_pos`, `le_of_eq`, and `.trans`. The matched arctangent control exposes a
parallel changed sibling but correctly produces no composition.

The frozen workspace cannot run `lake`, so local compilation is recorded as `unavailable`, not
silently treated as success. The real agent must use `lean_verify`. The semantic gate is scoped to
the wrapper-composition obligation and keeps issue match separate from resolution match: the frozen
maintainer resolution also incorporates the independently discovered `encard_` rename and a
`by_cases!` normalization, neither of which is required for Phase 5 source-recovery success.

The real smoke passed 3/3. Every positive requested the same wrapper composition, issue-matched the
frozen obligation, and independently compiled its proposed edit with `lean_verify_edit`; every
parallel-proof control returned `no_request`. Resolution recall was 0/3 exactly because the bounded
operator retained `card_maximalSeparatedSet` and ordinary `by_cases` rather than synthesizing the
separate Phase 4 rename and the maintainer's `by_cases!` normalization. This confirms reliable issue
recovery for the smoke mechanism while leaving cross-opportunity resolution synthesis unproven.

**Implement**

- Use PR relations to detect proofs that reconstruct behavior exposed by a repository or newly changed
  sibling API.
- Generate a composition sketch, compile it, and measure removed implementation dependencies or proof
  steps.
- Preserve all related change IDs and prevent physical work-unit boundaries from limiting scope.

**Real smoke gate**

- Run `coveringNumber_le_packingNumber` plus a parallel-proof control.
- The operator must automatically retrieve `IsCover.coveringNumber_le_encard` and relevant changed
  siblings.
- At least two of three repetitions issue-match; resolution recall and compilation are reported
  separately; no control finding survives.

### Phase 6: Historical adopted-transformation store

**Status:** DEFERRED after the offline source-coverage gate; store and retriever implemented

The Phase 6 store materializes 113 historical review situations as separately hashed trigger,
request, resolution, and join records. Ninety-nine triggers are grounded to review-time code and
snapshots. The corpus retains 52 adopted, 16 partially adopted, 32 dropped, and 13 unknown outcomes,
with method-specific trigger features and target-PR/post-cutoff exclusion. Gold-free queries are
frozen for the two proof-compression sites and the structural-rewrite site.

The pre-registered offline gate failed: useful adopted-transformation source recall@5 is 0/2 for
proof compression and 0/1 for structural rewrite. This is source absence rather than a top-k ranking
miss. Across the complete 8,161-event ledger, the only two temporally eligible `grind` mentions are
from one discussion of a proof that already used `grind`; neither records adoption of the requested
rewrite. There are no eligible empty-branch-to-`rfl` requests outside target PR 33098. The target-PR
`rfl` adoption, later `grind` comments, and non-adopted alternatives are correctly excluded or
retained as anti-precedents.

Do not run the paid real smoke and do not substitute the same-PR or post-cutoff examples. Phase 6 is
deliberately not on the critical path for Phases 7--10. It can resume after a broader pre-cutoff
corpus supplies at least one adopted source for each method family and at least two of the three
queries have a useful source in the top five.

**Implement**

- Materialize temporally prior review situations as separately hashed trigger, request, and adopted
  resolution objects.
- Index by method-specific trigger features, not generic comment similarity.
- Store reviewer, timestamp, outcome confidence, target snapshot, transfer features, and exceptions.
- Add stale, non-adopted, and superficially similar anti-precedents.
- Query this store only after a technically valid proof-compression or structural opportunity exists.

**Offline gate**

- On hidden gold-site queries, measure adopted-transformation hit@k separately for proof compression
  and structural rewrites.
- Stop if useful source recall is below a pre-registered threshold; do not compensate with larger
  prompts.

**Real smoke gate**

- Run the two `grind` cases and the `rfl` branch with matched alternatives.
- Compare technical evidence only versus technical plus historical selection evidence.
- Success requires improved request frequency without increased control publication. Compilation-only
  rejection is an expected baseline, not a failure of the harness.

### Phase 7: Three-axis adjudication and selective redundancy

**Status:** DONE (offline deterministic replay and two-call live redundancy gates passed)

Phase 7 adds separate `technical-assessment1`, `norm-assessment1`, and
`worthiness-decision1` records, linked by an `adjudication-bundle1`. Factual premises are represented
as structured cited claims; validation rejects evidence outside the source opportunity or factual
premises not covered by those claims. Deterministic policies cover direct failures, canonical APIs,
wrapper composition, strong naming contrasts, proof compression, repository-pattern evidence, and
negative family controls.

Selective redundancy is represented explicitly by `redundancy-request1`, independent adjudication
votes, and a consensus record. Only low-confidence or conflicting cases take this route, assessors
must be distinct, and any disagreement resolves to `defer`.

Opportunity-task submission now recompiles every supplied concrete edit before accepting the
terminal result. A successful check is persisted as an `adjudication-verification-artifact1` and
added to the adjudication's evidence lineage. Redundancy ingestion rejects a technically valid
request without this artifact, so a model rationale cannot stand in for mechanical evidence.

The frozen replay covers six production opportunities from Phases 3--5 and all ten oracle-evidence
opportunities. All five controls remain `no_request`; syntax-only and compilation-only proof
alternatives do not publish; the oracle wrapper and naming opportunities and the production naming
opportunity are the only requests. Request precision on both diagnostic contrasts remains 1.0. The
production canonical and wrapper opportunities route to selective redundancy because their frozen
applicability artifacts state that Lean was unavailable; their successful later real runs are not
silently imported as release evidence. Rebuilding the complete adjudication artifact set is
byte-stable.

The two-call live smoke over the canonical opportunity passed. Both independent assessors produced a
valid advisory request backed by a successful Lean verification artifact, and ingestion resolved the
votes to unanimous `request`. One response was emitted during the brief source-list alias bug; its
self-reference was removed only after the corrected payload reproduced the artifact's original ID
and SHA. The migration is therefore hash-checked rather than a permissive sanitizer.

Gate artifacts live under
`results/pr_review_v4/audits/phase7-adjudication-gate-0.1.1/`.

**Implement**

- Split technical, norm, and worthiness outputs and enforce their invariants.
- Encode deterministic policies for direct failures, canonical APIs, wrapper composition, and strong
  naming conventions.
- Add artifact-citation validation for every factual adjudication statement.
- Add a second adjudication only for low-confidence or conflicting ambiguous cases; disagreement
  defers.

**Gate**

- Replaying fixed evidence is byte-stable for deterministic policies.
- The five oracle-evidence controls remain `no_request`.
- Compiling minor proof alternatives do not publish without additional selection evidence.
- Candidate issue precision does not decline relative to the same discovered opportunity pool.

### Phase 8: PR-level synthesis

**Status:** DONE for deterministic synthesis; corrected verification-backed residual smoke ready

Phase 8 introduces explicit candidate-to-opportunity links and `synthesized-finding1` records. A
finding separately carries issue anchors, context-only dependencies, source candidates, source
opportunities, investigations, methods, and evidence artifacts. Same-action variants are merged;
same-action siblings group only across a high-confidence validated PR relation. Competing actions
require strict evidence dominance, while ties produce `defer_conflict`. The explicit finding budget
produces an auditable suppression decision rather than silently truncating output.

`synthesis-match-projection1` projects existing candidate-level semantic matches through the
many-to-one finding lineage. The real gate input includes the accepted canonical, naming, and wrapper
findings for PR 33098 plus PR 33438 as a control. All three issue-matched obligations survive
synthesis, the control has no finding, replay is byte-stable, and wrapper source dependencies remain
context rather than being promoted to issue locations.

The original residual novelty pass was a runnable two-PR diagnostic treatment. It received a compact
complete inventory, completed method outcomes, and accepted finding text, but no maintainer comments,
gold obligations, or post-review outcomes. Its terminal record is required even when it abstains. The
failed release is `inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.0`; synthesis gate
artifacts are under `results/pr_review_v4/audits/phase8-synthesis-gate-0.1.0/`.

The first residual smoke exposed a verification-contract failure: agents used scratch-only
`lean_verify` against `target/...`, received errors, and still submitted three unsupported blocking
claims. Version `phase8-residual-review/2` therefore distinguishes the tools explicitly and enforces
verification at terminal submission. `lean_verify` remains a scratch-code exploration tool;
submission independently uses the reviewed-file compilation path underlying `lean_verify_edit` to
compile the baseline and every structured proposed edit. Mechanically checkable residual families
must provide an edit, failed edits cannot terminate successfully, and ingestion requires the two
persisted compile artifacts. The corrected immutable smoke release is
`inputs/pr_review_v4/treatments/phase8-residual-smoke-0.1.1`.

**Implement**

- Group same-action sibling opportunities using validated PR relations.
- Deduplicate exact candidates before selection.
- Resolve competing fixes by evidence dominance or defer on conflict.
- Preserve atomic obligation visibility in evaluation even when one finding spans multiple anchors.
- Add the residual open-review pass after structured methods complete.

**Real smoke gate**

- Use one multi-anchor PR and one control PR.
- No supported issue match is lost in synthesis.
- No exact duplicate or contradictory pair is published.
- Grouped findings retain all source opportunity and evidence lineage.

### Phase 9: Fixed-orchestration smoke

**Status:** DONE (three-repetition fixed and call-matched comparison complete)

**Implement**

- Execute all accepted methods as one fixed pipeline on PR 33098 and PR 33438.
- Run three repetitions only for the remaining LLM transformation/adjudication stages.
- Compare with the frozen holistic baseline and a call-matched baseline union, reporting actual
  dollar cost separately.

The immutable execution release is
`inputs/pr_review_v4/releases/dev-pilot-0.9.4-fixed-smoke`. It combines all six production
opportunities from canonical API, naming contrast, and wrapper composition. Four routes terminate
deterministically: one supported naming request and three `no_request` controls. Only the positive
canonical and wrapper opportunities reach the model, so each repetition costs two calls. Both
bounded methods now require a structured edit at terminal submission and independently compile it
through the reviewed-file verification path.

The execution release remains gold-free. It freezes two original source work units and their nine
change IDs; a separate evaluation command maps them to the current eight eligible obligations. The
report also attributes misses over all 14 eligible PR 33098 obligations, so method coverage outside
the matched scope remains visible rather than disappearing from the denominator.

The call-matched holistic union reuses the existing PR 33098 sample for
`wu:b017b7314c4bea62d8f968c3` and runs only the missing
`wu:9354e29b0912d17d60b1d3e1` once per repetition. This gives two positive holistic calls against
two bounded fixed-pipeline calls. Existing PR 33438 responses remain the control comparison.

Because the user explicitly chose broader evidence before another development-set method addition,
Phase 9 now separates implementation readiness from efficacy. Successful orchestration, complete
lineage, control safety, and stage attribution gate expansion. Recall and precision deltas against
the cost-matched union are reported descriptively and must not trigger PR-33098-specific tuning
before the broader pilot.

**Pre-registered gate**

- all scheduled tasks terminate with artifact-backed records;
- source-retrieval and transformation outcomes are reported for all eight matched-scope and all 14
  full-PR obligations;
- mean issue and resolution recall are compared with the cost-matched reference without becoming a
  development-only expansion blocker;
- per-obligation issue-hit frequencies are reported across all three repetitions;
- deterministic opportunity artifacts are identical across repetitions;
- zero selected control findings and no material precision decline;
- the report names exactly which stage caused every miss.

Failure at this gate leads to a component decision, not a larger prompt:

- source misses revise the specific index or query;
- construction misses revise the specific operator;
- worthiness misses motivate norm evidence or an explicit irreducible-preference classification;
- synthesis misses revise graph/grouping logic;
- broad control pressure pauses expansion.

### Phase 10: Medium-tier pilot and temporal holdout decision

**Status:** TODO

The implementation contract has been expanded to the 16-PR medium tier in
`pr-review-v4-phase10-medium-executor-and-census-design.md`. That addendum defines the generic
opportunity executor, separates broad methods from narrow implementation capabilities, and specifies
the gold-side C0-C6 coverage census required before a paid medium run.

**Implement**

- Freeze method registry, implementation capabilities, policies, and thresholds before the medium
  pilot.
- Run three repetitions on the smallest diverse subset first, then the complete 16 PRs only if the
  smoke gate holds.
- Freeze a temporal holdout before adding method rules from further errors.

**Gate**

- gains appear in more than the development PR and more than one method;
- method-level precision and stability remain acceptable;
- cost per recovered obligation improves over cost-matched repeated holistic review;
- holdout results are reported without tuning.

## 8. Module plan

Reuse stable v4 I/O, hashing, runner, workspace, evidence, semantic judge, and selection modules.
Add narrow modules rather than another parallel pipeline:

```text
src/mathlib_review/
  modification_inventory.py
  pr_relations.py
  method_registry.py
  investigations.py
  opportunities.py
  opportunity_evidence.py
  norm_records.py
  adjudication.py
  synthesis.py
  evaluate_opportunities.py
  operators/
    canonical_api.py
    naming_contrast.py
    wrapper_composition.py
    historical_transformations.py

inputs/pr_review_v4/treatments/systematic-opportunities-v1/
  methods.json
  policies.json

tests/datasets/
  test_pr_review_v4_inventory.py
  test_pr_review_v4_methods.py
  test_pr_review_v4_opportunity_operators.py
  test_pr_review_v4_adjudication.py
  test_pr_review_v4_synthesis.py
```

The existing `oracle_opportunities.py` and `oracle_evidence_probe.py` remain diagnostic fixtures. Their
hand-authored alternatives must not become production operator data.

## 9. Regression invariants

1. Gold poisoning cannot change inventory, schedule, retrieval, opportunities, prompts, or findings.
2. Every source and norm artifact is temporally valid at review start and excludes the target PR.
3. Every expected investigation has exactly one terminal record in a sealed run.
4. A successful check cannot close a broader investigation.
5. A compiling edit cannot by itself establish review-worthiness.
6. Token overlap or one pattern example cannot independently establish naming or duplication support.
7. Candidates remain grounded in real changed subjects; unchanged declarations are evidence anchors.
8. Cross-target candidates remain within the same episode and cite validated relations.
9. Technical diagnosis and repair validity remain separate.
10. Issue and resolution matching remain separate.
11. Synthesis cannot create unsupported claims or erase lineage.
12. Oracle-development opportunities are rejected by production sealing.
13. Preview and execution prompts are byte-identical and record omissions.
14. Comparisons report calls, tokens, cost, and stochastic repetitions.
15. Approved/no-comment controls are never described as proof that all criticism is invalid.

## 10. Stop conditions

Pause or reject the direction if any of the following occurs:

- automatic source retrieval cannot reproduce the oracle API/naming/wrapper sources on the smoke;
- gains disappear against a cost-matched union of holistic samples;
- increased recall comes mainly from more findings and reduces issue precision materially;
- opportunity records are complete but operator artifacts show little real investigation;
- historical transformation retrieval has low hit@k or transfers stale preferences;
- the method registry accumulates PR-specific exceptions;
- the pipeline works only on PR 33098 after the nine-PR pilot;
- synthesis repeatedly suppresses supported distinct obligations;
- controls reveal that strong-looking evidence routinely legitimizes unrequested criticisms.

## 11. Immediate implementation sequence

The shortest evidence-preserving path is:

1. Freeze the baseline and claim matrix.
2. Land contracts, sealing, and a minimal registry.
3. Build coarse inventory and high-precision PR relations.
4. Implement and smoke the canonical API operator.
5. Implement and smoke naming contrast.
6. Implement and smoke wrapper composition.
7. Only then build adopted historical transformations for proof/syntax preferences.
8. Split adjudication and add selective redundancy.
9. Add PR-level synthesis.
10. Run the fixed-orchestration three-repetition smoke and compare it with a cost-matched baseline.
11. Expand to the nine-PR pilot only after the pre-registered gate passes.

This ordering deliberately implements the three mechanisms with positive oracle evidence before the
preference classes whose missing signal is still only suspected.

## 12. Commands to run

No external command is required for this design-only round. Each implementation phase must end with:

1. a local regression command;
2. a dry-run or artifact preview command;
3. the smallest real paid smoke command for that method;
4. deterministic post-processing and semantic-judge commands;
5. a verdict artifact that decides whether the next phase is authorized.

Exact commands should be added to the phase verdict when its implementation exists; inventing them
before module and config names are fixed would make this document less reproducible, not more.
