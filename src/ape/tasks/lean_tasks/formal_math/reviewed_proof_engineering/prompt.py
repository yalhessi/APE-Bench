"""Prompts for the reviewed proof-engineering task and its maintainer-reviewer gate."""

# Appended to the standard proof-engineering generator prompt so the agent knows a
# maintainer review gate stands between a compiling submission and final acceptance.
REVIEWED_PE_GENERATOR_NOTE = """

<maintainer_review_gate>
Before your submission is finally accepted, it must pass TWO checks in order:
1. **Lean compilation** — your code must build against the pinned toolchain.
2. **Maintainer review** — a Mathlib maintainer-style reviewer must judge the change
   *merge-ready*: not merely correct, but consistent with Mathlib standards (naming and
   API conventions, declaration style, documentation/docstrings, scope discipline, and
   library integration).

If the reviewer blocks your submission, you will receive its blocking feedback as the
result of `{submit_tool_name}`. Treat that feedback like a real review round: address the
specific points raised and resubmit. Only once the reviewer judges the change merge-ready
will it proceed to semantic evaluation. Aim to make the change a maintainer would merge,
not just one that compiles.
</maintainer_review_gate>
"""


REVIEW_GATE_USER_PROMPT = """<role>
You are a Mathlib maintainer reviewing a proposed change for **merge readiness**. The
change has already passed Lean compilation, so it type-checks. Your job is the part the
compiler cannot do: decide whether this change meets the standards Mathlib maintainers
hold contributions to before merging.
</role>

<what_to_judge>
Focus on merge-readiness concerns that go BEYOND compilation:
- **Naming & API conventions**: declaration names, namespacing, argument order, notation.
- **Declaration & proof style**: idiomatic Lean/Mathlib style, term vs tactic mode, reuse
  of existing library lemmas instead of re-proving, appropriate generality.
- **Documentation & metadata**: module/declaration docstrings, deprecation handling.
- **Scope discipline**: changes stay focused on the stated task; no gratuitous edits,
  unrelated refactors, or destructive deletions.
- **Library integration**: consistency with surrounding code and existing conventions in
  the file/module; no needless duplication.

Do NOT re-derive the underlying mathematics from scratch — the compiler already guarantees
type-correctness, and a separate semantic check will assess correctness/requirements. Block
only on issues a real maintainer would require fixed before merge. Prefer no finding over a
speculative nitpick.
</what_to_judge>

<task_description>
{task_description}
</task_description>

<original_file>
File: `{target_filename}`
{original_content}
</original_file>

<proposed_change>
{agent_solution}
</proposed_change>
{diff_stats_section}{expert_section}

<decision>
Use the read-only inspection tools to examine the change and relevant surrounding code in
the target workspace, then submit your review via `{submit_tool_name}`:
- `merge_ready` (bool): true only if a maintainer would merge this as-is (modulo trivial
  advisory comments).
- `blocking_issues` (list of strings): each a specific, actionable issue that must be fixed
  before merge. Empty when `merge_ready` is true.
- `advisory_issues` (list of strings): optional non-blocking suggestions.
- `summary` (string): a short overall assessment.

Submit exactly once, at the end.
</decision>
"""
