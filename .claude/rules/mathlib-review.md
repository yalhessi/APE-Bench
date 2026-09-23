---
paths:
  - "src/mathlib_review/**"
  - "src/ape/tasks/lean_tasks/formal_math/review/**"
  - "src/ape/tasks/lean_tasks/formal_math/pr_shared/**"
  - "tests/mathlib_review/**"
---
# mathlib_review: traps that have already bitten

- **Import rewrites.** `schema` and `evidence` each existed as a top-level module AND as a sibling
  inside a subpackage, so a name-based rewrite silently sends v4 files to v5's module. Resolve an
  import from the original file in git history, never by searching for what defines the name (that
  heuristic turned `from .phase7_adjudication import adjudicate` into a self-import).
- **Structural guards go vacuous.** A test that globs a package path passes trivially once the path
  is deleted. When moving or deleting a package, check that every `Path(...)` a guard test targets
  still exists.
- **Adding an arm is exactly two edits:** `ARM_DEFINITIONS` in `src/mathlib_review/agenda/registry.py` and a `FOCUSED_PROMPTS`
  entry in `src/ape/tasks/lean_tasks/formal_math/review/focused_prompts.py`. Spec, tool grant, bench
  roster and concern vocabulary derive from those. Do not add a third place.
- **Concern vocabulary:** arms say `documentation`, gold says `docs`; both spellings are hashed into
  sealed artifacts. Bridge through `CONCERN_ALIASES` (`src/mathlib_review/analysis/benches.py`), never rename. This one-word
  mismatch made the docs arm unmeasurable for its whole life.
- **Judge versions never join or resume into each other** — `judge_version` is in the cache key and
  the record hash. Active rubric v8; v7.1 sits in `legacy_pipeline` for provenance only, and history
  is not re-scored under it. The judge refuses a `partial` run without `allow_partial: true`, and
  `judge` requires `--of <run_name>`: judge configs carry no paths because `candidates` / `out_dir` /
  `run_name` are one identity.
- **Coordination is a refusable policy** (`review/coordination.py::assert_implemented`): a config
  field that is read but not implemented would attribute a result to a mechanism that never ran.
  Implement before accepting a new value.
- **The retrieval cutoff is gold-free** (`agenda/cutoffs.py`: committer timestamp of
  `reviewed_head_sha`). `review_started_at` lives under `gold/` and generation code may not read it.
  `lean_retrieve` is deliberately unused here; the precedent index is dense and filters *before*
  ranking (filtering a ranked top-k silently shortens it).
- **Per-arm benches score location + silence only** — a bench hit is necessary, not sufficient, for a
  scored hit. Payloads come from `build_agenda`; never rebuild them, and they carry no gold.
- **A task-data key the task model does not declare was dropped on the way to the worker
  (fixed 2026-09-16).** `TaskOrchestrator` built each job's `task_data` from
  `task.data.model_dump()`, and `BaseTaskData` ignores undeclared keys, so every reserved
  run-level directive vanished between the caller and the runtime: the lead's
  `execution_limits` never reached its arms (they ran under the *nested* orchestrator's
  `sample_max_cost` -- $1.00 -- not the run's `standard_budget_cap` of $0.30, so every v5 arm
  cap in the record is the looser number), and a decision-turn replay ran the task from its
  prompt instead, producing submissions that looked exactly like replays. `BaseTask.job_data()`
  now carries the payload's extra keys alongside the validated dump. **A directive that
  travels in task data must be asserted at the far end, not at the near one:** the unit test
  passed `task_data` straight to `main_from_params` and could not see the orchestrator drop it;
  what caught it was one real one-sample run and the absence of `session_replay.json` in the
  attempt. Every replay outcome row now carries `replayed_from_prefix`, and `replay_report`
  refuses a run with any stray row rather than reporting a re-run's variance as a decision's.
