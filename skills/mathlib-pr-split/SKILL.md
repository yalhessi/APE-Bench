---
name: mathlib-pr-split
description: Use when deciding whether a Mathlib pull request should be decomposed into smaller sub-PRs and how those chunks should be ordered for later independent application and review.
---

Use this skill for `lean_pr_split`, `skilled_pr_split`, and other Mathlib PR decomposition sessions.

Workflow:
1. Read `scratch/pr_context.md`, `scratch/pr.diff`, and `scratch/pr_change_units.json`.
2. In `skilled_pr_split`, complete the mandatory bootstrap before calling `submit_result`:
   - `references/splitting-guidelines.md`
   - `references/dependency-ordering.md`
   - `references/pr-metadata.md`
3. Inspect the base snapshot in `target/` when you need surrounding code or declaration context.
4. Decide first whether the PR should stay whole. If it is already coherent and reviewable, prefer `should_split=false`.
5. When splitting, aim for semantic boundaries that would still make sense if each chunk were reviewed against the PR base commit.
6. Use `depends_on` for prerequisite ordering instead of duplicating units across chunks.
7. Keep titles and summaries focused on why each chunk is a coherent future sub-PR, not just which files it touches.

Practical heuristics:
- Split preparatory refactors away from behavior-changing feature work when that makes later review easier.
- Keep declaration moves, naming cleanup, and metadata-only edits with the semantic change they explain unless they are clearly reusable prerequisites.
- Avoid tiny mechanical chunks that exist only to satisfy a target chunk count.
- Prefer chunks that a maintainer could plausibly merge independently.
- If a change only becomes understandable after another chunk lands, make that dependency explicit.
- Reuse the canonical unit IDs from `scratch/pr_change_units.json`; do not invent file ranges.

Reference files:
- `references/splitting-guidelines.md`: how to choose good split boundaries and when not to split.
- `references/dependency-ordering.md`: how to model prerequisites and chunk order without overlap.
- `references/pr-metadata.md`: Mathlib-facing guidance for chunk titles, summaries, and reviewer-readable PR framing.
