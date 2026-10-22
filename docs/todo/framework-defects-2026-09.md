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

**Closed 2026-10-22** (branch `dataflow-refactor`, Slice 0 of
`docs/research/task-dataflow-refactor-design-2026-10-22.md`). `ape.tasks.base.resolve_task_config`
is the one resolution: class defaults, then a concrete `config.task_config` of the task's own class,
then the record's overrides, then the invocation's. A key that is not a field of the task's config,
or a concrete config of another task's class, is refused (`TaskConfigError`) instead of dropped. The
scaffold config now serializes a concrete task config with its class, so it survives the worker
boundary (pydantic dumps a field by its annotation, which had dropped every subclass field
silently). Nested children inherit no task settings: `run_subtasks(task_config_overrides=...)` is
the whole of what they get, and both judges pass `judge_mode` that way.
What moved: the two nested judges now run in the mode their caller set. The Mathlib review judge is
not one of them (it is a top-level task with its own config). In `lean_semantic_evaluation` the
caller's default and the judge's default are both `with_ground_truth`, so only a run that set another
mode changes. The reviewed-proof-engineering gate does change: its pilot sets `generated_only`, and the
gate now runs that way (`docs/todo/thesis-pilot-integrity.md`, defects 1-2). v5 lead arms no longer
receive the lead's run-level settings; on all 17 lead configs on disk the setting they kept was a
tool list equal to their own default, so no arm on disk receives anything different.
Tests: `tests/ape/test_task_config_resolution.py`, each asserted on the task the worker rebuilds.

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

## Added 2026-09-24: three defects that put false claims in every v5 run, found in a per-job review

Found reviewing all 124 jobs of `pr5_FD_family_fanout4_rep1` against the code
(`docs/research/family-division-fanout4-review-2026-09.md`), and confirmed in the source. Each
affects the ten-arm runs too, so each confounds any comparison of arm designs until fixed.

1. **`declares_identifier` matches the leaf, strips primes, and echoes the query**
   (`src/mathlib_review/evidence/evidence.py:172`, `searchable_identifiers` just above it).
   - `declaration_search` then tells an arm that `Dense.continuous_inf` "is declared in
     `Topology/Order/Lattice.lean` (before this PR)". The file holds the root `continuous_inf`;
     no `Dense.continuous_inf` exists at base.
   - Likewise `Int.ceil_natCast_add` is reported for what is really `ENat.ceil_natCast_add`.
   - **Effect:** 12 of that run's 74 findings (9 published) were false "already exists" or
     "collision" claims, from 6 of its 9 arms; at least 5 more in V3 on the same units.
   - The evidence collector uses the same function, so such claims also draw `supports`.
   - **Close it:** match the qualified name, tracking `namespace … end` blocks, or read the
     elaborated names (`retrieval/statement_index.py` on the `naming-from-statement` branch); keep
     primes; return the name actually found with `file:line`. Test on the two cases above.
2. **Verification artifacts join on `(work_unit_id, candidate_ordinal)`** (`review/conditions.py:208`).
   - Several arms share a unit and each arm's first candidate is ordinal 0, so an edit-less
     candidate inherits another arm's compiled edit and is published as `verified_compile`.
   - **Effect:** 7 findings in that run, 6 of them false claims from defect 1; 5 in V3.
   - 12 of 28 join keys in that run are shared by more than one artifact.
   - The artifact rows carry no arm or invocation id, so past runs cannot be re-joined, and every
     published count in the v5 record carries some of this.
   - **Close it:** write `invocation_id` on each artifact and join on it. Add a test with two arms
     in one unit, one with an edit and one without.
3. **`lean_verify_edit` with an empty `new_declaration` compiles the unedited file and reports
   success** (`review/base.py:335`).
   - 6 false greens in that run: library_fit 4, design 2.
   - The submission validator refuses the same input, and `splice_declaration` documents it as a
     deletion.
   - **Close it:** decide once whether it means deletion, and make the tool splice it or refuse it.

**All three closed (recorded 2026-10-06, at the worktree consolidation).**
1. `5e215ffe` (2026-09-30, on `develop`): a declaration matches by its qualified name, primes kept,
   and `declaration_search` reports the name it found at `path:line`.
