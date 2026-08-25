"""Unit tests for the v2 first-round-review collector (derive + delta logic).

All tests run on synthetic bundles — no network. Operational definitions under
test are cross-referenced to docs/research/review-task-spec.md sections.
"""

from typing import Any, Dict, List, Optional

import pytest

from src.datasets.pr_review_v2.config import PRReviewV2Config
from src.datasets.pr_review_v2.delta import (
    diff_patches,
    link_comments_to_hunks,
    parse_patch_hunks,
)
from src.datasets.pr_review_v2.derive import (
    clean_input_description,
    clean_input_title,
    derive_record,
    strip_trivial_tokens,
)
from src.datasets.pr_review_v2.schema import GoldComment, PRReviewV2Record, SkipReason


def _commit(sha: str, date: str) -> Dict[str, Any]:
    return {"sha": sha, "commit": {"committer": {"date": date}, "author": {"date": date}}}


def _review(
    rid: int, state: str, at: str, body: str = "", login: str = "rev1",
    association: str = "MEMBER", commit_id: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": rid, "state": state, "submitted_at": at, "body": body,
        "user": {"login": login}, "author_association": association, "commit_id": commit_id,
    }


def _inline(
    cid: int, at: str, body: str, path: str = "Mathlib/Algebra/Foo.lean",
    line: int = 12, login: str = "rev1", association: str = "MEMBER",
) -> Dict[str, Any]:
    return {
        "id": cid, "created_at": at, "body": body, "user": {"login": login},
        "author_association": association, "path": path, "line": line,
        "original_line": line, "side": "RIGHT", "commit_id": None,
    }


def make_bundle(**overrides: Any) -> Dict[str, Any]:
    bundle: Dict[str, Any] = {
        "pr": {
            "number": 101,
            "title": "feat: add a lemma",
            "body": "Adds `Foo.bar`.",
            "state": "closed",
            "merged_at": "2025-10-02T00:00:00Z",
            "closed_at": "2025-10-02T00:00:00Z",
            "user": {"login": "alice"},
            "author_association": "CONTRIBUTOR",
            "labels": [],
            "additions": 30,
            "deletions": 5,
            "changed_files": 1,
            "base": {"sha": "base000"},
            "head": {"sha": "c2"},
        },
        "reviews": [
            _review(1, "CHANGES_REQUESTED", "2025-10-01T10:00:00Z", "please golf this proof", commit_id="c1"),
            _review(2, "APPROVED", "2025-10-01T14:00:00Z", ""),
        ],
        "review_comments": [_inline(11, "2025-10-01T10:00:00Z", "use `simp` here")],
        "issue_comments": [
            {"id": 21, "created_at": "2025-10-01T10:30:00Z", "body": "Thanks!",
             "user": {"login": "rev1"}, "author_association": "MEMBER"},
        ],
        "commits": [
            _commit("c1", "2025-10-01T08:00:00Z"),
            _commit("c2", "2025-10-01T12:00:00Z"),
        ],
        "files": [{"filename": "Mathlib/Algebra/Foo.lean"}],
        "timeline": [],
        "review_threads": None,
        "body_edits": [],
    }
    for key, value in overrides.items():
        if key == "pr":
            bundle["pr"].update(value)
        else:
            bundle[key] = value
    return bundle


@pytest.fixture()
def config(tmp_path) -> PRReviewV2Config:
    return PRReviewV2Config(cache_dir=tmp_path / "cache", output_dir=tmp_path / "out")


def derive(bundle: Dict[str, Any], config: PRReviewV2Config, roster=frozenset()) -> Any:
    return derive_record(bundle, config, set(roster))


# ---------------------------------------------------------------------------
# §3.2 t₁ / §3.4 F₁ / §3.5 verdict
# ---------------------------------------------------------------------------

