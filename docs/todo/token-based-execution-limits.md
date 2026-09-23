# A token-based ceiling in `ExecutionLimits`

**Status** — **CLOSED 2026-09-22.** Built, calibrated, and checked live: 10 of 11 arms on
`elm_qwen_3.5` stopped on `paused_token_limit` at $0.00 billed
(`results/pr_review_v5/runs/pr5_elm_qwen_tokencap_probe1`). See the closing note at the foot of
this file. The entry stands as written, because the reason it was open is part of the record.
**Cost** — no spend (code), plus one cheap rep on a local model to check the ceiling binds
**Motivating example** — Every cap this project relies on is denominated in dollars, and the
Edinburgh ELM gateway serves four open-weight models that cost nothing per token. Priced
truthfully at `0.0`, `standard_budget_cap` (0.30), `lead_cost_cap` (1.00), `per_pr_cost_cap`
(1.50) and `run_total_cost_cap` (10.00–35.00) are *all* satisfied by any run whatsoever, and
the only remaining governors are `max_turns` (40) and `max_delegations` (25). A lead that
delegates 25 jobs of 40 turns each on `elm_qwen_3.5` is bounded by nothing the run plan
records.
**What would close it** — `ExecutionLimits` carries a token ceiling alongside
`billed_cost_limit`; a task on a zero-priced model stops on that ceiling; and a run plan
records it, so two runs with different ceilings are not silently comparable.
**Evidence** —
- `src/ape/orchestration/models.py:265-300` — `ExecutionLimits` has exactly two fields,
  `max_turns` and `billed_cost_limit`; `task_execution_limits` reads only those two.
- `src/ape/llm_clients/config.py` — the four `elm_*` open-weight rows are priced `0.0`
  deliberately. The rejected alternative was a fictional per-token rate to make the dollar
  caps bite; it was rejected because a made-up `input_per_1M` is indistinguishable
  downstream from a real one, and every cost figure the repo reports (preflight estimate,
  budget ledger, `run_total_cost_cap`) would become a mix of money and metaphor.
- `configs/bases/v5_generation.yaml` — the cap block, every value in dollars, with comments
  calibrating each against measured billed spend on OpenAI models.
- Measured 2026-09-22 against the live gateway: every ELM model returns a `usage` block on
  both streaming and non-streaming calls, so token counts *are* available to enforce
  against. The open-weight ones return `prompt_tokens_details: null`, so there is no cache
  accounting to reconcile — input, output and total are all the enforcement needs.
- **The dry run cannot warn you.** `cli plan` on `configs/pr_review_v5_smoke4.yaml` prints
  byte-identical budget lines for `elm_gpt_5.2` (real rates) and `elm_qwen_3.5` (0.0):

      budget: mandatory floor $2.45 (uncapped per PR by design) + discretionary up to $8.00
      run_total_cost_cap $12.00 vs worst case $10.45 (floor + discretionary) — fits

  `_report_budget` (`src/mathlib_review/review/runner.py:819-836`) computes `floor` from
  `mandatory_floor_cost` — required jobs times `standard_budget_cap` — and
  `discretionary_cap` as `per_pr_cost_cap * pr_count`. Both are cap arithmetic with no
  model price in them, so preflight reports the same reassuring "fits" for a model whose
  caps bind and one whose caps cannot. Whatever the ceiling ends up being denominated in,
  this report should be able to say which currency it is estimating.

**Risk** — Two ceilings for one concept is how budget *tiers* got built and then retired
(`ExecutionLimits` replaced them). The failure mode to avoid is a second parallel mechanism:
the token ceiling should be another field on the same object and enforced at the same point
as `billed_cost_limit`, not a new limiter alongside it. There is also a real question of
whether the right primitive is tokens or wall-clock GPU time — a 397B MoE and a 22B dense
model cost the same per token and very different amounts of shared cluster.

**Related** — [Billed as the only spend number](cost-accounting-billed-only.md) is the same
axis from the other end: that entry is about which of two *dollar* figures the record shows,
this one is about runs where neither dollar figure means anything.


---

## How it closed (2026-09-22)

**The ceiling.** `ExecutionLimits.token_limit` beside `billed_cost_limit`, read by the same
`task_execution_limits`, enforced at the same checkpoint in `ape_agent`'s conversation loop and in
`base_relay`'s, resumed by the same cumulative rule. One object, two denominations; the risk this
entry named — a second limiter alongside the first — is what the shape avoids. The stop has its own
`TokenBudgetExhaustedError` / `TOKENS_EXHAUSTED` / `PAUSED_TOKEN_LIMIT` / `paused_tokens` chain,
because "paused on budget" without saying which budget is not actionable when one of the two cannot
fire.

**What it counts.** `TokenUsage.processed_tokens` — the whole prompt plus the completion, *not*
discounted for caching and unaffected by `cost_model`. A cached prompt token is still a token the
model read, and the models this exists for report no cache at all, so the same conversation
measures the same on a cached and an uncached provider.

**The numbers.** One measured exchange rate, **1,200,000 processed tokens per billed dollar** —
median 1,230,650 over 16 v5 runs, range 1.01M–1.70M, agreeing to within 4% across arm, solo and
judge tasks — applied once to pick five literal ceilings that went into
`configs/bases/v5_generation.yaml`. Nothing converts tokens to dollars at runtime, which is what
keeps this different in kind from the fictional `input_per_1M` this entry rejected. Full
derivation, including the one place the two denominations are not the same instrument:
[docs/research/2026-09-22-token-budget-calibration.md](../research/2026-09-22-token-budget-calibration.md).

**The refusal.** `cli plan` now refuses a run on a zero-priced model that has left its token
ceilings unset, rather than printing "$0.00 vs $10.00 — fits" about a run nothing bounds. That is
the concrete answer to "bounded by nothing the run plan records": the caps are also sealed into
`V5RunPlan`, and raising one is a resume rather than a different experiment.

**The primitive question** this entry raised — tokens or wall-clock GPU time — is answered for
*this* ceiling and left open for scheduling; see the last section of the calibration write-up and
[wall-clock-arm-runtime.md](wall-clock-arm-runtime.md).

**The live check, done.** `pr5_elm_qwen_tokencap_probe1`: `elm_qwen_3.5` at
`reasoning_effort=high`, fanout on the control PR 33438, `standard_budget_tokens=30000`. Ten of
eleven arms stopped on `paused_token_limit` at 32,145-41,319 tokens, each logging `Token limit
exceeded: NN,NNN >= limit 30,000 (billed $0.000000)`; 396,769 tokens for $0.00. Run twice, 10 of
11 both times.

**What is still open, and why it is not this entry.** The ELM distribution is *censored* -- ten
of eleven arms were cut, so they are lower bounds and Qwen's p50 says where the cap is, not what
the model consumes. An uncensored rep at the real 360,000 cap would give it, and would need to
state its `reasoning_effort`, since Qwen at `none` and at `high` are different measurements
(4 against 451 completion tokens on one prompt). That is a calibration refinement on a ceiling
that now exists and binds, not the hole this entry described. It is written up in
[the calibration](../research/2026-09-22-token-budget-calibration.md) rather than kept open here.

Two defects the live run exposed are in
[framework-defects-2026-09.md](framework-defects-2026-09.md): the manifest under-reporting a run
by 14x when its tasks pause, and `fanout`'s status counters being structurally zero.
