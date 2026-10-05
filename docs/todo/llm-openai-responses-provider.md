# An OpenAI Responses-API provider, so gpt-5.4 and gpt-5.5 can reason with tools

**Status** — **built 2026-09-30** on `openai-responses-provider`, merged into `develop`, both live
checks passed (section "Built", at the end). **The blocked runs ran 2026-09-30** on
`pipeline-overfit-review`, with reasoning carried (the user's choice, after the carry-over coherence
test). gpt_5.2 high with carry-over reached 0.93 of Claude, against 0.67 on Chat
(`reviewer-model-gap.md`). Open: whether carry-over should become the default for OpenAI reasoning
models in the pipeline. The ELM gateway's `/v1/responses` was measured and wired in on 2026-10-05
(last section), the day the project's own OpenAI key stopped working.
**Cost** — the build spends only its live checks, a few dollars. The blocked runs afterwards are
about $70 billed at the estimated rates, plus about $10 of calibration.
**Motivating example** — test (e) of `reviewer-model-gap.md` could not run its high-effort half.
`probe_postcutoff_gpt5{4,5}_Gr_rep1` failed every call with HTTP 400 on Chat Completions:
"Function tools with reasoning_effort are not supported for gpt-5.4 in /v1/chat/completions. To use
function tools, use /v1/responses or set reasoning_effort to 'none'." Every review task sends tools,
so on gpt-5.4 and gpt-5.5 the pipeline can only run with reasoning off. gpt-5.2 accepts the
combination, which is why its high-effort runs worked.

## Setting up the fresh session

This entry, and the model-table change it builds on, live on `pipeline-overfit-review`, which has
not been merged into `develop`. From the main checkout:

```
git worktree add -b openai-responses-provider .claude/worktrees/openai-responses-provider develop
.claude/worktree-setup.sh .claude/worktrees/openai-responses-provider
cd .claude/worktrees/openai-responses-provider
git cherry-pick a2b501e    # gpt_5.4's real rates and the gpt_5.5 entry; applies cleanly to develop
git checkout pipeline-overfit-review -- docs/todo/llm-openai-responses-provider.md
```

Then copy the section "A rejected request is retried like a transient one" from
`pipeline-overfit-review`'s `docs/todo/framework-defects-2026-09.md` into develop's copy. Its commit,
998468c, does not cherry-pick cleanly, because `reviewer-model-gap.md` is not on `develop`. Add this
entry's row to develop's `docs/todo/README.md`.

## What the probes settled (2026-09-30, one tiny call each)

- **The ELM gateway is no way round.** Its `/v1/chat/completions` returns the same 400, so it
  forwards to OpenAI. It does answer on `/v1/responses` (HTTP 200), so a Responses provider could
  later serve `elm_*` too.
- **OpenAI `/v1/responses` works** for both models with a function tool, `reasoning: {effort: high}`,
  `store: false` and `include: ["reasoning.encrypted_content"]`. gpt-5.4 returned a `reasoning` item
  carrying `encrypted_content`, then a `function_call` item with `arguments` as a JSON string.
- **Responses' usage names differ:** `input_tokens`, `input_tokens_details.cached_tokens`,
  `output_tokens`, `output_tokens_details.reasoning_tokens`.
- **gpt-5.5 reasons when no effort is sent;** gpt-5.2 and gpt-5.4 do not. `MODEL_MAPPINGS` records it,
  and reasoning-off configs send `reasoning_effort: none` explicitly.
- **Prices** for both models are in `MODEL_MAPPINGS` (a2b501e). The largest single prompt in gpt-5.2's
  high-effort sessions was 145K tokens, inside the 272K short-context band these rates assume.

## The design (chosen 2026-09-30)

The client is Chat-Completions-shaped end to end:
- `OpenAIMessageFormatter` emits `messages`;
- `ResponseProcessor` reads `choices[0].message`;
- `StreamingProcessor` merges `delta` chunks;
- `BaseProvider.parse_usage` reads `prompt_tokens`.

So the provider **translates at its own boundary**, and nothing downstream changes.
1. **Opt in by an explicit field,** `LLMConfig.openai_api: Literal["chat_completions", "responses"]`,
   defaulting to `"chat_completions"`. It is inside `scaffold_config_sha256`, so the run plan records
   it and no existing `gpt_5.4` run changes meaning. Select the provider in
   `LLMClient._PROVIDER_IMPLEMENTATIONS` / `_create_provider`.