- **Caps bind billed cost, not nominal** (they differ ~2.5× with prompt caching), so a job spends its
  whole cap; every scheduled task writes `task_outcome.json`; `task_result.json` is never synthesised
  for a pause or failure.
- **Never read JSONL with `splitlines()`; use `io.jsonl_rows` (or `io.load_jsonl`).** `jsonl_bytes`
  joins on `\n` and `canonical_json_bytes` writes `ensure_ascii=False`, so a record keeps U+2028,
  U+2029, U+0085, `\v`, `\f`, `\x1c`, `\x1d`, `\x1e` verbatim -- and `splitlines()` breaks on all
  of them, cutting a record in half mid-string. Two of 32,851 collected PRs carry U+2028 in a
  comment body; it killed the pre-gate with `Unterminated string` and a traceback naming no PR.
  Fixing the *writer* is not an option: escaping at write time rewrites every stored digest.
- **Check a store file against its ledger digest before believing it is corrupt.** Both damaged
  reads were `digest=ok json=BAD` -- intact bytes, wrong reader. `store.read` now reports which,
  and that distinction is the whole diagnosis.
- Boundary counts are pinned in `tests/datasets/test_package_boundaries.py` (0 backward
  cross-generation edges, 0 v5→v2, 3 private in-package imports). They may only go down.
- **Verification needs the *reviewed* workspace, not the source-only overlay.** The overlay
  (`_ensure_patched_target_workspace`) symlinks the base snapshot, materialises touched paths and
  applies δ₀ — it builds nothing, and `.lake` is a symlink into the shared cache — so every compile
  sees base `.olean`s, and on a multi-file PR a declaration the PR adds or renames in one file is
  `Unknown constant` when any other file is verified; the tool's note then asserted the file does not
  compile (13% of arm sessions on the held-out run; 16 `broken_build` findings on PRs that build).
  Fixed 2026-09-12: `workspaces/<base>+<fp>` = base + diff + changed modules rebuilt
  (`BuildManager.build_reviewed_workspace`; 2.4–16.6 min each on this NFS, driven by the import-path
  length between changed modules, not file count; the 2.8 GB `.lake/build` copy is the cost —
  hardlinks fail because Lean truncates `.ilean` in place). Build with
  `prebuild --reviewed --config <run cfg> --execute`; `plan` reports how many episodes lack one;
  `dataset.require_reviewed_workspaces: true` makes `run` refuse (on for the held-out configs, off in
  the base because smoke4 is unbuilt); the task falls back to the overlay at WARNING otherwise. Scope:
  only a *changed* file has a fully rebuilt import closure — dependents off the path between changed
  modules keep merge-base `.olean`s, and `lake env lean` never checks traces. Prebuild from one host
  and one shell (pid liveness is host-local). Full account: `docs/research/reviewed-workspaces.md`.
  Still true: never suppress a compile claim in a prompt — a compile claim on a PR that builds is a
  tool defect until proven otherwise, and now the first question is whether the run verified against
  a reviewed workspace (`plan` says).
- **A reviewed state that does not compile has no reviewed workspace, and never will.** The corpus
  premise "the PR compiles" is about the *merged* state; an episode is cut at a review round, and a
  maintainer who reviews a red PR is reviewing exactly the state `prebuild --reviewed` tries to
  build. 33057 round1 is one: the gold obligation *is* "Delegating so you can fix the last error",
  and the reviewed file has one `unsolved goals` at `expand_apply` — the merged version differs in
  one token (`simp only` → `simp`). `prebuild` will fail on such an episode on every invocation and
  `require_reviewed_workspaces: true` refuses any run containing it. Before treating a reviewed
  build failure as a tooling bug, compile the patched changed file against the base and read the
  error: on a **one-file** PR the base `.olean`s are the right environment, so `lake env lean
  <patched file>` with cwd = the base workspace answers in ~1 min instead of ~8. Note the inversion
  such an episode creates: the overlay fallback tells the agent "not evidence the PR fails to
  build", while the gold finding *is* a build failure.
