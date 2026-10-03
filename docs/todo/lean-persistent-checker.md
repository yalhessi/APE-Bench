# Lean checks from a persistent, incremental server, not a cold process per edit

**Status** — open; measured 2026-10-03 on two sets of runs (corrected the same day for a client race), with the routing policy, concurrency, and the copy-free reviewed build settled by experiment; nothing built in `src/`
**Cost** — no spend to build or to replay; one Claude-subscription dev rep to confirm (bills nothing)
**Motivating example** — Compile is **20–51% of session wall time** on the recent dev runs (Opus
hygiene rep2: 76 of 147 min; one session 83%) and ~20% of arm time in the lead pipeline (rel050:
362 compiles, 67 of 326 arm-min). Each check is a fresh `lake env lean --json <tmp>` that pays lake
startup (1.5–2.8 s), loads the import closure over NFSv3 (12,498 `.olean` files, 7.4 s for one
Analysis file), and elaborates the whole file from line 1, for every edit and again for the
baseline. Replaying recorded Claude edits on two sets of runs (strict completion wait, below): **median
9.6 s → 1.23 s** (56 edits, three dev runs) and **10.3 s → 0.70 s** (54 edits, review-designs
structured/3 rep 1) in one persistent server per file (`didChange`; Lean redoes only what follows the
edit), and **0.56 / 0.55 s** when a theorem edit that keeps its statement is checked on the file cut
after it. Per file, baseline and as-is calls included: **3.1× and 4.2×** less Lean time. Errors agree
55/56 and 54/54 once `=>`/`↦` is normalised, warnings 54/54; the one difference left is the engine's
own forbidden-axiom check.
**What would close it** — `lean_verify_edit` and `lean_verify` answered by a persistent server in
`src/ape/toolkits/execute/lean/`, with the cold engine as fallback; the probe replay rerun through
the tool shows per-edit median ≤ 1 s and error and warning sets equal to the cold path modulo
pretty-printing;
one dev rep shows compile below 10% of session wall, with findings unchanged in kind.

## Design, in order of payoff

1. **A persistent checker per attempt and reviewed workspace.** One Lean server (the official one,
   through `leanclient` with two fixes, below); a document per reviewed file, opened on first use.
   Its diagnostics *are* the baseline (`_baseline_errors` stops compiling), and an as-is call is
   answered from them. Each edit is `didChange` to the spliced text, routed by what it changes
   (`classify_edits.py`): **cut after the changed declaration** when it is proof-only, comment-only,
   or a statement change whose name nothing later mentions (50% / 58% of recorded edits); **import
   edits to a separate cold process** (sending one to the document restarts it, and the next edit
   pays a second restart: 23.0 s → 1.4 s once routed away); **whole file** otherwise. Measured on
   both replays: median **0.41 / 0.48 s** against 10.3 / 9.6 s cold, totals 6.8× / 5.0× less, and
   the same answer as the cold path on 109 of 110 (the axiom post-check). `lean_verify(code=…)`
   uses one scratch document per distinct header. Keep the engine's `#print axioms` / sorry checks
   by appending the command. Same response shape. The checker kind goes into the run plan.
   - **Completion is Lean's `textDocument/waitForDiagnostics` for the exact version just sent, then
     diagnostics stamped with that version** -- never leanclient's `get_diagnostics`, whose progress
     handler ignores versions (5 of 13 warnings and a missing error at 0.0-0.1 s in one replay).
   - **Documents keep the workspace's own path.** leanclient resolves symlinks into the URI, so a
     reviewed workspace's unchanged file (a symlink into the base) opens in the base's environment
     and its diagnostics never match; a 10-line subclass fixes it (probe `concurrency.py`).
   - **Concurrency needs no extra builds.** Every check is read-only: 16 servers on one build answered
     identically, per-edit median 0.50 → 0.74 s, ~1.45 GB per session (23 GB at 16).
   - **What stays slow, and is correct to be slow:** an edit that changes a `variable` line,
     a `def`/`abbrev` or anything later declarations use, early in an elaboration-heavy file --
     ContinuousAlgEquiv's line-92 redesigns cost 10.7-12.2 s (cold 24 s) -- and import edits, at
     today's cost. Untried: a second warm document per file (the edit after a redesign paid 9-14 s
     to restore the prefix), exact references from the server instead of the text test, a two-phase
     answer.