2. **The request.** Chat messages become Responses `input` items:
   - the system prompt goes to `instructions`;
   - user and assistant text become message items;
   - an assistant `tool_calls` entry becomes a `function_call` item (`call_id`, `name`, `arguments`);
   - a tool result becomes a `function_call_output` item (`call_id`, `output`).

   Chat tools `{type: function, function: {name, description, parameters}}` flatten to
   `{type: function, name, description, parameters}`. `reasoning_effort` becomes
   `reasoning: {effort}`, `max_completion_tokens` becomes `max_output_tokens`, and `store` is false.
   Temperature: check whether it is accepted with reasoning, and drop it if not.
3. **The response.** `output` items translate back into one Chat-Completions-shaped dict:
   `choices[0].message` with `content` and `tool_calls`, and `usage` with the Chat names. The
   existing `ResponseProcessor`, `parse_usage` and `_calculate_cost` then run unchanged.
4. **Streaming.** Stream, but keep only the final `response.completed` event, which carries the whole
   response; ignore the deltas. That keeps long reasoning calls alive, since the longest gpt-5.2
   high-effort call took 230 s, without a second delta merger.
5. **Reasoning between turns is a switch,** `openai_responses_reasoning_carryover: bool = False`, also
   hashed.
   - Off drops each turn's reasoning items, as Chat Completions does, so runs compare with gpt-5.2's
     high-effort runs.
   - On keeps the encrypted items, in a thinking `ContentBlock`, and sends them back as `reasoning`
     input items. OpenAI recommends this for tool use, and it is a separate condition to measure
     second.
6. **Refuse, don't retry.** `cli plan` refuses tools with a `reasoning_effort` other than `none` on
   gpt-5.4 or later over Chat Completions, naming `openai_api: responses`. `llm_clients/client.py`
   stops retrying an HTTP 400 whose message names an unsupported parameter. That second part is the
   defect in `framework-defects-2026-09.md`, "A rejected request is retried like a transient one".

## What would close it

- The two translations are unit-tested against recorded fixtures: the probe responses above, a
  multi-turn tool conversation, and a streamed `response.completed`. The whole suite stays green,
  `tests/ape/test_elm_provider.py` and `tests/datasets/test_cost_model.py` included.
- **Live check 1:** one solo review session through `responses` at `reasoning_effort: none` on one
  post-cutoff PR. It must succeed, with sane findings and usage, and cost comparable to its Chat
  Completions twin.
- **Live check 2:** one session at `high` completes with tool calls and reports reasoning tokens.
- The preflight refusal and the no-retry-on-400 are each pinned by a test.
- Merged into `develop` with the suite green there.

## Start here

- **read:**
  - `src/ape/llm_clients/client.py`: `_PROVIDER_IMPLEMENTATIONS`, `_create_provider`, and the retry
    loop with its non-retryable list;
  - `src/ape/llm_clients/providers/openai_provider.py`: 64 lines, the class to subclass;
  - `src/ape/llm_clients/providers/base.py`: `make_request`, `make_streaming_request`, `parse_usage`,
    `_calculate_cost`;
  - `src/ape/llm_clients/adapters/{message_formatter,openai_message_formatter,response_processor,streaming_processor}.py`;
  - `src/ape/llm_clients/config.py`: `LLMConfig.reasoning_effort`, and `MODEL_MAPPINGS` `gpt_5.4`,
    `gpt_5.5`;
  - `src/ape/llm_clients/models.py`: `ContentBlock` (a thinking block has `reasoning_content` and
    `signature`).
- **run (free):** reproduce the 400 and the Responses success with one-line `curl`s, as in the probe
  above (source `~/.config/secrets/env.zsh` first). Then
  `ape/bin/python -m src.mathlib_review.review.cli plan --config configs/pr_review_v5_probe_2026_07_08_v1_gpt54_Gr.yaml --run-name <new>`
  prices a run without calling a model.
- **settled:**
  - the gateway route fails;
  - Responses works for both models;
  - gpt-5.5 reasons by default;
  - both models' prices;
  - test (e)'s reasoning-off result: gpt-5.5 reaches 0.22, gpt-5.4 0.06, Claude 0.47
    (`results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/README.md`).