class TestFirstRound:
    def test_happy_path(self, config):
        record = derive(make_bundle(), config)
        assert isinstance(record, PRReviewV2Record)
        # t₁ = first substantive reviewer event
        assert record.validation.t1 == "2025-10-01T10:00:00Z"
        # round-1 window closes at the author's next push (c2 @ 12:00), so the
        # 14:00 approval is round 2 and the verdict is CHANGES_REQUESTED
        assert record.validation.t_push == "2025-10-01T12:00:00Z"
        assert record.gold.verdict == "CHANGES_REQUESTED"
        # F₁ keeps the review body and the inline comment; "Thanks!" is trivial (§3.2)
        kinds = {c.kind for c in record.gold.comments}
        assert kinds == {"review_body", "inline"}
        assert len(record.gold.comments) == 2
        assert record.gold.outcome.merged is True
        assert record.gold.outcome.rounds == 2
        # h₁ = head at the next reviewer event = c2
        assert record.validation.h1_sha == "c2"

    def test_h0_from_review_commit_id(self, config):
        record = derive(make_bundle(), config)
        assert record.input.head_sha == "c1"
        assert record.input.h0_resolution == "review_commit_id"

    def test_h0_prefers_original_commit_id_for_inline_comments(self, config):
        """GitHub repositions inline comments: commit_id drifts to the current
        head, original_commit_id stays at the review-time head (PR 33048 bug)."""
        bundle = make_bundle(reviews=[])
        bundle["review_comments"][0]["commit_id"] = "c2"  # drifted to final head
        bundle["review_comments"][0]["original_commit_id"] = "c1"
        record = derive(bundle, config)
        assert record.input.head_sha == "c1"
        assert record.input.h0_resolution == "review_commit_id"

    def test_h0_falls_back_to_last_commit_before_t1(self, config):
        bundle = make_bundle()
        bundle["reviews"][0]["commit_id"] = None
        record = derive(bundle, config)
        assert record.input.head_sha == "c1"
        assert record.input.h0_resolution == "pushed_before_t1"

    def test_approval_only_first_round_is_kept_as_control(self, config):
        """Spec §3.8: command-only approvals are the merge-ready control class."""
        bundle = make_bundle(
            reviews=[_review(1, "APPROVED", "2025-10-01T10:00:00Z", "")],
            review_comments=[],
            issue_comments=[],
        )
        record = derive(bundle, config)
        assert isinstance(record, PRReviewV2Record)
        assert record.gold.verdict == "APPROVED"
        assert record.gold.comments == []

    def test_bors_command_sets_verdict_but_is_not_a_finding(self, config):
        bundle = make_bundle(
            reviews=[],
            review_comments=[],
            issue_comments=[
                {"id": 21, "created_at": "2025-10-01T10:00:00Z", "body": "bors r+",
                 "user": {"login": "rev1"}, "author_association": "MEMBER"},
            ],
        )
        record = derive(bundle, config)
        assert record.gold.verdict == "APPROVED"
        assert record.gold.comments == []
        assert record.gold.outcome.merge_signal is not None

    def test_non_reviewer_comments_excluded(self, config):
        bundle = make_bundle(
            reviews=[_review(1, "CHANGES_REQUESTED", "2025-10-01T10:00:00Z",
                             "needs work", login="drive_by", association="NONE")],
            review_comments=[],
            issue_comments=[],
        )
        result = derive(bundle, config)
        assert isinstance(result, SkipReason)
        assert result.reason == "no_reviewer_events"

    def test_roster_overrides_weak_association(self, config):
        bundle = make_bundle(
            reviews=[_review(1, "CHANGES_REQUESTED", "2025-10-01T10:00:00Z",
                             "needs work", login="trusted", association="NONE")],
            review_comments=[],
            issue_comments=[],
        )
        record = derive(bundle, config, roster={"trusted"})
        assert isinstance(record, PRReviewV2Record)

    def test_events_before_ready_for_review_ignored(self, config):
        bundle = make_bundle(
            timeline=[{"event": "ready_for_review", "created_at": "2025-10-01T11:00:00Z"}],
        )
        record = derive(bundle, config)
        # 10:00 review predates ready_for_review → first counted event is the 14:00 approval
        assert record.validation.t1 == "2025-10-01T14:00:00Z"
        assert record.gold.verdict == "APPROVED"

    def test_multi_reviewer_flag(self, config):
        bundle = make_bundle()
        bundle["review_comments"].append(
            _inline(12, "2025-10-01T10:05:00Z", "also rename this", login="rev2")
        )
        record = derive(bundle, config)
        assert record.slices.multi_reviewer is True


# ---------------------------------------------------------------------------
# §3.8 funnel
# ---------------------------------------------------------------------------

