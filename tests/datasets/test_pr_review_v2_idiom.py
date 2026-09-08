"""Tests for the idiomaticity/canonicality checker (lean_pr_review_idiom) — no network."""

import ape.tasks.lean_tasks  # noqa: F401  (triggers registration)
from ape.tasks.base import get_task_class
from ape.tasks.lean_tasks.formal_math.review.base import VerifiedPRReviewTask
from ape.tasks.lean_tasks.formal_math.pr_review_v2.golf import GOLF_SYSTEM
from ape.tasks.lean_tasks.formal_math.pr_review_v2.idiom import (
    IDIOM_SYSTEM,
    IDIOM_USER,
    LeanPRReviewIdiomTask,
)

PROMPT_FIELDS = dict(
    pr_number=1, title="t", description="d", diff="x",
    changed_files="  - a", tool_summary="grep the repo", submit_tool_name="submit", budget=10,
)


def test_idiom_registers_and_is_verified():
    registered = get_task_class("lean_pr_review_idiom")
    assert registered is LeanPRReviewIdiomTask
    assert registered.task_type == "lean_pr_review_idiom"
    assert issubclass(registered, VerifiedPRReviewTask)  # kernel-gated submission


def test_idiom_is_canonicality_not_length():
    s = IDIOM_SYSTEM.lower()
    # the defining framing: canonical/idiomatic, explicitly NOT golf/length
    assert "idiomatic" in s and "canonical" in s
    assert "not golf" in s or "not about" in s
    # names the canonical tactics maintainers ask for
    for tac in ("grw", "gcongr", "simp", "omega", "grind"):
        assert tac in IDIOM_SYSTEM
    # still a verified, checkable claim
    assert "lean_verify" in IDIOM_SYSTEM and "replacement" in IDIOM_USER
    assert IDIOM_USER.format(**PROMPT_FIELDS)


def test_idiom_prompt_distinct_from_golf():
    assert IDIOM_SYSTEM != GOLF_SYSTEM
    # golf is about length; idiom explicitly disclaims it
    assert "shorter" in GOLF_SYSTEM.lower()
    assert "not about length" in IDIOM_SYSTEM.lower() or "not golf" in IDIOM_SYSTEM.lower()


def test_idiom_uses_native_verify_search_toolset():
    cfg = LeanPRReviewIdiomTask.task_config_class()
    assert "lean_verify" in cfg.enabled_tools and "content_search" in cfg.enabled_tools
