"""A bench must hand its arm the same gated context the real runner does.

`build_agenda` does not put `retrieval_cutoff` in the pool payload — `review/runner.py` attaches
it afterwards, and `bench_cli._payloads_for` did not. The consequence was silent, because
`_require_cutoff` raises *inside* the tool and the tool catches it and returns
`{"success": False, ...}`: the case still ran, still scored, and two of the arm's three evidence
tools were dead.

It was visible only in the arm's own words, in an abstention nobody read:

    "precedent/zulip searches failed due to missing retrieval cutoff configuration"

So every bench in `results/pr_review_v5/benches/` predating 2026-09-15 — the whole `rung3a/b/c`
series — measured an arm holding `naming_norm` and `declaration_search` and nothing else. For the
naming bench that is the tool under test, whose weight it silently inflated.

The cutoff is also a leak gate, so the failure had a second edge: a bench is the one path where
an ungated read would not have been refused loudly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.mathlib_review.agenda.cutoffs import cutoffs_by_episode
from src.mathlib_review.io import load_jsonl
from src.mathlib_review.schema import ReviewEpisodeInput

RELEASE = Path("inputs/pr_review_v4/releases/dev-medium-0.5.0")


def test_the_bench_attaches_a_cutoff_to_every_payload():
    """The bug, pinned on the real release rather than a fixture."""

    from src.mathlib_review.analysis.bench_cli import _payloads_for
    from src.mathlib_review.analysis.benches import build_all
    from src.mathlib_review.analysis.bench_cli import roster
    from src.mathlib_review.review.runner import load_release, load_run

    dataset, _scaffold, _ = load_run(Path("configs/pr_review_v5_medium_heldout_v5release.yaml"))
    release = load_release(dataset)
    bench = build_all(dataset.release, roster(), pr_numbers=[33337],
                      negatives_per_pr=1, selector="audited")["naming"]

    payloads = _payloads_for(bench, dataset, release)
    assert payloads, "no naming payloads built for 33337 — the fixture moved"

    missing = [wu for wu, data in payloads.items() if not data.get("retrieval_cutoff")]
    assert missing == [], (
        f"{missing} would reach the arm with no retrieval cutoff; `precedent_search` and "
        "`zulip_search` return an error for every call and the case still scores")


def test_the_cutoff_is_the_one_the_real_runner_would_have_used():
    """Not merely present: the same value, or the bench is a different experiment."""

    from src.mathlib_review.analysis.bench_cli import _payloads_for
    from src.mathlib_review.analysis.benches import build_all
    from src.mathlib_review.analysis.bench_cli import roster
    from src.mathlib_review.review.runner import load_release, load_run

    dataset, _scaffold, _ = load_run(Path("configs/pr_review_v5_medium_heldout_v5release.yaml"))
    release = load_release(dataset)
    expected = cutoffs_by_episode(
        load_jsonl(RELEASE / "input/episodes.jsonl", ReviewEpisodeInput))

    bench = build_all(dataset.release, roster(), pr_numbers=[33337],
                      negatives_per_pr=1, selector="audited")["naming"]
    for data in _payloads_for(bench, dataset, release).values():
        assert data["retrieval_cutoff"] == expected[data["episode_id"]]


def test_a_missing_cutoff_is_not_silent_at_the_tool():
    """The reason this went unnoticed for every bench: the tool swallows it into a result.

    Recorded so the swallow is understood as deliberate (a failed retrieval must not kill an
    arm mid-investigation) rather than repaired in the wrong place — the fix belongs where the
    cutoff is assigned, which is what the two tests above pin.
    """

    from ape.tasks.lean_tasks.formal_math.review.context_tools import _require_cutoff
    from types import SimpleNamespace

    with pytest.raises(RuntimeError, match="no retrieval cutoff"):
        _require_cutoff(SimpleNamespace(data=SimpleNamespace(retrieval_cutoff=None)))


def test_the_bench_gives_its_tools_a_trace(tmp_path):
    """A bench wrote no `context_trace.jsonl`: payloads carried no `trace_path`, so
    `_append_trace` returned at once and a tool's answer survived only in the session transcript."""

    from src.mathlib_review.analysis.bench_cli import _payloads_for
    from src.mathlib_review.analysis.benches import build_all
    from src.mathlib_review.analysis.bench_cli import roster
    from src.mathlib_review.review.runner import load_release, load_run

    dataset, _scaffold, _ = load_run(Path("configs/pr_review_v5_medium_heldout_v5release.yaml"))
    release = load_release(dataset)
    bench = build_all(dataset.release, roster(), pr_numbers=[33337],
                      negatives_per_pr=1, selector="audited")["naming"]
    trace = tmp_path / "context_trace.jsonl"
    payloads = _payloads_for(bench, dataset, release, trace_path=trace)
    assert payloads and all(data["trace_path"] == str(trace) for data in payloads.values())
