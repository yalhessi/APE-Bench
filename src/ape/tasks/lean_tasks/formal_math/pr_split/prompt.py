"""Prompt templates for standalone Mathlib PR split tasks."""

LEAN_PR_SPLIT_USER_PROMPT = """<objective>
Decide whether this PR should be split into smaller sub-PRs. If it should, propose coherent, reviewable sub-PRs that could later be applied independently to the PR's base commit.
</objective>

<submission_strategy>
1. Read `scratch/pr_context.md`, `scratch/pr.diff`, and `scratch/pr_change_units.json`.
2. Inspect surrounding code in the base snapshot under `target/` when needed.
3. Use `scratch/split_submission_schema.json` and `scratch/split_submission_example.json` as the exact structural contract for `{submit_tool_name}`.
4. If the PR is already coherent and manageable as-is, submit `should_split=false` with a clear rationale and `chunks=[]`.
5. If the PR should be split, propose 2-6 chunks with explicit dependency order.
6. Do not implement changes. Your role is planning the split only.
</submission_strategy>

{managed_skill_guidance}

<workspace_outputs>
- The base repository snapshot is available under `target/`.
- The full PR patch is available at `scratch/pr.diff`.
- Canonical diff units are listed in `scratch/pr_change_units.json`.
- After a successful `{submit_tool_name}` call, the task writes the final plan to `scratch/submitted_split.json`.
- The task also writes structural grading details to `scratch/split_grading.json`.
- Proposed per-chunk diffs are written under `scratch/splits/`.
</workspace_outputs>

<submission_contract>
- `should_split=false` requires a non-empty `rationale` and `chunks=[]`.
- `should_split=true` requires between 2 and 6 chunks.
- Every diff unit from `scratch/pr_change_units.json` must be assigned to exactly one chunk.
- `selected_unit_ids` must come from `scratch/pr_change_units.json`; do not invent IDs.
- `depends_on` must reference other chunk IDs from the same submission and must be acyclic.
- Every chunk must have a non-empty `chunk_id`, `title`, and `summary`.
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

<change_unit_summary>
Canonical change units are available at `scratch/pr_change_units.json`.
Summary:
{change_unit_summary}
</change_unit_summary>

<pr_description>
{pr_description}
</pr_description>

<pr_diff_summary>
Full diff is available at `scratch/pr.diff` (read-only) for decomposition context.
Preview:
{pr_diff_preview}
</pr_diff_summary>

<split_policy>
- Prefer semantic cohesion over superficial file-count balancing.
- Prefer chunks that are reviewable and independently understandable on top of the base commit.
- Small prerequisite refactors may be isolated into earlier chunks when that makes later chunks cleaner.
- Avoid creating micro-PRs that exist only to satisfy a numeric split target.
- If one chunk logically depends on another, express that with `depends_on` instead of duplicating units.
</split_policy>
"""
