<!-- Verbatim as approved. Status is not tracked here — see STATUS.md.

     This is not a second plan so much as the first one's remainder, reordered by what
     unblocks what after Stage 0 and Stage 3 had largely landed. Where the two disagree, this
     one is later and wins; where this one is silent, the original still stands. -->

# Remaining work: the subtask primitive, the last unbounded budget, and dual channels

## Context

18 commits on `september-checkpoint`, 971 → 1140 tests. The accounting failures that voided two
September runs are closed, prompts lost 32% of their bulk on the arm path, configs refuse silent
typos and unparsed overrides, the 2,187-line schema is split by lifecycle, each arm is declared
once, per-arm benches exist, and coordination is a sealed bounded policy.

What follows is what the plan still asks for, reordered by what unblocks what. The package
collapse into `mathlib_review` stays last: it is mechanical, and every item below makes it
smaller.

### The finding that reshapes Stage 0

The plan assumed per-spec execution limits would be expensive, and that budget tiers might have
to survive as orchestrator groupings. Reading the code says otherwise:

* `task_data` is available at `worker.py:72`, **before** the `Attempt` is constructed at `:95`;
* `Attempt.cost_limit` and `Attempt.max_turns` are already **per-attempt fields**;
* `runtime.run_task(..., cost_limit=...)` is already a **per-call parameter**.

Both sites are simply always filled from `config.execution.sample_max_cost`. So per-task limits
need **no new plumbing** — two sites read an override off the task before falling back.

And `_tier_config` differs from its parent in five ways, of which exactly **one** is
tier-specific:

```
sample_max_cost = standard_cap * TIER_MULTIPLIERS[tier]   <- the only tier-specific value
num_processes    = 0                                       same for every tier
sample_count     = 1                                       same for every tier
early_stop_mode  = DISABLED                                same for every tier
runs_base_dir    = subtasks/wave<N>/<tier>                 tier appears only because tiers exist
```

The entire tier-grouping machinery exists to vary one number. Moving that number onto the task
retires it, and takes three defects with it: unbounded concurrency across tiers dispatched by
`asyncio.gather`, an exception in one tier discarding another tier's completed outcomes *and*
their spend, and the tier-shaped directory layout that `trajectory.py` hardcodes a glob depth
against.

---

## Step 1 — `TaskExecutionSpec` and `spawn_subtasks`

The framework has no primitive for nested work. `TaskOrchestrator(` is constructed directly in
four files; `judgment/task.py` and `review_gate.py` share one convention and
`pr_review_v5/delegation.py` invented a divergent one. The accounting bugs already fixed were
what that divergence cost.

**`TaskExecutionSpec`** (`src/ape/orchestration/models.py`, beside `TaskOutcome`): child
identity, typed task data, sample count, per-task `max_turns` / `retries` / `billed_cost_limit`,
requiredness, budget scope, and a result projection.

**Per-task limits** — `worker.py:95-103` and `:410-418` prefer a limit carried on the task over
`config.execution.sample_max_cost`. Two small reads; the fields already exist.

**`BaseTask.spawn_subtasks(specs) -> list[TaskOutcome]`**, a thin wrapper over an injected
`SubtaskExecutor` that owns child directory layout, isolation, reservation, outcome recording
and usage bubbling — once, for every task family present and future. Nested execution keeps
`num_processes=0` and gains a **bounded** concurrency limit; nothing bounds it today (4 leads ×
4 arms × 3 tiers ≈ 48 concurrent Lean compiles from one process).

**Retire budget tiers.** With per-task limits, `_tier_config`, `run_tier` and `run_jobs`'s
gather-over-tiers collapse into one nested orchestrator per wave, and `subtasks/wave<N>/<tier>/`
becomes `subtasks/wave<N>/`. `TIER_MULTIPLIERS` stays as the vocabulary the lead uses to ask for
a budget; only the grouping goes.

**Acceptance:** `judgment` and `review_gate` migrate onto `spawn_subtasks` and their existing
tests still pass. That is the plan's own test of whether this is a primitive or a fourth
convention, and it is the reason to do this before anything else.

## Step 2 — the last unbounded budget, and the state that does not survive resume

* **Run-total scope.** Lead-self, mandatory-floor and discretionary-per-PR exist; there is no
  run-total ceiling, so the floor is still unbounded across a run. Preflight fails when
  mandatory coverage cannot fit — today's dry-run message says "raise `per_pr_cost_cap`", a cap
  that does not bind the floor at all.
* **`UsageBreakdown`** as one type carrying self / nested / inclusive for nominal, billed and
  budget-charged. The semantics are already right everywhere; the fields are spread across
  `TaskOutcome`, `JobOutcome` and the manifest, so nothing can state the whole picture.
* **Lead state as an append-only event journal** — reservations, dispatches, outcomes,
  synthesis decisions — reconstructed idempotently on resume. `lead.py:294-313` is in-memory, so
  a resumed lead still gets a fresh `per_pr_cost_cap` and loses its "already delegated" dedup.
