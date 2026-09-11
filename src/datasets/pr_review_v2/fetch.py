"""
Stages A and B: candidate selection and raw per-PR bundle fetching.

Bundles are cached as JSON on disk so that derivation (stage C) and delta
extraction (stage D) can be iterated on without touching the GitHub API again.
Nothing in a bundle is interpreted here — derivation logic lives in derive.py.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import PRReviewV2Config
from .github import GitHubClient, GitHubError

BUNDLE_VERSION = 1

from src.datasets.pull_reviews.github import (  # noqa: E402
    BODY_EDITS_QUERY as _BODY_EDITS_QUERY,
    REVIEW_THREADS_QUERY as _THREADS_QUERY,
    compact_compare,
)


def search_candidate_numbers(client: GitHubClient, config: PRReviewV2Config) -> List[int]:
    """Stage A: merged PRs in the date window (+ optional closed-unmerged slice)."""
    if config.pr_numbers:
        return list(config.pr_numbers)

    def run_search(extra_qualifiers: str, date_qualifier: str) -> List[int]:
        window = ""
        if config.start_date and config.end_date:
            window = f" {date_qualifier}:{config.start_date}..{config.end_date}"
        elif config.start_date:
            window = f" {date_qualifier}:>={config.start_date}"
        elif config.end_date:
            window = f" {date_qualifier}:<={config.end_date}"
        query = f"repo:{config.repo_slug} is:pr {extra_qualifiers}{window}"
        sort_order = "desc" if config.pr_order == "newest" else "asc"
        numbers: List[int] = []
        for item in client.paginate(
            "/search/issues",
            params={"q": query, "sort": "created", "order": sort_order},
            max_pages=config.max_search_pages,
        ):
            number = item.get("number")
            if number:
                numbers.append(int(number))
        return numbers

    # Mathlib4 PRs land via bors, which closes the PR (title rewritten to
    # "[Merged by Bors] …") instead of merging it — `is:merged` matches almost
    # nothing. Search closed PRs and let derivation classify merged vs unmerged.
    candidates = run_search("is:closed", "closed")

    seen, ordered = set(), []
    for number in candidates:
        if number not in seen:
            seen.add(number)
            ordered.append(number)
    return ordered[: config.max_prs]


def bundle_path(config: PRReviewV2Config, pr_number: int) -> Path:
    return config.cache_dir / "bundles" / f"pr_{pr_number}.json"


def _refuse_frozen_cache(target: Path) -> None:
    """The default cache *is* the frozen one. Eleven release manifests hash
    `data/pr_review_v2/cache/bundles` and eight hash `.../compares` as trees, so writing one new
    file there fails `verify_frozen` for every v4 release -- and `main fetch` over a new window did
    exactly that by default. Reading what is already cached is fine; new PRs go to the PR store
    (`python -m src.datasets.pull_reviews.collect`)."""

    from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_COMPARES

    frozen = {LEGACY_V2_BUNDLES.resolve(), LEGACY_V2_COMPARES.resolve()}
    if target.parent.resolve() in frozen:
        raise PermissionError(
            f"refusing to write {target}: that cache is hashed by frozen release manifests, so a new "
            "file breaks verify_frozen. Collect new PRs into the PR store instead: "
            "`python -m src.datasets.pull_reviews.collect --start … --end …`.")


def fetch_pr_bundle(
    client: GitHubClient,
    config: PRReviewV2Config,
    pr_number: int,
    *,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Stage B: fetch (or load cached) raw API payloads for one PR."""
    path = bundle_path(config, pr_number)
    if path.exists() and not refresh:
        return json.loads(path.read_text())
    _refuse_frozen_cache(path)

    repo = f"/repos/{config.repo_slug}"
    bundle: Dict[str, Any] = {
        "bundle_version": BUNDLE_VERSION,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "pr": client.get_json(f"{repo}/pulls/{pr_number}"),
        "reviews": client.paginate_all(f"{repo}/pulls/{pr_number}/reviews"),
        "review_comments": client.paginate_all(f"{repo}/pulls/{pr_number}/comments"),
        "issue_comments": client.paginate_all(f"{repo}/issues/{pr_number}/comments"),
        "commits": client.paginate_all(f"{repo}/pulls/{pr_number}/commits"),
        "files": client.paginate_all(f"{repo}/pulls/{pr_number}/files"),
        "timeline": client.paginate_all(f"{repo}/issues/{pr_number}/timeline"),
        "review_threads": None,
        "body_edits": None,
    }

    if config.use_graphql_enrichment and client.authenticated:
        try:
            bundle["review_threads"] = _fetch_review_threads(client, config, pr_number)
            bundle["body_edits"] = _fetch_body_edits(client, config, pr_number)
        except GitHubError:
            pass  # enrichment is optional; derivation tags records that lack it

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, ensure_ascii=False))
    return bundle


def _fetch_review_threads(
    client: GitHubClient, config: PRReviewV2Config, pr_number: int
) -> List[Dict[str, Any]]:
    threads: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        data = client.graphql(
            _THREADS_QUERY,
            {"owner": config.repo_owner, "name": config.repo_name, "number": pr_number, "cursor": cursor},
        )
        connection = data["repository"]["pullRequest"]["reviewThreads"]
        for node in connection["nodes"]:
            threads.append(
                {
                    "thread_id": node["id"],
                    "is_resolved": node["isResolved"],
                    "comment_ids": [c["databaseId"] for c in node["comments"]["nodes"]],
                }
            )
        if not connection["pageInfo"]["hasNextPage"]:
            return threads
        cursor = connection["pageInfo"]["endCursor"]


def _fetch_body_edits(
    client: GitHubClient, config: PRReviewV2Config, pr_number: int
) -> List[Dict[str, Any]]:
    data = client.graphql(
        _BODY_EDITS_QUERY,
        {"owner": config.repo_owner, "name": config.repo_name, "number": pr_number},
    )
    nodes = data["repository"]["pullRequest"]["userContentEdits"]["nodes"] or []
    return [{"edited_at": n.get("editedAt") or n.get("createdAt")} for n in nodes if n]


def fetch_compare(
    client: GitHubClient,
    config: PRReviewV2Config,
    base_ref: str,
    head_sha: str,
    *,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Cached three-dot compare: diff(merge_base(base_ref, head_sha), head_sha).

    This is exactly the patch-level P of spec §3.6 when base_ref is the target
    branch — the compare API diffs against the merge base, so upstream churn
    merged into the PR branch never appears.
    """
    cache_file = config.cache_dir / "compares" / f"{base_ref.replace('/', '_')}...{head_sha}.json"
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text())
    _refuse_frozen_cache(cache_file)

    payload = client.get_json(
        f"/repos/{config.repo_slug}/compare/{base_ref}...{head_sha}", params={"per_page": 100}
    )
    # `files` is capped at 300 and not paginated via Link headers on this endpoint;
    # the funnel's max_changed_files (≤30) keeps us far from the cap.
    compact = compact_compare(payload)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(compact, ensure_ascii=False))
    return compact