2. **Reviewed workspaces as symlink farms, not copies -- feasible.** `.lake/build` becomes real
   directories only on the paths Lake writes, everything else symlinks into the base's build; a
   module Lake must rewrite while still a link is refused by the base's 444 inode, and that module
   is materialized and the build resumed (`farm_iterative.py`). On 33337 (5 refusals, 6 passes) and
   9806 (1 pass) it converged on exactly the copy's rebuild set (10 and 13 modules), wrote 31 and
   16 MB in 151 and 21 s, produced byte-identical `.olean`/`.ilean`/`.ir`/`.c`, left Lake reporting
   up to date, and compiled `Positive.lean` with 0 errors through both the cold path and a server --
   which maps the base's own `.olean` inodes, so every reviewed workspace of one base shares one page
   cache. It replaces `_materialize_build_tree`'s 2.7 GB copy (~10 min each), which matters for the
   validation and test sets' reviewed workspaces, still open in `eval-set-selection.md`. Not yet
   tried on NFS or on a PR that adds or deletes modules. The import-graph superset is the one-pass
   alternative, safe but over-building (120 modules against Lake's 13 on 9806).
3. **No lake and no NFS on the hot path.** `lake setup-file` once per file, then `lean --setup`.
   This also fixes a fidelity gap: the cold path never applies Mathlib's `autoImplicit false`,
   `maxSynthPendingDepth 3`, `pp.unicode.fun` or linter options, which the setup data carries.
   Stage the read-only closure on tmpfs or `/data/local` keyed by base commit: imports load in 2.5 s
   against 7.5–8.7 s. This speeds up whatever stays cold: server opens, import edits, builds.

**Start here**
- read: `results/pr_review_v5/probes/lean-build-2026-10-03/README.md` (every number above);
  `src/ape/tasks/lean_tasks/formal_math/review/base.py` (`_register_lean_verify_edit`,
  `_edited_file_code`, `_baseline_errors`, `_attribute_errors`);
  `src/ape/toolkits/execute/lean/tools.py` (`LeanVerifyToolsProvider.execute`, the response shape);
  `src/ape/toolkits/execute/lean/core/verification.py` (the cold engine, axiom/sorry checks);
  `src/ape/toolkits/code/lean/provider.py` (the existing per-session `LeanLSPClient`, called
  synchronously inside async tools, and resolving paths -- on an unchanged reviewed file it
  presumably runs against the base, untested); `src/ape/toolkits/execute/lean/core/build_manager.py:556`
  (`_materialize_build_tree`, the copy the farm replaces); the probe's `farm_iterative.py`,
  `replay_policy.py`, `classify_edits.py`, `concurrency.py` (the client subclass)
- run: the probe README's commands (no spend; a replay ~45 min, a farm build 1-3 min)
- bounded by: `docs/dead-ends.md` "Snippet verification of findings" (why reviewed workspaces exist;
  hardlinks fail because Lean truncates `.ilean` in place; the overlay never writes the base);
  `docs/research/reviewed-workspaces.md` (an unchanged file importing an unrebuilt dependent can load
  a stale `.olean`, the same with an overlay); `wall-clock-arm-runtime.md` (NFS, not file count,
  is what makes `content_search` slow); branch `review-designs` `7f16d971` (a submitted edit the
  reviewer already compiled is not compiled again, complementary); branch `hygiene-layer`
  `f09e8135` (Claude Code aborts an MCP call after 300 s of silence)

**Evidence** — `results/pr_review_v5/probes/lean-build-2026-10-03/` (`replay.jsonl`,
`replay_analysis.txt`, `compile_times.txt`); `verification.py:310` (the `lake env lean` command)

**Risk** — A wrapper that trusts leanclient's completion or path handling reports a stale or wrong
"compiles", invisibly; both are fixed only by the two rules above. The cut rule must be exactly right
or a statement change reads as compiling: it uses a conservative text test for later references and
agreed with the cold path on 57 of 58 cut edits (the miss is the axiom post-check). Memory: ~1.45 GB
per session, 23 GB at 16 concurrent. `leanclient` is synchronous, so its calls belong in
`asyncio.to_thread`. Compile output changes with Mathlib's options, so findings are not
byte-comparable with recorded runs on compile text. The farm's refusal loop costs a Lake pass per
layer of downstream rebuilds (6 passes on 33337).
