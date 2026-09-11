"""The review-comment corpus, as a projection of the PR store.

The corpus used to be *collected*: `pr_review_v2/corpus.py` kept a comment at fetch time if its
author's `author_association` was MEMBER/OWNER/COLLABORATOR. That had no roster, so it dropped
every reviewer GitHub reports as CONTRIBUTOR, and no author rule, so it kept PR authors replying on
their own PRs -- on the 201 cached bundles, 144 and 44 comments of the 259 it should have decided.

Here the corpus is *derived*, and reviewer status is a **tag**, not a filter:

* `comments.jsonl` -- every non-bot, substantive inline comment anchored on a Lean file, in the
  window, from any PR that is not scored. Each row is the old 17-field `corpus_row` plus
  `schema_version`, `is_reviewer`, `reviewer_basis` (`roster` / `association` / `both` / `none`),
  `commenter_is_author` and `has_suggestion`.
* `reviewer_view.jsonl` -- `reviewer_view(comments)`: spec §3.1 reviewers only. This is what the
  precedent index and the review join consume, *by name*, and their manifests record the name, so
  no consumer re-derives the rule and a fifth copy of it cannot appear.

Keeping the author replies (tagged) rather than dropping them is what makes the new corpus a strict
superset of the old one, which is the acceptance test (`acceptance_report`).
"""

from __future__ import annotations

import collections
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.datasets.pull_requests.definitions import (
    DEFINITIONS_VERSION, MAINTAINER_ASSOCIATIONS, classify_commenter, is_bot, is_lean_anchor,
    is_substantive_text, load_roster, roster_sha256, scored_pr_numbers,
)
from src.datasets.pull_requests.store import PullRequestStore, write_atomically
from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes

CORPUS_ROW_VERSION = "pr-corpus-row/2"
CORPUS_PROJECTION_VERSION = "pr-corpus-projection/1"
REVIEWER_VIEW = "reviewer_view/1"
_PR_NUM_RE = re.compile(r"/pulls/(\d+)$")
SUGGESTION = re.compile(r"```suggestion\b")


def pr_number(comment: Dict[str, Any]) -> Optional[int]:
    m = _PR_NUM_RE.search(str(comment.get("pull_request_url") or ""))
    return int(m.group(1)) if m else None


def corpus_row(comment: Dict[str, Any]) -> Dict[str, Any]:
    """A retrieval situation: the comment and the code it was anchored to. The 17 fields the
    collected corpus always had, so rows compare field for field with the acceptance baseline."""

    return {
        "comment_id": comment.get("id"),
        "pr_number": pr_number(comment),
        "path": comment.get("path"),
        "line": comment.get("line") or comment.get("original_line"),
        "start_line": comment.get("start_line") or comment.get("original_start_line"),
        "original_position": comment.get("original_position"),
        "original_line": comment.get("original_line"),
        "side": comment.get("side"),
        "subject_type": comment.get("subject_type"),
        "diff_hunk": comment.get("diff_hunk") or "",
        "body": comment.get("body") or "",
        "commenter": (comment.get("user") or {}).get("login"),
        "author_association": comment.get("author_association"),
        "created_at": comment.get("created_at"),
        "in_reply_to_id": comment.get("in_reply_to_id"),
        "commit_id": comment.get("commit_id"),
        "html_url": comment.get("html_url"),
    }


def _pr_author(store: PullRequestStore, number: int) -> str:
    endpoints = store.ledger(number)["endpoints"]
    for name in ("listing", "pr"):
        if endpoints.get(name, {}).get("present"):
            return str(((store.read(number, name) or {}).get("user") or {}).get("login") or "")
    return ""


def project_corpus(store: PullRequestStore, *, roster: Iterable[str], start: Optional[str] = None,
                   end: Optional[str] = None, exclude: Optional[Iterable[int]] = None) -> List[Dict[str, Any]]:
    """Every corpus row the store supports, tagged. `exclude` defaults to the scored PRs."""

    roster = frozenset(roster)
    excluded = set(scored_pr_numbers() if exclude is None else exclude)
    rows = []
    for number in store.numbers():
        if number in excluded or "review_comments" not in store.ledger(number)["endpoints"]:
            continue
        author = _pr_author(store, number)
        for comment in store.read(number, "review_comments") or []:
            login = (comment.get("user") or {}).get("login")
            day = str(comment.get("created_at") or "")[:10]
            if (is_bot(login) or not is_lean_anchor(comment.get("path"))
                    or not is_substantive_text(comment.get("body"))
                    or (start and day < start) or (end and day > end)):
                continue
            decision = classify_commenter(login, comment.get("author_association"), author, roster)
            row = corpus_row(comment)
            row.update({
                "schema_version": CORPUS_ROW_VERSION,
                "is_reviewer": decision.is_reviewer,
                "reviewer_basis": decision.basis,
                "commenter_is_author": decision.excluded == "pr_author",
                "has_suggestion": bool(SUGGESTION.search(row["body"])),
            })
            rows.append(row)
    rows.sort(key=lambda r: (r["created_at"] or "", r["comment_id"] or 0))
    return rows


