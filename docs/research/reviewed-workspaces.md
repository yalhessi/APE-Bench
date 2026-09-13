# Reviewed workspaces: what a review task compiles against, and why it changed

*2026-09-13. Branch `verify-reviewed-state`, commits `6f38fc2`..`7207142` plus the hardening
that followed. Written after a five-reader / twelve-verifier pass over the code and the disk;
every claim below was traced to a line or a measurement, and the ones that were only partly
right are stated in their corrected form.*

## The one-paragraph version

Until 2026-09-12 every v5 review run compiled Lean against the **base commit's** build products.
The attempt's `target/` was a *source-only overlay*: symlinks into the read-only base workspace,
the PR's touched files as patched real copies, and `.lake` a symlink into the base's `.lake`. So
`lean_verify` on a changed file saw the PR's *source* but the base's `.olean`s, and a declaration
the PR renamed in a sibling file was `Unknown constant`. On the held-out `lead` run 41 of 321 arm
sessions hit that; 16 findings asserted a build failure on PRs that all build; the tool's own
note said "the file does not compile as it stands". The fix is a **reviewed workspace** per
episode — base snapshot + PR diff + the changed modules rebuilt by a targeted `lake build` in a
real copy of `.lake/build` — built ahead of time by `prebuild --reviewed`, shared by every run,
rep, condition and arm of that episode, and selected automatically by every v5 task when present.
On 33337 the same compile went from 3 errors to 0; across reps 11–12 the `Unknown constant`
count went from 19–68 files per rep to 0 and the phantom `broken_build` findings from 2 to 0.
Recall did not move and was not expected to.

## How a workspace comes to exist (unchanged upstream APE-Bench)

`ape/bin/python -m ape.toolkits.execute.lean.build --input_file <jsonl>` builds a **base commit**:
`git worktree add build_workspaces/<sha>_<pid>_<hex> <sha>` under `locks/source.lock` → `lake exe
cache get` (Mathlib's own cache, `XDG_CACHE_HOME=repos/mathlib4/cache/xdg/<ns>`) → `lake build` (no
targets) → every file sha256-hashed and copied once into the content-addressed store
`data/code_execute/storage/<h[:2]>/<h[2:4]>/<h>` (0o444) with a binary manifest at
`snapshots/<sha>.snap` → worktree deleted. State becomes **BUILT**. Nothing under `workspaces/`
exists yet. (`core/build_manager.py::_execute_build`, `_run_lake_build`, `_create_snapshot`.)

The first task that needs it **restores** `workspaces/<sha>`: each manifest entry is `os.link`ed
from the store (copy only if `link` fails), `.git` removed, the whole tree chmod'ed 0o444/0o555,
state **READY**. Two base workspaces therefore share the inode of every byte-identical file:
`lean-toolchain` has link count 632, `Cache/Main.olean` 55, a commit-unique `Mathlib.olean` 2.
A base costs 3.3 GB on disk but its blocks are shared with the 90 GB store. On disk today: 74
READY bases, 145 BUILT-never-restored, one stuck BUILDING since June with a dead pid.

Each attempt gets `attempts/<k>/workspaces/target` as a **symlink** to that shared read-only
directory (`BaseLeanTask.setup_attempt`). Nothing is copied per attempt; that has been true since
upstream `2001734`. The fork's contribution (`38c0407`) is the *overlay*: replace the symlink with
a directory of symlinks and materialise only the touched paths.

State machine: `snapshots/<id>.state` (JSON) under `snapshots/<id>.lock` (`fcntl.flock`, 5 s
non-blocking backoff). BUILDING → BUILT → RESTORING → READY, or FAILED. A live builder pid makes
a second builder *wait*; a dead pid is *taken over* by the next build call (not by a restore call,
which raises `BuildIncompleteError`).

## Which commit the runs verified against — confirmed

Every v5 task's `target_workspace.commit_hash` is the episode's `base_sha`
(`review/task_adapter.py:42-44`; `runner.py::_solo_task_data`); `reviewed_head_sha` is carried
only "for reference". `lean_verify` and `lean_verify_edit` write the code to a system temp file
and run `stdbuf -oL -eL lake env lean [-D experimental.module=true] --json /tmp/verification_X.lean`
with **cwd = `target/`**; `lake env` derives `LEAN_PATH` from the cwd's `.lake/build/lib/lean`.
In an overlay, `.lake` is a symlink to the base's, so imports resolve to base `.olean`s.

