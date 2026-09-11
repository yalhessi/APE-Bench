"""
Stage C: derive a first-round-review gold record from a raw PR bundle.

Pure functions over the cached bundle (no network), implementing the
operational definitions of docs/research/review-task-spec.md §3:

  t₁  — first substantive reviewer event (§3.2)
  h₀  — head the first reviewer saw, with provenance (§3.3)
  F₁  — substantive reviewer events in [t₁, first subsequent push) (§3.4)
  v₁  — round-1 verdict (§3.5)
  funnel — eligibility checks (§3.8), every drop recorded with a reason

Change-sets (Δ) and δ₀ hydration are stage D (delta.py): they need compare-API
calls, and this module stays network-free so dataset iteration is instant.
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from .config import PRReviewV2Config
from .schema import (
    Anchor,
    GoldBlock,
    GoldComment,
    InputBlock,
    Outcome,
    PRReviewV2Record,
    SkipReason,
    SliceFlags,
    ValidationBlock,
)

# The identity, substance, title and file rules shared with the release builder live in
# `src/datasets/pull_reviews/definitions.py`; this module and `episode_builder.py` held
# byte-identical copies. Names are re-exported because the v2 tests and `corpus.py` import them.
from src.datasets.pull_reviews.definitions import (  # noqa: E402
    APPROVAL_SIGNAL_RE,
    BORS_MERGED_TITLE_RE,
    BORS_TITLE_PREFIX_RE,
    MAINTAINER_ASSOCIATIONS,
    REVERT_TITLE_RE,
    TOOLCHAIN_ONLY_FILES,
    TRIVIAL_FEEDBACK_PATTERNS,
    classify_commenter,
    clean_description as clean_input_description,
    clean_title as clean_input_title,
    is_bot,
    is_substantive_event as _is_substantive,
    load_roster as _load_roster_file,
    strip_trivial_tokens,
)

AI_GENERATED_LABELS = {"llm-generated", "llm_generated", "ai-generated"}
AUTOMATED_SWEEP_TITLE_RE = re.compile(
    r"^\s*chore(\(|:)|deprecat(e|ion)s? .*sweep|bump .*(toolchain|dependenc)", re.IGNORECASE
)

DeriveResult = Union[PRReviewV2Record, SkipReason]


# ---------------------------------------------------------------------------
# small text/identity helpers
# ---------------------------------------------------------------------------

def load_roster(config: PRReviewV2Config) -> Set[str]:
    """The configured roster, or empty when none is configured (derive then falls back to
    `author_association`, and `ReviewerIdentity` stops counting disagreements)."""
    if not config.roster_file or not config.roster_file.exists():
        return set()
    return set(_load_roster_file(config.roster_file))


class ReviewerIdentity:
    """Spec §3.1: curated roster primary, author_association fallback, bots/author excluded."""

    def __init__(self, roster: Set[str], pr_author: Optional[str], config: PRReviewV2Config):
        self.roster = roster
        self.pr_author = (pr_author or "").lower()
        self.use_fallback = config.use_association_fallback
        self.association_only_hits = 0  # roster-vs-association disagreement counter (§7.7)

    def is_reviewer(self, login: Optional[str], association: Optional[str]) -> bool:
        decision = classify_commenter(login, association, self.pr_author, self.roster,
                                      use_association_fallback=self.use_fallback)
        if decision.is_reviewer and decision.basis == "association" and self.roster:
            self.association_only_hits += 1
        return decision.is_reviewer


# ---------------------------------------------------------------------------
# event extraction
# ---------------------------------------------------------------------------

def _normalize_events(bundle: Dict[str, Any], identity: ReviewerIdentity) -> List[Dict[str, Any]]:
    """Flatten reviews / inline comments / issue comments into one time-sorted stream."""
    events: List[Dict[str, Any]] = []

    for review in bundle.get("reviews") or []:
        login = ((review.get("user") or {}).get("login"))
        state = str(review.get("state") or "").upper()
        if not review.get("submitted_at"):
            continue
        events.append(
            {
                "kind": "review_body",
                "id": f"review_{review.get('id')}",
                "author": login,
                "is_reviewer": identity.is_reviewer(login, review.get("author_association")),
                "submitted_at": review["submitted_at"],
                "body": review.get("body") or "",
                "state": state if state in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"} else None,
                "commit_id": review.get("commit_id"),
            }
        )

    for comment in bundle.get("review_comments") or []:
        login = ((comment.get("user") or {}).get("login"))
        if not comment.get("created_at"):
            continue
        events.append(
            {
                "kind": "inline",
                "id": f"rc_{comment.get('id')}",
                "raw_id": comment.get("id"),
                "author": login,
                "is_reviewer": identity.is_reviewer(login, comment.get("author_association")),
                "submitted_at": comment["created_at"],
                "body": comment.get("body") or "",
                "state": None,
                # original_commit_id first: GitHub repositions inline comments as the
                # PR evolves, updating commit_id to the *current* attachment commit —
                # using it for h₀ resolves to the final head (observed on PR 33048).
                "commit_id": comment.get("original_commit_id") or comment.get("commit_id"),
                "anchor": {
                    "path": comment.get("path"),
                    "line": comment.get("line"),
                    "original_line": comment.get("original_line"),
                    "side": comment.get("side"),
                },
            }
        )

    for comment in bundle.get("issue_comments") or []:
        login = ((comment.get("user") or {}).get("login"))
        if not comment.get("created_at"):
            continue
        events.append(
            {
                "kind": "issue_comment",
                "id": f"ic_{comment.get('id')}",
                "author": login,
                "is_reviewer": identity.is_reviewer(login, comment.get("author_association")),
                "submitted_at": comment["created_at"],
                "body": comment.get("body") or "",
                "state": None,
            }
        )

    # At equal timestamps a review submission precedes the inline comments it carries.
    kind_order = {"review_body": 0, "inline": 1, "issue_comment": 2}
    events.sort(key=lambda e: (e["submitted_at"], kind_order[e["kind"]], e["id"]))
    return events


def _commit_times(bundle: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(committer_date, sha) per PR commit, sorted. Committer date is the best
    push-time proxy REST offers (§3.3 known failure mode; audited in Step 2)."""
    out: List[Tuple[str, str]] = []
    for item in bundle.get("commits") or []:
        sha = item.get("sha")
        commit = item.get("commit") or {}
        date = ((commit.get("committer") or {}).get("date")) or ((commit.get("author") or {}).get("date"))
        if sha and date:
            out.append((date, sha))
    out.sort()
    return out


