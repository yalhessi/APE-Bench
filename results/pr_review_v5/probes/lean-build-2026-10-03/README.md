# Where Lean compile time goes, and what a persistent server does to it (2026-10-03)

No spend. Measured on the shared 64-core box at load ~30 (other sessions' runs), so absolute
seconds carry that noise; the ratios held in every file tried.

## 1. Compile is a large share of a session

`compile_times.py 60` over the scaffold logs (`Verification completed, time:`) of the 60 most recent
runs: **2,769 compiles, median 7.3 s, p90 19.6 s, p99 40.4 s**; 13 hit the 300 s timeout (two Opus
hygiene reps). `compile_share.py` divides by each session's log span:

| run | sessions | session wall | compile | share |
|---|---|---|---|---|
| `probe_dev_opus55_contract2_hygiene_claude_sub_rep2` | 19 | 147 min | 76 min | **51%** (one session 83%) |
| `probe_dev_opus55_contract2_hygiene_claude_sub_rep3` | 23 | 177 min | 73 min | 42% |
| `probe_dev_structured_hygiene_claude_sub_rep1` | 15 | 117 min | 44 min | 38% |
| `iter_local397_contract2_dev_rep3` | 15 | 104 min | 22 min | 21% |
| `probe_dev_structured_gpt52_Grc_contract2_rep1` | 15 | 133 min | 27 min | 20% |
| `probe_dev_opus5_contract2_claude_sub_rep1` | 15 | 131 min | 26 min | 20% |

The lead pipeline is the same order: `pr5_A_lead_heldout12_rel050_rep1` ran 362 compiles, 67 min,
against 326 arm-minutes (~20%); `..._v2_rep1` 442 compiles, 72 min.

## 2. What one compile is made of

Every `lean_verify` / `lean_verify_edit` is `lake env lean --json <tmpfile>`
(`src/ape/toolkits/execute/lean/core/verification.py:310`), a fresh process that elaborates the
whole file from line 1. Measured by hand:

| | Functor/Basic (157 lines) | HasLimits (1213) | Mon_ (1038) | ContinuousAlgEquiv (229) |
|---|---|---|---|---|
| `lake env true` | 1.5 s | 1.5 s | 1.5 s | 2–2.8 s |
| + load imports (header-only file) | 3.7 s | 3.9 s | 4.1 s | 9.3–10.2 s |
| whole file | 3.9 s | 7.0 s | 11.4 s | 20–32 s |

ContinuousAlgEquiv's import closure is **12,498 `.olean*` files**, all opened over NFSv3 on every
compile. The same closure staged on tmpfs loads in **2.5 s against 7.5–8.7 s** from NFS (header-only,
no lake); staging it took 7 s. Command-line `lean` is effectively serial (user ≈ real) and
`-j8 -DElab.async=true` did not change Mon_ (10.1–10.7 s against 11.1 s).

The cold path also compiles with **Lean's defaults, not Mathlib's**: `lake setup-file` reports the
lakefile's `autoImplicit: false`, `maxSynthPendingDepth: 3`, `pp.unicode.fun: true` and the `weak.linter.*`
set, and `lake env lean` applies none of them (`LeanVerifyToolConfig.lean_options` is empty by
default). In the replay below this showed only as `=>` vs `↦` in 3 messages; the other two can in
principle accept an edit Mathlib rejects or reject an instance search Mathlib accepts. Not observed.

## 3. Replay: the same recorded edits, cold vs one persistent server per file

`replay_bench.py` takes the `lean_verify_edit` calls recorded in Claude runs, splices each exactly as
the tool does (`splice_declaration` / line span), and checks each one (a) through today's
`VerificationEngine` and (b) through one `leanclient` server per file: the file opened once, each
edit pushed as `didChange`. Lean re-elaborates only from the first changed command, with imports and
the prefix kept. Mode (c) cuts the file right after the new declaration. 7 files, up to 8 edits each.

**Correction (same day): the first numbers committed here were partly an artifact.** leanclient's
`get_diagnostics` can return before Lean has finished the new version. Its `$/lean/fileProgress`
handler ignores the document version, so a late "done" from the previous version marks the new one
done, and its `publishDiagnostics` handler accepts the previous version's messages
(`leanclient` 0.10.0, `file_manager.py`, `handle_file_progress` / `handle_publish_diagnostics` /
`FileState.is_ready`). On a file that already has messages it returns those. Seen on
GalerkinRegularity: 5 of 13 warnings and a missing error, at 0.0-0.1 s. The work is not skipped,
only billed to the next edit (ContinuousAlgEquiv edits 5/6: 0.5 s / 26.8 s with the race,
23.0 s / 2.0 s strictly), so totals barely moved and medians did. `replay_server_strict.py` redid
the server half of both replays waiting on Lean's own `textDocument/waitForDiagnostics` for the exact
version, then for diagnostics stamped with it: every answer stamped, none changed in the following
second, and leanclient's answer differed on 0 of 110 edits in that pass. The race is intermittent.
**A persistent checker must wait this way; leanclient's completion test is not usable as is.**

Strict results (cold side unchanged from the first pass). The first passes stay on disk as the record
of the race: `replay.jsonl` / `replay_analysis.txt` and `replay_review_designs*`; read the `strict_*` files.


| | first replay: three dev runs, develop's tool (`strict_first_replay*`) | review-designs `probe_dev_structured3_hygiene_claude_sub_rep1`, that branch's tool (`strict_review_designs*`) |
|---|---|---|
| edits | 56 on 7 files | 54 on 7 files |
| cold median / total | 9.6 s / 732 s | 10.3 s / 751 s |
| server, whole file: median / total | **1.23 s** / 195 s (3.8×) | **0.70 s** / 157 s (4.8×) |
| server, cut where sound: median / total | **0.56 s** / 179 s (4.1×), cut on 19 | **0.55 s** / 147 s (5.1×), cut on 14 |
| per file, baseline + edits + as-is calls | 862 s → 278 s (3.1×) | 1,041 s → 247 s (4.2×) |
| errors identical after `=>`/`↦` | 55/56 | 54/54 |
| warnings identical | not recorded cold | 54/54 |
| sound cuts agree on error presence | 18/19 | 14/14 |

The review-designs replay runs from that worktree (`replay_bench_v2.py`), so the splice, the
`WHOLE_FILE_OPTIONS` linter set, the kept final newline and "no replacement deletes the span" are
that branch's own. The one remaining error difference, in both runs the same GalerkinRegularity edit,
is `Forbidden axioms used: bkm_implies_regularity`: the engine's own `#print axioms` post-check,
which a server path must keep. `disagree_check.py` reproduced three of the racy disagreements four
ways (cold, a fresh `lean --setup` with the server's options, server, server after 20 s) and all
four agreed.

Opening the file costs about what today's baseline compile costs, and its diagnostics *are* the
baseline. The server's time depends on where the edit is: elaboration below the edit is redone.
ContinuousAlgEquiv (elaboration 15-22 s of a 24 s compile) stays at 0.8-24 s, median 12 s. An edit
in the import header restarts the file (BaseExists line 9: 9-12.5 s, about a reopen).

**When the cut is sound.** A theorem whose statement and attributes are unchanged cannot change
anything after it, so the cut file answers the same question; the replays cut only those edits.
Over five Claude runs' 576 `lean_verify_edit` calls (85 as-is, 237 declaration, 254 line span),
**164 of the 237 declaration edits are theorems with the statement kept**; 40 change the statement,
20 are `def`s, 13 `axiom`s. Line-span edits inside a proof would qualify too and are not cut here.
The 85 as-is calls cost nothing: the open's diagnostics answer them.

Server footprint seen: `lake serve` 0.8 GB, `lean --server` 1.0 GB (its reference index), each
open file's worker 1.6-1.8 GB RSS, mostly shared mmap of the same `.olean`s.

## 4. Reviewed workspaces without the copy: a symlink farm (feasible)

`51192f7a…+9806fbc709c7`: of **81,821 files (2.8 GB)** in its `.lake/build`, **143 (11 MB, 13
modules)** differ from the base (`lib/lean` only). Two ways to use that:

**Reading.** `lean --setup=<json>` takes an explicit artifact path per import (the JSON `lake
setup-file` emits). Base artifacts with only the rebuilt modules repointed reproduced 33337's
reviewed compile of `Positive.lean` message for message (0 errors); base alone gives the 3
``Unknown constant `Submodule.coe_starProjection_eq_isComplProjection` `` errors.

**Building, without the 2.7 GB copy.** The new root's sources are the existing source overlay;
`.lake/build` is a *farm* of links into the base's build, with real files only where Lake may
write. Three variants were built and checked against the copy-built workspace:

| | 33337 (2 changed) | 9806 (13 changed) | 33321 (5 changed, one new; touches `Algebra/Group/Hom/Basic`) |
|---|---|---|---|
| import-graph superset (changed modules and every module between them and a target) | 10 | 120 | 797 |
| modules Lake rebuilt in the copy-built workspace | 10 | 13 | 797 |
| **copy-on-write farm** (`farm_cow.py`): real copies of the superset's files, links for the rest; one Lake pass | **10 rebuilt, 97 s, 16 MB copied** | **13 rebuilt, 28 s, 170 MB** | **797 rebuilt, 446 s, 765 MB** (13 s to lay down) |
| refusal loop (`farm_iterative.py`): materialize a module only when Lake is refused | 10, 151 s, 6 passes | 13, 21 s, 1 pass | stopped after 25 passes, >15 min: one rebuild layer per pass |
| superset with no files at all (`farm_build.py`) | 10, 80 s | 120 (over-built), 170 s | -- |

The copy-on-write farm is the one to build: one pass, Lake's exact rebuild set every time (it rebuilt
13 of 120 on 9806 because copies of modules whose public interface did not change stay valid), never
a write into the base (links point at 444 files in 555 directories, and a module Lake might rewrite
is a real copy), and a copy bounded by the superset instead of the whole build. In every farm, `lake
build --no-build` reports everything up to date and every `.olean`, `.ilean`, `.ir` and `.c` Lake wrote
is byte-identical to the copied workspace's (only `.trace` logs and `.setup.json` embed the root
path). On 33337, `Positive.lean` compiles with 0 errors through the cold path and through a Lean
server, which maps the base's own `.olean` inodes (4,344) plus the farm's rebuilt ones (18), so a
base's reviewed workspaces share one page cache. The import-graph prediction cannot be exact in
advance under Lean's module system, which rebuilds downstream only when an upstream public interface
changed -- that is what the record meant by "not knowable before the build runs"; the copies make it
unnecessary to know. Built on tmpfs; NFS is untried (only laying down the farm should move).

