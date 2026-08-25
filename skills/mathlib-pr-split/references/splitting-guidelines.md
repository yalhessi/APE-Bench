# Mathlib PR Splitting Guidelines

Use splitting only when it improves reviewability.

Good reasons to split:
- A prerequisite refactor is mixed with the main theorem or API change.
- Independent subsystems are changed in one PR and can be reviewed separately.
- Mechanical cleanup obscures a smaller semantic change.
- The diff is large enough that maintainers would struggle to reason about it as one unit.

Reasons not to split:
- The PR is already coherent and small enough to review in one pass.
- The proposed chunks would only separate adjacent lines without creating clearer semantics.
- Every chunk would still need the rest of the PR to be understandable.

Chunk boundary rules:
- Prefer one conceptual purpose per chunk.
- Keep supporting declarations with the change that needs them unless they are reusable groundwork.
- Avoid overlapping units across chunks.
- Every changed unit should appear exactly once.
- A chunk should make sense as "one future PR on top of the base commit".
