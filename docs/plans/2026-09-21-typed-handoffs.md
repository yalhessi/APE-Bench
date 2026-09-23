# Typed hand-offs: task↔subtask contract, stage provenance, and a declared stage graph

## Context

The v5 pipeline works, but every hand-off in it is hand-assembled, and that is where the friction and the
bloat come from. Verified against the tree on 2026-09-21:

- **Nested work has a primitive nobody uses.** `BaseTask.spawn_subtasks` / `orchestration.subtasks.run_subtasks`
  has zero production callers. The lead's `delegation.run_wave` builds its own `TaskOrchestrator`, its own
  outcome reader (`_sample_facts`, a duplicate of `collect_outcomes`) and its own closed dataclass (`JobOutcome`,
  whose own comment says an undeclared field is dropped silently). `judgment/task.py` and `review_gate.py`
  construct `TaskOrchestrator` directly too. The unused primitive has two latent defects: it sets
  `orchestrator_id` *after* the constructor has fixed the directory (children land under a timestamped dir, so a
  resumed parent cannot find them), and it reads children off `results.task_results`, which omits any task with
  a paused sample (`worker.py:631-634` writes `task_outcome.json` and returns before aggregation).
- **Child results travel as untyped dicts.** 18 sites use `model_dump(...) if hasattr(...) else raw`.
  `arm_responses` rows are built in three places and `delegations` rows in two, with literal
  `"schema_version"` strings, while `DelegationRecord` (a `StrictModel`) validates **no row on disk** (requires
  `source_sha256`, forbids `brief`/`delivered_prompt_sha256`/`reason_given`). `BaseTaskResult` is
  `extra="ignore"` and `create_result(**kwargs)` forwards blindly: the six-instance "field silently dropped"
  bug class (`abstention`, `model_confidence`, `rejected_alternatives`, `execution_limits`, `session_replay`,
  `documentation`/`docs`) starts here.
- **Stages are chained by one string typed N times.** `judge --of`, `replay --of` and `report conditions`
  each re-derive paths; nothing records that a run was judged, by which identity, into which audit.
  `run_state.py` states a machine that nothing writes: `FINALIZED`/`JUDGED` have no writer,
  `assert_transition` no caller. `docs/todo/pipeline-stage-chaining.md` (2026-09-21) names the fix (typed
  `StageInput`, named selectors) and the risk: the hand-off must stay *named provenance*.
- **Bucketing vocabularies exist but nothing joins them.** `review_overlay.STATES` (10-rung per-target
  ladder), miss-decomposition's COVERED / LOCATED-MISS / UNTOUCHED (v2-only), `reachability`, abstention
  reasons, context-trace rows, replay stability — the join that puts an obligation in a bucket is the scratch
  join the todo describes. Off-gold findings (~90% of output) are unadjudicated; the design for a cross-run
  label store exists (`docs/research/open-code-review-comparison-2026-09.md` §1) and is unbuilt.

**Decisions taken with the user (2026-09-21):** two topic branches in parallel worktrees; a **declared stage
graph** (A→B→C, A→{B,C}, each node with its own runtime config, downstream nodes starting as soon as their
upstream has closed and its artifacts exist; sibling nodes concurrent under a cap; re-invocation resumes) rather
than a `--judge-config` flag; adjudication as a **finding key + cross-run label store + human labels** now,
the LLM adjudicator task later under its own run name; coordination **readiness only** (prove each refused
policy value is ≤3 files after the contract lands; implement none).

**Reconciling the graph with "not a scheduler".** The user chose a runner. The todo's constraint is kept in
three ways: every stage remains independently runnable by its own verb and produces identical artifacts and
ledger rows; the runner adds ordering and dispatch only — it never computes a path or reads an artifact on a
stage's behalf (each stage reads through `StageInput` and records digests); and the graph itself is sealed into
the root run. Item-granular streaming (judge PR X while PR Y is still reviewing) is the follow-on, recorded in
`docs/todo/`, not built here.

**Not on `docs/dead-ends.md`.** Checked: no entry covers typed hand-offs, a stage ledger, or a stage graph.
Related cautions honoured: "test tractability before redesigning" (2026-09-08 §9) — this plan changes no
run's output (byte-identity checks at every step); `ArmRuntime` stays unbuilt; task `type` strings keep their
`v5` spelling; the shared review base stays under `src/ape/tasks/`.

