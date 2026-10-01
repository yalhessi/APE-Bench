# A static analysis pass: what Mathlib cares about that a check can decide, on the reviewed state and on every edit

**Status** — open, 2026-10-01, **next up after the hygiene layer's re-baseline**
(`docs/plans/2026-10-01-beyond-the-solo-baseline.md` §4, Layer 1). The user (2026-10-01): *"The
idea of running the linter with lean_verify_edit is a very good one. We should consider expanding
this into a static analysis pass that captures what Mathlib cares about that could be captured
with a static analysis. This would mean these checks run with the edits as well ensuring the code
remain acceptable."* The first slice is in: every whole-file compile in a review task runs
`linter.mathlibStandardSet` (`0a3d7d33`).
**Cost** — compute only for the pass itself (compiles and `lake exe` runs in the reviewed
workspaces); one judged dev rep (a subscription window) to read it against the hygiene baseline.

**Motivating examples**, all measured:
- **A long line nobody's tool could see.** The maintainers asked to wrap a 101-character line
  (d0041). `lean_verify_edit` compiled the file and reported `warnings: []`, because `lake env
  lean` on a standalone file reads none of the lakefile's `leanOptions`; the one reviewer that found
  it compiled a snippet with `set_option linter.style.longLine true` by hand
  (`results/pr_review_v5/probes/transcript-inspection-2026-09-30/`). 33305's blocking obligation
  `cc44bb99`, "wrap the over-long doc-comment line", was located by neither the lead nor the solo
  condition in six reps and is hit by every Opus 5.x cell since.
- **An ask every session reaches, and a tool decides.** 43167's "remove the unused import" is the
  one post-cutoff ask reached by every reviewer in every harness
  (`harness-postcutoff-2026-10-01`); `lake exe shake` answers it without a model.
- **A fifth of the residual is one compile away.** Of the 67 asks no reviewer or only Claude
  reaches, 19 are `try_it_not_tried`: "can `positivity` do this", "`simpa using h`", "does the old
  proof still work", the `grind` golfs (`phase1-residual-mechanisms-2026-09-30/mechanisms.md`).
  The closer battery produced 8 of 15 such asks outright (`closer-battery-2026-09-26`), and
  Mathlib ships the same procedure as linters: `linter.tacticAnalysis.terminalToGrind`,
  `tryAtEachStepGrindSuggestions`, `tryAtEachStepSimpAllSuggestions`, `rwMerge`, `introMerge`.
- **The check is cheap.** The standard set fires on a standalone compile in a reviewed workspace
  with one `-D` option, at no measurable cost (checked 2026-10-01; `WHOLE_FILE_OPTIONS` in
  `src/ape/tasks/lean_tasks/formal_math/review/base.py`).

**What Mathlib ships that a pass could run**, read in the reviewed workspace at
`c2a50c83…+9ba5fc6ff7b4` (`lakefile.lean`, `Mathlib/Init.lean`, `Mathlib/Tactic/Linter/`,
`Mathlib/Tactic/TacticAnalysis/`, `.lake/packages/batteries/lakefile.toml`):
1. **The standard syntax linter set** (`linter.mathlibStandardSet`, on in CI): `flexible`,
   `hashCommand`, `oldObtain`, `privateModule`, `unusedDecidableInType` and `style.{cases, induction,
   refine, commandStart, cdot, docString, dollarSyntax, emptyLine, header, lambdaSyntax, longLine,
   longFile, multiGoal, nativeDecide, openClassical, missingEnd, setOption, show, maxHeartbeats}`.
   **Already on** for every edit and as-is compile (`0a3d7d33`).
2. **Opt-in syntax linters**, off by default and each a known maintainer concern: `docPrime`,
   `haveLet`, `minImports`, `globalAttributeIn`, `dupNamespace`, `ppRoundtrip`, `style.nameCheck`,
   `upstreamableDecl`, `unusedTactic`, `directoryDependency`, `deprecated.module`.
3. **Core's own**: `linter.unusedVariables`, `linter.unusedSimpArgs`, `linter.unnecessarySimpa`,
   deprecation warnings.
4. **The tacticAnalysis set** (`terminalToGrind`, `tryAtEachStep{Grind,SimpAll,Aesop,FromEnv}` with
   their `Suggestions` variants, `rwMerge`, `introMerge`, `omegaToLia`, `mergeWithGrind`), plus
   the `nightlyRegressionSet`: the try-it class as linters, each re-elaborating steps, so minutes
   per file rather than seconds.
