"""Tests for the guidelines-supplied review agent (no network)."""

import asyncio

import ape.tasks.lean_tasks  # noqa: F401  (triggers task registration)
from ape.tasks.base import list_task_types
from ape.tasks.lean_tasks.formal_math.pr_review_v2.guidelines import (
    guidelines_block,
    load_distilled,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.guidelines_task import (
    LeanPRReviewGuidelinesTask,
)
from ape.tasks.lean_tasks.formal_math.pr_review_v2.task import LeanPRReviewV2Task


def test_guidelines_task_registered():
    assert "lean_pr_review_guidelines" in list_task_types()


def test_distilled_loads_the_checklist_and_summaries():
    text = load_distilled()
    assert "Mathlib PR Review Checklist" in text
    for name in ("naming-conventions-reviewer.md", "style-guidelines-reviewer.md"):
        assert name in text  # each block is fenced by its filename


def test_guidelines_block_has_calibration_framing():
    block = guidelines_block()
    assert "Mathlib community review guidelines" in block
    assert "deviation from them is a finding" in block


def test_guidelines_task_appends_guidelines_to_holistic_system_prompt():
    # The guidelines agent's system prompt = the holistic agent's system prompt + guidelines.
    # create_system_prompt only reads config.task_config.prompt_version.
    from ape.tasks.lean_tasks.formal_math.review.base import BasePRReviewConfig

    async def system_prompt_for(task_cls):
        task = task_cls.__new__(task_cls)          # avoid full scaffold init
        class _Cfg:
            task_config = BasePRReviewConfig()
        task.config = _Cfg()
        return await task.create_system_prompt()

    base = asyncio.run(system_prompt_for(LeanPRReviewV2Task))
    withg = asyncio.run(system_prompt_for(LeanPRReviewGuidelinesTask))
    assert withg.startswith(base)                  # identical framing, guidelines appended
    assert len(withg) > len(base)
    assert "Mathlib community review guidelines" in withg
    assert "Mathlib community review guidelines" not in base
