"""Recover inline discussions in which the requesting reviewer answers the PR author.

Run from the repository root with PYTHONPATH=. and the project Python. The output is
source material. An author reply followed by a reviewer reply carries no automatic verdict.
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.datasets.pull_requests.definitions import scored_pr_numbers
from src.datasets.pull_requests.store import PullRequestStore, write_atomically
from src.mathlib_review.io import jsonl_bytes, jsonl_rows


PAIRS = Path("data/pr_review_v5/first_round_development_before_2026-01-01.jsonl")
ARCHIVE = Path("data/pull_requests/projections/corpus/comments.jsonl")
CUTOFF = {"development": "2026-01-01T00:00:00Z", "earlier": "2025-01-01T00:00:00Z"}


def development_roots():
    return {
        row["pr_number"]: {ask["gh_id"] for ask in row["requests"]
                           if ask["kind"] == "review_comment" and not ask["in_reply_to"]}
        for row in jsonl_rows(PAIRS)
    }


def earlier_roots():
    """Preselect plausible conversations in the old projection. Check order in the raw store."""
    excluded = scored_pr_numbers()
    opened, author_replied, other_replied = set(), set(), set()
    with ARCHIVE.open() as rows:
        for line in rows:
            row = json.loads(line)
            pr = row["pr_number"]
            if row["created_at"] >= CUTOFF["earlier"] or pr in excluded:
                continue
            parent = row["in_reply_to_id"]
            if parent is not None:
                participants = author_replied if row["commenter_is_author"] else other_replied
                participants.add((pr, parent))
            elif row["is_reviewer"]:
                opened.add((pr, row["comment_id"]))
    roots = defaultdict(set)
    for pr, root in opened & author_replied & other_replied:
        roots[pr].add(root)
    return roots


def discussions(source, roots, counts):
    store = PullRequestStore()
    cutoff = CUTOFF[source]
    for pr, root_ids in sorted(roots.items()):
        if not root_ids:
            continue
        author = store.read(pr, "listing")["user"]["login"].lower()
        groups = defaultdict(list)
        for comment in store.read(pr, "review_comments"):
            root = comment.get("in_reply_to_id") or comment["id"]
            if root in root_ids and comment["created_at"] < cutoff:
                groups[root].append(comment)
        for root, group in sorted(groups.items()):
            group.sort(key=lambda c: (c["created_at"], c["id"]))
            first = group[0]
            if first["id"] != root or first.get("in_reply_to_id"):
                raise ValueError(f"Missing opening comment {root} in PR {pr}")
            if any(c["updated_at"] >= cutoff for c in group):
                continue
            counts["opening comments checked"] += 1
            reviewer = first["user"]["login"].lower()
            if reviewer == author:
                raise ValueError(f"Source root {root} in PR {pr} was opened by the author")
            roles = {reviewer: "reviewer", author: "author"}
            saw_author = False
            returned = False
            last_edit = ""
            prefix_ready = []
            messages = []
            for c in group:
                login = c["user"]["login"].lower()
                role = roles.get(login, "other")
                if role == "reviewer" and saw_author:
                    returned = True
                    if last_edit < c["created_at"]:
                        prefix_ready.append(c["id"])
                if role == "author":
                    saw_author = True
                last_edit = max(last_edit, c["updated_at"])
                messages.append({"id": c["id"], "role": role, "login": login, "body": c["body"],
                                 "created_at": c["created_at"], "updated_at": c["updated_at"]})
            counts["with author reply"] += saw_author
            if returned:
                yield {"pr_number": pr, "root": root, "path": first["path"],
                       "original_commit_id": first["original_commit_id"], "diff_hunk": first["diff_hunk"],
                       "prefix_visible_for": prefix_ready, "messages": messages}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=CUTOFF)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    counts = Counter()
    roots = development_roots() if args.source == "development" else earlier_roots()
    rows = list(discussions(args.source, roots, counts))
    write_atomically(args.output, jsonl_bytes(rows))
    print(dict(counts), f"{len(rows)} threads on {len({r['pr_number'] for r in rows})} PRs, "
          f"{sum(bool(r['prefix_visible_for']) for r in rows)} with a dated input prefix")
