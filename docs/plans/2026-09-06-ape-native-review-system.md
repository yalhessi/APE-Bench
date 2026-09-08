<!-- Verbatim as approved. Status is not tracked here — see STATUS.md, which walks every
     numbered item. Keeping the plan unedited is the point: it is the record of what was
     decided and why, and annotating it in place would lose the distinction between what the
     plan asked for and what was built. -->

# Make the review system APE-native: everything is a task, coordination is a component

## Context

We have cycled between implementations without a breakthrough, so nothing in the tree is a
credible ablation baseline. The goal is **one good design** we can then ablate. Backward
compatibility with v2/v4/v5 is **not** a goal; git history is the archive. The one exception is a
dedicated reader for the September runs, which become forensic regression fixtures.

The organising problem is that the review pipeline was built **beside** the APE framework rather
than in it. `TaskOrchestrator(` is constructed directly in four files with **no shared primitive**:
`judgment/task.py:812` and `review_gate.py:322` share one simple pattern — flat `subtasks/`, both
setting `nested_token_usage` — while `pr_review_v5/delegation.py` invented
`subtasks/wave<N>/<tier>/`, its own `JobOutcome` and `_sample_facts`, and does **not** set
`nested_token_usage`. The accounting failure below is what that divergence cost.

**Coordination is the wall.** How a parent composes children is hardcoded in `delegation.py`: two
waves, three budget tiers, a lossy `summary()` upward, an immutable brief downward, no
child-to-child visibility, one merge at the end, and a pair may run **at most once**
(`lead.py:530-531`). None of it is named, configurable or measurable, so it cannot be explored —
and exploration is where this work is heading. Coordination gets a seam here so that work has
somewhere to attach.

### The measured problems

**Experiments touch too many files.** Adding one arm edits **13 source files across 6 packages**
plus 6 test files. **41 cross-generation imports** v5→v4/v2, **3 backward v4→v5 edges**, **20+
`_`-private cross-boundary imports**. This session changed `pr_review_v2/base.py` — the base class
for all three generations — on the strength of a v5-only observation.

**The CLI is a minefield.** 121 executable modules, **5 incompatible invocation conventions**,
`load_run` duplicated 3×. `V5DatasetConfig` ignores unknown keys, so a typo in `per_pr_cost_cap`
silently falls back to the default **8.0** against the 1.50 every config sets, while
`ExecutionConfig` rejects the same typo — the half of the config that spends money is the
unvalidated half. The command checked into `docs/research/medium-end-to-end-runbook.md` silently
does not parse. 13 load-bearing invariants live only in config comments; 3 are enforced.

**The books are wrong, and it changed a reported conclusion.** Both recent runs are marked
`completion_status: "failed"` and were scored anyway. Every step verified:

```
44% of every prompt is verbatim redundancy (33117's family_design prompt carries the
   same 100-line diff 5×, once per review target)
 → the arm exhausts the $0.30 standard cap mid-work
 → attempt.status = paused_cost_limit, nominal $0.3017, billed $0.1218
 → Sample.get_effective_cost() reads BILLED against a cap conversation.py:769
   enforced on NOMINAL → judged "resumable"
 → _try_aggregate writes no task_result.json
 → the ledger records status=failed, cost=0.0
 → the spend never enters delegated_spend → per_pr_cost_cap under-binds
 → `if invocation_id in state["outcomes"]` counts it as ran → coverage floor satisfied
 → agenda_report.units_without_specialist == []  — the field used to green-light the run
 → reported as "family_design abstains" when it was a budget cutoff
```

The nominal/billed split is a **half-landed fix**: `models.py:126`'s docstring records a prior
incident (a lead terminated at a $1.00 cap on a counted $1.164 having actually spent $0.200) and
moved *that* side to billed, while the conversation limit still fires on nominal.

On `heldout11_rep2`, four paused attempts hid **$1.8908 nominal / $0.6829 billed** against a
reported total of $10.1519 — **15.7% of the corrected nominal total of $12.0426** — while the
manifest said `paused: 0`. Separately, `token_usage` on a delegation row is the **tier total
copied onto every child** (59 jobs → 9 distinct values), so per-arm token attribution is impossible.

