# Billed as the only spend number

**Status** — open; code + docs, no rerun
**Cost** — no spend
**Motivating example** — across the 52 committed v5 manifests the field named `total_cost` sums to
**$283.53** against a true billed **$84.23**. The gap is not a constant to divide out: per-run it
ranges **2.06× to 3.38×**, and of the 820 pairs of the 41 runs that carry a `usage` block,
**69 (8.4%) are ordered differently by nominal than by billed** — `pr5_solo_ape_33438_probe` reads as
the most expensive of its set at $0.123 nominal while being the cheapest at $0.040 billed. Nominal is
not a conservative overestimate of spend; it is a different ranking of the same runs.
**What would close it** — no figure a human reads during or after a run is nominal, and no analysis
output carries nominal under the name `cost`. Concretely: the live progress line shows one cost
number and it is billed; `report["cost"]` and `score["cost"]` read `usage.billed`; the
`dead-ends.md` fanout-cost clause is restated in one currency.
**Evidence** — see below.
**Risk** — the manifest field cannot simply be deleted (§3), and step 2 changes numbers that already
appear in committed write-ups, so the commit has to state before/after on at least one run.

## What nominal is, and why it is not spend

`total_cost` / `nominal_cost` is the **no-cache counterfactual**: what the call would have cost had
no prompt cache existed. `cached_total_cost` / `billed_cost` is what was paid. Every cap in this
system — `sample_max_cost`, `ExecutionLimits.billed_cost_limit`, `per_pr_cost_cap`, `lead_cost_cap`,
`run_total_cost_cap` — binds the billed figure. Nothing binds nominal.

