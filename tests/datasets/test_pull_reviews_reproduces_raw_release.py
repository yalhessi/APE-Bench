"""The task pipeline still produces the frozen raw release, byte for byte.

`dev-raw-0.3.0` holds 201 funnel decisions, 138 reviewer-visible episodes and 138 hidden
boundaries, built by `legacy_pipeline/raw_release.py` from the 201 cached bundles, the 223 cached
compares and the 59-login roster. Rebuilding them in memory takes under a second, which makes them
the oracle for every change this refactor makes to the definitions the funnel uses and to where
its inputs come from: if a consolidated rule or a new data source moved one reviewer event, one
title, one diff, a byte here moves.

The roster is the one the release's manifest pins, not a newer snapshot. Membership is
time-varying, so a newer roster would shift reviewer events and fail this test for a reason that
has nothing to do with the code under test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mathlib_review.io import jsonl_bytes, sha256_file
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_COMPARES, LEGACY_V2_ROSTER
from src.mathlib_review.release.episode_builder import funnel_and_first_round, load_roster

RELEASE = Path("inputs/pr_review_v4/releases/dev-raw-0.3.0")


def _pinned_roster_path() -> Path:
    manifest = json.loads((RELEASE / "manifest.json").read_text())
    ref = next(r for r in manifest["sources"] if r["role"] == "reviewer_roster")
    path = Path(ref["path"])
    assert sha256_file(path) == ref["sha256"], "the pinned roster changed; verify_frozen would fail too"
    return path


def _rebuild_from_legacy_caches():
    roster = load_roster(_pinned_roster_path())
    funnels, episodes, boundaries = [], [], []
    for bundle_path in sorted(LEGACY_V2_BUNDLES.glob("pr_*.json")):
        decision, result = funnel_and_first_round(
            json.loads(bundle_path.read_text()), bundle_path=bundle_path,
            compare_cache=LEGACY_V2_COMPARES, roster=roster)
        funnels.append(decision)
        if result:
            episodes.append(result.episode)
            boundaries.append(result.boundary)
    episodes.sort(key=lambda item: (item.pr_number, item.round_index))
    boundaries.sort(key=lambda item: (item.pr_number, item.round_index))
    funnels.sort(key=lambda item: item.pr_number)
    return funnels, episodes, boundaries


@pytest.fixture(scope="module")
def rebuilt():
    if not RELEASE.is_dir() or not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("frozen raw release or bundle cache absent")
    return _rebuild_from_legacy_caches()


def test_the_roster_the_release_pins_is_the_legacy_roster():
    assert _pinned_roster_path() == LEGACY_V2_ROSTER


@pytest.mark.parametrize("index,relpath,count", [
    (0, "derived/funnel.jsonl", 201),
    (1, "input/episodes.jsonl", 138),
    (2, "gold/episode_boundaries.jsonl", 138),
])
def test_the_funnel_reproduces_the_frozen_release_byte_for_byte(rebuilt, index, relpath, count):
    rows = rebuilt[index]
    assert len(rows) == count
    assert jsonl_bytes(rows) == (RELEASE / relpath).read_bytes(), (
        f"{relpath} no longer reproduces from the same inputs; a definition or data source the "
        "funnel reads has changed behaviour")
