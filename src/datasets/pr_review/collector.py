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
from ape.tasks.lean_tasks.formal_math.pr_review.findings import (
    AI_GENERATED_PR_LABEL,
    AI_GENERATED_PR_GITHUB_LABEL,
    categories_to_review_findings,
    review_findings_to_json,
)
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging


MAINTAINER_ASSOCIATIONS = {"MEMBER", "OWNER", "COLLABORATOR"}
ACTIONABLE_REVIEW_STATES = {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}

FINDING_CATEGORY_PATTERNS = {
    "correctness": [
        r"\bwrong\b",
        r"\bincorrect\b",
        r"\bunsound\b",
        r"\bfails?\b",
        r"\bbug\b",
        r"\bdoesn['’]t compile\b",
    ],
    "requirements_scope": [
        r"\bmissing\b",
        r"\bnot enough\b",
        r"\bdoesn['’]t implement\b",
        r"\bneeds? to\b",
        r"\bshould also\b",
        r"\bout of scope\b",
        r"\bunrelated\b",
        r"\btoo (?:broad|large|many)\b",
        r"\bunnecessary refactor\b",
    ],
    "robustness_performance": [
        r"\bfragile\b",
        r"\bbrittle\b",
        r"\bunstable\b",
        r"\bperformance\b",
        r"\bslow\b",
        r"\btimeout\b",
    ],
    "documentation_metadata": [
        r"\bdoc(?:s|umentation)?\b",
        r"\bplease document\b",
        r"\badd (?:a )?comment\b",
    ],
    "tests_ci": [
        r"\btest(?:s|ing)?\b",
        r"\bregression test\b",
        r"\bcoverage\b",
    ],
    "integration_compatibility": [
        r"\bimport\b",
        r"\bnamespace\b",
        r"\bapi\b",
        r"\bbackward compatible\b",
        r"\bdeprecated\b",
        r"\bobsolete\b",
        r"\blegacy\b",
    ],
    "readability_maintainability": [
        r"\bstyle\b",
        r"\breadability\b",
        r"\bnaming\b",
        r"\bformat(?:ting)?\b",
        r"\bnit\b",
    ],
}

APPROVAL_COMMENT_PATTERNS = [
    r"\bbors\s+merge\b",
    r"\bbors\s+r\+",
    r"\bbors\s+d\+",
    r"\bmaintainer\s+merge\b",
    r"\blgtm\b",
    r"\blooks good\b",
    r"\bapproved?\b",
]
TRIVIAL_FEEDBACK_PATTERNS = [
    r"\bmaintainer\s+merge\b",
    r"\bbors\s+(?:merge|r\+|d\+)\b",
    r"\blgtm\b",
    r"\blooks good\b",
    r"\bapproved?\b",
    r"\bthanks?\b",
    r"\bthank you\b",
]
LOW_FEEDBACK_MAINTAINER_ITEMS_MAX = 3
HIGH_FEEDBACK_MAINTAINER_ITEMS_MIN = 4

BORS_MERGED_TITLE_RE = re.compile(r"^\s*\[merged by bors\](?:\s|$)", re.IGNORECASE)

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