- **The naming arm's silence was tooling before it was contract — retracted 2026-09-13.** This entry
  called it "a contract decision, not a bug". The arm *did* ask the corpus question (39 of 109
  `content_search` calls in the held-out run scoped to `target/Mathlib`, 60 with regex) and got its
  own neighbourhood back: `Path.rglob` does not descend the overlay's symlinks, so `target/Mathlib`
  reached 66 of 7,443 files with no warning — its `toLinearMap_` query matched 4 files then, 105 now
  (`c14fa9b`). `zulip_search` returned nothing on 71% of calls (FTS5 ANDed every term, and
  punctuation was a syntax error) — 4% after `9bf474e`. Naming hits from `precedent_search` are
  chance-level (3.3% naming-shaped vs a 3.28% base rate): the index embeds the diff hunk, never the
  comment body. And the abstention is mute — `submit_candidates([])` carries no reason — so there
  was never a rationale to aim a prompt at. **Before reading an arm's silence as its contract,
  replay its own queries through the tool on the real attempt workspace.** The contract is still
  open and is §D2 of `docs/research/pr-review-v5-principled-design.md` (norm store with maturity;
  emerging norms license advisory findings only), never built. Flat prefix prevalence is not the
  bar: at 33337's base `toLinearMap_` has ~50 declarations to `coe_`'s ~4,714.
- **A closed vocabulary silently filters a correct registration — three times now.** The pattern:
  a thing is registered correctly in the place that looks authoritative, and a second list that
  nothing checks it against drops it with no error. `documentation` vs `docs` made the docs arm
  unmeasurable for its whole life; the retrieval gate's closed `gate` Literal refused a compound
  value; `CONTEXT_TOOLS` in `schema/review.py` filtered `naming_norm` out of the naming arm's
  grant after it was added to `ARM_DEFINITIONS` *and* `_REGISTRARS`, so a paid run came back
  looking like "the new contract changed nothing" when the tool had never been registered
  ($1.11, 33337 rep14). **Before spending on a run that tests a new capability, assert the
  capability reaches the task** — and not with `plan`, which logs "DRY RUN — nothing is written"
  and leaves no `arm_pool.jsonl` to read. What works, in a second and for nothing:
  `ape/bin/python -c "from src.mathlib_review.agenda.arms import _grant_for; print(_grant_for('naming'))"`,
  or `ape/bin/python -m pytest tests/datasets/test_context_tool_grants_survive.py -q`. After a
  paid run, `arm_pool.jsonl`'s `task_data.context_tools` is the record of what the arm actually
  held. Adding an arm is two edits; adding a *tool* is four — registrar, `ARM_DEFINITIONS`,
  `CONTEXT_TOOLS`, and `ContextCall.tool`.
- **`declaration_search` was base-only by construction** — an arm judging a *rename* could not look
  up the name the PR introduced. It now also searches the PR's changed files in the reviewed
  overlay (`declared_before_this_pr` / `declared_in_this_pr`, `reviewed:` ids); the gate stays
  `base_snapshot` because the gate vocabulary is closed (`test_retrieval_gate.py`).
- **Tool output lives in `result_content`; a transcript's `tool_result.content` is always `null`.**
  `ape.llm_clients.models:55` stores the unified string form in `result_content` and never
  populates `content` for a `tool_result` block. Hand-parsing `content` therefore yields the
  literal string `"null"` for every tool result, which matches no pattern and lands every session
  in whatever bucket the classifier uses last — a 100%-in-one-class result that looks like a
  finding. This cost three retracted analyses in one sitting (100% "judgement stop", then all
  "unclear", then 100% "had usable content"). **A uniform 100% partition is the symptom; check the
  field before believing it.** `src/mathlib_review/analysis/trajectory.py:226` already reads it
  correctly — use `cli trajectory`, or copy its accessor, rather than re-parsing JSONL by hand.
  Two more shapes that bit the same analysis: the per-turn files under an attempt's
  `conversations/` are **cumulative** (read only the last one, or every call is counted N times),
  and `_attribute_errors` (`review/base.py:392`) **keeps `errors` intact** and *adds*
  `errors_introduced_by_your_edit` / `errors_already_in_the_file` — so a non-empty `errors` does
  not mean the agent's edit failed, only the split field does.
