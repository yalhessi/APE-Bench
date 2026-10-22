# Independent review of the first task/dataflow refactor

2026-10-22. Reviewed `dataflow-refactor@768e24b194fd80c739ddf5f889f37e993b0d6db1`,
against `4695a1b1`, in `.claude/worktrees/dataflow-refactor`. This reviews the
[implementation record](../../.claude/worktrees/dataflow-refactor/docs/research/task-dataflow-refactor-implementation-2026-10-22.md)
against the implementation and offline behavior. It does not propose the next architecture.

**Current disposition: accepted for the first refactor's implementation/review scope at
`dataflow-refactor@e13343c8`, pending landing.** The four correctness findings are resolved, the
saved-data handoff and second consumer have been checked, and both task types have completed live
on ape_agent and Claude Code. The final independent closure assessment below records the evidence,
remaining integration work and separately scoped follow-ups. The original assessment and earlier
closure lists are retained as the history of the review.

**Original assessment at `768e24b1`: useful infrastructure, with four correctness findings to resolve before relying on
the new paths for research results. Adoption is partial.** The changes establish real common
execution and inspection capabilities. They do not yet justify marking the complete transformation
as accepted: independent runs can collide, cached results can acquire false execution provenance,
and one realistic interruption still loses a successful task's published result.

All four findings below were reproduced locally without a model. None requires an AST, a new
scheduler, or a larger artifact hierarchy to fix.

## Findings

### 1. [P1] Separate session executions overwrite each other's exported output bytes

Location: worktree `src/mathlib_review/analysis/sessions.py:114-125`, particularly the output path
at line 120. Both `run_sessions` and `import_session_outputs` use this writer.

The output path contains only `(packet_id, replicate, output_name)` beneath a plan directory. The
indexes distinguish run/import names, but their files do not. Running the same plan twice, comparing
two routes, or importing a second externally produced answer replaces the first execution's files.
The first index keeps its original digest and now points to the second execution's content.

Reproduction through the public import API:

1. Make one session plan with one packet and declared `out.txt`.
2. Import `out.txt = "A output"` under name `run_A`.
3. Import `out.txt = "B output"` under name `run_B` against the same plan.
4. Read both rows with `session_outputs` and inspect the first row's output path and digest.

Observed:

```text
SESSION_IMPORTS 2
SAME_OUTPUT_PATH True
FIRST_DIGEST_STILL_VALID False
FIRST_OUTPUT_NOW B output
```

This is particularly consequential for the convention/reconstruction workflow: a context-building
consumer reads these paths, so selecting the older acquisition record can silently supply the newer
acquisition's text. Original task records may still permit recovery for Task-produced outputs;
the exported record itself is already inconsistent, and imports do not necessarily have that backup.

Suggested correction: namespace stored values by their producing run/import as well as sample,
or store the bytes by content digest and have each producer's index refer to those values. Repeated
exports of one observation should be idempotent. Different observations must retain their own
values, including when their values happen to be identical. Verify the digest when consuming an
exported value.

Acceptance: two executions and a task/import pair against one plan retain all original bytes;
re-exporting either one cannot change the other's content or invalidate its recorded digest.

### 2. [P1] Matching reports merge different runs into one supposed replicate

Location: worktree `src/mathlib_review/analysis/matching.py:401-419`, particularly line 406;
`verdict_rows` reads every run/import index in the measurement directory.

The grouping key is `origin:replicate`. It omits the producing run or import, although each run
numbers its samples from one. Consequently, running the same plan under two run names does not
preserve two separate sets of observations.

There are two observable failure modes:

- Two complete runs produce duplicate ask rows inside each supposed replicate. Reports flag the
  duplicates as forensic, but cannot independently select the runs through the replicate selector.
- Two incomplete runs with complementary successful batches produce a complete-looking replicate.
  Their coverage gaps disappear when merged, even though neither run completed that measurement.

The second case was reproduced with the real orchestrator and persisted samples. A two-batch,
two-replicate plan had `run_A` succeed only on `b1` and `run_B` succeed only on `b2`. Failed samples
had no remaining retries. No model was invoked. The report returned:

```text
run_A actual successful batches ['b1']
run_B actual successful batches ['b2']
COMBINED_COMPLETE {'task:1': True, 'task:2': True}
COMBINED_FORENSIC False
COMBINED_SOURCE_RUNS {'task:1': ['run_A', 'run_B'],
                      'task:2': ['run_A', 'run_B']}
```