2. `e4341209` (`814ed69d` from `arm-division`): artifacts carry the invocation and the join uses it.
   Rows written before it carry no invocation id, so older runs' `verified_compile` counts stay as
   they were measured.
3. `54263929` (`db07c835` from `arm-division`, adapted): half a declaration edit is refused. A line
   span with no `replacement` is a deletion, as the hygiene layer made it (`0a3d7d33`).

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

**A subscription can also go through the relay, as a pass-through (measured 2026-10-01, no
spend).** The check was a local listener that answers and never forwards. With
`CLAUDE_CODE_OAUTH_TOKEN` set, `HOME` elsewhere and `ANTHROPIC_BASE_URL` pointed at the listener,
CLI 2.1.269 sends the subscription bearer to that URL (`Authorization: Bearer sk-ant-oat…`, and
`oauth-2025-04-20` in `anthropic-beta`). With `ANTHROPIC_AUTH_TOKEN=relay_token` also set, as
`_get_env_vars` sets it, the CLI sends `relay_token` and drops the oauth beta, because that variable
outranks the token. The CLI's default model also moved with the credential: `claude-sonnet-5` under
the token, `claude-opus-5[1m]` under `relay_token`. So a relay mode that forwards Claude Code's own
request unchanged to `api.anthropic.com` would keep usage, the token half of `ExecutionLimits` and
transcripts. The relay never holds the token: the CLI attaches it and the relay passes headers on as
received. The subscription bills nothing per token, so it needs a zero-priced registry entry, as the
`elm_*` models have. The token must not go into `llm_clients`. The Agent SDK docs bar third parties
from offering claude.ai login, and press reports (2026-02) describe server-side refusal of
subscription tokens outside Claude Code. An Anthropic provider for `ape_agent` therefore needs an
API key. The gateway docs say nothing about OAuth through a gateway, and no request has been
forwarded yet.

**The relay's session id is broken on the installed CLI, whatever the credential.**
`_extract_session_id` looks for `__session_<uuid>` in `metadata.user_id`. CLI 2.1.269 sends a JSON
string there, `{"device_id":…,"account_uuid":"","session_id":"…"}` (the same capture), so
`claude_code_session_id` stays `None`. No transcript hardlink is written on the ordinary relay path
either. *Fixed on `claude-code-harness` (`d7f84ae`), merged with it: `_extract_session_id` reads the
JSON `session_id` as well as the old suffix, pinned by
`test_the_relay_reads_the_session_id_of_either_cli_generation`. This paragraph was measured on
`develop` before that merge. The subscription route (`75d85bd`) takes its session id from the SDK's
init message and needs neither.*

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

**The cost gap was the relay's, not the harness's (2026-10-01).** The three repetitions billed
$0.258 a session against APE-Agent's $0.051. Two relay defects explain most of it, and the system
prompt little: Claude Code's first-request prompt is 12.7K tokens against 9.1K.
- Claude Code opens its system prompt with a per-request `x-anthropic-billing-header` (a new `cch`
  each request). Forwarded, it broke the prefix at character 92, so OpenAI cached 0 tokens, against
  79% of input under APE-Agent (`5037f57`).
- Claude Code asks for every turn as a stream. Given JSON, it discards the reply and asks again:
  128 main-model requests for 64 turns, each billed twice (`04484fa`).
With both fixed, PR 43192 ran in 3 requests for 3 turns, mostly cached, for $0.050, against G's
$0.07 and $0.06 there. The findings of `probe_postcutoff_gpt52_G_claude_v2_rep{1,2,3}` stand,
since each turn used one normal reply. Their cost figures do not, and the relay's 40-turn limit
had been counting each turn twice. Residual per session, estimated with caching: 1.6x the requests
and 2.4x the output of APE-Agent, about $0.09 against $0.05. That is the harness's own difference,
from one set of runs.