**Two findings that shape the design.** The evidence chain has produced **0 supported verdicts**
across both runs (18 packets → 17 inconclusive, 1 contradicted); every publication came from the
compile gate, but only **16 of 43 gold obligations are compile-checkable**. And of the 19 gold
obligations labelled `style`, **11 sit on one PR and are `grind` simplifications and `encard_`
renames** — golf and naming in substance — while `ALLOWED_CONCERN_BY_ARM` gates submission on
those labels, so an arm that correctly finds one is rejected for declaring the wrong concern.

---

## Design

### 1. Narrow bases, not one `ReviewTask`

Everything is an APE task; not everything shares a submission contract. Judge, lead, arms, corpus
digest and norm synthesis have different terminal artifacts, so they take the narrowest suitable
base:

```
BaseTask
└── BaseLeanTask
    ├── ReviewArmTask     candidate submission, anchoring, edit confinement
    ├── ReviewLeadTask    coordination tools, final lead report
    └── LeanJudgmentTask  the existing generic judgment task — used, not forked
```

`mathlib_review.evaluation` **constructs and consumes** `LeanJudgmentTask` rather than moving or
subclassing it. Future tasks (`mathlib_digest`, `norm_synthesis`) pick their own base; adding one
must not drag candidate-submission machinery along.

### 2. Arms are task types; variants are for whole-reviewer ablations

`TaskVariantDefinition` is a static Cartesian expander with no eligibility predicate, dynamic
brief, dependency, budget or redispatch semantics — so it cannot express arm scheduling. Instead:

- **`ArmCatalog`** — registered arm task types plus their eligibility predicates.
- **`Coordinator`** — builds `TaskExecutionSpec`s dynamically, per round.
- **`TaskVariantDefinition`** — reserved for top-level ablations of the *complete* reviewer
  (coordinator strategy, `lead_authority` mode, arm-set variations). That is the ablation
  machinery this project will want once one design is good.

**Fix variant identity before relying on it.** `generate_global_index` excludes `task_id`,
`metadata` and `global_index` (`base.py:109`), while `variant_id` lands in metadata — so two
variants of the same runtime task type collide in storage. Variant identity or the sealed plan
hash must enter storage identity.

### 3. The generic subtask contract

The framework hierarchy is **task → samples → attempts** (the judge runs `sample_count: 3`), so:

```
TaskOutcome
└── SampleOutcome[]
    └── AttemptOutcome[]      immutable
```

Separate execution from verdict:
- `TaskOutcome.execution_status` ∈ `completed | paused | failed | cancelled`
- `TaskOutcome.result` — optional valid terminal `BaseTaskResult`
- `BaseTaskResult.success` stays the **domain** result; a valid negative judgment is
  `success=False` and `execution_status=completed`
- **Never synthesize a result to represent a failure or pause.**

`TaskExecutionSpec` defines child identity, typed task data, per-task sample count,
model/runtime/scaffold overrides, turn/retry/billed-cost limits, requiredness, budget scope and
result projection. The orchestrator today has **one `sample_max_cost` for the whole batch** — which
is why budget tiers exist as groupings — so this plan explicitly adds **per-spec execution limits**
rather than recreating tier-specific orchestrators.

`BaseTask.spawn_subtasks()` is a thin convenience over an injected `SubtaskExecutor`. Nested
execution defaults to `num_processes=0` with **bounded async concurrency**; today nothing bounds it
(4 leads × 4 arms × 3 tiers ≈ 48 concurrent Lean compiles from one process).

### 4. Coordinator and SynthesisPolicy are separate, sealed separately

Otherwise a coordination ablation silently changes synthesis and neither is interpretable.

- **`Coordinator`** — rounds, dispatch, redispatch, report projection, stopping.
- **`SynthesisPolicy`** — deduplication, conflicts, lead authority, rewrites, admission.

Every strategy declares hard `max_rounds`, `max_jobs`, `max_redispatches_per_pair` and budget
bounds; `until_quiet` is not preflightable without them.

