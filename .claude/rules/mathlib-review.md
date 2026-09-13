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
  capability reaches the task**: read `arm_pool.jsonl`'s `task_data.context_tools`, or run the
  guard (`tests/datasets/test_context_tool_grants_survive.py`). Adding an arm is two edits;
  adding a *tool* is four — registrar, `ARM_DEFINITIONS`, `CONTEXT_TOOLS`, and `ContextCall.tool`.
- **`declaration_search` was base-only by construction** — an arm judging a *rename* could not look
  up the name the PR introduced. It now also searches the PR's changed files in the reviewed
  overlay (`declared_before_this_pr` / `declared_in_this_pr`, `reviewed:` ids); the gate stays
  `base_snapshot` because the gate vocabulary is closed (`test_retrieval_gate.py`).