**Claude on a subscription: built on `claude-subscription` (2026-10-01), and run end to end once.**
Each item above has a fix and a test (`bcdf81e`, `75d85bd`). The scaffold config pins
`claude_model`, `cli_version` and `effort`. The login travels as `CLAUDE_CODE_OAUTH_TOKEN`, and
both the preflight and the scaffold refuse a run without it. Usage comes from the stream's
per-reply events, then from the result's cumulative `model_usage`, and the relay's limit
checkpoint (`limit_error`) runs before each reply. The session id comes from the init message. A
spent limit, an error reply or result, a fallback model or a safety refusal fails the attempt.
The live probes behind it (the user's login, seven short sessions):
- **The bundled CLI cannot run Opus 5.5.** SDK 0.1.81's 2.1.139 refuses `claude-opus-5-5` with
  "version 2.1.280 or newer is required". It also takes Opus 5 and 4.8 for 200K / 32K models when
  they are 1M / 128K, so it would compact a long session early. 2.1.285 is pinned at
  `data/resources/claude-2.1.285-linux-x64`, copied from the VS Code extension; its sha256 is beside
  it. The relay route still runs 2.1.139, so a relay cell and a subscription cell differ in CLI
  release as well as model.
- **The refusal reads as a success to a check on `subtype`.** It arrives with `subtype: success`,
  `is_error: true` and status 400, so `is_error` is what the scaffold reads.
- **The login brings its claude.ai connectors.** Without `strict_mcp_config`, the model's second
  reply quoted a notice injected mid-session ("several claude.ai connectors aren't authorized
  yet: Asana, ..."). With it, nothing appeared. The route requires it, and also sets
  `ENABLE_CLAUDEAI_MCP_SERVERS=false` and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- **A launching Claude Code session leaks into its child.** The SDK passes the parent
  environment through, including `CLAUDE_EFFORT=xhigh`, the parent's session id and its
  messaging socket. The route blanks every inherited `CLAUDE*` variable except the token.

For the model cells of `docs/plans/2026-10-01-claude-models-under-the-harness.md` (on
`post-carryover-replan`), from Anthropic's model pages, read 2026-10-01:

| model | id | training-data cutoff | dev PRs (created 2025-12-18..31) | post-cutoff set (2026-07-08 on) |
|---|---|---|---|---|
| Opus 5.5 | `claude-opus-5-5` | Jun 2026 | inside | after |
| Opus 5 | `claude-opus-5` | May 2026 | inside | after |
| Opus 4.8 | `claude-opus-4-8` | Jan 2026 | at the edge: a PR's review and merge can fall after it | after |

All three are dateless IDs, each a pinned snapshot. The probe harness recorded no effort for its
Claude sessions. They ran as subagents of a Claude Code session, and today's sessions export
`CLAUDE_EFFORT=xhigh`, but nothing shows what the swap ran at. So the H-claude cell carries an
effort guess against the swap, and should say so.

**Run end to end (`fd971ce`).** The smoke ran on PR 41930: claude-opus-5-5 on CLI 2.1.285 at
xhigh, with `apiKeySource: none` on the setup token. Its audit was clean and usable (8 tool
calls), and it used 84,797 tokens over 5 replies, billing nothing. It filed no findings, as both
G runs did there. The launch needs `PYTHONPATH=$PWD/src` in a worktree. Without it, the first
attempt failed on four validation errors, and `load_run` now refuses that mix by name
(`4369298`).

**Calibrated on a large dev PR, uncapped.** `probe_dev_opus55_G_claude_sub_calib1` ran PR 33149
under G with max_turns 400 and a 20M token cap. The session took 16 replies, 29 tool calls and 8
minutes, and used 1,179,025 processed tokens: 1,077,673 cache reads, 15,882 output, 10,421 of
them thinking. Its audit was clean and usable. It submitted 21 findings, which became 18 issues,
1 of them published. The gpt-era caps (40 replies, 1.8M) would not have stopped this session, but
it used 65% of the token cap. A prompt averaged 74K tokens here and grows with each reply, so a
session much longer than 16 replies would likely pass 1.8M. That is an estimate from one session;
the swap made 41 calls on this PR, under another prompt. For the plan's Claude cells, set the
caps to stop only a runaway (on the order of 10M tokens and 200 replies). Keep the run totals in
step: `test_every_shipped_config_keeps_its_two_blocks_in_step` refuses otherwise.

**The session record has no result in a submitted session.** The scaffold stops the session at
submission, before the CLI's final result message arrives. In both runs above,
`claude_code_session.json` therefore has an empty `results`: no notional API cost, and no
per-model usage. Its usage is the main model's stream count, without the CLI's Haiku
housekeeping calls (about 1K tokens a query in the probes, under 0.1% here). A failed or
turn-limited session does get its result. To recover the notional cost, price the recorded
tokens.

`code_hover`, `code_goto` and `get_lean_goal` take `file_path` relative to `workspaces/`, while
`lean_verify_edit` takes `path` relative to the reviewed target. A reviewer that uses one
convention for both fails the hover with "Cannot find Lean project". It happened once in each of
four runs: one APE-Agent, two Claude Code on the relay, and the calibration. In the plan's
dev cells it recurred in `code_goto` (H-claude rep 1) and `get_lean_goal` (H-claude rep 2). It is minor, but it
is the same family as the `lean_verify` path defect below.

**Not minor, and fixed (hygiene layer, `01b09ce7`, 2026-10-01).** Counted over the three Opus
subscription runs' transcripts (`results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py`):
7 of 9 hover, goto and goal calls were refused this way, every one on the `Mathlib/...` spelling,
so the three tools were dead under Claude Code. The provider now tries a relative path under
`workspaces/target/` when it is not under `workspaces/`, and the refusal names both spellings.

**A run that the subscription limit cut short can only be redone, not resumed (2026-10-01).**
`probe_dev_opus55_contract2_claude_sub_rep2` reached the five_hour limit at 10:00. Of 15 sessions,
13 had succeeded. Two (33321 and 33066) failed mid-session after 32-34 replies and about 2.4M
tokens each, on `ClaudeSessionError` ("usage limit is spent"), as designed. Their three retries
failed at once with no tokens, and the run finished `partial` with its outputs written. From
there `--resume` is refused, because it is meant for a run that was interrupted before writing
its outputs, and the orchestrator lists the two as Failed, not Resumable. So the only way to
complete it is `--redo`. That re-runs the 13 good sessions, about 21M tokens of subscription quota
spent again.

**The resume half is fixed (`ebee26c`, `9ceba2a`).** `run --resume` now reopens a partial run. In
each of its orchestrators it requeues the samples that failed on system errors with their
retries spent, keeps every success, and lets unfinished samples continue. It clears the closed
outputs but keeps the plan, the agenda and the append-only logs, and it records the reopen in
`stages.jsonl` (partial -> running). It refuses when nothing failed on errors, because then the
partial is the result, and it refuses lead runs, whose failures sit in nested orchestrators. On
rep 2 the dry run reads "would requeue 2 session(s)". **Still open:** a scheduler that starts no
new session once the CLI reports `allowed_warning`. That was done by hand that day: the chain
was stopped before rep 3 at the first warning.

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

**Closed.** The check compares against `provisioned_roots` (`tests/ape/test_lean_verify_paths.py`),
and since the hygiene layer (`0a3d7d33`, 2026-10-01) a review task registers `lean_verify` as the
snippet probe with no `file_path` at all: of 84 calls in the three Opus dev runs, 55 were
`#check`, `example` or `exact?` snippets and 0 gave a file path, and the reviewed file is
compiled through `lean_verify_edit`. proof_engineering's `file_path` registration is unchanged.

## Codex: the plan, with what Claude Code taught (2026-10-01)

Not started. Every step below is what the Claude Code half needed, or what the installed CLI
(`codex-cli 0.144.5`) now makes possible.

1. **Wire API.** The CLI speaks only Responses (`wire_api = "chat"` is refused), and always streams.
   The relay needs a Responses server route that answers as a Responses event stream: an answer in
   the wrong framing made Claude Code ask every turn twice (`04484fa`). Carried reasoning must
   survive the round trip. Codex sends reasoning items back natively, so the relay must map them to
   and from the message signature that `openai_provider` carries (`e064ae0`).
2. **No bridge.** Replace the unchecked-out CodexBridge submodule with `codex exec --json`, and
   `codex exec resume <id>` for the loop's nudges.
3. **Containment as a condition, not a patch.** `--disable shell_tool --disable unified_exec` leaves
   Codex no shell, so its tools are APE's MCP tools, the same grant as APE-Agent. Also disable
   `browser_use`, `computer_use`, `image_generation`, `apps`, `plugins`, `multi_agent`, `memories` and
   web search, and pass `--ignore-user-config --ignore-rules -s read-only`. Codex's own `hooks` may
   allow a PreToolUse refusal like `contain_to_workspace`. Audit the session rollout (in
   `CODEX_HOME/sessions/`) as `containment.audit_transcript` audits Claude Code's.
4. **Check before paying**, against a local recording server as in the Claude Code work (no model,
   no spend): the request's framing, any per-request field that breaks the prompt prefix (Claude
   Code's `x-anthropic-billing-header` cost 80% of its bill, `5037f57`), whether each turn is asked
   once, and that every task's process reaches its own relay (`196d948`).
5. **The task's contract is already delivered** (`4816cd2`), but `_initial_prompt` still appends the
   absolute-shell-path paragraph, which is wrong with the shell disabled.
6. **Comparable runs exist.** G and Grc under APE-Agent and Claude Code, three repetitions each, are
   matched (`a23892d`, `2dac2e0`) on `develop`'s tools, without the `declaration_search` fix. Codex
   runs on the same tools join that comparison with no re-runs. The fix (`5e215ff`) would make it
   a new baseline.

## The solo grant carries `proof_profile`, and its store holds one table (found 2026-10-01)

`configs/bases/v5_solo.yaml` grants `solo_context_tools: [..., proof_profile]`, and
`proof_profile` reads a declaration table per base commit (`data/pr_review_v5/declaration_tables/`).
One table is on disk (`af239326`). So on every other base the tool answers "no declaration table
for X; build it with `python -m src.mathlib_review.retrieval.declaration_table --commit X`", which
the reviewer cannot run. Over six gpt runs (2026-09-30 audit: dev gpt-5.2 G/Grc, gpt-5.4/5.5 Grc,
validation and post-cutoff gpt-5.2 Grc) that was 13 of the 14 `proof_profile` calls made. The
message is honest: it is an environment failure and says so. The defect is the grant. The reviewer
is shown a tool that cannot answer on almost every PR it reviews, and the Claude reviewers it is compared with
never had it.

What would close it: either build the tables for every base in a run's episode set (a local build,
no spend) and have `cli plan` refuse a run whose granted context tool has no backing store for an
episode; or take `proof_profile` out of the solo grant. That second option is the parity fix for any
gpt-vs-Claude comparison, and it moves every solo plan's identity, so it lands at a run boundary.
The rule this repeats is `.claude/rules/mathlib-review.md`'s "assert the capability reaches the
task". It was written for a tool filtered out of a grant. Here the tool is granted and dead.

**Closed by the second option** (hygiene layer, `786f00a1`, 2026-10-01): `proof_profile` is out of
`configs/bases/v5_solo.yaml`'s grant. The Opus dev runs had added 1 refusal in 2 calls to the count.
The first option, a `cli plan` refusal for a granted tool with no backing store, is not built.

**Correction (2026-10-02, `review-designs`): the close reached the base and not the dev set.**
`configs/pr_review_v5_dev_medium_gpt52.yaml` restates `solo_context_tools` with `proof_profile`
in it, and a child's list replaces the parent's, so every dev config extending it still grants the
tool: the hygiene baseline resolves to `[zulip_search, precedent_search, declaration_search,
naming_norm, proof_profile]`, against its own header ("less `proof_profile`, which left the base
grant"), and the D1 smoke registered it. Hygiene rep 1 never called it (trace: declaration_search
49, naming_norm 8, zulip_search 7, precedent_search 6), so no measured number moved. The baseline
is frozen and the designs extend it, so the designs hold the same grant and the design comparison
is at parity; the fix belongs to the next baseline, not to this one. What would close it: drop the
tool from the dev gpt52 config's list when a new baseline is cut, or build the first option.

## Claude Code aborts an MCP tool call after 300 s of silence, the compile tool's own timeout (found 2026-10-02)

In hygiene rep 2, seven `lean_verify` / `lean_verify_edit` calls in two sessions came back as
`MCP server "core" tool "lean_verify_edit" sent no response or progress for 300s; aborting`, all
between 06:56 and 06:59, when reps 2 and 3 ran in parallel (eight concurrent sessions compiling,
machine load about 13). The CLI's idle limit for an MCP call is 300 s, and so is
`LeanVerifyToolConfig.timeout`; `lean_verify_edit` can also need the file's baseline compile
before the edited one. So under load the CLI cuts a compile off before the tool can return its
own `timeout` outcome ("inconclusive, not a verdict on the code"), and the reviewer reads a bare
MCP error instead. Rep 1, run alone, had none.

**What would close it:** pass `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT` (ms) above the longest tool call
the task can make (two compiles, about 660 s) in the scaffold's CLI environment, beside the
subscription route's other variables in `claude_code/scaffold.py`, or a per-server `timeout` on the
`core` server if the SDK's server config takes one; with a test that the variable reaches the CLI.
It changes nothing a model sees except on a slow compile, so it lands at the next run boundary
(D1 rep 1), not inside the hygiene reps. Until then, do not run two dev runs in parallel on this
machine.

Also seen in the same rep: one `lean_verify_edit` call refused by the CLI as malformed JSON,
`"replacement": }` again (rep 1 of the Opus runs: 7). `0a3d7d33` made an omitted `replacement`
a deletion, but the model still writes the key with no value, which the CLI refuses before the
tool sees it. The description says "omit it to delete the span"; a separate `delete_span: true`
argument would be a shape the model has a value for.

## Every whole-file compile reports a `commandStart` warning at the end of the file (found 2026-10-02)

`LeanVerifyToolsProvider.execute` (`src/ape/toolkits/execute/lean/tools.py`) compiles
`code.strip()`, so a reviewed file loses its final newline before Lean sees it, and with Mathlib's
standard linter set on for whole-file compiles (`WHOLE_FILE_OPTIONS`, hygiene layer, 2026-10-01)
`linter.style.commandStart` fires on the last command: "'' starts on column 9, but all commands
should start at the beginning of the line". Reproduced on 33337's reviewed
`Projection/Submodule.lean`, which ends with `end Dense\n`: stripped, 1 warning; with the final
newline, 0 (`results/pr_review_v5/probes/review-designs-2026-10-02/eof_linter_check.py`, no spend).

**Motivating example.** The D1 test on gpt-5.2 (`probe_dev_structured_gpt52_Grc_contract2_smoke1`,
2026-10-02) filed 3 findings on 33337; 2 of them are this warning, one per changed file, claimed as
"will fail CI style linting" at the files' last lines (both unanchored, so diagnostic). Claude's
hygiene rep 1 saw the same tool and filed none of it. An edit-mode compile is not misled -- the
warning is in the baseline compile too, so `warnings_introduced_by_your_edit` stays empty -- but the
as-is `lean_verify_edit` shows it to the reviewer as the file's own warning, and on a control PR it
is a false finding waiting for a reviewer that reads warnings literally.

**What would close it.** Compile the text as given, or strip only leading whitespace and keep one
final newline, in `execute`; then re-run `eof_linter_check.py`, which must print 0 warnings for the
stripped case too. A test beside it: a whole-file compile of a file ending in a newline reports no
`commandStart` warning.

**Risk / sequencing.** It changes what every reviewer's compile reports, the frozen solo baseline's
included: fixed between hygiene reps 1 and 2, the reps would no longer share their tools. Fix it at a
rep boundary, with the decision recorded beside the reps.

**Closed 2026-10-02 (`review-designs`), at the hygiene reps' boundary** (reps 1-3 all run and
judged): `execute` now compiles `code.strip() + "\n"`, the source as a file holds it
(`tests/ape/test_lean_verify_paths.py::test_execute_hands_lean_the_source_with_its_final_newline`).
`eof_linter_check.py` re-run: the reviewer's as-is `lean_verify_edit` on 33337's
`Projection/Submodule.lean` no longer mentions `commandStart`, and the compile through `execute`
reports 0 warnings. Every run from here sees one warning fewer per reviewed file than hygiene reps
1-3 and D1 rep 1 did; the decision, the user's (2026-10-02: "Let's make the fixes first"), is to
fix before D1 reps 2 and 3, so those reps are of the fixed tools.