## 5. Early edits in slow files: a safe cut covers about half, the rest is genuinely sequential

`classify_edits.py` re-parses each recorded edit (old and new file) and sorts it by what it changes
(`edit_classes_*.json`):

| recorded `lean_verify_edit` edits | five dev runs (501) | review-designs (130) |
|---|---|---|
| proof only (one theorem's text; statement, name, attributes kept; nothing else changed) | 42% | 37% |
| comment / docstring only | 7% | 18% |
| statement or name changed, no attributes, name not mentioned later in the file | 1% | 3% |
| **safe to cut after the changed declaration** | **50%** | **58%** |
| import header | 7% | 4% |
| needs the rest: `variable`/`open`/other commands 15/14%, declarations added or removed 9/3%, `def`/`axiom`/`instance` 8/11%, several declarations 5/3%, statement used later 4/6%, attributes 3/2% | 43% | 38% |
| …of which in the first half of the file | 18% | 12% |

`replay_policy.py` re-timed both replays (strict wait) under that policy: cut where safe, import
edits to a separate cold process (sending them to the document restarts it, and the next edit pays a
second restart -- ContinuousAlgEquiv's edit after an import edit fell from 23.0 s to 1.4 s, BaseExists'
from 10.4 s to 2.1 s), everything else whole-file (`policy_*.jsonl`, `policy_analysis.txt`):

| | review-designs (54) | first replay (56) |
|---|---|---|
| cold median / p90 / total | 10.3 / 24.7 / 751 s | 9.6 / 25.1 / 732 s |
| **policy** median / p90 / total | **0.41 / 4.3 / 111 s (6.8×)** | **0.48 / 9.6 / 147 s (5.0×)** |
| excluding import edits | 47 s against 687 s (14.7×) | 95 s against 680 s (7.2×) |
| non-import edits over 5 s | none | 5, all ContinuousAlgEquiv |
| same answer as cold | 54/54 | 55/56 (the axiom post-check) |

The residual is one file. Three ContinuousAlgEquiv edits rewrite a section's `variable` line and an
`abbrev` at line 92 of 229: everything after can change meaning, and they cost 10.7-12.2 s (cold:
24 s). Two late proof edits right after them cost 9.2 and 13.6 s: Lean diffs against the document's
*current* text, so the first edit after a redesign pays to restore the prefix. Untried: a second warm
document per file, each edit sent to the one sharing the longer prefix (~1.5 GB more per file); exact
references from the server instead of the conservative text test; more worker threads (command-line
`lean -j8 -DElab.async=true` did not speed up Mon_); a two-phase answer (the edited declaration now,
the rest later), which changes the tool's contract.

## 6. Import edits: no cheap exact answer, so keep them off the warm document

All 39 recorded header edits *remove* imports. In 8 the module stays in the closure of the remaining
imports; in 31 it leaves it, so the environment really changes and the whole file must be redone
under the new header -- today's cost, no more. All of these files use the module system, where
import visibility makes even the 8 not a guaranteed identity. Routing them to a separate cold process
keeps the warm document's state for the edits that follow (section 5).

## 7. Concurrency, and many builds at once

`concurrency.py`: K sessions, each its own process and server, open Meromorphic/Basic (a reviewed
file) at once and push its 8 recorded edits with the strict wait; memory is read 60 s after the last
edit from `/proc/<pid>/smaps_rollup` over every server process (`concurrency.jsonl`):

| K on one build | open (median) | per-edit median (max) | answers identical | PSS total |
|---|---|---|---|---|
| 1 | 11.7 s | 0.50 s (0.6) | -- | 2.9 GB |
| 4 | 15.7 s | 0.53 s (0.6) | yes | 7.0 GB |
| 8 | 20.1 s | 0.54 s (0.7) | yes | 12.5 GB |
| 16 | 29.0 s | 0.74 s (0.9) | yes | 23.2 GB (1.45 GB/session, 1.2 GB of it private heap) |

A build is read-only to every check, so concurrent attempts need no build of their own: 16 servers on
one build answered identically. Three sessions on one shared build against three full copies of it,
opening the same unchanged file: 6.9 against 7.1 s, 0.04 s per edit, 4.8 against 5.0 GB -- once warm,
copies cost nothing extra at run time; their cost is the 2.8 GB and ~10 min each at build time, and
a cold read per copy. Farms share the base's inodes (section 4), so many reviewed workspaces of one
base share one page cache.

**leanclient defect 2: symlinks.** leanclient resolves symlinks when it builds a document's URI.
In a reviewed workspace an unchanged file is a symlink into the base, so it is opened in the **base's**
environment and its diagnostics never match the opened document: every check waited out the 30 s
stamp deadline (`concurrency_symlink_bug.jsonl`: "37.5 s open, 30.05 s per edit"). Keeping the
workspace's own path (a 10-line subclass in `concurrency.py`) fixes it: Lean publishes under that
path and the worker maps the reviewed copy's `.olean`s (422 mappings). The existing
`LeanCodeToolsProvider` (`code_hover`, `code_goto`, `get_lean_goal`) resolves the path and walks up
to the nearest `lean-toolchain`, so on an unchanged file it presumably runs against the base, not the
reviewed workspace; not tested.

## 8. PRs that add or delete modules, and `import Mathlib`

In the validation set (60 PRs, a natural-rate draw), **10 add Lean modules (17%)**, 14 new modules in
all, 4 PRs consisting only of new files; **none delete one** (nor in the 16 dev PRs, 2 of which add one:
33149 GalerkinRegularity, 33321 BaseExists). Deletions are rare, below ~5% on this sample.

- **Checking a new file** needs nothing special: it is a real file in the reviewed workspace, and the
  replays above already served GalerkinRegularity and BaseExists edits through the server.
- **Building a new module**: it is a target and part of the superset with no base files to copy; the
  copy-on-write farm built 33321's BaseExists in its single pass.
- **Importing a new module directly** works: `import Mathlib.LinearAlgebra.RootSystem.BaseExists` then
  `#check @RootPairing.baseOf_pairwise_pairing_le_zero` answers.
- **`import Mathlib` does not, in today's reviewed workspaces** (`aggregator_33321.txt`): the same `#check`
  under `import Mathlib` is ``Unknown constant `RootPairing.baseOf_pairwise_pairing_le_zero` ``. Only the
  changed modules and those between them are rebuilt; `Mathlib.lean` (the aggregator the PR edits to
  add the import) and everything else downstream are the base's -- Lake lists **571** modules plus the
  aggregator as out of date. So `import Mathlib` in a reviewed workspace is the base library with the
  rebuilt modules mixed in: it misses new modules and can load modules stale against the PR's changed
  interfaces. 58 of 258 recorded snippets (22%) start with `import Mathlib`. This is a defect of the
  current reviewed workspaces, independent of the server design.
- **Making it exact** means building the PR's whole downstream cone. On the base import graph (7,437
  modules) the validation PRs' cones are median 552 modules, p90 6,235, max 7,407; 29 of 60 reach
  1,000 or more -- near a full Mathlib build for half the PRs, per PR, before the module system's
  rebuild avoidance (13 of 120 on 9806, 797 of 797 on 33321). Cheaper options, untried: Mathlib's own
  content-addressed cache (`lake exe cache get` keys files by content, and CI builds every PR, so the
  PR's full build may already exist; the cache binary does not run in these workspaces as built);
  adding the PR's new modules to an `import Mathlib` snippet's header (new declarations visible, stale
  downstream modules still stale); or saying in the result that `import Mathlib` is the base library
  plus this PR's rebuilt modules.
- **Deleting a module**: the farm should simply not link the deleted module's files, so importing it
  fails as it would on the PR; the copy keeps the stale files importable. Untested -- no PR in the
  samples deletes one.

## 9. One design for `lean_verify` and `lean_verify_edit`

**The recorded snippets** (258 `lean_verify` calls in 56 sessions of six Claude runs): `example` 74,
`#check` 73, both 30, small theorems 22, other 56; median 10 lines. Their imports: **only the PR's
own changed modules 117 (45%)** -- usually the reviewed file's module -- **`import Mathlib` 58
(22%)**, other specific modules 68 (26%), a mix 15 (6%). 27 sessions use one header, 12 two; a
distinct header serves 1.9 calls on average.

**The design.** One Lean server per attempt and reviewed workspace, holding a pool of documents
keyed by import header (at most 3 open; least recently used closed first):
- the reviewed file's document, at its own path, pinned. Its open diagnostics are the baseline and
  answer an as-is call;
- an edit to the file's body goes to that document, cut after the changed declaration when sound,
  whole file otherwise (sections 3, 5);
- an import edit goes to the cold path: a fresh document under the new header was *slower* than
  cold (median 23.1 s against 16.2 s), because opening one costs a `lake setup-file` besides the import;
- a snippet goes to the document for its header. Hosting needs no file: the server accepts a
  document at a path that does not exist, inside the read-only reviewed workspace or under /tmp, and
  elaborates it against that workspace's build -- in 33337's reviewed workspace `#check
  @Submodule.coe_starProjection_eq_isComplProjection` answers, in its base it is Unknown constant; a
  second body under the same header took 0.01 s.

**Replayed whole sessions** (`replay_sessions.py`): the 12 review-designs structured/3 sessions that
used `lean_verify`, every call in recorded order -- 146 calls, 41 of them snippets -- through one
server each, against the branch's cold path (`sessions_review_designs.jsonl`, `sessions_analysis.txt`):

| route | calls | cold median → server median | cold total → server total | same answer |
|---|---|---|---|---|
| edit, cut | 54 | 9.7 → **0.47 s** | 712 → 209 s | 54/54 |
| edit, whole file | 37 | 10.3 → **2.17 s** | 516 → 175 s | 36/37 |
| as-is (pays the file's open) | 10 | 13.1 → 13.5 s | 180 → 171 s | 10/10 |
| import edit, new document | 4 | 16.2 → 23.1 s | 67 → 84 s | 4/4 |
| snippet, header already open | 17 | 22.7 → **0.36 s** | 328 → 69 s | 14/17 |
| snippet, new header | 24 | 8.2 → 8.5 s | 267 → 286 s | 24/24 |
| **all** | 146 | | **2,071 → 994 s (2.1×)** | 142/146 |

Per session 0.8-7.2×, median 2.2×; edits 2.3×, snippets 1.7×. Opening a document costs about a cold
compile, so a snippet gains only when its header is already open. The cold side here omits today's
extra baseline compile per file, so it is slightly understated.

**The four disagreements** (`sessions_disagreements.jsonl`, re-run with texts): three are the same
`aesop` failure with the goal printed differently; the fourth is the option gap of section 2 with the
server right -- a snippet using an unbound `ω` is a type mismatch under the cold path's default
`autoImplicit true` and ``Unknown identifier `ω` `` under Mathlib's `autoImplicit false`, which the
server applies even to a scratch document in the workspace.

**Pre-warming, estimated, not measured:** opening the reviewed module's header and `import Mathlib`
at session start would cover two thirds of recorded snippets. Re-pricing the 13 of 24 snippet opens
whose header that would have warmed at the warm median takes snippets from 355 s to ~164 s (cold
596 s), at the memory cost of a full-Mathlib document per session.

## Reproduce

```
export PATH=$HOME/.elan/bin:$PATH PYTHONPATH=$PWD/src:$PWD
ape/bin/python results/pr_review_v5/probes/lean-build-2026-10-03/compile_times.py 60
ape/bin/python results/pr_review_v5/probes/lean-build-2026-10-03/replay_bench.py \
  probe_dev_structured_hygiene_claude_sub_rep1,probe_dev_opus55_contract2_hygiene_claude_sub_rep2,probe_dev_opus55_contract2_hygiene_claude_sub_rep3 \
  7 8 /tmp/replay.jsonl                                   # ~45 min, no spend
ape/bin/python results/pr_review_v5/probes/lean-build-2026-10-03/replay_server_strict.py \
  results/pr_review_v5/probes/lean-build-2026-10-03/replay_bench.py <same runs> /tmp/replay.jsonl /tmp/strict.jsonl
ape/bin/python results/pr_review_v5/probes/lean-build-2026-10-03/analyze_v2.py /tmp/strict.jsonl
# a branch's own run: the same with replay_bench_v2.py, from inside that branch's worktree
```

Run `lean` from inside a workspace: from the repo root elan resolves a different toolchain and every
import fails with `incompatible header`.
