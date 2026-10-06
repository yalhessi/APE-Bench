# Keeping exploration small: what imploded, what a redesign would be, and what survives an adversarial review (2026-10-06)

**Status** — design write-up, not a plan. Nothing in it is built. The measurements are from
`develop` at `cb652ce2` (952 non-merge commits since the 2026-09-08 collapse), taken read-only by
three surveys (git churn, architecture, tests and freeze constraints). A first draft proposed a
five-registry redesign; three adversarial reviews (against the record, against the mechanics,
against the next five pieces of research work) rejected most of it on evidence, and §3 keeps that
record. The design in §4 is what survived. The request was the user's (2026-10-06): the codebase
has imploded again, agents change large parts of it at a time, exploration must stay open, and
the typical explorations should each be one small change with the rest of the tree untouched.

## 0. The answer in one paragraph

Not a rewrite. The layer the September plan fixed -- orchestration, accounting, strict config,
the schema split, the stage ledger -- holds and is quiet. Thread width now has two sources. The
first is a few missing seams: a fact supplied to the reviewer is wired through four vocabulary
copies and a 892-line tool module; a knob becomes a field and so forks every run's identity; a
design's run data lives in the 2,216-line run driver; and the probe harness grows a subcommand per
brief shape. The second is the legitimate fixing of shared machinery found by reading runs, which
is half the files of every wide thread, which no architecture removes, and which only cheap
run-reading and commit discipline make smaller. The design that survives review is three seams
(producers, design-owned run data, the stage as the probe unit), one identity rule, and a set of
guards, each introduced on the next piece of real work with a threshold stated before it starts.

## 1. What imploded, measured

### 1.1 Commits are small; threads are wide

- Commits touching `src/` since 2026-09-08: 302. Files per commit over `src + tests + configs`:
  median 3, p75 4, p90 7. The September rule of small commits holds.
- Threads are not small. Over 17 topic branches the median thread touches **10 `src/` files and
  about 8 test files**, edits `.claude/rules/mathlib-review.md` (11 of 17) and leaves 10^4 to
  10^5 lines under `results/`.
- 57 of the 302 code commits touch `review/runner.py` or `review/cli.py`.

### 1.2 The hubs

| file | lines | commits since 09-08 | distinct co-change partners |
|---|---:|---:|---:|
| `src/mathlib_review/review/runner.py` | 2,216 | 34 | 38 |
| `src/mathlib_review/review/cli.py` | 771 | 29 | 23 |
| `src/mathlib_review/analysis/probes.py` | 1,262 | 21 | |
| `src/ape/tasks/lean_tasks/formal_math/review/base.py` | 1,252 | 19 | |
| `src/mathlib_review/analysis/report.py` | 1,511 | 18 | 17 |
| `.../review/context_tools.py` | 892 | 17 | 18 |
| `.../review/candidates.py` | 941 | 14 | 17 |

`runner.py` has 52 functions and 18 `routing_mode ==` sites; it builds and seals an agenda for
every mode, solo included, and `finalize` and `reconcile` consume arm vocabulary, so the kernel
is agenda-shaped. A knob added for one mode (`target_verdicts`) appears in 11 source files. The
CLI has 11 commands, `report` 13 subcommands and `probe` 12, each hand-wired; every new brief
shape in the probe harness has been `probes.py` + `cli.py` + `test_probes.py`.

### 1.3 Two sources of width

Read against the commit bodies, a wide thread's files split in half:

- **Seams.** `arm-division`'s seven arm files; `target_verdicts` reaching 11 files; the
  `naming_statement` tool needing `schema/review.py`, `toolbox.py`, the consistency test and a
  procedure variant reachable only from `bench`; D1 and D2 needing `_ledger_rows`,
  `stage_rows_for` and `_design_preflight` in `runner.py`.
- **Shared machinery found by reading runs.** `arm-division`'s other seven `src/` files
  (`eec8d3a5` qualified-name match, `814ed69d` a compile warrants its candidate, `db07c835` the
  half-edit, `3e6e240b` tool-text contamination); all nine of `hygiene-layer`'s; five fix commits
  on `review-designs` reaching `ape/toolkits/execute/lean/tools.py`. `docs/dead-ends.md` says it
  of the family division: "most of the wrong output on shared machinery, not the division."

The widest thread of all, `conventions-nature` (95 commits, 734 files), is 721 files under
`results/` and 2 under `src/`: 288 `.jsonl`, 280 `.json`, 75 `.md`, about 50 of code. It never
crossed a hub. Its width is the record, and the record is meant to be wide.

### 1.4 The same concept, several times

- The context-tool vocabulary exists in four places (`schema/review.py:70`, `review/toolbox.py:53`,
  the `ContextCall.tool` Literal, already missing `proof_profile`, and `arm.py:_tool_summary`); two
  paths drop an unknown name silently (`arms.py:_grant_for`, `register_context_tools`), the rules
  file's "three times now". The concern vocabulary exists in six.
