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
