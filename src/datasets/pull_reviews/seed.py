"""Seed the store from the frozen v2 caches: the 201 bundles and 223 compares, read-only.

These are the exact bytes every frozen v4 release was built from, so seeding them -- rather than
refetching those PRs -- is what lets the store reproduce `dev-raw-0.3.0` byte for byte, and what
lets the retrieval cutoff move off the frozen cache without changing a single existing cutoff.

Compares are copied **verbatim**: the episode builder hashes the compare file into each episode's
provenance, so a re-serialised copy would change every episode. Bundles are split into per-endpoint
files, and the legacy file's sha is recorded so `PullReviewStore.bundle_sha256` returns it.

A compare is keyed by head sha, not PR. Seven of the 223 heads are in two PRs' commit lists
(stacked PRs sharing a commit), so those are stored in both PR directories -- each PR stays
self-contained, and the bytes, hence the sha, are identical in both.

The caches are read and never written, and `seed_from_legacy` proves it: it hashes both directories
before and after and raises if either moved.

    python -m src.datasets.pull_reviews.seed
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any, Dict

from src.datasets.pull_reviews.store import BUNDLE_ENDPOINTS, PullReviewStore
from src.mathlib_review.io import display_path, sha256_bytes, sha256_directory
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_COMPARES, assert_repo_root

SOURCE_BUNDLE = "legacy_bundle_cache"
SOURCE_COMPARE = "legacy_compare_cache"


def seed_from_legacy(store: PullReviewStore, *, bundles: Path = LEGACY_V2_BUNDLES,
                     compares: Path = LEGACY_V2_COMPARES) -> Dict[str, Any]:
    before = (sha256_directory(bundles), sha256_directory(compares))
    written = collections.Counter()
    head_to_prs: Dict[str, set] = collections.defaultdict(set)
    prs = []
    for bundle_path in sorted(bundles.glob("pr_*.json")):
        raw = bundle_path.read_bytes()
        bundle = json.loads(raw)
        number = int(bundle["pr"]["number"])
        prs.append(number)
        fetched_at = str(bundle.get("fetched_at") or "")
        for endpoint in BUNDLE_ENDPOINTS:
            if store.write_endpoint(number, endpoint, bundle.get(endpoint),
                                    request=f"{SOURCE_BUNDLE}:{endpoint}",
                                    fetched_at=fetched_at, source=SOURCE_BUNDLE):
                written["endpoints"] += 1
        store.record_legacy_bundle(number, {
            "path": display_path(bundle_path), "sha256": sha256_bytes(raw),
            "bundle_version": bundle.get("bundle_version"), "fetched_at": bundle.get("fetched_at"),
        })
        for commit in bundle.get("commits") or []:
            head_to_prs[str(commit.get("sha"))].add(number)

    unmapped = []
    shared = 0
    for compare_path in sorted(compares.glob("*.json")):
        base_ref, head = compare_path.name[: -len(".json")].split("...")
        owners = head_to_prs.get(head)
        if not owners:
            unmapped.append(compare_path.name)
            continue
        shared += len(owners) > 1
        raw = compare_path.read_bytes()
        for number in sorted(owners):
            if store.write_compare(number, head, raw, base_ref=base_ref,
                                   request=f"{SOURCE_COMPARE}:{display_path(compare_path)}",
                                   fetched_at="", source=SOURCE_COMPARE):
                written["compares"] += 1

    after = (sha256_directory(bundles), sha256_directory(compares))
    if after != before:
        raise RuntimeError("a frozen v2 cache changed during seeding; verify_frozen will fail")
    return {
        "prs": len(prs), "endpoints_written": written["endpoints"],
        "compares_written": written["compares"], "compare_files": len(list(compares.glob("*.json"))),
        "compares_shared_by_two_prs": shared, "compares_unmapped": unmapped,
        "legacy_caches_unchanged": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--store", type=Path, default=None)
    args = parser.parse_args()
    assert_repo_root()
    store = PullReviewStore(args.store) if args.store else PullReviewStore()
    print(json.dumps(seed_from_legacy(store), indent=2))


if __name__ == "__main__":
    main()
