# Calibrating a token budget against the dollar budget

**Measured 2026-09-22** over 16 committed v5 runs (2,857 arm attempts, 108 lead attempts, 48 solo
attempts, 216 judge attempts), all on `gpt_5.2` with prompt caching. Closes
[docs/todo/token-based-execution-limits.md](../todo/token-based-execution-limits.md).

The question this answers is not "should there be a token ceiling" — the todo settled that: the four
locally hosted ELM models are priced `0.0` because that is what they cost, so `standard_budget_cap`,
`lead_cost_cap`, `per_pr_cost_cap` and `run_total_cost_cap` are all satisfied by any run whatsoever
and only `max_turns` and `max_delegations` bound a run on one. The question is **what number** each
ceiling should be, such that a token-governed run is allowed about as much work as a dollar-governed
one.

## The exchange rate

Total processed tokens (prompt + completion, summed over every turn) divided by billed dollars, per
run:

| Run | Tokens | Billed | Tokens per billed $ |
|---|---:|---:|---:|
| `pr5_A_lead_heldout12_v2_rep1` | 16,243,690 | $13.83 | 1,174,450 |
| `pr5_A_lead_heldout12_v2_rep2` | 15,701,039 | $12.76 | 1,230,827 |
| `pr5_A_lead_heldout12_v2_rep3` | 16,700,307 | $13.75 | 1,214,528 |
| `pr5_A_lead_heldout12_rep1` | 14,410,903 | $14.05 | 1,026,030 |
| `pr5_A_lead_heldout12_fp3_rep1` | 15,699,981 | $12.87 | 1,219,894 |
| `pr5_A_lead_heldout12_rel040_rep1` | 9,975,237 | $7.48 | 1,333,106 |
| `pr5_A_lead_heldout12_rel050_rep1` | 9,243,254 | $7.28 | 1,269,965 |
| `pr5_A_lead_heldout12_rel050_rep2` | 9,450,630 | $7.22 | 1,308,488 |
| `pr5_A_lead_heldout12_rel050_rep3` | 8,543,862 | $7.34 | 1,164,746 |
| `pr5_B_solo_ape_heldout12_rep1` | 764,990 | $0.69 | 1,105,312 |
| `pr5_B_solo_ape_heldout12_v2_rep1` | 841,449 | $0.84 | 1,005,648 |
| `pr5_B_solo_ape_heldout12_v2_rep2` | 1,098,576 | $0.74 | 1,487,244 |
| `pr5_B_solo_ape_heldout12_v2_rep3` | 973,435 | $0.79 | 1,230,473 |
| `pr5_F_fanout_heldout12_v2_rep1` | 4,522,346 | $3.59 | 1,258,713 |
| `pr5_F_fanout_stage1_rep1` | 7,536,136 | $5.07 | 1,487,550 |
| `pr5_F_fanout_forced_stage1_rep1` | 15,868,476 | $9.35 | 1,696,854 |

**Median 1,230,650; range 1,005,648 – 1,696,854.** Per *task* rather than per run the same figure is
1,195,402 (arm), 1,155,912 (solo), 1,152,608 (judge) — three independent task shapes agreeing to
within 4%.

**The rate is used once, here, to pick five literal token counts that then go into the config.
Nothing converts tokens to dollars at runtime.** That is the whole difference between this and the
rejected alternative of putting a fictional `input_per_1M` on the free models: a made-up price would
enter every figure the repo reports as spend, whereas a calibration constant used once to set a
ceiling enters nothing. `MODEL_MAPPINGS` still prices the open-weight models at `0.0`, because that
is still what they cost.

## The caps

At a round **1,200,000 tokens per billed dollar**:

| Dollar cap | | Token cap | |
|---|---:|---|---:|
| `standard_budget_cap` | $0.30 | `standard_budget_tokens` | 360,000 |
| `lead_cost_cap` | $1.00 | `lead_token_cap` | 1,200,000 |
| `per_pr_cost_cap` | $1.50 | `per_pr_token_cap` | 1,800,000 |
| `solo_cost_cap` | $1.50 | `solo_token_cap` | 1,800,000 |
| `run_total_cost_cap` | $10.00 | `run_total_token_cap` | 12,000,000 |

One rate for all five, deliberately: the caps' **ratios** are what govern behaviour, not their
absolute values. `per_pr_cost_cap / standard_budget_cap = 5` is what lets a lead buy five standard
jobs before the reservation check refuses the sixth, and 1,800,000 / 360,000 is the same 5. Setting
any one cap by a different method would change how many jobs a lead may buy, which is a change to
the experiment rather than to its denomination.

That is also why the ratios are now checked. A child config restates only what it varies, and
`pr_review_v5_smoke4.yaml` had already drifted before this landed: `per_pr_cost_cap: 2.0` against
the base's `standard_budget_cap: 0.30` buys **6.7** standard jobs, while the token block it did
not touch bought **5** — the same config, a quarter less fan-out, depending only on whether the
model was priced. `plan` now says so, a test applies the same check to every config in the tree,
and the nine configs that overrode a dollar cap carry their token twin.