MAINTAINER_SPLIT_PATTERNS = [
    re.compile(r"\bsplice-bot\b", re.IGNORECASE),
    re.compile(r"\bsmaller prs?\b", re.IGNORECASE),
    re.compile(r"\bsplit(?:ting)? (?:this|the|it|these changes|the pr)?(?:\s+up)?\b", re.IGNORECASE),
    re.compile(r"\bits own pr\b", re.IGNORECASE),
    re.compile(r"\bseparate pr\b", re.IGNORECASE),
]


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        normalized = _normalize_record_label(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _normalize_record_label(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = re.sub(r"[\s\-]+", "_", str(value or "").strip().lower())
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized or None


def _normalize_feedback_text(body: Optional[str]) -> str:
    return re.sub(r"\s+", " ", str(body or "").strip().lower())


def _strip_trivial_feedback_tokens(body: Optional[str]) -> str:
    normalized = _normalize_feedback_text(body)
    for pattern in TRIVIAL_FEEDBACK_PATTERNS:
        normalized = re.sub(pattern, " ", normalized)
    normalized = re.sub(r"[`*_>#:\-.,!?()\[\]{}\"'/\\]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _is_substantive_feedback_item(item: Dict[str, Any]) -> bool:
    if str(item.get("state") or "").upper() == "CHANGES_REQUESTED":
        return True
    return bool(_strip_trivial_feedback_tokens(item.get("body")))


def _is_substantive_round(feedback: Dict[str, List[Dict[str, Any]]]) -> bool:
    return any(
        _is_substantive_feedback_item(item)
        for item in feedback["reviews"] + feedback["issue_comments"] + feedback["review_comments"]
    )


def _changes_requested_count(reviews: Sequence[Dict[str, Any]]) -> int:
    return sum(1 for review in reviews if str(review.get("state") or "").upper() == "CHANGES_REQUESTED")


def _maintainer_requested_split(feedback_items: Sequence[Dict[str, Any]]) -> bool:
    for item in feedback_items:
        body = str(item.get("body") or "")
        if not body.strip():
            continue
        if any(pattern.search(body) for pattern in MAINTAINER_SPLIT_PATTERNS):
            return True
    return False


def _is_split_candidate(
    *,
    pr: Dict[str, Any],
    changed_paths: Sequence[str],
    pr_diff: str,
    maintainer_requested_split: bool,
) -> bool:
    changed_file_count = len([path for path in changed_paths if path])
    diff_lines = int(pr.get("additions") or 0) + int(pr.get("deletions") or 0)
    hunk_count = sum(1 for line in (pr_diff or "").splitlines() if line.startswith("@@ "))
    return bool(
        maintainer_requested_split
        or diff_lines >= 250
        or changed_file_count >= 8
        or hunk_count >= 10
    )


def _is_effectively_merged(pr: Dict[str, Any]) -> bool:
    if pr.get("merged_at") or pr.get("merged") is True:
        return True
    title = str(pr.get("title") or "")
    return bool(BORS_MERGED_TITLE_RE.match(title))


def _final_pr_outcome(pr: Dict[str, Any]) -> str:
    if _is_effectively_merged(pr):
        return "merged"
    if str(pr.get("state") or "").lower() == "closed":
        return "closed_unmerged"
    return "open"


def _classify_authoring_mode(pr: Dict[str, Any]) -> str:
    labels = pr.get("labels") or []
    for label in labels:
        name = label.get("name") if isinstance(label, dict) else label
        if _normalize_record_label(str(name or "")) == AI_GENERATED_PR_LABEL:
            return "ai_authored"
    return "human"


def _classify_primary_case(
    *,
    final_pr_outcome: str,
    maintainer_round_count: int,
    maintainer_feedback_count: int,
    changes_requested_count: int,
) -> str:
    if final_pr_outcome == "closed_unmerged":
        return "abandoned"
    if final_pr_outcome == "open":
        return "active_review"
    if (
        final_pr_outcome == "merged"
        and maintainer_round_count <= 1
        and changes_requested_count == 0
        and maintainer_feedback_count <= LOW_FEEDBACK_MAINTAINER_ITEMS_MAX
    ):
        return "easy"
    return "major_feedback"


def _derive_case_flags(
    *,
    final_pr_outcome: str,
    maintainer_feedback_count: int,
    changes_requested_count: int,
    authoring_mode: str,
) -> List[str]:
    flags: list[str] = []
    if final_pr_outcome != "merged":
        flags.append("unmerged")
    if final_pr_outcome == "closed_unmerged":
        flags.append("closed_unmerged")
    if final_pr_outcome == "open":
        flags.append("open_unmerged")
    if changes_requested_count > 0:
        flags.append("changes_requested")
    if maintainer_feedback_count <= LOW_FEEDBACK_MAINTAINER_ITEMS_MAX:
        flags.append("low_feedback")
    if maintainer_feedback_count >= HIGH_FEEDBACK_MAINTAINER_ITEMS_MIN:
        flags.append("high_feedback")
    if authoring_mode == "ai_authored":
        flags.append("llm_generated_label")
    return flags


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


def _infer_finding_categories_from_feedback(feedback_texts: Sequence[str]) -> List[str]:
    if not feedback_texts:
        return []
    merged = "\n".join(feedback_texts).lower()
    categories: List[str] = []
    for category, patterns in FINDING_CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, merged):
                categories.append(category)
                break
    return _dedupe_preserve_order(categories)


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
        if _is_effectively_merged(pr):
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


def _build_round_infos(
    *,
    maintainer_feedback: Dict[str, List[Dict[str, Any]]],
    author_feedback: Dict[str, List[Dict[str, Any]]],
    event_groups: List[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    def group_end_time(group: List[Dict[str, Any]]) -> Optional[str]:
        times = [event.get("submitted_at") for event in group if event.get("submitted_at")]
        return max(times) if times else None

    def group_start_time(group: List[Dict[str, Any]]) -> Optional[str]:
        times = [event.get("submitted_at") for event in group if event.get("submitted_at")]
        return min(times) if times else None

    round_infos: List[Dict[str, Any]] = []
    for event_idx, event_group in enumerate(event_groups, 1):
        event = event_group[-1]
        event_cutoff_at = group_end_time(event_group)
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
        round_infos.append(
            {
                "event_idx": event_idx,
                "event_group": event_group,
                "event": event,
                "event_cutoff_at": event_cutoff_at,
                "feedback_snapshot": feedback_snapshot,
                "feedback_history_before_round": feedback_history_before_round,
                "round_conversation": round_conversation,
                "round_window": round_window,
                "substantive": _is_substantive_round(feedback_snapshot),
            }
        )
    return round_infos


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
    if config.include_merged and config.include_unmerged:
        # Search all PRs so unmerged selection can include both open and closed PRs.
        pass
    elif config.include_merged:
        # Mathlib's Bors flow can produce effectively merged PRs that GitHub
        # still marks as closed-unmerged, so we search closed PRs and classify
        # locally instead of relying on `is:merged`.
        parts.append("is:closed")
    elif config.include_unmerged:
        # Search all PRs so we can include both open and closed unmerged PRs.
        # We filter out effectively merged PRs locally.
        pass

    if config.exclude_draft:
        parts.append("draft:false")
    if config.only_llm_generated_prs:
        parts.append(f'label:"{AI_GENERATED_PR_GITHUB_LABEL}"')

    date_qualifier = _build_date_qualifier(config.date_field, config.start_date, config.end_date)
    if date_qualifier:
        parts.append(date_qualifier)
    return " ".join(parts)


def _extract_workspace_metadata(
    repo_url: str,
    commit_hash: str,
    cache: Dict[Tuple[str, str], WorkspaceMetadata],
) -> WorkspaceMetadata:
    cache_key = (repo_url, commit_hash)
    if cache_key in cache:
        return cache[cache_key]

    default_target = get_default_target(repo_url, commit_hash) or "Mathlib"
    toolchain = fetch_file_from_github(repo_url, commit_hash, "lean-toolchain")

    ws = WorkspaceMetadata(
        default_target=default_target,
        toolchain=toolchain.strip() if toolchain else None,
    )
    cache[cache_key] = ws
    return ws


def _extract_pr_head_metadata(
    *,
    config: PRReviewDatasetConfig,
    pr: Dict[str, Any],
    snapshot_head_sha: Optional[str],
    workspace_cache: Dict[Tuple[str, str], WorkspaceMetadata],
) -> Optional[Dict[str, Any]]:
    normalized_head_sha = str(snapshot_head_sha or "").strip()
    if not normalized_head_sha:
        return None

    head_payload = pr.get("head") or {}
    head_repo = head_payload.get("repo") or {}

    repo_full_name = str(head_repo.get("full_name") or "").strip()
    effective_repo_full_name = repo_full_name or f"{config.repo_owner}/{config.repo_name}"
    clone_url = str(head_repo.get("clone_url") or "").strip() or config.repo_url
    head_ref = str(head_payload.get("ref") or "").strip()
    base_repo_full_name = f"{config.repo_owner}/{config.repo_name}".lower()
    is_fork = effective_repo_full_name.lower() != base_repo_full_name

    head_workspace_metadata = _extract_workspace_metadata(
        repo_url=clone_url,
        commit_hash=normalized_head_sha,
        cache=workspace_cache,
    )

    return {
        "sha": normalized_head_sha,
        "repo_full_name": effective_repo_full_name,
        "clone_url": clone_url,
        "ref": head_ref,
        "is_fork": is_fork,
        "default_target": head_workspace_metadata.default_target,
        "toolchain": head_workspace_metadata.toolchain,
    }


def _build_target_workspace_payload(
    *,
    config: PRReviewDatasetConfig,
    workspace_metadata: WorkspaceMetadata,
    snapshot_base_sha: str,
) -> Dict[str, Any]:
    return {
        "name": "target",
        "commit_hash": snapshot_base_sha,
        "repo_url": config.repo_url,
        "default_target": workspace_metadata.default_target,
        "toolchain": workspace_metadata.toolchain,
        "read_only_path_patterns": ["**/*"],
    }


def _build_snapshot_payload(
    *,
    config: PRReviewDatasetConfig,
    pr: Dict[str, Any],
    changed_paths: List[str],
    pr_diff: str,
    snapshot_type: Optional[str],
    snapshot_at: Optional[str],
    snapshot_base_sha: Optional[str],
    snapshot_head_sha: Optional[str],
    pr_head_metadata: Optional[Dict[str, Any]],
    author_input: Optional[List[Dict[str, Any]]] = None,
    reviewer_feedback: Optional[List[Dict[str, Any]]] = None,
    pr_url_override: Optional[str] = None,
) -> Dict[str, Any]:
    pr_description, pr_dependencies = _extract_pr_description_and_dependencies(pr.get("body"))
    return {
        "pr_number": pr.get("number"),
        "pr_url": pr_url_override or pr.get("html_url"),
        "pr_title": pr.get("title") or "",
        "pr_author": (pr.get("user") or {}).get("login"),
        "pr_description": pr_description,
        "pr_dependencies": pr_dependencies,
        "pr_diff": pr_diff or "",
        "changed_files": [str(path) for path in changed_paths if path],
        "snapshot_type": snapshot_type,
        "snapshot_at": snapshot_at,
        "snapshot_base_sha": snapshot_base_sha,
        "snapshot_head_sha": snapshot_head_sha,
        "review_state": None,
        "review_focus": config.review_focus,
        "pr_head": pr_head_metadata,
        "conversation": {
            "author_input": list(author_input or []),
            "reviewer_feedback": list(reviewer_feedback or []),
        },
    }


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
    workspace_cache: Dict[Tuple[str, str], WorkspaceMetadata],
    snapshot_head_sha_source: str,
    snapshot_diff_source: str,
    review_event: Optional[Dict[str, Any]],
    allow_merge_outcome_fallback: bool,
    primary_case: Optional[str] = None,
    case_flags: Optional[List[str]] = None,
    authoring_mode: Optional[str] = None,
    final_pr_outcome: Optional[str] = None,
    maintainer_round_count: Optional[int] = None,
    maintainer_feedback_count: Optional[int] = None,
    changes_requested_count: Optional[int] = None,
    selected_snapshot_kind: Optional[str] = None,
    label_source: Optional[str] = None,
    round_index: Optional[int] = None,
    round_window: Optional[Dict[str, Optional[str]]] = None,
    feedback_history_before_round: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    round_conversation: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    maintainer_reviews = maintainer_feedback["reviews"]
    maintainer_issue_comments = maintainer_feedback["issue_comments"]
    maintainer_review_comments = maintainer_feedback["review_comments"]
    author_input, reviewer_feedback = _split_round_conversation(round_conversation or [])

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
    inferred_categories = _infer_finding_categories_from_feedback(feedback_texts)
    maintainer_requested_split = _maintainer_requested_split(feedback_items)
    split_candidate = _is_split_candidate(
        pr=pr,
        changed_paths=changed_paths,
        pr_diff=pr_diff,
        maintainer_requested_split=maintainer_requested_split,
    )

    if merge_ready:
        blocking_categories: List[str] = []
        advisory_categories = inferred_categories
    else:
        blocking_categories = inferred_categories or ["requirements_scope"]
        advisory_categories = []
    blocking_findings = categories_to_review_findings(blocking_categories)
    advisory_findings = categories_to_review_findings(advisory_categories)
    heuristic_builder_labels = {
        "blocking_finding_categories": _dedupe_preserve_order(blocking_categories),
        "advisory_finding_categories": _dedupe_preserve_order(advisory_categories),
        "merge_ready_source": merge_ready_source,
    }

    rationale = _build_review_rationale(feedback_items, max_chars=config.rationale_char_limit)

    changed_paths = [str(path) for path in changed_paths if path]

    if review_event and review_event.get("review_id") is not None:
        task_id = f"mathlib_pr_review_{pr.get('number')}_review_{review_event.get('review_id')}"
    elif snapshot_at:
        compact_ts = re.sub(r"[^0-9]", "", snapshot_at)[:14]
        task_id = f"mathlib_pr_review_{pr.get('number')}_t{compact_ts}" if compact_ts else f"mathlib_pr_review_{pr.get('number')}"
    else:
        task_id = f"mathlib_pr_review_{pr.get('number')}"

    pr_head_metadata = _extract_pr_head_metadata(
        config=config,
        pr=pr,
        snapshot_head_sha=snapshot_head_sha,
        workspace_cache=workspace_cache,
    )
    label_source_value = _normalize_record_label(label_source)
    benchmark_context = {
        "primary_case": _normalize_record_label(primary_case),
        "case_flags": _dedupe_preserve_order(_normalize_record_label(flag) or "" for flag in (case_flags or [])),
        "authoring_mode": _normalize_record_label(authoring_mode),
        "final_pr_outcome": _normalize_record_label(final_pr_outcome),
        "maintainer_round_count": maintainer_round_count,
        "maintainer_feedback_count": maintainer_feedback_count,
        "changes_requested_count": changes_requested_count,
        "selected_snapshot_kind": _normalize_record_label(selected_snapshot_kind),
        "source_labels": heuristic_builder_labels,
        "round_index": round_index,
        "round_window": round_window,
        "split_candidate": split_candidate,
        "maintainer_requested_split": maintainer_requested_split,
    }
    metadata: Dict[str, Any] = {
        "snapshot_assembly": {
            "snapshot_head_sha_source": snapshot_head_sha_source,
            "snapshot_diff_source": snapshot_diff_source,
        }
    }
    return {
        "task_type": "lean_pr_review",
        "task_id": task_id,
        "snapshot": {
            **_build_snapshot_payload(
                config=config,
                pr=pr,
                changed_paths=changed_paths,
                pr_diff=pr_diff,
                snapshot_type=snapshot_type,
                snapshot_at=snapshot_at,
                snapshot_base_sha=snapshot_base_sha,
                snapshot_head_sha=snapshot_head_sha,
                pr_head_metadata=pr_head_metadata,
                author_input=author_input,
                reviewer_feedback=reviewer_feedback,
            ),
            "review_state": review_state or None,
        },
        "evaluation": {
            "ground_truth": {
                "merge_ready": merge_ready,
                "needs_human_review": False,
                "decision_confidence": None,
                "blocking_findings": review_findings_to_json(blocking_findings),
                "advisory_findings": review_findings_to_json(advisory_findings),
                "rationale": rationale or None,
            },
            "label_source": label_source_value,
        },
        "benchmark_context": benchmark_context,
        "target_workspace": _build_target_workspace_payload(
            config=config,
            workspace_metadata=workspace_metadata,
            snapshot_base_sha=snapshot_base_sha,
        ),
        "metadata": metadata,
    }


def _build_live_task_record(
    *,
    task_type: str,
    config: PRReviewDatasetConfig,
    pr: Dict[str, Any],
    changed_paths: List[str],
    pr_diff: str,
    workspace_metadata: WorkspaceMetadata,
    snapshot_type: str,
    snapshot_base_sha: str,
    snapshot_head_sha: str,
    workspace_cache: Dict[Tuple[str, str], WorkspaceMetadata],
    snapshot_head_sha_source: str,
    snapshot_diff_source: str,
    pr_url_override: Optional[str] = None,
) -> Dict[str, Any]:
    pr_head_metadata = _extract_pr_head_metadata(
        config=config,
        pr=pr,
        snapshot_head_sha=snapshot_head_sha,
        workspace_cache=workspace_cache,
    )
    task_prefix = "mathlib_pr_split" if "pr_split" in task_type else "mathlib_pr_review"
    task_id = f"{task_prefix}_{pr.get('number')}_{snapshot_head_sha[:12]}"
    return {
        "task_type": task_type,
        "task_id": task_id,
        "snapshot": _build_snapshot_payload(
            config=config,
            pr=pr,
            changed_paths=changed_paths,
            pr_diff=pr_diff,
            snapshot_type=snapshot_type,
            snapshot_at=None,
            snapshot_base_sha=snapshot_base_sha,
            snapshot_head_sha=snapshot_head_sha,
            pr_head_metadata=pr_head_metadata,
            author_input=[],
            reviewer_feedback=[],
            pr_url_override=pr_url_override,
        ),
        "evaluation": None,
        "benchmark_context": None,
        "target_workspace": _build_target_workspace_payload(
            config=config,
            workspace_metadata=workspace_metadata,
            snapshot_base_sha=snapshot_base_sha,
        ),
        "metadata": {
            "snapshot_assembly": {
                "snapshot_head_sha_source": snapshot_head_sha_source,
                "snapshot_diff_source": snapshot_diff_source,
            }
        },
    }


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
        self.workspace_cache: Dict[Tuple[str, str], WorkspaceMetadata] = {}
        self.maintainers = _load_maintainers(config.maintainers_file)
        self.skip_reasons: Dict[str, int] = defaultdict(int)

    def close(self) -> None:
        self.github_client.close()

    @staticmethod
    def _validate_live_pr_task_type(task_type: str) -> str:
        normalized = str(task_type or "").strip()
        if normalized not in {
            "lean_pr_review",
            "skilled_pr_review",
            "skilled_policy_pr_review",
            "lean_pr_split",
            "skilled_pr_split",
            "skilled_policy_pr_split",
        }:
            raise ValueError(
                f"Unsupported live PR task type `{normalized}`. "
                "Expected one of: lean_pr_review, skilled_pr_review, skilled_policy_pr_review, "
                "lean_pr_split, skilled_pr_split, skilled_policy_pr_split."
            )
        return normalized

    def _load_pr_review_source_context(self, pr_number: int) -> Dict[str, Any]:
        pr = self.github_client.get_json(
            f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}"
        )
        changed_files = self.github_client.paginate_json(
            f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/files"
        )
        changed_paths = [str(f.get("filename")) for f in changed_files if f.get("filename")]

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

        base_sha = (pr.get("base") or {}).get("sha")
        if not base_sha:
            raise ValueError(f"PR {pr_number} is missing base SHA")

        final_pr_diff = self.github_client.get_text(
            f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}",
            accept="application/vnd.github.v3.diff",
        )
        final_head_sha = (pr.get("head") or {}).get("sha")
        commit_payload = self.github_client.paginate_json(
            f"/repos/{self.config.repo_owner}/{self.config.repo_name}/pulls/{pr_number}/commits"
        )
        pr_commits = _extract_pr_commits(commit_payload)

        return {
            "pr": pr,
            "changed_paths": changed_paths,
            "maintainer_feedback": maintainer_feedback,
            "author_feedback": author_feedback,
            "base_sha": str(base_sha),
            "final_pr_diff": final_pr_diff,
            "final_head_sha": final_head_sha,
            "pr_commits": pr_commits,
            "feedback_count": (
                len(maintainer_feedback["reviews"])
                + len(maintainer_feedback["issue_comments"])
                + len(maintainer_feedback["review_comments"])
            ),
        }

    @staticmethod
    def _resolve_snapshot_head_sha(
        *,
        requested_head_sha: str,
        pr_commits: Sequence[Dict[str, Any]],
        final_head_sha: Optional[str],
        pr_number: int,
    ) -> str:
        normalized_head_sha = str(requested_head_sha or "").strip()
        if not normalized_head_sha:
            raise ValueError("snapshot_head_sha must be non-empty")

        commit_lookup = {
            str(commit.get("sha")).lower(): str(commit.get("sha"))
            for commit in pr_commits
            if commit.get("sha")
        }
        resolved_head_sha = commit_lookup.get(normalized_head_sha.lower())
        if resolved_head_sha is None and final_head_sha and str(final_head_sha).lower() == normalized_head_sha.lower():
            resolved_head_sha = str(final_head_sha)
        if resolved_head_sha is None:
            raise ValueError(f"Commit {normalized_head_sha} does not belong to PR {pr_number}")
        return resolved_head_sha

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
        is_effectively_merged = _is_effectively_merged(pr)
        authoring_mode = _classify_authoring_mode(pr)
        if not config.include_merged and is_effectively_merged:
            self.skip_reasons["excluded_merged"] += 1
            return False
        if not config.include_unmerged and not is_effectively_merged:
            self.skip_reasons["excluded_unmerged"] += 1
            return False
        if config.exclude_draft and pr.get("draft"):
            self.skip_reasons["draft"] += 1
            return False
        if config.only_llm_generated_prs and authoring_mode != "ai_authored":
            self.skip_reasons["excluded_non_llm_generated"] += 1
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

    def build_live_pr_review_task_data(
        self,
        pr_number: int,
        snapshot_head_sha: str,
        *,
        pr_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build an unscored live PR review task for the requested PR head commit."""
        return self.build_live_pr_task_data(
            task_type="lean_pr_review",
            pr_number=pr_number,
            snapshot_head_sha=snapshot_head_sha,
            pr_url=pr_url,
        )

    def build_live_pr_split_task_data(
        self,
        pr_number: int,
        snapshot_head_sha: str,
        *,
        pr_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build an unscored live PR split task for the requested PR head commit."""
        return self.build_live_pr_task_data(
            task_type="lean_pr_split",
            pr_number=pr_number,
            snapshot_head_sha=snapshot_head_sha,
            pr_url=pr_url,
        )

    def build_live_pr_task_data(
        self,
        *,
        task_type: str,
        pr_number: int,
        snapshot_head_sha: str,
        pr_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build an unscored live PR review or split task for the requested PR head commit."""
        normalized_task_type = self._validate_live_pr_task_type(task_type)
        context = self._load_pr_review_source_context(pr_number)
        resolved_head_sha = self._resolve_snapshot_head_sha(
            requested_head_sha=snapshot_head_sha,
            pr_commits=context["pr_commits"],
            final_head_sha=context["final_head_sha"],
            pr_number=pr_number,
        )
        snapshot_context = self._fetch_snapshot_context(
            base_sha=context["base_sha"],
            head_sha=resolved_head_sha,
            final_changed_paths=context["changed_paths"],
            final_pr_diff=context["final_pr_diff"],
            cache={},
        )
        ws_meta = _extract_workspace_metadata(
            repo_url=self.config.repo_url,
            commit_hash=snapshot_context["base_sha"],
            cache=self.workspace_cache,
        )
        return _build_live_task_record(
            task_type=normalized_task_type,
            config=self.config,
            pr=context["pr"],
            changed_paths=snapshot_context["changed_paths"],
            pr_diff=snapshot_context["pr_diff"],
            workspace_metadata=ws_meta,
            snapshot_type="live_commit",
            snapshot_base_sha=snapshot_context["base_sha"],
            snapshot_head_sha=resolved_head_sha,
            workspace_cache=self.workspace_cache,
            snapshot_head_sha_source="manual_input",
            snapshot_diff_source=snapshot_context["snapshot_diff_source"],
            pr_url_override=pr_url,
        )

    def build_benchmark_pr_review_task_data(
        self,
        pr_number: int,
        snapshot_head_sha: str,
        *,
        pr_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a scored benchmark task for a PR review-round snapshot."""
        context = self._load_pr_review_source_context(pr_number)
        resolved_head_sha = self._resolve_snapshot_head_sha(
            requested_head_sha=snapshot_head_sha,
            pr_commits=context["pr_commits"],
            final_head_sha=context["final_head_sha"],
            pr_number=pr_number,
        )
        review_events = _collect_review_events(
            context["maintainer_feedback"]["reviews"],
            decision_review_states=self.config.decision_review_states,
            max_review_events_per_pr=self.config.max_review_events_per_pr,
        )
        issue_comment_anchor_events = _collect_comment_fallback_events(
            context["maintainer_feedback"],
            max_review_events_per_pr=0,
            include_issue_comments=True,
            include_review_comments=False,
        )
        events = _merge_round_anchor_events(
            review_events,
            issue_comment_anchor_events,
            max_review_events_per_pr=self.config.max_review_events_per_pr,
        )

        if not events and self.config.include_comment_only_rounds:
            events = _collect_comment_fallback_events(
                context["maintainer_feedback"],
                max_review_events_per_pr=self.config.max_review_events_per_pr,
                include_issue_comments=False,
                include_review_comments=True,
            )

        matching_records: List[Dict[str, Any]] = []
        event_groups = _group_review_events(events) if events else []
        round_infos = _build_round_infos(
            maintainer_feedback=context["maintainer_feedback"],
            author_feedback=context["author_feedback"],
            event_groups=event_groups,
        )
        substantive_round_count = sum(1 for info in round_infos if info["substantive"])
        maintainer_feedback_count = context["feedback_count"]
        changes_requested = _changes_requested_count(context["maintainer_feedback"]["reviews"])
        final_pr_outcome = _final_pr_outcome(context["pr"])
        authoring_mode = _classify_authoring_mode(context["pr"])
        primary_case = _classify_primary_case(
            final_pr_outcome=final_pr_outcome,
            maintainer_round_count=substantive_round_count,
            maintainer_feedback_count=maintainer_feedback_count,
            changes_requested_count=changes_requested,
        )
        case_flags = _derive_case_flags(
            final_pr_outcome=final_pr_outcome,
            maintainer_feedback_count=maintainer_feedback_count,
            changes_requested_count=changes_requested,
            authoring_mode=authoring_mode,
        )
        selected_round_infos = list(round_infos)
        if primary_case == "abandoned":
            substantive_rounds = [info for info in round_infos if info["substantive"]]
            if substantive_rounds:
                selected_round_infos = [substantive_rounds[-1]]
            elif round_infos:
                selected_round_infos = [round_infos[-1]]

        for info in selected_round_infos:
            event = info["event"]
            event_group = info["event_group"]
            event_cutoff_at = info["event_cutoff_at"]
            candidate_head_sha, candidate_head_sha_source = _select_snapshot_head_sha(
                context["pr_commits"],
                review_commit_id=event.get("commit_id"),
                cutoff_at=event_cutoff_at,
                default_head_sha=context["final_head_sha"],
            )
            if not candidate_head_sha or str(candidate_head_sha).lower() != resolved_head_sha.lower():
                continue

            event_payload = {
                **event,
                "group_size": len(event_group),
                "events": event_group,
            }

            matching_records.append(
                _pr_to_task_record(
                    config=self.config,
                    pr=context["pr"],
                    changed_paths=snapshot_context["changed_paths"],
                    pr_diff=snapshot_context["pr_diff"],
                    maintainer_feedback=info["feedback_snapshot"],
                    workspace_metadata=ws_meta,
                    snapshot_type="review_event",
                    snapshot_at=event_cutoff_at,
                    snapshot_base_sha=snapshot_context["base_sha"],
                    snapshot_head_sha=resolved_head_sha,
                    workspace_cache=self.workspace_cache,
                    snapshot_head_sha_source=candidate_head_sha_source,
                    snapshot_diff_source=snapshot_context["snapshot_diff_source"],
                    review_event=event_payload,
                    allow_merge_outcome_fallback=False,
                    primary_case=primary_case,
                    case_flags=case_flags,
                    authoring_mode=authoring_mode,
                    final_pr_outcome=final_pr_outcome,
                    maintainer_round_count=substantive_round_count,
                    maintainer_feedback_count=maintainer_feedback_count,
                    changes_requested_count=changes_requested,
                    selected_snapshot_kind=(
                        "last_substantive_round_before_closure"
                        if primary_case == "abandoned"
                        else "review_round"
                    ),
                    label_source="maintainer_feedback_heuristic",
                    round_index=info["event_idx"],
                    round_window=info["round_window"],
                    feedback_history_before_round=info["feedback_history_before_round"],
                    round_conversation=info["round_conversation"],
                )
            )

        if matching_records:
            return matching_records[-1]
        raise ValueError(
            f"No benchmark review-round snapshot matched PR {pr_number} at commit {resolved_head_sha}"
        )

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
                round_infos = _build_round_infos(
                    maintainer_feedback=maintainer_feedback,
                    author_feedback=author_feedback,
                    event_groups=event_groups,
                )
                substantive_round_count = sum(1 for info in round_infos if info["substantive"])
                changes_requested = _changes_requested_count(maintainer_feedback["reviews"])
                final_pr_outcome = _final_pr_outcome(pr)
                authoring_mode = _classify_authoring_mode(pr)
                primary_case = _classify_primary_case(
                    final_pr_outcome=final_pr_outcome,
                    maintainer_round_count=substantive_round_count,
                    maintainer_feedback_count=feedback_count,
                    changes_requested_count=changes_requested,
                )
                case_flags = _derive_case_flags(
                    final_pr_outcome=final_pr_outcome,
                    maintainer_feedback_count=feedback_count,
                    changes_requested_count=changes_requested,
                    authoring_mode=authoring_mode,
                )
                selected_round_infos = list(round_infos)
                if primary_case == "abandoned":
                    substantive_rounds = [info for info in round_infos if info["substantive"]]
                    if substantive_rounds:
                        selected_round_infos = [substantive_rounds[-1]]
                    elif round_infos:
                        selected_round_infos = [round_infos[-1]]

                for info in selected_round_infos:
                    event = info["event"]
                    event_group = info["event_group"]
                    event_cutoff_at = info["event_cutoff_at"]
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
                        commit_hash=snapshot_context["base_sha"],
                        cache=self.workspace_cache,
                    )
                    event_payload = {
                        **event,
                        "group_size": len(event_group),
                        "events": event_group,
                    }

                    record = _pr_to_task_record(
                        config=self.config,
                        pr=pr,
                        changed_paths=snapshot_context["changed_paths"],
                        pr_diff=snapshot_context["pr_diff"],
                        maintainer_feedback=info["feedback_snapshot"],
                        workspace_metadata=ws_meta,
                        snapshot_type="review_event",
                        snapshot_at=event_cutoff_at,
                        snapshot_base_sha=snapshot_context["base_sha"],
                        snapshot_head_sha=snapshot_head_sha,
                        workspace_cache=self.workspace_cache,
                        snapshot_head_sha_source=snapshot_head_sha_source,
                        snapshot_diff_source=snapshot_context["snapshot_diff_source"],
                        review_event=event_payload,
                        allow_merge_outcome_fallback=False,
                        primary_case=primary_case,
                        case_flags=case_flags,
                        authoring_mode=authoring_mode,
                        final_pr_outcome=final_pr_outcome,
                        maintainer_round_count=substantive_round_count,
                        maintainer_feedback_count=feedback_count,
                        changes_requested_count=changes_requested,
                        selected_snapshot_kind=(
                            "last_substantive_round_before_closure"
                            if primary_case == "abandoned"
                            else "review_round"
                        ),
                        label_source="maintainer_feedback_heuristic",
                        round_index=info["event_idx"],
                        round_window=info["round_window"],
                        feedback_history_before_round=info["feedback_history_before_round"],
                        round_conversation=info["round_conversation"],
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
        merge_ready_true = sum(
            1 for r in records if ((r.get("evaluation") or {}).get("ground_truth") or {}).get("merge_ready")
        )
        merge_ready_false = len(records) - merge_ready_true
        unique_prs = len(
            {
                (r.get("snapshot") or {}).get("pr_number")
                for r in records
                if (r.get("snapshot") or {}).get("pr_number") is not None
            }
        )
        primary_case_counts: Dict[str, int] = defaultdict(int)
        authoring_mode_counts: Dict[str, int] = defaultdict(int)
        for record in records:
            benchmark_context = record.get("benchmark_context") or {}
            primary_case = _normalize_record_label(benchmark_context.get("primary_case"))
            if primary_case:
                primary_case_counts[primary_case] += 1
            authoring_mode = _normalize_record_label(benchmark_context.get("authoring_mode"))
            if authoring_mode:
                authoring_mode_counts[authoring_mode] += 1
        return {
            "records": len(records),
            "unique_prs": unique_prs,
            "merge_ready_true": merge_ready_true,
            "merge_ready_false": merge_ready_false,
            "primary_case_counts": dict(sorted(primary_case_counts.items())),
            "authoring_mode_counts": dict(sorted(authoring_mode_counts.items())),
            "skip_reasons": dict(sorted(self.skip_reasons.items())),
        }

    def save_records(self, records: List[Dict[str, Any]], output_file: Path) -> None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with output_file.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