## Workstream A — one typed contract for nested work (branch `subtask-contract`)

Worktree: `git worktree add -b subtask-contract .claude/worktrees/subtask-contract develop &&
.claude/worktree-setup.sh .claude/worktrees/subtask-contract`; `export PYTHONPATH=$PWD/src`.
Nothing here changes what a run produces: `global_index` of every arm payload, directory layout
`subtasks/wave<N>/<pr>_w<N>/tasks/<gi>`, journal row shapes, `arm_responses.jsonl` / `delegations.jsonl` keys
and bytes are pinned by tests at each step.

**A1 — `tasks: create_result refuses a kwarg the result class does not declare`**
- `src/ape/tasks/base.py:503-513`: `unknown = set(kwargs) - set(self.task_result_class.model_fields)` → `TypeError`
  naming class and keys. Persisted-file loading (`persistence.py:106-129`, `orchestrator.py:456`) untouched;
  `BaseTaskResult.model_config` stays default so old `task_result.json` files still load.
- Audit of the 17 `create_result(` sites: exactly one would raise —
  `src/ape/tasks/lean_tasks/formal_math/proof_engineering/task.py:397` passes `evaluation_result=`, undeclared,
  never persisted; delete the kwarg.
- Test `tests/ape/test_task_result_contract.py`: refuses undeclared, accepts declared, old dict with extra key
  still loads via `TaskStorage._normalize_sample`, `ReviewArmTask.create_result` still stamps identity.

**A2 — `orchestration: run_subtasks returns one typed ChildRun per scheduled child, paused ones included`**
- `models.py`: `ChildRun(spec, global_index, task_dir, outcome: TaskOutcome, result: Optional[Any])`,
  `succeeded = result is not None`. Delete never-read `TaskExecutionSpec.sample_count`/`retries`;
  `budget_scope: Literal["floor","discretionary"]`.
- `subtasks.py`: signature `run_subtasks(specs, *, attempt_path, config, group, logger=None, concurrency=None,
  execution_overrides=None, orchestrator_id=None, index_path=None, parent_id=None) -> (Dict[str, ChildRun],
  OrchestratorResults)`. `orchestrator_id` to the **constructor** (delete `:114`); `concurrency=None` keeps the
  config's value; `attempt_path=None` means top-level (config verbatim); `create_task_from_data(payload, config,
  task_config_overrides=config.task_config_overrides)` (mirrors `scaffolds/runner.py:424-428`).
  `collect_outcomes` iterates the **scheduled tasks** by `global_index` (`TaskStorage.load_all_samples` +
  `load_task_result`; `result = task.task_result_class.model_validate(...)` when successful); per-child
  `try/except` → `FAILED, reason="unreadable"` so a wave is never lost; WARNING per `required` child without a
  result. `BaseTask.spawn_subtasks` forwards `attempt_path/config/index_path/parent_id`.
- Tests (`tests/orchestration/test_subtask_primitive.py`): paused child appears as `PAUSED, result=None`;
  succeeded child's `result` is the task's result class; `orchestrator_id="33098_w1"` yields
  `attempt/subtasks/wave1/33098_w1`; `concurrency=None` keeps config; unreadable child loses nothing.

**A3 — `review: delegation runs its waves through run_subtasks; the wave's own outcome plumbing is deleted`**
- `delegation.py`: delete `_wave_config`, `_sample_facts`, `_outcome_status`, `_outcome_usage`, `_STATUS_MAP`,
  `_normalize_status`, the in-module `execution_index.record` call. Add `WAVE_EXECUTION_OVERRIDES =
  {"sample_count": 1, "early_stop_mode": EarlyStopMode.DISABLED}` (enum, not string — `:196-201` lesson),
  `JobSpec.required` (`disposition == "mandatory"`), `JobSpec.budget_scope`, `JobSpec.execution_spec(cap) ->
  TaskExecutionSpec` (`task_data = compose_prompt(payload, brief_text)`; `with_limits()` must equal today's
  payload at `:320-324` byte for byte so `global_index` is unchanged), `ledger_status(run)` (typed
  `ExecutionStatus` → `success|paused_cost|paused_turns|failed`), `JobOutcome.from_run(job, run, *, budget_cap,
  delivered_prompt_sha256)`. `run_wave` = caps → specs → `run_subtasks(..., orchestrator_id=f"{pr}_w{wave}",
  index_path=data.execution_index_path, parent_id=data.episode_id)` → `JobOutcome.from_run`.
  `JobSpec`/`JobOutcome` **stay dataclasses with today's field sets**: `lead_journals/*.jsonl` on disk pin them
  (`journal.replay` filters by `dataclasses.fields`).