## What each cap does to the measured distributions

| Role | n | p50 | p90 | p99 | max | cap | cuts |
|---|---:|---:|---:|---:|---:|---:|---|
| arm | 2,857 | 35,276 | 87,589 | 243,736 | 558,101 | 360,000 | 6 (0.21%) |
| lead (own turns) | 108 | 67,016 | 125,582 | 187,480 | 207,318 | 1,200,000 | 0 |
| solo | 48 | 63,382 | 115,466 | 358,978 | 358,978 | 1,800,000 | 0 |

Run totals for the 12-PR held-out set are 8.5M–16.7M tokens against a 12M cap — which is the same
relation the dollar caps already have to the same runs ($7.22–$14.05 against $10.00), because
`run_total_cost_cap` is a preflight estimate check rather than a live ceiling. Parity is preserved,
including the part where it is already loose.

### The one place tokens and dollars are not the same instrument

The arm cap cuts 6 attempts of 2,857 where `$0.30` cut none: the arm maximum was 558,101 tokens at
$0.186 billed, a rate of 3.0M tokens per dollar against the 1.24M median. **The heaviest arms are
the cheapest per token**, because a 17-to-22-turn investigation re-sends a prefix that is cached at
1/14th the input rate. So the dollar cap is loosest exactly where the token cap is tightest.

This is entirely an artifact of the cache discount, and it does not exist in the regime the ceiling
is for: the locally hosted models return `prompt_tokens_details: null`, no discount is applied, and
under a uniform price per token the two ceilings are the same instrument to within rounding. The
6 cut attempts are the price of the ceiling behaving identically on a cached and an uncached
provider — which is the property worth having, and is why `ExecutionLimits.token_limit` counts
processed tokens rather than billed-equivalent ones.

## Two accounting facts found while measuring

Both were found by the sweep, both are recorded here because they change how the numbers above must
be read.

1. **Costs bubble from children to parents; token counts did not.** A lead's
   `result.token_usage.cached_total_cost` includes everything its arms spent, while the *token*
   fields on the same object are the lead's own. One lead attempt recorded 65,471 tokens against
   $0.9755 billed — 67,117 tokens/$, against $0.0818 for its own turns — because the numerator was
   self and the denominator was self-plus-nested. Read as recorded, leads come out at a median
   107,528 tokens/$ against their arms' 1,241,326: **11.5x understated**, and the error is not a
   constant, since it scales with how much a lead delegated. Every lead figure in this document is
   therefore the lead's **own** turns,
   with its billed cost recomputed from its own tokens at the `gpt_5.2` rates. `nested_usage()` in
   `orchestration/subtasks.py` fills only the cost fields; the token half now has somewhere to live
   (`UsageBreakdown.nested_tokens`).

2. **`Attempt.cost` is inclusive of nested spend while the ceiling that reads it is not.** The
   conversation loop enforces `billed_cost_limit` against the scaffold's own turns, but
   `Sample.get_accumulated_cached_cost` — what decides whether a paused sample may resume — sums
   `attempt.cached_cost`, which for a lead includes its arms. `attempt.tokens` is deliberately
   self-only so the token half does not inherit this; the cost half is left alone and recorded as a
   defect in [framework-defects-2026-09.md](../todo/framework-defects-2026-09.md).

## Re-measuring

`ape/bin/python -m src.mathlib_review.review.cli report token-census --run <run> [--run <run> ...]`
prints the per-role distribution and the exchange rate for any set of runs. Re-run it when the model
changes: the rate is a property of a price list and this project's cache hit rate, not a constant of
nature. The per-role token *distributions* are the more durable half — they are what the model
actually does — and the caps should be re-derived if a run's p99 approaches its cap.

## The ceiling on a zero-priced model, measured

`pr5_elm_qwen_tokencap_probe1`: `elm_qwen_3.5`, `reasoning_effort=high`, fanout on the control
PR 33438, 11 arms, `standard_budget_tokens` set to **30,000** — deliberately below the gpt_5.2
arm p50 of 35,276 so the ceiling would bind.

**Ten of eleven arms stopped on `paused_token_limit`**, at 32,145–41,319 processed tokens each,
every one of them logging `Token limit exceeded: NN,NNN >= limit 30,000 (billed $0.000000)`.
The eleventh finished at 27,555, under the cap. Total for the run: **396,769 tokens for $0.00**.
That is the todo's closing condition: a task on a model no dollar cap can bind stops on the
token one. (The same experiment run twice agreed: 10 of 11 both times, 385,684 and 396,769
tokens.)

Two things to hold onto before reading anything else into it:

* **The distribution is censored.** Every one of those ten is a lower bound — the arm was cut,
  not finished. Qwen's p50 of 36,145 against gpt_5.2's 35,276 is therefore *not* evidence that
  the two models consume alike; it is evidence that ten arms were stopped at about the same
  place. The uncensored ELM distribution is still unmeasured, and a rep at the real 360,000 cap
  is what would give it.
