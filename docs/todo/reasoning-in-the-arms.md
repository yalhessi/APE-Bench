# Are the arms reasoning at all, and which knob would decide it

**Status** — open; **diagnosis settled 2026-09-23** (see the foot of this file): gpt-5.2 has run
with reasoning off for the whole record. The test is paid and waits for a matched control on
current code.
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

## Diagnosis settled, 2026-09-23 — every gpt-5.2 number in the record is at reasoning off

Counted over `data/llm_logs` (the provider's own request and response records), deduplicating
streaming calls, which are logged twice (the final chunk carrying usage, and an aggregated
`streaming_request` record):

| | gpt-5.2 | gpt-5-mini, same provider and parser |
|---|---|---|
| distinct responses | 30,198 | 35,774 |
| requests carrying `reasoning_effort` | **0** | 0 |
| responses with `reasoning_tokens > 0` | **0** (explicit 0 on every one) | **35,239 (98.5%)** |
| mean completion tokens | 283 | ~1,095 reasoning tokens per call |

A second, independent 3,000-file sample agrees: 2,979 gpt-5.2 records carrying `reasoning_tokens`,
none positive; gpt-5-mini 3,600 of 3,632 positive. So "OpenAI does not report it" is ruled out, and
the one-call diagnostic above is unnecessary: gpt-5.2's default effort, which nothing overrides, is
no reasoning. The live `work-enumeration` run's `config.json` carries `reasoning_effort: null` and
`thinking_budget_tokens: 30000`, so it is in the same regime. **Every v5 recall number, the 7 / 5 / 6
wall included, was produced by arms that decided without reasoning.**

Why it matters to the wall, and why that is not yet evidence: the record's diagnosis is that the arms
*hold* answers and withhold them (forcing, 0.20 -> 0.50), which reasoning does not obviously address
-- more deliberation could as easily add `already_correct` abstentions. But the other half of the
wall is the ask, not the silence: 8 of 23 held-out obligations were located and asked for the wrong
thing (`docs/research/ab-heldout12-obligation-spine.md` §4), which is a quality-of-judgement failure a
reasoning setting could plausibly move. Neither reading is measured.

What the test needs, corrected from the first design: **not** a single `--set` run against the v2
reps -- those rendered `focused-prompt/2` at `a96b5af`, and the tree has moved 41 review-code commits
since, so they are not a control. It needs an effort-`none` control on the same code, which after the
contract branches are unified is the ready-made matched control
`configs/pr_review_v5_verdicts_fanout4_control.yaml` (on `work-enumeration`), plus a
`--set llm_config.reasoning_effort=low` twin. Check before spending whether `standard_budget_cap`
binds: specialists billed a median $0.039 and max $0.117 against $0.30, and at gpt-5-mini's ~1,100
reasoning tokens per call an arm's 10-20 calls add ~$0.15-0.30. Chat Completions discards reasoning
between turns, so a null there does not settle reasoning in general. Retire `thinking_budget_tokens`
from the 37 configs (28 at 8000, 7 at 30000, 2 at 3000) in the same commit that makes the effort
explicit, so no config reads as thinking when it does not.