- `lead.py:669` → `spec.budget_scope == "discretionary"`; `:863` → `spec.required and outcome.status != "success"`.
- Tests: `test_pr_review_v5_delegation.py` (`_wave_config` → `WAVE_EXECUTION_OVERRIDES`; monkeypatch
  `run_subtasks`); `test_subtask_isolation.py:93` → point at `subtasks.nested_config`; new: payload bytes equal
  the old inline dict; **journal compatibility** — replay a committed `lead_journals/*.jsonl` against its
  `arm_pool.jsonl` through `journal.replay`, every SETTLED row rebuilds; `test_pr_review_v5_brief.py:139`,
  `test_pr_review_v5_lead*.py` unchanged.

**A4 — `judgment, review_gate: nested judges run through run_subtasks; no nested caller constructs TaskOrchestrator`**
- `judgment/task.py:810-836`: `TaskExecutionSpec(spec_id="semantic_judge", task_type="lean_judgment",
  task_data=judge_data.model_dump(mode="json"))`; `run_subtasks([spec], attempt_path=parent_attempt_path,
  config=judge_config, group="subtasks", concurrency=None, execution_overrides={"num_processes": ...})`;
  `aggregated_result = runs["semantic_judge"].result` (`None` → existing failure branch);
  `nested_token_usage` still `results.total_token_usage`; `orchestrator_id` stays `None` (deterministic would turn
  a re-evaluation into a resume — behaviour change, other thread). `review_gate.py:321-366`: same.
- `test_subtask_primitive.py:229-248`: assert `"TaskOrchestrator(" not in text` and `"run_subtasks(" in text`
  for all three files; `global_index` of `create_task_from_data(judge_data.model_dump(...))` equals
  `LeanJudgmentTask(judge_data, cfg).data.global_index`.

**A5 — `schema: ArmResponse and DelegationRecord are the only constructors of their rows`**
- `schema/review.py`: `ArmResponse(StrictModel)` with exactly `ARM_RESPONSE_KEYS`
  (`tests/datasets/test_pr_review_v5_abstention.py:140-178`; `rendered_prompt_sha256` Optional — solo writes
  `None`), `.row()`, constructors `from_result` (fanout/rules), `from_job` (lead), explicit for solo.
  `DelegationRecord`: drop `source_sha256`; add `brief`, `delivered_prompt_sha256`, `reason_given`;
  `token_usage: Dict[str, Union[int, float]]` (float-only turns `"turns": 3` into `3.0`);
  `.row() = model_dump(mode="json", exclude_unset=True)` so the three on-disk shapes (lead-ran 20 keys,
  lead-pruned 18, rule/solo 10) survive byte-identically; constructors `ran`, `pruned_by_lead`, `by_rule`.
- Replace the literal dicts at `lead.py:820-910`, `runner.py:447-475`, `:527-558`, `:659-716`; fix the stale
  note in `analysis/delegation_view.py:52-58`.
- Tests: the three source-inspection tests in `test_pr_review_v5_abstention.py` become
  `set(ArmResponse.model_fields) == ARM_RESPONSE_KEYS` plus "no `responses.append({` literal remains";
  `test_pr_review_v5_finalize_replay.py`: every fixture row validates through `ArmResponse` and `finalize` over
  `.row()` output writes `findings.jsonl` **byte-identical**; for every committed
  `results/pr_review_v5/runs/*/delegations.jsonl` row, `jsonl_bytes([DelegationRecord.model_validate(r).row()])
  == jsonl_bytes([r])`. Boundary counts (`test_package_boundaries.py`) unchanged.

