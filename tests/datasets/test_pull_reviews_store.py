"""The store holds what the frozen caches hold, byte for byte, and never touches them.

Seeding copies the 201 bundles and 223 compares every v4 release was built from. Three things must
hold for the store to replace the caches as a source: every bundle reassembles to exactly the
dictionary it was, `null` kept distinct from `[]`; every compare keeps its exact bytes, because
episodes hash them; and the caches themselves -- hashed as trees by eleven and eight frozen
manifests -- are unchanged afterwards.
"""

from __future__ import annotations

import json

import pytest

from src.datasets.pull_reviews.seed import seed_from_legacy
from src.datasets.pull_reviews.store import (
    ImmutableEndpointError, IncompletePR, PullReviewStore, StoreError,
)
from src.mathlib_review.io import sha256_directory, sha256_file
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_COMPARES


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    if not LEGACY_V2_BUNDLES.is_dir():
        pytest.skip("no legacy bundle cache")
    store = PullReviewStore(tmp_path_factory.mktemp("store"))
    report = seed_from_legacy(store)
    return store, report


def test_seeding_reports_every_pr_and_compare(seeded):
    store, report = seeded
    assert report["prs"] == 201 and len(store.numbers()) == 201
    assert report["compare_files"] == 223 and report["compares_unmapped"] == []
    assert report["compares_shared_by_two_prs"] == 7
    assert report["legacy_caches_unchanged"] is True


def test_every_bundle_reassembles_exactly_with_null_kept_distinct_from_empty(seeded):
    store, _ = seeded
    nulls = 0
    for bundle_path in sorted(LEGACY_V2_BUNDLES.glob("pr_*.json")):
        legacy = json.loads(bundle_path.read_text())
        number = legacy["pr"]["number"]
        assert store.load_bundle(number) == legacy, number
        assert store.bundle_sha256(number) == sha256_file(bundle_path)
        nulls += sum(1 for key in ("body_edits", "review_threads") if legacy[key] is None)
    assert nulls == 2     # measured: one null body_edits, one null review_threads


def test_every_compare_keeps_its_exact_bytes(seeded):
    store, _ = seeded
    checked = 0
    for number in store.numbers():
        for head in store.ledger(number)["compares"]:
            payload, sha = store.compare(number, head)
            legacy = LEGACY_V2_COMPARES / f"master...{head}.json"
            assert sha == sha256_file(legacy)
            assert payload == json.loads(legacy.read_text())
            checked += 1
    assert checked == 230          # 223 files, seven stored under two PRs


def test_seeded_prs_are_complete_to_tier_2_with_no_listing(seeded):
    store, _ = seeded
    for number in store.numbers():
        assert store.tiers(number) == {1, 2}      # the listing row is a tier-0 fetch, not a bundle field


def test_reseeding_is_a_no_op(seeded):
    store, _ = seeded
    digest = store.content_digest()
    again = seed_from_legacy(store)
    assert again["endpoints_written"] == 0 and again["compares_written"] == 0
    assert store.content_digest() == digest


def test_the_caches_are_not_touched(seeded):
    """Hashes as `verify_frozen` computes them. Seeding already asserts this internally; this
    states it where a reader of the tests will look for it."""

    import json as _json
    manifest = _json.loads(open("inputs/pr_review_v4/releases/dev-raw-0.3.0/manifest.json").read())
    pins = {ref["path"]: ref["sha256"] for ref in manifest["sources"]}
    assert sha256_directory(LEGACY_V2_BUNDLES) == pins[str(LEGACY_V2_BUNDLES)]
    assert sha256_directory(LEGACY_V2_COMPARES) == pins[str(LEGACY_V2_COMPARES)]


def test_an_endpoint_is_never_rewritten(tmp_path):
    store = PullReviewStore(tmp_path)
    store.write_endpoint(1, "reviews", [{"id": 1}], request="r", fetched_at="t", source="github")
    assert store.write_endpoint(1, "reviews", [{"id": 1}], request="r", fetched_at="t2",
                               source="github") is False          # identical: no-op
    with pytest.raises(ImmutableEndpointError):
        store.write_endpoint(1, "reviews", [{"id": 2}], request="r", fetched_at="t3", source="github")
    with pytest.raises(ImmutableEndpointError):
        store.write_endpoint(1, "reviews", None, request="r", fetched_at="t4", source="github")


def test_a_null_endpoint_has_no_file_and_reads_back_as_none(tmp_path):
    store = PullReviewStore(tmp_path)
    store.write_endpoint(5, "body_edits", None, request="graphql", fetched_at="t", source="github")
    store.write_endpoint(5, "review_threads", [], request="graphql", fetched_at="t", source="github")
    assert store.read(5, "body_edits") is None
    assert store.read(5, "review_threads") == []
    assert not (store.pr_dir(5) / "body_edits.jsonl").exists()
    assert (store.pr_dir(5) / "review_threads.jsonl").read_bytes() == b""


def test_reading_an_unfetched_tier_raises(tmp_path):
    store = PullReviewStore(tmp_path)
    store.write_endpoint(7, "review_comments", [], request="r", fetched_at="t", source="github")
    with pytest.raises(IncompletePR):
        store.read(7, "commits")
    with pytest.raises(IncompletePR):
        store.load_bundle(7)


def test_a_store_inside_the_frozen_caches_is_refused():
    with pytest.raises(StoreError) as excinfo:
        PullReviewStore(LEGACY_V2_BUNDLES.parent / "store")
    assert "verify_frozen" in str(excinfo.value)
