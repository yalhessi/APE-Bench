"""
PR review benchmark data collector.

Collects real Mathlib pull requests from GitHub and derives ground-truth labels
from maintainer feedback. Supports temporal snapshots anchored to maintainer
review decision timestamps.
"""

import json
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, TYPE_CHECKING

import httpx

from ..external_benchmarks.github_utils import fetch_file_from_github, get_default_target
from .config import PRReviewDatasetConfig
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


MAINTAINER_ASSOCIATIONS = {"MEMBER", "OWNER", "COLLABORATOR"}
ACTIONABLE_REVIEW_STATES = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}

DEFAULT_ISSUE_TAGS = [
    "semantic_incorrectness",
    "requirement_mismatch",
    "scope_control_violation",
    "proof_fragility",
    "insufficient_documentation",
    "insufficient_tests",
    "library_integration_issue",
    "deprecated_api_usage",
    "performance_regression",
    "style_or_readability",
]

ISSUE_TAG_PATTERNS = {
    "semantic_incorrectness": [
        r"\bwrong\b",
        r"\bincorrect\b",
        r"\bunsound\b",
        r"\bfails?\b",
        r"\bbug\b",
        r"\bdoesn['’]t compile\b",
    ],
    "requirement_mismatch": [
        r"\bmissing\b",
        r"\bnot enough\b",
        r"\bdoesn['’]t implement\b",
        r"\bneeds? to\b",
        r"\bshould also\b",
    ],
    "scope_control_violation": [
        r"\bout of scope\b",
        r"\bunrelated\b",
        r"\btoo (?:broad|large|many)\b",
        r"\bunnecessary refactor\b",
    ],
    "proof_fragility": [
        r"\bfragile\b",
        r"\bbrittle\b",
        r"\bunstable\b",
    ],
    "insufficient_documentation": [
        r"\bdoc(?:s|umentation)?\b",
        r"\bplease document\b",
        r"\badd (?:a )?comment\b",
    ],
    "insufficient_tests": [
        r"\btest(?:s|ing)?\b",
        r"\bregression test\b",
        r"\bcoverage\b",
    ],
    "library_integration_issue": [
        r"\bimport\b",
        r"\bnamespace\b",
        r"\bAPI\b",
        r"\bbackward compatible\b",
    ],
    "deprecated_api_usage": [
        r"\bdeprecated\b",
        r"\bobsolete\b",
        r"\blegacy\b",
    ],
    "performance_regression": [
        r"\bperformance\b",
        r"\bslow\b",
        r"\btimeout\b",
    ],
    "style_or_readability": [
        r"\bstyle\b",
        r"\breadability\b",
        r"\bnaming\b",
        r"\bformat(?:ting)?\b",
        r"\bnit\b",
    ],
}

APPROVAL_COMMENT_PATTERNS = [
    r"\bbors\s+r\+",
    r"\bbors\s+d\+",
    r"\blgtm\b",
    r"\blooks good\b",
    r"\bapproved?\b",
]

DEPENDENCY_LINE_PATTERN = re.compile(r"^\s*-\s*\[[ xX]?\]\s*depends on:\s*.+$", re.IGNORECASE)
DEPENDENCY_PLACEHOLDER_PATTERN = re.compile(
    r"^\s*-\s*\[[ xX]?\]\s*depends on:\s*#(?:abc|xyz)\s*\[optional extra text\]\s*$",
    re.IGNORECASE,
)
BUTTON_LINE_PATTERNS = [
    re.compile(r"^\s*\[!\[.*\]\(.*\)\]\(.*\)\s*$"),
    re.compile(r"^\s*build with ona\b.*$", re.IGNORECASE),
    re.compile(r"^\s*open in gitpod\b.*$", re.IGNORECASE),
]


def _normalize_issue_tag(tag: str) -> str:
    normalized = (tag or "").strip().lower()
    normalized = re.sub(r"[\s\-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        normalized = _normalize_issue_tag(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _is_bot_login(user_login: Optional[str]) -> bool:
    if not user_login:
        return False
    lowered = user_login.lower()
    return lowered.endswith("[bot]") or lowered.endswith("-bot") or lowered == "bors"


def _is_human_non_author(user_login: Optional[str], pr_author_login: Optional[str]) -> bool:
    if not user_login:
        return False
    if _is_bot_login(user_login):
        return False
    if pr_author_login and user_login.lower() == pr_author_login.lower():
        return False
    return True


def _is_lean_file(path: str) -> bool:
    return str(path or "").lower().endswith(".lean")


def _date_key_in_range(date_value: Optional[str], start_date: Optional[str], end_date: Optional[str]) -> bool:
    if not date_value:
        return False
    day = date_value[:10]
    if start_date and day < start_date:
        return False
    if end_date and day > end_date:
        return False
    return True


def _build_date_qualifier(date_field: str, start_date: Optional[str], end_date: Optional[str]) -> Optional[str]:
    if not start_date and not end_date:
        return None
    if start_date and end_date:
        return f"{date_field}:{start_date}..{end_date}"
    if start_date:
        return f"{date_field}:>={start_date}"
    return f"{date_field}:<={end_date}"


def _build_review_rationale(feedback_items: List[Dict[str, Any]], max_chars: int) -> str:
    snippets: List[str] = []
    for item in feedback_items:
        body = (item.get("body") or "").strip()
        if not body:
            continue
        body = re.sub(r"\s+", " ", body)
        kind = item.get("kind", "feedback")
        user = item.get("user", "unknown")
        state = item.get("state")
        prefix = f"[{kind}:{user}"
        if state:
            prefix += f":{state}"
        prefix += "] "
        snippets.append(prefix + body)

        combined = "\n".join(snippets)
        if len(combined) >= max_chars:
            return combined[:max_chars].rstrip()
    return "\n".join(snippets)[:max_chars].rstrip()


def _infer_issue_tags_from_feedback(feedback_texts: Sequence[str]) -> List[str]:
    if not feedback_texts:
        return []
    merged = "\n".join(feedback_texts).lower()
    tags: List[str] = []
    for tag, patterns in ISSUE_TAG_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, merged):
                tags.append(tag)
                break
    return _dedupe_preserve_order(tags)


def _has_approval_signal(feedback_items: Sequence[Dict[str, Any]]) -> bool:
    merged = "\n".join((item.get("body") or "") for item in feedback_items if item.get("body"))
    if not merged.strip():
        return False
    lowered = merged.lower()
    return any(re.search(pattern, lowered) for pattern in APPROVAL_COMMENT_PATTERNS)