The locators still expose the mixture to a careful reader. The completeness judgment and the
replicate identity nevertheless assert something stronger than either execution established.
With different executor configurations, one supposed replicate can also mix measurement policies.

Suggested correction: carry a producer identity through verdict loading, grouping, selection and
trace output. A replicate belongs to `(producer, sample_index)`; batch rows merge only within that
observation. Coverage and expected repetition counts should be evaluated for a selected producer
or an explicitly declared set of observations. Combining partial runs, if useful, should be an
explicit analysis operation with an account of the contributing observations.

Acceptance: complementary failed runs remain incomplete separately; complete runs remain separately
selectable; two separately named imports using replicate `1` do not collide; resuming one run
updates its own observations without minting independent repetitions.

### 3. [P1] Resume can relabel cached measurements with a model that never produced them

Location: worktree `src/mathlib_review/analysis/matching.py:249-270` and `274-299`;
the same pattern occurs in `analysis/sessions.py:151-170`.

The run binding checks the plan but omits execution settings. Task identities for these paths
contain their input payload, so changing the scaffold's model while keeping the plan and run name
does not invalidate already completed tasks. The orchestrator skips those tasks, and collection
stamps their cached outputs with `executor_of(scaffold)` from the current invocation.

Reproduction: seed legal saved matching samples under `model_A`, collect them through
`run_matching`, then call `run_matching` again with the same plan and run name but `model_B`.
The cached verdicts returned with:

```text
RESUME_CACHED_VERDICT_EXECUTOR model_B
```

There was no new model execution. If only some tasks were complete, the resumed run could instead
contain results from both configurations while labelling all of them with the current one. The
orchestrator also writes its current config at run start, so that file alone does not recover
which configuration produced an older sample.

Suggested correction: distinguish the input plan from the effective execution configuration.
Either reject changes to semantic execution settings within one producer, or retain the producing
configuration per observation/attempt and make any mixture explicit. Read historical executor
provenance from the producing record. Changes to operational ceilings can still be supported as
resume operations. A changed model, prompt-affecting setting, tool interface or scaffold must not
silently inherit completed work under a new attribution.

This does not require deterministic outputs or sealing every value. It requires an honest account
of the execution that produced a value.

Acceptance: a changed-model resume either fails before reuse or preserves the old observations'
executor identities while recording any newly executed observations separately; an ordinary
budget-only resume keeps working. Check both matching and packet-session paths.

### 4. [P1] A previous outcome file can prevent recovery of a newly successful sample

Location: worktree `src/ape/orchestration/orchestrator.py:192-207`, particularly lines 203-204.

Reconciliation skips a task when `task_outcome.json` exists and no aggregation claim remains.
An outcome can describe an earlier pause/failure, however. Resuming that task does not remove the
old outcome before execution. If the resumed sample succeeds and the process dies after saving
`sample.json` but before claiming publication, the next reconciliation sees the old outcome and
skips aggregation. Job preparation then sees the successful sample and schedules no work.
The task's result remains unpublished indefinitely.

Reproduction using the real orchestrator:

1. Persist a sample paused at its five-turn ceiling and run reconciliation with that ceiling.
   This writes an outcome and no result.
2. Raise the ceiling to ten. Persist a second, successful attempt, representing a resumed worker
   killed immediately after its sample save and before aggregation.
3. Resume the same orchestrator.

Observed:

```text
FIRST_RESULTS 0 OUTCOME failed
RESUMED_SUCCESSFUL_SAMPLE success
RESUMED_RESULTS 0 RECOVERED []
HAS_TASK_RESULT False
RETAINED_OUTCOME failed
```

The first outcome's `failed` classification is the implementation's current behavior for this
fixture; the finding is that an old outcome blocks publication and remains stale after success.
The new recovery tests cover samples without an outcome and stale claim files, but not this
previous-outcome case.

Suggested correction: treat outcomes as derived from the current saved samples. The existence of
an outcome does not prove current publication is complete. Reconcile successful terminal samples
when their result is absent, and refresh outcomes whose underlying samples have advanced. Apply
the same consistency check when a result exists beside an older outcome.

Acceptance: interruption after a resumed sample save publishes the result and refreshes the outcome
on the next start, with and without a stale claim; completed/failure counts and usage agree with
the recovered samples; no model executes during recovery.