class TestFunnel:
    @pytest.mark.parametrize(
        "overrides, stage, reason_prefix",
        [
            ({"pr": {"user": {"login": "dependabot[bot]"}}}, "authorship", "bot_author"),
            ({"pr": {"title": "Revert: feat add lemma"}}, "change_type", "revert"),
            ({"files": [{"filename": "docs/notes.md"}]}, "content", "no_mathlib_lean_file"),
            ({"pr": {"additions": 5000, "deletions": 0}}, "size", "diff_lines"),
            ({"pr": {"state": "open", "merged_at": None, "closed_at": None}}, "outcome", "still_open"),
        ],
    )
    def test_skips(self, config, overrides, stage, reason_prefix):
        result = derive(make_bundle(**overrides), config)
        assert isinstance(result, SkipReason)
        assert result.stage == stage
        assert result.reason.startswith(reason_prefix)

    def test_bors_era_merged_pr_reclassified(self, config):
        bundle = make_bundle(pr={"merged_at": None, "title": "[Merged by Bors] - feat: add a lemma"})
        record = derive(bundle, config)
        assert isinstance(record, PRReviewV2Record)
        assert record.slices.merged is True
        assert record.input.title == "feat: add a lemma"

    def test_closed_unmerged_kept_in_secondary_slice(self, config):
        bundle = make_bundle(pr={"merged_at": None})
        record = derive(bundle, config)
        assert isinstance(record, PRReviewV2Record)
        assert record.slices.merged is False

    def test_no_body_edit_history_tags_description(self, config):
        record = derive(make_bundle(body_edits=None), config)
        assert record.input.description_maybe_post_edited is True
        record = derive(make_bundle(body_edits=[]), config)
        assert record.input.description_maybe_post_edited is False


# ---------------------------------------------------------------------------
# §3.6 patch-level Δ / §3.7 linkage
# ---------------------------------------------------------------------------

PATCH_A = "@@ -1,3 +1,4 @@\n context\n+lemma foo : 1 = 1 := rfl\n context2\n context3"
PATCH_B = "@@ -10,2 +11,3 @@\n context\n+lemma bar : 2 = 2 := rfl\n context2"


class TestDelta:
    def test_unchanged_patch_yields_empty_delta(self):
        p0 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", PATCH_A)}
        assert diff_patches(p0, p0) == []

    def test_added_and_removed_hunks(self):
        p0 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", PATCH_A)}
        p1 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", PATCH_A + "\n" + PATCH_B)}
        delta = diff_patches(p0, p1)
        assert [d.op for d in delta] == ["added_in_revision"]
        assert "lemma bar" in delta[0].patch

        reverse = diff_patches(p1, p0)
        assert [d.op for d in reverse] == ["removed_in_revision"]

    def test_hunk_identity_ignores_line_drift(self):
        """Upstream churn shifts positions but not content → no spurious Δ."""
        drifted = PATCH_A.replace("@@ -1,3 +1,4 @@", "@@ -7,3 +7,4 @@")
        p0 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", PATCH_A)}
        p1 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", drifted)}
        assert diff_patches(p0, p1) == []

    def test_linkage_by_line_overlap_and_thread_resolution(self):
        p0: Dict[str, List] = {}
        p1 = {"Mathlib/A.lean": parse_patch_hunks("Mathlib/A.lean", PATCH_B)}
        delta = diff_patches(p0, p1)

        def comment(cid: str, line: int, resolved: Optional[bool]) -> GoldComment:
            return GoldComment(
                id=cid, author="rev1", kind="inline", submitted_at="t", body="fix",
                anchor={"path": "Mathlib/A.lean", "line": line},
                thread_resolved=resolved,
            )

        near_hit = comment("c_near", 12, None)        # within hunk range + slack
        resolved_hit = comment("c_resolved", 12, True)
        far_miss = comment("c_far", 400, True)
        link_comments_to_hunks([near_hit, resolved_hit, far_miss], delta, line_slack=5)

        assert near_hit.link_confidence == "line_overlap" and near_hit.linked_hunks
        assert resolved_hit.link_confidence == "resolved_thread"
        assert far_miss.link_confidence == "none" and not far_miss.linked_hunks


class TestHelpers:
    def test_clean_input_title_strips_bors_outcome_prefix(self):
        assert clean_input_title("[Merged by Bors] - feat: add a lemma") == "feat: add a lemma"
        assert clean_input_title("[Closed by Bors] chore: rename declarations") == (
            "chore: rename declarations"
        )
        assert clean_input_title("feat: ordinary title") == "feat: ordinary title"

    def test_clean_input_description_removes_template_noise(self):
        body = """Adds `Foo.bar`.

---
Reviewer-visible note to keep.

<!-- Your PR title will become the first line of the commit message.
Please ask for help on Zulip.
-->

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/from-referrer/)
"""
        assert clean_input_description(body) == "Adds `Foo.bar`.\n\nReviewer-visible note to keep."

    def test_strip_trivial_tokens(self):
        assert strip_trivial_tokens("LGTM! bors r+ :tada:") == ""
        assert strip_trivial_tokens("maintainer merge") == ""
        assert "golf" in strip_trivial_tokens("LGTM but please golf this")