def _extract_pr_description_and_dependencies(body: Optional[str]) -> Tuple[str, List[str]]:
    raw_body = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    if not raw_body.strip():
        return "", []

    cleaned = re.sub(r"<!--.*?-->", "", raw_body, flags=re.DOTALL)
    cleaned_lines: List[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if any(pattern.match(stripped) for pattern in BUTTON_LINE_PATTERNS):
            continue
        if stripped == "---":
            continue
        cleaned_lines.append(line.rstrip())

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    if cleaned == "---":
        cleaned = ""
    elif cleaned.startswith("---\n"):
        cleaned = cleaned[4:].lstrip()
    elif cleaned.endswith("\n---"):
        cleaned = cleaned[:-4].rstrip()

    dependencies: List[str] = []
    seen_dependencies: Set[str] = set()
    for line in cleaned.splitlines():
        stripped = line.strip()
        if DEPENDENCY_LINE_PATTERN.match(stripped) and not DEPENDENCY_PLACEHOLDER_PATTERN.match(stripped):
            key = stripped.lower()
            if key not in seen_dependencies:
                seen_dependencies.add(key)
                dependencies.append(stripped)

    return cleaned, dependencies


def _derive_merge_ready(
    pr: Dict[str, Any],
    maintainer_reviews: List[Dict[str, Any]],
    *,
    allow_merge_outcome_fallback: bool = True,
) -> Tuple[bool, str, Dict[str, str]]:
    latest_state_by_user: Dict[str, str] = {}
    sorted_reviews = sorted(
        maintainer_reviews,
        key=lambda r: (r.get("submitted_at") or "", r.get("id") or 0),
    )

    for review in sorted_reviews:
        raw_user = review.get("user")
        if isinstance(raw_user, dict):
            user = raw_user.get("login")
        else:
            user = raw_user
        state = (review.get("state") or "").upper()
        if not user or state not in ACTIONABLE_REVIEW_STATES:
            continue
        latest_state_by_user[user] = state

    if latest_state_by_user:
        if any(state == "CHANGES_REQUESTED" for state in latest_state_by_user.values()):
            return False, "maintainer_reviews_final_state", latest_state_by_user
        if any(state == "APPROVED" for state in latest_state_by_user.values()):
            return True, "maintainer_reviews_final_state", latest_state_by_user

    if allow_merge_outcome_fallback:
        if pr.get("merged_at"):
            return True, "merge_outcome_fallback", latest_state_by_user
        return False, "merge_outcome_fallback", latest_state_by_user

    return False, "insufficient_actionable_review_state", latest_state_by_user


def _collect_review_events(
    maintainer_reviews: List[Dict[str, Any]],
    decision_review_states: Sequence[str],
    max_review_events_per_pr: int,
) -> List[Dict[str, Any]]:
    allowed_states = {str(state or "").upper() for state in decision_review_states}
    events: List[Dict[str, Any]] = []
    for review in sorted(maintainer_reviews, key=lambda r: (r.get("submitted_at") or "", r.get("id") or 0)):
        state = (review.get("state") or "").upper()
        submitted_at = review.get("submitted_at")
        if state not in allowed_states or not submitted_at:
            continue
        events.append(
            {
                "kind": "review_event",
                "review_id": review.get("id"),
                "state": state,
                "submitted_at": submitted_at,
                "user": review.get("user"),
                "commit_id": review.get("commit_id"),
                "html_url": review.get("html_url"),
            }
        )

    if max_review_events_per_pr > 0 and len(events) > max_review_events_per_pr:
        events = events[-max_review_events_per_pr:]
    return events


def _collect_comment_fallback_events(
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    max_review_events_per_pr: int,
    *,
    include_issue_comments: bool = True,
    include_review_comments: bool = True,
) -> List[Dict[str, Any]]:
    comment_items: List[Dict[str, Any]] = []
    if include_issue_comments:
        comment_items.extend(maintainer_feedback["issue_comments"])
    if include_review_comments:
        comment_items.extend(maintainer_feedback["review_comments"])
    comment_items.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))

    events: List[Dict[str, Any]] = []
    for item in comment_items:
        submitted_at = item.get("submitted_at")
        if not submitted_at:
            continue
        review_id = item.get("pull_request_review_id")
        if review_id is None:
            review_id = f"{item.get('kind')}_{item.get('id')}"
        commit_id = item.get("commit_id") or item.get("original_commit_id")
        events.append(
            {
                "kind": "review_event",
                "review_id": review_id,
                "state": "COMMENTED",
                "submitted_at": submitted_at,
                "user": item.get("user"),
                "commit_id": commit_id,
                "html_url": item.get("html_url"),
                "source_kind": item.get("kind"),
                "source_comment_id": item.get("id"),
            }
        )

    if max_review_events_per_pr > 0 and len(events) > max_review_events_per_pr:
        events = events[-max_review_events_per_pr:]
    return events


def _merge_round_anchor_events(
    review_events: List[Dict[str, Any]],
    comment_anchor_events: List[Dict[str, Any]],
    *,
    max_review_events_per_pr: int,
) -> List[Dict[str, Any]]:
    merged = list(review_events) + list(comment_anchor_events)
    merged.sort(key=lambda e: (e.get("submitted_at") or "", str(e.get("review_id") or "")))

    deduped: List[Dict[str, Any]] = []
    seen_ids: Set[Tuple[Any, Any]] = set()
    for event in merged:
        marker = (event.get("source_kind") or event.get("kind"), event.get("review_id"))
        if marker in seen_ids:
            continue
        seen_ids.add(marker)
        deduped.append(event)

    if max_review_events_per_pr > 0 and len(deduped) > max_review_events_per_pr:
        deduped = deduped[-max_review_events_per_pr:]
    return deduped