## Then, back on `pipeline-overfit-review`: the blocked runs

1. **Merge** `develop` into `pipeline-overfit-review`. Merge, never rebase: the branch's history is the
   record.
2. **Configs.** Add `llm_config.openai_api: responses` to
   `configs/pr_review_v5_probe_2026_07_08_v1_gpt5{4,5}_Gr.yaml`, with reasoning carry-over off. The run
   names `probe_postcutoff_gpt5{4,5}_Gr_rep1` are spent, with no sessions, so use new names, for
   example `probe_postcutoff_gpt5{4,5}_Gr_resp_rep1`. Their untracked result folders can be deleted.
3. **Calibrate.** One high-effort session per model on 43192, `--set dataset.pr_numbers=[43192]`,
   under a `_calib` name. gpt-5.2's first calibration found that 80 turns bind. Set the caps from it:
   the configs now allow 160 turns, 14.4M tokens and $12 (5.4) or $20 (5.5) a session.
4. **Pre-register** in the probe README's test (e) section, before the runs. The rule is unchanged:
   `q = reach(c) / reach(X)`, with `≥ 0.8` closing the gap and `≤ 0.5` leaving it. State that
   Responses without carry-over is the Chat-Completions-equivalent condition.
5. **Run** both detached, as the plan doc's hand-off describes
   (`docs/plans/2026-09-29-probe-harness.md`). Commit the runs before any matcher input.
6. **Match.** Seal X1, X2, Ha1 (gpt-5.4 high), Hb1 (gpt-5.5 high), and gpt-5.2's Gr1 as anchor, on the
   six ask PRs. Then `cli probe match-inputs`, two blind matchers, `cli probe audit`,
   `cli probe unblind`, and the write-up in the README and `reviewer-model-gap.md`.
