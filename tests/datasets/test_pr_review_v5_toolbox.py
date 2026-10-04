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


VAL_EPISODES = Path("inputs/pr_review_v4/releases/val-2025-06-2026-03-v1/input/episodes.jsonl")
VAL_CONFIG = Path("configs/pr_review_v5_val_2025_06_2026_03_v1_small12.yaml")


def test_it_compiles_against_the_reviewed_workspace_when_one_is_built(tmp_path):
    """PR 30458 generalises `div_right_injective` in `Algebra/Group/Basic.lean` and uses it in
    `Pointwise/Finset/Basic.lean`. Against the source-only overlay the second file reported
    `failed to synthesize Group α` (2026-09-29); against the reviewed workspace it compiles, and
    the result says which environment it had."""

    from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key
    from src.mathlib_review.evidence.evidence import snapshot_workspace
    from src.mathlib_review.review.toolbox import call, workbench

    episode = next(e for e in load_jsonl(VAL_EPISODES, ReviewEpisodeInput) if e.pr_number == 30458)
    if snapshot_workspace(reviewed_workspace_key(episode.base_sha, episode.diff)) is None:
        pytest.skip("needs PR 30458's reviewed workspace under data/code_execute/")
    mcp = workbench(episode, tmp_path / "work", VAL_CONFIG)
    result = call(mcp.tools, "lean_verify_edit",
                  {"path": "Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean"})
    assert result["compiles"] is True, result
    assert result["errors_already_in_the_file"] == []
    assert result["environment"].startswith("Verified against the reviewed workspace")
    # a second call on the same workdir finds the link, not a stale overlay
    assert call(mcp.tools, "lean_verify_edit", {
        "path": "Mathlib/Algebra/Group/Pointwise/Finset/Basic.lean"})["compiles"] is True


def test_it_refuses_a_stale_overlay_where_a_reviewed_workspace_exists(tmp_path):
    from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key
    from src.mathlib_review.evidence.evidence import snapshot_workspace
    from src.mathlib_review.review.toolbox import workbench

    episode = next(e for e in load_jsonl(VAL_EPISODES, ReviewEpisodeInput) if e.pr_number == 30458)
    if snapshot_workspace(reviewed_workspace_key(episode.base_sha, episode.diff)) is None:
        pytest.skip("needs PR 30458's reviewed workspace under data/code_execute/")
    (tmp_path / "work" / "target").mkdir(parents=True)
    with pytest.raises(RuntimeError, match="source-only overlay from an earlier call"):
        workbench(episode, tmp_path / "work", VAL_CONFIG)


def test_the_cli_prints_only_its_json_when_it_resolves_a_reviewed_workspace(tmp_path):
    """The far end a probe reads is `cli tool`'s stdout. Resolving the reviewed workspace with no
    logger printed the restore manager's INFO lines there, ahead of the JSON (2026-09-29)."""

    import json
    import os
    import subprocess
    import sys

    from ape.toolkits.execute.lean.core.build_manager import reviewed_workspace_key
    from src.mathlib_review.evidence.evidence import snapshot_workspace

    episode = next(e for e in load_jsonl(VAL_EPISODES, ReviewEpisodeInput) if e.pr_number == 30458)
    if snapshot_workspace(reviewed_workspace_key(episode.base_sha, episode.diff)) is None:
        pytest.skip("needs PR 30458's reviewed workspace under data/code_execute/")
    out = subprocess.run(
        [sys.executable, "-m", "src.mathlib_review.review.cli", "tool", "list",
         "--episodes", str(VAL_EPISODES), "--pr", "30458", "--workdir", str(tmp_path / "work"),
         "--run-config", str(VAL_CONFIG)],
        capture_output=True, text=True, check=True,
        env={**os.environ, "PYTHONPATH": os.pathsep.join(["src", os.environ.get("PYTHONPATH", "")])})
    assert "lean_verify_edit" in json.loads(out.stdout)
    assert (tmp_path / "work" / "target").is_symlink()