def _slice_feedback_until(
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    cutoff_at: Optional[str],
) -> Dict[str, List[Dict[str, Any]]]:
    if not cutoff_at:
        return {
            "reviews": list(maintainer_feedback["reviews"]),
            "issue_comments": list(maintainer_feedback["issue_comments"]),
            "review_comments": list(maintainer_feedback["review_comments"]),
        }

    def take(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sliced: List[Dict[str, Any]] = []
        for item in items:
            submitted_at = item.get("submitted_at")
            if not submitted_at or submitted_at <= cutoff_at:
                sliced.append(item)
        return sliced

    return {
        "reviews": take(maintainer_feedback["reviews"]),
        "issue_comments": take(maintainer_feedback["issue_comments"]),
        "review_comments": take(maintainer_feedback["review_comments"]),
    }


def _filter_feedback_by_window(
    items: List[Dict[str, Any]],
    *,
    start_exclusive: Optional[str],
    end_inclusive: Optional[str],
    user: Optional[str] = None,
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for item in items:
        submitted_at = item.get("submitted_at")
        if end_inclusive and submitted_at and submitted_at > end_inclusive:
            continue
        if start_exclusive and submitted_at and submitted_at <= start_exclusive:
            continue
        if user and item.get("user") != user:
            continue
        filtered.append(item)
    return filtered


def _build_round_feedback(
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    *,
    review_events: List[Dict[str, Any]],
    round_start_exclusive: Optional[str],
    round_end_inclusive: Optional[str],
) -> Dict[str, List[Dict[str, Any]]]:
    review_ids = {event.get("review_id") for event in review_events if event.get("review_id") is not None}
    reviewers = {event.get("user") for event in review_events if event.get("user")}

    round_reviews: List[Dict[str, Any]] = []
    if review_ids:
        round_reviews = [
            review for review in maintainer_feedback["reviews"] if review.get("id") in review_ids
        ]
    if not round_reviews and reviewers:
        round_reviews = [
            review
            for review in maintainer_feedback["reviews"]
            if review.get("user") in reviewers
            and (
                not round_end_inclusive
                or not review.get("submitted_at")
                or review.get("submitted_at") <= round_end_inclusive
            )
            and (
                not round_start_exclusive
                or not review.get("submitted_at")
                or review.get("submitted_at") > round_start_exclusive
            )
        ]

    round_review_comments: List[Dict[str, Any]] = []
    if review_ids:
        round_review_comments = [
            comment
            for comment in maintainer_feedback["review_comments"]
            if comment.get("pull_request_review_id") in review_ids
        ]

    additional_round_review_comments = _filter_feedback_by_window(
        maintainer_feedback["review_comments"],
        start_exclusive=round_start_exclusive,
        end_inclusive=round_end_inclusive,
        user=None,
    )
    round_review_comments.extend(additional_round_review_comments)
    deduped_round_review_comments: List[Dict[str, Any]] = []
    seen_review_comment_ids: Set[Any] = set()
    for comment in round_review_comments:
        marker = comment.get("id")
        if marker in seen_review_comment_ids:
            continue
        seen_review_comment_ids.add(marker)
        deduped_round_review_comments.append(comment)
    round_review_comments = deduped_round_review_comments

    round_issue_comments = _filter_feedback_by_window(
        maintainer_feedback["issue_comments"],
        start_exclusive=round_start_exclusive,
        end_inclusive=round_end_inclusive,
        user=None,
    )

    round_reviews.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    round_issue_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    round_review_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))

    return {
        "reviews": round_reviews,
        "issue_comments": round_issue_comments,
        "review_comments": round_review_comments,
    }


def _parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


def _group_review_events(review_events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    if not review_events:
        return []
    sorted_events = sorted(review_events, key=lambda e: (e.get("submitted_at") or "", e.get("review_id") or 0))

    groups: List[List[Dict[str, Any]]] = []
    current_group: List[Dict[str, Any]] = []
    for event in sorted_events:
        if not current_group:
            current_group = [event]
            continue

        prev = current_group[-1]
        prev_commit = prev.get("commit_id")
        this_commit = event.get("commit_id")
        same_commit = bool(prev_commit and this_commit and prev_commit == this_commit)

        should_merge = same_commit
        if not should_merge:
            prev_user = prev.get("user")
            this_user = event.get("user")
            prev_ts = _parse_timestamp(prev.get("submitted_at"))
            this_ts = _parse_timestamp(event.get("submitted_at"))
            if prev_user and this_user and prev_user == this_user and prev_ts and this_ts:
                seconds = (this_ts - prev_ts).total_seconds()
                # Coalesce fragmented review submissions that are very close in time.
                if 0 <= seconds <= 300:
                    should_merge = True

        if should_merge:
            current_group.append(event)
            continue

        groups.append(current_group)
        current_group = [event]

    if current_group:
        groups.append(current_group)
    return groups


def _extend_round_end_with_followups(
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    *,
    review_events: List[Dict[str, Any]],
    round_end_inclusive: Optional[str],
    next_group_start: Optional[str],
    max_followup_seconds: int = 600,
) -> Optional[str]:
    if not round_end_inclusive:
        return round_end_inclusive
    base_end = _parse_timestamp(round_end_inclusive)
    if not base_end:
        return round_end_inclusive

    next_start_dt = _parse_timestamp(next_group_start)
    reviewer_users = {event.get("user") for event in review_events if event.get("user")}
    if not reviewer_users:
        return round_end_inclusive

    extended_end = base_end
    followup_items = maintainer_feedback["issue_comments"] + maintainer_feedback["review_comments"] + maintainer_feedback["reviews"]
    for item in followup_items:
        if item.get("user") not in reviewer_users:
            continue
        submitted_at = item.get("submitted_at")
        submitted_dt = _parse_timestamp(submitted_at)
        if not submitted_dt or submitted_dt <= base_end:
            continue
        if next_start_dt and submitted_dt >= next_start_dt:
            continue
        if (submitted_dt - base_end).total_seconds() > max_followup_seconds:
            continue
        if submitted_dt > extended_end:
            extended_end = submitted_dt

    return extended_end.isoformat().replace("+00:00", "Z")


def _build_round_conversation(
    maintainer_round_feedback: Dict[str, List[Dict[str, Any]]],
    *,
    author_feedback: Dict[str, List[Dict[str, Any]]],
    review_events: List[Dict[str, Any]],
    round_start_exclusive: Optional[str],
    round_end_inclusive: Optional[str],
) -> List[Dict[str, Any]]:
    review_ids = {event.get("review_id") for event in review_events if event.get("review_id") is not None}

    author_reviews = _filter_feedback_by_window(
        author_feedback["reviews"],
        start_exclusive=round_start_exclusive,
        end_inclusive=round_end_inclusive,
        user=None,
    )
    author_issue_comments = _filter_feedback_by_window(
        author_feedback["issue_comments"],
        start_exclusive=round_start_exclusive,
        end_inclusive=round_end_inclusive,
        user=None,
    )
    author_review_comments = _filter_feedback_by_window(
        author_feedback["review_comments"],
        start_exclusive=round_start_exclusive,
        end_inclusive=round_end_inclusive,
        user=None,
    )
    if review_ids:
        for comment in author_feedback["review_comments"]:
            if comment.get("pull_request_review_id") in review_ids:
                author_review_comments.append(comment)
        deduped_author_review_comments: List[Dict[str, Any]] = []
        seen_ids: Set[Any] = set()
        for comment in author_review_comments:
            marker = comment.get("id")
            if marker in seen_ids:
                continue
            seen_ids.add(marker)
            deduped_author_review_comments.append(comment)
        author_review_comments = deduped_author_review_comments

    def with_role(items: List[Dict[str, Any]], role: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for item in items:
            enriched = dict(item)
            enriched["role"] = role
            out.append(enriched)
        return out

    conversation_items = (
        with_role(maintainer_round_feedback["reviews"], "reviewer")
        + with_role(maintainer_round_feedback["issue_comments"], "reviewer")
        + with_role(maintainer_round_feedback["review_comments"], "reviewer")
        + with_role(author_reviews, "pr_author")
        + with_role(author_issue_comments, "pr_author")
        + with_role(author_review_comments, "pr_author")
    )

    comment_backed_review_ids = {
        item.get("pull_request_review_id")
        for item in conversation_items
        if item.get("kind") == "review_comment" and item.get("pull_request_review_id") is not None
    }
    conversation_items = [
        item
        for item in conversation_items
        if not (
            item.get("kind") == "review"
            and not (item.get("body") or "").strip()
            and item.get("id") in comment_backed_review_ids
        )
    ]

    conversation_items.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))

    deduped_items: List[Dict[str, Any]] = []
    seen_markers: Set[Tuple[Any, Any]] = set()
    for item in conversation_items:
        marker = (item.get("kind"), item.get("id"))
        if marker in seen_markers:
            continue
        seen_markers.add(marker)
        deduped_items.append(item)
    return deduped_items