* **The one uncensored arm's output share was 2.29%**, against gpt_5.2's 1.6–1.9%. With
  reasoning ON. That is the first indication that prompt re-sending dominates on both models
  and the gpt_5.2-derived caps may transfer — one arm, so it is an indication and nothing more.

**Operational note.** The gateway is not reliably fast. The same 11 jobs took 5m12s on one
invocation and, on the next, stalled for **46 minutes** inside a single streaming call before
the run hit its wall-clock limit at 10 of 11. `LLMConfig.timeout` is 3600s, so one call can
hang for an hour with nothing but the absence of progress to say so. Size an ELM run's
wall-clock budget accordingly, and do not read a slow run as a large one.

## Two defects this run exposed

* **The census this document tells you to re-run was wrong when it mattered most.** It read
  `result.token_usage`, which a paused attempt never writes, so it reported the distribution of
  the one job that finished — 1 attempt of 11 — and paused attempts are the heavy ones by
  construction. It now reads `Attempt.tokens`. Re-checked against the gpt_5.2 runs: every
  number in this document is unchanged.
* **The manifest under-reported the run by 14x**, `self_tokens: 27,555` against 396,769,
  because `worker._try_aggregate` synthesises a `task_result.json` with `token_usage=None` for
  a task that paused (framework defect #4) and `OrchestratorResults.total_token_usage` sums
  those results. `self_tokens` now comes from `task_outcome.json`, which is written for every
  scheduled task precisely because `task_result.json` is reserved for a successful submission.
  That is a fix at the reader: every other consumer of `total_token_usage` still sees the short
  number, and on a paid run `total_cached_cost` is short the same way.

## Reasoning is the other axis, and it was neither recorded nor kept

`reasoning_effort` moves Qwen's completion tokens by about two orders of magnitude (4 against
451 on one arithmetic prompt) and its latency by about 23x. `elm_qwen_3.5` reasons by default
and `elm_mistral_small_4` does not, so there is no single "ELM default" for a run to inherit,
and a token distribution measured without stating the setting is unreadable. The knob is now
`LLMConfig.reasoning_effort`, inside `scaffold_config_sha256`; the per-model measurements are
in `MODEL_MAPPINGS`. The parameter is `reasoning_effort` — `reasoning: null` returns HTTP 200,
leaves reasoning on, and reports nothing.

**What is separable on a local model, and what is not.** The reasoning *text* comes back in its
own field and never mixed into `content` — `message.reasoning` non-streaming,
`delta.reasoning` streaming, `null` when reasoning is off. The reasoning *token count* does
not: the gateway sends no `completion_tokens_details` at all, so `completion_tokens` is
reasoning plus answer undifferentiated. vLLM can emit that breakout when a reasoning parser is
configured, so it is a reasonable thing to ask ELM to enable; failing that the count is
recoverable by tokenizing the text.

This repo was reading only `reasoning_content`, the DeepSeek and older-vLLM spelling, so on an
ELM model with reasoning on it kept the answer and dropped the thinking — a 2,551-character
trace and about 75% of the completion tokens, absent from the session record, on a project
whose method is reading what the agent did. Both spellings are now normalised at the boundary
(`llm_clients/models.py::REASONING_KEYS`) and the trace arrives as a thinking block on both
transports.

**On commercial models the count is not a separate currency.** Reasoning tokens are output
tokens: billed at the output rate, inside the completion/output count, against the output
limit, on every frontier provider. What varies is visibility — OpenAI breaks them out as
`completion_tokens_details.reasoning_tokens` without returning the text, Anthropic returns the
thinking blocks, Gemini reports `thoughtsTokenCount`. So `processed_tokens` already counts them
correctly everywhere and the cost model already prices them at `output_per_1M`; nothing in the
ceiling needs a reasoning-specific case.

Which leaves one open question, in [reasoning-in-the-arms.md](../todo/reasoning-in-the-arms.md):
all 2,857 arm attempts behind the caps above report `reasoning_tokens: 0`, and the config field
that appears to control thinking is inert for every provider this project uses.

Not yet measured: the uncensored distributions on an ELM open-weight model. A 397B MoE may be more or less
verbose per turn than `gpt_5.2`, and until one full rep exists the caps above are calibrated on
OpenAI behaviour and applied to a model that has not been watched. The first ELM rep should be read
against the arm p50/p90 here before anything is concluded from it.

## The primitive question the todo raised

The todo asks whether tokens or wall-clock GPU time is the right primitive, since "a 397B MoE and a
22B dense model cost the same per token and very different amounts of shared cluster". Tokens, for
this ceiling: it is a per-task bound enforced inside a conversation loop, and tokens are what the
provider reports on every call, on both the streaming and non-streaming paths. GPU-time fairness is
a question about how much of a shared cluster a *run* may occupy, which is a scheduling concern and
belongs with [wall-clock-arm-runtime.md](../todo/wall-clock-arm-runtime.md), not a second field on
`ExecutionLimits`.
