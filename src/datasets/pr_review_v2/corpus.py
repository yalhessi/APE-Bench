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
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

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
        # Where in the hunk the comment sits. `original_position` is 1-based over the hunk's
        # lines after the `@@` header and is stable across force-pushes, unlike `position`.
        # Without it a comment can only be attached to *some* declaration in its hunk -- and
        # measured on a hand-read 50, that was the right declaration 27 times. With it the
        # declaration enclosing the commented line resolves 9/9 on PR 33098. The precedent
        # corpus was built without these fields; every row here now carries them.
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


#: GitHub's `/pulls/comments` listing answers 5xx once a `next`-link chain runs deep (a 21-month
#: window is ~2,000 pages; the user's run died there). The walk is created-ascending, so every
#: `REANCHOR_EVERY_PAGES` pages the query is restarted with `since` = the last created_at seen.
#: `since` filters on updated_at, and updated ≥ created, so nothing created later is skipped;
#: comments created in the anchor's own second are re-fetched and dropped by the id dedup.
REANCHOR_EVERY_PAGES = 10


def _day(iso: str) -> date:
    return date.fromisoformat(iso[:10])


def _window_fraction(day: str, start: str, end: str) -> float:
    """How far through [start, end] a created date is: the only progress GitHub lets us compute,
    since the endpoint carries no total."""
    span = max(1, (_day(end) - _day(start)).days + 1)
    done = (_day(day) - _day(start)).days + 1
    return min(1.0, max(0.0, done / span))