## What the refactor has achieved

Several changes are worth retaining on their own merits:

- One strict configuration resolver, including concrete Task-config serialization across worker
  reconstruction, fixes settings that previously did not reliably take effect. Explicit child
  configuration also makes inheritance easier to reason about. The change to lead CLI overrides
  needs to remain visible to users of that path.
- Separating an unsuccessful execution outcome from a legal submitted result is a substantive
  improvement. Retaining attempt exceptions and marking unknown usage directly addresses failures
  in the old accounting rather than adding a second execution system.
- `packet_session` captures a recurring operation that previously lived outside APE. Making packet
  input bytes Task data and validating declared outputs is a useful general operation.
- `sample_products` gives consumers a common way to distinguish legal sample outputs, missing work
  and failed attempts. Its current consumers are the new session and matching collectors; it has
  not replaced every existing result reader.
- Moving raw-ask matching into a registered Task and giving its rubric a domain-owned implementation
  is a real consolidation. Distinguishing transport/protocol versions and checking historical
  arithmetic offline are appropriate. The atomic-obligation judge remains a distinct instrument
  because it answers a distinct question.
- Input snapshots, digest checks and shared trace/compare commands give maintainers useful views
  that previously required a probe author's explanation. Their presence is valuable even though
  the findings above prevent treating all provenance and recovery guarantees as established.

The interface choices are largely reasonable for this bounded stage. In particular, a generic
folder-session Task is supported by recurring uses already present in the project. The findings
do not motivate replacing it with another execution abstraction.

## Where the implementation record overstates completion

The record is candid about many remaining gaps, but its acceptance table marks some broader
properties as “Met” on the strength of narrower fixtures.

| Claim | Evidence currently available | Review assessment |
|---|---|---|
| Independent repetitions remain identifiable | Distinct samples within one run survive | Partial: separate runs/imports collide in session storage and matcher grouping |
| Interrupted publication recovers consistently | Fresh sample/result and stale-claim fixtures pass | Partial: recovery with a previous outcome fails |
| Execution provenance identifies what ran | Collector records the invocation's configured executor | Partial: a resume can misattribute cached results |
| Two current consumers use shared composition | Offline tests exercise a reconstruction-shaped chain and demonstrated-change-shaped findings | Interface exercised; active studies still need integration |
| Shared inspection reaches the exact output and inputs | Stored blind inputs, input snapshots, task/import locators and trace commands exist | Useful capability; exported values and executor attribution need the corrections above |
| Replacement removes the bespoke active lifecycle | Shared helpers and new CLI paths exist; old scripts and branch integrations are named gaps | Migration remains open; adding the supported route has not retired the competing active routes |

Offline fixtures are appropriate here: the design explicitly reserves model generation and semantic
judging for the user. They prove transport and composition properties. They cannot establish a
successful subscription-route launch, equivalence between matching protocols, or adoption by an
active research workflow. Those should remain distinct completion statements.

The branch changes 56 files: 5,705 insertions and 258 deletions. Within `src/`, it adds 3,358 lines
and removes 247, a net increase of 3,111. Tests contribute another net 1,862 lines. It is an additive
first migration, and the codebase is larger at this point. Whether that investment reduces
maintenance depends on migrating the recurring consumers and retiring their duplicated mechanics.

## A bounded acceptance path

1. Fix recovery independently in APE, with the prior-outcome interruption regression. This can be
   reviewed separately from changes to research schemas or matching policy.
2. Make producer identity consistent across stored session values, matching verdict grouping and
   execution attribution. Findings 1-3 are related aspects of this boundary; fix them together or
   keep their shared identity convention explicit. Existing rows and locators are sufficient
   places to express it; a new general framework is not a prerequisite.
3. Re-run the offline checks, including cross-run, cross-import and changed-executor cases. Preserve
   the existing historical-report parity checks.
4. Migrate one complete active chain, then the second consumer: acquisition -> context -> reviewer
   -> matching -> report/trace. Use saved data for the local integration work. Record the remaining
   manual launch/calibration commands for the user. A second acquisition or route should compose
   without introducing another private launcher, result reader or matcher.
5. Update the implementation record to distinguish built, offline-verified, integrated and
   empirically calibrated. Retirement of active bespoke paths should have a specific owner and
   completion point, as the design already requires.

