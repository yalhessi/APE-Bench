# PR #29513 — notes on the PR as a change (reviewer P2)

1. **Wanted?** Yes. At base, `toLeanOptions` (the helper that strips `weak.`) was dead code: line 71 called `Lean.LeanOptions.toOptions`, so `weak.linter.mathlibStandardSet` was never resolved. As a result `checkInitImports` and `allScriptsDocumented` (both default false) never ran. Searches found no existing `ToExpr` for NameMap/TreeMap/RBMap and no existing compile-time capture of linter sets, so nothing is duplicated. The new elaborator is used once, but it cannot really be inlined: it is an elaborator. No finding.

2. **Every hunk an improvement?** Every hunk serves the fix. Rewriting `toLeanOptions` from a `foldl` into an `Id.run do`/`for` loop is partly a preference: `NameMap` has `foldl`. But the signature change forces the edit anyway, so I did not file it. Removing the first `initSearchPath` is safe because a second call remains before `findWithExt` (base line 193). No finding.

3. **One thing?** The two fixes (option parsing, linter-set loading) are both needed for a single outcome: the standard set enabling the script checks. They touch one file, and the title names both. No finding.

4. **Description?** It is empty. It has no motivation, no statement of which checks were silently off, no rationale for choosing compile-time `linter_sets%` over fixing the runtime import, no links and no AI statement. Filed as blocking.

5. **Finishes the job?** There is no analogous site: only scripts/lint-style.lean turns Lake options into `Lean.Options`. `check-yaml` uses `CoreM.withImportModules` but reads only `constants`, not an extension. The new meta code and the fixed parsing have no test, although the `#guard` precedent in scripts/autolabel.lean exists. Filed as advisory. Unrelated and not filed: in Mathlib/Tactic/Linter/TextBased.lean:397, `modulesForbiddenWindows` is gated on `linter.modulesUpperCamelCase`.

6. **Right place?** The generic orphan `ToExpr (NameMap α)` instance, with its type hard-coded to `LinterSets`, sits in a script. Mathlib/Tactic/ToExpr.lean is the home for core-type `ToExpr` instances. Filed as advisory: narrow the instance, or move it there. The `linter_sets%` elaborator is fine in the script, since it captures sets at its use site.
