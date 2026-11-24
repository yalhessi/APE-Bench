# Checkout and experiment reference

The operational notes below were moved from the October project guide. Provider availability, quotas and timings are dated observations. Verify them before planning a run.

## Git

- **Branches.** `develop` is the integration branch (successor of `september-checkpoint`). `main` is
  the upstream APE-Bench drop; the guard hook refuses commits there. Work that may not land — a new
  experiment, a speculative refactor — goes on a topic branch off `develop` and is merged only when it
  succeeds. If it is abandoned, write its `docs/dead-ends.md` entry first, then delete the branch.
- **One working tree per session.** A branch is a pointer; the working tree is the files. Two
  sessions in one directory share the files whatever branch each believes it is on, so a switch in
  one rewrites the other's files under it (2026-09-12: `baseline-solo-agent` was created in a tree
  another session was committing to `develop` from; that commit landed on the wrong branch and
  `develop` had to be reset by hand). A new thread while this tree is in use starts in a worktree:
  `git worktree add -b <topic> .claude/worktrees/<topic> develop && .claude/worktree-setup.sh
  .claude/worktrees/<topic>` — the setup links the venv, `.ape/` and the untracked data stores from
  the main checkout, never tracked files. The `[session]` line reports other sessions in the tree,
  and the guard refuses `switch/checkout/rebase/clean/reset --hard` while any exist. The stash stack
  is shared by every worktree: never a bare `git stash` or `git stash pop`; set work aside with a
  WIP commit. The shared venv's editable install pins `ape` to the main checkout, so `pytest.ini`
  and the Claude Code settings put `src` first and `assert_repo_root` refuses a mixed tree; in your
  own shell in a worktree, `export PYTHONPATH=$PWD/src`.
- **The data stores are shared by every worktree, so a branch never regenerates one that `develop`
  checks.** `data/` is linked, not copied. On 2026-09-24 a topic branch grew `scored_pr_numbers()`
  and rewrote `data/pr_review_v5/review_join` to match, and `develop`'s suite went red for every
  session, because the report no longer counted what `develop`'s source counts. Regenerate such an
  artifact as a step of the merge, not before it. The precedent index was different: an index that
  excludes *more* PRs still satisfies `develop`'s check, so it could be rebuilt early.
- **Small logical commits, always.** One commit is one thing, with the suite green. Message form is
  `<area>: <what changed, and why it is right>`, measurements in the body (see `git log`). Commit at
  each step boundary — a standing instruction (2026-09-11): uncommitted work spanning steps is how the
  codebase imploded and threads got duplicated across places. The hook warns past 10 files / 400 lines
  uncommitted; the median commit here is 5 files. Never push, rewrite published history, or delete a
  branch without being asked. Commit by explicit path, never `git add -A`.
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
| Per-task budget | `ExecutionLimits` (task-data key `execution_limits`): `billed_cost_limit` binds **billed** cost, `token_limit` binds **processed tokens** (prompt + completion, cache-inclusive). Two fields on one object, enforced at one checkpoint — never a second limiter. A zero-priced model needs the token half; nothing converts between them. Calibration: `docs/research/2026-09-22-token-budget-calibration.md` |
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

- **Every number names its measurement.** Two instruments are live and they answer different
  questions: the registered judge (`semantic-judge/<JUDGE_VERSION>`: one finding against one atomic
  gold obligation, hits out of the denominator) and the raw-ask matcher (`ask-match/<version>`: a
  maintainer's ask against all of a reviewer's findings, reach as a fraction of asks, comparable only
  within one seal). Quote a number with its instrument and version, reference set, seal, subjects'
  output channel (submitted, finalized, published), denominator and replicates -- the report's
  `measurement` block holds all of them (`report match`, the judge's `semantic_report.json`, the
  `measurements` row of `report conditions`). Never pool or subtract numbers from two instruments or
  two seals. A matching is planned, run or imported, and read through `analysis/matching.py`
  (`cli probe match-plan`, `cli match`, `cli probe match-import`, `cli report match`); sessions over
  folders, and what one session hands the next or a reviewer, through `analysis/sessions.py` (`cli
  probe session-plan --input-from`, `cli session`, `cli probe session-import`, `cli probe
  context-derive`, `cli report sessions`); `cli report trace` follows any one number back to its
  bytes. `probe seal`, `match-inputs`, `unblind` and per-probe launchers are historical. (2026-10-22:
  the user could not tell which results were being reported or how two reports compared.)
