"""Tests for the workspace-grounded distillation task (lean_pr_review_distill) — no network."""

import ape.tasks.lean_tasks  # noqa: F401  (triggers registration)
from ape.tasks.base import get_task_class
from ape.tasks.lean_tasks.formal_math.review_task import BasePRReviewData, BasePRReviewTask
from ape.tasks.lean_tasks.formal_math.pr_review_v2.distill_task import (
    DISTILL_SYSTEM,
    DISTILL_USER,
    LeanPRReviewDistillTask,
)


def test_distill_registers_and_shares_base():
    registered = get_task_class("lean_pr_review_distill")
    assert registered is LeanPRReviewDistillTask
    assert registered.task_type == "lean_pr_review_distill"
    assert issubclass(registered, BasePRReviewTask)
    assert registered.data_class is BasePRReviewData  # no extra data needed; reuses the shared model


def test_prompt_pushes_workspace_grounding_and_discrimination():
    # the whole point of the grounded version: read the full proof, don't default to high legibility
    assert "target/" in DISTILL_SYSTEM and "full" in DISTILL_SYSTEM.lower()
    assert "discriminating" in DISTILL_SYSTEM.lower() or "do not default" in DISTILL_SYSTEM.lower()
    assert "legibility" in DISTILL_SYSTEM
    assert DISTILL_USER.format(
        pr_number=1, title="t", description="d", diff="x",
        changed_files="  - a", tool_summary="read files", submit_tool_name="submit_distillation",
    )


def test_normalize_declarations_clamps_and_drops_nameless():
    out = LeanPRReviewDistillTask._normalize_declarations([
        {"name": "foo", "legibility": 150, "nl_statement": "s"},  # clamp to 100
        {"name": "", "legibility": 50},                           # dropped (no name)
        {"name": "bar", "legibility": "bad"},                     # -> 50
        {"name": "baz", "legibility": -5},                        # clamp to 0
        "not-a-dict",                                             # skipped
    ])
    assert [d["name"] for d in out] == ["foo", "bar", "baz"]
    assert [d["legibility"] for d in out] == [100, 50, 0]
    assert out[0]["nl_statement"] == "s"