- **A hand-built fake cannot disagree with the class it stands in for.** Twice in one session:
  a fixture built a `BuildManager` with `__new__` and set `workspace_dir` by hand, so the fake
  had an attribute the real class did not and the first real prebuild died in 1s with
  `'BuildManager' object has no attribute 'workspace_dir'`; and `_record_outcome` in
  `test_pr_review_v5_lead.py` built a `SimpleNamespace` shaped like a `JobOutcome`, so when the
  lead started reading a new field the three tests that exercise that exact code path kept
  passing until the field was added to the real dataclass. Both fakes were green precisely
  because they were free to be wrong. **Construct the real class in a fixture** — a dataclass or
  pydantic model is cheap to build and will refuse an argument it does not have. Reserve
  `SimpleNamespace` for things with no class to construct.
- **"Last tool before submit" is not investigation depth — retracted 2026-09-13.** A last-action
  analysis of `pr5_A_lead_heldout12_rep1` put 40% of empty arm submissions (33 of 82) at
  "stopped on an as-is compile check, which proves nothing", and that number went into
  `591961d`'s commit message as evidence of shallow specialist work. It is an accurate count of
  *final tool calls* and a wrong diagnosis. Once `submit_candidates` recorded why an arm
  abstained (`5699f3a`), the arms ending that way turned out to have done the work and then made
  a closing compile call: *"Checked the module doc in `Mathlib/Data/Matrix/Mul.lean`: the updated
  reference `.../ConjTranspose.lean` exists and its module doc indeed introduces…"*. Measured
  directly, tool calls before an empty submission are **median 6.0** against **median 7.0 before
  a finding** (n=95/23; the validation run repeats it at 6.0 vs 6.5, n=17/8) — an arm that
  abstains investigates about as much as one that files, and the shallow-work premise does not
  survive it. **A tool-call histogram cannot see deliberation; ask the agent and record the
  answer.** The reshape in `591961d` stands on its own ground — a no-op compile returning
  `success: true` was wrong however deep the session was, and it fixed a false promise in the
  `correctness` prompt — but as-is endings did *not* fall after it (9 of 17, 53%), so it is not
  the fix for a problem that was mostly not there.
- **Any proposal about which of the system's findings reach a maintainer is SELECTION, however it
  is phrased (2026-09-22).** It has now been derived five times under five names: a pointwise
  selector, a listwise one, an agentic one, a legibility score, and "the publication rule" -- the
  last of which got past the standing refusal in `dead-ends.md` by being about concern *families*
  rather than individual findings, which is the same decision at a coarser grain. The tells: a keep
  rule, a threshold, a ranking, a second channel, a confidence cut, "publish the families that
  hit". **The ordering rule that comes first: fix the generator.** The user's ruling, 2026-09-22 --
  *"we currently don't have a good enough reviewer to start talking about selection"* -- and the one
  intervention that moved issue recall (0.20 -> 0.50) did it by changing what the arms say, not by
  re-ranking what they had already said. Measuring the gate is fine and the measurement is kept;
  proposing a different gate is not.