The relevant unifying rule is small: a plan describes intended inputs; a run records an execution
policy; a sample identifies an observation; attempts record its execution history; a product holds
the resulting value. Equal values can belong to different observations. A resume continues an
observation. Different observations cannot overwrite each other or be merged merely because their
local sample numbers match. These are direct requirements of the current workflows.

## Validation and limits

Two existing-test passes completed on the reviewed worktree:

```bash
TMPDIR=/dev/shm PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest -q \
  tests/ape/test_task_config_resolution.py tests/orchestration \
  tests/datasets/test_ask_matching_task.py \
  tests/mathlib_review/test_ask_matching.py tests/mathlib_review/test_matching.py \
  tests/mathlib_review/test_sessions.py tests/mathlib_review/test_run_inputs.py \
  tests/mathlib_review/test_compare.py tests/mathlib_review/test_tool_outcomes.py
# 201 passed

TMPDIR=/dev/shm PYTHONPATH="$PWD/src:$PWD" ape/bin/python -m pytest -q \
  tests/datasets/test_pr_review_v4_judge_source_run.py \
  tests/datasets/test_pr_review_v4_judge_task.py \
  tests/datasets/test_pr_review_v4_schema_split.py \
  tests/datasets/test_pr_review_v5_conditions_report.py \
  tests/datasets/test_pr_review_v5_finalize.py \
  tests/datasets/test_pr_review_v5_finalize_replay.py \
  tests/datasets/test_pr_review_v5_judge_denominator_scope.py \
  tests/datasets/test_pr_review_v5_report.py \
  tests/datasets/test_pr_review_v5_task_data_knobs.py \
  tests/mathlib_review/test_probes.py tests/datasets/test_package_boundaries.py \
  tests/datasets/test_pr_review_v4_no_duplicate_helpers.py
# 176 passed
```

The four additional probes used temporary directories under `/dev/shm`. Matching probes built
the existing `_v2_plan` fixture and seeded legal per-sample results through `TaskStorage`, then
called the real `run_matching`/orchestrator/report paths. Recovery used the existing
`test_recovery_and_identity` fixtures and the real orchestrator. The session overwrite probe used
`plan_sessions`, `import_session_outputs`, `session_outputs` and digest verification directly.
They establish the specific counterexamples above; they are not an exhaustive crash or concurrency
audit. The full repository suite was not run.

No model calls, ingestion, semantic judging, shared-data regeneration, implementation fixes or
branch changes were performed. This review document is separate from the implementation author's
record and is uncommitted in the main checkout.

## Response (Claude, 2026-10-22, on `dataflow-refactor`)

All four findings were confirmed by reading the code and are fixed on the branch, each with a
regression test built from the finding's own reproduction. Nothing called a model.

| Finding | Disposition | Commit |
|---|---|---|
| 1. Separate executions overwrite each other's exported bytes | Fixed. Stored under the producer (`task-<run>`, `import-<name>`), written once: re-exporting one observation is a no-op, different bytes under one observation are refused, a tampered stored value is refused on read (`read_output`). | `58ffe5bc` |
| 2. Reports merge different runs into one replicate | Fixed. An observation is `producer:replicate`; batch rows merge only within one. A report reads one producer, refuses when several are held until one is named (`--producer`), and reads several only explicitly (`--producers`), each judged on its own coverage, the report naming them. The complementary partial runs stay forensic separately and together. | `58ffe5bc` |
| 3. A resume relabels cached measurements with a model that never produced them | Fixed. The run binding records the executor and a digest of every non-operational scaffold setting; a resume on another route is refused before any cached observation is read, naming what differs (`differs in ['model']`); a ceilings-only resume proceeds; every observation carries the binding's executor, never the invoking config's. Both the matching and the session paths. | `58ffe5bc` |
| 4. A previous outcome blocks recovery of a newly successful sample | Fixed in APE alone, first, as suggested. Reconciliation reads the samples: with no result, `_try_aggregate` runs (still running, nothing; resumable, a refreshed outcome; ended, the publication); a result beside an older outcome refreshes it. The review's scenario, with and without a stale claim, publishes and refreshes. | `cbb1a9bc` |

The unifying rule in the review's last section is adopted as the record's own.

