"""The pinned roster is read, never written.

`src/datasets/pr_review_v2/data/mathlib_roster.txt` is declared with a hash by nine frozen release
manifests. `python -m src.datasets.pr_review_v2.roster` used to write there when run without
arguments, so a routine roster refresh would have failed `verify_frozen` for every v4 release.
New snapshots are dated files under `inputs/pull_requests/rosters/`.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.datasets.pull_requests import roster
from src.mathlib_review.paths import LEGACY_V2_ROSTER, PULL_REQUESTS_ROSTERS


def test_writing_the_pinned_roster_is_refused_before_any_network_call(monkeypatch):
    monkeypatch.setattr(roster, "build_roster",
                        lambda: pytest.fail("must refuse before fetching anything"))
    with pytest.raises(PermissionError) as excinfo:
        roster.write_roster(LEGACY_V2_ROSTER)
    assert "nine frozen release manifests" in str(excinfo.value)


def test_the_default_output_is_a_dated_snapshot_not_the_pinned_file():
    path = roster.dated_roster_path(date(2026, 9, 11))
    assert path == PULL_REQUESTS_ROSTERS / "mathlib_roster_2026-09-11.txt"
    assert path.resolve() != LEGACY_V2_ROSTER.resolve()


def test_the_old_module_re_exports_the_shared_writer():
    from src.datasets.pr_review_v2 import roster as legacy

    assert legacy.write_roster is roster.write_roster
    assert legacy.ROSTER_TEAMS == roster.ROSTER_TEAMS


def test_zulip_identities_share_the_team_set_and_fetch():
    from src.datasets.zulip import identity

    assert identity.ROSTER_TEAMS is roster.ROSTER_TEAMS
    assert identity.DATA_URL == roster.DATA_URL
