# Adversarial review of the task/data refactor

2026-10-22. **Author-conducted adversarial pass, followed by Claude's independent review.**
The first section records the author's pass on v0.1/v0.2 of the
[design](task-dataflow-refactor-design-2026-10-22.md). Claude's review and later correction
are preserved below. Current decisions appear in the
[v0.3 disposition](task-dataflow-refactor-design-2026-10-22.md#20-disposition-of-claudes-review),
including reuse of existing sampling/persistence and the priority of maintainer inspection.
“Addressed” in the original pass means the specification was amended, not that code exists
or works. Neither review establishes runtime correctness or approves a broad implementation.

The pass used concrete counterexamples and current APE contracts. Its strongest conclusion
is that a small typed-data boundary is promising, while general durable Python workflows
and comprehensive automatic reuse would be substantially more work than the initial
proposal acknowledged. Those features should not enter the first implementation slice.

## Review method and evidence

For each proposed guarantee, construct an execution that still satisfies the apparent
type/signature but gives the wrong scientific or operational conclusion. Trace the
expected data/occurrence keys, outputs and outcomes. Check relevant current code where
the counterexample depends on an existing implementation detail.

Inspected particularly:

- `src/ape/orchestration/orchestrator.py`: task storage and completed-result lookup are
  keyed by `task.data.global_index`; sample slots live beneath that key.
- `src/ape/tasks/base.py`: data hashing, result contract, config resolution and default
  highest-score aggregation.
- `src/ape/orchestration/persistence.py`: historical result loading can fall back to
  `BaseTaskResult` after task-specific validation fails.
- `src/ape/orchestration/models.py`: outcomes, samples, attempts and `ChildRun` distinguish
  persisted results from usable typed child outputs.
- `src/mathlib_review/judge/semantic_judge.py`: planned-pair reconciliation and source checks.
- `src/mathlib_review/schema/runs.py`: existing command-pipeline restriction to one run.

These are source inspections and specification counterexamples. They are not runtime
fault-injection tests, new model evaluations or proof that the new design is implemented.

## A1 — Identical inputs can collapse independent observations

**Severity:** blocks an implementation claiming independent repetitions.

**Counterexample:** one program invokes the same reviewer twice on identical episode and
evidence data. Both calls have the same task input hash. If mapped to the same orchestrator
task directory/sample slot, the second call resumes or reads the first. The report counts
two reviews even though only one was generated. Conversely, deduplicating identical output
bytes can erase two legitimately separate observations.

**Current evidence:** `_prepare_sample_jobs` uses `global_index` to locate task storage and
skips new work when an aggregate result exists. Changing only a display name does not
establish a new sample.

**Correction after review:** existing `sample_count` already schedules repeated samples,
and `run_subtasks` rejects duplicate-data specs within a batch. This counterexample is an
obligation on new composition adapters, not a claim that the current nested API silently
accepts those specs. Reuse existing scopes/sample slots; growing an aggregated task's
sample count remains a separate engine limit.

**Required change:** map `(program scope, explicit call key, case, replicate)` to a distinct
execution address/sample slot. Keep task semantic identity and output content identity
separate. A new occurrence must resolve to a new slot or explicit isolated execution scope;
adding a provenance label after execution is insufficient.

**Acceptance:** two equal-input fresh calls schedule two distinct sample addresses; resume
returns the original occurrence; identical products remain two production occurrences.
Addressed in design §§6 and 9. The engine mapping remains an implementation obligation.

## A2 — Ordinary Python does not provide durable program control

**Severity:** blocks claims of general program resume; not a blocker to a sequential pilot.

**Counterexample:** a program decides whether to retrieve more evidence by reading a live
directory or clock. After a crash it re-enters, chooses a different branch, and reuses a
call key for different work. Or two iterations of a dynamic agent use the same key, causing
an earlier output to stand in for a later request.

**Required change:** explicit unique call keys and a sealed program/request identity;
persist branch decisions that matter to continuation. Deterministic branches may be
recomputed only from the same recorded data. Changed branch inputs must conflict or fork
the scope. External I/O in program control must enter through recorded inputs or explicit
effect boundaries. Do not promise to checkpoint arbitrary closures or Python state.

**Acceptance:** after interruption, re-entry follows the recorded branch or refuses the
changed request; loop iterations have distinct keys. If this cannot remain small, use
manual invocation-boundary continuation or evaluate an established workflow engine.
Addressed in §9; broader durable workflow support remains deferred.

## A3 — Bytes and receipts can disagree after a crash

**Severity:** blocks trusting committed output/reuse.

**Counterexample:** the provider returned a finding, the payload was written, and the
process died before recording production/completion. A retry pays again or an output-file
existence check reports success despite a missing outcome. The inverse occurs if a receipt
is committed before all nested payloads are durable. Concurrent writers can publish two
different products for one sample slot.

**Required change:** validate and write payloads first; atomically publish a per-sample
output binding through existing legal result/sample persistence; reconcile with the engine
outcome. A separate binding record or commit subsystem is not required by v0.3. Verify the
actual locking/write boundaries. Identical re-publication is idempotent; conflicting
publication fails. Artifacts
without a binding remain uncommitted, recoverable data. A committed binding with missing
payloads is corrupt/incomplete. Do not introduce a second authoritative execution status.

**Acceptance:** inject interruptions at each boundary and recover without silently losing
output or accepting contradictory bindings. A provider response lost before persistence
can still require paid re-execution; exactly-once provider work is not guaranteed and
unknown usage is not zero. Addressed in §9; fault-injection checks are required later.

## A4 — Correct types can still bind the wrong PR or code state

**Severity:** blocks safe cross-task composition.

**Counterexample:** an `EvidenceSet` from PR A is valid under its schema and is supplied to
PR B. Or a valid compile result concerns an earlier patch with another import list. Every
generic type check passes, but the evidence does not support the resulting claim.

**Required change:** domain input validation checks episode/revision/scope relations and
exact subject references. Technical checks bind patch, prerequisites, workspace and tool
context. Generic schema validation and provenance links are necessary but insufficient.
Reject incompatible bindings before a paid invocation where the mismatch is knowable.

**Acceptance:** same-shaped, wrong-episode evidence and stale patch checks are refused.
Addressed in §§4–5 and 10–11. Some source applicability remains a judgment, not an
automatically provable invariant.

## A5 — Provenance can contaminate the experiment it describes

**Severity:** blocks blinded or temporally isolated evaluation claims.

**Counterexample:** a common artifact manifest exposes reference files to generation;
`treatment/` names or source links reveal the condition to a judge; future maintainer
feedback enters a reconstruction source. A metadata `gold=false` flag does not prevent
the model reading mounted files or a native shell from reaching a shared store.

**Required change:** researcher provenance and model-visible projections are separate.
Runtime identities and hashes are stamped outside model submissions. Workspaces/tool
grants must enforce the declared view; native tools need their own checks. Unobservable or
unenforced access routes are recorded limitations, not certified isolation.

**Acceptance:** inspect actual delivered prompts/tool routes and attempt forbidden reads
in a fixture; blinded inputs omit condition cues while the researcher retains the seal.
Addressed in §§5 and 10. General prompt-injection resistance is not solved by this refactor.

## A6 — Reuse and missingness can create misleading performance and cost

**Severity:** blocks unqualified comparison claims.

**Counterexample:** only successful acquisitions reach review, inflating conditional
quality while failures vanish in a join. A costly sketch is reused across treatments and
charged to none. A policy tuned on this panel is compared with an old baseline on another
panel. Or 100 asks in one PR are presented as 100 independent replications.

**Required change:** explicit expected populations, join cardinalities, failure policies,
provenance/exposure and cost views. Record intrinsic production cost once, consumption
reuse without duplicate billed cost, and the acquisition cost required by the hypothetical
deployed system. Choose reporting groups/estimands in the study, not the scheduler.

**Acceptance:** failed rows remain visible; actual incurred cost and deployment/amortized
cost are separately reproducible; group-level comparisons retain panel membership.
Addressed in §§7 and 11. Causal interpretation still requires a controlled study.

## A7 — A normalized invocation can falsely endorse a synthetic legacy result

**Severity:** blocks the first adapter if overlooked.

**Counterexample:** historical loading falls back to a bare `BaseTaskResult` after domain
validation fails. A worker-generated failure result exists on disk and the task outcome
looks completed. An adapter equates `has_result` with a valid domain output and publishes
an empty/default `FindingSet`.

**Required change:** validate legal task-specific submission and output projection before
binding domain output. Retain malformed/synthetic results as diagnostics. Where outcome
semantics are wrong, fix the authoritative engine contract; do not create another local
status vocabulary as a workaround.

**Acceptance:** bare failure results and malformed task-specific payloads never become
valid output products; a legal empty finding submission does. Addressed in §§5–6.

## A8 — Generic records can turn into a second framework

**Severity:** unresolved design-cost objection; limit the first slice.

**Counterexample:** every two-line transformation needs a registry entry, an artifact type,
a receipt, a scheduler adapter and a generic `Program` class. The refactor replaces ad-hoc
scripts with more bookkeeping and still cannot express a new reviewer without hub edits.

**Simpler alternative:** existing typed Tasks/results plus a small output projection,
verified file references, expected-case manifests and ordinary Python composition. Use
existing outcomes and storage. Extract a richer generic API only after the two-program
demonstration shows repeated mechanics that it removes.

**Discrimination:** implement the evaluator handoff this way first. Count required shared
changes, retired active special cases and the effort to add one second program. Measure
artifact/orchestration overhead on realistic files. If the larger abstraction adds only
generic names, remove it. The design now makes this small implementation admissible;
the benefit of a richer framework remains unestablished.

## A9 — Streaming and useful partial work challenge one final output product

**Severity:** unresolved beyond the initial final-finding path.

**Counterexample:** an agent emits useful candidates incrementally and later pauses or
fails. A single terminal output can hide those candidates; treating provisional emissions
as final can inflate deployed quality or let incomplete verification pass.

**Required initial boundary:** checkpoint/provisional data may be retained under attempt
diagnostics; final consumers require an explicitly committed final product. A deliberate
incremental publication design needs its own finalization/withdrawal policy and can
materialize each accepted emission. Do not force it through a fake terminal success.

**Discrimination:** walk through an actual incremental-emission use case before adding
multiple independent output ports or streaming dataflow. Keep final serialized findings
as the first adopter. Addressed as a limitation in §§6 and 16; streaming semantics are
deferred, not solved.

## A10 — Better provenance does not create scientific progress

**Severity:** unresolved scientific limitation, not an infrastructure defect.

**Counterexample:** every task is typed and reproducible, but the acquisition intervention
still delivers irrelevant evidence, reviewers reject good alternatives, or evaluation
rewards historical imitation over useful requests. A workflow view shows all green nodes
and encourages another local tuning round without a better hypothesis.

**Required response:** reports separate plumbing completion, intermediate mechanism
demonstrations and fresh reviewer improvement. A study record names the intended contrast,
observed contrast, unresolved explanation and next discriminating test. Off-gold findings
need independent assessment. References and their induced judgments need challenge.

**Discrimination:** using the same output contracts, compare a solo program, an assisted
program and a diagnostic holding a relevant intermediate fixed. If the typed boundary does
not make the scientific ambiguity easier to isolate, revisit that boundary. The architecture
cannot guarantee novelty or replace domain research.

## Result and independent-review priorities

At the end of the author-conducted pass, the amended design was suitable for independent
criticism and a small implementation proposal. Claude's review follows, and the current
disposition is linked above. The principal unresolved questions from that initial pass were
are A8's abstraction cost, A9's eventual streaming contract, and whether A2's limited
continuation rules cover the near-term programs without a workflow runtime.

The initial independent-review questions were:

1. Is a simple output projection plus existing `ChildRun`/`TaskOutcome` already enough?
2. Can the proposed occurrence mapping actually coexist with content-keyed task storage?
3. Is the output-commit protocol precise enough and placed at the right engine boundary?
4. Which concrete reviewing design would require a substantially different data model?
5. Are we hiding fixed-pipeline assumptions in the canonical finding/evaluation contracts?
6. Which piece should be deleted from the proposed first slice to progress faster?

The [design's reviewer brief](task-dataflow-refactor-design-2026-10-22.md#17-brief-for-an-independent-reviewer)
contains the reading list and a self-contained review prompt.

## Independent review of the adversarial pass (Claude, 2026-10-22)

Checked against `develop` at `4695a1b1`. "Built" below means the code exists and a test pins
it; "spec" means only the design text was amended. Line references were read, not run.

| Finding | Counterexample holds? | Required change, after checking the tree | Severity after review |
|---|---|---|---|
| A1 identical inputs collapse | Yes for `global_index`. But `run_subtasks` refuses identical specs with a message saying why, and `sample_count` is the existing independent-sample primitive (`judgment.py` docstring: "sample_count > 1 gives repeated verdicts on the same pair for free") | Mostly built. Residual: a task with `task_result.json` is skipped by `_prepare_sample_jobs`, so an aggregated task cannot grow a sample without removing the aggregate, and `requeue_failed_samples` is the only path that does. Record that as the engine limit; do not design an address space. | low |
| A2 Python is not durable | Yes | Agreed. The conclusion, resume at invocation boundaries, is what `cli pipeline` already does at stage grain. Say so. | not a blocker |
| A3 bytes and receipt disagree after a crash | No instance in the record. The recorded inconsistency of this family is framework defect 4: a synthesised failure written and then `has_result=True` (`worker.py:674-697`) | Fix defect 4. The commit protocol is a solution to a hypothetical. | low; fold into defect 4 |
| A4 right type, wrong PR | Yes in principle | Partly built: `StageInput.require` hashes consumed artifacts; the judge refuses a source-hash mismatch. The episode-scope check on an `EvidenceSet` cannot exist because `EvidenceSet` does not. Build the check with the first consumer. | medium |
| A5 provenance contaminates | Yes | Already a rule and a test: the reviewer's run tree is gold-free (`judgment.py`), `test_prompt_contamination`, and the probes' leak audits (`questions.md`, "Do probe sessions and matchers stay inside their packets"). The symlink-search defect shows a declared capability certifies nothing; recorded on `route-search-symlinks`. | right as stated |
| A6 reuse and missingness mislead | Yes | Mostly built: `coverage_gaps`, the partial-run refusal, the denominator refusal. Residual: the cost of a shared producer attributed across treatments is a reporting column, not an object. | medium |
| A7 a synthetic result endorsed | Yes at the orchestrator's aggregate path (`orchestrator.py:459-460`) | Built at the `ChildRun` boundary: `succeeded` is `result is not None`, and the failure sentence goes to `error`. The other half is defect 4. | low |
| A8 a second framework | Yes, and under-weighted | Add the October 6 evidence: half of thread width is shared-machinery fixes that no architecture removes; the September layer has one commit since October 6; October 6 §3 rejected "no code in `results/`". Make the discrimination test the gate for everything past Slice A. | the principal objection |
| A9 streaming | Yes | Defer, as stated. Precedent: `coordinated-emission` in `dead-ends.md`, a schema's existence is not model use. | deferred |
| A10 provenance is not progress | Yes | This is the user's standing rule: a labelling-only session is not a contribution; design over diagnosis. Name the next experiment and ask which slice it needs. | the frame for the whole design |

### Findings the author-conducted pass did not raise

- **A11 The record was not consulted.** October 6 §3 (rejected proposals), §4.6 (the stage as
  the probe unit, unbuilt and waiting for the next hand-launched probe), §11 (what was built and
  its thresholds). The design re-states step 5's problem with no reference to step 5's plan.
- **A12 No cost and no merge surface.** Two sessions share the working tree; 44 worktrees exist
  and several are unmerged; October 6 gated hub steps on in-flight branches merging first.
- **A13 "Addressed in §X" reads as built.** Five of the ten findings are partly or wholly built
  already (A1, A4, A5, A6, A7). The design should carry a built / spec / not-built column.
- **A14 E1 is a research decision presented as refactor work.** Whether raw asks and atomic
  obligations are one instrument is settled by reading aligned examples, not by a type.
- **A15 The pass shares its author's priors.** The user's rule is independent reviewers. This
  appendix is one; a second, by a different model, would be in the spirit.
- **A16 The next experiment is not named.** `docs/todo/review-as-demonstrated-change.md` is the
  thread on record. Sized against it, the slice this design must deliver is O1, a result-side
  field for unbuilt concerns with their failed attempts, and the E1 decision.

### The six priorities, answered

1. Yes. A `product()` projection plus `ChildRun` and `TaskOutcome` is enough for Slice A.
   Demonstrate it before anything else.
2. Yes, through sample slots. The one residual is growing an aggregated task.
3. Not needed. Fix defect 4.
4. The demonstrated-change design: a finding carrying a verified construction, its compile
   result and its failed attempts. `filing_contract` has the types; the new thing is a
   result-side field, not a framework object.
5. Two. The final-finding contract is request-shaped (`CandidateClaim`) and the issue judge
   does not credit questions, while the matcher gained a question form on 2026-10-13. And one
   finding is one target, so a coordinated edit does not fit (the `coordinated-emission` dead
   end). The demonstrated-change design is suggestion-shaped and fits the first.
6. Delete from the first slice: the program API and `ctx`, the `Invocation` type, the commit
   protocol, the collection-snapshot type, the `ArtifactRef` move. Keep: the product
   projection, F1, defect 4, O1, the E1 decision.

### Correction, after the user's question (2026-10-22, later the same day)

- **A14 is withdrawn in its emphasis.** E1 is a decision, and it is the refactor's most
  valuable step; it needs code to stick (a registered matcher Task with a versioned rubric in
  `src/`). Calling it "research, not refactor" read as "not urgent", which is wrong.
- **A17 The friction the design exists for is not named with its evidence.** Neither the
  design nor this pass states what a researcher cannot currently answer. Checked in the tree:
  two live instruments with no declared primary (judge in `src/`, versioned; matcher rubric
  imported by the kernel from a probe directory, `analysis/probes.py:782`; 14 probes on the
  matcher against 4 on the judge since 2026-09-29; 11 rubric copies and variants under
  `results/`); reach figures that compare only within one of seven seals; briefs and context
  files addressed by path and read at execution (`solo.py:231-357`), whose bytes enter no
  identity and refuse no resume; the Claude Code route's packet folder and undisclosed system
  prompt outside the orchestrator; and each probe's chain of gate scripts, sessions, seals and
  readers described only in its own protocol. A design that opened with these four facts and
  their counts would have been sized correctly from the start. See the design's §19.8 for the
  revised slice.
