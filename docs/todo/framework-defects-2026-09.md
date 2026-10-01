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
**Fixed 2026-09-23 (`e163523`):** a fanout or rules run reads its scheduled jobs through
`collect_child_runs` and writes each one's status, cost and counts on its ledger row, and a mandatory
job that did not succeed is a coverage gap. It hit a paid run first: `pr5_V2_verdicts_fanout4_rep1`
reads `paused: 0` for a job that paused at $0.18 and lost its answer.

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


## Added 2026-09-23: a missing or rejected API key retries for hours instead of failing

**Motivating example.** The user, before the first paid work-enumeration rep: *"Unless the API key
is supplied appropriately, the process may be stuck retrying"* -- seen in runs the day before.
The code agrees. `src/ape/llm_clients/client.py:125-141` retries **every** exception except
`ContextLengthExceededError`, `MalformedResponseError` and `StreamingInterruptedError`, so an
authentication or permission failure is retried like a transient one: `retry_max_attempts: 100`
(`llm_clients/config.py:326`) with exponential waits capped at 60 s plus up to 10 s of jitter is
roughly **1.5-2 hours per call, per job**, and the only trace is a WARNING, "API call failed,
retrying ... error_type: AuthenticationError". A run with a bad key looks alive for hours and
bills nothing, which is the one outcome no cap or preflight catches.

**What would close it:** (1) a provider's authentication and permission errors (HTTP 401/403)
are not retried -- they are not transient, and the first one ends the attempt with its message;
(2) `cli run --execute` refuses to start when the provider's key variable is unset in the
launching environment (`OPENAI_API_KEY` for `gpt_*`, `ELM_API_KEY` for `elm_*`, per `CLAUDE.md`,
"Providers"), where preflight already refuses other unrunnable configurations. Test both with a
fake provider raising the real exception class.

**Until then**, `CLAUDE.md` ("Providers") carries the launch check: confirm the key in the launching
shell, then watch the first minutes of the log for completed jobs and for that warning.

**Risk:** a gateway that returns 401/403 transiently (a token-refresh race) would now fail a job
instead of waiting. None is known for OpenAI or ELM; if one appears, a single short retry is the
narrow version.

## Added 2026-09-23: the tool schemas an arm is shown are sealed nowhere

A plan seals each arm's prompt text (`prompt_sha256`), its tool *names* (`tools_sha256`, over
`FOCUSED_PROMPTS[arm][0]`), the workspace tools (`scaffold_config_sha256`) and its context grant
(inside the agenda). It does not seal the tools' **schemas** -- the argument descriptions the model
reads. So a change to a tool's description reaches every run, control included, with no identity
moving: the `severity` description on `CandidateSubmission` (unification commit C3) is one; the
`lean_verify_edit` example naming `Subgroup.closure_pow_le`, PR 33401's gold target
(`eval-unseen-window.md`), is another that no gate or hash can see. Two runs with byte-identical
plans can therefore have shown their arms different tool text. The fix is a `tool_schemas_sha256`
per arm over the rendered JSON schemas of the tools its task registers, sealed beside
`tools_sha256`; it moves every plan's identity once, so it lands at a run boundary with its own
dated reason.

## gpt_5.2's cached-input rate is gpt-5's (found 2026-09-30)

`MODEL_MAPPINGS["gpt_5.2"]` prices cached input at $0.125 per 1M. OpenAI's pricing page gives $0.175
(read 2026-09-30); $0.125 is gpt-5's rate. So every gpt_5.2 billed figure in the record understates
cached input by $0.05 per 1M. That is a few percent of a run: cached input is most of the prompt
tokens, and the whole billed cost is mostly output. It is not fixed in place, because
`tests/datasets/test_cost_model.py` reproduces the record's figures exactly at $0.125. A fix needs a
dated price history, so an old figure keeps its rate and a new run gets the real one.

## A rejected request is retried like a transient one (seen again 2026-09-30)

