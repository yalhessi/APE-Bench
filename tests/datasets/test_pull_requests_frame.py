"""The evaluation frame's draw: deterministic from its sealed inputs, proportional by month, and a
walk that never reorders the seeded order to fit what happens to be collected."""

from __future__ import annotations

import collections
import json

import pytest

from src.datasets.pull_requests.projections import frame as f
from src.datasets.pull_requests.seed import seed_from_legacy
from src.datasets.pull_requests.store import PullRequestStore
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_ROSTER
from src.datasets.pull_requests.definitions import load_roster


def _spec(**overrides):
    values = dict(
        name="test-frame", created_from="2025-11-01", created_to="2025-12-31",
        listing_window=("2024-03-01", "2026-08-31"), store_content_sha256="0" * 64,
        roster_path=str(LEGACY_V2_ROSTER), roster_sha256="0" * 64, definitions_version="pull-request-definitions/2",
        seed="test-seed", main_size=10, ai_size=2, main_target_cap=100, ai_target_cap=150,
        per_author_cap=3, per_base_cap=2, main_candidate_factor=2.0, ai_candidate_factor=3.5,
        rules=dict(f.RULES),
    )
    values.update(overrides)
    return f.FrameSpec(**values)


def _member(number, month="2025-12", author="a", ai=()):
    return f.FrameMember(pr_number=number, created_at=f"{month}-01T00:00:00Z", month=month,
                         author=author, ai_evidence=tuple(ai))


def test_the_order_is_a_pure_function_of_seed_and_number():
    members = [_member(n) for n in range(100, 140)]
    first = [m.pr_number for m in f.seeded_order(members, "s1")]
    assert first == [m.pr_number for m in f.seeded_order(list(reversed(members)), "s1")]
    assert first != [m.pr_number for m in f.seeded_order(members, "s2")]


def test_month_quotas_are_proportional_and_sum_to_the_size():
    members = ([_member(n, "2025-06") for n in range(0, 10)] + [_member(n, "2025-07") for n in range(10, 40)]
               + [_member(n, "2025-08") for n in range(40, 100)])
    assert f.month_quotas(members, 10) == {"2025-06": 1, "2025-07": 3, "2025-08": 6}
    assert sum(f.month_quotas(members, 7).values()) == 7


def test_round_k_plus_1_extends_round_k():
    members = [_member(n, "2025-06" if n % 2 else "2025-07", ai=("label",) if n % 5 == 0 else ())
               for n in range(200)]
    spec = _spec()
    one, two = f.candidates(spec, members, 1), f.candidates(spec, members, 2)
    for key in one:
        assert two[key][: len(one[key])] == one[key]
        assert len(two[key]) >= len(one[key])
    assert set(one["ai"]) <= {m.pr_number for m in members if m.ai_evidence}


def test_the_seal_is_write_once_and_loading_checks_its_digests(tmp_path):
    spec = _spec()
    members = [_member(n) for n in range(5)]
    digest = f.seal(spec, {"used": []}, members, {"members": 5}, root=tmp_path)
    assert f.seal(spec, {"used": []}, members, {"members": 5}, root=tmp_path) == digest   # identical: no-op
    loaded_spec, loaded_members, loaded_digest = f.load_sealed(spec.name, root=tmp_path)
    assert (loaded_spec, loaded_members, loaded_digest) == (spec, members, digest)
    with pytest.raises(FileExistsError):
        f.seal(spec.model_copy(update={"seed": "other"}), {"used": []}, members, {"members": 5}, root=tmp_path)
    (tmp_path / spec.name / "frame.jsonl").write_text("{}\n")
    with pytest.raises(ValueError, match="sealed digest"):
        f.load_sealed(spec.name, root=tmp_path)


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullRequestStore(tmp_path_factory.mktemp("store"))
    seed_from_legacy(store)
    roster = load_roster(LEGACY_V2_ROSTER)
    members, report = f.frame_members(store, _spec(), dev_used=[], roster=roster)
    return store, roster, members, report


def _walk(seeded, spec, **kwargs):
    store, roster, members, _ = seeded
    return f.walk(spec, members, store=store, roster=roster, frame_seal_sha256="seal",
                  targets_of=kwargs.pop("targets_of", lambda episode: 5), **kwargs)


def test_the_frame_is_the_pre_gate_passes_minus_dev_used(seeded):
    store, roster, members, report = seeded
    assert report["members"] == len(members) > 100
    _, dev_report = f.frame_members(store, _spec(), dev_used=[members[0].pr_number], roster=roster)
    assert dev_report["by_reason"]["dev_used"] == 1 and dev_report["members"] == len(members) - 1