**A6 — `docs: subtask contract adopted; coordination readiness stated; framework defects recorded`**
- `docs/plans/STATUS.md` Stage 0 row 15 and six-steps row 1 → Built. `.claude/rules/mathlib-review.md`:
  locate children by scheduled `global_index`, never `results.task_results`; `orchestrator_id` is
  constructor-only. `docs/todo/framework-defects-2026-09.md` (motivating file:line each): `judge_mode` never
  reaches the worker's judge task (`create_task_from_data` builds a fresh `LeanJudgmentConfig`,
  `base.py:670-677`); `theorem_proving/task.py:147` omits required `theorem_statement` and raises on every
  termination; `TaskOutcome.resumable` uses the orchestrator-wide `sample_max_cost`, not the child's cap.
- **Coordination readiness (documented, not built).** Shared precondition (2 files): `ReviewLeadConfig` gains
  `coordination: CoordinationPolicy`; `runner.py` passes `coordination_config(dataset).coordination` via
  `task_config_overrides`. Then: `sibling_view="blackboard"` = `lead.py` (`BlackboardEntry` beside
  `InvestigationBrief`, `brief.board` rendered; `state["board"]` appended per settle from `summary()` claims) +
  `journal.py` (`BOARD_POSTED` event, replayed) + `coordination.py` (lift) — a board-bearing brief changes
  `rendered_user_prompt`, hence `global_index`, so no resume collision. `parent_view ∈ {counts, full}` =
  `JobOutcome.summary(view)` + `lead.py:689` + `coordination.py`. `max_redispatches_per_pair>0` = `lead.py:537`
  per-pair counter with `@n` suffix on `spec_id`/`invocation_id`, a brief that differs from every prior dispatch
  (identical payload would resume the previous run — `base.py:99-112`, `orchestrator.py:183`), `trace.py`
  reconcile strips the suffix, `coordination.py` lifts. Each ≤3 files; each is a run-name-changing lever and
  belongs to the coordination thread.

## Workstream B — stage provenance, a declared stage graph, and evaluation stages (branch `stage-provenance`)

Worktree: `git worktree add -b stage-provenance .claude/worktrees/stage-provenance develop && ...`.
Homes (no new modules except the framework primitive in B7): `StageInput`/ledger → `run_state.py`;
`StageRecord`, `PipelineSpec`, `PipelinePlan` → `schema/runs.py`; `AdjudicationLabel` → `schema/scoring.py`;
`finding_key` → `review/merge.py` beside `canonical_action`; selectors → `review/replay.py`; `buckets`,
`stages` → `analysis/report.py`; verbs → `review/cli.py`; DAG runner → `src/ape/orchestration/pipeline.py`.

**B1 — `analysis: report reads JSONL through io.jsonl_rows; splitlines cuts a U+2028 record in half`**
Delete `report.py:24 _load_jsonl` (and the `splitlines` at `:247`); callers use `io.jsonl_rows`.

**B2 — `run_state: StageInput resolves a run's artifacts, digests and state in one place; paths owns the audit root`**
- `paths.py`: `AUDITS = RESULTS / "audits"`, `ADJUDICATIONS = RESULTS / "adjudications"`; delete
  `judge/runner.py:443 JUDGE_AUDIT_ROOT` and `analysis/denominators.py:37 _AUDIT_ROOT`.
- `run_state.py`: `RUN_ARTIFACTS` table (name → filename, writer stage, append-only?, missing hint — the
  `arm_pool.jsonl` gitignored/worktree hint moves here from `replay.py:228-232`); `AUDIT_ARTIFACTS`;
  `StageInput` (frozen dataclass: `run_name, run_dir, release, state, manifest, consumed: Dict[name, sha256],
  audit_dir, consumed_audit, ledger`) with `at(directory, *, audit_dir=None, require=(), allow_partial=False)`,
  `of(run_name, *, audit=False|<node>, require=(), allow_partial=False)`, `path(name)` (raises naming the
  writer stage and hint); `state_of(directory)`: manifest → `from_manifest`; GENERATED + `findings.jsonl` →
  FINALIZED; non-forensic judge ledger row → JUDGED; plan without manifest → RUNNING; nothing → PLANNED.
  `release` from `agenda.json["release"]`. Hash only `require`d files (`context_trace.jsonl` is large).