The blackboard is **coordinator-owned, append-only, typed**. Children receive logged read-only
snapshots through their next brief; they never share a mutable directory or inspect sibling
conversations. (An earlier draft proposed a shared blackboard, which contradicted the isolation
contract stated alongside it.)

`lead_authority` modes:
- **`router_only`** — lead schedules; deterministic synthesis owns the output.
- **`advisory`** — recommendations drive only mechanically safe duplicate/identity operations;
  semantic drops and rewrites are reported, not applied.
- **`final_arbiter`** — lead decisions applied and audited.

A lead rewrite creates a **new finding revision**; claim-scoped evidence does not transfer to
rewritten text and must be rebound or rerun before entering `verified`.

### 5. Arms own strategy; the runtime owns safety

```
async def run(request: ArmRequest, runtime: ArmRuntime) -> ArmResult
```

Arms own **strategy**: prompt, loop shape, tool choices, retrieval, warrant generation.
`ArmRuntime` centrally enforces **safety and accounting**: budgets, tool grants, temporal gates,
artifact recording, candidate schema, anchoring, edit confinement — duplicating those per arm is
how anchoring and confinement break. No arm imports another arm. **No mandatory file layout**: a
deterministic linter arm may be one file, an agent arm several. All 11 arms carry over for
migration parity, not as an endorsement of the set.

### 6. Benches are gold-bearing, so they live in evaluation

`obligation_capability.py:20` states gold-derived classification must never reach routing or
prompts, and this session already produced one contamination incident. Fixtures and scorers live in
`evaluation/benches/<arm>/`; the arm receives a gold-free work unit and the scorer sees the expected
obligation afterward. The capability is unchanged:

```
ape review bench duplication [--tools] [--execute]
```

runs one arm with no lead, no nested orchestrator, no judge run. `--execute` is required whenever
it calls models or writes. Each bench carries development positives, hard negatives and control
PRs, plus **held-out fixtures not consulted while changing the arm**, and reports candidate hit
rate, false-positive rate, verified/contradicted rates, cost per accepted finding, latency, illegal
submissions and tool usage — stamped with prompt/model/tool/corpus hashes, repeated for stochastic
arms.

### 7. Package layout

```
src/mathlib_review/
  domain/       schemas split by LIFECYCLE (Stage 2)
  corpus/       artifact catalog + source-specific typed retrieval
  arms/         one directory per arm, no fixed shape
  pipeline/     arm catalog, routing, coordinator, synthesis policy, finalization
  evaluation/   gold, benches, pairing, reports; constructs LeanJudgmentTask
  ape_tasks/    ReviewArmTask, ReviewLeadTask, discovery hook
  cli.py
```

`pr_review`, `pr_review_v2`, `pr_review_v4`, `pr_review_v5` are **deleted**. The live v2 surface is
3 modules (`pr_review_v2/base.py` with 3 importers, `precedent_bench.hunk_code`,
`corpus._eval_pr_numbers`); move those, delete the rest including `pr_review_v4/legacy/`. Old task
registrations, imports, configs and CLIs may disappear; keep only a dedicated September reader.
Retrieval uses source-specific typed requests under a shared `RetrievalContext(as_of, exclude_pr)`
— Zulip search and declaration search are not the same shape — with the temporal gate written
**once** (today 4 times) and paths from an injected `ArtifactCatalog`.

**Task registration is by discovery**, not a registry line: adding a task type means adding its
directory, or the "one-directory addition" goal is not met.

---

## Stage 0 — the framework primitive and the accounting

Landing this in `SubtaskExecutor` fixes the lead, `judgment` and `review_gate` together.

1. **`TaskOutcome / SampleOutcome / AttemptOutcome`** as above; `task_result.json` reserved for a
   legal successful completion.
2. **`paused` ≠ `partial`.** `paused` is a resumable run state; `partial` is a *closed* run that
   cannot satisfy required coverage.
3. **`UsageBreakdown`** with self / nested / inclusive values for **nominal**, **billed** and
   **budget-charged** cost. Enforce caps and resumability on billed; report nominal; never call
   nominal "real spend".
