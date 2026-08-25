# Mathlib Maintainer Guides

This file indexes the maintainer-guide references collected for this skill.

Use the paired files like this:

- Read the `*-reviewer.md` file first when you want a compact PR-review-oriented summary.
- Read the matching `*-official.md` file when you need canonical wording, more examples, or edge
  cases from the original guide.
- When a review question is narrow, open only the relevant pair instead of loading everything.

## Naming and theorem statement conventions

- `naming-conventions-reviewer.md`: reviewer-focused summary of the same guide, tuned to PR review.
- `naming-conventions-official.md`: canonical-source reference for the official Mathlib naming
  conventions guide.

## Documentation, comments, and presentation

- `documentation-style-reviewer.md`: reviewer-focused summary for module headers, docstrings,
  citations, and section comments.
- `documentation-style-official.md`: verbatim copy of the official documentation style guide.

## Library style, imports, API, and compatibility

- `style-guidelines-reviewer.md`: reviewer-focused summary for formatting, imports, tactic style,
  API design, performance expectations, deprecations, and `nonrec`.
- `style-guidelines-official.md`: verbatim copy of the official library style guide.

## Review norms and merge readiness

- `pr-review-guide-reviewer.md`: reviewer-focused summary of review posture, blocking-vs-advisory
  heuristics, and the main review areas.
- `pr-review-guide-official.md`: verbatim copy of the official pull request review guide.

## PR metadata and git workflow

- `commit-conventions-reviewer.md`: reviewer-focused summary for checking PR metadata.
- `commit-conventions-official.md`: verbatim copy of the official PR title and description guide.
- `git-guide-reviewer.md`: reviewer-focused summary for forks, remotes, branch workflow, and PR
  checkout advice.
- `git-guide-official.md`: verbatim copy of the official git guide for Mathlib contributors.

## Branches, toolchains, and CI

- `tags-and-branches-reviewer.md`: reviewer-focused summary for `nightly-with-mathlib`,
  `lean-pr-testing-NNNN`, `nightly-testing`, `bump/v4.X.Y`, and related CI workflow.
- `tags-and-branches-official.md`: verbatim copy of the official Lean/Mathlib branch and tag guide.