- `derive_from_run(run_name, node="judge")`: default node keeps today's `audits/<slug>`; another node name →
  `audits/<slug>.<node>` — this is what lets one run carry several judges (B7).
- Tests extend `tests/mathlib_review/test_run_state.py`; source-inspection that `judge.runner`,
  `review.replay`, `analysis.report` reference `StageInput`.

**B3 — `judge: read the source run through StageInput and refuse a second judge identity into one audit before spending`**
`assert_source_run_is_complete` / `judged_pr_scope` keep signatures (pinned by
`test_pr_review_v4_judge_source_run.py`, `test_pr_review_v5_judge_denominator_scope.py`) but resolve through
`StageInput.at(Path(dataset.candidates).parent, require=("findings","run_manifest","agenda_report"),
allow_partial=...)`. In `run()` after `judge_identity` and before `dry_run` returns: if the ledger (fallback:
`out_dir/semantic_report.json["judge_identity"]`) shows a *different* identity for this audit dir, raise naming
both and the two overrides a second judgement needs. Today this fails only at the final `write_once`, after
spend.

**B4 — `run_state: an append-only stage ledger per run; run and judge write rows and the state machine is asserted, not described`**
- `io.py`: `append_jsonl(path, row)` (canonical bytes, `open("a")`, fsync) — the pipeline side's one append
  primitive (the `ape/` copies stay: framework must not import `src.mathlib_review`).
- `schema/runs.py`: `StageRecord(StrictModel)` — `schema_version="v5-stage1"`, `stage`, `node`, `pipeline`
  (root run, nullable), `run_name`, `consumed`, `consumed_audit`, `produced` (display_path → sha256),
  `identity`, `state_before`, `state_after`, `transition`, `forensic`, `evaluation_contract_version`,
  `git_commit`, `git_tree_state`, `written_at`, `source_sha256` (sealed via `sealed_model`).
- `run_state.py`: `append_stage(run_dir, record)`, `ledger(run_dir)`; `StageInput.ledger` reads it.
- `review/runner.py:run()` after `write_once(run_manifest.json)` (`:1311`): `assert_transition(RUNNING,
  from_manifest(...))` then `(GENERATED, FINALIZED)` when complete; row `stage="run"` with produced digests of
  every file written. `judge/runner.py:run()` after `sample_votes.jsonl`: row `stage="judge"` into the **source
  run's** ledger (digests and identity only — no gold content), `assert_transition(FINALIZED, JUDGED)` unless
  `forensic` (`allow_partial`) or same identity already judged (`transition=None`).
- `report stages --run X` (read-only): rows plus a reconciliation line (manifest state vs `state_of`,
  `ledger_missing_run_row`, audits on disk with no row — the archive).
- Risks: `stages.jsonl` is append-only; `write_once` must never touch it; `--redo` deletes it with the run
  (correct); a resume after pause writes no second `run` row (`guard_run_name` refuses reuse once terminal
  outputs exist) — `report stages` shows RUNNING for a crashed run.

**B5 — `replay: locate the source run through StageInput and leave a ledger row in it`**
`select_sources:224-232` → `StageInput.of(dataset.of_run, require=("execution_index","arm_pool","run_plan"))`;
`run_replay:423` takes `release` from `stage.release`; row `stage="replay"` (identity: `condition_sha256`,
`cut_label`, `sample_count`; `transition=None`). Test message still contains "gitignored".

**B6 — `analysis: reports read runs and audits through StageInput; the overlay reads semantic_matches.jsonl instead of planting a symlink in the audit`**
`conditions:547`, `score`, `overlay:439-455` via `StageInput`; `review_overlay.py:852` reads
`semantic_matches.jsonl` first, `matches.jsonl` second (v4 audits); delete the symlink block at
`report.py:451-455`. Test: `overlay` never creates a file inside the audit dir.