The known retry defect (`llm_clients/client.py` retries every exception but three), with a second
cause. `gpt-5.4` and `gpt-5.5` at `reasoning_effort: high` return HTTP 400 on Chat Completions:
"Function tools with reasoning_effort are not supported for gpt-5.4 in /v1/chat/completions. To use
function tools, use /v1/responses or set reasoning_effort to 'none'." The client retried it 27 and
25 times in the first ten minutes (`probe_postcutoff_gpt5{4,5}_Gr_rep1`), billing nothing, until the
runs were stopped by hand. A 400 whose message names an unsupported parameter can never succeed, so
the fix is to refuse 400s, not only authentication errors, and to surface the provider's message.

**Fixed 2026-09-30, for 400s** (`openai-responses-provider`). `RequestRejectedError`, a subclass of
`ProviderError`, is never retried. The provider raises it for an HTTP 400 whose body names a
parameter (`error.param`), and ELM's own pre-send refusals raise it too. Those refusals (tools on
Llama/EuroLLM, an effort the gateway refuses) had been plain `ProviderError`s inside the retried call,
so each was repeated a hundred times. A 400 that names no parameter is still retried: the only other
400 in the run logs, "Could not finish the message because max_tokens or model output limit was
reached", succeeded on retry (`pr_review_v4_judge_r0pinned_rep1`). The 401/403 half of the
2026-09-23 entry above is still open. Pinned by `tests/ape/test_request_rejection.py`.

## `reasoning_effort` and `openai_api` change what a run measures, and a resume may change them (found 2026-09-30)

Both live only inside `scaffold_config_sha256`, and `RESUMABLE_PLAN_FIELDS`
(`src/mathlib_review/review/runner.py`) lets a resume change that hash, because it also carries
retries and timeouts. So `cli run --resume` with `reasoning_effort` raised from `none` to `high`, or
`openai_api` switched, only writes `run_plan_revision_N.json` and a warning. The run's finished tasks
keep the first condition, and the rest run under the second. Not seen happening. The motivating
example is the code path, found while adding `openai_api` and `openai_responses_reasoning_carryover`,
which inherit the same status. The fix is a semantic plan field over the llm_config keys that change
what a run measures (`reasoning_effort`, `openai_api`, the carry-over, `temperature`; `model_name`
already is one). It moves every plan's identity once, so it lands at a run boundary.

## Codex has drifted from the relay, and Claude on a subscription bypasses it (found 2026-09-30)

Found by reading, while asking what running the reviewer through Codex, or through Claude on a
subscription, would need. Neither scaffold has run a review (`e6541bc`).

**None of this is in the task.** The solo review task runs unchanged under every scaffold, as the
proof-engineering tasks did upstream. The paper's scaffold comparison put the same models (GPT-5.2,
Gemini 3 Pro and Flash) through all three scaffolds on identical tasks, with each harness's model
calls going through its relay to APE's client. Budget, usage and transcripts live in that relay,
so they are the same in every harness. The paper reports "APE-Agent outperforms Claude Code and
Codex by 15-23 percentage points across models". Upstream's registry has no Anthropic model, so
Claude the model was never in that comparison. On the relay path `claude_code` needs no code
change for a review, only the leak audit.

**Except the task's system prompt, which neither `claude_code` nor `codex` delivers.** `ape_agent`
appends `task.create_system_prompt()` to its workspace preamble (`1d32ef7`,
`ape_agent/conversation.py::_task_system_prompt`); the other two build only the preamble and never
call it. The solo task's `SOLO_SYSTEM`, or the brief `system_prompt_file` names (`brief_G.md` on
the post-cutoff set), reaches the model through that method alone. So under either scaffold the
reviewer would run with no brief, and a harness comparison would also be a prompt comparison.
`cli plan` cannot see it: plan passes for the G config with `--set scaffold_type=claude_code` and
with `codex`, because it never starts a scaffold. Fix before any C or Codex run: move
`_task_system_prompt` somewhere all three scaffolds share, and pin it with a test.

**Codex.** Upstream pinned both CLIs as binaries under `data/resources/` (`claude-2.0.37-linux-x64`,
`codex-x86_64-unknown-linux-musl`, in `get_required_resources`); that directory is not in this
checkout. The relay serves only `/chat/completions` (`codex/relay.py`), and the installed
`codex-cli 0.144.5` refuses it: its binary carries "`wire_api = \"chat\"` is no longer supported ...
set `wire_api = \"responses\"`". Batch mode also needs `codexbridge/`, a git submodule of a
third-party repo pinned to a 2025 commit, which is not checked out (the directory is empty).
`codex exec --json` with `codex exec resume` would replace it with no Node service. The scaffold
defaults to `sandbox_mode: danger-full-access`. No review config and no containment test exist.