4. **Cumulative billed cost across every sample and attempt.** Today `get_effective_cost` returns
   the *last* non-error attempt's billed cost and `get_accumulated_cost` sums *all* attempts'
   nominal cost — the two differ on both axes and neither is cumulative-billed.
5. **Per-child usage, not tier totals** — `delegation.py:266-271` stamps the tier's
   `total_token_usage` and `elapsed` on every job (already named `_LEDGER_POISONED` at
   `delegation_view.py:45-47`).
6. **Atomic reservations** before parallel dispatch, settled after; `lead.py:537-541` checks once
   per wave and a per-job check at dispatch still races.
7. **Per-spec execution limits** in `TaskExecutionSpec`, replacing tier-grouped orchestrators.
8. **Hierarchical scopes** — lead-self, mandatory-floor, discretionary-per-PR, run-total. Mandatory
   bypasses only the discretionary cap, never the run total. Preflight fails when mandatory
   coverage cannot fit; today's dry-run message says "raise `per_pr_cost_cap`", a cap that does not
   bind the floor at all.
9. **Root inclusive usage counted once** via `nested_token_usage` (`ape/tasks/base.py:158`), which
   `lead.py:705-719` does not set; adjust `trace.reconcile` (`trace.py:148-152`).
10. **Failure reasons propagate** to delegation rows, reports and manifests.
11. **Mandatory failure ⇒ coverage gap ⇒ `partial`.** `lead.py:797-804` accepts a failed job as ran.
12. **Run transitions, explicit:**
    ```
    planned → running ↔ paused
                      → generated → finalized → judged
                      → partial
    ```
    Discretionary failures may still yield `generated`; unresolved mandatory coverage may not.
    Forensic processing never moves a partial run into the successful chain.
13. **Lead state as an append-only event journal** — reservations, dispatches, outcomes, synthesis
    decisions — reconstructed idempotently on resume so a crash cannot redispatch a child.
14. **`execution_index.jsonl`** mapping semantic run/sample/attempt/delegation/candidate IDs to
    physical paths and snapshot hashes — retires the hardcoded `samples/0` and fixed-depth globs
    (`trajectory.py:51,225`).
15. **Isolation contract, stated and tested** — own target, scratch, skills and conversation
    directories per child; no implicit shared or persistent subagent memory; parent→child only the
    immutable brief, child→parent only the typed report. Today this holds by accident of path
    derivation, with no lock, assertion or test.
16. **Kill the prompt redundancy** — `render_focused.py:87-99` and `render_prompts.py:168-178`
    inline `diff_fragments` per target and repeat `FACET_CHECKLIST`.
17. **Two one-line bugs** — `Path` unimported in `.../pr_review_v4/candidates.py` but used at
    `:322-326`; `trajectory.py:152` reads a `sample.json` path that never exists.

**Correction sidecars, not rewrites.** Leave the September ledgers untouched; add sidecars as
derived artifacts carrying derivation version and source hashes, recovering paused status and both
cost figures, and mark affected scores forensic. Extract **small, tracked** fixtures with source
hashes rather than depending on the gitignored `.ape` trees.

---

## Stage 1 — one entrypoint, strict config

- **`ape review`**: `plan | run | resume | finalize | judge | report | bench | build-corpus`.
- **Mutating commands are read-only without `--execute`** — print the sealed plan, paths,
  reservations and conflicts; no model calls, no writes. **Pure preflight must not instantiate
  `TaskOrchestrator`**, whose constructor does `workspace_path.mkdir(parents=True, exist_ok=True)`.
- **Overrides only via repeated `--set key=value`**; reject positional leftovers, unknown keys and
  malformed overrides. `parse_cli_args` (`config_loader.py:53-85`) currently discards any token
  without `=`, which is why the checked-in runbook command silently runs the wrong experiment.
- **`extends:`** — one relative parent, recursive mapping merge, list replacement, explicit nulls
  preserved, cycle detection. Headroom: 13 of 20 keys never vary across the 9 v5 generation
  configs, 13 of 18 across the 6 judge configs.