7. **Optional, second:** the carry-over-on condition, the same runs with
   `openai_responses_reasoning_carryover: true`.

   **Added 2026-09-30, from the transcript inspection** (`reviewer-model-gap.md`, "Why high effort
   still reaches less"). Carry-over may be the more informative condition, and it needs a `gpt_5.2`
   arm. None of gpt_5.2's 120 profiled sessions wrote any visible text, and its reasoning is discarded
   each turn. Its forgetting signatures are highest in the sessions that wandered to the cap. `gpt_5.2`
   at high effort through `responses` with carry-over on, against Gr1 on Chat Completions, varies
   only persistence. gpt-5.4 and gpt-5.5 cannot give that comparison, because they have no Chat
   Completions high-effort run to compare against. Merge `eec8d3a` (`declaration_search`) before
   either run: every run so far used its false-duplicate defect.

   **Run 2026-09-30, as a coherence test** (`results/pr_review_v5/probes/carryover-coherence-2026-09-30/`,
   $9.18). The test was gpt_5.2 high through Responses, carry-over off against on, on the three Gr1
   sessions that looped most. `eec8d3a` was held out, as for every run in the thread.
   - Carry-over works end to end: every turn that reasoned carried its encrypted items, and the next
     turn's input grew by the previous turn's reasoning (coefficient 0.99-1.01, against −0.01-0.01
     off).
   - On submitted 3 of 3 before the cap, against 1 of 3 off.
   - Pooled on over off: 0.30 on far repeats and 0.00 on negative repeats, so it improves coherence
     by the rule. Length-matched, post hoc, the ratio is 0.59: mostly, sessions conclude instead of
     repeating to the cap.
   - Reach is not measured. One session a cell, so provisional.

## Evidence

- The 400: `.ape/probe_scratch/test_e/probe_postcutoff_gpt54_Gr_rep1.log` and the attempt's scaffold
  log.
- `results/pr_review_v5/probes/gpt52-postcutoff-2026-09-29/README.md`, test (e) and its amendment.
- Commits a2b501e (prices, gpt-5.5 entry), 998468c (blocker recorded), 9e6c9ee (probes).

## Risk

- **Comparability.** With carry-over off, Responses should equal Chat Completions' semantics, but it
  is a different endpoint. Live check 1 is the guard: at `none`, the two should match within noise.
- **Surface.** Responses' streaming event names and item shapes may have details the probes did not
  exercise, such as parallel tool calls or refusals. Record fixtures from real calls, not from the
  docs alone.
- **Scope creep.** The ELM gateway's `/v1/responses` and the carry-over-on condition are follow-ups,
  not part of closing this.

## Built (2026-09-30)

Commits on `openai-responses-provider`: 232bf38 (no retry), 331fae7 (the provider), c706ef9 (the
refusal). Where the build departs from the design above, it is from a measurement:

- **Tools are sent `strict: false`.** Responses makes a tool strict by default when its schema
  qualifies (a probe tool came back `additionalProperties: false, strict: true`), and Chat
  Completions never does. Strict is constrained decoding, which would be a different condition.
- **Temperature is sent as configured.** 1.0 is accepted with reasoning on, and 0.7 is a 400 naming
  `temperature`. Nothing is dropped silently, and a bad value fails at once.
- **No-retry is keyed on `error.param`, not on the message.** All three parameter 400s recorded carry
  it. The judge's "Could not finish the message because max_tokens ..." 400 succeeded on retry in
  `pr_review_v4_judge_r0pinned_rep1` and stays retried. That error was not reproduced, so whether its
  body names a parameter is unverified. ELM's pre-send refusals are now not retried either; they had
  been retried a hundred times each.
- **Carry-over keeps each reasoning item's position** among the calls, since the API rejects a
  reasoning item passed without the item that followed it. The items ride in
  `ConversationMessage.signature`.
- **`cli plan` refuses first thing in `run()`**, in a dry run too, before the agenda build.

**Live check 1** (`probe_postcutoff_gpt54_G_resp_rep1`, gpt-5.4, effort `none`, all six post-cutoff
PRs): 6 of 6 succeeded, $0.468 billed. Against the two Chat Completions reps:

| | Chat rep1 | Chat rep2 | Responses |
|---|---|---|---|
| turns | 23 | 24 | 23 |
| tool calls | 89 | 90 | 83 |
| tokens | 355K | 403K | 401K |
| cache hit | 66% | 75% | 68% |
| billed | $0.441 | $0.424 | $0.468 |
| findings | 5 | 4 | 4 |

Everything but billed is inside the spread of the two reps, and billed is 6% over the higher one. One
rep each way, so this shows comparability within noise, not equivalence.

**Live check 2** (`probe_postcutoff_gpt54_Gr_resp_check41930`, gpt-5.4, effort `high`, PR 41930,
capped at $4): succeeded in 10 turns with 26 tool calls and 7,714 reasoning tokens, $0.254 billed, no
retries. It submitted 0 findings on 41930, as gpt-5.2's high-effort Gr1 session did there.

Both ran from a throwaway detached worktree holding `pipeline-overfit-review` with this branch
merged in. Their result folders are committed on `pipeline-overfit-review` (a582826), and the
worktree is removed. The logs are in `.ape/probe_scratch/responses_livecheck/`. The rehearsal merge conflicts in four files:
`config.py` and `framework-defects-2026-09.md` take this branch's side, and `docs/todo/README.md` and
this entry take the other branch's. The branch's suite has one failure there that the merge does not
cause: `test_probes.py::test_a_packet_is_the_committed_one_but_for_its_paths_and_logger` reads a
gitignored per-session `brief.md`, so it fails on any fresh checkout of that branch.

**`store`, measured the same day** (gpt-5.4 at high effort, one two-turn tool conversation with a
5.1K-token prefix, turn 2's usage):

| turn 2 | input | cached | note |
|---|---|---|---|
| `store: false`, no carry-over (as built) | 5,186 | 4,608 | |
| `store: false`, encrypted carry-over | 5,265 | 4,608 | +79, about turn 1's 77 reasoning tokens |
| `store: true`, `previous_response_id` | -- | -- | HTTP 400: "Previous response cannot be used for this organization due to Zero Data Retention" |

So the account is Zero Data Retention, and stored-state chaining is not available at all.
`store: false` with encrypted carry-over is the only way to carry reasoning. Earlier turns are billed
as input either way, and carried reasoning is billed again as input. Separately, the API has
`reasoning.context` (`auto`, `current_turn`, `all_turns`), and every response so far echoed
`current_turn`, carry-over included. In a review session every call after the task prompt is a
tool continuation, so a "turn" probably spans the session. Where the scaffold adds a user message
(a retry prompt), `current_turn` may drop the reasoning carried from before it. Settled below: it
does, and our sessions have no such message.

**`reasoning.context`, settled the same day.** The same carried history was cut at each point and
sent three ways (gpt-5.4, input tokens):

| history ends | no items | `current_turn` | `all_turns` |
|---|---|---|---|
| mid-loop, only tool outputs since the task prompt | 236 | 360, all 4 kept | 360 |
| mid-loop, with a text note beside every call | 322 | 453, all 3 kept | 453 |
| after the model's text-only answer | 281 | 281, all dropped | 405 |
| after a user message inserted mid-loop | 248 | 284, only items after it | 372 |

So a turn is ended by a user message or a text-only answer, and not by tool outputs or notes beside
calls. `auto` and the default both resolve to `current_turn`. **gpt-5.2 rejects `all_turns`**
("Supported values are: 'auto' and 'current_turn'"); gpt-5.4 and gpt-5.5 accept it.

Our sessions have no boundary at all. In gpt-5.2's 33 high-effort solo sessions (the three Gr1 runs
plus check 2), median 45 turns and max 80, there is no mid-session user message and no text-only
answer. So under the default, carry-over keeps every reasoning item of a session. The provider
therefore sends no `context`: sending `all_turns` would change nothing in these sessions, and it would
refuse gpt_5.2, which d23fbde's clean persistence test needs. If a scaffold retry prompt ever appears
(`_no_submission_prompt`, after a malformed response), reasoning before it is dropped. Count
such prompts before reading a carry-over run; there were 0 in 33.

**What carry-over costs over tens of turns** (projected from those 32 gpt-5.2 sessions, each call's
prompt plus every earlier reasoning item; carry-over may shorten the reasoning, which this ignores):

| | as run | all reasoning carried |
|---|---|---|
| processed tokens per session, median | 2.2M | 5.2M (2.0x) |
| sessions over the 7.2M token cap (gpt-5.2 Gr) | 2 | 14 |
| peak prompt, median / max | 60K / 145K | 183K / 400K |
| sessions whose peak prompt passes 272K | 0 | 7 of 33 |

The token cap is what binds, because carried tokens are mostly cached: about $1 more a session at
gpt-5.4's rates, and double that at gpt-5.5's. A carry-over condition therefore needs its token cap
recalibrated, not copied from the Chat runs, or it will be read through truncation. A capped session
submits nothing. Above 272K, the `MODEL_MAPPINGS` rates (short-context) understate cost, and the
largest prompts approach the context window, so check the window before a gpt_5.2 carry-over run.
gpt-5.4 reasons far less than gpt-5.2: 7.7K reasoning tokens in 10 turns on 41930, against 31K in 15.
So the growth there should be smaller. The projection is gpt-5.2's.

Also seen: with no effort sent, gpt-5.5 on Responses runs at `medium` (the response echoes it).

Still open, and not part of closing this: the 401/403 half of the
retry defect; and `openai_api` and the carry-over, like `reasoning_effort`, can be changed by a resume
(`framework-defects-2026-09.md`).

## The replay dropped `phase` (measured and fixed 2026-10-05, no spend)

OpenAI's reasoning guide says that for gpt-5.4 and gpt-5.5 on Responses a manually replayed
assistant message should keep its `phase` (`commentary` or `final_answer`): "Missing or dropped
`phase` can cause preambles to be treated as final answers". The provider drops it:
`responses_to_chat_completion` records a message as `{"type": "message"}` and `_assistant_items`
replays `{"role": "assistant", "content": ...}`. The Codex relay (`scaffolds/codex/relay.py`,
`_assistant_turn` and `_nodes_to_response`) drops it as well, so Codex never receives one to send back.

**It did not touch the APE-Agent numbers.** Every Responses call in `data/llm_logs` from 29 September
to 5 October, 6,278 of them:

| | sessions | calls | assistant messages emitted | assistant text replayed |
|---|---|---|---|---|
| gpt-5.4, APE-Agent, effort high | 51 | 847 | 0 | 0 |
| gpt-5.5, APE-Agent, effort high | 65 | 1,215 | 2, both `final_answer` | 0 |
| gpt-5.4, Codex (`probe_postcutoff_gpt54_Grc_codex_rep1`) | 6 | 110 | 41 `commentary` | all, 0 with a phase |
| gpt-5.5, Codex (`probe_postcutoff_gpt55_Grc_codex_rep1`) | 6 | 80 | 70 `commentary` | all, 0 with a phase |

Under APE-Agent the models go from reasoning straight to tool calls and write no preamble, so there
was no phase to lose. The preamble's "Every response MUST include TOOL CALLS" is not why: under
`batch_preamble: plain`, which drops it, 81 sessions (66 gpt-5.2, 15 gpt-5.5; 1,981 calls) emitted no
assistant message either, and only Codex's own prompt drew commentary. Those sessions are every gpt-5.4 and gpt-5.5 figure in `reviewer-model-gap.md`'s
post-cutoff, validation and dev comparisons. gpt-5.2 emits no phase at all and shows the same gap.

**Where it was dropped, the documented symptom did not appear.** All 12 Codex sessions, 10 of which
replayed unphased commentary, ended on `submit_findings`, with no text-only turn and no incomplete
response. Their reach was 0.31 (gpt-5.4) and 0.25 (gpt-5.5) against APE-Agent's 0.19 and 0.31, one run
each. That rules out early stopping, the named failure. It does not rule out the guide's unnamed
"other misbehavior", which one run a model cannot see.

**Fixed on `gpt-harness-parity`.** A message's phase is recorded in its `responses_output` entry and
sent back on the replayed text, with carry-over on or off; a turn with no phase and no carry-over
records nothing, so those requests are unchanged. The Codex relay puts it on the message it sends and
reads it from the one Codex returns: `codex-cli` 0.144.5 does return it, captured against a local
server with no model. Under Claude Code it rides the relay's turn-signature cache, as reasoning does.
Pinned on `responses_gpt55_stream_text_and_tool_call.sse` and in both relay test files. It matters for
a run that makes these models write between tool calls: the Codex harness, or the unrun gpt cells
under Claude Code. It changes those requests, so a rerun of a Codex condition is a new condition.
Live, through ELM the same day: gpt-5.4 and gpt-5.5 each opened with a `commentary` message, and the
next turn, with that message replayed under its phase, answered HTTP 200.

## No gpt transcript holds readable reasoning, because no summary was requested (found 2026-10-05; knob built and checked through ELM)

The provider sends `reasoning: {"effort": ...}` and nothing else, so every reasoning item comes back
with `summary: []`: 1,998 of 1,998 in the gpt-5.4 and gpt-5.5 APE-Agent review sessions. The models do
reason (median 342 and 201 reasoning tokens a call) and each item is carried, but the transcript shows
only tool calls. Codex as this project runs it asks for none either: its own request, captured
against a local server, carries `reasoning: {"effort": "medium"}` and no summary. Under
APE-Agent these models also write no text between calls (0 messages a session, against 6.8 and 11.7
under Codex's prompt). So every reading of *why* a gpt reviewer passed over an ask has been made from
its calls and its final findings alone. The loop itself is the same: one user message, then about 16-18
rounds of reasoning, 2-3 tool calls and their results, ending on `submit_findings`.

**Built on `gpt-harness-parity`:** `llm_config.openai_responses_reasoning_summary` (`auto`, `concise`
or `detailed`; unset by default, so existing requests are unchanged). Set, the request carries
`reasoning.summary`, the summary stays inside the carried reasoning item, and its text is recorded as
the turn's thinking block, which a session file and `cli trajectory` show and no request sends back.
A reply that is reasoning alone stays an empty reply. Refused without `openai_api: responses`. The
relays need nothing: both build their request from `llm_config`.

**Checked live through ELM** (2026-10-05; the direct key was refused that day, HTTP 401,
`not_authorized_invalid_project`). `reasoning.summary: auto` is accepted with `store: false` and
carry-over on, and echoed back as `detailed`. gpt-5.4 returned three `summary_text` parts (1,495
characters, on 516 reasoning tokens) and gpt-5.2 one (455, on 293); gpt-5.5 returned none on one call
(386 reasoning tokens) and one on the next, so an empty summary there is not a failure. The item goes
back with its summary and the next turn answers HTTP 200. The summary is not in the output tokens:
gpt-5.4's 561 are its 516 reasoning tokens plus 45 of text and call. The gpt-5.4 response is the
fixture `responses_elm_gpt54_high_summary_commentary_call.json`.

Then the stage-by-stage relabelling in `docs/research/gpt-reviewer-gap-diagnosis-2026-10-05.md` (was
the specific concern raised?) has something written to read. Whether a summary changes what the model
does is unmeasured; treat a summarised run as its own condition until one pair says otherwise. Like
`reasoning_effort` and `openai_api`, the knob changes what a run measures and a resume may change it
(`framework-defects-2026-09.md`).

## The OpenAI models through ELM's `/v1/responses` (measured and built 2026-10-05)

**Motivating fact.** The project's OpenAI key stopped working on 2026-10-05: HTTP 401,
`not_authorized_invalid_project`, "The project you are requesting has been archived", on `/v1/models`
too. Every `gpt_*` config (52 of them name gpt_5.2, gpt_5.4 or gpt_5.5, and the judge base names
gpt_5_mini) would retry for hours and bill nothing.

**Measured, one tiny call each, `httpx` to `https://elm.edina.ac.uk/api/v1/responses`:**

| | gpt-5.2 | gpt-5.4 | gpt-5.5 |
|---|---|---|---|
| snapshot the alias resolved to | gpt-5.2-2025-12-11 | gpt-5.4-2026-03-05 | gpt-5.5-2026-04-23 |
| function tool with `reasoning: {effort: high}`, `store: false` | 200 | 200 | 200 |
| encrypted reasoning item returned, and accepted back on turn 2 | yes | yes | yes |
| `summary: auto` | 1 part | 3 parts | 0, then 1 |
| message `phase`, and a replay carrying it | none set | `commentary`, 200 | `commentary`, 200 |

These are the snapshots the direct rows name. A stream ends in `response.completed`. The prompt cache
works through the gateway: a 3,336-token request repeated twice reported 2,688 cached tokens each time
(gpt-5.2). On Chat Completions the gateway behaves as OpenAI does: gpt-5.2 takes tools with high effort,
gpt-5.5 answers the same 400 naming `/v1/responses`. `gpt-5-mini` on Chat Completions resolves to
gpt-5-mini-2025-08-07, the judge's snapshot.

**Built on `gpt-harness-parity`.** `elm_gpt_5.5` is a row; `elm_gpt_5.4` takes `gpt_5.4`'s rates in
place of a placeholder it had kept. The three rows carry `openai_responses: True`, `LLMConfig` accepts
`openai_api: responses` for a row with that mark and refuses any other ELM row, and
`ElmResponsesProvider` is `OpenAIResponsesProvider` at the gateway's address with `ELM_API_KEY`. A
tool conversation through `LLMClient.call_api` ran to its final answer on each model, and streamed on
gpt-5.5. A run moves with
`--set llm_config.model_name=elm_gpt_5.5`; the name is in the plan, so the plan says which endpoint.

**Not known, and to settle on the first real run:**
- ELM's rate limits and quota. A dev run is 20-24M processed tokens; nothing here sent more than a few
  thousand. Watch the first minutes for 429s, which the client retries quietly.
- How ELM's charge relates to the caps. The key's limit is £500 and ELM reports its spend in pounds
  (`GET /api/v1/costs`, read by `python -m ape.llm_clients.elm_budget`; on 2026-10-05 £0.10 used, as
  of that day's 00:00 sync). The caps price at OpenAI's list rates in dollars. After the first paid run,
  compare its billed total with the change in ELM's `usage` once `asOf` has passed the run, and record
  the ratio here.
- Whether a run through ELM reproduces a direct one. Same snapshots and the same API, but no pair has
  been run; treat the first ELM repetition of a direct condition as a replication, not as a given.
- The judge. `configs/bases/v5_judge.yaml` pins `gpt_5_mini`, direct. `elm_gpt_5_mini` is the same
  snapshot, but the name is in the judge's cache key, so moving it forfeits every cached verdict. That
  is a decision, and it is not taken here.
- Codex is told `llm_config.model_name` with `_` as `-`, so `elm_gpt_5.5` reaches it as `elm-gpt-5.5`,
  which has no catalog entry. A Codex config on ELM sets `codex_model: gpt-5.5`.

