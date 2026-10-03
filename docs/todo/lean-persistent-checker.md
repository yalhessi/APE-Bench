# Lean checks from a persistent, incremental server, not a cold process per edit

**Status** — open; measured 2026-10-03, nothing built
**Cost** — no spend to build or to replay; one Claude-subscription dev rep to confirm (bills nothing)
**Motivating example** — Compile is **20–51% of session wall time** on the recent dev runs (Opus
hygiene rep2: 76 of 147 min; one session 83%) and ~20% of arm time in the lead pipeline (rel050:
362 compiles, 67 of 326 arm-min). Each check is a fresh `lake env lean --json <tmp>` that pays lake
startup (1.5–2.8 s), loads the import closure over NFSv3 (12,498 `.olean` files, 7.4 s for one
Analysis file), and elaborates the whole file from line 1, for every edit and again for the
baseline. Replaying **56 recorded Claude edits** on 7 reviewed files: **median 9.6 s → 0.79 s** with
one persistent server per file (`didChange`; Lean re-elaborates only from the edit), and **0.11 s**
when a theorem edit is checked on the file cut after the edited declaration (395 s → 8.7 s on 32
edits). Error sets identical in 52/56; 3 differ only by `=>`/`↦`; 1 is the engine's axiom post-check.
**What would close it** — `lean_verify_edit` and `lean_verify` answered by a persistent server in
`src/ape/toolkits/execute/lean/`, with the cold engine as fallback; the probe replay rerun through
the tool shows per-edit median ≤ 1 s and error sets equal to the cold path modulo pretty-printing;
one dev rep shows compile below 10% of session wall, with findings unchanged in kind.

## Design, in order of payoff

1. **A persistent checker per attempt and reviewed workspace.** One Lean server (the official one,
   via `leanclient`, already a dependency for `code_hover`/`get_lean_goal`); a document per reviewed
   file, opened on first use. Its diagnostics *are* the baseline (`_baseline_errors` stops
   compiling), and an as-is call is answered from them (85 of 576 calls). Each edit is `didChange` to
   the spliced text. A theorem edit that keeps statement and attributes is sent cut after the edited
   declaration, since nothing after it can change (164 of 237 declaration edits; statement changed,
   `def`, `instance`, `axiom` → whole file). `lean_verify(code=…)` uses one scratch document per
   distinct header with the body replaced, Kimina's header caching inside one server. Keep the
   engine's `#print axioms` / sorry checks by appending the command. Same response shape, so the
   tools' contracts do not move. The checker kind goes into the run plan (it changes compile output).
2. **Reviewed workspaces as overlays, not copies.** 143 of 81,821 build files (11 MB of 2.8 GB)
   differ from base; `lean --setup` with the base's artifacts and the rebuilt modules repointed
   reproduced 33337's reviewed compile message for message, where base alone gives the three
   `Unknown constant` errors. Prebuild then costs the targeted build (67 s on 33337) instead of
   144–997 s and 2.8 GB per PR, which matters for the validation and test sets' reviewed workspaces,
   still open in `eval-set-selection.md`. The build side is untested: Lake over a build tree of
   symlinks with only the to-be-rebuilt artifacts real, or `lean --setup … -o` per module in order.
3. **No lake and no NFS on the hot path.** `lake setup-file` once per file, then `lean --setup`.
   This also fixes a fidelity gap: the cold path never applies Mathlib's `autoImplicit false`,
   `maxSynthPendingDepth 3`, `pp.unicode.fun` or linter options, which the setup data carries.
   Stage the read-only closure on tmpfs or `/data/local` keyed by base commit: imports load in 2.5 s
   against 7.5–8.7 s. This speeds up whatever stays cold: server opens, the evidence chain, builds.

**Start here**
- read: `results/pr_review_v5/probes/lean-build-2026-10-03/README.md` (every number above);
  `src/ape/tasks/lean_tasks/formal_math/review/base.py` (`_register_lean_verify_edit`,
  `_edited_file_code`, `_baseline_errors`, `_attribute_errors`);
  `src/ape/toolkits/execute/lean/tools.py` (`LeanVerifyToolsProvider.execute`, the response shape);
  `src/ape/toolkits/execute/lean/core/verification.py` (the cold engine, axiom/sorry checks);
  `src/ape/toolkits/code/lean/provider.py` (the existing per-session `LeanLSPClient`, called
  synchronously inside async tools); `src/ape/toolkits/execute/lean/core/build_manager.py:556`
  (`_materialize_build_tree`, the copy the overlay replaces)
- run: the probe README's `replay_bench.py` / `analyze.py` commands (no spend, ~45 min)
- bounded by: `docs/dead-ends.md` "Snippet verification of findings" (why reviewed workspaces exist;
  hardlinks fail because Lean truncates `.ilean` in place; the overlay never writes the base);
  `docs/research/reviewed-workspaces.md` (an unchanged file importing an unrebuilt dependent can load
  a stale `.olean`, the same with an overlay); `wall-clock-arm-runtime.md` (NFS, not file count,
  is what makes `content_search` slow); branch `review-designs` `7f16d971` (a submitted edit the
  reviewer already compiled is not compiled again, complementary); branch `hygiene-layer`
  `f09e8135` (Claude Code aborts an MCP call after 300 s of silence)

**Evidence** — `results/pr_review_v5/probes/lean-build-2026-10-03/` (`replay.jsonl`,
`replay_analysis.txt`, `compile_times.txt`); `verification.py:310` (the `lake env lean` command)

**Risk** — Memory: a server is ~1 GB plus 1.6–1.8 GB per open file (mostly shared mmap); at 16
concurrent arms, 30–50 GB. One server per workspace shared by a run's arms would save the 1 GB
reference index per session, at the cost of isolation. Per-edit time still depends on position, so
an early edit in an elaboration-heavy file stays slow (ContinuousAlgEquiv up to 28 s); truncation
covers only theorem edits. The truncation rule must be exactly right, or a statement change will
read as compiling. `leanclient` is synchronous, so the calls belong in `asyncio.to_thread`. Compile
output changes with Mathlib's options, so findings are not byte-comparable with recorded runs on
compile text.