- Report at the altitude the evidence supports. A negative result means *the designs tried so far*
  did not work; enumerate the untried designs before concluding anything, and mark findings
  provisional until replicated. (The user has corrected over-claimed negatives three times.)
- Three repetitions minimum, reported as mean / union / stable. The semantic judge's self-agreement
  is about 90%, so one obligation at n≈8 is ±12pp — larger than most deltas discussed.
- Before iterating an LLM stage's prompt, read that stage's *inputs*: every prompt-side "fix" in
  this project's history was really an evidence gap.
- Read the routing degenerate-check before any recall number. Externally, never show the
  leak-inflated Phase-C numbers (~70%).
- **`location_recall` is not a quality signal.** It counts obligations where some candidate
  anchored to the gold `change_id` *without* naming the issue — the agent asking for something
  else at the right line, which is at best neutral. For coverage use `coverage_gaps` (0 means
  every gold site had a job, and it is gold-independent); for what the reviewer could express
  use `issue_recall_reachable`. A 2026-09-15 comparison was nearly read as a regression on a
  location drop that meant only that a quieter run said fewer off-target things.
- Gold is a lower bound, so `gold_alignment_rate` is not precision and a candidate absent from
  gold is unaligned rather than wrong. Nothing in the current evaluation adjudicates the ~90% of
  findings that are not maintainer obligations; until something does, precision claims in either
  direction are unsupported.

## Running

```
ape/bin/python -m pytest tests -q -n auto --dist loadfile            # suite, ~45s
ape/bin/python -m src.mathlib_review.release.verify_frozen verify   # must print ok
R="ape/bin/python -m src.mathlib_review.review.cli"
$R plan --config <cfg> --run-name <name>                             # preflight, spends nothing
```

Tests that need a built Lean workspace under `data/code_execute/` fail on a fresh clone; expected.

**A Lean build from a shell needs `ELAN_HOME=/research/projects/proofedit/ya475/.elan`.** Without it
elan unpacks a missing toolchain into `~/.elan`, and the home directory is at quota: the first
stage-5 base build (2026-10-06) died in `lake cache get` with "Quota exceeded (os error 122)" and left
871 MB of partial unpacks there. The project's elan home holds the toolchains; `PATH` alone is not enough.

**Never gate a commit on `pytest … | tail`.** A pipeline's status is its last command's, so
`pytest … | tail -2 && git commit …` commits a red suite (2026-09-23: two failures went in that
way and the commit had to be amended). Capture pytest's own exit code — redirect to a file and
check `$?`, or `set -o pipefail` — before the commit step. The prose did not stop it (2026-10-01:
a failing script, `| tail -3 && git commit`), so `guard.sh` now refuses a commit whose `&&`-chain
holds a pipe, unless `pipefail` is set (`tests/cli/test_guard_hook.py`).

**An edit and a commit do not share one command line.** In `check && edit; test; commit`, a failing
check skips the edit while the test and commit after the `;` still run -- on the old files, so the
suite passes and the commit carries the unfixed code (2026-09-24: a constructor probe failed, the test
edit it guarded was skipped, and the commit had to be amended). Edit, then test, then commit, each
gated on the one before.

**The suite is parallel, and the flags are not in `pytest.ini` on purpose.** `--dist loadfile`
keeps a file's tests on one worker, which the module-scoped fixtures need. Leave the flags off a
targeted run — worker startup costs more than the file does (`tests/orchestration/test_pipeline.py`
alone: 0.24s serial, 2.38s under `-n auto`) — and off `--pdb`. A bare `pytest tests -q` still
passes, just serially, so a checkout without `pytest-xdist` degrades rather than breaks.

**`No space left on device` from the suite while `df -h /tmp` shows space is `/tmp` out of inodes.**
`/tmp` is a 1M-inode tmpfs that other sessions' scratch fills (2026-10-22: 98% used, 27k free, 502 GB
of bytes free), and one suite run needs tens of thousands. Check `df -i /tmp`; run with
`TMPDIR=/dev/shm/<your dir>` (148M inodes), and never delete another session's scratch to make room.

