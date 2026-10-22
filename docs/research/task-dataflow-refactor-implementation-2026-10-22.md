# Task/data refactor: implementation record

2026-10-22. Branch `dataflow-refactor`, off `develop` at `4695a1b1`. Implements
[the design, v0.3](task-dataflow-refactor-design-2026-10-22.md) slice by slice. That design and its
companions are untracked in the main checkout at the time of writing and are not on this branch;
commit them to `develop` before merging this branch, or the links below dangle.

This file records what is built, the interface decisions taken while building it, and every place
the work departs from the design or from an earlier recommendation. **Interface decisions below are
proposals made during implementation, not decisions the maintainer has agreed** (design §15 asks
that the shared interface be agreed before runtime work). Each is reversible on this branch.

## Slice 0: execution semantics (built)

| Commit | What | Acceptance check |
|---|---|---|
| `405a6410` | One task-config resolution; unknown keys and another task's config refused; faithful worker round trip; children inherit no task settings | `tests/ape/test_task_config_resolution.py`, asserted on the worker-rebuilt task |
| `0633e932` | No synthetic result for an all-failed task; outcome carries attempt errors and unknown usage; batch counts failures and spend from outcomes | `tests/orchestration/test_task_outcome.py` (+4, real `SampleWorker`) |
| `2146b285` | A tool call with no recorded result is `missing`; coverage counted | `tests/mathlib_review/test_tool_outcomes.py` (+2) |

Departures and flags:

- **Placement against an earlier recommendation.** `docs/todo/thesis-pilot-integrity.md` advised fixing
  the gate at its call site and not in `tasks/base.py`, to protect v5 lead inheritance. The design's F1
  takes the general rule (no broadcast into children). Measured first: on all 17 lead configs the one
  setting arms kept from the broadcast equals their own default. CLI `--set task_config.X` on a lead run
  no longer reaches its arms.
- **Found while fixing, and fixed:** no attempt error ever reached an outcome (0 of 11,501 attempts),
  and a raised attempt was booked at $0. Both are inside "expose failure and usage".
- **Named remaining gap:** the two proof-engineering judges bubble `results.total_token_usage`, which
  misses a failed judge's spend. Moving them to `nested_usage(runs)` changes that family's token
  accounting; recorded in `framework-defects-2026-09.md` §4.

## Slice A1: common evaluation and result inspection (interface proposal, then build)

### What exists, read before designing

- The atomic-obligation judge: `judge/protocol.py` (rubric `JUDGE_VERSION`), the registered Task
  `lean_pr_review_v4_semantic_judgment`, `judge/runner.py` (pairing, `seal_pair`, orchestrated
  judging, `semantic_report`, the stage ledger row). Its sealed v4 contracts (`EvaluationProtocol`,
  `PairManifest`, `EvaluationReceipt`) are used only by the v4 release builders, not by this path.
- The raw-ask matcher: `analysis/probes.py` (`seal_labels`, `match_inputs`, `matcher_rubric`,
  `judge_folders`, `unblind`), its rubric read from
  `results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/matcher_rubric.md`, and the shell chain
  `one-reviewer-table-2026-10-10/run_matching.sh` → `conventions-ceiling-2026-10-04/run_claude_batch.sh`,
  `audit_batch.py`, `check_matches.py`. Matcher inputs are written under
  `/research/projects/proofedit/ya475/table_scratch/`, outside the repository: for the filing-contract
  seals only `matches.{1,2}.json`, `session_stats.json` and `unblinded.json` were kept, so the bytes the
  matchers judged are not in the record.
- A third subject shape is in flight: `demonstrated-change`'s
  `compiled-unfiled-2026-10-18/match.py` writes findings from a file, not a run, and calls the same
  helpers.

### Proposed interface

1. **Instruments are named and versioned in `src/`** (`src/mathlib_review/judge/instruments.py`):
   - `ask-match/1-session`: the historical matcher. Rubric bytes stay where they are and are identified
     by SHA-256 (request-only and question-form). Hand-launched Claude Code sessions over folders.
     **Import only**: results under it stay interpretable; no new run uses it.
   - `ask-match/2-task`: the registered Task. The judgment rules are v1's text verbatim; only the input
     paragraph (inline sections named as v1's files) and the output paragraph (a typed submit tool in
     place of `matches.json`) change. Not declared equivalent to v1: equivalence is a calibration
     question on aligned saved examples, and calibration is user-run.
   - `semantic-judge/<JUDGE_VERSION>`: the existing judge, unchanged.
