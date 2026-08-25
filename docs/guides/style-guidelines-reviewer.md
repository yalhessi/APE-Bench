# Library Style Guidelines For Reviewers

Use this file when a PR review depends on file structure, theorem formatting, imports, tactic style,
API design, deprecations, or other library-wide code conventions.

Derived from the official Mathlib library style guide.

## Core layout rules

- Files should stay within the 100-character line limit.
- The header should contain copyright information, `Authors`, `module`, grouped `public import`s,
  grouped `import`s, and then a module docstring.
- Imports should stay alphabetical within their blocks when practical.
- Module docstrings should summarize the file, mention notation, and include references when useful.

## Declaration formatting

- Top-level commands stay flush-left, even inside namespaces or sections.
- Use spaces around `:`, `:=`, and infix operators.
- In multiline theorem statements, continuation lines are indented; proofs are still indented by
  two spaces and typically start with `:= by`.
- Give explicit argument types and return types.
- Structure and class fields should be indented by two spaces and should have docstrings.
- Instance definitions should prefer `where` syntax.
- Hypotheses to the left of the colon are preferred when the proof immediately introduces them.

## Proof style

- Prefer `fun ... ↦ ...` over `λ`.
- `calc` chains should be aligned and easy to edit.
- In tactic mode, `by` should appear at the end of the previous line, not on a line by itself.
- Use `·` or named `case`s for subgoals; keep semicolon-heavy tactic scripts limited to short,
  local situations.
- Avoid squeezing terminal `simp` calls unless performance or robustness requires it.

## Maintenance and API concerns

- Performance matters when a PR adds new classes, instances, `simp` lemmas, imports, or important
  definitions; such PRs should be benchmarked proactively.
- The default expectation is that definitions stay `semireducible`. A PR should justify unusual
  transparency choices.
- If proofs need `erw` or extra `rfl` after `simp` or `rw`, that often signals missing API lemmas.
- Prefer normal forms that match established Mathlib conventions.
- Use `<|` rather than `$`, and include a space after `←` in `rw` and `simp`.
- Empty lines inside declarations are discouraged; comments are preferred when structure is needed.

## Compatibility conventions

- Publicly exposed renamed or removed declarations should usually carry `@[deprecated]` guidance,
  including a date and either an alias or migration message.
- Deprecated declarations can typically be deleted after six months.
- Avoid `nonrec` when explicit namespace qualification would be clearer.

## Review use

- Clear violations affecting maintenance, imports, API boundaries, deprecation hygiene, or
  performance expectations can justify blocking comments.
- Purely local formatting nits are usually advisory unless the PR repeatedly ignores entrenched
  Mathlib style.
