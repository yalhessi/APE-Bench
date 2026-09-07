"""The judge refuses to score a run that did not cover what it promised.

Two September runs closed with `completion_status: failed` and were scored anyway, because
nothing between the generation run and the judge ever looked at the manifest. Their recall
figures were reported, compared against each other, and used to decide what to build next.

A partial run's artifacts are still worth reading. Its recall is not a measurement: the
denominator includes work units that were never reviewed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.datasets.pr_review_v4.judge_runner import (
    JudgeDatasetConfig, assert_source_run_is_complete,
)

LOGGER = logging.getLogger("test")


def _config(tmp_path, *, status=None, gaps=(), allow_partial=False):
    run_dir = tmp_path / "runs" / "r1"
    run_dir.mkdir(parents=True)
    (run_dir / "findings.jsonl").write_text("", encoding="utf-8")
    if status is not None:
        (run_dir / "run_manifest.json").write_text(json.dumps({
            "run_name": "r1", "completion_status": status,
            "coverage_gaps": list(gaps),
        }), encoding="utf-8")
    return JudgeDatasetConfig(
        release=tmp_path / "release", candidates=run_dir / "findings.jsonl",
        out_dir=tmp_path / "audit", allow_partial=allow_partial,
    )


@pytest.mark.parametrize("status", ["partial", "failed"])
def test_an_incomplete_run_is_refused(tmp_path, status):
    config = _config(tmp_path, status=status,
                     gaps=[{"invocation_id": "wu:1#family_design"}])
    with pytest.raises(ValueError) as excinfo:
        assert_source_run_is_complete(config, LOGGER)
    message = str(excinfo.value)
    assert status in message
    assert "wu:1#family_design" in message
    assert "allow_partial" in message


def test_a_complete_run_passes(tmp_path):
    config = _config(tmp_path, status="complete")
    assert assert_source_run_is_complete(config, LOGGER) == "complete"


def test_allow_partial_scores_it_and_says_the_numbers_are_forensic(tmp_path, caplog):
    config = _config(tmp_path, status="partial",
                     gaps=[{"invocation_id": "wu:1#generalist"}], allow_partial=True)
    with caplog.at_level(logging.WARNING):
        assert assert_source_run_is_complete(config, LOGGER) == "partial"
    assert "forensic" in caplog.text


def test_a_run_with_no_manifest_is_unchecked_rather_than_assumed_good(tmp_path):
    """v4 runs and hand-assembled candidate files have no manifest. Saying nothing is honest;
    inventing a verdict about them is not."""

    config = _config(tmp_path, status=None)
    assert assert_source_run_is_complete(config, LOGGER) is None


# --- deriving judge paths from the run they score -----------------------------------------
#
# `candidates`, `out_dir` and `run_name` are three free-form strings encoding one run
# identity, with nothing making them agree. They disagree in the tree right now:
# pr_review_v5_medium_heldout.yaml was bumped to rep2 while its judge config still reads
# rep1/findings.jsonl into audits/medium-heldout-rep1. Running that pair scores the old run
# under the new run's name, and nothing errors.


def test_the_three_paths_are_derived_from_one_name():
    from src.datasets.pr_review_v4.judge_runner import derive_from_run

    derived = derive_from_run("pr_review_v5_specialist4_rep1")
    assert derived["candidates"] == Path(
        "results/pr_review_v5/runs/pr_review_v5_specialist4_rep1/findings.jsonl")
    assert derived["out_dir"] == Path("results/pr_review_v5/audits/specialist4-rep1")
    assert derived["run_name"] == "pr_review_v5_judge_specialist4_rep1"


def test_candidates_pointing_at_another_run_is_refused(tmp_path):
    """The exact live mistake: judging run A's findings while claiming to judge run B."""

    from src.datasets.pr_review_v4.judge_runner import (
        JudgeDatasetConfig, assert_paths_agree,
    )

    config = JudgeDatasetConfig(
        release=tmp_path / "release",
        candidates=Path(
            "results/pr_review_v5/runs/pr_review_v5_lead_medium_heldout_rep1/findings.jsonl"),
        out_dir=tmp_path / "audit",
    )
    with pytest.raises(ValueError) as excinfo:
        assert_paths_agree(config, "pr_review_v5_lead_medium_heldout_rep2")
    message = str(excinfo.value)
    assert "rep1" in message and "rep2" in message
    assert "attribute one run's findings to another" in message


def test_candidates_inside_the_named_run_are_accepted(tmp_path):
    from src.datasets.pr_review_v4.judge_runner import (
        JudgeDatasetConfig, assert_paths_agree, derive_from_run,
    )

    run_name = "pr_review_v5_specialist4_rep1"
    config = JudgeDatasetConfig(
        release=tmp_path / "release",
        candidates=derive_from_run(run_name)["candidates"],
        out_dir=tmp_path / "audit",
    )
    assert_paths_agree(config, run_name)