**B7 — `orchestration+cli: a declared stage graph runs stages as their artifacts become available and seals what it ran`**
- `src/ape/orchestration/pipeline.py` (framework primitive, generic — knows nothing about run/judge):
  `StageNode(name, needs: List[str])`, `StageStatus ∈ done|skipped|refused|failed|ran`,
  `run_pipeline(nodes, *, execute: Dict[name, Callable[[], Awaitable[Dict]]], is_done: Dict[name,
  Callable[[], bool]], max_parallel: int, logger) -> Dict[name, StageStatus+detail]`: validates acyclicity,
  starts a node the moment every `needs` is `done`/`ran`, bounded by an `asyncio.Semaphore(max_parallel)`;
  `is_done()` true → `done` without running (resume); a refusal (`ValueError`/`ReplayRefused`) → `refused` with
  the message, dependents `skipped(upstream_refused)`; never raises across nodes; returns the table.
- `schema/runs.py`: `PipelineSpec(StrictModel)`: `root: str`, `max_parallel_stages: int = 2`, `stages:
  Dict[name, PipelineNode]` where `PipelineNode(kind: Literal["run","judge","replay","adjudicate",
  "report.buckets"], config: Optional[Path], of: Optional[str], needs: List[str] = [], set: Dict[str, str] = {},
  select: Optional[str], labels: Optional[Path])`; validators: exactly one `run`-kind root, `of` names a
  `run`-kind node, `needs` resolvable, no cycles. `PipelinePlan` (sealed via `write_once` into the root run dir
  as `pipeline.json`): resolved graph, each node's config path + sha256 + overrides, derived run names / audit
  dirs (root = `--run-name`; judge → `derive_from_run(root, node)`; replay →
  `f"{root}_{node}_{condition}_{cut}"` so `run_replay`'s name check holds), `git_state`.
- `review/cli.py`: `pipeline --config <p.yaml> --run-name <root> [--set node.key=value] [--execute]`.
  Without `--execute`: validate the spec, load **every** node's config (a bad judge config fails before the run
  spends), run each kind's no-spend preflight (`run` → `plan`; judge/replay → config load + derived paths),
  print the resolved plan under the `NOTHING RAN` banner. With `--execute`: seal `pipeline.json`, then
  `run_pipeline` with adapters that call exactly the existing `_run/_judge/_replay/...` code paths; each stage
  still reads through `StageInput` and appends its own `StageRecord` (with `pipeline=root, node=name`);
  `is_done` = produced artifacts exist and a matching ledger row exists (identity equal). Exit non-zero if any
  node is `refused`/`failed`; `report stages --run <root>` shows the table. `pipeline` joins `SPENDS`.
- `configs/pipelines/heldout12_judged.yaml` as the worked example: `run → {judge, judge_relation}` where
  `judge_relation` sets `dataset.pairing_tiers: "[anchor, relation]"` (the never-run widening from
  `docs/todo/judge-and-measurement.md` §1) into `audits/<slug>.judge_relation`.
- Tests (`tests/orchestration/test_pipeline.py`, `test_pr_review_v5_cli.py`): topological start (B and C start
  only after A; B and C overlap under `max_parallel=2`, serialize under 1); a refused upstream skips
  dependents with the reason; `is_done` short-circuits; cycle and bad `of` refused at validation; `pipeline`
  in `SPENDS`; preflight loads every config and calls no runner (monkeypatch); `pipeline.json` sealed once.
- Note in the module docstring: stage-granular by design; per-PR streaming would need per-PR finalize outputs
  and is recorded as a todo (B12).

**B8 — `merge+scoring: finding_key and AdjudicationLabel; the full action_key recurs in 0 of 300 findings across reps, the site+kind key in 127`**
`review/merge.py`: `finding_key(finding) = f"{pr_number}|{primary_change_id}|{issue_kind}"` (measured
2026-09-21 on `pr5_A_lead_heldout12_v2_rep{1,2,3}`: fine key recurs in all three reps 0×, in ≥2 reps 2×;
coarse key 127× / 225×; within-run collision ~16%, reported beside label coverage). `schema/scoring.py`:
`AdjudicationLabel(StrictModel)` — `key, pr_number, primary_change_id, issue_kind, label ∈
correct_ask|wrong|valid_not_an_ask, exemplar_finding_id, exemplar_action_key, exemplar_source_sha256,
labelled_by ("human:<name>" | "task:<identity>"), adjudication_version, from_run, written_at, note,
source_sha256`. Export from `schema/__init__.py`. Test pins the recurrence numbers (skip if runs absent).

