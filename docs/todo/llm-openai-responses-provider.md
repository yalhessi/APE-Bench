# An OpenAI Responses-API provider, so gpt-5.4 and gpt-5.5 can reason with tools

**Status** — **built 2026-09-30** on `openai-responses-provider`, merged into `develop`, both live
checks passed (section "Built", at the end). Open: the blocked runs, back on `pipeline-overfit-review`
(section "Then, back on `pipeline-overfit-review`").
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
(`_create_empty_response_prompt`, after a malformed response), reasoning before it is dropped. Count
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

Still open, and not part of closing this: the ELM gateway's `/v1/responses`; the 401/403 half of the
retry defect; and `openai_api` and the carry-over, like `reasoning_effort`, can be changed by a resume
(`framework-defects-2026-09.md`).
