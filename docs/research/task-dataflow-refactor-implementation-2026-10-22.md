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
| (this commit) | The judge's report carries the same identity; `report conditions` names each repetition's; `cli report trace` for both instruments; the matcher's stage-ledger row; the reporting rule in `CLAUDE.md` |

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