def _split_round_conversation(
    round_conversation: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    author_input: List[Dict[str, Any]] = []
    reviewer_feedback: List[Dict[str, Any]] = []
    for item in round_conversation:
        role = item.get("role")
        if role == "pr_author":
            author_input.append(item)
        elif role == "reviewer":
            reviewer_feedback.append(item)
    return author_input, reviewer_feedback


def _extract_pr_commits(commits_payload: List[Dict[str, Any]]) -> List[Dict[str, Optional[str]]]:
    commits: List[Dict[str, Optional[str]]] = []
    for item in commits_payload:
        sha = item.get("sha")
        if not sha:
            continue
        commit_obj = item.get("commit") or {}
        author_obj = commit_obj.get("author") or {}
        committer_obj = commit_obj.get("committer") or {}
        committed_at = author_obj.get("date") or committer_obj.get("date")
        commits.append(
            {
                "sha": str(sha),
                "committed_at": committed_at,
            }
        )
    commits.sort(key=lambda c: (c.get("committed_at") or "", c.get("sha") or ""))
    return commits


def _select_snapshot_head_sha(
    commits: List[Dict[str, Optional[str]]],
    *,
    review_commit_id: Optional[str],
    cutoff_at: Optional[str],
    default_head_sha: Optional[str],
) -> Tuple[Optional[str], str]:
    sha_set = {str(c.get("sha")) for c in commits if c.get("sha")}
    if review_commit_id and review_commit_id in sha_set:
        return review_commit_id, "review_commit_id"

    if cutoff_at:
        eligible = [
            str(c.get("sha"))
            for c in commits
            if c.get("sha") and c.get("committed_at") and str(c.get("committed_at")) <= cutoff_at
        ]
        if eligible:
            return eligible[-1], "latest_commit_before_cutoff"

    if commits:
        latest_sha = commits[-1].get("sha")
        if latest_sha:
            return str(latest_sha), "latest_pr_commit"

    if default_head_sha:
        return default_head_sha, "pr_head_sha_fallback"
    return None, "missing_head_sha"


@dataclass
class WorkspaceMetadata:
    default_target: str
    toolchain: Optional[str]


class GitHubClient:
    """Small GitHub REST client for PR extraction."""

    def __init__(self, token: Optional[str], timeout_seconds: float, request_interval_seconds: float):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ape-bench-pr-review-builder",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(headers=headers, timeout=timeout_seconds)
        self._request_interval_seconds = max(0.0, request_interval_seconds)

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        accept: Optional[str] = None,
    ) -> httpx.Response:
        url = f"https://api.github.com{path}"
        headers = {}
        if accept:
            headers["Accept"] = accept

        response = self._client.request(method, url, params=params, headers=headers)
        if self._request_interval_seconds > 0.0:
            time.sleep(self._request_interval_seconds)

        if response.status_code in {403, 429}:
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset_at = response.headers.get("X-RateLimit-Reset")
            raise RuntimeError(
                f"GitHub rate limit hit (status={response.status_code}, "
                f"remaining={remaining}, reset={reset_at})"
            )

        response.raise_for_status()
        return response

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params).json()

    def get_text(self, path: str, *, accept: str, params: Optional[Dict[str, Any]] = None) -> str:
        return self._request("GET", path, params=params, accept=accept).text

    def paginate_json(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        items_key: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        page = 1
        while True:
            page_params = dict(params or {})
            page_params["per_page"] = 100
            page_params["page"] = page

            payload = self.get_json(path, params=page_params)
            if items_key:
                if not isinstance(payload, dict):
                    raise TypeError(f"Expected dict payload for {path}, got {type(payload).__name__}")
                page_items = payload.get(items_key, [])
            else:
                page_items = payload

            if not page_items:
                break
            if not isinstance(page_items, list):
                raise TypeError(f"Expected list payload for {path}, got {type(page_items).__name__}")

            items.extend(page_items)
            if len(page_items) < 100:
                break

            page += 1
            if max_pages is not None and page > max_pages:
                break
        return items


def _load_maintainers(path: Optional[Path]) -> Set[str]:
    if not path:
        return set()
    if not path.exists():
        raise FileNotFoundError(f"Maintainers file not found: {path}")
    maintainers: Set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        maintainers.add(line.lower())
    return maintainers


def _is_maintainer_author(
    user_login: Optional[str],
    author_association: Optional[str],
    explicit_maintainers: Set[str],
    pr_author_login: Optional[str] = None,
    reviewer_usernames: Optional[Set[str]] = None,
) -> bool:
    if not _is_human_non_author(user_login, pr_author_login):
        return False
    if user_login and user_login.lower() in explicit_maintainers:
        return True
    if user_login and reviewer_usernames and user_login.lower() in reviewer_usernames:
        return True
    return (author_association or "").upper() in MAINTAINER_ASSOCIATIONS


def _collect_author_feedback(
    reviews: List[Dict[str, Any]],
    issue_comments: List[Dict[str, Any]],
    review_comments: List[Dict[str, Any]],
    pr_author_login: Optional[str],
) -> Dict[str, List[Dict[str, Any]]]:
    if not pr_author_login or _is_bot_login(pr_author_login):
        return {
            "reviews": [],
            "issue_comments": [],
            "review_comments": [],
        }

    author_lower = pr_author_login.lower()

    def compact_review(review: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = (review.get("user") or {}).get("login")
        if not user or user.lower() != author_lower:
            return None
        return {
            "id": review.get("id"),
            "kind": "review",
            "user": user,
            "state": review.get("state"),
            "submitted_at": review.get("submitted_at"),
            "commit_id": review.get("commit_id"),
            "body": review.get("body") or "",
            "author_association": review.get("author_association"),
            "html_url": review.get("html_url"),
        }

    def compact_comment(comment: Dict[str, Any], kind: str) -> Optional[Dict[str, Any]]:
        user = (comment.get("user") or {}).get("login")
        if not user or user.lower() != author_lower:
            return None
        created_at = comment.get("created_at")
        line = comment.get("line")
        original_line = comment.get("original_line")
        start_line = comment.get("start_line")
        original_start_line = comment.get("original_start_line")
        return {
            "id": comment.get("id"),
            "kind": kind,
            "user": user,
            "state": None,
            "submitted_at": created_at,
            "body": comment.get("body") or "",
            "author_association": comment.get("author_association"),
            "html_url": comment.get("html_url"),
            "pull_request_review_id": comment.get("pull_request_review_id"),
            "commit_id": comment.get("commit_id"),
            "original_commit_id": comment.get("original_commit_id"),
            "in_reply_to_id": comment.get("in_reply_to_id"),
            "path": comment.get("path"),
            "line": line if line is not None else original_line,
            "original_line": original_line,
            "start_line": start_line if start_line is not None else original_start_line,
            "original_start_line": original_start_line,
        }

    author_reviews = [item for item in (compact_review(r) for r in reviews) if item is not None]
    author_issue_comments = [item for item in (compact_comment(c, "issue_comment") for c in issue_comments) if item is not None]
    author_review_comments = [item for item in (compact_comment(c, "review_comment") for c in review_comments) if item is not None]

    author_reviews.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    author_issue_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    author_review_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))

    return {
        "reviews": author_reviews,
        "issue_comments": author_issue_comments,
        "review_comments": author_review_comments,
    }