- **"What the run found" and "what it would tell a maintainer" are different numbers, and only
  one was ever reported (2026-09-22).** `finalize` publishes a claim only when a deterministic
  collector can warrant its concern family and keeps the rest as `diagnostic` with `channels: []`.
  Over the three held-out A reps the run hits **7 / 5 / 6** gold obligations and publishes
  **2 / 1 / 1**; 21 of rep1's 24 suppressed hit-findings say "no collector can support this
  claim's concern family". The gate's axis is close to orthogonal to where maintainers ask:
  `correctness` files 161, hits 39, publishes 2, while `generalization` has never hit and
  publishes 40%; the generalist holds **64 of 71** hits at 2.8% publication. Quote the pair, never
  one of them -- `report buckets --audit` prints both in its `gate` block, with control emission
  beside them, because published control emission is **0/0/0** against 12 pre-gate and the gate is
  what buys it. `docs/research/the-admission-gate-2026-09.md`.
- **A capability nothing has ever exercised is a capability nobody has ever tested (2026-09-22).**
  `patch_set` -- the one way to submit a fix spanning declarations -- was carried by 0 of 3,411
  candidates across 60 runs, and *five* independent defects were waiting in it: granted to the one
  arm that never files, `Path(WorkspaceInfo)` raising on first use, `apply` splicing a declaration
  by `text.replace(name, new, 1)` so a well-formed edit rewrote the first *mention* of the name
  (its own docstring) and compiled the wreckage, the contract template omitting the field under
  "This supersedes any field list above", and the finding schema dropping it before the judge. Two
  of the five had tests written over them that passed: one assigned a string where the runtime
  passes a `WorkspaceInfo`, and every source in the patch-set tests was a single line whose
  declaration name occurred exactly once. **Before costing a capability's absence as a finding
  about the model, exercise it once by hand** -- here that was two local compiles, no spend, and it
  is the check that separates "the arms decline to use it" from "it never worked".
- **A gold-site silence is not evidence about an arm unless the ask was in that arm's remit
  (2026-09-21).** "41 of 45 gold-site specialist silences reproduce under replay" was read for a
  week as arms withholding findings, and a plan costed three interventions against it. Labelling
  all 58 silent sessions against the ask each was silent about says otherwise: **37 are an arm
  correctly quiet about somebody else's concern** (`duplication` at a rename, `naming` at "factor
  out the repeated argument"), 17 are the right arm declining on stated grounds, and the three
  mechanisms total four sessions. An on-concern arm was scheduled at **22 of 22** counted
  obligations, so this is not a coverage gap either. `cli report silences` computes the remit test
  (`registry.expected_concerns` bridged through `benches.gold_labels_for`); use it before reading
  any silence count as a fact about a contract, and see
  `docs/research/specialist-silences-2026-09.md`.
- **The abstention *reason* is not the diagnosis; the detail is.** Replay produced a different
  `abstention_reason` on 17 of 45 sessions with the outcome unchanged -- `already_correct` and
  `could_not_establish` swap freely -- so any split built on the enum (including the 76%
  `already_correct` figure that motivated the forcing experiment) is measuring a coin flip. Label
  from `abstention_detail`, which now survives into replay outcome rows and into `report silences`.
  `finalize` reads neither: it contains no occurrence of `abstention`.
- **`naming_norm` counts leaf PREFIXES only** (`naming_norm.py:122`, `leaf.split("_", 1)[0]`), so a
  convention expressed in a suffix is invisible to it at any threshold. PR 33421's gold ask renames
  `round_eq'` to `round_eq_div`; both are prefix `round`. Separate from the unreachable 0.80 bar
  already recorded in `docs/todo/specialist-arm-contents.md`.
- **Control-PR emission is 0-1 per run, not 0.** Measured over every v5 run covering 33315:
  `heldout12_rep1` 0/13 invocations, `heldout11_rep1` 1/11 (generalist), `heldout11_rep2` 1/11
  (generalist), `medium_heldout_rep1` 0/13, `validate_abstention_rep1` 1/18 (docs). The "0 false
  candidates per control per rep" figure is the **v4 deterministic arm's**, from the
  deterministic-precision comparison (0 vs 2 against the generalist), and does not transfer to a
  v5 lead run — it was mis-transferred into a commit message and into run advice on 2026-09-13.
  A single control candidate is inside the historical range and is not evidence that a change
  regressed precision; it takes reps, and the source says to label it `silent_pr_emission`,
  never a false-finding rate.
