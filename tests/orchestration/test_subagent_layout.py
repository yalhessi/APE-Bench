"""What a subagent gets, where it lives, and what of it reaches its parent.

The user's words: "it's unclear how the subagent scratch/memory directories are organized
(our system relies on certain assumptions and I don't think they are clear here)."

The assumptions are real and were nowhere written down. This file writes them down, and each
one is load-bearing rather than incidental:

* **Isolation is a property of path derivation.** Every child runs under
  `<parent attempt>/subtasks/<group>/`, and inside it the orchestrator's own
  `tasks/<i>/samples/<n>/attempts/<id>_<timestamp>` gives each attempt its own directory. That
  is the *only* thing making concurrent arms safe: `_ensure_patched_target_workspace` unlinks
  and rebuilds whatever path it is handed, so two children sharing one would race and each
  would see the other's half-built workspace.
* **A child's scratch is its own and reaches nobody.** Review tasks write no scratch file at
  all -- the thing worth compiling is the reviewed file in `target/` -- so the directory is
  created and left empty. A parent reads a child through its returned outcome, not its files.
* **What reaches the parent is a summary, by policy.** `CoordinationPolicy.parent_view` is
  `"summary"`, and `JobOutcome.summary()` is that summary: counts and cost and a reason, never
  candidate bodies. The lead routes; it does not re-adjudicate.

Measured against a real run (`pr_review_v5_specialist4_rep1`), whose arm attempt directories
hold exactly: the session transcript, `conversations/`, `logs/`, `skills/`,
`skills_manifest.json`, `subtasks/`, and `workspaces/{scratch,target}`.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from ape.orchestration import subtasks


def test_a_child_runs_under_its_parents_attempt():
    """The isolation invariant, and the one thing `nested_config` is not free to change."""

    source = inspect.getsource(subtasks.nested_config)
    assert 'Path(attempt_path) / "subtasks" / group' in source
    assert "config.runs_base_dir = subtasks" in source


def test_nested_execution_spawns_no_processes_by_default():
    """The parent is already inside a worker. It is a default rather than a rule because
    `judgment` and `review_gate` set their own concurrency and pass it through."""

    source = inspect.getsource(subtasks.nested_config)
    assert "config.execution.num_processes = 0" in source


def test_nested_concurrency_is_bounded():
    """Nothing bounded it: four leads x four arms x three tiers dispatched by
    `asyncio.gather` was up to 48 simultaneous Lean compiles from one process, each carrying
    its own multi-gigabyte workspace overlay."""

    assert subtasks.DEFAULT_NESTED_CONCURRENCY == 4


def test_each_group_gets_its_own_directory(tmp_path):
    """Two waves must not write into one directory, or the second overwrites the first's
    evidence -- which is what a resumed lead restarting at wave 1 used to do."""

    from ape.scaffolds.ape_agent.config import ApeAgentConfig

    config = ApeAgentConfig()
    first = subtasks.nested_config(tmp_path, config, group="wave1")
    second = subtasks.nested_config(tmp_path, config, group="wave2")
    assert first.runs_base_dir != second.runs_base_dir
    assert first.runs_base_dir.parent == tmp_path / "subtasks"
    assert first.runs_base_dir.is_dir() and second.runs_base_dir.is_dir()


def test_a_review_task_writes_no_scratch_file():
    """So the empty `workspaces/scratch` under every arm attempt is expected, not a symptom.
    The reviewed file lives in `target/`, read-only to the agent and readable by the
    compiler."""

    from ape.tasks.lean_tasks.formal_math.review_task import BasePRReviewTask

    assert BasePRReviewTask.lean_verify_allows_target is True
    source = inspect.getsource(BasePRReviewTask)
    assert "A review task has no scratch file" in source


def _outcome(**candidate):
    from ape.tasks.lean_tasks.formal_math.pr_review_v5.delegation import JobOutcome

    return JobOutcome(
        invocation_id="wu:1#proof_golf", arm_id="proof_golf", work_unit_id="wu:1",
        pr_number=1, budget_tier="standard", status="completed", cost=0.2,
        candidates=[candidate],
        verification_artifacts=[{"artifact_id": "a1", "success": True}],
    )


def test_what_reaches_the_parent_is_truncated_not_omitted():
    """`parent_view` is a sealed policy value and `JobOutcome.summary()` implements it.

    The boundary is truncation, and it moved once for a reason: the first version returned no
    claim text at all, on the reasoning that the lead routes and does not re-adjudicate. That
    stopped being true when synthesis became subtractive -- the lead decides which claims are
    the same observation, and it cannot do that from a count.
    """

    from src.mathlib_review.review.coordination import CoordinationPolicy

    assert CoordinationPolicy().parent_view == "summary"

    summary = _outcome(claim="x" * 2000, requested_change="y" * 2000).summary()
    assert summary["candidates"] == 1
    assert len(summary["claims"][0]["claim"]) == 800
    assert len(summary["claims"][0]["requested_change"]) == 400


def test_the_gates_the_lead_cannot_reach_stay_out_of_the_summary():
    """Evidence requests, proposed edits and verification artifacts belong to the gates. The
    lead sees that an artifact exists, not what it says."""

    summary = _outcome(
        claim="a claim", requested_change="a change",
        proposed_edit={"replacement": "a replacement the lead must not arbitrate over"},
        evidence_requests=[{"kind": "repository_search"}],
    ).summary()
    assert summary["verified_edits"] == 1
    rendered = str(summary)
    assert "a replacement the lead must not arbitrate" not in rendered
    assert "repository_search" not in rendered


def test_a_sibling_sees_nothing_of_another_sibling():
    """Sealed as a policy value so that coordination becoming a variable is a recorded change
    rather than a silent one."""

    from src.mathlib_review.review.coordination import CoordinationPolicy

    assert CoordinationPolicy().sibling_view == "none"


def test_the_child_directory_shape_is_what_the_index_records():
    """And why the index exists: the shape below is the thing readers used to parse. A child's
    physical path is `<parent attempt>/subtasks/<group>/<orchestrator id>/tasks/<i>/samples/
    <n>/attempts/<id>_<timestamp>`, and every segment of that has changed at least once."""

    from ape.orchestration import execution_index

    assert hasattr(execution_index, "record")
    assert "task_dir" in inspect.getsource(execution_index.record)