There is a **PR-head fast path** in the code (`cache_probe` mode, `pr_head_cache_*` config): fetch
the PR head into the local mathlib repo, make a worktree, `lake exe cache --repo=<fork> get`, and
snapshot a head workspace if Mathlib's remote cache has it. It lives only in the *legacy*
`ReviewPRCoreTask.setup_attempt` (task type `lean_pr_review`). Every v5 task descends from
`BasePRReviewTask`, whose `setup_attempt` goes through `BaseLeanTask.setup_attempt` and never
calls it; `BasePRReviewData` has no `pr_head` field. No PR-head sha in either corpus (193 v4
episodes, 146 v2) has ever had a workspace, snapshot or state file. **So: base builds, always,
until rep11 of 33337.**

## What the reviewed workspace is

**Identity.** `workspaces/<base_sha>+<first 12 hex of sha256(base_sha ‖ NUL ‖ diff)>`
(`build_manager.py::reviewed_workspace_key`; the same `patch_fingerprint` feeds the overlay's
marker). Nothing about the run enters it — not run name, rep, condition, arm, model or config —
so every rep, every A/B/C condition and every arm subtask of an episode resolves to one shared
read-only directory. It changes only when the release re-renders the diff bytes or the reviewed
head changes; then a whole new workspace is needed and the old one is not garbage-collected.
Two PRs on one base need two workspaces (33304/33305/33315 share base `51192f7a` and have three).

**Tree shape** (observed on 33337). Root 0o555. Every base child is a symlink into
`workspaces/<base>/…` except: real directories along each touched path whose untouched children
are symlinks; the changed files as real 0o444 patched copies; and `.lake`, a real directory whose
`build` is a full `copytree` copy (0o444/0o555 after finalisation) and whose `config` and
`packages` are symlinks to the base's. ~150 absolute symlinks in total.

**Why a copy.** Lean rewrites `.ilean` files in place across the rebuilt set, so hardlinks into
the shared 0o444 inodes fail with EACCES (measured); NFSv3 has no reflink. The copy is the cost:
585 s cold, ~150–250 s warm, 2.8 GB per workspace, not deduplicated, not in the content store
(no `.snap` is written; it cannot be restored elsewhere).