**B9 — `analysis: report buckets -- per-obligation ladder on the overlay's vocabulary, with the judge-independent coarse level from miss-decomposition`**
`report buckets --run X [--run Y …] [--audit] [--replay <run>]`, no spend. Built on `StageInput.of(run,
audit=…, require=("agenda","delegations","arm_responses","findings","context_trace"))`,
`analysis/delegation_view.load_lead_views` (already joins agenda+delegations+responses per PR),
`semantic_judge.eligible_obligations` + `obligation_exclusions.excluded_ids` (the same population
`scoped_obligations` uses), `finding_key`, `review_overlay.STATES/STATE_LABEL/deepest`.
Per obligation: cells = delegations whose `site_change_ids` meet `obligation.change_ids`; cell state in the
overlay's own vocabulary — `unscheduled · pruned · unavailable (ran, failed/paused = coverage gap) · silent ·
candidate (anchored finding exists but diagnostic/`channels=[]`) · finding (published)`; `state =
deepest(cells)`. Orthogonal annotations, never buckets: `abstention_reason` (or `unstated`),
`filed_elsewhere_in_unit`, `context ∈ none|empty|partial|ok` (from trace rows of the invocations that ran; tool
refusals are not traced today — say so, do not guess), `gate` (admission/channels of the deepest finding),
`judge ∈ null|unpaired|paired_unmatched|matched` (from `semantic_pairs`/`semantic_matches`), `replay_stable`
(when `--replay` covers the invocation). Coarse level: `UNTOUCHED` iff `state < candidate` (judge-independent);
with an audit `COVERED` iff `per_obligation.issue_status == hit` (read from the judge's report so it cannot
disagree with it) else `LOCATED_MISS`; without an audit → `LOCATED_UNJUDGED` and the report says to judge
first. Per finding: `judge` bucket, label (with `label_basis: exact|site_kind`), `reps_with_key: k/N` across
the `--run`s given. Output JSON carries per-bucket obligation ids, `requires` (digests read),
`evaluation_contract_version`, and the `location_recall_note` verbatim. Registered as pipeline kind
`report.buckets`.
Tests: tmp run built from the **real models** (`AgendaProposal`, `DelegationRecord`, `ReviewFinding`,
`JudgmentNode`) covering each state once; UNTOUCHED identical with/without audit; coarse counts equal the
judge's `obligation_status_counts` when an audit is present; on `pr5_A_lead_heldout12_v2_rep1` the `silent`
cells at `required` obligations with specialist arms number 45 (the replay diagnostic's population).

**B10 — `replay: named selectors sealed into the plan; gold-site-abstentions reproduces the 45 sessions the scratch join chose`**
`ReplayDatasetConfig.selector ∈ all|arm|invocation_ids|gold-site-abstentions|missed-obligations` (default
`all`); `select_invocations(dataset, stage)`; the two gold-dependent selectors call `analysis.report.buckets`
lazily and set `gold_derived=True` (`missed-obligations` refuses without an audit: "judge first");
`build_plan` seals `selection={selector, gold_derived, resolved ids, obligation_ids,
audit_semantic_report_sha256}` (not in `RESUMABLE_PLAN_FIELDS`, so a changed selection under one name is
refused); outcome rows carry `selector`; `replay_report` carries a `gold_derived_selection` caveat.
`cli replay --select`; pipeline node field `select`.

**B11 — `judge: cli adjudicate -- a cross-run label store keyed by site+kind, human labels without spend`**
`judge/runner.py`: `AdjudicateDatasetConfig(extra="forbid")` (`labels: Optional[Path]`, `allow_partial`);
`load_labels()/append_label()` over `paths.ADJUDICATIONS / "labels.jsonl"` (append-only via `io.append_jsonl`;
two rows on one key with different labels are `contested`; resolution = latest `human:` row else latest
`task:` row); `adjudicate(stage_input, ...)`: population = findings with judge bucket `unpaired` or
`paired_unmatched` (`matched` excluded), keyed by `finding_key`, joined to labels; `--labels <file>` ingests
`AdjudicationLabel` rows whose `labelled_by` starts with `human:`; writes `adjudication_report.json` into the
audit dir (`write_once`: per-finding rows, `labelled_share`, per-label counts, within-run key collision rate,
and the sentence that this is not precision until coverage is complete); ledger row `stage="adjudicate"`,
`identity={"adjudicator": "human", "labels_sha256"}`. `cli adjudicate --of <run> --labels <file>` is
read-only (no model) and **not** in `SPENDS`; pipeline kind `adjudicate` with `labels`. The LLM adjudicator
(`task:` rows, own task type and `adjudication_version`, own run name) is **not built**: `docs/todo/
adjudication-rubric.md` records the socket (`labelled_by` prefix, identity field, store) and the motivating
numbers (~90% off-gold; `gold_alignment_rate` 0.069→0.181 unreadable).

**B12 — `docs: stage chaining closed by StageInput and the ledger; the graph runner recorded as the user's choice; streaming and the rubric opened as todos`**
`docs/plans/2026-09-21-typed-handoffs.md` = this plan verbatim (plans are kept unedited; status in
`STATUS.md`). `docs/todo/pipeline-stage-chaining.md` → closed with commits, its Risk paragraph amended: the
user chose a declared graph runner and the constraint is met as stated in Context. `docs/todo/README.md`:
index line for `pipeline-stage-chaining.md` (missing today), new entries `pipeline-streaming.md` (per-PR
finalize + judge-resume-as-streaming; motivating: `finalize` is whole-run and `findings.jsonl` is one
`write_once` file) and `adjudication-rubric.md`. `docs/plans/STATUS.md` rows. `.claude/rules/mathlib-review.md`:
"a stage reads a run through `StageInput` and leaves a row in `stages.jsonl`; hand-built sibling paths are the
defect `judge --of` fixed once."

