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
- Boundary counts are pinned in `tests/datasets/test_package_boundaries.py` (0 backward
  cross-generation edges, 0 v5→v2, 3 private in-package imports). They may only go down.
