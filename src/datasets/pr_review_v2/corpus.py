"""Stage 0 — build a corpus of historical Mathlib MAINTAINER review comments for precedent
retrieval (docs/research/precedent-retrieval-design.md).

Streams GitHub's repo-level review-comment endpoint (`/repos/{repo}/pulls/comments`), where every
comment already carries its anchored `diff_hunk` — so we get "comment + the code it was made on"
without any per-PR checkout. We keep only substantive MAINTAINER comments on .lean files
(author_association MEMBER/OWNER/COLLABORATOR — this also drops author self-comments, which are
CONTRIBUTOR/NONE), in a created-at window that ends BEFORE the eval window so there is no leakage.

The unit of the corpus is the REVIEW SITUATION (comment + its diff_hunk), not the PR — matching the
retrieval design (query = a site; precedent = a situation).

  python -m src.datasets.pr_review_v2.corpus --start 2024-03-01 --end 2025-08-31 \
      --out inputs/pr_review_v2/corpus/mathlib_review_comments.jsonl

Needs GITHUB_TOKEN (unauthenticated is 60 req/hr; a full window is ~hundreds of pages).
Resumable: re-running appends only comment_ids not already present.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

from ape.utils.logging import create_logger
from ape.utils.project import PROJECT_ROOT

from .derive import MAINTAINER_ASSOCIATIONS, is_bot, strip_trivial_tokens
from .github import GitHubClient
from src.mathlib_review.corpus import eval_pr_numbers

REPO = "leanprover-community/mathlib4"
DEFAULT_OUT = PROJECT_ROOT / "inputs" / "pr_review_v2" / "corpus" / "mathlib_review_comments.jsonl"
_PR_NUM_RE = re.compile(r"/pulls/(\d+)$")


def pr_number(comment: Dict[str, Any]) -> Optional[int]:
    m = _PR_NUM_RE.search(str(comment.get("pull_request_url") or ""))
    return int(m.group(1)) if m else None


def keep_comment(comment: Dict[str, Any]) -> bool:
    """A substantive maintainer comment on a .lean file."""
    login = (comment.get("user") or {}).get("login")
    if not login or is_bot(login):
        return False
    if (comment.get("author_association") or "").upper() not in MAINTAINER_ASSOCIATIONS:
        return False
    if not str(comment.get("path") or "").lower().endswith(".lean"):
        return False
    return bool(strip_trivial_tokens(comment.get("body")))


def corpus_row(comment: Dict[str, Any]) -> Dict[str, Any]:
    """A retrieval situation: the comment + the code it was anchored to."""
    return {
        "comment_id": comment.get("id"),
        "pr_number": pr_number(comment),
        "path": comment.get("path"),
        "line": comment.get("line") or comment.get("original_line"),
        "start_line": comment.get("start_line") or comment.get("original_start_line"),
        "diff_hunk": comment.get("diff_hunk") or "",
        "body": comment.get("body") or "",
        "commenter": (comment.get("user") or {}).get("login"),
        "author_association": comment.get("author_association"),
        "created_at": comment.get("created_at"),
        "in_reply_to_id": comment.get("in_reply_to_id"),
        "commit_id": comment.get("commit_id"),
        "html_url": comment.get("html_url"),
    }


def _existing_state(out: Path) -> Tuple[Set[Any], Optional[str]]:
    """Existing comment_ids + the max created_at already written (the resume frontier)."""
    if not out.exists():
        return set(), None
    ids: Set[Any] = set()
    max_created: Optional[str] = None
    for l in out.read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        ids.add(r.get("comment_id"))
        cc = r.get("created_at")
        if cc and (max_created is None or cc > max_created):
            max_created = cc
    return ids, max_created


def build_corpus(
    start: str, end: str, out: Path, *, exclude_prs: Set[int], max_pages: int, logger,
    interval: float = 0.0, progress_every: int = 500,
) -> int:
    """Walk review comments in created-ascending order, filtered server-side by `since` so we start
    at the window (not at the repo's whole history and not the newer eval region). Keep the window
    [start, end]; stop once created passes end. Returns #rows written this run.

    Ascending+`since` (vs newest-first) matters here: it starts near `start` so progress is visible
    immediately, and it never paginates the post-window eval region at all."""
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, max_created = _existing_state(out)
    if seen:
        # Always re-scan the whole window from `start` and dedup by comment_id. We deliberately do
        # NOT resume from max(created) as a frontier: an interrupted run (or an older newest-first
        # run) can leave a non-contiguous slice, so a created frontier would silently skip the gap.
        logger.info("Resume: %d existing rows (max created %s); re-scanning from %s, dedup by id",
                    len(seen), max_created or "-", start)
    since_iso = f"{start}T00:00:00Z"
    client = GitHubClient(None, request_interval_seconds=interval, logger=logger)
    if not client.authenticated:
        logger.warning("No GITHUB_TOKEN set — GitHub allows only 60 req/hr unauthenticated; "
                       "a full window needs hundreds of requests. Set GITHUB_TOKEN.")
    logger.info("Fetching review comments created %s..%s (since=%s), ascending", start, end, since_iso)
    kept = scanned = pre_window = 0
    fh = out.open("a", encoding="utf-8")
    try:
        for c in client.paginate(
            f"/repos/{REPO}/pulls/comments",
            params={"sort": "created", "direction": "asc", "since": since_iso},
            per_page=100, max_pages=max_pages,
        ):
            scanned += 1
            day = str(c.get("created_at") or "")[:10]
            if scanned % progress_every == 0:
                logger.info("  scanned %d, kept %d (at %s)", scanned, kept, day or "?")
            if not day:
                continue
            if day < start:          # updated-in-window but created before it → not yet in window
                pre_window += 1
                continue
            if day > end:            # created past the window (ascending → all rest are too) → done
                break
            cid = c.get("id")
            if cid in seen or pr_number(c) in exclude_prs or not keep_comment(c):
                continue
            fh.write(json.dumps(corpus_row(c), ensure_ascii=False) + "\n")
            fh.flush()
            seen.add(cid)
            kept += 1
    finally:
        fh.close()
        client.close()
    logger.info("Done: kept %d maintainer .lean comments this run (scanned %d, %d pre-window) -> %s",
                kept, scanned, pre_window, out)
    return kept


def _eval_pr_numbers() -> Set[int]:
    """Exclude the eval-set PRs outright (belt-and-suspenders; the date cutoff already
    excludes them). Defined in `mathlib_review.corpus`, which is where v5's index reads it
    from too -- it used to reach in here for it across a package boundary."""

    return eval_pr_numbers(
        PROJECT_ROOT / "inputs" / "pr_review_v2"
        / "mathlib_pr_review_v2_actionable_20260618.jsonl")


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 0: build the maintainer-comment precedent corpus")
    p.add_argument("--start", default="2024-03-01", help="YYYY-MM-DD (inclusive) — window start")
    p.add_argument("--end", default="2025-08-31", help="YYYY-MM-DD (inclusive) — window end; must be "
                   "before the eval window (2025-09-01..2025-12-31) to avoid leakage")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--max-pages", type=int, default=3000)
    p.add_argument("--interval", type=float, default=0.0, help="seconds between requests")
    args = p.parse_args()
    logger = create_logger()
    excl = _eval_pr_numbers()
    logger.info("Corpus window [%s .. %s], excluding %d eval PRs -> %s",
                args.start, args.end, len(excl), args.out)
    build_corpus(args.start, args.end, args.out, exclude_prs=excl,
                 max_pages=args.max_pages, logger=logger, interval=args.interval)


if __name__ == "__main__":
    main()
