# ELM does not enforce tool schemas under `tool_choice: auto`

**Status** — open upstream; worked around locally. The workaround is live and labelled for
deletion; this entry is what tells you when to delete it.
**Cost** — no spend. A few cents to re-measure whenever the gateway changes.
**Motivating example** — On `iter_qwen_plumbing_33438_rep1`, **79 of 155 tool calls failed
(51%)**, and **64 of those 79** were one thing: the model sent the *text* of a list where the
schema declared an array (`line_range: "[200, 220]"`). `gpt_5.2` on the same PR set is 65/644
(10%) with **zero** such failures. Strip them and Qwen's rate is 15/155 — also 10%.

**The cause is enforcement, not comprehension.** One tool, 8 trials, only `tool_choice` varied:

| `tool_choice` | Qwen conformant | `gpt-5-mini` |
|---|---|---|
| `auto` (what an agent sends) | **0/8** | 8/8 |
| `required` | 7/8 | 8/8 |
| named function | 8/8 | 8/8 |

vLLM applies guided decoding against a tool's JSON Schema only when a call is compelled. The
same model is conformant the instant the constraint is applied.

**It is not schema quality**, which was ruled out separately — under `auto`, typing `items`
and replacing Python `None` with JSON `null` in the description left it at 0/8. Only removing
the nesting (5/8) or compelling the call (7/8) moved it.

**What would close it** — any one of:
1. the gateway constraining tool arguments under `auto`;
2. the proxy forwarding vLLM's per-request structured-output parameters, so we can constrain
   from our side;
3. a decision to adopt `tool_choice: "required"` after all.
Then delete the workaround and re-run the 8-trial probe to confirm `auto` is 8/8.

**Evidence** —
- `src/ape/llm_clients/providers/elm_provider.py` — the workaround, under a banner carrying
  these numbers. `ElmProvider.repaired_argument_count` is the live signal: **when it stays 0
  across a run, nothing there is load-bearing any more.** It fired 47 times on
  `iter_qwen_plumbing_33438_rep2`.
- `src/ape/toolkits/file_system/tools.py` — `file_read` flattened to `line_start`/`line_end`.
- `docs/research/2026-09-22-token-budget-calibration.md` — the before/after run comparison.

**What we can and cannot reach**, measured against the live gateway:

| lever | honoured? | constrains tool arguments? |
|---|---|---|
| `tool_choice: required` / named | yes | yes |
| `response_format: json_schema` | **yes** | no — *suppresses* the tool call, emits JSON as content |
| `guided_json`, `structural_tag`, `guided_decoding_backend` | no effect | no |
| a deliberately bogus parameter (control) | 200, silently ignored | — |

The control row is why the three vLLM extensions are read as *dropped by the proxy* rather
than refused by vLLM. `/v1/version` returns `Unknown or unsupported endpoint`, so ELM routes
a whitelist rather than passing through.

**The questions for EDINA** — phrased as questions because they can see the serving config
and we can only see behaviour:
1. Does the proxy forward non-OpenAI body parameters to vLLM? If it strips them, could
   `structural_tag` / `guided_*` be allowed through for the locally hosted models? That alone
   would let us fix this client-side with nothing else changing.
2. Which vLLM version and `--tool-call-parser` is Qwen served with? Structural-tag support for
   tool calls under `auto` is version-dependent, so it decides whether (1) helps.
3. `response_format: json_schema` is honoured and produces correct arrays. Is that same
   constrained-decoding path available for tool-call *arguments* under `tool_choice: auto`?

**Risk** — `tool_choice: "required"` is the lever we have and chose not to pull: it forbids a
tool-free assistant turn for every model and stage, which is a larger and longer-lived
commitment than a defect we expect to be fixed upstream. Worth revisiting if EDINA cannot
help. Note the measured precondition is favourable: 146 of 146 assistant turns in the
observed run already carried a tool call.