def _collect_maintainer_feedback(
    reviews: List[Dict[str, Any]],
    issue_comments: List[Dict[str, Any]],
    review_comments: List[Dict[str, Any]],
    explicit_maintainers: Set[str],
    pr_author_login: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    reviewer_usernames: Set[str] = set()
    for collection in (reviews, issue_comments, review_comments):
        for item in collection:
            user = ((item.get("user") or {}).get("login")) if isinstance(item, dict) else None
            if _is_human_non_author(user, pr_author_login):
                reviewer_usernames.add(str(user).lower())

    def compact_review(review: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = (review.get("user") or {}).get("login")
        if not _is_maintainer_author(
            user,
            review.get("author_association"),
            explicit_maintainers,
            pr_author_login=pr_author_login,
            reviewer_usernames=reviewer_usernames,
        ):
            return None
        return {
            "id": review.get("id"),
            "kind": "review",
            "user": user,
            "state": review.get("state"),
            "submitted_at": review.get("submitted_at"),
            "commit_id": review.get("commit_id"),
            "body": review.get("body") or "",
            "author_association": review.get("author_association"),
            "html_url": review.get("html_url"),
        }

    def compact_comment(comment: Dict[str, Any], kind: str) -> Optional[Dict[str, Any]]:
        user = (comment.get("user") or {}).get("login")
        if not _is_maintainer_author(
            user,
            comment.get("author_association"),
            explicit_maintainers,
            pr_author_login=pr_author_login,
            reviewer_usernames=reviewer_usernames,
        ):
            return None
        created_at = comment.get("created_at")
        line = comment.get("line")
        original_line = comment.get("original_line")
        start_line = comment.get("start_line")
        original_start_line = comment.get("original_start_line")
        return {
            "id": comment.get("id"),
            "kind": kind,
            "user": user,
            "state": None,
            "submitted_at": created_at,
            "body": comment.get("body") or "",
            "author_association": comment.get("author_association"),
            "html_url": comment.get("html_url"),
            "pull_request_review_id": comment.get("pull_request_review_id"),
            "commit_id": comment.get("commit_id"),
            "original_commit_id": comment.get("original_commit_id"),
            "in_reply_to_id": comment.get("in_reply_to_id"),
            "path": comment.get("path"),
            "line": line if line is not None else original_line,
            "original_line": original_line,
            "start_line": start_line if start_line is not None else original_start_line,
            "original_start_line": original_start_line,
        }

    maintainer_reviews = [item for item in (compact_review(r) for r in reviews) if item is not None]
    maintainer_issue_comments = [item for item in (compact_comment(c, "issue_comment") for c in issue_comments) if item is not None]
    maintainer_review_comments = [item for item in (compact_comment(c, "review_comment") for c in review_comments) if item is not None]

    maintainer_reviews.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    maintainer_issue_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    maintainer_review_comments.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))

    return {
        "reviews": maintainer_reviews,
        "issue_comments": maintainer_issue_comments,
        "review_comments": maintainer_review_comments,
    }


def _build_search_query(config: PRReviewDatasetConfig) -> str:
    parts = [f"repo:{config.repo_owner}/{config.repo_name}", "is:pr"]
    if config.include_merged and config.include_closed_unmerged:
        parts.append("is:closed")
    elif config.include_merged:
        parts.append("is:merged")
    elif config.include_closed_unmerged:
        parts.extend(["is:closed", "is:unmerged"])

    if config.exclude_draft:
        parts.append("draft:false")

    date_qualifier = _build_date_qualifier(config.date_field, config.start_date, config.end_date)
    if date_qualifier:
        parts.append(date_qualifier)
    return " ".join(parts)


def _extract_workspace_metadata(
    repo_url: str,
    base_sha: str,
    cache: Dict[str, WorkspaceMetadata],
) -> WorkspaceMetadata:
    if base_sha in cache:
        return cache[base_sha]

    default_target = get_default_target(repo_url, base_sha) or "Mathlib"
    toolchain = fetch_file_from_github(repo_url, base_sha, "lean-toolchain")

    ws = WorkspaceMetadata(
        default_target=default_target,
        toolchain=toolchain.strip() if toolchain else None,
    )
    cache[base_sha] = ws
    return ws