**Claude on a subscription.** Setting `llm_config.model_name: null` skips the relay, so Claude
Code uses its own login. Four things break without the relay:
- `HOME` is set to the attempt's `workspaces/`, so `~/.claude/.credentials.json` is not found. A
  `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` does reach the CLI, because the SDK passes
  the parent environment through (`subprocess_cli.py:430`).
- `get_token_usage` delegates to the relay, so there is no usage and no `ExecutionLimits`.
- `get_claude_code_session_id` reads the relay, so no transcript hardlink is written.
- `model=None` means the CLI's default model, which the run plan does not record.
A spent subscription usage limit also needs handling as a failed attempt, or it reads as an
empty review.

**What would close it:** for Codex, an older pinned CLI or a `/responses` route on the relay,
and the bridge checked out or replaced. For Claude there are two routes. An Anthropic provider in
`llm_clients` and an API key would keep the design and reach all three harnesses, `ape_agent`
included. A subscription reaches only Claude Code, and needs usage and the session id read from the
SDK's own messages, the model
pinned and recorded, and the usage-limit error mapped to a failure. Both still need the leak
audit that the `solo_claude` configs' headers require.

**Claude Code, on the relay path: fixed on `claude-code-harness` (2026-10-01).** The task's system
prompt now reaches the model under every scaffold (`4816cd2`). `contain_to_workspace` adds a
PreToolUse refusal and a per-attempt transcript audit (`bf26b5e`). The relay reads the bundled
2.1.139 CLI's session ID, and the transcript is found by name (`d7f84ae`). APE's MCP server and the
grant are pre-approved, because `dontAsk` refused 7 of 8 calls otherwise (`8dbcf9c`). Smoke 3 (PR
41930, $0.14, 26 s) ran end to end: brief delivered, audit clean and usable, one submission landed,
no findings, as with both G runs on that PR. Smokes 1 and 2 ($0.00 and $0.38) are the two failures
those commits name. Each session's CLI now reaches its own relay (`196d948`): in
`probe_postcutoff_gpt52_G_claude_rep1` four of six sessions shared one, so that run is spent and is
not a measurement. Its commit guessed that the 12 `CancelledError` tracebacks meant sessions cut off
at the shared turn limit. That was wrong: the valid runs show the same 12, two a session, from the
session being stopped at submission. The valid runs are `probe_postcutoff_gpt52_G_claude_v2_rep{1,2,3}`
(`d682c71`), 18 of 18 attempts audited clean and usable.

## `lean_verify` with a `file_path` refuses every path, under every scaffold (found 2026-10-01)

`toolkits/execute/lean/tools.py` resolves `workspaces_dir / file_path` and then requires the result
`is_relative_to(workspaces_dir)`. `target/` is a symlink into the shared reviewed-workspace store,
so every `target/...` file resolves outside the workspace. `scratch/Review.lean` fails as well,
which suggests `workspaces_dir` is itself unresolved, though that is unchecked. Measured in
`probe_postcutoff_gpt52_G_rep1` and `_rep2` (ape_agent): 0-3 "File path outside workspaces
directory" errors a session, on `target/` and on `scratch/` paths. Smoke 3 under Claude Code hit
it twice and stopped compiling. `lean_verify_edit` is unaffected, because it reads
`target_workspace.path` directly.

**It is not neutral between harnesses** (corrected the same day, from the three-repetition run
`d682c71`). Under Claude Code it refused 29 of 32 `lean_verify` calls, against 13 of 18 under
APE-Agent. Claude Code's preamble is built with absolute paths (`use_absolute_paths=True`, from
`.resolve()`), so it advertises the store paths, which the check always rejects. APE-Agent's
relative `target/` paths fail too, but less often. So the harness comparison on the post-cutoff
set carries this difference as well as the harness's own. **What would close it:** compare resolved paths with a resolved
root, and allow the task's provisioned workspaces (the same roots as
`claude_code/containment.provisioned_roots`). It changes what every review condition can do, so it
lands at a run boundary, with G re-run beside whatever is compared against it.
