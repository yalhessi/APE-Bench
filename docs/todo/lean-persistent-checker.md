# Lean checks from a persistent, incremental server, not a cold process per edit

**Status** — open; measured 2026-10-03 (corrected the same day for a client race): routing, one checker for both tools, concurrency and the copy-on-write reviewed build settled by experiment; `import Mathlib` found wrong in today's reviewed workspaces; nothing built in `src/`
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

1. **One checker for `lean_verify` and `lean_verify_edit`: a Lean server per attempt and reviewed
   workspace, holding a few documents keyed by import header.** The reviewed file's document is
   pinned; its open diagnostics are the baseline and answer an as-is call (`_baseline_errors` stops
   compiling). A body edit goes to it, routed by what it changes (`classify_edits.py`): **cut after the
   changed declaration** when proof-only, comment-only, or a statement change whose name nothing later
   mentions (50-58% of edits), **whole file** otherwise. An **import edit goes to the cold path** (a
   fresh document under the new header was slower than cold, 23.1 s against 16.2 s). A **snippet goes
   to the document for its header**, at a path that need not exist (the server accepts one inside the
   read-only reviewed workspace and elaborates it against that workspace's build). Replayed over 12
   whole recorded sessions, 146 calls in order: **2,071 s → 994 s (2.1×)**, edits 2.3×, snippets 1.7×;
   the same answer on 142, the other four being rendering (3) and the `autoImplicit` gap with the
   server right (1). On edits alone, both replays: median **0.41 / 0.48 s** against 10.3 / 9.6 s.
   - **Snippets gain only when their header is already open** (0.36 s warm against 8.5 s to open). Two
     headers known at session start -- the reviewed module, `import Mathlib` -- cover two thirds of
     recorded snippets; opening them in the background is estimated to take snippets from 355 s to
     ~164 s (cold 596 s), at the memory of a full-Mathlib document per session. Not measured.
   - **Completion is Lean's `textDocument/waitForDiagnostics` for the exact version, then
     diagnostics stamped with it** -- never leanclient's `get_diagnostics` (it returned the previous
     version's messages at 0.0-0.1 s). **Documents keep the workspace's own path** -- leanclient
     resolves symlinks, so an unchanged reviewed file opens in the base. Both fixed by a ~30-line
     subclass (probe `replay_sessions.py`).
   - **Concurrency needs no extra builds**: 16 servers on one read-only build answered identically,
     per-edit median 0.50 → 0.74 s, ~1.45 GB per session. Keep the engine's `#print axioms` / sorry
     checks by appending the command. The checker kind goes into the run plan.
   - **What stays slow, correctly:** an early edit that changes what later declarations use, in an
     elaboration-heavy file (ContinuousAlgEquiv's line-92 redesigns, 10.7-12.2 s against 24 s), import
     edits (today's cost), and a snippet under a header nobody opened. Untried: a second warm copy of
     the file, exact references from the server, a two-phase answer.
2. **Reviewed workspaces as copy-on-write farms -- feasible, one Lake pass, exact.** `.lake/build`
   becomes links into the base's build, except real copies (mtimes kept) of every file in the
   import-graph superset (changed modules and every module between them and a target); new modules
   need no files. Lake rewrites exactly what its traces call stale: 10 / 13 / 797 modules on
   33337 / 9806 / 33321, the same as the copy-built workspaces, in 97 / 28 / 446 s, copying 16 / 170 /
   765 MB instead of 2.8 GB; byte-identical build products; nothing ever written into the base; a
   server on the farm maps the base's own `.olean` inodes. Replaces `_materialize_build_tree`'s copy.
   Not yet tried on NFS or with a deleted module (the farm should not link its files).
3. **`import Mathlib` in a reviewed workspace is not the PR's library, today.** Only changed and
   in-between modules are rebuilt, so the aggregator and the rest of the downstream cone are the
   base's: on 33321 a `#check` of the lemma the PR adds is Unknown constant under `import Mathlib`
   (importing the new module directly works), and Lake lists 571 modules plus the aggregator as stale.
   22% of snippets use `import Mathlib`; 17% of validation PRs add modules. Exact means building the
   downstream cone (median 552 modules, 29 of 60 PRs at 1,000+). Cheaper, untried: Mathlib's
   content-addressed cache may already hold the PR's build; or add the PR's new modules to such a
   snippet's header; at least, say what `import Mathlib` resolves to.
4. **No lake and no NFS on the hot path.** `lake setup-file` once per file, then `lean --setup`; this
   also fixes the fidelity gap (the cold path never applies Mathlib's `autoImplicit false`,
   `maxSynthPendingDepth 3`, `pp.unicode.fun`, linter options -- one replayed snippet already gave a
   different answer because of it). Stage the read-only closure on tmpfs or `/data/local`: imports
   load in 2.5 s against 7.5-8.7 s, which is what every document open and cold call still pays.

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
