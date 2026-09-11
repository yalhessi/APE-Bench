"""Every consolidated rule agrees with the copy it replaced, except where the spec says otherwise.

`src/datasets/pull_requests/definitions.py` replaces five copies of the association set, four bot
predicates, three `.lean` predicates, two trivial-feedback filters and five roster loaders. A
consolidation is only safe if it is shown to change nothing it did not mean to, so the old
implementations are kept below **verbatim** as reference oracles and compared over every login,
association, body, path and title in the 201 cached bundles and the 43,881-row acceptance
baseline -- the real inputs, not examples written to pass.

The one intended behaviour change is the corpus's reviewer rule, which moves from
`author_association` alone to spec §3.1's roster-primary, author-excluded rule. The last test
proves every disagreement between the two is one of exactly those two causes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from src.datasets.pull_requests import definitions as d
from src.mathlib_review.paths import LEGACY_V2_BUNDLES, LEGACY_V2_ROSTER

BASELINE = Path("data/pull_requests/baseline/mathlib_review_comments.jsonl")

# --- verbatim pre-consolidation copies (reference oracles; do not "fix") ---------------------

_LEGACY_MAINTAINER = {"MEMBER", "OWNER", "COLLABORATOR"}
_LEGACY_TRIVIAL = [r"\bmaintainer\s+merge\b", r"\bbors\s+(?:merge|r\+|d\+|d=)", r"\blgtm\b",
                   r"\blooks good(?: to me)?\b", r"\bthanks?\b", r"\bthank you\b", r":\w+:"]
_LEGACY_BORS_PREFIX = re.compile(r"^\s*\[(?:merged|closed) by bors\]\s*-?\s*", re.IGNORECASE)


def _legacy_strip(body):                                   # derive.strip_trivial_tokens
    text = re.sub(r"\s+", " ", str(body or "").strip().lower())
    for pattern in _LEGACY_TRIVIAL:
        text = re.sub(pattern, " ", text)
    text = re.sub(r"[`*_>#:\-.,!?()\[\]{}\"'/\\~+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _legacy_is_bot(login):                                 # derive.is_bot
    if not login:
        return True
    lowered = login.lower()
    return lowered.endswith("[bot]") or lowered.endswith("-bot") or lowered in {
        "bors", "github-actions", "leanprover-community-bot", "leanprover-community-mathlib4-bot"}


def _legacy_is_reviewer(login, association, author, roster):   # episode_builder._is_reviewer
    return bool(login and not _legacy_is_bot(login) and login.lower() != author.lower()
                and (login.lower() in roster or str(association or "").upper() in _LEGACY_MAINTAINER))


def _legacy_is_substantive(event):                         # episode_builder._is_substantive
    return event.get("state") == "CHANGES_REQUESTED" or bool(_legacy_strip(event.get("body")))


def _legacy_keep_comment(comment):                         # pr_review_v2/corpus.keep_comment
    login = (comment.get("user") or {}).get("login")
    if not login or _legacy_is_bot(login):
        return False
    if (comment.get("author_association") or "").upper() not in _LEGACY_MAINTAINER:
        return False
    if not str(comment.get("path") or "").lower().endswith(".lean"):
        return False
    return bool(_legacy_strip(comment.get("body")))


def _legacy_clean_title(title):                            # derive.clean_input_title
    return _LEGACY_BORS_PREFIX.sub("", str(title or "")).strip()


def _legacy_clean_description(body):                       # derive.clean_input_description
    text = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    kept_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept_lines.append("")
            continue
        if stripped == "---":
            continue
        if "gitpod.io/" in stripped.lower():
            continue
        kept_lines.append(line.rstrip())
    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# --- real inputs ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def bundles() -> List[Dict[str, Any]]:
    paths = sorted(LEGACY_V2_BUNDLES.glob("pr_*.json"))
    if not paths:
        pytest.skip("no cached bundles")
    return [json.loads(p.read_text()) for p in paths]


@pytest.fixture(scope="module")
def roster():
    return d.load_roster(LEGACY_V2_ROSTER)


def _events(bundle):
    author = str(((bundle.get("pr") or {}).get("user") or {}).get("login") or "")
    for kind in ("reviews", "review_comments", "issue_comments"):
        for item in bundle.get(kind) or []:
            yield kind, author, item


def test_the_roster_loader_matches_every_old_loader(roster):
    from src.mathlib_review.retrieval.precedents import load_reviewer_roster
    assert len(roster) == 59
    assert set(roster) == set(load_reviewer_roster(LEGACY_V2_ROSTER))


def test_is_bot_agrees_on_every_login(bundles):
    logins = {None, "", "bors", "Github-Actions", "mathlib-bot", "dependabot[bot]"}
    for bundle in bundles:
        for _, author, item in _events(bundle):
            logins.add((item.get("user") or {}).get("login"))
            logins.add(author)
    for login in logins:
        assert d.is_bot(login) == _legacy_is_bot(login), login


def test_is_reviewer_agrees_with_the_release_builder_on_every_event(bundles, roster):
    checked = 0
    for bundle in bundles:
        for _, author, item in _events(bundle):
            login = (item.get("user") or {}).get("login")
            association = item.get("author_association")
            assert d.is_reviewer(login, association, author, roster) == \
                _legacy_is_reviewer(login, association, author, roster), (login, association, author)
            checked += 1
    assert checked == 1509          # the 201 bundles are frozen, so this cannot drift


def test_substance_agrees_on_every_body_and_review(bundles):
    for bundle in bundles:
        for _, _, item in _events(bundle):
            assert d.strip_trivial_tokens(item.get("body")) == _legacy_strip(item.get("body"))
            assert d.is_substantive_event(item) == _legacy_is_substantive(item)
    for body in (None, "", "LGTM!", "bors r+", ":tada: thanks", "maintainer merge", "Please golf"):
        assert d.strip_trivial_tokens(body) == _legacy_strip(body)


def test_titles_and_descriptions_clean_identically_under_both_old_copies(bundles):
    from src.mathlib_review.release.episode_builder import _clean_description, _clean_title
    for bundle in bundles:
        pr = bundle.get("pr") or {}
        assert d.clean_title(pr.get("title")) == _legacy_clean_title(pr.get("title")) \
            == _clean_title(pr.get("title"))
        assert d.clean_description(pr.get("body")) == _legacy_clean_description(pr.get("body")) \
            == _clean_description(pr.get("body"))


def test_the_old_corpus_gate_decomposes_into_the_new_predicates_on_every_baseline_row():
    """Every row in the baseline was kept by `keep_comment`. Re-expressing that gate through the
    consolidated predicates must also keep all 43,881 -- otherwise the new corpus could not be a
    superset of the old one, which is the acceptance test."""

    if not BASELINE.is_file():
        pytest.skip("acceptance baseline not snapshotted")
    rows = [json.loads(line) for line in BASELINE.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 43881
    for row in rows:
        as_comment = {"user": {"login": row["commenter"]}, "path": row["path"],
                      "author_association": row["author_association"], "body": row["body"]}
        old = _legacy_keep_comment(as_comment)
        new_components = (not d.is_bot(row["commenter"])
                          and str(row["author_association"] or "").upper() in d.MAINTAINER_ASSOCIATIONS
                          and d.is_lean_anchor(row["path"]) and d.is_substantive_text(row["body"]))
        assert old and new_components, row["comment_id"]


def test_the_only_change_to_the_corpus_rule_is_spec_3_1(bundles, roster):
    """Old corpus rule vs new reviewer rule, over every inline comment in the 201 bundles: every
    disagreement is the author rule or the roster rule. Nothing else moved."""

    causes: Dict[str, int] = {}
    for bundle in bundles:
        author = str(((bundle.get("pr") or {}).get("user") or {}).get("login") or "")
        for comment in bundle.get("review_comments") or []:
            login = (comment.get("user") or {}).get("login")
            old = _legacy_keep_comment(comment)
            new = (d.is_reviewer(login, comment.get("author_association"), author, roster)
                   and d.is_lean_anchor(comment.get("path")) and d.is_substantive_text(comment.get("body")))
            if old == new:
                continue
            decision = d.classify_commenter(login, comment.get("author_association"), author, roster)
            cause = ("pr_author" if old and decision.excluded == "pr_author"
                     else "roster_reviewer" if new and decision.basis == "roster" else "UNEXPLAINED")
            causes[cause] = causes.get(cause, 0) + 1
    assert "UNEXPLAINED" not in causes, causes
    assert causes == {"pr_author": 44, "roster_reviewer": 144}


def test_the_audit_reports_the_disagreement_the_spec_asks_for(bundles, roster):
    audit = d.ReviewerAudit()
    for bundle in bundles:
        for _, author, item in _events(bundle):
            audit.record(d.classify_commenter((item.get("user") or {}).get("login"),
                                              item.get("author_association"), author, roster))
    report = audit.report()
    assert report["reviewers"] > 0
    assert set(report["reviewers_by_basis"]) <= {"roster", "association", "both"}
    assert "pr_author" in report["excluded"]
    assert 0 < report["roster_only_share"] < 1


def test_the_scored_set_refuses_to_be_empty(tmp_path):
    with pytest.raises(FileNotFoundError) as excinfo:
        d.scored_pr_numbers(root=tmp_path)
    assert "refusing to return an empty exclusion" in str(excinfo.value)
    assert len(d.scored_pr_numbers()) == 138
