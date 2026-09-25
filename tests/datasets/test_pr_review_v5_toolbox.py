"""`cli tool`: the arms' own tools, called outside a run, for probes.

A probe's reviewer that holds hand-written tools says nothing about an arm that holds the
pipeline's. These pin that the toolbox registers the arms' tools through the arms' own code,
and that it refuses rather than compiling against a base that was never built.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ReviewEpisodeInput

EPISODES = Path("inputs/pr_review_v4/releases/dev-medium-0.5.0/input/episodes.jsonl")
RUN_CONFIG = Path("configs/pr_review_v5_verdicts_fanout4.yaml")


def _episode(pr_number: int) -> ReviewEpisodeInput:
    return next(e for e in load_jsonl(EPISODES, ReviewEpisodeInput) if e.pr_number == pr_number)


def test_it_refuses_a_base_that_was_never_built(tmp_path):
    from src.mathlib_review.review.toolbox import workbench

    unbuilt = _episode(33098).model_copy(update={"base_sha": "0" * 40})
    with pytest.raises(RuntimeError, match="no compiled base workspace"):
        workbench(unbuilt, tmp_path / "work", RUN_CONFIG)
    assert not (tmp_path / "work" / "target").exists(), "nothing is laid down before the refusal"


def test_it_holds_every_tool_an_arm_can_hold(tmp_path):
    from src.mathlib_review.evidence.evidence import snapshot_workspace
    from src.mathlib_review.review.toolbox import CONTEXT_TOOLS, FILE_TOOLS, describe, workbench

    episode = _episode(33098)
    if snapshot_workspace(episode.base_sha) is None:
        pytest.skip("needs the compiled base workspace under data/code_execute/")
    mcp = workbench(episode, tmp_path / "work", RUN_CONFIG)
    assert set(CONTEXT_TOOLS) | {"lean_verify_edit"} | FILE_TOOLS <= set(mcp.tools)
    # the agent is shown what an arm is shown: every tool's description and argument schema
    described = describe(mcp)
    assert all(item["description"] for item in described.values())
    assert described["lean_verify_edit"]["arguments"]["new_declaration"]["description"]
    # and the reads are gated at the episode's own cutoff, not left open
    from src.mathlib_review.agenda.cutoffs import episode_cutoff

    assert mcp.tools and episode_cutoff(episode)