- Six modules each describe themselves as producing the system's output; six run readers in `src/`
  plus about 40 probe scripts glob `.ape/runs` by hand; 19 scripts under `results/` (outside
  `tmp/`) and 3 modules in `src/` read JSONL with `splitlines`, which the rules file forbids.
- About fifteen two-way package cycles. `legacy_pipeline` (28 modules) is imported by seven
  modules outside it, two at top level in production (`review/conditions.py:29`,
  `judge/r0_equivalence.py:32`), and `release/change_graph.py:865` sits in the byte-for-byte
  re-render path.
- Three identities carry a knob today, and they behave differently: a `dataset` field reaches the
  plan through `evaluation_settings` (written only when set, not resumable); a `task_config` key
  reaches `scaffold_config_sha256` (resumable, so a knob changed there is silently resumed onto the
  old results); a task-data field reaches `global_index` (`src/ape/tasks/base.py:109` hashes
  `model_dump` with defaults, so adding one field moves every task's identity even where unset).

### 1.5 Where new code lands

Since 2026-09-08: 392 `.py` files added, **1 deleted**.
- `results/`: 249 files -- 137 agents' scratch under `tmp/`, **112 researcher scripts (9,947
  lines) in 26 of 31 probe directories, 84 of them importing nothing from `src/`**. Three
  `unblind.py`; the spine (`status_of` / `hits_of` / `audit_of`) rewritten in `consistency.py`,
  `reading.py` and `read_critic.py`; `read_critic.py` needs two `sys.path.insert` to reach `src/`.
- `tests/`: 105 files, +25,377 lines, against `src/` +30,778. The suite is 216 files and 2,391
  tests; about twenty pin the *shape* of the tree -- paths, basenames, exact counts
  (`schema.__all__ == 133`), a private-import ceiling of 3 with 3 used -- and 50 configs are named
  by filename in tests.
- `configs/`: 106 added, 2 deleted; 166 on disk, 97 `pr_review_v5_*`, `extends:` chains ten deep,
  the contract spelled in filename suffixes (`_G`, `_Gr`, `_Grc`, `_contract2`) because the
  contract is not a model; 26 v2/v4 configs name a run already spent.
- Prompts as data under `results/`: the frozen baseline's brief is
  `results/pr_review_v5/probes/contract-2026-10-01/brief_G2.md`; 14 configs point
  `system_prompt_file` or `context_file` there; `probes.py` hard-codes rubric paths there; the solo
  task imports `analysis.probes` (`solo.py:408`). Prompt text is an input and runs backwards;
  `context_file` data (`model_context.jsonl`) is probe-produced data and belongs where it is.

### 1.6 Why the September remedy did not prevent it