* **`execution_index.jsonl`** mapping semantic run/sample/attempt/delegation/candidate ids to
  physical paths and snapshot hashes. Retires `trajectory.py`'s hardcoded `samples/0` and fixed
  glob depth, which Step 1 would otherwise break by changing the subtask layout.

## Step 3 — dual admission channels

`finalize` emits one admission axis, so "we think this" and "we proved this" are the same field.
That is what makes the 63% ceiling look like a reviewer failure.

* **`review`** — every synthesized maintainer-facing finding.
* **`verified`** — the subset with claim-scoped deterministic support and no contradiction.
* Contradiction is **not** an automatic veto: the finding stays in `review` with a warning and
  its full evidence trail, and is excluded from `verified`.

With reachability already reported, this is what makes a recall number readable: reviewer
performance against `review`, mechanism performance against `verified`.

## Step 4 — provenance instead of a concern gate

* Record immutable `origin_arm_id`; let candidates carry non-gating, possibly multi-valued
  `concern_tags`.
* **Then** remove `ALLOWED_CONCERN_BY_ARM` as an admission rule — but only after finalization
  reports every drop. The gate exists because removing it reintroduces a silent deletion:
  `arm.py:50` records that an arm reporting an unexpected concern passes submission and is then
  dropped at finalization for lacking an artifact its declared concern can never produce,
  "without a word", which on the rep2 smoke run was all four specialist candidates.
* The vocabularies also disagree by one word — arms say `documentation`, gold says `docs` — and
  `benches.CONCERN_ALIASES` bridges it today. Provenance makes that bridge unnecessary for
  scoring, not for routing.

## Step 5 — Stage 1 remainder

Landed: `extra="forbid"`, the override parser, `extends:`, `guard_run_name`'s two leaks, the
runbook fix. Remaining, in rough value order:

* **`judge --of <run_name>`** — derives findings/evidence/audit/output paths from the generation
  run. Three free-form strings must agree by hand today and currently do not:
  `pr_review_v5_medium_heldout.yaml` says `rep2`, its judge config reads `rep1/findings.jsonl`.
* **Promote the comment-invariants to preflight** — judge model pinned per release,
  `units_without_specialist` empty when the floor is off, `execution_release` /
  `skip_evidence_chain` / `pr_finding_limit` recorded in the plan.
* **`evaluation_contract_version`**, so changing `pairing_tiers` without incrementing it fails.
* **`run_plan_revision_N`** for monotonic resume — budget, timeout and retries may change on
  resume; anything semantic requires a new run name.
* **The config backlog I did not do and should flag:** the plan said delete the 36 stale
  configs. I committed them instead, so 64 are tracked, **7 v5 configs still name an
  already-spent run**, and only 2 use `extends:`. Convert the live ones, delete the spent ones.
* **`ape review` as one entrypoint** with `--execute` gating. Lowest value of these now that the
  sharp edges are individually fixed.

## Step 6 — the collapse

`src/mathlib_review/` with `ReviewArmTask` / `ReviewLeadTask` on `BaseLeanTask`, arms behind an
`ArmRuntime` that owns anchoring/confinement/budget while arms own strategy, one
`RetrievalContext` over the 8 implementations with the temporal gate written once instead of
four times, and v2/v4/v5 deleted. Boundary tests pin the current counts (11 backward v4→v5
names, 6 v5→v2, 42 private cross-module) so nothing worsens meanwhile.

---

## Verification

* `./ape/bin/python -m pytest tests/ -q` green at every step (1140 today).
* **Step 1:** `judgment` and `review_gate` pass their existing tests on `spawn_subtasks`;
  per-task limits are honoured (a job with a tighter limit pauses earlier than a sibling in the
  same batch); nested concurrency is bounded; one wave produces one nested orchestrator.
* **Step 2:** preflight refuses a run whose mandatory floor exceeds the run-total cap; a resumed
  lead recovers `delegated_spend` and its dedup set from the journal; every physical path in a
  run resolves through `execution_index.jsonl`.
* **Step 3:** a supported finding appears in both channels, an abstaining one only in `review`,
  a contradicted one in `review` with a warning and never in `verified`.
* **Step 4:** an arm declaring an unexpected concern is reported, not silently dropped.
* **Per arm:** `bench_cli --execute` runs and scores an arm with no lead. **Never yet run
  against a model** — the mechanism is verified offline against fabricated perfect, silent,
  noisy and wrong-declaration runs.

## Not in this plan

* **Running anything against a model.** The first real bench run — `family_design` on PR 33117,
  where it abstained and whose fixture now targets that exact obligation — is a handful of arm
  invocations and the sharpest cheap test available, but it is a spend decision.
* **The per-arm literature work** (premise selection and tactic search for `proof_golf`,
  retrieval-by-mechanism for `family_design`). The benches make it measurable; choosing
  components is the research that follows.
* **Coordination experiments.** The seam and the default policy exist; choosing among
  strategies is the next research step, not this rework.
