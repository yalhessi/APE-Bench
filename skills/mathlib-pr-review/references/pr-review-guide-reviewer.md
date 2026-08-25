# Pull Request Review Guide For Reviewers

Use this file as the main reviewer-behavior guide when deciding what to comment on, how strongly to
push, and how to separate blocking issues from helpful suggestions.

Derived from the official Mathlib pull request review guide.

## Review posture

- Reviews should be respectful, encouraging, and specific.
- Even when pointing out mistakes, comments should help the author improve rather than shut the work
  down.
- Reviewers should stay humble and leave room for the possibility that their preferred approach is
  not the only good one.
- Partial reviews are still useful; newer reviewers can contribute a lot by focusing on style,
  documentation, and location even before they are comfortable judging deeper API questions.

## Main review areas

- Style: formatting, naming, and whether the PR title and description are informative.
- Documentation: useful docstrings, cross references, proof sketches in comments, warnings about
  restricted-use declarations, and references to the literature when appropriate.
- Location: correct file placement, avoiding duplicate results, keeping imports minimal, and
  splitting files when needed.
- Improvements: extracting supporting lemmas, using clearer tactics, or restructuring proofs when
  that materially improves readability or maintainability.
- Library integration: sensible attributes and API lemmas, enough generality for likely future use,
  and consistency with existing Mathlib design patterns.

## Review heuristics

- New imports can be a clue that declarations belong elsewhere or that a file boundary should move.
- Long proofs often deserve refactoring or at least comments that explain the argument.
- Long or subtle theorem statements often deserve docstrings and cross references.
- Review suggestions should prefer concrete, actionable guidance over vague criticism.

## Benchmark-oriented use

- In this benchmark, blocking findings should correspond to issues that genuinely affect merge
  readiness: broken placement, missing key documentation, incorrect or misleading metadata, harmful
  imports, poor API choices, and similar substantial concerns.
- Advisory comments should cover polish, alternative tactics, optional refactors, and nicer naming
  when the existing code would still be acceptable to merge.