5. **Environment linters** (Batteries' `#lint`, driver `lake exe runLinter`): `docBlame`,
   `unusedArguments`, `simpNF`, `defLemma`, `dupNamespace`, `nonClassInstance`,
   `impossibleInstance`, and the rest of `Batteries/Tactic/Lint/`. These need the module built,
   which the reviewed workspaces are.
6. **`lake exe shake`** for unnecessary imports; **`lake exe lint-style`** for the text-based checks
   (header, whitespace, file length); `lake exe unused` for transitively unused imports.

**The design, three uses of one pass.** Each hit is a deterministic evidence line, keyed to the
line and the declaration it is on, with the check's name and its own "how to fix" text:
- **a packet section** (Layer 1): what CI and the linters say about the reviewed state, restricted to
  the PR's changed lines so a pre-existing hit is never charged to the PR;
- **a gate on every edit**: `lean_verify_edit` already reports the standard set's hits an edit
  introduces (`warnings_introduced_by_your_edit`); the pass widens that to the checks above, so a
  golf that leaves an unused `simp` argument or a deprecated name is refused as "acceptable to
  Lean, not to Mathlib";
- **a finder for the mechanical subset**: a hit that *is* an ask (an unused import, a long line, an
  unnecessary `simpa`, a terminal `grind`) is filed by the pass with its evidence and no model
  turn, as the closer battery's eight were.

**Bounded by.** `docs/dead-ends.md`, "Linter-as-convention-oracle": a linter is a step function
and dates *availability*, not a convention; it is a `stated` source only, never the oracle. This
pass is the use that entry permits, a check on the code with the linter's own "How to fix this?"
text as the extractor, and it never says what the convention is. A `terminalToGrind` suggestion
is advisory while `grind` adoption is 14.5% and contested; the pass carries each check's maturity
(standard set, opt-in, regression-only) and files the opt-in and tacticAnalysis hits as advisory.
And the pass files; it does not rank or filter what the reviewer files (the 2026-09-22 ruling).

**What would close it.**
1. **The ceiling, free.** Label the validation round-1 asks (`results/pr_review_v5/adjudications/
   facet-relabel-val1000-v1/`, 506 asks; or the arm-coverage set) by whether a check in the list
   above would fire on the reviewed state, two blind readers, by family. The share is what the
   pass can reach by construction; the hypothesis from Phase 1 is the mechanical 15-25%.
2. **The pass, measured alone.** One module (beside `src/mathlib_review/evidence/`, where the
   collectors live; no new package) that runs the checks over a reviewed workspace's changed files
   and writes hits as evidence rows. Run it on the dev 15 and validation small12, match its hits
   against the gold obligations and the asks, and report the pair: asks reached by the pass alone,
   and hits on the two control PRs (33304, 33315) and the no-ask validation PRs, which is its
   false-positive floor at zero model cost.
3. **In the harness.** The packet section and the edit gate, then one judged dev rep against the
   hygiene baseline under Layer 1's rule (≥ 4 of the ten never-hit dev obligations, ≥ 10 of the 44
   knowledge and try-it asks, control emission unchanged).

**Start here.**
- read: `src/ape/tasks/lean_tasks/formal_math/review/base.py` (`WHOLE_FILE_OPTIONS`,
  `_attribute_errors`, the baseline cache), `results/pr_review_v5/probes/closer-battery-2026-09-26/README.md`
  (which procedures produced asks outright), `results/pr_review_v5/probes/phase1-residual-mechanisms-2026-09-30/mechanisms.md`
  (the 19 try-it asks), `docs/dead-ends.md` "Linter-as-convention-oracle", and in a reviewed
  workspace `Mathlib/Init.lean` (the standard set), `Mathlib/Tactic/TacticAnalysis/Declarations.lean`.
- run, in a reviewed workspace, no spend:
  `lake env lean -Dweak.linter.mathlibStandardSet=true --json Mathlib/<changed>.lean`;
  `lake env lean -Dweak.linter.tacticAnalysis.terminalToGrind=true --json Mathlib/<changed>.lean`;
  `lake exe shake Mathlib.<Changed>`; `lake exe runLinter Mathlib.<Changed>`.
- bounded by: the dead-ends entry above; the selection ruling; Layer 1 of the plan, whose closer
  battery and mechanism catalogue this pass joins rather than replaces.

**Evidence** — `0a3d7d33` (the standard set on whole-file compiles, with the measurement);
`results/pr_review_v5/probes/claude-models-2026-10-01/tool_outcomes.py` (no linter warning in 313
`lean_verify_edit` results before it); `closer-battery-2026-09-26/outcomes.json`;
`phase1-residual-mechanisms-2026-09-30/mechanisms.py`.

**Risk** — a hit is not an ask: the opt-in and tacticAnalysis checks fire on code maintainers
accept, and the standard set fires on pre-existing lines a PR did not touch (restrict to the diff,
and split against the baseline as the edit gate does). The tacticAnalysis checks cost minutes per
file; the pass must run once per reviewed state, cached like the baseline compile, not per edit.
`runLinter` and `shake` need the module's build products, so the pass depends on the reviewed
workspace being prebuilt, as every run already requires. And the share it can reach is bounded by
the mechanical fraction of asks; the ten never-hit dev obligations are mostly convention and design,
which no check decides.