def _fmt_seconds(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


def _state_path(out: Path) -> Path:
    return out.with_name(out.name + ".state.json")


def build_corpus(
    start: str, end: str, out: Path, *, exclude_prs: Set[int], max_pages: int, logger,
    interval: float = 0.0, log_every_pages: int = 5,
    reanchor_every_pages: int = REANCHOR_EVERY_PAGES, client: Optional[GitHubClient] = None,
) -> int:
    """Walk review comments in created-ascending order through [start, end], appending the
    maintainer `.lean` comments not already in `out`. Returns the number of rows written.

    The walk is server-filtered by `since` so it begins near `start` and never touches the
    post-window region; it stops at the first comment created after `end`. It is re-anchored
    every `reanchor_every_pages` pages (see `REANCHOR_EVERY_PAGES`). Progress is logged as the
    share of the date window reached, with a page estimate derived from it; a state file beside
    `out` records the created-at frontier after every page so an interrupted run can be resumed
    with `--start <frontier day>` — everything before the frontier was walked contiguously.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    seen, max_created = _existing_state(out)
    client = client or GitHubClient(None, request_interval_seconds=interval, logger=logger)
    logger.info(
        "PLAN  window %s..%s | %d rows already in %s (latest created %s) | GITHUB_TOKEN %s\n"
        "      walk /pulls/comments created-ascending, 100 per page, re-anchoring `since` every "
        "%d pages so no page is deep; keep maintainer .lean comments not already present; "
        "stop at the first comment created after %s. GitHub reports no total, so progress is "
        "the share of the date window reached and the page estimate is derived from it.",
        start, end, len(seen), out.name, max_created or "-",
        "set" if client.authenticated else "MISSING (60 requests/hour; this will not finish)",
        reanchor_every_pages, end)
    if seen and max_created and max_created[:10] < start:
        logger.info("      existing rows end %s, before this window: nothing is re-scanned.",
                    max_created[:10])
    elif seen:
        logger.info("      re-scanning from %s and deduplicating by comment id "
                    "(an earlier interrupted run may have left a gap, so no frontier is assumed).",
                    start)

    since = f"{start}T00:00:00Z"
    kept = scanned = pre_window = requests = 0
    last_created: Optional[str] = None
    t0 = time.monotonic()
    done = False
    fh = out.open("a", encoding="utf-8")

    def progress(final: bool = False) -> None:
        elapsed = max(1e-6, time.monotonic() - t0)
        rate = requests / elapsed
        if last_created:
            frac = _window_fraction(last_created, start, end)
            est_total = requests / frac if frac > 0 else float("inf")
            left = max(0.0, est_total - requests)
            where = f"at {last_created[:10]} ({100 * frac:4.1f}% of window)"
            eta = f"~{left:.0f} pages left (~{_fmt_seconds(left / rate if rate else 0)})"
        else:
            where, eta = "before the window (older comments edited recently)", "no estimate yet"
        logger.info("%s page %d | %s | scanned %s kept %s | %.1f req/s | %s",
                    "DONE " if final else "     ", requests, where,
                    f"{scanned:,}", f"{kept:,}", rate, eta)

    def save_state() -> None:
        _state_path(out).write_text(json.dumps({
            "start": start, "end": end, "frontier_created_at": last_created,
            "requests": requests, "scanned": scanned, "kept": kept, "done": done,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "resume_hint": (f"--start {last_created[:10]} --end {end}" if last_created else
                            f"--start {start} --end {end}"),
        }, indent=2) + "\n", encoding="utf-8")

    try:
        while not done and requests < max_pages:
            anchor_created = last_created
            pages_this_anchor = 0
            for page in client.pages(
                f"/repos/{REPO}/pulls/comments",
                params={"sort": "created", "direction": "asc", "since": since},
                per_page=100, max_pages=None,
            ):
                requests += 1
                pages_this_anchor += 1
                for c in page:
                    scanned += 1
                    created = str(c.get("created_at") or "")
                    day = created[:10]
                    if not day:
                        continue
                    if day < start:          # updated in the window, created before it
                        pre_window += 1
                        continue
                    if day > end:            # ascending: everything after this is past the window
                        done = True
                        break
                    last_created = created
                    cid = c.get("id")
                    if cid in seen or pr_number(c) in exclude_prs or not keep_comment(c):
                        continue
                    fh.write(json.dumps(corpus_row(c), ensure_ascii=False) + "\n")
                    fh.flush()
                    seen.add(cid)
                    kept += 1
                save_state()
                if requests % max(1, log_every_pages) == 0:
                    progress()
                if done or requests >= max_pages:
                    break
                # Re-anchor once this chain is `reanchor_every_pages` deep -- but only if the
                # frontier moved, otherwise the chain is still in pre-window comments and a
                # re-anchor at the same `since` would loop forever.
                if pages_this_anchor >= reanchor_every_pages and last_created != anchor_created:
                    break
            else:
                done = True                  # the chain ended: no `next` link, nothing more exists
            if not done and requests < max_pages and last_created:
                since = last_created
        if requests >= max_pages and not done:
            logger.warning("Stopped at --max-pages %d before reaching %s; resume with %s",
                           max_pages, end, json.loads(_state_path(out).read_text())["resume_hint"])
    except BaseException:
        save_state()
        logger.error("Interrupted after %d pages at %s; %d rows were written and are kept. "
                     "Resume with: %s", requests, (last_created or "-")[:10], kept,
                     json.loads(_state_path(out).read_text())["resume_hint"])
        raise
    finally:
        fh.close()
        client.close()
    save_state()
    progress(final=True)
    logger.info("Kept %d maintainer .lean comments this run (scanned %d, %d created before the "
                "window) -> %s", kept, scanned, pre_window, out)
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
    p.add_argument("--end", default="2025-08-31", help="YYYY-MM-DD (inclusive) — window end. "
                   "The window MAY now extend into the eval period: leakage is prevented at READ "
                   "time, where the precedent index gates every row at the consuming PR's own "
                   "base-commit date (RetrievalGate on created_epoch), and the eval PRs' own "
                   "comments are excluded here regardless of window. A December PR reading a "
                   "corpus that runs to November sees September-November discussion and nothing "
                   "after its base -- which is exactly the evidence the review-corpus window "
                   "ending in August could not supply.")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--max-pages", type=int, default=3000, help="hard cap on requests this run")
    p.add_argument("--interval", type=float, default=0.0, help="seconds between requests")
    p.add_argument("--log-every-pages", type=int, default=5,
                   help="print a progress line every N pages (one page = one request of 100)")
    p.add_argument("--reanchor-every-pages", type=int, default=REANCHOR_EVERY_PAGES,
                   help="restart the walk from the last created_at every N pages (GitHub 5xxs deep chains)")
    args = p.parse_args()
    logger = create_logger()
    excl = _eval_pr_numbers()
    logger.info("Corpus window [%s .. %s], excluding %d eval PRs -> %s",
                args.start, args.end, len(excl), args.out)
    build_corpus(args.start, args.end, args.out, exclude_prs=excl,
                 max_pages=args.max_pages, logger=logger, interval=args.interval,
                 log_every_pages=args.log_every_pages,
                 reanchor_every_pages=args.reanchor_every_pages)


if __name__ == "__main__":
    main()
