"""The whole-PR reviewer: one agent, the entire diff, no work units and no arms.

Two properties carry the experiment and are pinned here.

**It must not inherit the work-unit submission contract.** `LeanPRReviewV4CandidateTask`
enforces `change_ids` drawn from the unit, subject equality and entity membership -- a
vocabulary the baseline is deliberately never given. Inheriting it would smuggle the
decomposition into the condition that exists to do without it, and the resulting number would
be a measurement of a half-decomposed reviewer that nobody proposed.

**It must be scaffold-agnostic.** The same task runs under `ape_agent` and `claude_code`, so
those two conditions differ only in the harness and send byte-identical prompt text. That is
what makes the harness contrast interpretable at all; a whole-PR-vs-work-unit contrast cannot
have byte-identity, so this is the only place the invariant of commit 43e9d88 survives.
"""

from __future__ import annotations

import pytest

from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.review import (
    SOLO_TASK_TYPE, SoloReviewData, SoloReviewTask,
)


def _data(**overrides):
    payload = dict(
        task_id="solo-1", pr_number=33098, pr_title="feat: minimal covers",
        pr_description="A description.", diff="--- a/Mathlib/A.lean\n+++ b/Mathlib/A.lean\n",
        changed_files=["Mathlib/A.lean"], episode_id="ep:33098",
        invocation_id="ep:33098#solo_agent",
        target_workspace=WorkspaceInfo(name="target", commit_hash="c" * 40, repo_url="x"),
    )
    payload.update(overrides)
    return SoloReviewData(**payload)


def test_the_task_type_is_registered_and_keeps_its_v5_spelling():
    """A task type is a recorded identity, not a class name -- see the package `__init__`."""

    assert SOLO_TASK_TYPE == "lean_pr_review_v5_solo"
    assert get_task_class(SOLO_TASK_TYPE) is SoloReviewTask


def test_it_does_not_inherit_the_work_unit_submission_contract():
    names = [cls.__name__ for cls in SoloReviewTask.__mro__]
    assert "BasePRReviewTask" in names
    assert "LeanPRReviewV4CandidateTask" not in names, (
        "the baseline would be handed the change-id vocabulary it exists to do without")


def test_its_data_carries_a_pr_and_an_episode_but_no_work_unit():
    data = _data()
    assert data.pr_number == 33098
    assert data.episode_id == "ep:33098"
    for smuggled in ("work_unit_id", "change_ids", "primary_subjects_by_change",
                     "rendered_user_prompt"):
        assert smuggled not in type(data).model_fields, smuggled


def test_the_prompt_names_the_pr_the_diff_and_the_submit_tool():
    """`create_user_prompt` fills a fixed set of placeholders; a template naming one it does
    not supply raises at run time, on a paid run, after the workspace is built."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_SYSTEM, SOLO_USER

    rendered = SOLO_USER.format(
        pr_number=1, title="t", description="d", diff="DIFFBODY", changed_files="  - `a`",
        tool_summary="none (diff only)", submit_tool_name="submit_findings", budget=20,
    )
    assert "DIFFBODY" in rendered and "submit_findings" in rendered
    assert "maintainer" in SOLO_SYSTEM


def test_the_prompt_asks_for_a_path_and_a_line_because_anchoring_depends_on_it():
    """The baseline is judged by resolving `file:line` onto change targets. A prompt that does
    not ask for a location produces findings that cannot be anchored, and an unanchored finding
    is a measured loss -- so this is the one prompt requirement the scoring chain depends on."""

    from ape.tasks.lean_tasks.formal_math.review.solo import SOLO_USER

    assert "path" in SOLO_USER and "line_start" in SOLO_USER


def test_the_result_takes_its_episode_from_the_data_not_the_model():
    """The arms' rule, for the arms' reason: an identity the model can state is one it can get
    wrong, and every downstream join is keyed on it."""

    import inspect

    source = inspect.getsource(SoloReviewTask.create_result)
    assert "self.data.episode_id" in source


def test_the_task_is_scaffold_agnostic():
    """No *executable* line may name a scaffold. The two baseline conditions are this one task
    under two scaffolds, so a scaffold-specific branch here would silently make the harness
    contrast a prompt contrast as well -- and the prompt text is part of the executable source,
    so a scaffold named in either would do it.

    Docstrings are excluded deliberately: this module's docstring explains *why* it must run
    under both, which is the opposite of a violation. Comments never reach the AST.
    """

    import ast
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import solo

    tree = ast.parse(inspect.getsource(solo))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    executable = ast.unparse(ast.fix_missing_locations(tree))
    for scaffold_type in ("ape_agent", "claude_code", "codex"):
        assert scaffold_type not in executable, scaffold_type


# --- the contract the retrieval tools read off task.data ------------------------------------


def _attributes_the_context_tools_read():
    """Every `task.data.<attr>` in `context_tools.py`, read off the AST rather than listed."""

    import ast
    import inspect

    from ape.tasks.lean_tasks.formal_math.review import context_tools

    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(context_tools))):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
                and node.value.attr == "data"
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "task"):
            names.add(node.attr)
    return names


def test_the_solo_task_satisfies_the_contract_the_context_tools_read():
    """Granting a tool is not the same as being able to call it.

    The tools read attributes straight off `task.data` while building their trace row, and
    that happens *before* the best-effort trace write can swallow anything -- so a missing
    field is not a missing trace, it is an exception returned to the agent as the tool's
    result. Measured on the first paid run: `invocation_id` was absent, and all 3 retrieval
    calls the agent made came back as
    `'SoloReviewData' object has no attribute 'invocation_id'`. The run still closed
    `complete` with findings on disk, so nothing downstream could tell that the condition had
    reviewed the PR with its retrieval grant silently revoked.

    Derived from the AST rather than a hand-written list, so the next attribute added to a
    context tool fails here instead of in a paid run.
    """

    required = _attributes_the_context_tools_read()
    assert "invocation_id" in required, "the AST scan found nothing; the guard is vacuous"

    missing = sorted(name for name in required
                     if name not in SoloReviewData.model_fields)
    assert not missing, (
        f"the solo task grants context tools but its data lacks {missing}; every call to "
        f"them would return an AttributeError to the agent as a tool result")


def test_the_retrieval_grant_is_traceable_or_it_cannot_be_audited():
    """Two things depend on the trace existing, and both are load-bearing for this experiment:
    the fairness invariant that every condition saw the same sources under the same gate, and
    the leak audit's temporal check that each row carries a non-null `gate` and an `as_of` at
    or before the cutoff. An untraced retrieval grant is unverifiable in both directions."""

    fields = SoloReviewData.model_fields
    assert "trace_path" in fields and "retrieval_cutoff" in fields
