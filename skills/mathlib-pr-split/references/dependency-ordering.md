# Dependency Ordering

Use `depends_on` to represent prerequisite order between chunks.

Rules:
- Dependencies must point only to earlier logical prerequisites.
- Keep the dependency graph acyclic.
- If two later chunks share one prerequisite hunk, assign that hunk to the prerequisite chunk once and let both later chunks depend on it.
- Do not duplicate units to make two chunks independently buildable in the abstract. The task expects each unit exactly once.

Ordering heuristics:
- Put mechanical preparation first.
- Put new shared lemmas or helper declarations before chunks that consume them.
- Put metadata-only follow-up cleanup last unless it is required to understand the earlier chunk.
- Prefer a short dependency chain over a wide graph when both are equally coherent.
