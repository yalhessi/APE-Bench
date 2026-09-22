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

Not yet measured: the distributions on an ELM open-weight model. A 397B MoE may be more or less
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