def _pr_to_task_record(
    *,
    config: PRReviewDatasetConfig,
    pr: Dict[str, Any],
    changed_paths: List[str],
    pr_diff: str,
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    workspace_metadata: WorkspaceMetadata,
    snapshot_type: str,
    snapshot_at: Optional[str],
    snapshot_base_sha: str,
    snapshot_head_sha: Optional[str],
    snapshot_head_sha_source: str,
    snapshot_diff_source: str,
    review_event: Optional[Dict[str, Any]],
    allow_merge_outcome_fallback: bool,
    round_index: Optional[int] = None,
    round_window: Optional[Dict[str, Optional[str]]] = None,
    feedback_history_before_round: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    round_conversation: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    maintainer_reviews = maintainer_feedback["reviews"]
    maintainer_issue_comments = maintainer_feedback["issue_comments"]
    maintainer_review_comments = maintainer_feedback["review_comments"]
    author_input, reviewer_feedback = _split_round_conversation(round_conversation or [])
    pr_description, pr_dependencies = _extract_pr_description_and_dependencies(pr.get("body"))

    merge_ready, merge_ready_source, latest_state_by_user = _derive_merge_ready(
        pr,
        maintainer_reviews,
        allow_merge_outcome_fallback=allow_merge_outcome_fallback,
    )
    review_state = ((review_event or {}).get("state") or "").upper()
    if review_state == "APPROVED":
        merge_ready = True
        merge_ready_source = "decision_review_state"
    elif review_state == "CHANGES_REQUESTED":
        merge_ready = False
        merge_ready_source = "decision_review_state"
    elif _has_approval_signal(reviewer_feedback or maintainer_reviews + maintainer_issue_comments + maintainer_review_comments):
        merge_ready = True
        merge_ready_source = "reviewer_approval_comment"

    feedback_items = maintainer_reviews + maintainer_issue_comments + maintainer_review_comments
    feedback_items.sort(key=lambda x: (x.get("submitted_at") or "", x.get("id") or 0))
    feedback_texts = [f.get("body", "") for f in feedback_items if (f.get("body") or "").strip()]
    inferred_tags = _infer_issue_tags_from_feedback(feedback_texts)

    if merge_ready:
        blocking_issue_tags = []
        advisory_issue_tags = inferred_tags
    else:
        blocking_issue_tags = inferred_tags or ["requirement_mismatch"]
        advisory_issue_tags = []

    rationale = _build_review_rationale(feedback_items, max_chars=config.rationale_char_limit)

    changed_paths = [str(path) for path in changed_paths if path]
    lean_changed_paths = [path for path in changed_paths if _is_lean_file(path)]

    if review_event and review_event.get("review_id") is not None:
        task_id = f"mathlib_pr_review_{pr.get('number')}_review_{review_event.get('review_id')}"
    elif snapshot_at:
        compact_ts = re.sub(r"[^0-9]", "", snapshot_at)[:14]
        task_id = f"mathlib_pr_review_{pr.get('number')}_t{compact_ts}" if compact_ts else f"mathlib_pr_review_{pr.get('number')}"
    else:
        task_id = f"mathlib_pr_review_{pr.get('number')}"

    record = {
        "task_type": "lean_pr_review",
        "task_id": task_id,
        "pr_number": pr.get("number"),
        "pr_url": pr.get("html_url"),
        "pr_title": pr.get("title") or "",
        "pr_author": (pr.get("user") or {}).get("login"),
        "pr_description": pr_description,
        "pr_dependencies": pr_dependencies,
        "pr_diff": pr_diff or "",
        "changed_files": changed_paths,
        "snapshot_type": snapshot_type,
        "snapshot_at": snapshot_at,
        "snapshot_base_sha": snapshot_base_sha,
        "snapshot_head_sha": snapshot_head_sha,
        "review_state": review_state or None,
        "review_focus": config.review_focus,
        "author_input": author_input,
        "reviewer_feedback": reviewer_feedback,
        "ground_truth": {
            "merge_ready": merge_ready,
            "blocking_issue_tags": _dedupe_preserve_order(blocking_issue_tags),
            "advisory_issue_tags": _dedupe_preserve_order(advisory_issue_tags),
            "rationale": rationale or None,
        },
        "target_workspace": {
            "name": "target",
            "commit_hash": snapshot_base_sha,
            "repo_url": config.repo_url,
            "default_target": workspace_metadata.default_target,
            "toolchain": workspace_metadata.toolchain,
            "read_only_path_patterns": ["**/*"],
        },
        "metadata": {},
    }
    return record


class PRReviewDataCollector:
    """Collector for real Mathlib PR review benchmark records."""

    def __init__(self, config: PRReviewDatasetConfig, logger: Optional["logging.LoggerAdapter"] = None):
        self.config = config
        self.logger = logger or create_logger()

        token = config.github_token or os.getenv("GITHUB_TOKEN")
        self.github_client = GitHubClient(
            token=token,
            timeout_seconds=config.timeout_seconds,
            request_interval_seconds=config.request_interval_seconds,
        )
        self.workspace_cache: Dict[str, WorkspaceMetadata] = {}
        self.maintainers = _load_maintainers(config.maintainers_file)
        self.skip_reasons: Dict[str, int] = defaultdict(int)

    def close(self) -> None:
        self.github_client.close()

    def _collect_pr_numbers(self) -> List[int]:
        query = _build_search_query(self.config)
        self.logger.info(f"GitHub search query: {query}")
        search_sort = "created" if self.config.date_field == "created" else "updated"
        search_order = "asc" if self.config.pr_order == "oldest" else "desc"
        self.logger.info(
            "Search ordering: sort=%s order=%s (pr_order=%s)",
            search_sort,
            search_order,
            self.config.pr_order,
        )

        search_items = self.github_client.paginate_json(
            "/search/issues",
            params={
                "q": query,
                "sort": search_sort,
                "order": search_order,
            },
            max_pages=self.config.max_search_pages,
            items_key="items",
        )

        pr_numbers: List[int] = []
        for item in search_items:
            if "pull_request" not in item:
                continue
            number = item.get("number")
            if not isinstance(number, int):
                continue
            pr_numbers.append(number)
            if len(pr_numbers) >= self.config.max_prs:
                break
        return pr_numbers

    def _should_keep_pr(
        self,
        pr: Dict[str, Any],
        changed_paths: List[str],
    ) -> bool:
        config = self.config
        if not config.include_merged and pr.get("merged_at"):
            self.skip_reasons["excluded_merged"] += 1
            return False
        if not config.include_closed_unmerged and not pr.get("merged_at"):
            self.skip_reasons["excluded_closed_unmerged"] += 1
            return False
        if config.exclude_draft and pr.get("draft"):
            self.skip_reasons["draft"] += 1
            return False

        date_value = pr.get(f"{config.date_field}_at")
        if config.date_field in {"closed", "merged"} and not _date_key_in_range(
            date_value, config.start_date, config.end_date
        ):
            self.skip_reasons["date_out_of_range"] += 1
            return False

        lean_paths = [path for path in changed_paths if _is_lean_file(path)]
        if config.require_lean_files and not lean_paths:
            self.skip_reasons["no_lean_files"] += 1
            return False

        changed_file_count = len(changed_paths)
        if changed_file_count < config.min_changed_files:
            self.skip_reasons["too_few_changed_files"] += 1
            return False
        if changed_file_count > config.max_changed_files:
            self.skip_reasons["too_many_changed_files"] += 1
            return False

        diff_lines = int(pr.get("additions") or 0) + int(pr.get("deletions") or 0)
        if diff_lines < config.min_diff_lines:
            self.skip_reasons["diff_too_small"] += 1
            return False
        if diff_lines > config.max_diff_lines:
            self.skip_reasons["diff_too_large"] += 1
            return False

        return True

    def _fetch_snapshot_context(
        self,
        *,
        base_sha: str,
        head_sha: str,
        final_changed_paths: List[str],
        final_pr_diff: str,
        cache: Dict[Tuple[str, str], Dict[str, Any]],
    ) -> Dict[str, Any]:
        key = (base_sha, head_sha)
        if key in cache:
            return cache[key]

        compare_path = f"/repos/{self.config.repo_owner}/{self.config.repo_name}/compare/{base_sha}...{head_sha}"
        snapshot_base_sha = base_sha
        snapshot_changed_paths = list(final_changed_paths)
        snapshot_pr_diff = final_pr_diff
        snapshot_diff_source = "pulls_diff_fallback"

        try:
            compare_payload = self.github_client.get_json(compare_path)
            compare_files = compare_payload.get("files") if isinstance(compare_payload, dict) else None
            if isinstance(compare_files, list):
                snapshot_changed_paths = [
                    str(item.get("filename"))
                    for item in compare_files
                    if isinstance(item, dict) and item.get("filename")
                ]

            compare_base_sha = None
            if isinstance(compare_payload, dict):
                compare_base_sha = ((compare_payload.get("base_commit") or {}).get("sha")) or None
            if compare_base_sha:
                snapshot_base_sha = str(compare_base_sha)
            snapshot_diff_source = "compare_endpoint"
        except Exception as exc:
            self.logger.warning(
                "Compare JSON fallback for %s...%s (%s)",
                base_sha,
                head_sha,
                exc,
            )

        try:
            snapshot_pr_diff = self.github_client.get_text(
                compare_path,
                accept="application/vnd.github.v3.diff",
            )
            snapshot_diff_source = "compare_endpoint"
        except Exception as exc:
            self.logger.warning(
                "Compare diff fallback for %s...%s (%s)",
                base_sha,
                head_sha,
                exc,
            )

        snapshot = {
            "base_sha": snapshot_base_sha,
            "head_sha": head_sha,
            "changed_paths": snapshot_changed_paths,
            "pr_diff": snapshot_pr_diff,
            "snapshot_diff_source": snapshot_diff_source,
        }
        cache[key] = snapshot
        return snapshot

    def collect_records(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        pr_numbers = self._collect_pr_numbers()
        self.logger.info(f"Candidate PRs from search: {len(pr_numbers)}")

        for idx, pr_number in enumerate(pr_numbers, 1):
            pr_url = f"https://github.com/{self.config.repo_owner}/{self.config.repo_name}/pull/{pr_number}"
            self.logger.info(f"[{idx}/{len(pr_numbers)}] considering PR {pr_url}")
            records_before_pr = len(records)
            skip_reasons_before_pr = dict(self.skip_reasons)
            outcome = "unknown"
            try:
                pr = self.github_client.get_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}"
                )
                changed_files = self.github_client.paginate_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/files"
                )
                changed_paths = [f.get("filename") for f in changed_files if f.get("filename")]
                changed_paths = [str(path) for path in changed_paths]

                if not self._should_keep_pr(pr, changed_paths):
                    outcome = "skipped"
                    continue

                reviews = self.github_client.paginate_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/reviews"
                )
                issue_comments = self.github_client.paginate_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{pr_number}/comments"
                )
                review_comments = self.github_client.paginate_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/comments"
                )
                pr_author = (pr.get("user") or {}).get("login")
                maintainer_feedback = _collect_maintainer_feedback(
                    reviews=reviews,
                    issue_comments=issue_comments,
                    review_comments=review_comments,
                    explicit_maintainers=self.maintainers,
                    pr_author_login=pr_author,
                )
                author_feedback = _collect_author_feedback(
                    reviews=reviews,
                    issue_comments=issue_comments,
                    review_comments=review_comments,
                    pr_author_login=pr_author,
                )
                feedback_count = (
                    len(maintainer_feedback["reviews"])
                    + len(maintainer_feedback["issue_comments"])
                    + len(maintainer_feedback["review_comments"])
                )
                if self.config.require_maintainer_feedback and feedback_count == 0:
                    self.skip_reasons["no_maintainer_feedback"] += 1
                    outcome = "skipped"
                    continue

                base_sha = (pr.get("base") or {}).get("sha")
                if not base_sha:
                    self.skip_reasons["missing_base_sha"] += 1
                    outcome = "skipped"
                    continue

                final_pr_diff = self.github_client.get_text(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}",
                    accept="application/vnd.github.v3.diff",
                )
                final_head_sha = (pr.get("head") or {}).get("sha")
                commit_payload = self.github_client.paginate_json(
                    f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/commits"
                )
                pr_commits = _extract_pr_commits(commit_payload)

                event_groups: List[List[Dict[str, Any]]]
                review_events = _collect_review_events(
                    maintainer_feedback["reviews"],
                    decision_review_states=self.config.decision_review_states,
                    max_review_events_per_pr=self.config.max_review_events_per_pr,
                )
                issue_comment_anchor_events = _collect_comment_fallback_events(
                    maintainer_feedback,
                    max_review_events_per_pr=0,
                    include_issue_comments=True,
                    include_review_comments=False,
                )
                events = _merge_round_anchor_events(
                    review_events,
                    issue_comment_anchor_events,
                    max_review_events_per_pr=self.config.max_review_events_per_pr,
                )

                if not events:
                    review_comment_fallback_events: List[Dict[str, Any]] = []
                    if self.config.include_comment_only_rounds:
                        review_comment_fallback_events = _collect_comment_fallback_events(
                            maintainer_feedback,
                            max_review_events_per_pr=self.config.max_review_events_per_pr,
                            include_issue_comments=False,
                            include_review_comments=True,
                        )
                    if review_comment_fallback_events:
                        event_groups = _group_review_events(review_comment_fallback_events)
                        self.logger.info(
                            "[%d/%d] PR #%s (%s): using %d comment-derived review events grouped into %d round(s)",
                            idx,
                            len(pr_numbers),
                            pr_number,
                            pr.get("html_url"),
                            len(review_comment_fallback_events),
                            len(event_groups),
                        )
                    else:
                        review_state_counts: Dict[str, int] = defaultdict(int)
                        for review in maintainer_feedback["reviews"]:
                            state = str(review.get("state") or "").upper() or "UNKNOWN"
                            review_state_counts[state] += 1
                        self.skip_reasons["no_selected_review_events"] += 1
                        self.logger.info(
                            "[%d/%d] skipped PR #%s (%s): no maintainer review events matched states %s; available review states=%s; maintainer issue_comments=%d, review_comments=%d",
                            idx,
                            len(pr_numbers),
                            pr_number,
                            pr.get("html_url"),
                            self.config.decision_review_states,
                            dict(sorted(review_state_counts.items())),
                            len(maintainer_feedback["issue_comments"]),
                            len(maintainer_feedback["review_comments"]),
                        )
                        outcome = "skipped"
                        continue
                else:
                    event_groups = _group_review_events(events)

                if not event_groups:
                    self.skip_reasons["no_grouped_review_rounds"] += 1
                    outcome = "skipped"
                    continue

                snapshot_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
                records_before = len(records)

                def group_end_time(group: List[Dict[str, Any]]) -> Optional[str]:
                    times = [event.get("submitted_at") for event in group if event.get("submitted_at")]
                    return max(times) if times else None

                def group_start_time(group: List[Dict[str, Any]]) -> Optional[str]:
                    times = [event.get("submitted_at") for event in group if event.get("submitted_at")]
                    return min(times) if times else None

                for event_idx, event_group in enumerate(event_groups, 1):
                    event = event_group[-1]
                    event_cutoff_at = group_end_time(event_group)
                    snapshot_type = "review_event"
                    previous_event_cutoff = group_end_time(event_groups[event_idx - 2]) if event_idx > 1 else None
                    next_group_start = group_start_time(event_groups[event_idx]) if event_idx < len(event_groups) else None
                    event_cutoff_at = _extend_round_end_with_followups(
                        maintainer_feedback,
                        review_events=event_group,
                        round_end_inclusive=event_cutoff_at,
                        next_group_start=next_group_start,
                    )
                    feedback_snapshot = _build_round_feedback(
                        maintainer_feedback,
                        review_events=event_group,
                        round_start_exclusive=previous_event_cutoff,
                        round_end_inclusive=event_cutoff_at,
                    )
                    feedback_history_before_round = (
                        _slice_feedback_until(maintainer_feedback, previous_event_cutoff)
                        if previous_event_cutoff
                        else {"reviews": [], "issue_comments": [], "review_comments": []}
                    )
                    round_conversation = _build_round_conversation(
                        feedback_snapshot,
                        author_feedback=author_feedback,
                        review_events=event_group,
                        round_start_exclusive=previous_event_cutoff,
                        round_end_inclusive=event_cutoff_at,
                    )
                    round_window = {
                        "start_exclusive": previous_event_cutoff,
                        "end_inclusive": event_cutoff_at,
                    }

                    snapshot_head_sha, snapshot_head_sha_source = _select_snapshot_head_sha(
                        pr_commits,
                        review_commit_id=event.get("commit_id"),
                        cutoff_at=event_cutoff_at,
                        default_head_sha=final_head_sha,
                    )
                    if not snapshot_head_sha:
                        self.skip_reasons["missing_snapshot_head_sha"] += 1
                        outcome = "skipped"
                        continue

                    snapshot_context = self._fetch_snapshot_context(
                        base_sha=base_sha,
                        head_sha=snapshot_head_sha,
                        final_changed_paths=changed_paths,
                        final_pr_diff=final_pr_diff,
                        cache=snapshot_cache,
                    )

                    ws_meta = _extract_workspace_metadata(
                        repo_url=self.config.repo_url,
                        base_sha=snapshot_context["base_sha"],
                        cache=self.workspace_cache,
                    )
                    event_payload = (
                        {
                            **event,
                            "group_size": len(event_group),
                            "events": event_group,
                        }
                    )
                    allow_merge_outcome_fallback = False

                    record = _pr_to_task_record(
                        config=self.config,
                        pr=pr,
                        changed_paths=snapshot_context["changed_paths"],
                        pr_diff=snapshot_context["pr_diff"],
                        maintainer_feedback=feedback_snapshot,
                        workspace_metadata=ws_meta,
                        snapshot_type=snapshot_type,
                        snapshot_at=event_cutoff_at if snapshot_type == "review_event" else None,
                        snapshot_base_sha=snapshot_context["base_sha"],
                        snapshot_head_sha=snapshot_head_sha,
                        snapshot_head_sha_source=snapshot_head_sha_source,
                        snapshot_diff_source=snapshot_context["snapshot_diff_source"],
                        review_event=event_payload,
                        allow_merge_outcome_fallback=allow_merge_outcome_fallback,
                        round_index=event_idx,
                        round_window=round_window,
                        feedback_history_before_round=feedback_history_before_round,
                        round_conversation=round_conversation,
                    )
                    records.append(record)

                diff_lines = int(pr.get("additions") or 0) + int(pr.get("deletions") or 0)
                added_records = len(records) - records_before
                self.logger.info(
                    f"[{idx}/{len(pr_numbers)}] kept PR #{pr_number} "
                    f"(records={added_records}, files={len(changed_paths)}, diff={diff_lines})"
                )
                outcome = "kept" if added_records > 0 else "no_records"

            except Exception as exc:
                self.skip_reasons["processing_error"] += 1
                outcome = "failed"
                self.logger.warning(f"[{idx}/{len(pr_numbers)}] failed PR #{pr_number}: {exc}")
            finally:
                added_records = len(records) - records_before_pr
                skip_deltas = {
                    key: self.skip_reasons[key] - skip_reasons_before_pr.get(key, 0)
                    for key in self.skip_reasons
                    if self.skip_reasons[key] - skip_reasons_before_pr.get(key, 0) > 0
                }
                if outcome != "kept":
                    detail = f"skip_reasons={dict(sorted(skip_deltas.items()))}" if skip_deltas else "skip_reasons={}"
                    self.logger.info(
                        "[%d/%d] finished PR #%s outcome=%s records_added=%d %s",
                        idx,
                        len(pr_numbers),
                        pr_number,
                        outcome,
                        added_records,
                        detail,
                    )

        return records

    def build_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        merge_ready_true = sum(1 for r in records if (r.get("ground_truth") or {}).get("merge_ready"))
        merge_ready_false = len(records) - merge_ready_true
        unique_prs = len({r.get("pr_number") for r in records if r.get("pr_number") is not None})
        return {
            "records": len(records),
            "unique_prs": unique_prs,
            "merge_ready_true": merge_ready_true,
            "merge_ready_false": merge_ready_false,
            "skip_reasons": dict(sorted(self.skip_reasons.items())),
        }

    def save_records(self, records: List[Dict[str, Any]], output_file: Path) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
