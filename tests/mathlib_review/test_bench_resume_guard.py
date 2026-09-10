"""A bench attempt must not silently return the previous one from cache.

`bench_{arm}` was used as the orchestrator id for every attempt, and that name is the
orchestrator's *resume key*. Five runs of one bench therefore produced two distinct results and
four no-ops: costs identical to the microdollar, four of them paid for and all four reporting
the earlier attempt's behaviour as if it were new. Only the prompt change kept the two variants
from collapsing into each other as well -- a different prompt is a different task id.

`review.runner.guard_run_name` documents exactly this hazard for the pipeline path. The bench
path had no equivalent.
"""

from __future__ import annotations

import logging

import pytest

from src.mathlib_review.analysis.bench_cli import (
    assert_scratch_is_unused, bench_run_name,
)

LOGGER = logging.getLogger("test")


class _Scaffold:
    def __init__(self, base):
        self.runs_base_dir = base


def test_the_run_name_carries_the_variant_and_the_attempt():
    assert bench_run_name("proof_idiom", "baseline", 1) == "bench_proof_idiom_baseline_a1"
    assert bench_run_name("proof_idiom", "rung3a", 3) == "bench_proof_idiom_rung3a_a3"
    # Two attempts of one variant, and two variants of one attempt, must all differ.
    names = {
        bench_run_name("proof_idiom", "baseline", 1),
        bench_run_name("proof_idiom", "baseline", 2),
        bench_run_name("proof_idiom", "rung3a", 1),
    }
    assert len(names) == 3


def test_an_unused_name_passes(tmp_path):
    assert_scratch_is_unused("bench_x_baseline_a1", _Scaffold(tmp_path),
                             resume=False, logger=LOGGER) is None


def test_an_existing_attempt_is_refused_with_the_reason(tmp_path):
    (tmp_path / "bench_x_baseline_a1").mkdir()
    with pytest.raises(SystemExit) as excinfo:
        assert_scratch_is_unused("bench_x_baseline_a1", _Scaffold(tmp_path),
                                 resume=False, logger=LOGGER)
    message = str(excinfo.value)
    assert "resume key" in message
    assert "--attempt" in message


def test_resume_is_allowed_but_says_it_is_not_a_new_sample(tmp_path, caplog):
    (tmp_path / "bench_x_baseline_a1").mkdir()
    with caplog.at_level(logging.WARNING):
        assert_scratch_is_unused("bench_x_baseline_a1", _Scaffold(tmp_path),
                                 resume=True, logger=LOGGER)
    assert "not an independent attempt" in caplog.text