It is also **redundant data**. Nominal is a pure function of the persisted token counts and the price
table ([`providers/base.py:278`](../../src/ape/llm_clients/providers/base.py#L278)):
`(input + cache_read) × input_rate + output × output_rate`. Tokens are already on disk, so the field
carries no information that could not be recomputed at analysis time.

*Amended 2026-09-22.* "Tokens are already on disk" is true per attempt and was **not** true for a
parent: `subtasks.nested_usage` filled only the cost fields, so a lead's recorded `token_usage`
carried its children's dollars and only its own tokens. Recomputing nominal from the persisted
counts would therefore have come out ~11.5x low for every lead row. The token half now lives on
`UsageBreakdown.self_tokens` / `nested_tokens`, deliberately beside the costs rather than folded
into the flat `TokenUsage` — see `subtasks.nested_usage` for why. With that, the recompute this
entry proposes is available at every level.

The one rationale in its own docstring — "For reporting cache effectiveness, nothing else"
([`orchestration/models.py:420-423`](../../src/ape/orchestration/models.py#L420-L423)) — does not
survive contact with how cache effectiveness is actually measured here. The live number in
[lead-prompt-cost.md](lead-prompt-cost.md) (fanout **80.2%** against lead **71.2%**) comes from
`cache_read_input_tokens`, not from the billed/nominal ratio. Tokens do that job directly and without
a second currency.

## 1. Where nominal is still displayed, usually holding the label `cost`

| Site | What it prints |
|---|---|
| [`orchestration/persistence.py:339-343`](../../src/ape/orchestration/persistence.py#L339-L343) | the live run line: `Cost:$X→$Y` (nominal, yellow) **before** `Cached:$X→$Y` (billed, green). The number labelled "Cost" is the one that is not spend — this is what is seen during a run |
| [`scaffolds/ape_agent/conversation.py:738-739`](../../src/ape/scaffolds/ape_agent/conversation.py#L738-L739) | on resume, `Already spent: $X` (nominal) printed directly above `Cost limit: $Y` (billed) — two currencies, one apparent comparison |
| [`orchestration/worker.py:226-231`](../../src/ape/orchestration/worker.py#L226-L231) | per-sample completion `cost=$…` = `attempt.cost` = nominal |
| [`conversation.py:267`](../../src/ape/scaffolds/ape_agent/conversation.py#L267), [`:413-418`](../../src/ape/scaffolds/ape_agent/conversation.py#L413-L418), [`:529-532`](../../src/ape/scaffolds/ape_agent/conversation.py#L529-L532) | turn and resume logs, all `total_cost` |
| [`analysis/report.py:131`](../../src/mathlib_review/analysis/report.py#L131) | `report["cost"] = manifest.get("total_cost")` — nominal, into the routing report |
| [`analysis/bench_cli.py:258`](../../src/mathlib_review/analysis/bench_cli.py#L258) | `score["cost"] = results.total_cost` — nominal, onto a score file |
| [`orchestration/subtasks.py:175-176`](../../src/ape/orchestration/subtasks.py#L175-L176) | rolls nested `nominal_cost` up into `TokenUsage.total_cost` |

The last two are not cosmetic: they are how nominal reaches a write-up under the name `cost`. That is
the mechanism behind [`dead-ends.md:68`](../dead-ends.md)'s "fanout costs $0.085/job against lead's
$0.040", which compares a nominal per-job figure against a billed one. Restricted to the same four
PRs it is **+1.7% nominal and −7.9% billed** — already queued in
[record-corrections.md](record-corrections.md#L31-L37), and an instance of exactly this class.

## 2. The name is the trap

`TokenUsage.total_cost` ([`llm_clients/models.py:27-28`](../../src/ape/llm_clients/models.py#L27-L28))
is the nominal figure under the most authoritative-looking name in the codebase, with the billed one
beside it as `cached_total_cost` — which reads like a subset or a cache statistic rather than the
real number. Every leak in §1 is someone reaching for the obvious attribute. Renaming at the source
is what actually closes this; suppressing the display alone leaves the trap armed.

## 3. What blocks a clean delete

`V5RunManifest.total_cost` ([`schema/review.py:356`](../../src/mathlib_review/schema/review.py#L356))
is nominal, is a **required** field, and is hashed into the manifest's own `source_sha256`
([`review/trace.py:249-250`](../../src/mathlib_review/review/trace.py#L249-L250)) under
`StrictModel`'s `extra="forbid"`. 52 v5 manifests plus the frozen `results/pr_review_v4/` root carry
it. Removing the field breaks reads of every existing run and invalidates the seals.

**11 of the 52 predate the `usage` block entirely** — `pr_review_v5_lead_heldout11_rep1` ($12.48),
`pr_review_v5_lead_smoke4_rep4` ($10.58), `pr_review_v5_lead_heldout11_rep2` ($10.15) and eight
others — so for those runs the only cost figure on disk *is* the nominal one under the name
`total_cost`, and the corrections sidecar exists to reconcile them. The field has to stay readable.

## Proposed shape

1. **Billed-only in every live surface.** One cost number during a run, labelled billed. Pure win,
   and where the complaint that opened this originates.
2. **Retire `total_cost` as a name at the analysis boundary.** Every user-facing figure reads
   `usage.billed`. This is the step that stops §1 from recurring.
3. **Keep `nominal` persisted at attempt / `UsageBreakdown` level only**, under a name that cannot be
   read as spend — as it already is there. It is the audit trail for the cache-pricing bug class that
   has bitten this project twice: `6381a83` (cached tokens charged twice, inflating *both* figures)
   and `9b63f87` (a lead killed at a $1.00 cap having spent $0.200). It costs nothing to keep.
4. **Keep the manifest field**, still written, docstring marked deprecated — it already says "Never
   call this spend."

Step 2 changes numbers in existing reports, so the commit that does it should state before/after on
at least one named run.

## Related

- [record-corrections.md](record-corrections.md) — the fanout-cost clause is one instance of this
  class; fixing the record and fixing the plumbing are separate commits, and the record correction
  does not wait on the plumbing.
- [lead-prompt-cost.md](lead-prompt-cost.md) — quotes prompt spend in billed terms already, and is
  the entry whose cache-rate measurement shows tokens are the better instrument.