2. **A measurement identity travels with every number** (`MeasurementIdentity`, a sealed record):
   instrument and version and rubric digest; reference kind (raw ask or atomic obligation), source and
   digest; subjects per session label (source kind, run, output channel, findings digest); population
   (PRs, scope); seal (path and digest) or pairing tiers; blind projection (fields kept, redaction,
   harness-blind cut); replicates and aggregation; denominator; missingness policy; executor
   (orchestrator run, or external import). `unblinded.json` and `semantic_report.json` carry it.
3. **Subjects are bound by source and output channel** (`SubjectSource`): `packet` (a Claude
   session's `findings.json`), `solo` (a run's submitted task findings, channel `submitted`), `lead`
   (a run's `findings.jsonl`, channel `finalized`, with `published` indices), `findings_file` (an
   explicit file per PR and session, channel `declared`). The loaders move out of `probes.py`.
4. **A matching plan is sealed before any matcher runs** (`MatchingPlan`, `write_once` in the
   measurement directory, in the repository): identity, the seal, batches of PRs, and per PR the exact
   blind inputs with their digests, and the expected cells. The inputs are retained, not written to
   scratch.
5. **The matcher is a registered Task** `lean_pr_review_ask_matching`: one task per batch, `sample_count`
   = the number of blind matchers (independent samples of the same inputs, as the two matchers were),
   a typed `submit_matches` tool that refuses an incomplete or out-of-range verdict, and an aggregate
   that keeps every replicate (no majority). Runs through `TaskOrchestrator`, resumable.
6. **Verdicts are one store** (`verdicts.jsonl` in the measurement directory): one row per replicate and
   batch, from a task sample (locator: task directory, sample, attempt) or from an external import
   (locator: file and digest, provenance `external_session`). Historical `matches.{1,2}.json` import
   through the same validation against the plan's expected cells.
7. **One report function** produces `unblinded.json` from the plan and the verdict store; the existing
   `unblind` arithmetic is kept and called, with the identity block added.
8. **One reader** (`cli report trace`) follows a row back: report → plan → seal label → the blind input
   file and digest the matcher saw → each replicate's verdict cell and its task/attempt or import file →
   the subject's source and the reviewer's original finding.
9. **CLI:** `cli match plan|run|import|report`. `run` spends and requires `--execute` and `--run-name`.
   `cli probe seal|match-inputs|unblind` call the shared implementation and remain for the historical
   shell chains, listed below as a remaining adoption gap.

### Built

| Commit | What |
|---|---|
| `a644d4d2` | The instrument (`judge/ask_matching.py`): v1 identified by its files' digests, v2's text with v1's judgment rules byte for byte, projection, seal, verdict validation; the evaluation records in `schema/scoring.py` |
| `2aec9b04` | The registered Task `lean_pr_review_ask_matching` |
| `e6de27f3` | The lifecycle (`analysis/matching.py`): plan, run, import, report; `cli probe match-plan`, `cli match`, `cli probe match-import`, `cli report match`; the route config |
| `c443aee8` | The judge's report carries the same identity; `report conditions` names each repetition's; `cli report trace` for both instruments; the matcher's stage-ledger row; the reporting rule in `CLAUDE.md` |

Acceptance, checked without calling a model:

- **A row identifies its subject, channel, protocol, population, seal and repetitions:** the
  `measurement` block of `report match` and of `semantic_report.json`, and the `measurements` row of
  `report conditions`.
