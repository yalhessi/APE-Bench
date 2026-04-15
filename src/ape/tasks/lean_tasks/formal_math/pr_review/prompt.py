"""
PR review task prompts.

Provides prompt templates for merge-readiness review of Mathlib pull requests.
"""

LEAN_PR_REVIEW_USER_PROMPT = """<objective>
Review the pull request like a Mathlib maintainer and decide whether it is ready to merge.
Your review must be precise, evidence-based, and focused on merge readiness.
</objective>

<submission_strategy>
1. Inspect the PR metadata and diff.
2. If the task specifies required guide reads or other review prerequisites, complete them before forming policy or quality judgments.
3. Use tools to inspect changed files and relevant surrounding code in the target workspace. The target workspace already has the PR patch applied at the review snapshot.
4. Mirror the exact submission shape from `{submission_schema_path}` and use `{submission_example_path}` as a filled example.
5. Identify blocking issues vs advisory suggestions, and attach structured evidence to each finding.
6. Submit your final decision via `{submit_tool_name}` only once, at the end. Include merge readiness, whether the case needs human review, an optional confidence score, and evidence-backed findings. Do not use it to probe which prerequisites are still missing.

Do not implement changes. Your role is reviewer only.
</submission_strategy>

{managed_skill_guidance}

<submission_contract>
- Mirror the field names and nesting from `{submission_schema_path}` exactly.
- Use `{submission_example_path}` only as a structural example; do not copy its substantive claims.
- Each finding must include at least one code-local anchor in `diff_locations`, `referenced_files`, or `referenced_declarations`; guide citations alone do not satisfy the evidence requirement.
- `diff_locations.file_path` must be a repo-root file path from the PR, not `scratch/pr.diff`.
- Every `diff_locations.file_path` must point to a changed file from this PR.
- `diff_side` must be `old` or `new`.
- `referenced_declarations` entries must be objects with `name`.
- `guide_citations` entries must use `topic` and `relative_path`.
- Do not invent alternate keys like `path`, `file`, `declaration`, `title`, `quote`, or `comment`.
</submission_contract>

<pr_metadata>
PR: {pr_display}
Title: {pr_title}
Author: {pr_author}
Dependencies:
{pr_dependencies}
Changed files ({changed_files_count}):
{changed_files_list}
</pr_metadata>

<snapshot_metadata>
{snapshot_context}
</snapshot_metadata>

<review_focus>
{review_focus}
</review_focus>

<pr_description>
{pr_description}
</pr_description>

<pr_diff_summary>
Full diff is available at `scratch/pr.diff` (read-only) for review context.
Preview:
{pr_diff_preview}
</pr_diff_summary>

<finding_taxonomy>
Use these finding categories when reporting issues:
{finding_categories}
</finding_taxonomy>

<evaluation_policy>
- "Merge ready" means no blocking correctness/scope/library-integration issues remain.
- Advisory suggestions should not block merge.
- Prioritize mathematical correctness, requirement alignment, and scope control.
- Avoid style-only nitpicks unless they reflect real Mathlib policy violations.
</evaluation_policy>
"""
