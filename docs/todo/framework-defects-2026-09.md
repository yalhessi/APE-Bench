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

*Widened 2026-09-22.* The token ceiling was built with the same defect on purpose. `can_execute`
now takes `sample_max_tokens` beside `sample_max_cost` and both come from the orchestrator, so
fixing one half alone would leave the two halves of one ceiling disagreeing about what resumable
means. Fix them together.

*And a second, adjacent one found by the same measurement.* `Sample.get_accumulated_cached_cost`
— what the cost branch of `can_execute` reads — sums `attempt.cached_cost`, which for a lead is
**inclusive of its children**: `runner._merge_token_usage` folds `nested_token_usage` into the
result before the worker writes it. So a lead's resumability is decided by comparing a
self-plus-nested figure against a ceiling the conversation loop enforced on its own turns alone.
On the held-out runs leads recorded a median $0.712 inclusive against $0.067 of their own, so the
comparison is off by roughly 10x in the direction that refuses a legitimate resume.
`attempt.tokens` is deliberately self-only and does not inherit this; the two should agree once
this is fixed, and `subtasks.nested_usage` is where the asymmetry is documented.

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

*Measured 2026-09-22, and it is not only a paused task's own record that suffers.* On
`pr5_elm_qwen_tokencap_probe1` 10 of 11 arms stopped on their token ceiling. Each got a
synthesised `task_result.json` carrying `token_usage=None`, so all eleven read
`execution_status: completed` and `OrchestratorResults.total_token_usage` summed only the one
job that finished -- **27,593 tokens against a true 385,684**, a 14x under-report of what the
run consumed. The manifest's `self_tokens` now reads `task_outcome.json` instead
(`analysis/runs.py::scheduled_task_tokens`), which is a workaround at the reader rather than a
fix: every other consumer of `total_token_usage` still sees the short number, and on a paid
run `total_cached_cost` is short in exactly the same way.

**A second thing the same run showed.** In `fanout` the manifest reported `delegated: 11,
succeeded: 0, failed: 0, paused: 0` and `completion_status: complete`. Those three counters
are summed over delegation-ledger `status` fields, and a fanout ledger has no lead to write
them, so they are structurally zero however the run went -- eleven jobs delegated and none
accounted for is a sum that does not balance, and nothing refuses it. `arm_responses.jsonl`
had the one successful row. The `solo` mode already carries a note of this shape for
`context_calls_total` in `review/trace.py`; this is the same gap on the status counters.

**What would close it:** either stop writing the synthetic result (and let `task_outcome.json`
carry the failure, which is what it exists for), or amend the rule and the docstring to say a
failure result is written deliberately. Both are readable; the current state is not.

## 5. A pipeline's rows do not say they came from a pipeline

`StageRecord` declares `pipeline` (the root run) and `node` (which node of the graph), and
nothing writes either: both are `None` on every row, including the rows of the run that was
driven by `cli pipeline` on 2026-09-21. Verified on
`results/pr_review_v5/runs/pr5_verify_typed_handoffs_rep1/stages.jsonl`.

The rows are not wrong -- each says what its stage consumed, produced and transitioned -- but
the two fields that would let a reader reconstruct *which graph* produced them are declared and
empty, which is the "a field that is read but not implemented" shape one step removed: here it
is written by nobody rather than read by nobody.

It is empty because each stage writes its own row through its own `run()`, and the pipeline
deliberately does not reach into them -- the same separation that keeps every node runnable by
its own command. Threading the context would mean a reserved task-data-style key on the stage
call, which is a real design choice rather than a fix.

**What would close it:** either pass the pipeline context the way `execution_limits` travels --
as a reserved argument the stage records and otherwise ignores -- or delete the two fields and
let `pipeline.json` be the only record of the graph, joined by run name. The second is cheaper
and loses the ability to tell two nodes of one kind apart in the ledger, which is exactly what a
run carrying two judgements needs. Decide before a run carries two.

## Added 2026-09-22: `cli trajectory` cannot see a paused task

`iter_qwen_plumbing_33438_rep1` scheduled 9 arms plus a lead and 3 arms stopped on their token
ceiling. `cli trajectory` reports **7 conversations** — the lead and the 6 arms that finished.
The transcripts of the paused three are on disk; the tool does not reach them.

That is backwards from what the tool is for. After a `completion_status=partial` run the arms
you most want to read are exactly the ones that were cut off, and those are the ones it cannot
show. It is the same family as the defect already recorded in `.claude/rules/mathlib-review.md`
— read a nested run's children from what was SCHEDULED, never from `results.task_results`,
because a task that pauses returns before aggregation.

**What would close it:** `cli trajectory` on that run reporting 10 conversations, with the
paused arms' turns present and marked as truncated.

