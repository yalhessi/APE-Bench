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

## 4. Reviewed workspaces are 99.6% copy

`51192f7a…+9806fbc709c7`: of **81,821 files (2.8 GB)** in its `.lake/build`, **143 (11 MB, 13
modules)** differ from the base. `lean --setup=<json>` takes an explicit artifact path per import
(the JSON `lake setup-file` emits), so a reviewed environment can be the base's artifacts with only
the rebuilt modules repointed. On 33337 (`a36c84ab…+ae229ca53e6b`, the PR whose sibling rename
caused the `Unknown constant` transcripts), compiling `Positive.lean`:

| environment | errors |
|---|---|
| reviewed workspace (full 2.8 GB copy) | 0 |
| base artifacts + the 10 rebuilt modules (overlay) | 0, every message identical |
| base artifacts only | 3: ``Unknown constant `Submodule.coe_starProjection_eq_isComplProjection` `` and its cascade |

Overlay and reviewed also agree on all 13 changed files of `+9806fbc709c7` (where base agrees too,
so that PR does not discriminate). This shows the *read* side only; building the overlay without the
copy (Lake over a symlinked build tree, or `lean --setup … -o` per module in import order) is not
tested here.

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