- **`extra="forbid"` everywhere**, recursively.
- **Resume is monotonic in execution only** — budget caps, timeouts, retry allowance — written as
  `run_plan_revision_N.json` with the prior plan hash and an explicit delta. Any prompt, model,
  corpus, routing, arm or evaluation change requires a **new run name**.
- **`judge --run`** derives all paths from that run. A live mismatch exists today:
  `pr_review_v5_medium_heldout.yaml` says `rep2`, its judge config reads `rep1/findings.jsonl`.
- **`evaluation_contract_version`** replaces "pairing tiers unchanged unless acknowledged":
  changing pairing tiers without incrementing it fails preflight.
- **Comment-invariants become preflight**: judge model pinned per release,
  `units_without_specialist` empty when the generalist floor is off, and `execution_release` /
  `skip_evidence_chain` / `pr_finding_limit` recorded in the plan.
- **Reusable templates** under `configs/review/`; resolved plans live in run receipts, not as a
  checked-in config per paid repetition. Delete the 36 untracked configs naming spent runs.

---

## Stage 2 — the collapse, the arm split, the coordinator

1. **Split the 2,187-line schema by LIFECYCLE, not by concern** — identities and work units;
   candidates and findings; evidence and warrants; execution and usage; run plans and manifests;
   evaluation records. Splitting by concern would bake the very taxonomy this plan shows to be
   unreliable into the domain model. Temporary re-export façade while migrating the 83 importers,
   then delete it.
2. **Move the 3 live v2 modules; delete v2, `v4/legacy/`, one-off scripts and superseded CLIs.**
3. **Merge into `src/mathlib_review/`**; introduce `ReviewArmTask` / `ReviewLeadTask`; discovery-
   based registration.
4. **Build `ArmCatalog` + `Coordinator`-driven dispatch**, replacing the pre-rendered agenda pool.
5. **Split the arms** into `arms/<arm>/` behind `ArmRuntime`, gathering what is spread across
   `pr_shared/focused_prompts.py`, `arms.py`, `arm.py`, `verifiers.py`, `routing.py`,
   `components.py` (`_INTENT_GRAIN`) and `census.py` (`_INTENT_KEYWORDS`, `_RELATION_ARMS` — which
   must agree with `_INTENT_GRAIN` by hand today). Benches land under `evaluation/`.
6. **Separate `SynthesisPolicy` from `Coordinator`**, sealed and hashed independently.
7. **De-duplicate the drifted constants** — `TIER_MULTIPLIERS` (verbatim in two packages, neither
   importing the other) and the `CONTEXT_TOOLS` docstring at `schema.py:47-51`, which still
   documents the uniform grant `arms.py` replaced this session.
8. **Boundary tests** — no legacy imports from active code, no `_`-private cross-package imports.
9. Delete `lead.py`'s dead `floor_summary` / `_floor_block` — `LEAD_USER` has no placeholder.

---

## Stage 3 — admission channels, provenance, reachability

1. **Two channels.** `review` = all synthesized maintainer-facing findings; `verified` = the subset
   with claim-scoped deterministic support and no contradiction. Contradiction is **not** an
   automatic veto: the finding stays in `review` with a warning and its full evidence trail, and is
   excluded from `verified`.
2. **Provenance replaces the concern gate.** Record immutable `origin_arm_id`; candidates carry
   non-gating, possibly multi-valued `concern_tags`; **remove `ALLOWED_CONCERN_BY_ARM` as an
   admission rule**; validate anchors, scope, requested change and evidence instead — not whether
   the arm guessed the evaluator's label. **Dependency:** the gate exists because removing it
   reintroduces a silent drop — `arm.py:50` records that a `generality` arm reporting a `style`
   claim passes submission and is then dropped at finalization for lacking an artifact "without a
   word", which on the rep2 smoke run was all four specialist candidates. Finalization must report
   every drop *before* the gate comes out, or a loud rejection becomes a silent one.
3. **Reachability is predeclared and evaluation-only.** Compute it from a mechanism-capability map
   declared and hashed **before** generation; it must not influence arm eligibility or prompts.
   Report total gold and reachable gold side by side, by concern and warrant. Do not label gold
   alignment as precision.