**The bounded acceptance path.** Steps 1 to 3 are the commits above (the historical-report parity
checks still pass). Step 4 is done for the reconstruction chain on saved data (`1b451597`): the
cheap-baselines joint seal rebuilt as a plan whose blind inputs are byte-identical to the 46 files
its matchers judged (45 exactly; the 46th, `session_stats.json`, equal as JSON and reordered by
canonical serialisation), its two matchers' verdicts imported, its committed `unblinded.json`
reproduced on every field, and a cell traced to a Sonnet subject's run, route and stored first
message; the eight extractor sessions as a plan over their finished folders' named inputs
(`probe session-plan --include`, `b1a0027c`), all 32 input files carrying the manifest's digests,
their outputs imported. Step 5 is the record's new acceptance table, which says the strongest of
built / offline-verified / integrated / calibrated that applies, with the overstated rows
corrected, and retirement with an owner and a completion point for each bespoke path.

**Still open, as the review says.** The chain's sessions are imported, not re-run as tasks; the
demonstrated-change branch is not migrated; `sample_products` has not replaced the review
runner's and probes' result readers; `ask-match/2-task` is not calibrated against `1-session`; a
first `cli session` or `cli match` run on the subscription route is the user's call. The lead
`task_config` change is now logged at every lead run.

## Independent follow-up and closure criteria (2026-10-22)

Reviewed `dataflow-refactor@cd080f569bf4200d4e8323e3c89fbdfc300fcdef`. The four findings have
specific regression coverage, and the implementation now addresses their triggers. Re-ran the
two earlier groups together: **389 targeted tests passed**. This is an independent targeted run;
the implementation commit separately reports its full-suite result.

Inspected the saved live artifacts and regenerated the matching report without writing it:

- `joint_dev_v2_luna`: three batches, two replicates, six saved verdicts; each replicate covers
  the expected 154 cells, with the Luna/ape_agent/high executor recorded. The report is complete
  and not forensic.
- `extract_r1_luna`: eight packet outputs, each declaring both `goal_brief.md` and `ledger.json`.
  Read all 16 stored values through `read_output`; all digests verify. The Luna producer remains
  separate from the historical imported producer.
- The persisted outcomes mark all three matching tasks and all eight extraction tasks completed,
  with no unknown-usage flag. These confirm successful execution of both new Task paths on Luna
  through ELM. They do not establish reviewer improvement or isolate a matching-protocol effect.

The remaining work is primarily adoption and integration. The original design's requirement is
one operational account of the research, including the connections between operations. Successful
individual Tasks establish the endpoints; the following checks establish their use by the studies.

### Closure work for the original scope

1. **Finish one actual acquisition-to-review handoff.** The branch contains live extractor outputs
   and a live matching of existing reviewer outputs. A study consumer that reads the selected
   extraction producer through `session_outputs`/`read_output` and derives reviewer context is
   still missing from the inspected path. Add that small deterministic adapter, bind its context
   digest to the selected upstream observations, and use the normal reviewer input resolver.
   One study record should lead from acquisition plan/producer to derived context, reviewer
   run/output channel, and matching plan/producer/report. Use existing records/readers for this;
   ordinary Python can own the context-building algorithm. Saved data and rendered reviewer
   prompts can verify the binding without another paid study. Validate one missing/tampered
   upstream output before it reaches a reviewer. Swapping the acquisition producer must change
   the intended context and its recorded lineage.

2. **Exercise the second real consumer at the same boundary.** The demonstrated-change branch
   remains unmigrated. Its existing saved findings and asks should pass through the shared
   matching/report/trace path via a thin adapter. Its study-specific reading should consume the
   common report. The existing synthetic `findings_file` fixture is useful, but does not retire
   that branch's custom matcher. The larger demonstrated-change research experiment and its
   exact-patch technical-check contract can remain in that thread. If integration is deliberately
   deferred until its branch lands, close this branch as an infrastructure slice and leave the
   original two-consumer adoption milestone explicitly open.

3. **Make the prospective cutover concrete.** The next active convention/reconstruction probe
   should use `cli session`, `cli match` and their shared reports. Mark the old launch/match
   paths as historical in the relevant study instructions and templates. Historical artifacts
   need not be regenerated. For the migrated paths, centralize repeated result loading,
   validation and missingness handling; `review/runner.py` and `analysis/probes.py` still have
   their older readers. Preserve the distinction between aggregate task results and individual
   sample products where the report intentionally uses one or the other. The completion
   criterion is that the next study has no reason to copy those mechanics again; replacing
   every historical reader with `sample_products` is not an independent objective.

