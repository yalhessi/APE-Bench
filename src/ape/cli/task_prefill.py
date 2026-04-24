"""Task-specific helpers for interactive CLI task creation."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ape.utils.logging import create_logger


PR_LIVE_TASK_TYPES = {
    "lean_pr_review",
    "skilled_pr_review",
    "skilled_policy_pr_review",
    "lean_pr_split",
    "skilled_pr_split",
    "skilled_policy_pr_split",
}


def build_pr_task_data(task_type: str, pr_url: str, commit: str) -> dict[str, Any]:
    """Build a live PR-shaped task record from a PR URL and commit SHA."""
    normalized_task_type = str(task_type or "").strip()
    if normalized_task_type not in PR_LIVE_TASK_TYPES:
        supported = ", ".join(sorted(PR_LIVE_TASK_TYPES))
        raise ValueError(f"Unsupported PR live task type `{normalized_task_type}`. Expected one of: {supported}")

    normalized_pr_url = str(pr_url or "").strip()
    repo_owner, repo_name, pr_number = _parse_github_pr_url(normalized_pr_url)
    normalized_commit = str(commit or "").strip()
    if not normalized_commit:
        raise ValueError("commit must be non-empty")

    dataset_config_class, collector_class = _get_pr_review_dataset_helpers()
    collector = collector_class(
        config=dataset_config_class(repo_owner=repo_owner, repo_name=repo_name),
        logger=create_logger(to_console=False),
    )
    try:
        return collector.build_live_pr_task_data(
            task_type=normalized_task_type,
            pr_number=pr_number,
            snapshot_head_sha=normalized_commit,
            pr_url=normalized_pr_url,
        )
    finally:
        collector.close()


def build_pr_review_task_data(pr_url: str, commit: str) -> dict[str, Any]:
    """Build a lean_pr_review task record from a PR URL and commit SHA."""
    return build_pr_task_data(task_type="lean_pr_review", pr_url=pr_url, commit=commit)


def build_pr_split_task_data(pr_url: str, commit: str) -> dict[str, Any]:
    """Build a lean_pr_split task record from a PR URL and commit SHA."""
    return build_pr_task_data(task_type="lean_pr_split", pr_url=pr_url, commit=commit)


def _get_pr_review_dataset_helpers():
    """Load PR review dataset helpers lazily to keep CLI startup light."""
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)

    module = importlib.import_module("src.datasets.pr_review")
    return module.PRReviewDatasetConfig, module.PRReviewDataCollector


def _parse_github_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into repository owner, name, and PR number."""
    normalized_url = str(pr_url or "").strip()
    if not normalized_url:
        raise ValueError("pr_url must be non-empty")

    parsed = urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("pr_url must start with http:// or https://")
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise ValueError("pr_url must point to github.com")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2] != "pull":
        raise ValueError("pr_url must have the form https://github.com/<owner>/<repo>/pull/<number>")

    repo_owner, repo_name, _, pr_number_text = parts[:4]
    try:
        pr_number = int(pr_number_text)
    except ValueError as exc:
        raise ValueError("pr_url must end with a numeric pull request number") from exc

    return repo_owner, repo_name, pr_number
