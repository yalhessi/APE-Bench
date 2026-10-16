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
- **Adding a per-PR review design is three edits** (2026-10-02, `docs/plans/2026-10-02-review-designs.md`):
  a task module under `src/ape/tasks/lean_tasks/formal_math/review/` subclassing `SoloReviewTask`
  (its result keeps the solo's `findings`/`episode_id`; it may override `design_payload`,
  `describe_design_payload` and `reads_stage`), one line in `DESIGNS` in that package's
  `__init__.py`, and one `configs/designs/<design>_<set>_<route>.yaml` extending the frozen
  baseline and stating `dataset.design` alone. Never a branch in the runner, and never an edit to
  `solo.py`'s prompts or the two baseline configs: `test_pr_review_v5_designs.py` pins them by
  digest and refuses a design config that differs from its baseline in anything else. A design that
  reads a finished run (`reads_stage`) takes it as `--of <run>` on `plan`/`run`, through `StageInput`.
- **What moves a hash, and what does not** (2026-10-06, `docs/research/codebase-redesign-2026-10.md` §4.3).
  Renaming a class or moving a module moves nothing: no `__name__` or `__module__` enters an identity.
  Identity is: a task `type` string (`FocusedAgentSpec.identity()`, and resume's `get_task_class`),
  prompt text (`prompt_sha256` → spec → agenda → plan), the *field set* of any `sealed_model` record
  or task data class (`src/ape/tasks/base.py:109` hashes `model_dump` with defaults, so one added
  field moves every task's `global_index` even where it is unset, and every resume misses),
  `DESIGNS` keys (they prefix `task_id`), `*_VERSION` constants, and the serializer. Three objects
  carry a knob and they differ: a `dataset` field reaches the plan through `evaluation_settings`,
  written only when set and not resumable; a `task_config` key reaches `scaffold_config_sha256`,
  which *is* resumable, so a knob changed there is silently resumed onto the old results; a
  task-data field reaches `global_index`. A knob the model sees or the submission enforces goes on
  task data, declared with `knob()` (`ape.tasks.base`, 2026-10-06): None until a run sets it, and
  left out of `global_index` until then, so the tasks that do not use it keep their identity and
  the ones that do fork. Never on `task_config`. `test_pr_review_v5_task_data_knobs.py` refuses a
  new review data field that is not a knob, and an old one that becomes one.
- **Concern vocabulary:** arms say `documentation`, gold says `docs`; both spellings are hashed into
  sealed artifacts. Bridge through `CONCERN_ALIASES` (`src/mathlib_review/analysis/benches.py`), never rename. This one-word
  mismatch made the docs arm unmeasurable for its whole life.
- **Judge versions never join or resume into each other** — `judge_version` is in the cache key and
  the record hash. Active rubric v9 (`judge/protocol.py::JUDGE_VERSION`); v7.1 sits in `legacy_pipeline` for provenance only, and history
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
  held. Adding an arm is two edits; adding a *tool* is three -- its registrar in `_REGISTRARS`,
  its name in `schema/review.py::CONTEXT_TOOLS` (the trace Literal and the toolbox list derive
  from it, 2026-10-06), and a grant in `ARM_DEFINITIONS` or `solo_context_tools`. A name outside
  the vocabulary is now refused wherever a grant is built, and at registration, not dropped.
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
- **The dev set is one reviewer's review of four PRs, so check that a dev ask recurs before writing
  it into anything a model sees (2026-09-24).** One reviewer wrote 30 of the dev set's 52 round-1
  comments, on 33066, 33098, 33145 and 33337. 33098 alone is 14 of the 43 dev gold obligations.
  Naming is 29% of dev asks, against 9.7% of the 1,833 asks on the 1,000-PR validation set, where
  the busiest of 80 reviewers wrote 8.5% (the 60-PR set's 3% was a small sample). The prompts carry that fit:
  - the naming example is 33337's counts;
  - `(α := αᵒᵈ)` is 33145's suggestion, verbatim;
  - `family_design`'s five bullets are five dev obligations.

  And the asks the dev set lacked have no owner: on 1,000 validation PRs, API design (122),
  PR-level asks (111) and attribute registration (62) are most of the 21% that no arm's remit
  covers. Before cutting a remit, example or threshold to a dev
  obligation, count that ask's family in the validation set's round-1 comments. The families, and
  both readers' labels, are in `results/pr_review_v5/adjudications/arm-coverage-val-2025-06-2026-03-v1/`.
  The audit is `docs/research/pipeline-overfit-2026-09.md`.
- **The contamination gate matches gold verbatim, so a paraphrase of dev gold passes it.** It
  misses:
  - namespaced forms (`Subgroup.closure_pow_le`), altered names (`coe_starProjection_eq_x`),
    statistics (`21 … 7`) and camelCase words;
  - `to_fun`, which is on its allow-list;
  - everything it does not sweep: tool descriptions, served pydantic docstrings, `LEAD_USER`, the
    generalist prompt, context slices.

  A clean gate is not evidence that a prompt is dev-free.
- **A v5 run made before 2026-10-06 can carry two kinds of false claim (found 2026-09-24).**
  - `declaration_search` reported a declaration as existing when only its last name component did
    (fixed `5e215ffe`, 2026-09-30). 12 of 74 findings in the family-division run were false "already
    exists" claims, 9 published; V3 had at least 5.
  - Verification artifacts joined on `(work_unit_id, candidate_ordinal)`, so an edit-less claim
    could be published on another arm's compile (fixed `e4341209`, 2026-10-06). 7 in that run, 5 in
    V3. The old rows carry no invocation id, so those runs cannot be re-joined.
  - So read an older run's "already exists" claims, and its `verified_compile` count, with that in
    mind. A "moved declaration" story for such a claim was told once and was wrong: check base with
    `git show <base>:<path>` first.
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
- **A forced-choice label vocabulary hides the mechanism it was built to count (2026-09-23).**
  `SilenceLabel` admits one label per cell, and the rubric handed to the reader ranked
  `decision_noise` above `advisory_suppressed` whenever any replay sample filed. So the two 33337
  `naming` cells that motivated the advisory-licensing condition -- the arm writing "emerging
  (`toLinearMap_` 21 vs `coe_` 7) ... so I'm not requesting a rename" while 2 of 5 replays filed
  the gold rename -- were recorded as `decision_noise` and `evidence_gap`, and the condition was
  then killed by a `>= 3 advisory_suppressed` gate that its own examples could not reach. An arm
  that files 2 times in 5 at an `emerging` verdict is advisory-suppressed *and* unstable; the
  labels are not alternatives. **The reader said so in its note** -- "the quote is a textbook
  `advisory_suppressed` tell" -- and the note was in the store while the counts were what got
  acted on. Two rules, both cheap: a label vocabulary for *mechanisms* must be non-exclusive,
  because mechanisms co-occur and a taxonomy that forces a winner reports the tiebreak rule
  rather than the system; and **read the notes before the counts**, since a `by_label` histogram
  cannot say that its second choice was nearly as strong. Same family as the closed-vocabulary
  trap above, one level up: there a correct registration was dropped by a second list, here a
  correct observation was dropped by a ranking.
- **The elaborated corpus names 33337's coercion `coe`, not `toLinearMap` (2026-09-24).** The
  `toLinearMap_` 21 vs `coe_` 7 figure that the naming prompt, the arm and several records cite was
  bucketed by the *surface* projection `.toLinearMap`; people who write the projection name it
  `toLinearMap`. Read from the elaborated statements (`retrieval/statement_index.py`, on tag
  `parked/naming-from-statement`), when
  `ContinuousLinearMap.toLinearMap` heads a left-hand side the corpus names it `coe` 37 times and
  `toLinearMap` 3 (aligned over all positions, 62 of 72). The gold ask is a judgement against the
  corpus, and its "to reflect that the statement is about `.toLinearMap`" is the gold writer's inference.
  Do not cite 21:7 as corpus support for it.
- **`naming_statement` rows fire on most names, renamed or not (2026-09-24; the tool is on tag
  `parked/naming-from-statement`).** On the rename testbed,
  unthresholded they flag 100% of never-renamed controls while proposing the right word for 41.5% of
  renames; a variant that grants the tool adds stable off-gold advisory renames (2 per attempt on
  33421). A row is evidence for *what* a rename would be, not a reason to ask for one.
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
- **A probe reviewer must not have been trained on the PRs it reviews (2026-09-25).** The
  facet-brief probes (`docs/research/facet-brief-probe-2026-09.md`) ran Claude reviewers, knowledge
  cutoff June 2026, on PRs from 2025-06..2026-03, every one merged before that cutoff. A reviewer
  can then recall the merged code or the maintainers' discussion. So reach is not reviewing, and
  Claude-vs-pipeline numbers are not comparable. The between-brief comparisons survive only because
  both arms share the same memory. **Before any probe, compare the reviewer model's cutoff with the
  PR window**, and pick one of three:
  - PRs created after the cutoff;
  - the pipeline's own model through `cli run` (the solo scaffold holds the same tools);
  - an explicit statement that only between-brief comparisons are being read.

  Blind matchers are not affected: they judge text they are shown.

  *Measured 2026-09-29* (`results/pr_review_v5/probes/postcutoff-2026-09-29/`): on 10 PRs created
  after the cutoff, the same Claude reviewer reached asks at 79-107% of its in-window rate. So
  in-window reach is not mainly recall, at probe altitude and with a different ask mix. The
  post-cutoff set `probe-2026-07-08-v1` (config `configs/pr_review_v5_probe_2026_07_08_v1.yaml`) has
  reviewed workspaces built, and is the first option above, ready to use.
- **Restore a built base only after its build process has exited (2026-09-29).** A restore started
  as the build was finishing its snapshot (under a second after `build_completed_at`) failed with
  "Restore file failed" and left the state `failed`, "need to rebuild". Recovery was a rebuild of that
  one commit, then a restore. A restore run on commits whose builds are done is safe beside builds of
  other commits. So is `prebuild --reviewed` on a config restricted with `dataset.pr_numbers`, and an
  absolute `extends:` path lets that config live in scratch.
- **Probe subagents share the session scratchpad; keep what a reviewer must not see out of it
  (2026-09-29).** In the construction demonstration, reviewers wrote snippet files into the session
  scratchpad, two sessions collided on a folder name, and the round-1 feedback file with the
  maintainers' asks sat in the same scratchpad until the first collision was reported. So:
  - generate asks, gold or unblinded indices only after every reviewer has finished;
  - tell every reviewer to keep temporary files in a `tmp/` inside its own packet directory;
  - log every tool call in the wrapper, not by the reviewer;
  - audit the transcripts (tool calls and tool results) before matching;
  - redact condition cues, such as a K reviewer's construction ids, from matcher inputs.

  The probe's `audit_transcripts.py` flags reads outside the packet, foreign scratch files, the
  study's scratch, agent transcripts and the web. It was checked against planted violations.
- **While probe sessions run, commit packets by file, never the probe directory (2026-09-29).**
  Sessions write `calls.jsonl`, `tmp/` and then `findings.json` into their packets as they work, so
  `git add <probe_dir>` mid-run committed 21 half-written session files with the validation
  packets (amended out before any push). Commit a session's outputs only after its transcript is
  audited. The harness for all of this is `analysis/probes.py` and `cli probe`.

- **Count what every tool call came back with before reading a run's tool use as the model's
  (2026-10-01).** The command is `cli report tools --run <run>` (2026-10-06; either scaffold,
  every attempt, a lead's nested arms included). Over the three Opus subscription runs on the dev
  set (47 sessions), read then with the probe script it replaced
  (`results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py`): hover, goto and goal
  were refused on 7 of 9 calls (the `Mathlib/...` spelling, which every other tool takes),
  `declaration_search` refused 15 of 249 real names as "not identifier-shaped", 7
  `lean_verify_edit` calls never ran because the model wrote `"replacement": }` to delete a span,
  `proof_profile` had no table, and `lean_verify` was used 55 times in 84 as a `#check`/`example`
  probe while described as "verify ... correctness" with a `file_path`. None of that was visible in
  a tool-call histogram, and a reviewer's "investigation" numbers counted every refused call. The
  interface rule the hygiene layer settled on: a reviewed file is `Mathlib/.../X.lean` for every
  tool; a tool that asks for `target/...` or `scratch/...` is the trap; one tool per question
  (`lean_verify` compiles a snippet against the library, `lean_verify_edit` compiles the reviewed
  file with an edit); a refusal says which spellings exist; and a tool a run cannot answer with
  is out of the grant, not in the prompt.
- **A convention's one-line sentence, and a detector built on it, misstate the convention; check a
  statement against what maintainers fixed before measuring with it (2026-10-16).** The "maintainers raise a
  convention at 5% of the places it applies" figure did not survive being taken apart
  (`results/pr_review_v5/probes/enforcement-at-departures-2026-10-16/`). For namespace placement the
  detector proposed the conclusion's namespace while the convention as held puts a lemma in its main
  hypothesis's namespace first: 97% of the unasked "departures" were not departures. For primed names two
  written versions of the convention, each from the maintainers' words, both failed to reproduce the primes
  maintainers had fixed. Only dot notation measured as stated (real departures, merged unasked, fixed only
  when a maintainer asks). Before any number about where a convention "applies", write the convention with
  its precedence and the line maintainers draw, and calibrate it on departures they actually fixed, held
  out from the derivation; a statement that fails that check measures us, not them.
