# A token-based ceiling in `ExecutionLimits`

**Status** — open, and blocking any real use of the locally hosted ELM models
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
