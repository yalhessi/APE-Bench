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
4. Identify blocking issues vs advisory suggestions.
5. Submit your final decision via `{submit_tool_name}` only once, at the end. Do not use it to probe which prerequisites are still missing.

Do not implement changes. Your role is reviewer only.
</submission_strategy>

{managed_skill_guidance}

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
