# Tag Mapping For `lean_pr_review`

Map review findings to the benchmark tags conservatively.

## Blocking-oriented tags

- `semantic_incorrectness`
  Use for wrong proofs, wrong statements, unsound transformations, invalid assumptions, or behavior that is mathematically incorrect.

- `requirement_mismatch`
  Use when the PR does not do what the title, description, or reviewer-requested goal says it should do.

- `scope_control_violation`
  Use when the PR introduces extra surface area, refactors, or policy changes outside the intended scope.

- `proof_fragility`
  Use when the proof or implementation is likely to break easily, relies on brittle patterns, or is not robust enough for merge readiness.

- `library_integration_issue`
  Use for import hygiene, naming/API integration, downstream breakage risk, or incompatibility with surrounding Mathlib structure.

- `deprecated_api_usage`
  Use when the PR relies on deprecated names or creates avoidable deprecation churn.

## Usually advisory tags

- `insufficient_documentation`
  Use for missing or weak docstrings, comments, or explanatory text when that matters but would not usually block merge on its own.

- `insufficient_tests`
  Use for missing coverage or validation when the risk is real but not obviously merge-blocking.

- `performance_regression`
  Use when the change plausibly harms performance, elaboration time, or generated code size in a meaningful way.

- `style_or_readability`
  Use for naming, theorem shape, formatting, readability, or house-style concerns that do not by themselves make the PR unmergeable.

## Tie-breaking rules

- If a naming or theorem-shape issue would actually force maintainers to request changes before merge, prefer `library_integration_issue` or `requirement_mismatch` over `style_or_readability`.
- Do not assign a blocking tag just because a reviewer suggested a nicer formulation.
- If you are unsure whether something is blocking, explain the ambiguity and prefer the weaker tag.
