# One per-PR budget, and a lead that spends it on what each wave returned

**Status** — open, designed 2026-09-23, **deferred** behind `docs/plans/2026-09-23-one-run-to-move-the-wall.md`:
allocation is not what binds until the arms speak, so this is built only after that run moves recall.
**Owned elsewhere (corrected the same day):** the `work-enumeration` branch's plan
(`docs/plans/2026-09-23-work-enumeration.md` on that branch, Phase 5) already schedules this -- a
belief-driven scheduler computed offline from its ceiling runs, implementing `max_rounds > 2`,
`parent_view: full`, `max_redispatches_per_pair` and `sibling_view: blackboard`. This entry is
input to that phase, not a separate thread; the design below is the record of what one planning
pass found, to be merged into it when the two branches are unified
**Cost** — code (about eight commits), then one 12-PR rep at an estimated $18–25 billed against today's $13–14
**Owner question** — the user's, 2026-09-23: *"queue reviewing work iteratively, and update verdicts
about the strengths of the PR and issues in the PR as subreviews come in"*, instead of "queue the
generalist, fit specialists into the remainder".

## Motivating example

Measured on `pr5_A_lead_heldout12_v2_rep{1,2,3}` (`delegations.jsonl`, `lead_journals/`):

| | |
|---|---|
| floor per rep (generalist on all 203 units + rule-required specialists) | 281 / 280 / 282 jobs, billed $9.83–11.06, exempt from the per-PR cap |
| the lead's discretion | 34–38 `proposed` + 0–5 `agent_added` per rep, **3–5 per PR regardless of size** — 33149 (120-job floor) got 3, 33305 (13) got 5 |
| pruned | ~1,090 per rep, 1,087 of 1,089 as "not selected by the lead" |
| leads that opened a second wave | **3 of 12** in rep1 (sizes 4, 3, 3) |
| briefs on floor jobs | 0 of 281 |

The mechanism: `per_pr_cost_cap: 1.50` binds only discretionary spend at $0.30 a job, and the lead's
between-wave view is `JobOutcome.summary()` (`src/ape/tasks/lean_tasks/formal_math/review/delegation.py`),
which omits `abstention` — an arm that looked and declined reads as `success, candidates: 0`. The
lead is told about 4 of 10 arms (`review/prompts.py`, "## The specialists"), `max_rounds` is recorded
and enforced nowhere, and a pair can never be re-dispatched.

**And the reason it is deferred, also measured:** `fanout` (every specialist at every slot, no lead)
scored issue recall 0.20 on four held-out PRs, identical to `lead`; where the lead's pruned on-concern
arms did run under fanout they filed nothing, 7 of 7 (`docs/todo/routing-remit-and-silence.md`). Only
forcing moved it (0.50). A smarter queue over arms that decline 84% of the time buys better-placed
silence.

## The design (from the 2026-09-23 planning pass; verified against the tree that day)

1. **One per-PR budget** `per_pr_budget_base + per_pr_budget_scale × Σ cost_hint(mandatory proposals)`,
   token twin beside it. The agenda's 0.05/job hint tracks actual floor spend closely (33149: hint
   $5.85, actual $5.08–6.10), so preflight prices it with no new estimator. The floor is **charged but
   never refused** (the 2026-08-25 defect was charging it *and* refusing on it); preflight refuses a PR
   that cannot afford one standard job after its floor. Replaces `per_pr_cost_cap` / `per_pr_token_cap`
   in `V5DatasetConfig`, `ReviewLeadConfig`, `_state()`, `journal.py`, `trace.py`; `ExecutionLimits`
   stays the only limiter.
2. **`parent_view: full`** — `JobOutcome.summary(view=)` with `summary` byte-identical to today and
   `full` adding the abstention, the per-target `target_verdicts` (declared on `JobOutcome` by the
   verdict contract, `work-enumeration`), and each context tool's verdict (`naming_norm`'s trace rows carry `result_ids` but
   not the verdict word — one key in `context_tools.py`). Waves over 40 jobs collapse silent jobs; a
   `read_results` tool returns the full view on demand. Remove the refusal in
   `src/mathlib_review/review/coordination.py::assert_implemented`; bump `COORDINATION_VERSION`.
3. **`max_redispatches_per_pair: 1`**, brief required, `invocation_id@n`, with a `base_invocation_id`
   helper stripped in `trace.reconcile`, `journal.replay`, `review/candidates.py`, `analysis/report.py`
   and `review/replay.py`; `payload["task_id"] += "__r{n}"` because `run_subtasks` keys specs by task
   id. Enforce `max_rounds`.
4. **Sibling follow-ups as a deterministic rule** (§D5 of `docs/research/pr-review-v5-principled-design.md`):
   a candidate on X + a `changed_siblings`/`name_family` edge X–Y (`release/pr_relations.py`; nothing
   produces `repeated_implementation_shape`) + an unrun pool pair (unit(Y), same arm) → a queued job
   with a question-shaped `InvestigationBrief`, prepended to the next wave exactly as the floor is,
   `disposition: propagated`, skippable by id with a reason. Deterministic because the trigger is
   mechanical and the measured lead prunes what it does not reach.
5. **`LEAD_SYSTEM`**: delete the "authority is subtractive and it is real" block (contradicts
   `apply_lead_synthesis: False`), the "7% of available specialist jobs" complaint and the `cheap`
   contradiction; replace "Two waves beat one" with the loop; render all ten arms from
   `registry.ARM_DEFINITIONS`. `LEAD_RENDERER_VERSION` is read by nothing today — seal it into the plan.
6. **`report routing`**: waves per lead, discretionary share, redispatches, brief rate, `hits_by_wave`
   (needs `investigation_id` populated on candidate rows — `None` on every row today), and degenerate
   checks printed first (`one_wave`, `redispatch_all`, `follow_ups_declined`, `budget_idle`).

**The selection line.** Wave returns decide which pair runs next and what brief it carries. Nothing
here ranks, keeps, drops or folds a returned finding (`docs/dead-ends.md`, "Publication as selection").

## What would close it

Three reps of the iterative lead on the held-out twelve, read against three reps of the one-run
plan's contract under today's lead: the difference is the loop's contribution. Pre-gate issue recall
mean / union / stable with control emission (33304, 33315) beside it, and `report routing`'s
degenerate block read first.

## Start here

- **read:** `src/ape/tasks/lean_tasks/formal_math/review/lead.py` (`delegate`, the floor injection, `_reconcile`),
  `src/ape/tasks/lean_tasks/formal_math/review/delegation.py` (`JobSpec.budget_scope`, `JobOutcome.summary`),
  `src/ape/tasks/lean_tasks/formal_math/review/prompts.py`, `src/mathlib_review/review/coordination.py`,
  `docs/plans/STATUS.md` ("What the subtask contract makes cheap" — what each refusal takes).
- **run:** `ape/bin/python -m src.mathlib_review.review.cli report routing --run pr5_A_lead_heldout12_v2_rep1`
  (free; the degenerate check and today's dispositions).
- **bounded by:** `docs/dead-ends.md` "Specialists as the coverage floor" (more slots buy silence) and
  "Selection from artifact-only signals" (no new static unit score as the main idea — the signal is
  what a wave returned); `docs/todo/routing-remit-and-silence.md`; the one-run plan, which must move
  recall first.

## Risk

The loop is measured on arms whose filing rate is set by the one-run plan's contract; if that run
does not move recall, the loop is optimising where silence lands. The lead's own conversation grows
under `full` (33149's sweep is ~25–35K tokens in one tool result), so `lead_cost_cap` needs raising
and `degenerate_budget_idle` must be read before any recall number.