4. **Check the other advertised scaffold at small scale.** The live coverage is currently
   Luna/ape_agent. If Claude Code is included in the accepted supported scope, a small
   `packet_session` and matching smoke run on that route should establish that workspace paths,
   tools and submission work there. One packet/batch is enough for this operational check;
   a full replay of eight extractions is unnecessary for refactor acceptance. These remain
   user-run. Until checked, record that route as configured and offline-verified. The file-path
   defect found by the first Luna run is a concrete reason to keep route coverage explicit.

5. **Complete the integration record.** Bring the referenced design/review documents into version
   control with the integration, make the status index reflect the live Luna runs (its slice-B
   row still says extractors were imported and not re-run), and preserve the explicit lead
   task-config behavior change. Check integration with `review-reconstruction` and
   `demonstrated-change`; the two reconstruction cherry-picks and their rule-file conflict are
   already identified in the implementation record. Run the normal offline suite on the final
   integrated tree. The branch and several referenced documents are not yet on `develop`.

Items 1 and 3 directly address the maintainer's original problem of shared primitives remaining
unused while studies reconstruct execution and results independently. Item 2 determines whether
the original two-consumer scope can be declared complete. Items 4 and 5 establish the supported
scope and finish integration. These do not require a second general architecture refactor.

### Open work that can have separate completion criteria

- **Matching calibration.** The Luna results show operational success and an initial agreement
  check. Model, effort, scaffold, batching/presentation and protocol differ from the historical
  Opus sessions, so the comparison does not isolate the protocol change. Select a stable
  prospective instrument and executor for each new study. Controlled calibration or adjudication
  becomes necessary for claims of measurement continuity, quality, or substitutability. Software
  closure can retain the explicit boundary between the old and new measurements.
- **Full historical replay and every historical reader.** Preserve access and definitions; migrate
  readers that remain active. Re-running all past extractor/auditor/sketch sessions is not needed
  to establish the new execution contract.
- **Research-specific extensions.** Exact-patch technical checks, the reconstruction sketch
  instrument and blinded trace export remain with their named consumers. They should become
  shared operations when those consumers use them, with the existing Tasks as the execution path.
- **The proof-engineering judges' failed-attempt accounting gap.** It remains explicitly recorded
  in the implementation report and framework-defect list. It is outside the verified
  matching/session paths and needs its own correction before making inclusive spend claims for
  that family.
- **Further architecture work.** Review IR/AST proposals, a broader sealing redesign and additional
  generic workflow machinery remain separate design questions, each requiring its own motivating
  failures and acceptance checks.

No model calls, implementation changes or merges were made during this follow-up. This review
update is uncommitted in the main checkout.

## Response to the follow-up (Claude, 2026-10-22, on `dataflow-refactor` at `b5d3d9ca`)

All five closure items are done as far as they go without the subscription route or a merge. The
details and commits are in the implementation record's "Closure work" section.

| Item | Outcome |
|---|---|
| 1. One acquisition-to-review handoff | Built and integrated on saved data. A session plan's inputs bind to upstream observations (`lineage.json`). A reviewer context is derived from stored outputs (`probe context-derive`) with a lineage the input resolver recomputes before any run, refusing a missing or tampered upstream output. The reconstruction chain's nine Phase A contexts derive byte-identical. Their rendered sections are in all 56 stored first messages of the 21 Phase A runs. The three Phase A matchings reproduce their readings on every field. `report trace` walks a matcher's cell back to the extraction. |
| 2. The second consumer | Integrated. The compiled-unfiled probe's findings and asks are planned through a thin adapter that imports the probe's own renderer, and both matchers are imported. Its reading, taken from the common report, prints `reading.txt` exactly. `match.py inputs` and `read` retire when that branch merges. |
| 3. The prospective cutover | Built. There is one collector, one producer naming and one coverage rule for sessions and matchings (`report sessions` is new). Locators are resolved through the worktree link. The historical `probe unblind` refuses files that miss cells. The instructions, todos and CLI help mark the old routes historical. |
| 4. The other scaffold | Smoke plans sealed and dry-run on the Claude Code configs: one packet, and one batch of 14 cells. Not run, because the subscription is the user's account. The route stays configured and offline-verified until then. |
| 5. The integration record | STATUS and the record are updated. A trial merge in a detached worktree passed: `develop`, then the untracked documents, then this branch, `review-reconstruction` and `demonstrated-change`. It ran 3157 tests, all passing, and `verify_frozen` reported ok. The conflicts are recorded with their resolutions. Nothing was merged. |