**A slow test is nearly always repeated work, not coverage.** The suite was 350s in 2026-09-22 and
88% of that sat in 60 of its 2,213 tests; the three worst were 50% between them and none was
buying anything. They were, in order: a test asserting payload *key spellings* that built the
library exposure index first (130s), an AST guard that rebuilt its docstring set once per string
constant (25s), and a catalogue that read the Mathlib tree four times over (22s). Profile the
outlier before marking it slow, splitting the suite or reaching for any other machinery — all
three were plain redundancy, and the fixes took a line each.

**Providers.** `OPENAI_API_KEY` for the `gpt_*` models; `ELM_API_KEY` for the `elm_*` ones, which
go through the University of Edinburgh gateway. The OpenAI key stopped working on 2026-10-05
(HTTP 401, project archived), so a `gpt_*` run now only retries. `elm_gpt_5.2`, `elm_gpt_5.4` and
`elm_gpt_5.5` are the same snapshots through ELM and take `openai_api: responses` with carry-over
(measured that day; `docs/todo/llm-openai-responses-provider.md`). **An OpenAI model runs only on
Responses with `openai_responses_reasoning_carryover: true`**: Chat Completions, or carry-over off,
drops its reasoning every turn, so both are refused before the first request and at `cli plan`
(`reasoning_drop_refusal`, user, 2026-10-05). 103 of the 129 GPT configs then on disk were written for
the old paths and are refused rather than reinterpreted; a new GPT config states both lines. The judge base
pins `elm_gpt_5_mini` since 2026-10-06 (the same snapshot as the old `gpt_5_mini`; 73 of 76 issue
verdicts agree, `results/pr_review_v5/probes/judge-elm-2026-10-06/`), and the move forked its cache: an
audit judged before then does not resume into one judged after. The ELM key has a fixed **£500**
limit (GBP, not dollars): `ape/bin/python -m ape.llm_clients.elm_budget` prints what is left, from
ELM's `GET /api/v1/costs` (spec at `/swagger-ui/`). ELM syncs that figure periodically (`asOf`), so
spend since the last sync is not in it, and the run caps are USD list-price estimates, not ELM's bill. Separate variables on purpose — both are usually
exported in the same shell and neither may stand in for the other. `elm_*` names are their own
canonical models, not a `base_url` override, so the run plan records which endpoint produced a run;
switching one forks the judge cache, so switch at a run boundary. The four open-weight `elm_*`
models are priced at **0.0**, which makes every dollar cap vacuous; the token block in
`configs/bases/v5_generation.yaml` is what bounds a run on one, and `cli plan` refuses a
zero-priced run that has left it unset. Llama 3.3 and EuroLLM are served without tool-calling and
are refused by name if a scaffold sends tools; Qwen3.5 and Mistral-Small-4 are agent-capable.

**Claude models run on the Claude Code subscription route**, not through `llm_clients`. Set
`llm_config.model_name: null` with `claude_model` (a full name), `cli_version` (a binary at
`data/resources/claude-<v>-linux-x64`; the SDK's bundled CLI cannot run Opus 5.5) and `effort`.
The login is `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`, in `env.zsh`), and the preflight
refuses a run without it. A subscription bills nothing per token. Its five_hour window held about
one dev run (20-24M processed tokens), and that window is shared with interactive use. So check the
token before a run: a one-line `claude -p` with `HOME` set elsewhere reports its `rate_limit_event`.
A spent limit fails the sessions it reaches, never as a short review, and `run --resume` then
requeues exactly those. **Since 2026-10-06 the two Pro accounts refuse** (`CLAUDE_CODE_OAUTH_TOKEN_B` and `_C`:
"Your organization has disabled Claude subscription access for Claude Code"); only the primary
token runs, and it is the user's interactive account (its seven_day window stood at 67% that day),
so a run on it is the user's call, asked before, never assumed. Configs: `configs/pr_review_v5_dev_medium_*_claude_sub.yaml`. Readings:
`results/pr_review_v5/probes/claude-models-2026-10-01/`.

