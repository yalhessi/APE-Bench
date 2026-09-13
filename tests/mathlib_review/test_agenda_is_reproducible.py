"""A sealed plan must be the same plan in the next process.

`build_slices` fed its exposure list from `mine = set(change_ids)` and sorted it by reach
alone, so declarations at equal reach kept set-iteration order -- which Python randomises per
process unless PYTHONHASHSEED is fixed. On the 12-PR held-out set one work unit (PR 33294) has
two declarations at reach 6, which was enough to give that unit two possible rendered prompts
and `agenda_sha256` two possible values.

That breaks two things the project relies on. The plan is a pre-registration, so it has to name
one experiment rather than one of two. And `seal_or_revise_plan` refuses a resume whose plan
differs outside `RESUMABLE_PLAN_FIELDS`, so an interrupted run would have been refused as a
semantic change when nothing semantic had changed.
"""

from __future__ import annotations

import subprocess
import sys

from src.mathlib_review.agenda.review_map import build_slices


def _slice(change_ids, exposure):
    return build_slices(
        jobs=[("inv:1", 33294, "ep:1", list(change_ids))],
        components_by_pr={}, graphs_by_episode={},
        paths_by_change={c: "Mathlib/A.lean" for c in change_ids},
        subjects_by_change={c: f"Subject.{c[-1]}" for c in change_ids},
        exposure_by_change=exposure,
    )["inv:1"]


def test_ties_are_broken_by_name_not_by_set_order():
    change_ids = ["change:a", "change:b", "change:c", "change:d"]
    tied = {c: 6 for c in change_ids}

    exposure = _slice(change_ids, tied).exposure

    assert [name for name, _reach in exposure] == sorted(name for name, _ in exposure), (
        "declarations at equal reach must be ordered by name")
    # and reach still dominates the name
    mixed = _slice(change_ids, {"change:a": 1, "change:b": 9, "change:c": 9, "change:d": 3})
    assert [reach for _n, reach in _slice(change_ids, {"change:a": 1, "change:b": 9,
                                                       "change:c": 9, "change:d": 3}).exposure] \
        == [9, 9, 3, 1]
    assert [name for name, _ in mixed.exposure][:2] == sorted(
        [name for name, reach in mixed.exposure if reach == 9])


def test_the_slice_is_identical_under_different_hash_seeds():
    """The regression itself: same inputs, different PYTHONHASHSEED, one answer."""

    program = (
        "from src.mathlib_review.agenda.review_map import build_slices;"
        "ids=['change:a','change:b','change:c','change:d'];"
        "s=build_slices(jobs=[('inv:1',1,'ep:1',ids)], components_by_pr={}, graphs_by_episode={},"
        " paths_by_change={c:'M/A.lean' for c in ids},"
        " subjects_by_change={c:'Subject.'+c[-1] for c in ids},"
        " exposure_by_change={c:6 for c in ids})['inv:1'];"
        "print(s.exposure)"
    )
    seen = set()
    for seed in ("0", "1", "7", "13", "99"):
        result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True,
                                env={"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"})
        assert result.returncode == 0, result.stderr
        seen.add(result.stdout.strip())
    assert len(seen) == 1, f"the slice differs across hash seeds: {seen}"