Two findings change the record:

- **Revision inputs were on disk.** An earlier note said the extraction revisions' inputs were not on
  disk. They are, and all 32 equal the manifest's digests.
- **The real-chain swap stops at the decision sessions.** Swapping the acquisition producer changes
  the context and its lineage, but only up to that step. The decision-context sessions searched
  through `ctxtool`: grep and show at the base commit, plus Zulip and precedent search. The folder
  session task cannot grant those tools yet. This is recorded as gap 13, with what completes it.

## Final independent closure assessment (2026-10-22)

Reviewed `dataflow-refactor@e13343c8`. **The first refactor is ready to close as an implementation
and review thread.** The outstanding work is landing the changes and documents, rather than
another architecture iteration or another model run. This accepts the shared execution and data
boundaries, their adoption by two real consumers and the advertised scaffold support. It does not
claim that every stage of the reconstruction workflow has been freshly executed through Tasks.

The evidence now satisfies the earlier bounded acceptance path:

- **Correctness and regression coverage.** The four original findings remain fixed. Independently
  ran the expanded offline selection covering orchestration, config resolution, sessions,
  matching, reports, probes, finalization and package boundaries: **401 tests passed**.
- **Acquisition-to-review handoff.** Independently verified all nine derived Phase A contexts
  against their upstream observations. The decision and both sketch plans' input lineage loaded
  without unmatched upstream inputs. Regenerated the dev, post and validation matching reports
  without writing them; each exactly equals its saved report, with complete, non-forensic
  observations. This checks the saved chain's data bindings, rather than merely the existence of
  its component APIs.
- **Second consumer.** On the integration-trial tree, independently ran the compiled-unfiled
  adapter's reading through the common report and asserted exact equality with its original
  `reading.txt`. The study owns its interpretation; it uses the shared matching/report boundary.
- **Both scaffolds.** The earlier Luna/ape_agent runs cover extraction and matching. The new
  Sonnet 5.5/Claude Code smoke also completed both: one packet with both required outputs and one
  14-cell matching batch. Independently checked the session's output digests and complete
  coverage, and regenerated the matching report exactly. The stored executor identifies Claude
  Code, Sonnet 5.5, high effort and CLI 2.1.285. Another Opus run is not required to establish this
  scaffold's operational support.
- **Adoption and integration.** The shared collection/coverage paths and prospective cutover
  instructions are in place. Inspected the clean integration-trial history combining the design
  documents, refactor, reconstruction and demonstrated-change branches. The implementation
  record reports **3157 passing tests and `verify_frozen` OK** there; this review did not rerun
  that full suite or frozen check. The second consumer check above was independently run there.

### Landing checklist

1. Commit the relevant design/review documents, including this closure assessment. They remain
   untracked in the main checkout; the main checkout also has unrelated work to preserve.
2. Integrate the latest refactor HEAD and the related branches using the recorded conflict
   resolutions. The successful trial predates the final Sonnet configs, submission-tool counting
   fix and live artifacts/documentation; it is not a test of the exact final merged tree.
3. Run the normal offline checks and frozen verification on that final integrated tree. No actual
   merge into `develop` has been performed by this review.

### Carry forward without reopening this refactor

- **Episode-bound tools for decision sessions (gap 13).** A fresh acquisition replacement cannot
  yet be propagated live through the complete reconstruction chain: `packet_session` lacks the
  repository/Lean/Zulip/precedent tool grants those sessions used. Their existing outputs are
  imported and linked. Add those grants when migrating that operation, preserving its episode
  and cutoff bindings. The saved-chain acceptance above must not be described as a full live
  replay or evidence that this gap is solved.
- **Matching calibration.** Cross-model/scaffold agreement and report reproduction establish
  operational checks, not controlled equivalence of `ask-match/2-task` and `1-session` or reviewer
  improvement. Keep protocol and executor differences visible in research comparisons.
- **Already scoped work.** Exact-patch technical checks, proof-engineering failed-judge accounting,
  historical-path retirement and broader IR/sealing proposals retain their own completion
  criteria. None requires another general refactor to accept the work reviewed here.

No model calls, implementation changes or merges were made in this assessment. This review
document remains uncommitted in the main checkout.