4. **Judging consumes final serialized findings**, never discarded pre-merge candidates. Gold,
   ambiguity registries, judge identity and metric definitions stay in `evaluation/`; any
   relabeling is versioned there and retains the original gold label.
5. **No broad new style/documentation checkers this iteration** — the evidence does not support the
   recall gain, and the linter-shaped cases are not decision-complete enough to scope here.

---

## Baseline policy

**This rework does not preserve comparability with today's runs.** The accounting fixes, prompt
deduplication, outcome semantics and concern-gate removal all materially change execution, so the
default coordinator preserving today's *topology* does not make results comparable. The September
runs are **forensic regression fixtures, not an ablation baseline**. The first successful paid probe
after Stages 0–2 is named the **new reference baseline**, and future coordination and arm work
compares against that sealed run.

---

## Verification

Assert invariants, not incidental numbers.

- `./ape/bin/python -m pytest tests/ -q` green at every stage boundary (971 today).
- **The primitive:** paused work records billed and nominal usage without a terminal result and
  resumes after a cap increase; one aggregate outcome per scheduled task over immutable
  sample/attempt records; execution status and domain success are independently assertable;
  failure reasons reach the manifest; sibling child totals reconcile with parent nested usage and
  root inclusive cost without duplication; cumulative billed cost spans all samples and attempts;
  atomic reservations prevent a parallel wave exceeding any cap; failed mandatory work yields a
  coverage gap and `partial`; child directories isolated and resolvable through the execution
  index. **`judgment` and `review_gate` migrate onto `spawn_subtasks` and their existing tests
  still pass** — the proof it is a real primitive and not a fourth convention.
- **Prompt rendering:** each hunk payload occurs once; the shared checklist occurs once; target
  identities and semantic prompt sections unchanged; the representative fixture records a
  substantial reduction.
- **Config:** strict config rejects the known typo and the malformed runbook forms; `extends:`
  merge, cycle detection, list replacement and no-execute preflight are deterministic; resume
  accepts a monotonic budget change and rejects a prompt change; **filesystem and model-client
  state are unchanged before and after every no-`--execute` command**; every config under
  `configs/review/**` loads.
- **Structure:** boundary tests; frozen September fixtures load through the dedicated reader;
  illegal submissions return structured feedback and a later legal submission terminates normally;
  a new task type is added by adding its directory alone; variant identity cannot collide in
  storage.
- **Channels and authority:** supported, abstaining and contradicted findings enter the correct
  channels; each `lead_authority` mode **respects its authority contract and records complete
  lineage** — identical outputs across modes may be correct and must not fail the test; a rewritten
  finding cannot inherit the prior revision's evidence into `verified`.
- **Per arm:** `ape review bench <arm>` runs with no lead and reports its full metric set;
  held-out fixtures stay unconsulted during arm changes.
- **Paid probe — provide, do not execute:**
  ```
  ./ape/bin/python -m ape review plan  --config configs/review/runs/verify-probe.yaml
  ./ape/bin/python -m ape review run   --config configs/review/runs/verify-probe.yaml --execute
  ./ape/bin/python -m ape review judge --run RUN --config configs/review/judges/verify-probe.yaml --execute
  ./ape/bin/python -m ape review report --run RUN
  ```
  Success = non-partial run, complete mandatory coverage, reconciled billed/nominal cost, correct
  per-child accounting, materially smaller prompts, judge inputs derived from that run. This run
  becomes the reference baseline.

## Deliberately not in this plan

- **The coordination experiments themselves.** Stage 2 builds the `Coordinator`/`SynthesisPolicy`
  seam and the default strategy; choosing among strategies is the next research step.
- **The per-arm literature work.** Stage 2 builds the benches that make it measurable — premise
  selection and tactic search for `proof_golf`, retrieval-by-mechanism for `family_design` (the
  `Mathlib/Tactic/**` docstring index PR 33117 needs).
- **Any change to arm prompt content** beyond removing the redundancy.
- **Revisiting the arm set.** All 11 carry over for migration parity; whether the set is right is a
  question the benches will answer.
