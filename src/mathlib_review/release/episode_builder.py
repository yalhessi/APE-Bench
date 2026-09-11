"""Derive first-review episodes directly from raw GitHub events and cached Git compares."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.datasets.pull_reviews.definitions import (
    APPROVAL_SIGNAL_RE,
    BORS_MERGED_TITLE_RE,
    REVERT_TITLE_RE,
    TOOLCHAIN_ONLY_FILES,
    clean_description as _clean_description,
    clean_title as _clean_title,
    is_bot as _is_bot,
    is_mathlib_lean_file,
    is_reviewer as _is_reviewer,
    is_substantive_event as _is_substantive,
    load_roster,
)
from src.mathlib_review.diffs import CompareSource, DirectoryCompares
from src.mathlib_review.release.episodes import changed_files_from_diff
from src.mathlib_review.release.events import events_from_bundle
from src.mathlib_review.io import canonical_json_bytes, sha256_bytes, sha256_file
from src.mathlib_review.schema import (
    ArtifactRef,
    FunnelDecision,
    ReviewEpisodeBoundary,
    ReviewEpisodeInput,
    ReviewRoundSegment,
    VisibleText,
)


RAW_EPISODE_BUILDER_VERSION = "raw_first_round_v1"
MULTI_ROUND_BUILDER_VERSION = "raw_multi_round_v1"

# Who counts as a reviewer, what counts as substance, which titles and files gate the funnel: all
# of it lives in `src/datasets/pull_reviews/definitions.py` now. This module and `derive.py` held
# byte-identical copies, and the retrieval corpus held a third that diverged (association alone,
# no author rule). The builder's output is unchanged -- `test_pull_reviews_reproduces_raw_release`
# rebuilds `dev-raw-0.3.0` byte for byte -- and the private names are kept as aliases so the
# funnel below reads as it did.


@dataclass(frozen=True)
class EpisodeBuildResult:
    episode: ReviewEpisodeInput
    boundary: ReviewEpisodeBoundary


@dataclass(frozen=True)
class MultiRoundBuildResult:
    episodes: List[ReviewEpisodeInput]
    boundaries: List[ReviewEpisodeBoundary]
    segments: List[ReviewRoundSegment]


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


def _sources(
    bundle_path: Optional[Path], compare_cache: Optional[Path],
    bundle_sha256: Optional[str], compares: Optional[CompareSource],
) -> Tuple[str, ArtifactRef, CompareSource]:
    """Resolve where a bundle and its compares come from: the v2 cache paths, or a sha plus a
    compare source (the PR store). Exactly one of each pair, so a caller cannot half-switch."""

    if (bundle_path is None) == (bundle_sha256 is None):
        raise TypeError("pass exactly one of bundle_path or bundle_sha256")
    if (compare_cache is None) == (compares is None):
        raise TypeError("pass exactly one of compare_cache or compares")
    if bundle_path is not None:
        sha = sha256_file(bundle_path)
        ref = ArtifactRef(path=bundle_path.as_posix(), role="raw_github_bundle", sha256=sha)
    else:
        sha = str(bundle_sha256)
        ref = ArtifactRef(path="pull_review_store", role="raw_github_bundle", sha256=sha)
    return sha, ref, compares if compares is not None else DirectoryCompares(compare_cache)


def _normalized_feedback_events(
    bundle: Dict[str, Any], *, source_object: ArtifactRef, repo: str, author: str, roster: set[str]
) -> List[Dict[str, Any]]:
    source_ids = {
        event.source_key: event.event_id
        for event in events_from_bundle(bundle, source_object=source_object, repo=repo)
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


def _ready_for_review_floor(bundle: Dict[str, Any]) -> Optional[str]:
    values = [
        item.get("created_at")
        for item in bundle.get("timeline") or []
        if item.get("event") == "ready_for_review" and item.get("created_at")
    ]
    return min(values) if values else None


def _reviewer_activity(
    bundle: Dict[str, Any], *, source_object: ArtifactRef, repo: str, author: str, roster: set[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """(reviewer events, substantive ones, decisions): the funnel's reading of who reviewed.

    A *decision* is a reviewer event after ready-for-review that is substantive, carries any review
    state, or is a bors / maintainer-merge signal. The first-round funnel, the multi-round builder
    and the collector's tier-2 pre-gate all call this, so the pre-gate cannot drift from the funnel
    it stands in front of -- an approximation of it, written separately, missed 14 of the 138 PRs
    the funnel includes.
    """

    events = _normalized_feedback_events(
        bundle, source_object=source_object, repo=repo, author=author, roster=roster)
    floor = _ready_for_review_floor(bundle)
    reviewer_events = [
        event for event in events
        if event["is_reviewer"] and (floor is None or event["at"] >= floor)
    ]
    substantive = [event for event in reviewer_events if _is_substantive(event)]
    decisions = [
        event for event in reviewer_events
        if _is_substantive(event) or event.get("state")
        or APPROVAL_SIGNAL_RE.search(event.get("body") or "")
    ]
    return reviewer_events, substantive, decisions


def has_reviewer_decision(bundle: Dict[str, Any], *, roster, repo: str = "leanprover-community/mathlib4") -> bool:
    """Whether the funnel would find at least one reviewer decision in this bundle.

    Needs only `pr` (or the listing row) and the three conversation endpoints -- tier 1 -- which is
    what lets the collector decide which PRs are worth tier 2 without fetching it. Without the
    timeline the ready-for-review floor is unknown and no event is dropped for predating it, so on
    tier-1 data this can only say yes where the funnel would say no, never the reverse."""

    pr = bundle.get("pr") or {}
    author = str((pr.get("user") or {}).get("login") or "")
    ref = ArtifactRef(path="pre-gate", role="raw_github_bundle", sha256="0" * 64)
    _events, _substantive, decisions = _reviewer_activity(
        bundle, source_object=ref, repo=repo, author=author, roster=set(roster))
    return bool(decisions)


def funnel_and_first_round(
    bundle: Dict[str, Any],
    *,
    bundle_path: Optional[Path] = None,
    compare_cache: Optional[Path] = None,
    bundle_sha256: Optional[str] = None,
    compares: Optional[CompareSource] = None,
    repo: str = "leanprover-community/mathlib4",
    roster: Optional[set[str]] = None,
) -> Tuple[FunnelDecision, Optional[EpisodeBuildResult]]:
    """The eligibility funnel and first review round for one PR.

    Inputs come either from the v2 cache (`bundle_path` + `compare_cache`) or from the PR store
    (`bundle_sha256` + `compares`, from `PullReviewStore.bundle_sha256` / `.compares`). The two are
    byte-equivalent for the 201 seeded PRs -- `test_pull_reviews_reproduces_raw_release` rebuilds
    `dev-raw-0.3.0` from each."""

    bundle_hash, source_object, compare_source = _sources(
        bundle_path, compare_cache, bundle_sha256, compares)
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
    if not any(is_mathlib_lean_file(path) for path in paths):
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

    reviewer_events, substantive, decisions = _reviewer_activity(
        bundle, source_object=source_object, repo=repo, author=author, roster=roster or set())
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
        diff, merge_base, compare_hash = compare_source.review_diff(reviewed_head)
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
    bundle_path: Optional[Path] = None,
    compare_cache: Optional[Path] = None,
    bundle_sha256: Optional[str] = None,
    compares: Optional[CompareSource] = None,
    repo: str = "leanprover-community/mathlib4",
    roster: Optional[set[str]] = None,
) -> Tuple[FunnelDecision, Optional[MultiRoundBuildResult]]:
    """Derive all maximal reviewer-event groups separated by at least one author push."""
    bundle_hash, source_object, compare_source = _sources(
        bundle_path, compare_cache, bundle_sha256, compares)
    decision, first = funnel_and_first_round(
        bundle,
        bundle_sha256=bundle_hash,
        compares=compare_source,
        repo=repo,
        roster=roster,
    )
    if not first:
        return decision, None

    pr = bundle.get("pr") or {}
    pr_number = int(pr["number"])
    author = str((pr.get("user") or {}).get("login") or "")
    reviewer_events, substantive, decisions = _reviewer_activity(
        bundle, source_object=source_object, repo=repo, author=author, roster=roster or set())
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
            diff, merge_base, compare_hash = compare_source.review_diff(reviewed_head)
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