def reviewer_view(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Spec §3.1 reviewers: roster (or association fallback), not a bot, not the PR author."""

    return [row for row in rows if row["is_reviewer"] and not row["commenter_is_author"]]


def write_corpus_projection(store: PullRequestStore, *, roster_path: Path, out: Optional[Path] = None,
                            start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
    out = Path(out) if out else store.root / "projections" / "corpus"
    rows = project_corpus(store, roster=load_roster(roster_path), start=start, end=end)
    view = reviewer_view(rows)
    all_bytes, view_bytes = jsonl_bytes(rows), jsonl_bytes(view)
    write_atomically(out / "comments.jsonl", all_bytes)
    write_atomically(out / "reviewer_view.jsonl", view_bytes)
    manifest = {
        "projection_version": CORPUS_PROJECTION_VERSION, "row_version": CORPUS_ROW_VERSION,
        "view": REVIEWER_VIEW, "definitions_version": DEFINITIONS_VERSION,
        "store_content_sha256": store.content_digest(),
        "roster": {"path": str(roster_path), "sha256": roster_sha256(roster_path)},
        "window": [start, end], "excluded_scored_prs": len(scored_pr_numbers()),
        "rows": len(rows), "reviewer_view_rows": len(view),
        "comments_sha256": sha256_bytes(all_bytes), "reviewer_view_sha256": sha256_bytes(view_bytes),
        "by_basis": dict(collections.Counter(r["reviewer_basis"] for r in rows)),
        "author_self_comments": sum(r["commenter_is_author"] for r in rows),
        "with_suggestion": sum(r["has_suggestion"] for r in rows),
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    write_atomically(out / "manifest.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    return manifest


# --- acceptance ------------------------------------------------------------------------------------

#: Fields every baseline row has; a shared row must agree on all of them.
COMPARED_FIELDS = ("pr_number", "path", "line", "start_line", "diff_hunk", "body", "commenter",
                   "author_association", "created_at", "in_reply_to_id", "commit_id", "html_url")


def _old_gate(row: Dict[str, Any]) -> bool:
    return (not is_bot(row["commenter"])
            and str(row["author_association"] or "").upper() in MAINTAINER_ASSOCIATIONS
            and is_lean_anchor(row["path"]) and is_substantive_text(row["body"]))


def acceptance_report(new_rows: List[Dict[str, Any]], baseline_rows: List[Dict[str, Any]],
                      store: PullRequestStore) -> Dict[str, Any]:
    """Old ⊆ new, field for field, and a cause for every added row.

    A baseline row missing from the projection is a **failure** unless the comment is also absent
    from the raw payload the store holds for its PR (`deleted_upstream`) -- a data change, not a
    filter regression. A shared row that differs is a failure unless GitHub shows the comment
    edited since it was created (`edited_upstream`) or only its association moved
    (`association_changed_upstream`, which the old gate would have been sensitive to and the tag is
    not). Every added row is caused by construction: either the old gate would have rejected it --
    and then it is a roster reviewer, a PR author, or a non-reviewer -- or the old gate would have
    kept it and the old collector never reached it (`old_collection_gap`).
    """

    new = {r["comment_id"]: r for r in new_rows}
    raw_ids: Dict[int, Dict[int, Dict[str, Any]]] = {}

    def raw(number: int) -> Dict[int, Dict[str, Any]]:
        if number not in raw_ids:
            raw_ids[number] = ({c["id"]: c for c in store.read(number, "review_comments") or []}
                               if store.has(number) and "review_comments" in store.ledger(number)["endpoints"]
                               else {})
        return raw_ids[number]

    missing = collections.Counter()
    missing_failures: List[Any] = []
    mismatches = collections.Counter()
    mismatch_failures: List[Tuple[Any, List[str]]] = []
    for old in baseline_rows:
        cid = old["comment_id"]
        mine = new.get(cid)
        if mine is None:
            if cid in raw(old["pr_number"]):
                missing["present_in_raw_but_not_projected"] += 1
                missing_failures.append(cid)
            elif store.has(old["pr_number"]):
                missing["deleted_upstream"] += 1
            else:
                missing["pr_not_collected"] += 1
                missing_failures.append(cid)
            continue
        differing = [f for f in COMPARED_FIELDS if old.get(f) != mine.get(f)]
        if not differing:
            continue
        payload = raw(old["pr_number"]).get(cid, {})
        if set(differing) <= {"author_association"}:
            mismatches["association_changed_upstream"] += 1
        elif set(differing) <= {"body", "author_association"} and \
                str(payload.get("updated_at") or "") > str(payload.get("created_at") or ""):
            mismatches["edited_upstream"] += 1
        else:
            mismatches["unexplained"] += 1
            mismatch_failures.append((cid, differing))

    baseline_ids = {r["comment_id"] for r in baseline_rows}
    added = collections.Counter()
    gap_prs = collections.Counter()
    for cid, row in new.items():
        if cid in baseline_ids:
            continue
        if _old_gate(row):
            added["old_collection_gap"] += 1
            gap_prs[row["pr_number"]] += 1
        elif row["is_reviewer"]:
            added["roster_reviewer"] += 1
        elif row["commenter_is_author"]:
            added["author_self_comment"] += 1
        else:
            added["non_reviewer_contributor"] += 1

    return {
        "baseline_rows": len(baseline_rows), "projection_rows": len(new_rows),
        "reviewer_view_rows": len(reviewer_view(new_rows)),
        "superset": not missing_failures, "fields_agree": not mismatch_failures,
        "passed": not missing_failures and not mismatch_failures,
        "missing": dict(missing), "missing_failures": missing_failures[:50],
        "shared_row_mismatches": dict(mismatches), "mismatch_failures": mismatch_failures[:50],
        "added_by_cause": dict(added), "old_collection_gap_prs": dict(gap_prs.most_common(50)),
    }


def load_baseline(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    import argparse

    from src.mathlib_review.paths import PULL_REQUESTS_TRACKED, assert_repo_root

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", default="2024-03-01")
    parser.add_argument("--end", default="2025-12-31")
    parser.add_argument("--roster", type=Path, default=None, help="default: latest dated roster")
    parser.add_argument("--store", type=Path, default=None)
    parser.add_argument("--acceptance", action="store_true",
                        help="also check the projection against the frozen acceptance baseline and "
                             "write inputs/pull_requests/acceptance_report.json")
    args = parser.parse_args()
    assert_repo_root()
    from src.datasets.pull_requests.collect import latest_roster

    store = PullRequestStore(args.store) if args.store else PullRequestStore()
    roster_path = args.roster or latest_roster()
    manifest = write_corpus_projection(store, roster_path=roster_path, start=args.start, end=args.end)
    print(json.dumps({k: manifest[k] for k in ("rows", "reviewer_view_rows", "by_basis",
                                               "author_self_comments", "with_suggestion")}, indent=2))
    if args.acceptance:
        record = json.loads((PULL_REQUESTS_TRACKED / "acceptance_baseline.json").read_text())
        baseline_path = Path(record["path"])
        if sha256_bytes(baseline_path.read_bytes()) != record["sha256"]:
            raise SystemExit(f"the acceptance baseline at {baseline_path} no longer matches its "
                             "recorded sha; restore it before judging the projection against it")
        rows = [json.loads(line) for line in (store.root / "projections/corpus/comments.jsonl")
                .read_text(encoding="utf-8").splitlines() if line.strip()]
        report = acceptance_report(rows, load_baseline(baseline_path), store)
        report.update({"baseline_sha256": record["sha256"], "projection": {
            k: manifest[k] for k in ("store_content_sha256", "comments_sha256", "roster", "window")}})
        write_atomically(PULL_REQUESTS_TRACKED / "acceptance_report.json",
                         (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print(json.dumps({k: report[k] for k in ("passed", "superset", "fields_agree", "missing",
                                                 "shared_row_mismatches", "added_by_cause")}, indent=2))
        if not report["passed"]:
            raise SystemExit("acceptance FAILED; see inputs/pull_requests/acceptance_report.json")


if __name__ == "__main__":
    main()