The September plan fixed the layer below the explorations; `ape/orchestration` has six co-changes
with the review tasks in a month. The one seam it built in the spirit of this document, `DESIGNS`
(one module, one registry line, one config), is the clean extension point in the tree: D1 and D2
went through it at four and three source files. What it declined to build (`ArmRuntime`, "a hook
layer with exactly one implementation") turned out not to be where the width came from -- the arm
seam that exists is tested by `test_a_new_arm_needs_nothing_beyond_those_two_edits` and passes.
What it did not foresee is facts delivered as packet sections, probes and readings as the main
line of work, and the identity cost of a knob.

## 2. The kinds of exploration

Every thread since the collapse is one of these, or a framework fix:

| kind | what varies | threads |
|---|---|---|
| **design** | how a model, or several, read one PR and decide; owns its submission schema | solo v1/v2, `structured`, `structured_critic`, lead / fanout / rules, the family division, `pr_level`; a decisive detector that files directly is a design with no model |
| **producer** | a fact about the PR, delivered as a tool the reviewer may call or a section it always sees; measured alone before any reviewer sees it | `naming_norm`, `naming_statement`, `declaration_search`, the hygiene layer's outputs, the conventions section at four levels, the static pass, the closer battery; planned: convention detectors, the try-it battery, analogue retrieval, the area census as a section |
| **record** | labels, census asks and negatives, seals, adjudications; gated by PR-disjointness from every evaluation set, not by a timestamp | the conventions census, reader codebooks, the blind seals, `cli adjudicate` |
| **reading** | a two-phase protocol: prepare folders, wait for sessions or labels, read a table | judge v9, the blind matchers, `report union`, the consistency spine, `report buckets`, stage H's `score` |
| **set** | which PRs, which asks, which workspaces, which labels | dev 12/15, validation small12, post-cutoff 10, census 973, the sealed 60s; `configs/probe_sets/` |
| framework | execution, routes, workspaces | ELM Responses, the subscription route, local vLLM, reviewed workspaces, resume, token limits, the persistent checker (planned) |

A **stage** is one of these run over the artifacts of the previous one (`StageInput`, `cli
pipeline`, D2's `--of`: all built). A probe is a chain of stages with a reading rule stated first.
Members of these kinds may be sessions, not only functions: four of stage H's five decision designs
are Claude sessions over folders.

## 3. The first draft, and what the review did to it

The draft proposed five discovered registries (`designs/`, `producers/`, `contracts/`,
`readings/`, `sets/`) under one-direction layering, cells as YAML, two executors sharing a
byte-identical packet, the run driver and CLI dissolved, tests de-pinned, deletion in the same
commit. Kept here so the next session does not re-derive it.

| proposal | verdict | the evidence |
|---|---|---|
| five registries under `schema, io ← kernel ← registries ← cli`, never importing each other | **rejected** | a design is a `BaseLeanTask` subclass and must stay in the task package (`dead-ends.md`: "do not retry" moving the base out); `structured.py` imports `base`, `candidates`, `solo` and calls `lookup_declaration` / `naming_census` at submission -- a design → producer import by construction. Downward imports (design → producer) are the normal case |
| registration by discovery | **rejected** | the explicit line was chosen deliberately on 2026-10-02 (`b073a564`) as one of three edits; the `code_references` lesson is a *granted* name with no registration, which `test_every_granted_tool_survives_the_grant` already checks in the right direction; a conformance test that fails on an unreferenced member makes work in progress red |
| lead / fanout / rules collapsed into one `arms` design | **rejected** | the kernel builds an agenda for every mode; `CoordinationPolicy` and `SynthesisPolicy` already are the routing policy, sealed separately; 15-30 commits and 21 test files for a path no planned work runs; the in-flight fanout rep and `smoke4_rules.yaml` use the modes |
| a `contracts/` registry, one directory per contract | **rejected** | a design owns its submission schema (D1's ledger is a contract, changed inside `structured.py` by `c3f24639`); the cross-design knobs compose orthogonally (`dead-ends.md`: "the contract stays as opt-in knobs"), so directories enumerate a cross-product; this is the registry where "a hook layer with one implementation" still bites |
| a free `params` mapping for knobs | **rejected, the aim kept** | reopens the unvalidated half the September plan closed (`extra="forbid"` recursively); the only-when-set convention already exists (`runner.py:1095`, `ebb1378e`, `c25cd958`); see §4.3 |
| readings as a discovered registry, `read(runs, asks) -> table` | **rejected** | half the readings are prepare-then-read protocols waiting on external labels (`seal_labels`, `match_inputs`, `judge_folders`, `unblind`); producers are measured alone with no run (`standard_set_alone.py`); what three scripts duplicate is one spine function, not a registry; pre-registration code belongs beside its result |
| cells as YAML only | **amended** | stage H is 5 designs × 2 seeded halves, a generator; a `cells.py` may yield cells |
| two executors, byte-identical packets | **amended** | unattainable: the scaffold's first message carries per-attempt paths and MCP tool names; the probe's session reads `brief.md` / `model.md` from disk and logs through `ptool`. Content-equal already exists (`write_swap_packets`, `import_probe_session`); the subscription route *is* a scaffold route, and only reader and matcher sessions are hand-launched. The honest build is a `packet_on_disk` scaffold mode with `ptool` emitting `ContextCall` rows, 3-5 commits |
| `plan \| run \| read \| bench \| lint`, readings not hand-wired | **rejected** | `read` collapses `judge` (spends) and `report` (free) against the recorded lesson that a decorative `--execute` teaches the flag is decorative (`test_pr_review_v5_cli.py:44-55`); drops `pipeline`, `replay`, `adjudicate`, `trajectory` without saying where they go |
| no code in `results/` | **rejected** | pushes scripts into `scratch/` (137 of 249 already are `tmp/`); the livable rule is narrower (§4.1) |
| "deleted in the commit that supersedes it" | **amended** | every comparison here runs old and new under one seal (the solo baseline is pinned *because* D1 and D2 are read against it); deletion happens in the commit that records the comparison's reading, at a run boundary |
| a hook that warns when one commit touches a kernel file and a registry file | **amended** | as drawn it fires on every legitimate shared-machinery fix (§1.3); inverted, it is the one behavioural lever (§4.1) |
| per-instance tests replaced by conformance | **rejected as a programme** | the ten-hash table is differential ("nine of ten unchanged is the check that this touched one arm and not the registry's shape") and carries each deliberate move's reason inline; `test_every_granted_tool_survives_the_grant` records the $1.11 rep14 lesson; `test_family_design_has_no_identifier_lookup`, `test_every_arm_keeps_lean_verify_edit`, `test_the_convention_arms_keep_the_review_corpus` record measurements. Pure pins exist and go one by one from an inventory (§4.7) |
| deleting legacy as part of the collapse | **amended** | `dead-ends.md`: "the generations had to be consolidated, not pruned"; seven importers, not three; `change_graph.py:865` is in the re-render path. Hygiene after the seams, with the importer list in the plan, not the route to anything |
| the "under the design" column of the draft's past-threads table | **corrected** | it reached "7 files" by omitting the shared-machinery half; §5 is the honest version |

## 4. The design that survives

### 4.1 Guards: make the small change the path of least resistance

The project's own hooks are what has held so far (the pipe-in-commit refusal, the tree-switch
refusal, the session line). Three more, all mechanical:

- **The framework-fix hook.** A commit that edits an *exploration* file (a design, a producer, a
  prompt, a config or cell, anything under `results/`) and also a *kernel* file (`runner.py`,
  `cli.py`, `base.py`, `candidates.py`, `schema/*`, `ape/orchestration/*`, `ape/toolkits/*`) is
  warned: "a framework fix in its own commit, or a missing seam". It does not refuse -- the fix is
  usually right -- it makes the split the default and leaves the kernel's history readable.
- **The run-reader lint.** A script under `results/` that globs `.ape/runs` or `attempts/`, or
  reads JSONL with `splitlines`, fails a test; the fix is the one import of the spine (§4.2). The
  rules file already forbids the second; the test makes it bite where it happens.
- **The input lint.** No config or cell names a *prompt* input under `results/`
  (`system_prompt_file`, `context_file` pointing at a brief). Probe-produced *data* inputs
  (`model_context.jsonl`) stay where they are, hashed; data never moves, only code and prompt text.

And one rule of record: the identity map (§4.3) goes into `.claude/rules/mathlib-review.md`
whatever else is built.

### 4.2 Reading runs cheaply

The half of thread width that is machinery fixes is found by reading runs, and today every probe
re-writes the reader. One spine in `analysis/` -- `status_of`, `hits_of`, `audit_of` over
`TaskStorage` and `StageInput`, the three functions `consistency.py`, `reading.py` and
`read_critic.py` each contain -- and one reading, *tool outcomes*: what every tool call in a run
returned, by tool and by outcome (`claude-models-2026-10-01/tool_outcomes.py` is the prototype; the
hygiene layer's nine fixes were each found this way by hand). Both are additions under `analysis/`,
touch no hub, and are what the run-reader lint points at.

### 4.3 Identity: fixed shapes, omitted when unset, one fork at a boundary

The map of what moves a hash is now known and goes to the rules file: renaming a class or moving a
module moves nothing; a task type string, prompt text, the shape of a `sealed_model` record, the
fields of a task data class, the `DESIGNS` keys, `*_VERSION` constants and the serializer are
identity. The rule for knobs: **a knob is a typed optional field, omitted when unset, on the object
whose identity should fork when it is set** -- task data for anything the model sees or the
submission enforces (so the orchestrator cache forks), the plan for evaluation settings. Never
`task_config`, whose digest is resumable, so a knob changed there is silently resumed onto the old
results. The framework half is one change in `generate_global_index`. *As built (2026-10-06,
§11):* not "hash with unset fields excluded", which would have moved every existing identity once
and needed a run boundary, but a marker: a field declared with `knob()` is left out of the hash
while it is None, and no existing field carries it, so nothing on disk moves and no boundary is
needed. A guard refuses a new review data field that is not a knob, and an old one that becomes
one. The run-name rule keeps its human-readable half and loses its job as the only thing standing
between a knob and a wrong resume.

### 4.4 Producers: the seam the next work needs

`_REGISTRARS` in `context_tools.py` becomes the one registry and the one vocabulary:
`CONTEXT_TOOLS`, `toolbox.CONTEXT_TOOLS` and the `ContextCall.tool` Literal are derived from it
(a validator, shape-neutral: `str` stays `str`, and no sealed record hashes a schema); an unknown
name is refused, never dropped; every grant is explicit and sorted, the generalist's included, so
that adding a producer file does not re-seal the generalist's `tools_sha256` and refuse every
lead / fanout resume. A producer declares `facts(episode, as_of, scope)` and a delivery: `tool`
(an MCP registration, as today) or `section` (through the existing per-PR `context_file` /
`model_context` channel, which is how the conventions section and `probes.conventions_section`
already reach the solo task). Promoting the area census from tool to section is then a config
line. A producer carries its own bench, `measure(set, truth)`: hits at gold sites, emission on the
control PRs, before any reviewer reads it -- the protocol of `static-pass-2026-10-01`. A detector
decisive enough to file directly is not a delivery mode; it is a design with no model, and the
warrant it files under comes from `conditions.deterministic_findings` as the v4 arm's did.

What this changes: the `naming_statement` thread's `schema/review.py`, `toolbox.py` and
consistency-test edits go; the four planned producers (detectors, try-it battery, analogue stage,
area census as a section) land as one module each plus a bench fixture; the procedure-variant
machinery reachable only from `bench` is retired once grants are config.

### 4.5 Designs own their run data

`DESIGNS` stays where it is, with its explicit line. *Amended 2026-10-06, on reading the code
(§11):* the move proposed here -- `_ledger_rows`, `stage_rows_for` and `_design_preflight` onto the
design class -- is dropped. Each already dispatches through the design's own hooks
(`reads_stage`, `design_payload`, `describe_design_payload`) and works for any design; the
`runner.py` edits in D1's and D2's commits built that generic chain once, and moving it would
relocate code without making the next design cheaper. What remains is below.
A design declares its stages, and each stage its route and budget, so a critic on another model is
one design's declaration and not a second run config. The target is checkable: a new per-PR design
is its module, its registry line and its config, and `runner.py` is not in the diff.

### 4.6 The stage as the probe unit

The probe harness's three halves separate: its *sets* are `configs/probe_sets/` already; its
*packets, seals and matching* are kernel (a `packet_on_disk` scaffold mode so a hand-launched
reader session and an orchestrated run read content-equal packets and log `ContextCall` rows; the
seal as one kernel function); its *readings* are prepare-then-read pairs beside the results they
pre-register. A probe is then a chain of stages over `cli pipeline`, written as cells (YAML, or a
`cells.py` that yields them), each stage naming what it reads through `StageInput`. The *record*
kind (§2) gets its gate written once -- PR-disjointness from every evaluation set, checked at plan
time -- the way the temporal gate was written once for retrieval. Stage H under this is a record,
a pinpointer design, five decider units, a reading and a `cells.py`; its seals are not run by hand
and its three `unblind.py` siblings are one. Its width in `results/` does not change, and should not.

### 4.7 Hygiene, measured, after the seams

- **Legacy.** Cut the seven external imports of `legacy_pipeline` by moving the functions they
  need (`change_graph.py:865` stays in the re-render path and is tested byte for byte), then tag
  and delete what is unreachable: 24 of 28 `legacy_pipeline` modules, 11 of 12 `opportunities`,
  `datasets/legacy`, `datasets/pr_review`, with their 43 test files. `datasets/pr_review_v2` keeps
  its directory and its roster, hashed by nine manifests, and may lose its code with 17 tests --
  a decision for the user, since it closes the v2 selector line by fiat (the tag keeps it).
- **Configs.** The 26 v2/v4 configs naming a spent run go first; then whatever a cell expresses.
- **Pins.** The inventory is §10. Three tests are pure pins (the exact class count, the
  basename allow-list, the design-config filename prefix) and go in the commit that would
  otherwise have had to edit them; the rest record a lesson, are ratchets, or are differential,
  and stay with their paths updated.

## 5. Would it have changed the past threads? (honest)

| thread | as it was | under §4 | what stays |
|---|---|---|---|
| family-division arms (`arm-division`) | 14 `src/` files: 7 arm files, 7 shared-machinery fixes; 6 test files; 1 config | 7 arm files + 1 config; the 7 fixes as framework-fix commits found by the tool-outcomes reading; `render_focused.py` and `agenda.py` for the PR-grain unit (a routing change, kernel either way); 2 tests (a new refusal, the contamination gate on tool text) | the prompts (280 lines) and the fixes; what goes is the mixing, not the work |
| the submission contract (`arms-speak`, `target_verdicts`) | 11 `src/`, 8 tests, 0 configs; the knob now in 11 files | typed optional knobs are how it ended; §4.3 removes the run-name dance and the identity fork of every later knob; the four read sites remain | 4 sites: render, two submit tools, finalize |
| `naming_statement` (`naming-from-statement`) | 8 `src/` (one `.lean`), 5 tests, a procedure variant reachable from `bench` only | 4 code units (`statement_export.lean`, `statement_index.py`, `naming_parts.py` at 990 lines, the registrar) + 1 bench fixture; the `schema/review.py`, `toolbox.py` and consistency-test edits go; the grant is a config line | the 1,500 lines that are the idea |
| D1 / D2 (`review-designs`) | 4 + 3 `src/` + a 5-file registry commit + 5 fix commits touching `base.py`, `runner.py`, `solo.py`, `lean/tools.py` | the module, the line and the config each; the `runner.py` edits go to the design class; the end-of-file linter fix stays a framework fix | the designs' 1,300 lines; the registry commit, done once |
| conventions ceiling L-M (`conventions-nature`) | 95 commits, 734 files, 721 under `results/`; 17 scripts (12 import nothing from `src/`); seals run by hand | 721 files under `results/`, unchanged; the 17 scripts become a record, a design, five deciders, a reading and a `cells.py`; one seal function; one spine | the width, which is the record |
| hygiene layer | 9 `src/` files, 7 commits, all harness fixes | unchanged, and labelled | everything |
| ELM provider | 46 `src/` files (9 `llm_clients`, 12 `scaffolds`), 14 configs | unchanged: a route is framework work; noted as the next seam if a fourth route comes | everything |

The honest reading: the design removes the seam half of the width and labels the other half. It
does not shrink the record, the prompts or the ideas, and it should not.

## 6. The planned work under it

| planned (`docs/plans/2026-10-03-after-structure.md`, `2026-10-06-convention-decision-designs.md`, todos) | kind | footprint under §4 |
|---|---|---|
| convention detectors as packet sections (§2), measured alone first | producers (`section`), one each, with a bench fixture; a decisive one a model-free design | 1 module + 1 fixture each |
| the try-it battery on a persistent checker (§3) | the checker is framework; the battery a producer (`section`) | framework commits + 1 module |
| analogue retrieval (§4), measured on the 43 labelled asks first | a producer (`section`) over a retrieval index; the measurement its bench | 1 module + 1 fixture + the index builder |
| the area census promoted from tool to section | a config line | 0 modules |
| five decision designs over one convention record (stage H) | a record, five decider units, a reading, a `cells.py` | ~8 files, no `cli probe` edit |
| a critic on another model | one design's stage declaration with its own route | 1 edit in the design, 1 config |
| `pr_level` | an arm file plus the PR-grain unit it needs in `agenda.py` / `render_focused.py` | 1 arm file + 1 kernel commit |
| the AI-generated stratum | a set label, already carried | 0 |
| gpt-5.5 `xhigh`; unions across designs | a config; the existing `report union` | 0 |

## 7. Order, thresholds and cost

Each step is a thread in its own worktree, merged at a run boundary; the hub steps wait until the
three branches that touch `runner.py` / `cli.py` (`arms-speak`, `increment0-rebaseline`,
`convening-demo`) are merged or parked. Each step has a threshold measured on the next piece of
real work, and a step that misses it is reported as missed, not widened.

| step | what | threshold, stated first | est. commits | tests touched |
|---|---|---|---:|---|
| 0 | this document; the pin inventory; the identity map into the rules file; cut the task layer's import of a reading (`solo.py:408` → `analysis.probes`). The second edge the review named, `arm.py:34` → `agenda.registry`, is kept: `registry.py` imports only `dataclasses` and `typing` and `agenda/__init__.py` is empty, so it is a downward edge to a data declaration; cutting it mattered only for the rejected move of designs out of the task package | -- | 2-3 | 1-2 |
| 1 | the three guards (§4.1); the spine and the tool-outcomes reading (§4.2) | the next thread's fixes to shared machinery are their own commits, found through the reading rather than a new script | 4-6 | +3 new |
| 2 | identity (§4.3): omitted-when-unset hashing, once, at the declared boundary; the knob rule | the next knob forks no run that does not set it, and resumes refuse a changed one | 2-3 | `test_pr_review_v5_designs.py` (the payload pin moves once), `task_adapter_fields` |
| 3 | producers (§4.4): one registry and vocabulary, explicit sorted grants, `section` delivery, the bench shape | after-structure §2's first detector lands in ≤ 3 `src/` files, 1 fixture, 0 hub edits | 8-12 | ~8 (`context_tools`, `prompt_delivery`, the consistency table's comment, grants) |
| 4 | per-stage route and budget (§4.5), with the critic-on-another-model work. *Amended 2026-10-06:* the move of `_ledger_rows`, `stage_rows_for` and `_design_preflight` is dropped -- they already dispatch through each design's hooks, see §11 | the next design (a critic on another model, or D3) lands with `runner.py` absent from the diff | 2-4 | ~4 |
| 5 | the stage as the probe unit (§4.6): `packet_on_disk`, one seal, the record gate, prepare/read readings, `cells.py` | the next probe needs no new `cli probe` subcommand and no `probes.py` edit | 8-12 | ~8 (`test_probes.py` shrinks) |
| 6 | hygiene (§4.7): legacy by importer list, spent configs, pure pins | the boundary counts go down and nothing frozen moves | 4-6 | −43 legacy, −17 v2 if decided |

About 35-50 commits in all, against the rejected draft's 60-100, and the first two steps need
no hub rewrite. Steps 3-5 pay for themselves on work already planned; if that work is not done,
they are not done either.

## 8. What nothing here touches

The roster at `src/datasets/pr_review_v2/data/mathlib_roster.txt`; the hashed data trees
(`data/pr_review_v2/cache/{bundles,compares}`, `data/pr_review_v4/cache/base_files`,
`inputs/pr_review_v2|v3`, `inputs/pull_requests/{rosters,evaluation}`); `io`'s hashing and both
sealing functions; the `release/*` builders' output and `render_prompts` text; every task type
string, `task_id` format, `DESIGNS` key and `*_VERSION` constant; `JUDGE_VERSION` and the judge
model; every prompt's text, which moves only with its digest checked. The frozen roots
(`inputs/pr_review_v4`, `results/pr_review_v4`, `data/pr_review_v2`) and the four live sessions
in the main tree, which is why every step is a worktree.

## 9. Decisions for the user

*Decided 2026-10-06; the user: "You can decide whatever seems most reasonable."* (1) The v2
package's code stays: beyond the roster nine manifests hash, `retrieval/precedent_index.py` names
`python -m src.datasets.pr_review_v2.corpus` as the way to rebuild the precedent corpus, so the
code is live. (2) No run boundary is needed: step 2 was built so that nothing moves (§4.3).
(3) `packet_on_disk` waits for the next probe that launches reader sessions by hand, and is
measured there. (4) Step 3 was split: the vocabulary and the refusals now; the producer
interface, section delivery and bench with the first convention detector, their first
implementation. The original questions:

1. Whether to delete `datasets/pr_review_v2`'s code, keeping the directory and the roster: it
   closes the v2 selector line by fiat; the tag keeps the code.
2. The run boundary for the one-time identity fork (§4.3): after `pr5_F_fanout_heldout12_v2_rep1`
   and before the next design rep.
3. Whether `packet_on_disk` (§4.6) is worth 3-5 commits now, or waits until the next probe that
   launches reader sessions by hand.
4. Whether steps 3-5 start with the after-structure plan's §2 detector, which is both the first
   planned producer and the threshold for step 3.

## 10. The pin inventory (step 0, 2026-10-06)

The surveys counted about twenty tests that pin the *shape* of the tree, and the reviews asked
which of them record a lesson. Read one docstring at a time, nearly all do: each names the defect
it was written after, usually with the measurement. So the inventory's result is narrower than
§4.7 expected. Almost nothing is deleted; what a step needs is the list of pins it will have to
*update*, and the few pure pins it may drop instead.

**Pure pins: a number or a name with no lesson behind it.** Each goes in the commit that would
otherwise have had to edit it, replaced by the property it stands for.

| test | pins | replace with |
|---|---|---|
| `test_pr_review_v4_schema_split.py::test_every_class_landed_in_exactly_one_module` | exactly 112 classes | the duplicate-class check alone; the count adds nothing to it |
| `test_pr_review_v4_no_duplicate_helpers.py::ALLOWED` | allowed files keyed by *basename*; the `phase9_fixed_orchestration.py` entry is already dead because `legacy_pipeline` is excluded | keys by repo path; the dead entry removed |
| `test_pr_review_v5_designs.py::test_there_is_a_config_per_registered_design_and_each_names_its_design` | a design config's filename starts with the design's name | the config's `dataset.design` field, which the next test already reads |

**Ratchets: counts that may only go down.** Kept. The ceiling inside `mathlib_review` is 3 with 3
used, so a step that splits a subpackage and turns a sibling import into a crossing one either
removes the crossing or raises the ceiling in the same commit with the reason. Its docstring had
gone stale -- it named an import that no longer exists while a different one filled the slot --
and is corrected in the commit that adds this section.

| test | count |
|---|---|
| `test_package_boundaries.py::test_private_imports_inside_mathlib_review_do_not_increase` | ≤ 3 (3 used: `wrapper_composition` ×2, `review.runner._scratch_dirs`) |
| `test_package_boundaries.py::test_private_cross_boundary_imports_do_not_increase` | ≤ 14 in the v2 packages (9 used) |
| `test_pr_review_v5_cli.py::test_no_v5_config_is_longer_than_its_own_deltas_plus_its_reasoning` | ≤ 8 leaves per v5 config |

**Differential or identity pins.** Kept, and the reason each is not a pure pin is written in it.

| test | why it stays |
|---|---|
| `test_pr_review_v5_arm_registry_consistency.py::test_spec_identities_are_unchanged` | nine of ten unchanged is the check that a commit touched one arm and not the registry's shape; each deliberate move carries its reason inline |
| `test_pr_review_v5_designs.py` baseline digests and `test_a_solo_payload_is_what_it_was_before_the_registry_existed` | the hygiene reps and every design comparison read these exact bytes and resume on this identity |
| `test_pr_review_v4_schema_split.py::test_the_facade_still_resolves_every_name` (exactly 133) | exact on purpose, so a record that silently stops being exported fails |
| `test_pr_review_v4_rerender_release.py` | today's renderer reproduces a frozen release's `prompt_sha256` |

**Lessons pinned by path.** Kept; the step that moves the named file updates the path in the same
commit, and `test_the_structural_guards_are_pointed_at_a_directory_that_exists` is the backstop
against a vacuous pass.

| step | tests it will update |
|---|---|
| 3 producers | `test_context_tool_grants_survive.py` (vocabulary and registrar checks become one), `test_package_boundaries.py::test_the_context_tool_grant_has_one_owner`, `test_retrieval_gate.py::test_every_context_tool_records_a_gate` (regexes over `context_tools.py`'s text), `test_prompt_contamination.py::MODEL_TEXT_MODULES` (any new prompt or brief location), `test_pr_review_v5_cli.py::test_nothing_asks_for_a_tool_that_cannot_register` |
| 4 design-owned run data | `test_pr_review_v5_designs.py` (ledger rows, stage rows), `test_pr_review_v5_lead.py` (one `TaskOrchestrator(` in `runner.run`), `test_config_strictness.py::test_load_run_has_one_implementation` (the module trio) |
| 5 the stage as the probe unit | `test_probes.py` |
| 6 hygiene | `test_pr_review_v4_no_prior_generation.py` and `test_pr_review_v4_no_duplicate_helpers.py` (the `legacy_pipeline` exclusion), `test_package_boundaries.py` (generation paths, if v2's code goes), `test_subtask_primitive.py::test_every_nested_call_site_uses_the_shared_convention` and `test_subtask_isolation.py::test_the_workspace_hangs_off_the_attempt_path` (named source files) |

The record this leaves: the tests are not what made threads wide. A thread edits them because it
moves the thing they guard, and the docstrings say why each guard exists. §4.7's "pure pins go"
is three tests, not twenty.

## 11. Implementation record

On branch `codebase-redesign` (worktree `.claude/worktrees/codebase-redesign`), each commit with
the suite green and `verify_frozen verify` ok. Not merged into `develop`: four sessions are
working in the main checkout, and a fast-forward there rewrites files under them, as the
2026-10-06 consolidation also found; it waits for that checkout to be idle.

| step | status | commits |
|---|---|---|
| 0 the identity map in the rules file | built | `fd2a6dfe` (on `develop`) |
| 0 the task layer imports no reading | built: the unlabelled label pair moved to `schema/findings.py`; a boundary test pins it, checked to bite on `develop`'s `solo.py` | `a0cf0110` |
| 0 `arm.py` → `agenda.registry` | not done, on purpose: `registry.py` imports only `dataclasses` and `typing`, a downward edge to a data declaration | -- |
| 0 the pin inventory | built: §10; three pure pins, the rest record a lesson; one stale ceiling docstring corrected | `622ac775` |
| 1 the spine | built, as an addition to `report conditions` (which already held mean / union / stable, exclusive sets, control emission and the judge and denominator refusals): `per_obligation` and `never_hit`. Agrees with `consistency.py` on all 23 obligations for the three hygiene reps | `cd341464` |
| 1 tool outcomes | built: `cli report tools --run <run>`, either scaffold, every attempt, nested arms. Same counts as the probe script on all 12 tools of an Opus run; reads a gpt (ape_agent) run the script could not; 333 attempts on `pr5_A_lead_heldout12_rep1` (12 leads, 321 arm sessions) | `01c101ed` |
| 1 the run-reader and input lints | built, as exact allow-lists that only shrink: 23 results scripts, 9 configs; tracked files only | `c3a689ab` |
| 1 the framework-fix note | built: a PostToolUse hook that notes, never refuses, a commit mixing a framework file with an exploration file; registered in `.claude/settings.json`, live once merged | `9005184f` |
| 2 identity, omitted when unset | built as `knob()`: no identity on disk moves (checked on 104,942 recorded arm payloads), so no run boundary; a guard freezes the 63 existing review data fields | `fca5a6cf` |
| 3 producers, first half | built: one vocabulary (the trace Literal and the toolbox list derive from it); a tool outside it refused at the arm grant, a procedure variant's grant, `solo_context_tools` and registration. `cli plan` on the frozen hygiene config seals the same agenda as `develop` (f96210790c7a). A tool is three edits, not four | `e71f32a2` |
| 3 producers, second half | built: the seam (`Fact`, an explicit `PRODUCERS` registry, delivery through the existing per-PR `context_file`, `analysis/producer_bench.py`, `cli producer bench|context`), then the first detector, `dot_notation`, measured alone under a pre-registered rule (`results/pr_review_v5/probes/convention-detectors-2026-10-06/`). Step 3's threshold met: the detector landed in three src files, one new test file, no hub edit. Its measurement: one exact in-sample ask, no control emission, silent out of sample | `b54b29aa`, `6128044d`, `d3df70b9` |
| 4 the design move | dropped (§4.5); per-stage route goes with the critic work | -- |
| 5 the stage as the probe unit | waits for the next probe that launches sessions by hand (§9.3) | -- |
| 6 hygiene | the deletions are dropped on the record: v2's code is live (§9.1); `legacy_pipeline`'s phase scripts are the authoritative producers of frozen releases (PROJECT-STATUS §7: "Do not archive"); `datasets/pr_review` is the published-paper reference (§2: "left as it is"); the spent v2/v4 configs are how frozen results were produced. The three pure pins (§10) go when a step first has to edit them | -- |

Step 1's threshold -- the next thread's shared-machinery fixes land as their own commits, found
through `report tools` rather than a new script -- is read on the next thread, not here. So are
step 2's (the next knob forks no run that does not set it) and step 3's (the first detector lands
in at most three `src/` files, one fixture and no hub edit).
