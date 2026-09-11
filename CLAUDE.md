# APE-Bench — Mathlib PR review

Research fork of APE-Bench (arXiv 2504.19110). The question: given a real Mathlib PR that
already compiles, would a maintainer merge it, and if not, what specifically would they ask
for? Throughline: *verifiable correctness is not enough.* Exploratory and long-running, with
many threads, some abandoned. Read the record before proposing anything that sounds new.

## Where the truth lives (read before designing)

- `docs/PROJECT-STATUS.md` — index of the whole effort and the honest ledger of what is unfinished.
- `docs/plans/STATUS.md` — every planned item marked built / partial / not built, checked against the tree.
- `docs/dead-ends.md` — abandoned threads and retracted conclusions, each with what would reopen it.
  **Check it before starting, or "rediscovering", a direction.** If a proposal is on that list, say so.
- `docs/plans/<date>-*.md` are plans kept verbatim; `docs/research/` holds designs and result write-ups.
- Commit bodies carry the reasoning and the measurements; `git log` is the primary document.
- Auto-memory holds only the user's preferences, funder context and external references. Project
  facts belong in this file, in `.claude/rules/` (path-scoped), or in `docs/`.

## Session discipline

- **One thread per session.** A thread is one feature, experiment or subsystem — what would be one
  topic branch or one commit series. When a prompt starts a different thread from the one this
  session has been on, say so in one line and recommend a fresh session (`/clear` or a new session)
  before continuing; offer to write any unsaved lesson to disk first. The `[session]` line printed on
  every prompt carries the compaction count; after any compaction, treat a new thread as a hard
  recommendation rather than a suggestion.
- **Record a lesson the moment it is learned**, in the strongest place it fits, in this order: a test
  or a refusal in code → a hook → this file → `.claude/rules/<area>.md` → `docs/dead-ends.md`.
  Never only in the conversation: compaction drops it, and the same mistake gets made again.
- At the end of any turn that finishes a step, say whether the step is committed.

## Git

- **Branches.** `develop` is the integration branch (successor of `september-checkpoint`). `main` is
  the upstream APE-Bench drop; the guard hook refuses commits there. Work that may not land — a new
  experiment, a speculative refactor — goes on a topic branch off `develop` and is merged only when it
  succeeds. If it is abandoned, write its `docs/dead-ends.md` entry first, then delete the branch.
- **Small logical commits, always.** One commit is one thing, with the suite green. Message form is
  `<area>: <what changed, and why it is right>`, measurements in the body (see `git log`). Commit at
  each step boundary — a standing instruction (2026-09-11): uncommitted work spanning steps is how the
  codebase imploded and threads got duplicated across places. The hook warns past 10 files / 400 lines
  uncommitted; the median commit here is 5 files. Never push, rewrite published history, or delete a
  branch without being asked.
- **Frozen artifact roots** — `inputs/pr_review_v4/`, `results/pr_review_v4/`, `data/pr_review_v2/` —
  are hook-guarded against Edit/Write because release manifests hash those trees. Add artifacts
  through the tooling (`verify_frozen build-lock`) and run `verify_frozen verify` after any change
  near them.

## Code: native to APE, and minimal

The framework is `src/ape/` (the top-level `ape/` directory is the venv). Before writing any runner,
orchestrator, budget or cost accounting, resume or cache, workspace materialisation, tool provider or
result store, find the primitive below and use it; extend it *in `src/ape/`* if it falls short.
Reimplementing one ad hoc under `src/datasets/` or `src/mathlib_review/` is the failure mode this
repo has paid for repeatedly: a hand-rolled `TaskRunner` loop lost the standard run layout, a
hand-rolled judge cache was replaced by orchestrator resume, budget tiers by `ExecutionLimits`.

| Need | Use |
|---|---|
| Run a batch of tasks | `TaskOrchestrator` (`src/ape/orchestration/orchestrator.py`): standard layout `.ape/runs/<run>/tasks/<id>/samples/<n>/attempts/`, resumable. Never a loop over `TaskRunner.run_task`. |
| Nested or delegated work inside a task | `BaseTask.spawn_subtasks` with `orchestration/subtasks.py::nested_config` |
| Per-task budget | `ExecutionLimits` (task-data key `execution_limits`); caps bind **billed** cost |
| Usage and outcome | `UsageBreakdown`, `TaskOutcome / SampleOutcome / AttemptOutcome` in `orchestration/models.py`; `task_result.json` only for a legal successful submission |
| A new task | subclass `BaseTask` / `BaseLeanTask` under `src/ape/tasks/`. Review tasks build on `src/ape/tasks/lean_tasks/formal_math/review/` (`base.py`, `ReviewArmTask`, `ReviewLeadTask`). `ape/tasks/__init__.py` imports every task package eagerly, so a task class outside that tree cannot import `ape.tasks.base` without a cycle; do not retry moving the base out. |
| Run configs | the standard scaffold YAML (`llm_config / execution / task_config / scaffold_type`), `extends:`, `extra="forbid"`, overrides as repeated `--set key=value` |
| Reading run artifacts | `TaskStorage.load_all_samples` → `Sample.successful_attempt.path`, never mtime globbing; workspaces via `WorkspaceStateManager`, never raw `.state` JSON |
| Lean execution and retrieval | `ape.toolkits.execute.lean`, `ape.toolkits.retrieve.lean` |

- Minimal: no new module when an existing one can hold it; no duplicate helpers; delete superseded
  code in the same commit that supersedes it. `tests/datasets/test_package_boundaries.py` and
  `test_pr_review_v4_no_duplicate_helpers.py` pin the current counts, which may only go down.
- One entrypoint per pipeline: `ape/bin/python -m src.mathlib_review.review.cli
  <plan|run|judge|bench|report|trajectory>`; PR data through `-m src.datasets.pull_requests.*`.
  Nothing that spends money runs without `--execute`; `--run-name` is required.
- Every knob that changes what a run does goes into the run name or the run plan, or the
  orchestrator silently resumes the wrong run.
- Data never moves, only code moves. All tooling runs from the repo root (`paths.assert_repo_root`).
- `sealed_from_payload` and `sealed_model` (`src/mathlib_review/io.py`) produce different digests;
  merging them rewrites every frozen hash. Task `type` strings keep their `v5` spelling because they
  sit inside spec hashes.

## Reporting results

- Report at the altitude the evidence supports. A negative result means *the designs tried so far*
  did not work; enumerate the untried designs before concluding anything, and mark findings
  provisional until replicated. (The user has corrected over-claimed negatives three times.)
- Three repetitions minimum, reported as mean / union / stable. The semantic judge's self-agreement
  is about 90%, so one obligation at n≈8 is ±12pp — larger than most deltas discussed.
- Before iterating an LLM stage's prompt, read that stage's *inputs*: every prompt-side "fix" in
  this project's history was really an evidence gap.
- Read the routing degenerate-check before any recall number. Externally, never show the
  leak-inflated Phase-C numbers (~70%).

## Running

```
ape/bin/python -m pytest tests -q                                    # suite
ape/bin/python -m src.mathlib_review.release.verify_frozen verify   # must print ok
R="ape/bin/python -m src.mathlib_review.review.cli"
$R plan --config <cfg> --run-name <name>                             # preflight, spends nothing
```

Tests that need a built Lean workspace under `data/code_execute/` fail on a fresh clone; expected.