## The no-submission prompts named `submit_result` and told a finished reviewer to keep working (found and fixed 2026-10-05)

A batch session's result is what its submission tool records, so a turn with no tool call cannot be
left alone: the model has yielded with nothing filed. Both scaffolds answer it with a user message.
APE-Agent's is `_create_no_tool_call_prompt` ("No tool call detected! You must use tools to make
progress ... When the task is fully completed, use `submit_result`"), with `_create_empty_response_prompt`
for an empty reply; Claude Code's is `_create_retry_prompt` ("Continue. You must submit your final result
using the `...submit_result` tool ..."). The text the model wrote stays in the history.

Two things are wrong with the wording, in all three. It hard-codes `submit_result`, and a review task's
tool is `submit_findings`. And it reads a stop as being stuck ("Leverage all available tools to
thoroughly complete the task"), where a reviewer that stops has usually finished: the prompt should
say to call the task's own submission tool if done, and to continue otherwise. `batch_preamble: plain`
does not reach these prompts.

**It has not touched a result.** In the 262 APE-Agent gpt review sessions logged 29 September to
5 October (5,072 calls), the no-tool-call prompt was sent 0 times and the empty-response prompt twice,
both to gpt-5.5 after an empty `final_answer` (0 characters; PRs 43167 and 26185). After the first it
submitted at once; after the second it went back to searching. Each also lost that turn's reasoning
item, since the API refuses a reasoning item with nothing after it. Not measured: how often the
open-weight `elm_*` models hit it, and how often Claude Code's fires.

**Fixed on `gpt-harness-parity`.** `BaseTask.submit_tool` names the tool a task ends on
(`submit_result` by default; `submit_findings`, `submit_candidates`, `submit_routing`,
`submit_scores`, `submit_distillation` and `submit_opportunity_adjudications` where a class registers
one), and a test checks it against the tools registered by the nearest class that registers any, for
all 27 task types. `prompts.no_submission_prompt` is the one wording: "Your last reply called no tool,
so nothing has been submitted yet. If you have finished, call `<tool>` now. If you have not, continue
with the tools." APE-Agent sends it for a reply with no tool call and, opening "Your last reply was
empty", for an empty one; Claude Code and Codex send it from one method on the base manager, and
their two copies are deleted.

## An exhausted ELM key will look like a slow run: its 429 is retried for hours (found 2026-10-05)

ELM's OpenAPI spec (`/api-docs/elm-proxy-api.yaml`): "Each API key has a spend limit. Once exceeded,
requests return `429` until the quota resets or is increased by an administrator." The client retries
a 429 like any transient error, 100 attempts with waits up to 60 s, so when the key's £500 runs out
every job of a run sits retrying for 1.5-2 h a call, billing nothing, logged only as "API call failed,
retrying". A rate-limit 429 is transient and a quota 429 is not, and the status alone does not say
which. Not yet seen: no ELM call has met either (the gateway reported OpenAI's limits, 30,000 requests
and 180M tokens a minute, on 2026-10-05).

**What would close it:** on a 429 from an ELM model, read `GET /api/v1/costs`
(`ape.llm_clients.elm_budget.key_costs`) once; if `usage >= limit`, raise `RequestRejectedError`
naming the spend and the limit, so the run fails at once; otherwise retry as now. Pin it with a
transport answering 429 and a `/costs` at its limit. A preflight in `cli plan` that compares a run's
worst-case cost with what `/costs` reports left would catch the same thing before any spend, with the
caveat that the caps are dollar list-price estimates and the limit is pounds.

