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
  (`BuildManager.build_reviewed_workspace`; 4–12 min each on this NFS depending on cache, the
  `.lake/build` copy is the cost — hardlinks fail because Lean truncates `.ilean` in place). Build with
  `prebuild --reviewed --config <run cfg> --execute`; `plan` reports how many episodes lack one;
  `dataset.require_reviewed_workspaces: true` makes `run` refuse; the task falls back to the overlay
  at WARNING otherwise. Still true: never suppress a compile claim in a prompt — a compile claim on
  a PR that builds is a tool defect until proven otherwise, and now the first question is whether
  the run verified against a reviewed workspace (`plan` says).
- **The naming arm is calibrated to the *local family*, by its prompt, and the maintainer often is not.**
  On 33337 the local siblings at base all used the `_coe_` style; the maintainer asked for the
  repo-wide emerging `toLinearMap_` prefix (24 files elsewhere, 0 in the PR's files, 0 precedent
  hits, 0 Zulip). The arm searched correctly and submitted nothing, 10/10 reps — as its contract
  says. The generalist, carrying no such guardrail, named the convention 8/10. The registry row
  already records that *"the code corpus argues against the maintainer on both naming asks this
  release scores"*. This is a contract decision, not a bug: widening the arm's evidence bar trades
  its precision for the maintainer's convention radius. Decide it on purpose.
- **`declaration_search` was base-only by construction** — an arm judging a *rename* could not look
  up the name the PR introduced. It now also searches the PR's changed files in the reviewed
  overlay (`declared_before_this_pr` / `declared_in_this_pr`, `reviewed:` ids); the gate stays
  `base_snapshot` because the gate vocabulary is closed (`test_retrieval_gate.py`).
