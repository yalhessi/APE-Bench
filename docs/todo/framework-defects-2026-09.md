# Framework defects found while adopting the subtask contract

**Status** — open; three unrelated defects in `src/ape/`, each cheap, each changing behaviour
**Cost** — no model spend to fix; each needs a run to confirm it changed what it should
**Owner question** — which of these is a bug worth fixing, and which is a contract nobody meant?

Found by reading, not by failing: the 2026-09-21 subtask-contract work touched every nested
call site and these three were beside it. None is fixed there, because each changes what a run
does and that commit's whole claim was that nothing changed.

## 1. `judge_mode` has never reached either nested judge

`judgment/task.py` builds `LeanJudgmentConfig(judge_mode=judge_mode)` and passes it as
`task_config=` on the scaffold config; `review_gate.py` does the same with
`LeanReviewGateConfig`. Neither arrives. Every execution path reaches the task through
`task_data` and the orchestrator's config —
`worker._execute_with_early_stop_monitoring` → `runtime.run_task` → `main_from_params` →
`create_task_from_data(task_data, config, task_config_overrides=config.task_config_overrides)`
— and `create_task_from_data` builds a **fresh** `task_config_class(**valid_overrides)` from
`task_config_overrides` alone (`tasks/base.py`). `config.task_config` is never read.

So both judges have always run under their config class's defaults. This is the same shape as
`CONTEXT_TOOLS` filtering `naming_norm` out of an arm's grant after it was registered
correctly, and as `execution_limits` being dropped between the orchestrator and the worker
(`ac396ee`): a value set in the place that looks authoritative, and a second path that does not
read it.

**What would close it:** decide whether `task_config` on a scaffold config means anything. If
it does, `create_task_from_data` should seed the overrides from it; if it does not, the field
should stop being settable and both callers should pass `task_config_overrides`. Then check
what a judge run does differently — the defaults may be what everyone has been measuring, in
which case the fix moves numbers and needs a new run name.

## 2. `theorem_proving` cannot construct its own result

`tasks/lean_tasks/formal_math/theorem_proving/task.py` calls `create_result(...)` without
`theorem_statement`, which `LeanTheoremProvingResult` declares **required**. Every termination
therefore raises inside the surrounding `try`, which logs a warning and continues — so the task
reports no result and says so only in a log line. Independent of the `create_result` refusal
added on 2026-09-21: this one raised before it and raises the same way after.

**What would close it:** pass the statement (it is on `self.data`), or make the field optional
if a result without one is legitimate. One line either way; the question is which.

## 3. `TaskOutcome.resumable` is computed against the orchestrator's cap, not the child's

`from_samples(sample_max_cost=config.execution.sample_max_cost)` decides whether a sample may
run again, and a child carrying its own `ExecutionLimits.billed_cost_limit` — every v5 arm —
is judged against the orchestrator-wide value instead. A job that exhausted its own $0.30 cap
under a $1.00 orchestrator reads as resumable, which makes its `TaskOutcome.execution_status`
`paused` rather than `failed`.

Harmless today because the delegation ledger reads the finest *sample* status, not the
outcome's. It stops being harmless the moment anything resumes a wave.

**What would close it:** pass the child's limit where one exists. The ledger vocabulary must
not move with it — `ledger_status` is what the routing analysis reads.

## 4. A synthesised failure is written as a result, against the rule that says not to

The 2026-09-06 plan states it: *"Never synthesize a result to represent a failure or pause."*
`worker._try_aggregate` does exactly that — a task whose samples all failed gets a bare
`BaseTaskResult(success=False, error="All samples failed: [...]")` written to
`task_result.json`, and `_write_task_outcome` is then called with `has_result=True`, so the
outcome reads `execution_status: completed` for a task that completed nothing.
`TaskOutcome.has_result`'s own docstring says the opposite happens.

`ChildRun` sidesteps it by asking whether the result was a *success*, and keeps the error
sentence on `ChildRun.error`, which is the most specific account of the failure anyone has. The
underlying contradiction is untouched.

**What would close it:** either stop writing the synthetic result (and let `task_outcome.json`
carry the failure, which is what it exists for), or amend the rule and the docstring to say a
failure result is written deliberately. Both are readable; the current state is not.
