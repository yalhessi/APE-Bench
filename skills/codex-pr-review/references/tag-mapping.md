# APE-Bench Tag Mapping

Only use this file when the task explicitly asks for APE-Bench PR-review issue tags.

## Core tags

- `semantic_incorrectness`
  Use for wrong statements, wrong proofs, unsound assumptions, or mathematically incorrect code.

- `requirement_mismatch`
  Use when the PR does not actually deliver the intended result, interface, or user-facing change.
  This includes cases where the implementation is correct but the reviewer clearly wants a
  different abstraction, theorem shape, or PR focus before merge.

- `scope_control_violation`
  Use when the PR expands beyond the intended scope with unrelated refactors, broader API work, or
  changes that should be split into follow-ups.

- `proof_fragility`
  Use when the proof or implementation is brittle enough that maintainers would plausibly ask for a
  more robust approach before merge.

- `insufficient_documentation`
  Use for missing or weak docstrings, citations, warnings, or proof comments when documentation is
  the important issue.

- `insufficient_tests`
  Use when missing validation is a real risk. In Mathlib this is less common than in ordinary
  software review, but it can still apply to generated code, performance checks, or toolchain
  behavior.

- `library_integration_issue`
  Use for wrong file placement, bad imports, missing essential API lemmas or attributes, dangerous
  instances, downstream breakage risk, or naming/API choices that are poor fits for Mathlib.

- `deprecated_api_usage`
  Use when the PR relies on deprecated declarations or introduces avoidable deprecation churn.

- `performance_regression`
  Use when the change plausibly harms elaboration time, simp behavior, generated code size, or
  other meaningful performance properties.

- `style_or_readability`
  Use for non-blocking naming, formatting, tactic-style, or readability suggestions.

## Tie-breakers

- If a naming comment is serious enough that reviewers would reject the API as a bad library fit,
  prefer `library_integration_issue` over `style_or_readability`.
- If a style complaint is actually about breakage, wrong abstraction, or hidden scope expansion, do
  not reduce it to a pure style tag.
- If you are unsure whether a point is blocking, keep the explanation explicit and prefer the
  weaker tag.
