# An OpenAI Responses-API provider, so gpt-5.4 and gpt-5.5 can reason with tools

**Status** — open, 2026-09-30. For a **fresh session in a worktree off `develop`**. Build, merge into
`develop`, then return to `pipeline-overfit-review` to run the blocked runs (last section).
**Cost** — the build spends only its live checks, a few dollars. The blocked runs afterwards are
about $70 billed at the estimated rates, plus about $10 of calibration.
**Motivating example** — test (e) of `reviewer-model-gap.md` could not run its high-effort half.
`probe_postcutoff_gpt5{4,5}_Gr_rep1` failed every call with HTTP 400 on Chat Completions:
"Function tools with reasoning_effort are not supported for gpt-5.4 in /v1/chat/completions. To use
function tools, use /v1/responses or set reasoning_effort to 'none'." Every review task sends tools,
so on gpt-5.4 and gpt-5.5 the pipeline can only run with reasoning off. gpt-5.2 accepts the
combination, which is why its high-effort runs worked.

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
