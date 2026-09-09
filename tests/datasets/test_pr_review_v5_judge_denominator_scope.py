"""Recall is divided by the obligations of the PRs the run actually reviewed.

Every audit before `pr5-smoke4-rep9` was scored against the same 40-obligation pool spanning
twelve PRs, whatever PRs it ran: `lead-smoke4-rep7` (4 PRs) and `heldout11-rep2` (11 PRs) have
byte-identical obligation sets. `semantic_report` grew a `scoped_pr_numbers` argument to fix
it, but its default is the whole release, so a judge config that simply omitted `pr_numbers`
silently restored the bug.

The scope is therefore taken from the generation run's own `agenda_report.json` — the only
artifact that records which PRs it enumerated work for — rather than from the config alone.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from src.mathlib_review.judge.runner import JudgeDatasetConfig, judged_pr_scope

LOGGER = logging.getLogger("test")


def _config(tmp_path, *, planned=None, pr_numbers=(), control=()):
    run_dir = tmp_path / "runs" / "r1"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "findings.jsonl").write_text("", encoding="utf-8")
    if planned is not None:
        (run_dir / "agenda_report.json").write_text(
            json.dumps({"pr_numbers": list(planned)}), encoding="utf-8")
    return JudgeDatasetConfig(
        release=tmp_path / "release", candidates=run_dir / "findings.jsonl",
        out_dir=tmp_path / "audit",
        pr_numbers=list(pr_numbers), control_pr_numbers=list(control),
    )


def test_a_config_that_names_no_prs_is_scoped_to_the_run(tmp_path):
    """The case that produced every 40-obligation audit: silence meant the whole release."""

    config = _config(tmp_path, planned=[33057, 33066, 33098, 33438])
    assert judged_pr_scope(config, LOGGER) == [33057, 33066, 33098, 33438]


def test_control_prs_are_kept_in_scope(tmp_path):
    """A control PR carries no obligations, so it cannot change the denominator — but it is
    part of what was reviewed, and dropping it here would disagree with the pair filter."""

    config = _config(tmp_path, planned=[33066, 33098], control=[33438])
    assert judged_pr_scope(config, LOGGER) == [33066, 33098, 33438]


def test_a_stated_subset_is_authoritative(tmp_path):
    """An R0 replay deliberately scores fewer PRs than the run reviewed."""

    config = _config(tmp_path, planned=[33057, 33066, 33098, 33438], pr_numbers=[33098])
    assert judged_pr_scope(config, LOGGER) == [33098]


def test_scoring_a_pr_the_run_never_reviewed_is_refused(tmp_path):
    config = _config(tmp_path, planned=[33066, 33098], pr_numbers=[33098, 33117])
    with pytest.raises(ValueError) as excinfo:
        judged_pr_scope(config, LOGGER)
    message = str(excinfo.value)
    assert "33117" in message
    assert "never reviewed" in message


def test_without_an_agenda_report_the_config_still_decides(tmp_path):
    """v4 runs and hand-assembled candidate files have no agenda report. The fallback is the
    previous behaviour, not a guess: `None` means the whole release, and the report now says
    so in `denominator_pr_scope` rather than looking scoped."""

    assert judged_pr_scope(_config(tmp_path), LOGGER) is None
    assert judged_pr_scope(_config(tmp_path, pr_numbers=[33098]), LOGGER) == [33098]
