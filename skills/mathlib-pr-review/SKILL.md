---
name: mathlib-pr-review
description: Use when reviewing Mathlib pull requests, especially to apply maintainer conventions, decide merge readiness, and map findings to the PR review benchmark issue tags.
---

Use this skill for `lean_pr_review`, `skilled_pr_review`, and Mathlib PR review sessions.

Workflow:
1. Read `scratch/pr_context.md` and `scratch/pr.diff`.
2. In `skilled_pr_review`, complete the mandatory guide bootstrap before forming a final judgment or calling `submit_result`:
   - `references/pr-review-guide-reviewer.md`
   - `references/naming-conventions-reviewer.md`
   - `references/documentation-style-reviewer.md`
   - `references/style-guidelines-reviewer.md`
3. Use `references/checklist.md` as a compact review pass after the bootstrap, not as a substitute for the guides.
4. After the bootstrap, inspect the touched code in `target/`.
5. If the review depends on PR metadata, git workflow, branch/toolchain process, or other house-style conventions, start with `references/maintainer-guides.md`. Open the relevant `*-reviewer.md` file first, then consult the matching `*-official.md` file only when you need canonical wording or more examples.
6. Convert every finding into the benchmark schema using `references/tag-mapping.md`.
7. In `skilled_pr_review`, every guide-backed judgment must be supported by reading the matching guide file and declaring its topic in `guide_evidence_topics` when calling `submit_result`.
8. Treat `submit_result` as final-only. Do not use it to discover which guides are still missing.
9. Only mark the PR as not merge ready when there is a genuinely blocking issue. Non-blocking polish should stay advisory.

Practical heuristics:
- The benchmark is about merge readiness, not whether the PR could be rewritten in a nicer way.
- Prefer evidence from the diff or surrounding declarations over generic preferences.
- Avoid style-only objections unless the maintainer guides make the convention important enough to block.
- If reviewer guidance is ambiguous, explain the uncertainty briefly and default to the least overconfident tag choice.

Guide evidence topics for `skilled_pr_review`:
- `review_norms`: `references/pr-review-guide-reviewer.md` or `references/pr-review-guide-official.md`
- `naming`: `references/naming-conventions-reviewer.md` or `references/naming-conventions-official.md`
- `documentation`: `references/documentation-style-reviewer.md` or `references/documentation-style-official.md`
- `style`: `references/style-guidelines-reviewer.md` or `references/style-guidelines-official.md`
- `pr_metadata`: `references/commit-conventions-reviewer.md` or `references/commit-conventions-official.md`
- `git_workflow`: `references/git-guide-reviewer.md` or `references/git-guide-official.md`
- `branches_ci`: `references/tags-and-branches-reviewer.md` or `references/tags-and-branches-official.md`

Required topics in `skilled_pr_review`:
- `review_norms`
- `naming`
- `documentation`
- `style`

Reference files:
- `references/checklist.md`: short review checklist tuned to this benchmark.
- `references/tag-mapping.md`: how Mathlib-style review comments map to the allowed issue tags.
- `references/maintainer-guides.md`: index of the maintainer-guide references collected for this skill.
- `references/naming-conventions-reviewer.md`: reviewer-focused summary of Mathlib naming conventions.
- `references/naming-conventions-official.md`: canonical-source reference for the official naming conventions guide.
- `references/documentation-style-reviewer.md`: reviewer-focused summary of Mathlib documentation conventions.
- `references/documentation-style-official.md`: verbatim official documentation style guide.
- `references/style-guidelines-reviewer.md`: reviewer-focused summary of Mathlib library style and compatibility conventions.
- `references/style-guidelines-official.md`: verbatim official library style guide.
- `references/pr-review-guide-reviewer.md`: reviewer-focused summary of Mathlib review norms.
- `references/pr-review-guide-official.md`: verbatim official Mathlib review guide.
- `references/commit-conventions-reviewer.md`: reviewer-focused summary of PR title and description rules.
- `references/commit-conventions-official.md`: verbatim official PR title and description guide.
- `references/git-guide-reviewer.md`: reviewer-focused summary of contributor git workflow.
- `references/git-guide-official.md`: verbatim official git workflow guide.
- `references/tags-and-branches-reviewer.md`: reviewer-focused summary of Lean/Mathlib branch and CI conventions.
- `references/tags-and-branches-official.md`: verbatim official Lean/Mathlib branch and tag guide.