## What is deliberately not in this plan
- The nine finding representations stay (split by lifecycle on purpose; `144bde7`). The only lineage change is
  `finding_key`. The `model_confidence`/`rejected_alternatives` carry-through (2026-09-14 Step 1) is a
  separate, already-recorded item.
- No coordination policy is implemented; no replay condition is run; no judge rubric changes; no bump of
  `EVALUATION_CONTRACT_VERSION` (nothing here changes pairing, admission or the denominator — a `judge_relation`
  node changes what *its* number means and is labelled by its own audit dir and identity).
- No LLM adjudicator task; no per-PR streaming.

## Verification
- Each commit: `ape/bin/python -m pytest tests -q` green (10 Lean-workspace failures expected on a fresh
  clone); `ape/bin/python -m src.mathlib_review.release.verify_frozen verify` prints `ok`.
- No-spend identity checks: `plan --config configs/pr_review_v5_specialist4.yaml --run-name identity_check`
  seals the same agenda before/after A3–A5; `test_pr_review_v5_finalize_replay.py` byte-identical
  `findings.jsonl` on the committed `specialist4_rep1` responses; every committed `delegations.jsonl` row
  round-trips through `DelegationRecord.row()` byte-identically; journal replay on a committed
  `lead_journals/*.jsonl`.
- Framework: `test_every_nested_call_site_uses_the_shared_convention` forbids `TaskOrchestrator(` in the
  three nested files; `grep -rn "TaskOrchestrator(" src/` leaves only `orchestrator.py`, `subtasks.py`, the
  top-level drivers (`review/runner.py`, `judge/runner.py`, `replay.py`, `bench_cli.py`, `opportunities/
  runner.py`, `retrieve/lean/build.py`).
- Stage graph, no spend: `cli pipeline --config configs/pipelines/heldout12_judged.yaml --run-name
  pipeline_dry` prints the resolved graph, derived audit dirs and every node's loaded config, and writes
  nothing. `report buckets --run pr5_A_lead_heldout12_v2_rep1` (committed run) reproduces 45 `silent`
  gold-site specialist cells and coarse counts equal to its audit's `obligation_status_counts`.
- Paid (user's call, ~$2, smoke4): one `run` after A5 to confirm `arm_responses.jsonl`/`delegations.jsonl`
  key sets and the `subtasks/wave1/<pr>_w1/` layout on a live nested orchestrator; then `pipeline --execute` on
  `run → judge` for that same run name to confirm resume-as-done (the judge node runs; a second invocation
  reports both nodes `done`).
- Merge order: A and B are disjoint except `schema/__init__.py` exports and the docs files; merge whichever
  finishes first into `develop`, rebase the other's docs step.