def test_the_walk_fills_the_main_strata_with_funnel_included_prs_under_the_caps(seeded):
    draw = _walk(seeded, _spec(per_author_cap=2))
    assert all(v is None for k, v in draw.stopped.items() if k.startswith("main:"))
    main = [a for a in draw.accepted if a.stratum.startswith("main:")]
    assert len(main) == 10
    assert max(collections.Counter(a.author for a in draw.accepted).values()) <= 2
    assert max(collections.Counter(a.base_sha for a in draw.accepted).values()) <= 2
    assert len({a.pr_number for a in draw.accepted}) == len(draw.accepted)
    assert all(s.reason.split(":")[0] in {"funnel", "targets>100", "targets>150", "author_cap",
                                          "base_cap", "in_main", "replaced"} for s in draw.skipped)
    assert draw.model_dump() == _walk(seeded, _spec(per_author_cap=2)).model_dump()   # deterministic


def test_the_ai_stratum_draws_ai_members_the_main_stratum_did_not_take(seeded):
    _, _, members, _ = seeded
    ai_members = {m.pr_number for m in members if m.ai_evidence}
    assert ai_members, "the seeded store has AI-disclosing PRs (33123, 33153)"
    draw = _walk(seeded, _spec(ai_size=1))
    main = {a.pr_number for a in draw.accepted if a.stratum.startswith("main:")}
    ai = [a for a in draw.accepted if a.stratum == "ai"]
    assert all(a.pr_number in ai_members and a.pr_number not in main for a in ai)
    assert {s.pr_number for s in draw.skipped if s.reason == "in_main"} == ai_members & main
    assert draw.stopped["ai"] is None or draw.stopped["ai"]["reason"] == "order_exhausted"


def test_the_target_cap_skips_and_the_walk_moves_on(seeded):
    draw = _walk(seeded, _spec(main_target_cap=3, ai_target_cap=3))
    assert not draw.accepted and all(s.reason.startswith(("targets>", "funnel", "in_main")) for s in draw.skipped)
    assert {v["reason"] for v in draw.stopped.values() if v} == {"order_exhausted"}


def test_the_walk_stops_at_an_uncollected_candidate_rather_than_skipping_it(seeded):
    store, roster, members, _ = seeded
    spec = _spec()
    first = f.strata_orders(spec, members)["main:2025-12"][0]
    ghost = first.model_copy(update={"pr_number": 999_999})
    # The same draw key position is not reachable for an invented number, so put it first by hand.
    draw = f.walk(spec, [ghost] + [m for m in members if m.pr_number != first.pr_number], store=store,
                  roster=roster, frame_seal_sha256="seal", targets_of=lambda episode: 5)
    stops = [v for v in draw.stopped.values() if v and v["reason"] == "needs_collection"]
    assert all(v["at"] == 999_999 for v in stops)


def test_a_replaced_pr_is_skipped_and_its_stratum_walks_on(seeded):
    before = _walk(seeded, _spec())
    victim = before.accepted[0]
    after = _walk(seeded, _spec(), replaced={victim.pr_number: "reviewed state does not compile"})
    assert all(v is None for k, v in after.stopped.items() if k.startswith("main:"))
    assert victim.pr_number not in {a.pr_number for a in after.accepted}
    assert any(s.pr_number == victim.pr_number and s.reason.startswith("replaced:") for s in after.skipped)


def test_a_base_file_missing_from_the_clone_stops_the_walk(seeded):
    draw = _walk(seeded, _spec(), targets_of=lambda episode: None)
    assert {v["reason"] for v in draw.stopped.values() if v} == {"needs_base"}


def test_git_hydrated_targets_reproduce_the_frozen_change_graphs(tmp_path):
    from pathlib import Path

    from src.mathlib_review.io import jsonl_rows
    from src.mathlib_review.paths import MATHLIB_CLONE
    from src.mathlib_review.schema import ReviewEpisodeInput

    release = Path("inputs/pr_review_v4/releases/dev-medium-0.5.0")
    if not (MATHLIB_CLONE / ".git").exists() and not (MATHLIB_CLONE / "HEAD").exists():
        pytest.skip("no local mathlib4 clone")
    graphs = {g["episode_id"]: len(g["targets"]) for g in jsonl_rows(release / "derived/change_graphs.jsonl")}
    episodes = [ReviewEpisodeInput.model_validate(row) for row in jsonl_rows(release / "input/episodes.jsonl")]
    assert {e.episode_id: f.change_targets(e, cache_root=tmp_path) for e in episodes} == graphs   # 16 of 16


def test_the_committed_pre_registration_is_intact_and_says_what_was_ruled():
    """eval-2025-06-2026-03-v1 was sealed 2026-09-24, before any candidate's tier 2 was read."""

    spec, members, digest = f.load_sealed("eval-2025-06-2026-03-v1")    # refuses a moved digest
    assert digest == "bcf93808a52879d216a873e2d5f810f4d4bb909f62e21d2360e99a56cb50f66f"
    assert (spec.created_from, spec.created_to) == ("2025-06-01", "2026-03-31")
    assert (spec.main_size, spec.ai_size, spec.main_target_cap, spec.ai_target_cap) == (50, 10, 100, 150)
    assert (spec.per_author_cap, spec.per_base_cap) == (3, 2)
    assert spec.store_content_sha256.startswith("f2d2beb6")
    assert len(members) == 9939
    assert sum(f.month_quotas(members, spec.main_size).values()) == 50
