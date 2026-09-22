# Are the arms reasoning at all, and which knob would decide it

**Status** — open. Diagnosis is free; a re-measurement of the token caps under reasoning-on
costs one rep.
**Cost** — no spend to diagnose; ~1 rep to re-calibrate if the answer is "no"
**Motivating example** — Across **2,857 arm attempts** on nine v5 `gpt_5.2` runs, every single
one reports `reasoning_tokens: 0`. Not a distribution with a low median — the value is 0 in
2,857 of 2,857. Meanwhile `configs/bases/v5_generation.yaml` carries
`llm_config.thinking_budget_tokens: 30000`, which reads as "these runs think hard", and that
field is **inert**: only `BaseProvider.build_request_payload` sends it (as Anthropic's
`thinking: {type: enabled, budget_tokens: N}`), while `OpenAIProvider` and `ElmProvider` both
override the method and neither sends it — and those two are the entire provider table
(`client.py:47-48`). About twenty configs set it, at 8000 or 30000, and not one has reached an
API.

So every number this project has produced was measured under gpt-5.2's *default* reasoning
behaviour, whatever that is, and the config knob that appears to control it controls nothing.

**What would close it** — A direct answer to "were the arms reasoning": either
`reasoning_tokens: 0` is OpenAI declining to report a breakout, or the model really was not
reasoning. Those are different worlds and the distinction is cheap to settle — one call to
`gpt_5.2` at an explicit `reasoning_effort`, comparing the reported breakout and the completion
count against the same call without it. Then: if the arms were not reasoning, decide whether
they should be (the user's stated preference is yes, as the closer analogue of a frontier
commercial deployment), and re-measure the token caps under that setting, because they were
calibrated on runs where the value was 0.

**Evidence** —
- `src/ape/llm_clients/config.py` — `thinking_budget_tokens` and the comment recording its
  inertness; `reasoning_effort` beside it is the knob that does reach OpenAI and ELM.
- `src/ape/llm_clients/providers/base.py:63-68` — the only sender, on the Anthropic-shaped
  payload.
- `src/ape/llm_clients/providers/openai_provider.py:36` and `elm_provider.py:46` — both
  override it.
- `src/ape/llm_clients/client.py:47-48` — the provider table is OPENAI and ELM only.
- `docs/research/2026-09-22-token-budget-calibration.md` — the caps, and the arm distribution
  (p50 35,276, output share 1.9%) they were derived from.

**Risk** — Turning reasoning on is not free and not obviously right. Measured on
`elm_qwen_3.5`, `reasoning_effort=high` against `none` is ~100x the completion tokens (451
against 4 on one arithmetic prompt) and ~23x the latency (11.5s against 0.5s); a run is already
~38 min. If the arms have not been reasoning and start, the 360,000 arm cap and every wall-clock
figure in the record become historical. The honest sequence is diagnose first, decide second,
re-measure third — not flip the knob and compare against numbers from the other regime.

**Related** — [Token-based execution limits](token-based-execution-limits.md) (closed) supplies
the ceiling and the census this would re-measure with; the ELM section there records what is
known about reasoning on the local models, including that their token *breakout* is not
reported at all — the gateway sends no `completion_tokens_details` — so on those the only
separable thing is the reasoning **text**, now preserved as a thinking block.
[Wall clock](wall-clock-arm-runtime.md) is where the latency half of the cost lands.
