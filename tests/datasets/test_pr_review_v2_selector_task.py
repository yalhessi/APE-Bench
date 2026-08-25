"""Tests for the agentic selector task (lean_pr_review_selector) — no network.

Covers: registration + base sharing; the data model carries candidate_findings; the
prompt renders the candidate list and the submit_scores tool; score normalization
clamps to [0,100], drops out-of-range/duplicate/malformed indices.
"""

import asyncio

import ape.tasks.lean_tasks  # noqa: F401  (triggers registration)
from ape.tasks.base import get_task_class
from ape.tasks.models import WorkspaceInfo
from ape.tasks.lean_tasks.formal_math.pr_review_v2.base import BasePRReviewTask
from ape.tasks.lean_tasks.formal_math.pr_review_v2.selector_task import (
    LeanPRReviewSelectorTask,
    PRReviewSelectorData,
    SELECTOR_SYSTEM,
    SELECTOR_USER,
)


def _make_task(n_candidates=3):
    task = LeanPRReviewSelectorTask.__new__(LeanPRReviewSelectorTask)
    task.data = PRReviewSelectorData(
        task_id="lean_pr_review_selector_1", pr_number=1, diff="x",
        candidate_findings=[
            {"index": i, "path": f"Mathlib/A.lean", "line_start": 10 + i, "line_end": 10 + i,
             "severity": "advisory", "claim": f"claim {i}", "suggested_fix": None}
            for i in range(n_candidates)
        ],
        target_workspace=WorkspaceInfo(name="target", commit_hash="abc123", repo_url="x"),
    )
    return task


def test_selector_registers_and_shares_base():
    registered = get_task_class("lean_pr_review_selector")
    assert registered is LeanPRReviewSelectorTask
    assert registered.task_type == "lean_pr_review_selector"
    assert issubclass(registered, BasePRReviewTask)
    assert registered.data_class is PRReviewSelectorData


def test_data_carries_candidate_findings():
    task = _make_task(4)
    assert len(task.data.candidate_findings) == 4


def test_findings_block_renders_indices_and_claims():
    task = _make_task(3)
    block = task._findings_block()
    for i in range(3):
        assert f"[{i}]" in block
        assert f"claim {i}" in block


def test_prompt_mentions_scoring_and_selectivity():
    assert "score" in SELECTOR_SYSTEM.lower()
    assert "selective" in SELECTOR_SYSTEM.lower()
    # system formats with the submit tool name; user has the candidate section
    assert SELECTOR_SYSTEM.format(submit_tool_name="submit_scores")
    assert "Candidate findings to score" in SELECTOR_USER


def test_normalize_scores_clamps_and_filters():
    task = _make_task(3)
    raw = [
        {"index": 0, "score": 150},          # clamp to 100
        {"index": 0, "score": 5},            # duplicate -> dropped
        {"index": 3, "score": 50},           # out of range -> dropped
        {"index": 1, "score": -3, "reason": "r"},  # clamp to 0
        {"index": "bad", "score": 1},        # malformed -> dropped
        {"index": 2},                        # missing score -> 0
    ]
    out = task._normalize_scores(raw)
    by_idx = {o["index"]: o["score"] for o in out}
    assert by_idx == {0: 100.0, 1: 0.0, 2: 0.0}
    assert next(o for o in out if o["index"] == 1)["reason"] == "r"