def _ready_for_review_floor(bundle: Dict[str, Any]) -> Optional[str]:
    floors = [
        item.get("created_at")
        for item in bundle.get("timeline") or []
        if item.get("event") == "ready_for_review" and item.get("created_at")
    ]
    return min(floors) if floors else None


# ---------------------------------------------------------------------------
# derivation
# ---------------------------------------------------------------------------

def derive_record(bundle: Dict[str, Any], config: PRReviewV2Config, roster: Set[str]) -> DeriveResult:
    pr = bundle.get("pr") or {}
    pr_number = int(pr.get("number") or 0)

    def skip(stage: str, reason: str) -> SkipReason:
        return SkipReason(pr_number=pr_number, stage=stage, reason=reason)

    author = ((pr.get("user") or {}).get("login")) or ""
    title = str(pr.get("title") or "")
    input_title = clean_input_title(title)

    # --- funnel stage 2: authorship / change-type exclusions (§3.8.2) ---
    if is_bot(author):
        return skip("authorship", "bot_author")
    if REVERT_TITLE_RE.search(title):
        return skip("change_type", "revert")
    files = bundle.get("files") or []
    paths = [str(f.get("filename") or "") for f in files]
    if paths and all(p in TOOLCHAIN_ONLY_FILES for p in paths):
        return skip("change_type", "toolchain_or_build_only")

    # --- funnel stage 3: lean content + size bounds (§3.8.3) ---
    if config.require_mathlib_lean_file and not any(
        p.startswith("Mathlib/") and p.endswith(".lean") for p in paths
    ):
        return skip("content", "no_mathlib_lean_file")
    changed_files = int(pr.get("changed_files") or len(paths))
    if not (config.min_changed_files <= changed_files <= config.max_changed_files):
        return skip("size", f"changed_files={changed_files}")
    diff_lines = int(pr.get("additions") or 0) + int(pr.get("deletions") or 0)
    if not (config.min_diff_lines <= diff_lines <= config.max_diff_lines):
        return skip("size", f"diff_lines={diff_lines}")

    # --- outcome (§3.8.5): open PRs have no defined endpoint ---
    merged = bool(pr.get("merged_at")) or bool(BORS_MERGED_TITLE_RE.match(title))
    state = str(pr.get("state") or "").lower()
    if not merged and state != "closed":
        return skip("outcome", "still_open")
    if not merged and not config.include_unmerged:
        return skip("outcome", "closed_unmerged_excluded")

    # --- reviewer events, t₁ (§3.2) ---
    identity = ReviewerIdentity(roster, author, config)
    events = _normalize_events(bundle, identity)
    floor = _ready_for_review_floor(bundle)
    reviewer_events = [
        e for e in events
        if e["is_reviewer"] and (floor is None or e["submitted_at"] >= floor)
    ]
    substantive = [e for e in reviewer_events if _is_substantive(e)]
    # Command-only approvals (bare APPROVED review, "bors r+", "maintainer merge")
    # are not findings but still anchor t₁ and set the verdict (§3.2, §3.5) — these
    # PRs are the merge-ready control class (§3.8).
    decision_events = [
        e for e in reviewer_events
        if _is_substantive(e) or e.get("state") or APPROVAL_SIGNAL_RE.search(e.get("body") or "")
    ]
    if not decision_events:
        return skip("review_signal", "no_reviewer_events")
    t1 = decision_events[0]["submitted_at"]

    # --- h₀ (§3.3) ---
    commits = _commit_times(bundle)
    if not commits:
        return skip("h0", "no_pr_commits")
    commit_shas = {sha for _, sha in commits}
    first_event_commit = next(
        (e.get("commit_id") for e in decision_events
         if e["submitted_at"] == t1 and e.get("commit_id")),
        None,
    )
    if first_event_commit and first_event_commit in commit_shas:
        h0, h0_resolution = first_event_commit, "review_commit_id"
    else:
        before_t1 = [sha for date, sha in commits if date < t1]
        if not before_t1:
            return skip("h0", "no_commit_before_t1")
        h0, h0_resolution = before_t1[-1], "pushed_before_t1"

    # --- round-1 window and F₁ (§3.4) ---
    pushes_after_t1 = [date for date, _ in commits if date > t1]
    t_push = pushes_after_t1[0] if pushes_after_t1 else None
    in_window = [
        e for e in substantive
        if e["submitted_at"] >= t1 and (t_push is None or e["submitted_at"] < t_push)
    ]
    window_all = [
        e for e in reviewer_events
        if e["submitted_at"] >= t1 and (t_push is None or e["submitted_at"] < t_push)
    ]

    # --- verdict v₁ (§3.5) ---
    states = {e.get("state") for e in window_all}
    has_approval_signal = any(
        e.get("state") == "APPROVED" or APPROVAL_SIGNAL_RE.search(e.get("body") or "")
        for e in window_all
    )
    if "CHANGES_REQUESTED" in states:
        verdict = "CHANGES_REQUESTED"
    elif has_approval_signal:
        verdict = "APPROVED"
    else:
        verdict = "COMMENT_ONLY"

    # --- gold comments ---
    thread_by_comment = _thread_index(bundle)
    gold_comments: List[GoldComment] = []
    for event in in_window:
        anchor = None
        if event.get("anchor") and event["anchor"].get("path"):
            anchor = Anchor(**event["anchor"])
        thread = thread_by_comment.get(event.get("raw_id"))
        gold_comments.append(
            GoldComment(
                id=event["id"],
                author=event["author"] or "",
                kind=event["kind"],
                submitted_at=event["submitted_at"],
                body=event["body"],
                anchor=anchor,
                thread_id=thread["thread_id"] if thread else None,
                thread_resolved=thread["is_resolved"] if thread else None,
            )
        )

    # --- h₁ / final head / rounds (§2, §3.4) ---
    final_head = commits[-1][1]
    h1 = final_head
    if t_push is not None:
        next_round_events = [e for e in substantive if e["submitted_at"] >= t_push]
        if next_round_events:
            t2 = next_round_events[0]["submitted_at"]
            at_t2 = [sha for date, sha in commits if date <= t2]
            h1 = at_t2[-1] if at_t2 else final_head
    rounds = _count_rounds(decision_events, commits)

    # --- validation block (§3.5 cross-checks, §7) ---
    label_timeline = [
        {
            "action": item.get("event"),
            "label": (item.get("label") or {}).get("name"),
            "at": item.get("created_at"),
            "actor": ((item.get("actor") or {}).get("login")),
        }
        for item in bundle.get("timeline") or []
        if item.get("event") in {"labeled", "unlabeled"}
    ]
    process_signals = [
        {"at": e["submitted_at"], "actor": e["author"], "kind": "merge_command",
         "excerpt": (e.get("body") or "")[:120]}
        for e in events
        if APPROVAL_SIGNAL_RE.search(e.get("body") or "")
    ]
    force_push_before_t1 = any(
        item.get("event") == "head_ref_force_pushed" and str(item.get("created_at") or "") < t1
        for item in bundle.get("timeline") or []
    )

    # --- description edit hygiene (§6) ---
    body_edits = bundle.get("body_edits")
    if body_edits is None:
        description_maybe_post_edited = True  # no edit history available → conservative tag
    else:
        description_maybe_post_edited = any(
            (edit.get("edited_at") or "") > t1 for edit in body_edits
        )

    label_names = {str((lab or {}).get("name") or "").lower() for lab in pr.get("labels") or []}
    slices = SliceFlags(
        merged=merged,
        author_is_maintainer=(author.lower() in roster)
        or str(pr.get("author_association") or "").upper() in MAINTAINER_ASSOCIATIONS,
        ai_authored=bool(label_names & AI_GENERATED_LABELS),
        multi_reviewer=len({e["author"] for e in in_window}) > 1,
        automated_sweep=bool(AUTOMATED_SWEEP_TITLE_RE.search(title)),
    )

    merge_signal = next((s["excerpt"] for s in process_signals), None)
    record = PRReviewV2Record(
        repo=config.repo_slug,
        pr_number=pr_number,
        slices=slices,
        input=InputBlock(
            title=input_title,
            description=clean_input_description(pr.get("body")),
            description_maybe_post_edited=description_maybe_post_edited,
            base_sha=str(((pr.get("base") or {}).get("sha")) or ""),  # replaced by merge-base in stage D
            head_sha=h0,
            h0_resolution=h0_resolution,
        ),
        gold=GoldBlock(
            verdict=verdict,
            comments=gold_comments,
            outcome=Outcome(
                merged=merged,
                merged_at=pr.get("merged_at"),
                closed_at=pr.get("closed_at"),
                rounds=rounds,
                merge_signal=merge_signal,
            ),
        ),
        validation=ValidationBlock(
            label_timeline=label_timeline,
            process_signals=process_signals,
            force_push_before_t1=force_push_before_t1,
            roster_association_disagreements=identity.association_only_hits,
            h1_sha=h1,
            final_head_sha=final_head,
            t1=t1,
            t_push=t_push,
        ),
    )
    return record


def _thread_index(bundle: Dict[str, Any]) -> Dict[Any, Dict[str, Any]]:
    index: Dict[Any, Dict[str, Any]] = {}
    for thread in bundle.get("review_threads") or []:
        for comment_id in thread.get("comment_ids") or []:
            index[comment_id] = {
                "thread_id": thread.get("thread_id"),
                "is_resolved": thread.get("is_resolved"),
            }
    return index


def _count_rounds(decision_events: Sequence[Dict[str, Any]], commits: Sequence[Tuple[str, str]]) -> int:
    """Number of maximal reviewer-event groups separated by at least one push."""
    rounds = 0
    commit_dates = [date for date, _ in commits]
    previous_event_time: Optional[str] = None
    for event in decision_events:
        time = event["submitted_at"]
        if previous_event_time is None or any(previous_event_time < d <= time for d in commit_dates):
            rounds += 1
        previous_event_time = time
    return rounds
