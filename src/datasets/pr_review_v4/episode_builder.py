"""Derive first-review episodes directly from raw GitHub events and cached Git compares."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .diffs import review_diff
from .episodes import changed_files_from_diff
from .events import events_from_bundle
from .io import canonical_json_bytes, sha256_bytes, sha256_file
from .schema import (
    FunnelDecision,
    ReviewEpisodeBoundary,
    ReviewEpisodeInput,
    ReviewRoundSegment,
    VisibleText,
)


RAW_EPISODE_BUILDER_VERSION = "raw_first_round_v1"
MULTI_ROUND_BUILDER_VERSION = "raw_multi_round_v1"
MAINTAINER_ASSOCIATIONS = {"MEMBER", "OWNER", "COLLABORATOR"}
TOOLCHAIN_ONLY_FILES = {"lean-toolchain", "lakefile.lean", "lakefile.toml", "lake-manifest.json"}
BORS_MERGED_TITLE_RE = re.compile(r"^\s*\[merged by bors\](?:\s|-|$)", re.I)
BORS_TITLE_PREFIX_RE = re.compile(r"^\s*\[(?:merged|closed) by bors\]\s*-?\s*", re.I)
REVERT_TITLE_RE = re.compile(r"^\s*revert\b", re.I)
APPROVAL_SIGNAL_RE = re.compile(r"\bbors\s+(?:merge|r\+|d\+|d=)|\bmaintainer\s+merge\b", re.I)
TRIVIAL_FEEDBACK_PATTERNS = (
    r"\bmaintainer\s+merge\b",
    r"\bbors\s+(?:merge|r\+|d\+|d=)",
    r"\blgtm\b",
    r"\blooks good(?: to me)?\b",
    r"\bthanks?\b",
    r"\bthank you\b",
    r":\w+:",
)


@dataclass(frozen=True)
class EpisodeBuildResult:
    episode: ReviewEpisodeInput
    boundary: ReviewEpisodeBoundary


@dataclass(frozen=True)
class MultiRoundBuildResult:
    episodes: List[ReviewEpisodeInput]
    boundaries: List[ReviewEpisodeBoundary]
    segments: List[ReviewRoundSegment]


def _strip_trivial_tokens(body: Any) -> str:
    text = re.sub(r"\s+", " ", str(body or "").strip().lower())
    for pattern in TRIVIAL_FEEDBACK_PATTERNS:
        text = re.sub(pattern, " ", text)
    text = re.sub(r"[`*_>#:\-.,!?()\[\]{}\"'/\\~+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_title(title: Any) -> str:
    return BORS_TITLE_PREFIX_RE.sub("", str(title or "")).strip()


def _clean_description(body: Any) -> str:
    text = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "---" or "gitpod.io/" in stripped.lower():
            continue
        kept.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def _is_bot(login: Optional[str]) -> bool:
    lowered = str(login or "").lower()
    return not lowered or lowered.endswith("[bot]") or lowered.endswith("-bot") or lowered in {
        "bors",
        "github-actions",
        "leanprover-community-bot",
        "leanprover-community-mathlib4-bot",
    }


def load_roster(path: Path) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def _is_reviewer(
    login: Optional[str], association: Optional[str], author: str, roster: set[str]
) -> bool:
    return bool(
        login
        and not _is_bot(login)
        and login.lower() != author.lower()
        and (
            login.lower() in roster
            or str(association or "").upper() in MAINTAINER_ASSOCIATIONS
        )
    )


def _commit_times(bundle: Dict[str, Any]) -> List[Tuple[str, str]]:
    commits = []
    for item in bundle.get("commits") or []:
        commit = item.get("commit") or {}
        date = (commit.get("committer") or {}).get("date") or (
            commit.get("author") or {}
        ).get("date")
        if item.get("sha") and date:
            commits.append((str(date), str(item["sha"])))
    return sorted(commits)


def _normalized_feedback_events(
    bundle: Dict[str, Any], *, bundle_path: Path, repo: str, author: str, roster: set[str]
) -> List[Dict[str, Any]]:
    source_ids = {
        event.source_key: event.event_id
        for event in events_from_bundle(bundle, bundle_path=bundle_path, repo=repo)
    }
    events = []
    for index, review in enumerate(bundle.get("reviews") or []):
        login = (review.get("user") or {}).get("login")
        if not review.get("submitted_at"):
            continue
        state = str(review.get("state") or "").upper()
        events.append(
            {
                "kind": "review",
                "source_event_id": source_ids[f"/reviews/{index}"],
                "author": login,
                "is_reviewer": _is_reviewer(
                    login, review.get("author_association"), author, roster
                ),
                "at": str(review["submitted_at"]),
                "body": review.get("body") or "",
                "state": state
                if state in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"}
                else None,
                "commit_id": review.get("commit_id"),
            }
        )
    for index, comment in enumerate(bundle.get("review_comments") or []):
        login = (comment.get("user") or {}).get("login")
        if not comment.get("created_at"):
            continue
        events.append(
            {
                "kind": "review_comment",
                "source_event_id": source_ids[f"/review_comments/{index}"],
                "author": login,
                "is_reviewer": _is_reviewer(
                    login, comment.get("author_association"), author, roster
                ),
                "at": str(comment["created_at"]),
                "body": comment.get("body") or "",
                "state": None,
                "commit_id": comment.get("original_commit_id") or comment.get("commit_id"),
            }
        )
    for index, comment in enumerate(bundle.get("issue_comments") or []):
        login = (comment.get("user") or {}).get("login")
        if not comment.get("created_at"):
            continue
        events.append(
            {
                "kind": "issue_comment",
                "source_event_id": source_ids[f"/issue_comments/{index}"],
                "author": login,
                "is_reviewer": _is_reviewer(
                    login, comment.get("author_association"), author, roster
                ),
                "at": str(comment["created_at"]),
                "body": comment.get("body") or "",
                "state": None,
                "commit_id": None,
            }
        )
    order = {"review": 0, "review_comment": 1, "issue_comment": 2}
    return sorted(events, key=lambda event: (event["at"], order[event["kind"]], event["source_event_id"]))


def _is_substantive(event: Dict[str, Any]) -> bool:
    return event.get("state") == "CHANGES_REQUESTED" or bool(
        _strip_trivial_tokens(event.get("body"))
    )


def _ready_for_review_floor(bundle: Dict[str, Any]) -> Optional[str]:
    values = [
        item.get("created_at")
        for item in bundle.get("timeline") or []
        if item.get("event") == "ready_for_review" and item.get("created_at")
    ]
    return min(values) if values else None


def funnel_and_first_round(
    bundle: Dict[str, Any],
    *,
    bundle_path: Path,
    compare_cache: Path,
    repo: str = "leanprover-community/mathlib4",
    roster: Optional[set[str]] = None,
) -> Tuple[FunnelDecision, Optional[EpisodeBuildResult]]:
    pr = bundle.get("pr") or {}
    pr_number = int(pr.get("number") or 0)

    def excluded(stage: str, reason: str):
        return FunnelDecision(
            repo=repo, pr_number=pr_number, included=False, stage=stage, reason=reason
        ), None

    author = str((pr.get("user") or {}).get("login") or "")
    raw_title = str(pr.get("title") or "")
    files = bundle.get("files") or []
    paths = [str(file.get("filename") or "") for file in files]
    if _is_bot(author):
        return excluded("authorship", "bot_author")
    if REVERT_TITLE_RE.search(raw_title):
        return excluded("change_type", "revert")
    if paths and all(path in TOOLCHAIN_ONLY_FILES for path in paths):
        return excluded("change_type", "toolchain_or_build_only")
    if not any(path.startswith("Mathlib/") and path.endswith(".lean") for path in paths):
        return excluded("content", "no_mathlib_lean_file")
    changed_files = int(pr.get("changed_files") or len(paths))
    if not 1 <= changed_files <= 30:
        return excluded("size", f"changed_files={changed_files}")
    diff_lines = int(pr.get("additions") or 0) + int(pr.get("deletions") or 0)
    if not 10 <= diff_lines <= 800:
        return excluded("size", f"diff_lines={diff_lines}")
    merged = bool(pr.get("merged_at")) or bool(BORS_MERGED_TITLE_RE.match(raw_title))
    if not merged and str(pr.get("state") or "").lower() != "closed":
        return excluded("outcome", "still_open")

    events = _normalized_feedback_events(
        bundle, bundle_path=bundle_path, repo=repo, author=author, roster=roster or set()
    )
    floor = _ready_for_review_floor(bundle)
    reviewer_events = [
        event
        for event in events
        if event["is_reviewer"] and (floor is None or event["at"] >= floor)
    ]
    substantive = [event for event in reviewer_events if _is_substantive(event)]
    decisions = [
        event
        for event in reviewer_events
        if _is_substantive(event)
        or event.get("state")
        or APPROVAL_SIGNAL_RE.search(event.get("body") or "")
    ]
    if not decisions:
        return excluded("review_signal", "no_reviewer_events")
    review_started_at = decisions[0]["at"]
    commits = _commit_times(bundle)
    if not commits:
        return excluded("reviewed_head", "no_pr_commits")
    commit_shas = {sha for _at, sha in commits}
    event_commit = next(
        (
            event.get("commit_id")
            for event in decisions
            if event["at"] == review_started_at and event.get("commit_id")
        ),
        None,
    )
    if event_commit and event_commit in commit_shas:
        reviewed_head = str(event_commit)
        resolution = "review_commit_id"
    else:
        before_review = [sha for at, sha in commits if at < review_started_at]
        if not before_review:
            return excluded("reviewed_head", "no_commit_before_review")
        reviewed_head = before_review[-1]
        resolution = "pushed_before_review"

    pushes_after = [(at, sha) for at, sha in commits if at > review_started_at]
    feedback_end, next_head = pushes_after[0] if pushes_after else (None, None)
    feedback = [
        event
        for event in substantive
        if event["at"] >= review_started_at
        and (feedback_end is None or event["at"] < feedback_end)
    ]
    try:
        diff, merge_base, compare_hash, _compare_path = review_diff(compare_cache, reviewed_head)
    except ValueError as exc:
        return excluded("hydration", str(exc))
    body_edits = bundle.get("body_edits")
    post_review_edit = body_edits is None or any(
        str(edit.get("edited_at") or "") > review_started_at for edit in body_edits
    )
    description_text = _clean_description(pr.get("body"))
    if post_review_edit:
        description = VisibleText(
            text=None,
            provenance="legacy_post_edit_risk_omitted",
            omission_reason="raw edit history cannot recover the description at review start",
        )
    elif description_text:
        description = VisibleText(text=description_text, provenance="review_time_verified")
    else:
        description = VisibleText(text="", provenance="absent")

    episode_id = f"{repo}:{pr_number}:round1:{reviewed_head}"
    bundle_hash = sha256_file(bundle_path)
    projection = {
        "repo": repo,
        "pr_number": pr_number,
        "round_index": 1,
        "title": _clean_title(raw_title),
        "description": description.model_dump(mode="json"),
        "base_sha": merge_base,
        "reviewed_head_sha": reviewed_head,
        "diff_sha256": sha256_bytes(diff.encode("utf-8")),
        "bundle_sha256": bundle_hash,
        "compare_sha256": compare_hash,
    }
    episode = ReviewEpisodeInput(
        episode_id=episode_id,
        repo=repo,
        pr_number=pr_number,
        round_index=1,
        title=VisibleText(
            text=_clean_title(raw_title), provenance="source_current_value_unverified"
        ),
        description=description,
        base_sha=merge_base,
        reviewed_head_sha=reviewed_head,
        diff=diff,
        changed_files=changed_files_from_diff(diff),
        patch_sha256=sha256_bytes(diff.encode("utf-8")),
        source_projection_sha256=sha256_bytes(canonical_json_bytes(projection)),
    )
    triggers = [event["source_event_id"] for event in decisions if event["at"] == review_started_at]
    boundary = ReviewEpisodeBoundary(
        episode_id=episode_id,
        repo=repo,
        pr_number=pr_number,
        round_index=1,
        review_started_at=review_started_at,
        feedback_window_end=feedback_end,
        reviewed_head_sha=reviewed_head,
        reviewed_head_resolution=resolution,
        triggering_event_ids=triggers,
        feedback_event_ids=[event["source_event_id"] for event in feedback],
        next_head_sha=next_head,
        source_bundle_sha256=bundle_hash,
        compare_sha256=compare_hash,
    )
    return FunnelDecision(
        repo=repo, pr_number=pr_number, included=True, stage="included", reason="eligible"
    ), EpisodeBuildResult(episode=episode, boundary=boundary)


def _description_at_review(bundle: Dict[str, Any], review_started_at: str) -> VisibleText:
    body_edits = bundle.get("body_edits")
    unsafe = body_edits is None or any(
        str(edit.get("edited_at") or "") > review_started_at for edit in body_edits
    )
    text = _clean_description((bundle.get("pr") or {}).get("body"))
    if unsafe:
        return VisibleText(
            text=None,
            provenance="legacy_post_edit_risk_omitted",
            omission_reason="raw edit history cannot recover the description at review start",
        )
    if text:
        return VisibleText(text=text, provenance="review_time_verified")
    return VisibleText(text="", provenance="absent")


def segment_review_rounds(
    bundle: Dict[str, Any],
    *,
    bundle_path: Path,
    compare_cache: Path,
    repo: str = "leanprover-community/mathlib4",
    roster: Optional[set[str]] = None,
) -> Tuple[FunnelDecision, Optional[MultiRoundBuildResult]]:
    """Derive all maximal reviewer-event groups separated by at least one author push."""
    decision, first = funnel_and_first_round(
        bundle,
        bundle_path=bundle_path,
        compare_cache=compare_cache,
        repo=repo,
        roster=roster,
    )
    if not first:
        return decision, None

    pr = bundle.get("pr") or {}
    pr_number = int(pr["number"])
    author = str((pr.get("user") or {}).get("login") or "")
    events = _normalized_feedback_events(
        bundle,
        bundle_path=bundle_path,
        repo=repo,
        author=author,
        roster=roster or set(),
    )
    floor = _ready_for_review_floor(bundle)
    reviewer_events = [
        event
        for event in events
        if event["is_reviewer"] and (floor is None or event["at"] >= floor)
    ]
    substantive = [event for event in reviewer_events if _is_substantive(event)]
    decisions = [
        event
        for event in reviewer_events
        if _is_substantive(event)
        or event.get("state")
        or APPROVAL_SIGNAL_RE.search(event.get("body") or "")
    ]
    commits = _commit_times(bundle)
    commit_shas = {sha for _at, sha in commits}
    groups: List[List[Dict[str, Any]]] = []
    for event in decisions:
        if not groups or any(groups[-1][-1]["at"] < at <= event["at"] for at, _sha in commits):
            groups.append([event])
        else:
            groups[-1].append(event)

    episodes = [first.episode]
    boundaries = [first.boundary]
    segments: List[ReviewRoundSegment] = []
    bundle_hash = sha256_file(bundle_path)
    for round_index, group in enumerate(groups, 1):
        review_started_at = group[0]["at"]
        explicit_head = next(
            (
                event.get("commit_id")
                for event in group
                if event["at"] == review_started_at and event.get("commit_id")
            ),
            None,
        )
        if explicit_head and explicit_head in commit_shas:
            reviewed_head = str(explicit_head)
            resolution = "review_commit_id"
        else:
            prior = [sha for at, sha in commits if at < review_started_at]
            if not prior:
                raise ValueError(f"PR {pr_number} round {round_index}: no commit before review")
            reviewed_head = prior[-1]
            resolution = "pushed_before_review"
        pushes_after = [(at, sha) for at, sha in commits if at > review_started_at]
        feedback_end, next_head = pushes_after[0] if pushes_after else (None, None)
        feedback = [
            event
            for event in substantive
            if event["at"] >= review_started_at
            and (feedback_end is None or event["at"] < feedback_end)
        ]
        triggers = [
            event["source_event_id"] for event in group if event["at"] == review_started_at
        ]
        episode_id = f"{repo}:{pr_number}:round{round_index}:{reviewed_head}"
        segment_id = f"segment:{sha256_bytes(canonical_json_bytes([episode_id, review_started_at]))}"

        if round_index == 1:
            if first.episode.episode_id != episode_id:
                raise ValueError(f"PR {pr_number}: multi-round segmentation changed round one")
            segments.append(
                ReviewRoundSegment(
                    segment_id=segment_id,
                    episode_id=episode_id,
                    repo=repo,
                    pr_number=pr_number,
                    round_index=round_index,
                    review_started_at=review_started_at,
                    feedback_window_end=feedback_end,
                    reviewed_head_sha=reviewed_head,
                    reviewed_head_resolution=resolution,
                    triggering_event_ids=triggers,
                    feedback_event_ids=[event["source_event_id"] for event in feedback],
                    next_head_sha=next_head,
                    hydration_status="hydrated",
                )
            )
            continue

        try:
            diff, merge_base, compare_hash, _compare_path = review_diff(compare_cache, reviewed_head)
        except ValueError as exc:
            segments.append(
                ReviewRoundSegment(
                    segment_id=segment_id,
                    repo=repo,
                    pr_number=pr_number,
                    round_index=round_index,
                    review_started_at=review_started_at,
                    feedback_window_end=feedback_end,
                    reviewed_head_sha=reviewed_head,
                    reviewed_head_resolution=resolution,
                    triggering_event_ids=triggers,
                    feedback_event_ids=[event["source_event_id"] for event in feedback],
                    next_head_sha=next_head,
                    hydration_status="missing_compare",
                    exclusion_reason=str(exc),
                )
            )
            continue

        description = _description_at_review(bundle, review_started_at)
        title = _clean_title(pr.get("title"))
        projection = {
            "repo": repo,
            "pr_number": pr_number,
            "round_index": round_index,
            "title": title,
            "description": description.model_dump(mode="json"),
            "base_sha": merge_base,
            "reviewed_head_sha": reviewed_head,
            "diff_sha256": sha256_bytes(diff.encode("utf-8")),
            "bundle_sha256": bundle_hash,
            "compare_sha256": compare_hash,
        }
        episode = ReviewEpisodeInput(
            episode_id=episode_id,
            repo=repo,
            pr_number=pr_number,
            round_index=round_index,
            title=VisibleText(text=title, provenance="source_current_value_unverified"),
            description=description,
            base_sha=merge_base,
            reviewed_head_sha=reviewed_head,
            diff=diff,
            changed_files=changed_files_from_diff(diff),
            patch_sha256=sha256_bytes(diff.encode("utf-8")),
            source_projection_sha256=sha256_bytes(canonical_json_bytes(projection)),
        )
        boundary = ReviewEpisodeBoundary(
            episode_id=episode_id,
            repo=repo,
            pr_number=pr_number,
            round_index=round_index,
            review_started_at=review_started_at,
            feedback_window_end=feedback_end,
            reviewed_head_sha=reviewed_head,
            reviewed_head_resolution=resolution,
            triggering_event_ids=triggers,
            feedback_event_ids=[event["source_event_id"] for event in feedback],
            next_head_sha=next_head,
            source_bundle_sha256=bundle_hash,
            compare_sha256=compare_hash,
        )
        episodes.append(episode)
        boundaries.append(boundary)
        segments.append(
            ReviewRoundSegment(
                segment_id=segment_id,
                episode_id=episode_id,
                repo=repo,
                pr_number=pr_number,
                round_index=round_index,
                review_started_at=review_started_at,
                feedback_window_end=feedback_end,
                reviewed_head_sha=reviewed_head,
                reviewed_head_resolution=resolution,
                triggering_event_ids=triggers,
                feedback_event_ids=[event["source_event_id"] for event in feedback],
                next_head_sha=next_head,
                hydration_status="hydrated",
            )
        )
    return decision, MultiRoundBuildResult(
        episodes=episodes, boundaries=boundaries, segments=segments
    )