**Build.** `BuildManager.build_reviewed_workspace(key, base, prepare_sources, changed_files)`:
`try_start_build(key)` (the base build's locking, waiting and dead-pid takeover, unchanged) →
in a hidden same-parent sibling `.<key>.<pid>.<hex>`: the task layer's
`ReviewPRCoreTask.prepare_reviewed_sources` lays the overlay and applies δ₀ (the same function
the per-attempt overlay uses, so the two cannot lay down different sources) →
`_materialize_build_tree` replaces the `.lake` symlink with the real dir + copied `build` →
targets derived **from the patched tree** (`+Mathlib.A.B` per changed `.lean` that still exists
under a library root; a module the PR adds is absent at base, one it deletes is present, so the
base tree is wrong in both directions) → `lake build +…` → `set_workspace_readonly` →
`os.rename` into place → `complete_build` → BUILT; the first `get_workspace` flips it READY.

**What Lake rebuilds.** `lake build +A +B` examines only the transitive import closures of A
and B, rebuilding whatever in them has a changed trace: the targets and the modules *between*
them on the import graph. On 33337: 2 changed + 8 between = 10 modules, 140 build products.
Dependents *off* that path keep the base's byte-identical `.olean`s. Consequence: a **changed
file** always compiles against a fully rebuilt import closure (this is the fix); an **unchanged
file** that transitively imports an unrebuilt dependent could load a stale `.olean`, and `lake
env lean` performs no trace check — Lean's import validates only the `.olean` header and
duplicate constants, never dependency hashes — so that surfaces lazily as `Unknown constant` or
an unnamed `simp` cascade. The arms' default target is the changed file, so the exposure is
`lean_verify_edit` on an unchanged `path` or `lean_verify` with hand-written imports. The
environment note now states this scope; a `path ∉ changed_files` refusal was considered and not
added — it changes agent behaviour and is a design decision.

A surprise recorded in the artifact test: 33337's rebuilt `Positive.olean` is byte-identical to
the base's — its two hunks rename a lemma inside `simpa [...]` lists that the elaborated terms
never used. Lake's `.trace` and `.ilean` differ, `Submodule.olean` (where the rename is declared)
differs. So the test asserts Lake's own evidence of a rebuild, not olean bytes.

## How the run uses it

`BasePRReviewTask.setup_attempt`: base symlink (BaseLeanTask) → **reviewed** (`_maybe_setup_reviewed_target_workspace`:
compute the key, `RestoreManager.get_workspace(key)`, relink `target/` to the reviewed root,
`WorkspaceInfo.commit_hash = key`) → else the overlay, with a WARNING naming the key, the PR and
the prebuild command. `_verification_environment_note` picks its text by whether the commit hash
carries `+`: "changed modules and the modules between them are rebuilt … a pre-existing error in
a changed file is genuine" vs "imports resolve against the base commit's build products … not
evidence the PR fails to build". `declaration_search` also reads the PR's changed files in the
reviewed overlay (`declared_in_this_pr`, `reviewed:` ids; gate stays `base_snapshot`).

A run **never builds** a reviewed workspace and never waits for one: while a key is BUILDING (or
FAILED, or crashed) `_requires_build_first` is true, the resolver returns None, and the attempt
takes the overlay. The run-level guard is `dataset.require_reviewed_workspaces`: preflight
(`assert_reviewed_workspaces_prebuilt`) always warns with the PR numbers, and refuses the run
when the knob is on. `plan` prints `reviewed workspaces: N of M episode(s) prebuilt`. The knob is
**on** for the two held-out configs (all 12 built) and off in the base config, because smoke4's
four PRs have no workspace yet.

## Building ahead of time, and sharing

`ape/bin/python -m src.mathlib_review.release.prebuild --reviewed --config <run cfg> [--execute]`
plans from the run's own episode selection (`select_units_and_episodes`, shared with `run`), prints
ready / to build / base not built, refuses an episode whose base is not restored, builds
sequentially only with `--execute`, keeps going past a failure and reports it, and checks the
toolchain before a manager exists (`assert_toolchain`: the toolchain half of `assert_ready`,
because the prebuild compiles Lean and calls no model).

Done for the held-out 12 on 2026-09-12 (13:00–15:02): per-PR build 144–997 s, **74.9 min
sequential**, 12 × 2.8 GB ≈ 34 GB (≈1% of the 3.2 TB free on the export). File count is not
the driver — 13-file 33304 took 214 s, 6-file 33321 took 776 s — the length of the import path
between changed modules is. Every rep and condition since shares those twelve directories.

| PR | key | build s | changed files |
|---|---|---:|---:|
| 33117 | `7478ffb2…+75524e45f66e` | 204 | 1 |
| 33145 | `c2a50c83…+9ba5fc6ff7b4` | 144 | 1 |
| 33149 | `e9a7156e…+80eabfc51d64` | 167 | 1 |
| 33285 | `4be5c687…+89dfcf685b0e` | 467 | 9 |
| 33294 | `74bdd8de…+bac116010241` | 189 | 11 |
| 33304 | `51192f7a…+9806fbc709c7` | 214 | 13 |
| 33305 | `51192f7a…+fc3f62ab77e8` | 309 | 7 |
| 33315 | `51192f7a…+eb21388524cd` | 428 | 11 |
| 33321 | `0bf098ca…+b156e3e2fecd` | 776 | 6 |
| 33337 | `a36c84ab…+ae229ca53e6b` | 245 | 2 |
| 33362 | `cc0ebd15…+3bacd846ca00` | 351 | 1 |
| 33421 | `473b5744…+8f934922bdc5` | 997 | 15 |

## Could Mathlib's cache or Lake do this faster or more completely?

Mathlib's cache is **content-addressed per module**, not per commit: key = hash(rootHash ∘ path ∘
file content ∘ hashes of imported modules), recursively, with rootHash over `lakefile.lean`,
`lean-toolchain`, `lake-manifest.json`. `lake exe cache get` recomputes these from the checkout
and fetches `f/{hash}.ltar` from the main namespace or `f/{fork}/…/{hash}.ltar` for a fork; a 404
is skipped silently and `get` exits 0. In a PR-head checkout, modules whose import closure is
untouched share master's hashes; the changed modules *and every transitive dependent* get new
hashes that exist only if CI built that exact content state. If it did, `get` returns the
**complete** head build — strictly more than the local targeted rebuild, which leaves dependents
stale.