**The self-hosted model is DeepSeek-V4.1-Flash on `first`: the free iteration tier** (2026-10-07). It
reaches 8, 6, 9 of 23 on the dev held-out 12 (Opus 5.5: 7, 7), at about 35 min a rep and $0.
`local_deepseek_v4.1_flash` is `LLMProvider.LOCAL` (no key, `http://127.0.0.1:8012`); config
`configs/pr_review_v5_dev_medium_local_ds41_contract2.yaml`.
- **Server:** `sbatch /research/projects/proofedit/ya475/localmodel/serve_ds41.sbatch` (8 GPUs, ~12 min
  to serving), then the probes `probe_correct.py` and `probe_carry.py` before any review.
  - The defaults are the only working setup: a vLLM nightly with an SM120 patch, DSpark speculative
    decoding and a 1M context.
  - It deletes its 476 GB `/tmp` weight copy, which is node RAM, once serving.
- **Run the harness as a Slurm job on `first`** (`run_ds41_keepthink.sh` is the pattern), not from a
  session: the server binds to localhost.
- **Never edit a gate script while its job runs.** Bash reads a script as it goes (fd 255 holds the
  next command's offset), so an edit above that offset reroutes the gate mid-line. On 2026-10-08 a
  comment edit to `run_stage_d_gate.sh` under job 434256 was caught at offset 5412 and the submitted
  bytes restored. Edit after the job ends, or submit a copy.
- **Earlier thinking must reach the server.** A local model takes the plain `MessageFormatter`,
  because `OpenAIMessageFormatter` drops `reasoning_content`
  (`test_a_local_model_gets_its_earlier_thinking_back`). With it dropped, DeepSeek re-derived ~8k
  thinking tokens a turn, and a session wrote ~215k tokens against ~62k.
- **Qwen3.5-397B is the floor tier** (`docs/dead-ends.md`).
- Readings: `results/pr_review_v5/probes/local-ds41-2026-10-06/`.

**A missing or rejected key does not fail; it retries for hours.** `llm_clients/client.py` retries
every exception except four, authentication included: 100 attempts, waits up to 60 s plus jitter,
~1.5-2 h per call per job, logged only as a WARNING "API call failed, retrying". (A 400 whose body
names a parameter is the fourth, `RequestRejectedError`, and fails at once.) A run with a bad key
looks alive and bills nothing. Before `--execute`, confirm the provider's variable is set in the
launching shell (`source ~/.config/secrets/env.zsh` in the same command); in the first minutes,
confirm `completed with success` lines appear and "API call failed, retrying" does not. The fix is
queued in `docs/todo/framework-defects-2026-09.md`.

**Launch a paid run detached, and read its bill from the outcomes, not the log.** A run started as a
Claude Code background task dies with that process: stage 5's gpt-5.5 runs did at 7 of 16 sessions
(2026-10-07). **`setsid nohup` is not enough**: the shell sits in a login-session scope
(`/proc/self/cgroup`), and tearing that scope down kills every process in it -- S2 died that way at 10
of 16. Start it as a user unit, which lives outside the session:
`systemd-run --user --collect --unit=<name> /bin/bash -c "exec <command> >> <log> 2>&1 < /dev/null"`
(it survived the next restart; `systemctl --user status <name>` to watch it). A unit starts without the login `PATH` and `HOME`: pass `--setenv=PATH="$PATH" --setenv=HOME="$HOME"`, or a tool resolved from `PATH` vanishes (2026-10-11: a window check read "unknown, 100%" and stopped a Claude batch). Lingering is off, so it
lasts while any login session does; a Slurm job outlives even that. **A user unit is still in
`/user.slice`, and systemd-oomd kills there under memory pressure** (60% for 20 s, `oomctl`): it picks
the cgroup with the most reclaim, not the biggest, so a 272 MB unit reading files died `oom-kill` at
08:01 on 2026-10-07 while the `vllm-ds4` Slurm job held 1,000 GB of `first`'s 1,129 GB; the
interactive sessions that died the same morning sit in the same slice. Before a long run, look at
`squeue -w first` and `oomctl`; a Slurm job is outside `/user.slice`. `run --resume` keeps the finished
sessions. The `completed with success (cost=$...)` log line is **nominal** cost, uncached list price;
billed is `billed_cost` in each `tasks/*/task_outcome.json`, five times smaller on those runs ($65.44
against $13.15 for seven sessions). Read as a bill, the log line stopped a run that was within budget.