- **Read a nested run's children from what was SCHEDULED, never from `results.task_results`.**
  The orchestrator aggregates only finished tasks, and a task with a resumable sample writes
  `task_outcome.json` and returns *before* aggregation — so a job that spent its whole cap and
  concluded nothing is absent from that list entirely. Both readers this repository had did
  exactly that; `cli replay` hit it, lost two whole sessions, and worked around it by locating
  task directories from the tasks it had scheduled. `run_subtasks` is now the one way to nest
  work and returns a `ChildRun` per spec — the spec, the `TaskOutcome` and the child's own
  *typed* result — built from the scheduled tasks. `succeeded` means a legal submission came
  back, never `execution_status == COMPLETED`: a task can complete having concluded nothing,
  and a failed floor job once counted as coverage on exactly that conflation.
- **`orchestrator_id` is a constructor argument.** `TaskOrchestrator.__init__` fixes
  `workspace_path = runs_base_dir / orchestrator_id`, so assigning it afterwards changes
  nothing except making `OrchestratorResults.orchestrator_id` disagree with the directory —
  children land under `orchestrator_<timestamp>_<hash>/` and a resumed parent cannot find work
  it already paid for.
- **A ledger row has one constructor.** `ArmResponse` and `DelegationRecord`
  (`schema/review.py`) are the only writers of `arm_responses.jsonl` and `delegations.jsonl`;
  five dict literals in two files wrote them before, compared only by a test that parsed their
  own source for quoted keys. `row()` uses `exclude_unset` deliberately: a pruned job carries
  its outcome keys explicitly null and a rule-dispatched job does not carry them at all, and
  flattening those makes "considered and declined" indistinguishable from "never considered".
  Before changing either model, run `tests/datasets/test_pr_review_v5_row_models.py` — it
  round-trips every row in the tree, byte for byte, which is how a float-typed `turns` gets
  caught before it rewrites 20,262 rows.
- **A stage reads a run through `StageInput` and leaves a row in `stages.jsonl`.** Rebuilding a
  sibling path by hand is the defect `judge --of` fixed once and nothing generalised: the judge
  still rebuilt `run_manifest.json` and `agenda_report.json` that way, replay re-implemented the
  whole check, and choosing 45 replay sessions took a scratch join across four files that a
  named selector reproduces as 58 (it filtered on required gold changes; the selector filters on
  gold sites). `StageInput.at/of` resolves the artifacts a stage names, hashes exactly those,
  and refuses a run whose manifest says it did not cover what it promised -- while a run with no
  manifest stays *unchecked* rather than refused, because v4 runs never wrote one.
  `run_state.RUN_ARTIFACTS` is where an artifact's filename, its writing stage and its
  missing-file hint live; add one there, not in a caller.
- **`write_once` and `append_jsonl` are different guarantees, and mixing them loses one.**
  `write_once` refuses a second write with different bytes, which is what makes a run
  reproducible; it must never touch a file written *while* work happens. Those -- the lead
  journal, the context trace, the execution index, `stages.jsonl` -- are appended, and their
  reader (`io.appended_rows`) stops at the first line it cannot parse, because a crash truncates
  the last line by construction. Reading one with the strict reader loses every row before the
  tear.
- **A label is not gold and must never become gold.** `cli adjudicate` records judgements about
  the ~90% of findings gold cannot judge, keyed by `finding_key` (site and kind, which recurs
  127 times across three reps where the full key recurs 0). Gold's worth is that it is revealed
  preference -- what maintainers actually asked for. An adjudication label is an opinion about
  what they did not ask for: it may order a queue and say how much output has been read, and it
  may not enter recall or be reported as precision. A human row outranks a `task:` row, a
  correction is a later row rather than an edit, and disagreement is reported, never averaged.