CI uploads for every push to a `leanprover-community/mathlib4` branch (main namespace) and, for
fork PRs via `pull_request_target`, to `f/<fork owner>/<repo>` — but `stage` packs only the
modules that run rebuilt, so a fork namespace holds the changed cone and nothing else; unchanged
modules come from the main namespace (CI runs `get` twice). Uploads happen on success, failure
and cancellation, and fork builds are cancelled when a PR gets a new push, so a superseded head
can be partial. **14 of the 16 dev-medium PRs are from forks** (33057 main-repo; 33149's fork is
deleted). GitHub lists fork-CI runs on 9 of 16 reviewed heads and none on 6. No retention policy
is documented locally or upstream; whether the Nov-2025 fork-namespace `.ltar`s still exist is
unverified — a live probe needs the `Cache` executable built at a head checkout.

Temporal leak: none in content — a `get` can only return artifacts for exactly the head's
source state. What leaks is *whether CI built that head*. Network at prebuild only; runs restore
snapshots and the reviewed `lake build` is local.

Cost picture. Local: 585 s copy + 67 s build cold (705 s), ~245 s warm, 2.8 GB/episode. A
full-commit `get` is ~7.8k `.ltar` (~375 MB at ~48 KB each) plus decompressing ~2.6 GB onto
NFS — untimed here. "Copy base then `get` into it" costs the same copy plus a few MB, and
rewrites only differing modules (unpack is skipped when the local `.trace` already matches).
Rebuilding all dependents locally means `lake build Mathlib` (Lake replays untouched traces,
compiles only the cone) — minutes for a leaf, potentially hours for a low-level file; unmeasured.
Lake's own artifact cache is a separate opt-in that Mathlib CI disables.

**Verdict:** the local targeted rebuild is the right design for what the tools compile today
(changed files). The two-pass `cache get` into a fresh `.lake/build` is the one option that would
both avoid the copy and fix the stale-dependent edge, and it is gated on cache retention for
fork heads — an infra question, not a code one. Nothing here is built.

## Stability: what is solid, what was fixed, what remains

**Solid.** The happy path has run 12 real builds and two A/B pairs; 59 tests cover key shape,
target derivation, the builder (with `lake` faked), the from-scratch overlay, task ordering, the
WARNING fallback, the note branches, preflight and prebuild; the read-only finalisation is a
no-op on the base (verified on four bases); the runtime path needs no network and no write to
shared state beyond the one-time BUILT→READY flip.

**Fixed after the verification pass** (all with regression tests):

- `--force-rebuild` built the new tree, failed to `rename` it onto the non-empty old one, read
  the refusal as "another builder won", deleted the *new* tree and **recorded success**. The old
  tree is now moved aside first and removed after the rename.
- Any failed reviewed build would have `chmod`'ed *through* the overlay's symlinks into the base
  — its top-level entries to 0700/0600, on hardlinked blob-store inodes shared by every
  workspace. `safe_remove_directory` now skips symlinks. It had not fired: all 12 builds
  succeeded.
- A hard-killed builder leaves `.<key>.<pid>.<hex>` (up to 2.8 GB) that nothing swept; the next
  builder on that key now removes trees whose pid is dead.
- A second builder on a key waited `restore_queue_timeout` = 600 s and then reported FAILED while
  the first was fine; two real builds took 776 s and 997 s. Reviewed waits now use a 3600 s bound.
- A READY reviewed workspace whose base directory has been removed out of band was served and
  every compile failed on a dangling link; `get_workspace` now refuses it by name.

**Remaining, by choice or for lack of measurement:**

- `lake build` has no timeout (`build_timeout` default None) — a pathological import path blocks
  the sequential prebuild indefinitely. Not observed; the slowest was 997 s.
- `is_process_alive` is host-local: a builder on another host reads as dead and would be taken
  over. One host, one shell for prebuilds, by convention.
- Stale-dependent exposure via `lean_verify_edit` on an unchanged path: stated in the note, not
  refused.
- Reviewed workspaces are not in the content store, not deduplicated, not GC'd; a release
  re-render orphans a set. 34 GB today.
- Eleven of the 12 are BUILT not READY; the first attempt on each flips the state (3 ms write
  to shared `.state`). The 33337 artifact test does the same for that key.
- smoke4's four PRs (33057, 33066, 33098, 33438) have no reviewed workspace; a smoke4 run
  today warns and verifies against base `.olean`s.