- **One reader traces it to exact bytes:** `cli report trace`, on a historical matching cell (label,
  shown findings and their digest, both replicates' verdicts and files, the session's original
  findings) and on a real judged obligation (its pair, verdict, three issue votes, the finding and the
  judge task's directory).
- **Shared execution, sealing and reporting:** the matcher runs through `TaskOrchestrator` with its
  replicates as samples, its plan is sealed before running, its source runs' ledgers get a row as the
  judge's do, and both instruments' reports carry one identity record. They keep their own verdict
  schemas, as the design allows.
- **No silent change to past numbers:** the post-cutoff seal and the filing-contract dev seal,
  rebuilt as `1-session` plans and their committed `matches.json` imported, reproduce their committed
  readings on every field; the filing-contract plan's 72 input files equal the ones its matchers
  judged, byte for byte.

### Remaining adoption gaps

Named here, each with what completes it, rather than dropped:

1. **The historical shell chain** (`one-reviewer-table-2026-10-10/run_matching.sh`,
   `conventions-ceiling-2026-10-04/run_claude_batch.sh` and helpers) still runs through `probe seal`,
   `probe match-inputs` and `probe unblind`, which now call the shared implementation. Complete when no
   script written after this branch calls `probe match-inputs`; then the verb goes.
2. **`demonstrated-change`'s `compiled-unfiled-2026-10-18/match.py`** builds matcher folders by hand.
   Its findings are a `findings_file` source and its asks are `--ask-packets`; it migrates when that
   branch merges. Owner: that thread.
3. **The reconstruction branch's sketch matcher** (`sketch_matcher_rubric.md`, on `review-reconstruction`)
   is a third instrument, unregistered here because its code is not on `develop`. It is registered or
   retired when that branch merges.
4. **Calibration of `2-task` against `1-session`** on aligned saved examples (questions, partials,
   target mismatches) is user-run: it calls the matcher model. Until then a `2-task` number is not
   compared with a `1-session` number.
5. **Judge audits written before this branch** carry no identity; `report conditions` and `report trace`
   say "unrecorded" for them. Re-judging is not required: their meaning is unchanged.
6. **Choosing the primary instrument per objective** (design §11) is the maintainer's decision; the
   tooling now lets either be named, run and reported, and refuses neither.

## Slice A2: resolved context and run inspection (built, `135e81a2`)

`review/inputs.py` is the one resolver for the files a solo-family config names. The plan seals their
digests in `evaluation_settings["input_files"]` (only when a file is named), tasks verify the bytes
they read against the digest, a real run snapshots the bytes into `<run>/inputs/`, and `cli report
inputs` shows a run's route, its input files' status and each attempt's stored first messages and
tools, naming what the Claude Code route does not record. **Boundary, flagged:** a run sealed before
this resumes with a warning and a plan revision instead of being refused, because refusing would
strand every paused subscription run; a recorded setting that changed alongside is still refused.

Also built with the first evaluation path, as design §11 requires (`e6276795`): `cli report compare`,
the comparison path -- identity differences, a comparability verdict, each run's sealed plan and task
settings, and every difference not declared as the contrast. It found that `agenda_sha256` differs
between any two runs (the agenda names its own run), so the comparison uses the agenda's content.

## Slice B: shared composition in two consumers

### The spike (design §15: before implementing B, walk the consumers through the APIs)

Walked against saved inputs on the two consumer branches, after slices 0, A1 and A2:

| Mechanic | Reconstruction (`review-reconstruction@eecb7d18`) | Demonstrated change (`demonstrated-change@e9b9b6e0`) | Shared after A1/A2? |
|---|---|---|---|
| Reviewer runs | `cli run` with a `context_file` per condition | `cli run` with the `compiled_filed` design (a `DESIGNS` entry) | Yes: sealed by content (A2), compared (`report compare`) |
| Matching and its reading | `probe match-inputs` + `run_matching.sh` + `read_*.py` re-unblinding | `compiled-unfiled-2026-10-18/match.py` building folders by hand | Yes: `match-plan` (with `findings_file` and `--ask-packets`), `match`, `match-import`, `report match`, `report trace` |
| Model sessions over prepared folders | extractor, auditor, revision, sketch, context preparer, blind trace readers: `make_packets.py` writes folders to scratch, `run_claude_batch.sh` runs them headless outside the orchestrator, `audit_batch.py` audits transcripts, outputs read by path; `manifest.json` keeps only the inputs' digests | the compile probes' added findings are built by a script, not a session | **No.** The one recurring mechanic left; the same chain in at least six probes (conventions-ceiling stages, one-reviewer table, filing contract, ask-reading, stage H, reconstruction) |
| Packet and section building | `make_packets.py`, `step4/build_sections.py` | the added-findings builder | Study algorithm: stays beside the study |
| Registered readings | `read_scores.py`, `read_phase_a.py`, `read_baselines.py`, `read_joint.py` | `match.py read` | Stay beside the study; they read the shared report instead of re-unblinding |
| Blind trace export for readers | `step3/build_traces.py`, `step4/build_place_traces.py` | -- | Partly: `report inputs` and `report trace`; a blinded trace export is a named gap below |

### The decision: an engine extension, not a thin adapter

The bespoke remainder is one lifecycle repeated in six probes, and in every instance the inputs a
session read were lost. A thin adapter per study would keep that. So, in APE:

- `BaseTask.product_of` and `ape.orchestration.products.sample_products`: every sample's product read
  one way, validated as the task's own result class (never the `BaseTaskResult` fallback), one row per
  requested slot, a missing product never empty. This is design §5's output projection. The matcher's
  verdict store now reads through it.
- `packet_session`, a generic registered Task: a brief with `{dir}`, the folder's files as task data,
  declared outputs validated by `submit_outputs`, replicates as independent samples.

and in the domain, `analysis/sessions.py`: a sealed `SessionPlan` holding every packet's files, `cli
session --execute` (in `SPENDS`), an import for hand-launched sessions' folders, and an outputs store
with digests and locators; `configs/session/packet_session_opus55_claude_sub.yaml` for the route the
hand-launched sessions used.

### Acceptance, checked without a model

`tests/mathlib_review/test_sessions.py` drives the real task end to end (setup lays the folder out,
`submit_outputs` refuses missing outputs and accepts written ones) and walks the reconstruction
consumer through the shared records: extractor sessions run through `run_sessions`, their outputs
read from the store into a context file, the context file sealed by content and read by a pinned solo
config into the reviewer's prompt. Swapping the extractor (a different brief) is a different session
plan; the context digest and the reviewer's prompt change and no downstream code is touched. The
demonstrated-change consumer composes through `cli run` and `match-plan` with a `findings_file` source
(`tests/mathlib_review/test_matching.py`).

### Remaining adoption gaps (slice B)

7. **The probes' hand-launched sessions** still run through `run_claude_batch.sh`. A new probe uses
   `probe session-plan` and `cli session`; existing ones are historical. A paid first run of a session
   plan on the subscription route is the user's call.
8. **A blinded trace export for readers** (`build_traces.py`, `build_place_traces.py`) is still
   study code; `report inputs` and `report trace` cover the unblinded reading. Completes when the next
   blind-reader probe exports through a shared function.
9. **Ask readers and matchers as packet sessions.** Both are folder sessions and can run as `packet_session`
   with their v1 prompts unchanged; that would make `ask-match/1-session` re-runnable under the task route.
   Not done: it is a new instrument version and needs its own calibration.

## Slice C: failure and dynamic behaviour (built)

Each property in design §15's slice C, with the test that holds it
(`tests/orchestration/test_recovery_and_identity.py`, real orchestrator and tasks, no model):

| Property | How it holds now |
|---|---|
| **Interrupted output** | Reproduced before fixing: a task whose sample succeeded but whose process died before aggregation, and a task whose result was written but whose log row was not, both reached `task_results` as nothing on resume, so a resumed review lost that PR's findings silently. Now `TaskOrchestrator._reconcile_interrupted` finishes such publications at the start of a run with the worker's own aggregation and outcome writer, and final aggregation reads each task's `task_result.json` when the log lacks it and heals the log. Both are listed in `OrchestratorResults.recovered_results`. |
| **Conflicting publications** | A worker claims a task's publication atomically (`task_result.claim`, created inside the aggregation lock; the writes cannot be under the lock in async mode). A second publisher backs off; a claim left by a killed process is stale at the next start. Two different log rows for one task are read from the task's file and named in `conflicting_results`, never chosen silently. |
| **Resumed sample** | One observation with several attempts (`sample_products`: one row, `attempts=2`); resume never mints a repetition. |
| **Fresh repetition** | Identical products of independent samples stay two rows; nothing deduplicates by content. |
| **Nested failure** | A failed child's `ChildRun.error` comes from its outcome's attempt errors (slice 0). |
| **Explicit fallback** | A reviewer whose context file lacks its PR refuses (`KeyError`), so a failed acquisition never becomes an unassisted review without a word. |
| **External labels** | Imports are validated against the plan (matchings, sessions); a plan with no verdicts yet is "waiting", refused by the report, never scored. |
| **Unsupported continuation** | A matching or session run name is bound to its plan (`plan_binding.json`): the same plan resumes, another plan is refused with "give the new plan a new run name". A review run's plan already refuses a semantic change (and, since A2, an edited input file). |

### Overhead, measured on real records (design §15's last acceptance check)

| Operation | Size | Time |
|---|---|---|
| Build a matching plan | filing-contract dev seal: 12 PRs, 5 sessions, 235 cells; 576 KiB | 1.4 s (loads five runs) |
| Load and verify a plan / import two replicates / report | same | 6 ms / 3 ms / 7 ms |
| Trace one cell | same | 0.1 s (reloads the session's run) |
| `sample_products` | `pr5_F_fanout_heldout12_v2_rep1`, 1,409 tasks on NFS | 1.0 s (about 1 ms a task) |
| Reconciliation's file checks | same | 0.15 s; tasks without both files then have their samples loaded, as `_prepare_jobs` already does |

Nothing here is a reason to hold back adoption. The plan file grows with the inputs it now keeps,
which is the point of keeping them.

## Design §15's acceptance checks

Status words, after the implementation review of 2026-10-22: **built** (the code exists),
**offline-verified** (a test or an offline check on saved records holds it), **integrated** (an
active study's chain runs through it on its saved data), **calibrated** (a model or human comparison
established it; user-run). A row says the strongest that applies.

| Check | Status | Where |
|---|---|---|
| Independent identical outputs remain two observations; resume does not mint a repetition | offline-verified | `test_recovery_and_identity.py`; and, after review finding 2, two runs or imports of one plan are separate producers (`test_matching.py`, `test_sessions.py`) |
| A stale source, unsupported schema or missing required output fails before consumption | offline-verified | edited plans, briefs and stored outputs refused on load or read; strict `schema_version`s; `submit_outputs` and the imports refuse a missing output |
| Same-shaped evidence from another episode fails the domain binding before a paid call | offline-verified for context rows | `solo_context_block` refuses a row bound to another episode or reviewed head (`270838de`) |
| ... and a check of another patch | **not built** (gap 10) | lands with the demonstrated-change branch's construction artifacts |
| Interrupted publication recovers a consistent binding or stays visibly incomplete; conflicting publications are not silently chosen | offline-verified | `e90b51ef`; review finding 4 (a previous outcome blocked a resumed sample's publication) fixed in `cbb1a9bc` |
| The same sealed cases and recorded judgments give the same report after the refactor; changed semantics get a different protocol | offline-verified, and integrated for three seals | post-cutoff, filing-contract dev and the reconstruction joint seal reproduce their committed readings; `ask-match/2-task` is its own version, **not calibrated** |
| A whole-PR reviewer and an assisted program run through one execution system and project to one final-finding contract | integrated | `cli run` for both; the reconstruction chain end to end on saved data: extraction -> decision and sketch sessions (inputs bound by `lineage.json`) -> the nine Phase A contexts derived byte-identical -> 21 reviewer runs -> three matchings reproduced (closure item 1); the acquisition link also run live on GPT-6 Luna (`extract_r1_luna`, 8 of 8) |
| A program changes a component and its configuration without editing the common runner's condition branches | offline-verified | `test_sessions.py`: replacing the extractor touches nothing downstream |
| A maintainer follows one evaluation row to exact submitted or published bytes and all resolved inputs, with no per-study reader | integrated | `cli report trace` on the joint seal reaches a Sonnet subject's run, route, sealed-input status and stored first message; on Phase A it goes on through the reviewer's context, its recomputed lineage and each section's session observation back to the extraction (`954c6f9b`); `report inputs` |
| Editing one prompt or context byte changes the request or refuses resume; an old run still shows its original bytes and tool interface | offline-verified | slice A2 |
| Comparing saved runs shows differing channels, protocols, populations, seals and routes, refuses unsupported pooling, permits declared contrasts | offline-verified; integrated across the joint seal's subjects | `cli report compare`; subjects whose run plans are on another branch are named as without a plan, not guessed |
| The second consumer adds its algorithm and contract extensions without copying evaluation, context resolution, execution or reading code | integrated | the compiled-unfiled probe's matching planned, imported and read from the common report through a thin adapter that imports the probe's own renderer; its reading reproduced line for line (`68dea3b5`); `match.py inputs`/`read` retire with that branch's merge |
| Handoff writes are bounded; overhead measured on realistic outputs before broad adoption | offline-verified | slice C's table |
| Execution provenance identifies what ran | offline-verified | review finding 3: a run is bound to its route; a resume on another route is refused before any cached observation is read (`58ffe5bc`); on the live Luna runs every observation carries its executor, which `report compare` now reads (`6ddb81b3`) |

10. **A technical check bound to the exact patch across tasks.** Completes with the
    demonstrated-change design's construction artifacts: a check names the patch digest, imports and
    workspace it compiled, and the consumer refuses a check of another patch. Owner: that branch's
    merge.
11. **`sample_products` has not replaced every result reader**, and is not meant to (the follow-up
    review's item 3). The shared paths now collect a run in one place (`matching.task_observations`),
    name producers and import executors in one place, and report coverage the same way for matchings
    and sessions (`report sessions`). The review runner's readers of `results.task_results` and
    `probes._solo` read aggregate results on purpose and stay; they move only when one of them is
    next changed.
12. **The reconstruction chain's sessions as tasks.** Run once as tasks, on GPT-6 Luna through ELM
    (`extract_r1_luna`, `f1c6f692`): 8 of 8 sessions handed in both outputs. Completes when the plan
    is run through `cli session --execute` on the subscription route, where the imported extractions
    came from, and the two producers' outputs are compared; user-run.
13. **Decision-context sessions cannot yet run as tasks.** They searched through `ctxtool`: grep and
    show at the PR's base commit, and the harness's cutoff-filtered `zulip_search` and
    `precedent_search`. `packet_session` grants file tools only, on either route. Completes when a
    packet session can be granted those episode-bound tools (the base snapshot and the cutoff are the
    episode's, as the review arms have them); until then a swap of the acquisition producer on the real
    chain stops at the decision step, and the swap is shown on the shared derivation's own test.
14. **The Claude Code route has not run the new tasks.** Smoke plans are sealed and preflighted
    (`smoke_claude_code_session`, one packet; `smoke_claude_code_match`, one batch of 14 cells);
    the route stays configured and offline-verified until the user runs them.

Retirement, as the design requires it with an owner and a completion point: `probe seal`,
`probe match-inputs` and `probe unblind` go when no script under `results/` written after this
branch calls them (owner: the next matched probe's author); `run_claude_batch.sh` and
`run_matching.sh` go when the next probe's sessions run through `cli session` and `cli match`
(owner: that probe's author); `make_packets.py`'s extractor, auditor and sketch folders go when
that probe is re-run on the shared path (owner: the reconstruction thread).

## The implementation review of 2026-10-22, and what it changed

`docs/research/task-dataflow-refactor-implementation-review-2026-10-22.md` (independent, no fixes
proposed as code) reproduced four defects on the branch at `768e24b1`, none of which the slices'
tests had reached. Each is reproduced by a test now and fixed:

| Finding | What was wrong | Fix |
|---|---|---|
| 1. Session outputs overwrote each other | the stored path was `<packet>/<replicate>/<name>`; a second execution or import replaced the first's bytes while its index kept the old digest | stored under the producer (`task-<run>`, `import-<name>`), written once; `read_output` verifies the digest (`58ffe5bc`) |
| 2. Matching replicates merged across runs | observations were keyed `origin:replicate`; two partial runs with complementary batches read as one complete replicate | an observation is `producer:replicate`; a report reads one producer, or several only explicitly, each judged on its own coverage (`58ffe5bc`) |
| 3. A resume relabelled cached verdicts with a new model | the run binding checked the plan, not the route | the binding records the executor and a digest of every non-operational scaffold setting; a resume on another route is refused before reuse, naming what differs; observations carry the binding's executor (`58ffe5bc`) |
| 4. A previous outcome blocked a resumed sample's publication | reconciliation skipped any task with an outcome file | the samples decide: `_try_aggregate` runs whenever a result is absent, and a result beside an older outcome refreshes it (`cbb1a9bc`) |

The review's rule, adopted as the record's: a plan describes inputs; a run or import is a producer
with one execution policy; a sample is an observation; equal values can belong to different
observations; a resume continues an observation; different observations are never overwritten or
merged because their sample numbers match.

Its step 4, migrating one active chain on saved data, is done for the reconstruction chain
(`1b451597`): the joint seal as a plan whose inputs are byte-identical to what its matchers judged
(45 of 46 files; the 46th equal as JSON), its verdicts imported and its committed reading reproduced
on every field; the eight extractor sessions as a plan whose 32 inputs carry the manifest's digests,
their outputs imported. Not done: the chain's remaining links as *tasks* -- the extractor,
auditor and sketch sessions have been imported, not re-run -- and the demonstrated-change branch,
which is not on `develop`.

## Decisions taken while implementing, for review

None of these changes the agreed plan's scope; each is a choice the plan left open or an
interaction with an earlier record. All are on this branch and reversible.

1. **Configuration (slice 0).** Children inherit no task settings; the earlier pilot todo advised a
   call-site fix instead. Measured safe on every config on disk; CLI `--set task_config.X` on a lead
   run no longer reaches its arms.
2. **Failure records (slice 0).** `OrchestratorResults.completed_tasks` now counts tasks with a
   result; failures are `failed_tasks`. Two adjacent defects were fixed because they sat inside
   "expose failure and usage": attempt errors never reached outcomes, and a raised attempt was booked
   at $0 (now `usage_known: false`).
3. **The matcher's v2 text (A1).** v1's judgment rules verbatim; the input and output paragraphs
   changed for a task route. Declared a new version, not equivalent until calibrated.
4. **Pins (A1, B).** The schema facade's export count 133 -> 144 with reasons; the pure class-count
   pin dropped, as the October 6 inventory proposed; the knob guard exempts a new task type's birth
   fields only.
5. **Resume boundary (A2).** A run sealed before input files were recorded resumes with a warning and
   a revision instead of being refused, so paused subscription runs are not stranded.
6. **Engine extension (B).** `packet_session` and `sample_products` live in APE, domain-free; the
   spike's evidence (six probes, inputs lost every time) is why it is not a per-study adapter.
7. **Recovery (C).** On resume the orchestrator writes the missing result, outcome or log row of an
   interrupted task into that run's directory. That is recovery by the engine's own writer, as the
   design asks; it does change files of interrupted runs when they are next resumed.
8. **CLI.** New verbs: `cli match`, `cli session` (both spend, gated); `probe match-plan`,
   `match-import`, `session-plan`, `session-import`; `report match`, `trace`, `inputs`, `compare`.
   `probe seal`, `match-inputs` and `unblind` remain for the historical shell chain (gap 1).

## First live runs, on GPT-6 Luna (2026-10-22)

The user chose a cheap model for the first live tests: not the self-hosted DeepSeek (slow to start),
and GPT-6 Luna over gpt-5-mini. `elm_gpt_6_luna` came from `review-reconstruction` as two
cherry-picks with `-x` (`819acde3` from 033765c7, `178bafc2` from 8b918cce). Configs:
`configs/match/ask_match_elm_luna.yaml` and `configs/session/packet_session_elm_luna.yaml`, ape_agent at
effort high, both halves of the per-session ceiling.

| Run | What | Outcome | Billed |
|---|---|---|---|
| `joint_dev_v2_luna` | the joint dev seal as `ask-match/2-task`, one PR per matcher, 2 replicates: 6 sessions | 6 of 6 submitted; 154 of 154 cells a replicate; not forensic | USD 0.0253 |
| `extract_r1_luna` | the eight extractor sessions as `packet_session` tasks | 8 of 8 handed in both outputs; 98 tool calls, all answered | USD 0.1432 |

What they established, beyond the offline checks:
- **The task paths complete on a live model.** Both submissions validate at the far end. Two matcher
  sessions were refused once by `verdict_problems` for finding indices that do not exist (R2 on
  33066 has 3 findings; the model named 7 and 11), then corrected. The refusal path works live.
- **Producers stay apart.** The Luna verdicts and outputs sit beside the imported Opus ones, under
  `task-joint_dev_v2_luna` and `task-extract_r1_luna`. `report match`, `report trace` and
  `report compare` read them without a per-study reader.
- **Cross-route agreement is no lower than within-route.** Over 154 cells, three-valued / reached-or-not:
  Opus replicates 149 / 150, Luna replicates 145 / 149, Opus against Luna 143-151 / 146-153 over the four
  pairs. This is **not** the calibration of 2-task against 1-session: the model, effort and scaffold
  differ as well as the version and rubric.

Three defects the live runs found, which no offline test had reached, each fixed with a test:
1. **An ape_agent session could not open its own folder** (`9d9e593a`). The brief gave the
   folder's absolute path, and APE's file tools refuse every absolute path. The old test asserted the
   absolute path under `ApeAgentConfig`, so it pinned the defect. `{dir}` now becomes `scratch/packet`
   on ape_agent; the new test opens the brief's folder with the real `file_read`.
2. **A matching wrote a ledger into a folder that is not a recorded run** (`6ddb81b3`). A worktree
   links each run's untracked arm pool, so `probe_dev_opus55_contract2_claude_sub_rep3/` existed with
   only that link, and the matching created a lone `stages.jsonl` there. Runs recorded on another
   branch were skipped in silence. Rows now go only where the run's `findings.jsonl` is recorded, and
   every skipped run is named in a warning.
3. **`report compare` did not say who ran the matchers** (`6ddb81b3`). Opus at xhigh on Claude Code
   against Luna at high on ape_agent showed only the version and rubric. `executor_differences` now
   reads the executors from the observations, and a plan matched by two executors stays side by side
   unless `--contrast executor` declares the comparison a calibration. `executor_of` also read effort
   only from Claude Code's field, so an ape_agent binding would have said `unknown` (`9d9e593a`).

## Closure work after the follow-up review (2026-10-22)

The independent follow-up on `cd080f56` named five pieces of closure work for the original scope.
All five are done to the extent that does not need the subscription route or a merge.

1. **One acquisition-to-review handoff** (`d33943e5`, `3e82e102`, `153ffff8`, data `f3486255`, `954c6f9b`).
   - **Code.** An observation is one checked reference (`ObservationRef`, `read_observation`). A session
     plan's inputs can be taken from, or checked against, upstream outputs, recorded in `lineage.json`.
     A reviewer context can be derived from upstream outputs (`context-derive`), with a lineage that the
     input resolver recomputes before any run, refusing a missing or tampered upstream output.
   - **Data.** The reconstruction chain on saved data: 32 + 105 + 97 planned inputs equal the probe
     manifest's digests; every decision and sketch input is bound to the observation it was, with none
     unmatched.
   - **Checks.** The nine Phase A contexts derive byte-identical to the files the reviewers read. Their
     rendered sections are in all 56 stored first messages of the 21 Phase A runs. The three Phase A
     matchings reproduce their readings on every field. `report trace` walks a matcher's cell back to the
     extraction.
   - **The swap.** It changes the derived context and its lineage in the derivation's own test. On the
     real chain it stops at the decision sessions (gap 13).
2. **The second consumer** (`68dea3b5`). The compiled-unfiled probe's findings and asks are planned
   (11 PRs, 126 cells) through a thin adapter that imports the probe's own renderer. Both matchers are
   imported. Its reading, re-based on the shared report, prints `reading.txt` exactly.
3. **The prospective cutover** (`ce58055c`, `a5cb0966`).
   - One collector, one producer naming and one coverage rule for the shared paths. `report sessions` is
     new.
   - Locators are resolved through the worktree's `.ape` link.
   - The historical `probe unblind` refuses a matcher file that misses cells.
   - One task-to-PR reading is shared.
   - CLAUDE.md, the probe rule, four open todos, the CLI help and probes.py's docstring say which routes
     are historical.
4. **The other scaffold** (`fe80c4a2`). The Claude Code smoke plans are sealed and pass the dry run.
   Running them is the user's call (gap 14). The commands:

   ```
   source ~/.config/secrets/env.zsh
   ape/bin/python -m src.mathlib_review.review.cli session --plan results/pr_review_v5/probes/review-reconstruction-2026-10-19/measurements/smoke_claude_code_session --config configs/session/packet_session_opus55_claude_sub.yaml --run-name smoke_claude_code_session --execute
   ape/bin/python -m src.mathlib_review.review.cli match --plan results/pr_review_v5/probes/review-reconstruction-2026-10-19/measurements/smoke_claude_code_match --config configs/match/ask_match_opus55_claude_sub.yaml --run-name smoke_claude_code_match --execute
   ```
5. **The integration record.**
   - STATUS.md's rows now carry the live runs, the handoff, the second consumer, the cutover and the
     lead `task_config` change.
   - The integration was tried in a detached worktree (`.claude/worktrees/integration-trial`). The
     sequence was: `develop`, then the seven untracked design and review documents and the main
     checkout's `docs/plans/README.md`, then `dataflow-refactor`, then `review-reconstruction`, then
     `demonstrated-change`.
   - **The trial passed.** The suite ran 3157 tests, all passing, and `verify_frozen` reported ok. On
     the merged tree the Phase A trace finds each context by the file's own bytes, and the adapter
     prints `reading.txt` from its own probe folder.
   - **Conflicts and their resolutions:**
     - `review/runner.py`: keep the lead-run log line and review-reconstruction's `sample_limits`.
     - `.claude/rules/mathlib-review.md`: three places, keep every bullet.
     - `docs/plans/README.md`: keep both rows.
     - `docs/todo/README.md`: keep the new row and demonstrated-change's version of its own row.
   - Nothing was merged into `develop`.

## Before merging

- Commit the design documents (`task-dataflow-refactor-design`, the systems reading, the adversarial
  review, the plan and the audit) to `develop` first; they are untracked in the main checkout and this
  branch links to them.
- Read `.claude/worktrees/dataflow-refactor` against the in-flight branches mapped at the start:
  `review-reconstruction` adds `context_with_sections` and a cap fix beside code this branch touches
  only in `probes.py`'s matcher section; `demonstrated-change` adds a design (gaps 2 and 10).
- Two live runs on GPT-6 Luna through ELM are recorded above, USD 0.17 billed. The runs on the
  subscription route (the smoke plans, gap 14) and the v2-against-v1 calibration on the original route
  remain the user's call.
- The integration order and its conflicts are in "Closure work", item 5. On the merged tree, the
  Phase A runs' contexts are traced by their own bytes.
- `review-reconstruction`'s `033765c7` and `8b918cce` are on this branch as cherry-picks. Their
  changes are identical except in `.claude/rules/mathlib-review.md`, where this branch took only
  8b918cce's new bullet. Expect a conflict there when both merge; keep both sides' bullets.
