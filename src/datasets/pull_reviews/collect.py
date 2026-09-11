"""Collect Mathlib PRs into the store, by tier, resumably, on the core quota.

    python -m src.datasets.pull_reviews.collect --start 2024-03-01 --end 2025-12-31          # tiers 0+1
    python -m src.datasets.pull_reviews.collect --start 2024-03-01 --end 2025-12-31 --tier 2 # then tier 2

**Tier 0** walks `/repos/{repo}/pulls?state=all&sort=updated&direction=desc` from the top until it
falls below the window, keeping every PR updated on or after the start and created on or before the
end, and records each listing row. That endpoint is on the 5,000/hour core bucket and answers in
about a second at any depth; the search API is capped at 30 requests a minute and the repo-level
comment listing times out on page 1, which is why neither is used.

**Tier 1** fetches the three conversation endpoints for every such PR -- inline review comments,
reviews, issue comments -- newest PR first. All three, because Mathlib review often lives in
review bodies and bors approvals rather than inline comments: a pre-gate that saw only inline
comments would have skipped 55 % of the PRs the funnel includes.

**The pre-gate** then decides which PRs get tier 2: closed or merged, a non-bot author, a
non-revert title, and at least one reviewer decision as the funnel itself counts them
(`episode_builder.has_reviewer_decision`, the same function the funnel calls). It prints how many
PRs pass and what tier 2 will cost before any of it is spent.

**Tier 2** fetches the PR object, commits, files, timeline, the GraphQL review threads and body-edit
history, and the compares the funnel asks for. Which compares is decided by running the funnel with
a source that records every head it requests, fetching those, and repeating until it asks for
nothing new -- so the collector never re-implements how a reviewed head is chosen.

The store is neutral: scored (eval) PRs are collected like any other, because the task side needs
them. Exclusion is a projection's job (`definitions.scored_pr_numbers`), not collection's.

Resumable at every point: an endpoint already recorded for a PR is never fetched again, and the
tier-0 PR list for a window is cached in `data/pull_reviews/collect.state.json`.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from src.datasets.pull_reviews.definitions import (
    REVERT_TITLE_RE, is_bot, load_roster, roster_sha256,
)
from src.datasets.pull_reviews.github import (
    GitHubClient, GitHubError, compact_compare, compare_bytes, fetch_body_edits,
    fetch_review_threads,
)
from src.datasets.pull_reviews.store import PullReviewStore, write_atomically
from src.mathlib_review.paths import PULL_REVIEWS_ROSTERS, PULL_REVIEWS_TRACKED, assert_repo_root

REPO = "leanprover-community/mathlib4"
OWNER, NAME = REPO.split("/")
COLLECTOR_VERSION = "pull-review-collector/1"

TIER1 = {
    "review_comments": "/repos/{repo}/pulls/{n}/comments",
    "reviews": "/repos/{repo}/pulls/{n}/reviews",
    "issue_comments": "/repos/{repo}/issues/{n}/comments",
}
TIER2_REST = {
    "pr": "/repos/{repo}/pulls/{n}",
    "commits": "/repos/{repo}/pulls/{n}/commits",
    "files": "/repos/{repo}/pulls/{n}/files",
    "timeline": "/repos/{repo}/issues/{n}/timeline",
}
TIER2_GRAPHQL: Dict[str, Callable] = {
    "review_threads": fetch_review_threads,
    "body_edits": fetch_body_edits,
}
#: Rough request cost of tier 2 per PR: four REST lists, two GraphQL calls, ~2 compares.
TIER2_REQUESTS_PER_PR = 8


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fmt_seconds(seconds: float) -> str:
    seconds = max(0.0, seconds)
    if seconds < 90:
        return f"{seconds:.0f}s"
    if seconds < 5400:
        return f"{seconds / 60:.0f}m"
    return f"{seconds / 3600:.1f}h"


def latest_roster() -> Path:
    snapshots = sorted(PULL_REVIEWS_ROSTERS.glob("mathlib_roster_*.txt"))
    if not snapshots:
        raise FileNotFoundError(f"no dated roster under {PULL_REVIEWS_ROSTERS}; run "
                                "`python -m src.datasets.pull_reviews.roster`")
    return snapshots[-1]


# --- tier 0 --------------------------------------------------------------------------------------

def walk_listing(client, start: str, end: str, logger: logging.Logger, *,
                 log_every_pages: int = 10, recheck_pages: int = 3) -> Dict[int, Dict[str, Any]]:
    """Every PR updated on or after `start` and created on or before `end`, as its listing row.

    Ordered by `updated_at` descending, so the walk stops at the first page that has fallen below
    the window. An update moves a PR *up*: one above the cursor is only re-read, but one bumped from
    below the cursor to the top would be stepped over, so the first `recheck_pages` are read again.
    """

    path = f"/repos/{REPO}/pulls"
    params = {"state": "all", "sort": "updated", "direction": "desc"}
    found: Dict[int, Dict[str, Any]] = {}

    def keep(item: Dict[str, Any]) -> None:
        number, updated, created = item.get("number"), item.get("updated_at") or "", item.get("created_at") or ""
        if number and updated[:10] >= start and created[:10] <= end:
            found.setdefault(int(number), item)

    pages, reached, t0 = 0, "", time.monotonic()
    for page in client.pages(path, params=params, per_page=100, max_pages=None):
        pages += 1
        if not page:
            break
        for item in page:
            reached = (item.get("updated_at") or "")[:10] or reached
            keep(item)
        below = (page[-1].get("updated_at") or "")[:10] < start
        if pages % max(1, log_every_pages) == 0 or below:
            logger.info("  tier 0 page %d | back to %s (window starts %s) | %d PRs in window | %.1f req/s",
                        pages, reached or "?", start, len(found), pages / max(1e-6, time.monotonic() - t0))
        if below:
            break
    before = set(found)
    for page in client.pages(path, params=params, per_page=100, max_pages=recheck_pages):
        for item in page:
            keep(item)
    if set(found) - before:
        logger.info("  tier 0 re-check found %d PR(s) bumped during the walk: %s",
                    len(set(found) - before), sorted(set(found) - before))
    return found


# --- the pre-gate ---------------------------------------------------------------------------------

def pre_gate(store: PullReviewStore, number: int, roster) -> Tuple[bool, str]:
    """Whether a PR is worth tier 2, from tier 0 and 1 alone. The changed-files and size gates need
    tier 2 and stay in the funnel; this only drops what the funnel certainly would."""

    from src.mathlib_review.release.episode_builder import has_reviewer_decision

    endpoints = store.ledger(number)["endpoints"]
    pr = store.read(number, "listing") if endpoints.get("listing", {}).get("present") else \
        store.read(number, "pr") if endpoints.get("pr", {}).get("present") else None
    if pr is None:
        return False, "no_listing"
    if not (pr.get("merged_at") or str(pr.get("state") or "").lower() == "closed"):
        return False, "still_open"
    if is_bot((pr.get("user") or {}).get("login")):
        return False, "bot_author"
    if REVERT_TITLE_RE.search(str(pr.get("title") or "")):
        return False, "revert"
    if not all(name in endpoints for name in TIER1):
        return False, "tier1_incomplete"
    partial = {"pr": pr, **{name: store.read(number, name) for name in TIER1}}
    if not has_reviewer_decision(partial, roster=roster):
        return False, "no_reviewer_decision"
    return True, "pass"


# --- collection ----------------------------------------------------------------------------------

class Collector:
    def __init__(self, store: PullReviewStore, client, logger: logging.Logger, *,
                 roster_path: Path, state_path: Optional[Path] = None, log_every_prs: int = 25):
        self.store = store
        self.client = client
        self.logger = logger
        self.roster_path = Path(roster_path)
        self.roster = load_roster(self.roster_path)
        self.state_path = state_path or store.root / "collect.state.json"
        self.log_every_prs = log_every_prs
        self.requests = 0

    # state: the tier-0 PR list per window, so a resume never re-walks
    def _state(self) -> Dict[str, Any]:
        if self.state_path.is_file():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"collector_version": COLLECTOR_VERSION, "windows": {}}

    def _save_state(self, state: Dict[str, Any]) -> None:
        write_atomically(self.state_path, (json.dumps(state, indent=1, sort_keys=True) + "\n").encode())

    def window_prs(self, start: str, end: str) -> List[int]:
        """Tier 0 for a window: walked once, cached, every listing row recorded."""

        key = f"{start}..{end}"
        state = self._state()
        cached = state["windows"].get(key)
        if cached and cached.get("complete"):
            return cached["prs"]
        rows = walk_listing(self.client, start, end, self.logger)
        fetched_at = _now()
        for number, row in rows.items():
            self.store.write_endpoint(number, "listing", row, request=f"/repos/{REPO}/pulls#listing",
                                      fetched_at=fetched_at, source="github")
        prs = sorted(rows)
        state["windows"][key] = {"prs": prs, "complete": True, "walked_at": fetched_at}
        self._save_state(state)
        return prs

    def _progress(self, label: str, index: int, total: int, number: int, t0: float, done: int) -> None:
        elapsed = max(1e-6, time.monotonic() - t0)
        rate = done / elapsed
        left = total - index
        self.logger.info("  %s PR %d/%d (%3.0f%%) | #%d | %d requests | %.1f PR/s | ~%s left", label,
                         index, total, 100 * index / max(1, total), number, self.requests, rate,
                         _fmt_seconds(left / rate) if rate else "?")

    def tier1(self, prs: Iterable[int]) -> Dict[str, int]:
        todo = sorted((n for n in prs if not all(
            name in self.store.ledger(n)["endpoints"] for name in TIER1)), reverse=True)
        self.logger.info("  tier 1: %d PRs to read, newest first (~%d requests, ~%s at the core limit)",
                         len(todo), 3 * len(todo), _fmt_seconds(3 * len(todo) / 1.39))
        t0, rows = time.monotonic(), 0
        for index, number in enumerate(todo, start=1):
            for name, template in TIER1.items():
                if name in self.store.ledger(number)["endpoints"]:
                    continue
                payload = self.client.paginate_all(template.format(repo=REPO, n=number), max_pages=None)
                self.requests += max(1, (len(payload) + 99) // 100)
                rows += len(payload)
                self.store.write_endpoint(number, name, payload,
                                          request=template.format(repo=REPO, n=number),
                                          fetched_at=_now(), source="github")
            if index % max(1, self.log_every_prs) == 0 or index == len(todo):
                self._progress("tier 1", index, len(todo), number, t0, index)
        return {"prs_read": len(todo), "rows": rows}

    def gate_report(self, prs: Iterable[int]) -> Dict[str, Any]:
        reasons: Dict[str, int] = {}
        passing: List[int] = []
        for number in prs:
            ok, reason = pre_gate(self.store, number, self.roster)
            reasons[reason] = reasons.get(reason, 0) + 1
            if ok:
                passing.append(number)
        need = [n for n in passing if 2 not in self.store.tiers(n)]
        report = {"prs": sum(reasons.values()), "passing": len(passing), "by_reason": reasons,
                  "tier2_needed": len(need),
                  "tier2_request_estimate": TIER2_REQUESTS_PER_PR * len(need),
                  "tier2_hours_estimate": round(TIER2_REQUESTS_PER_PR * len(need) / 5000, 1)}
        self.logger.info("  pre-gate: %d of %d PRs pass (%s); tier 2 needed for %d -> ~%d requests, "
                         "~%.1f h of core quota", report["passing"], report["prs"],
                         ", ".join(f"{k} {v}" for k, v in sorted(reasons.items())),
                         report["tier2_needed"], report["tier2_request_estimate"],
                         report["tier2_hours_estimate"])
        return {**report, "passing_prs": passing}

    def tier2(self, prs: Iterable[int]) -> Dict[str, int]:
        if not getattr(self.client, "authenticated", False):
            raise PermissionError(
                "tier 2 needs GITHUB_TOKEN: review threads and body-edit history come from GraphQL, "
                "and without them every description would be recorded as possibly post-edited")
        todo = sorted((n for n in prs if 2 not in self.store.tiers(n)), reverse=True)
        self.logger.info("  tier 2: %d PRs, newest first", len(todo))
        t0, compares = time.monotonic(), 0
        for index, number in enumerate(todo, start=1):
            endpoints = self.store.ledger(number)["endpoints"]
            for name, template in TIER2_REST.items():
                if name in endpoints:
                    continue
                path = template.format(repo=REPO, n=number)
                payload = self.client.get_json(path) if name == "pr" else \
                    self.client.paginate_all(path, max_pages=None)
                self.requests += 1
                self.store.write_endpoint(number, name, payload, request=path, fetched_at=_now(),
                                          source="github")
            for name, fetch in TIER2_GRAPHQL.items():
                if endpoints.get(name, {}).get("present"):
                    continue
                try:
                    payload = fetch(self.client, OWNER, NAME, number)
                except GitHubError as exc:
                    self.logger.warning("  #%d %s: GraphQL failed (%s); recorded as null, fillable "
                                        "by a later run", number, name, exc)
                    payload = None
                self.requests += 1
                self.store.write_endpoint(number, name, payload, request=f"graphql:{name}",
                                          fetched_at=_now(), source="github")
            compares += self.fetch_compares(number)
            if index % max(1, self.log_every_prs) == 0 or index == len(todo):
                self._progress("tier 2", index, len(todo), number, t0, index)
        return {"prs_read": len(todo), "compares_fetched": compares}

    def fetch_compares(self, number: int, *, max_rounds: int = 12) -> int:
        """Fetch every compare the funnel asks for, by asking it: run the multi-round builder with
        a source that records requested heads, fetch the missing ones, repeat until none are new.
        Plus the PR's final head, which the delta between review and merge is measured against."""

        from src.mathlib_review.release.episode_builder import segment_review_rounds

        fetched = 0
        final_head = str(((self.store.read(number, "pr") or {}).get("head") or {}).get("sha") or "")
        wanted = {final_head} if final_head else set()
        for _ in range(max_rounds):
            recorder = _RecordingCompares(self.store, number)
            segment_review_rounds(self.store.load_bundle(number),
                                  bundle_sha256=self.store.bundle_sha256(number),
                                  compares=recorder, roster=set(self.roster))
            wanted |= set(recorder.requested)
            missing = sorted(h for h in wanted if h not in self.store.ledger(number)["compares"])
            if not missing:
                break
            for head in missing:
                path = f"/repos/{REPO}/compare/master...{head}"
                try:
                    payload = self.client.get_json(path, params={"per_page": 100})
                except GitHubError as exc:
                    self.logger.warning("  #%d compare %s failed: %s", number, head[:12], exc)
                    wanted.discard(head)
                    continue
                self.requests += 1
                self.store.write_compare(number, head, compare_bytes(compact_compare(payload)),
                                         base_ref="master", request=path, fetched_at=_now(),
                                         source="github")
                fetched += 1
        return fetched


class _RecordingCompares:
    """A compare source that notes every head the funnel asks for, then answers from the store."""

    def __init__(self, store: PullReviewStore, number: int):
        self.inner = store.compares(number)
        self.requested: List[str] = []

    def review_diff(self, reviewed_head_sha: str):
        self.requested.append(reviewed_head_sha)
        return self.inner.review_diff(reviewed_head_sha)


def _append_report(entry: Dict[str, Any], tracked: Path = PULL_REVIEWS_TRACKED) -> None:
    path = tracked / "collection_report.json"
    history = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"runs": []}
    history["runs"].append(entry)
    write_atomically(path, (json.dumps(history, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def main() -> None:
    from ape.utils.logging import create_logger
    from src.datasets.pull_reviews.index import write_tracked_export

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--tier", type=int, choices=[1, 2], default=1,
                        help="1: walk the window and fetch conversations (then report the pre-gate); "
                             "2: fetch tier 2 for PRs passing the pre-gate")
    parser.add_argument("--roster", type=Path, default=None, help="default: the latest dated roster")
    parser.add_argument("--store", type=Path, default=None)
    args = parser.parse_args()
    assert_repo_root()
    logger = create_logger()
    store = PullReviewStore(args.store) if args.store else PullReviewStore()
    roster_path = args.roster or latest_roster()
    client = GitHubClient(None, logger=logger)
    collector = Collector(store, client, logger, roster_path=roster_path)
    logger.info("PLAN  window %s..%s | tier %d | store %s (%d PRs already) | roster %s | "
                "GITHUB_TOKEN %s", args.start, args.end, args.tier, store.root, len(store.numbers()),
                roster_path.name, "set" if client.authenticated else "MISSING (60 requests/hour)")
    started = _now()
    try:
        prs = collector.window_prs(args.start, args.end)
        logger.info("  tier 0: %d PRs in the window", len(prs))
        if args.tier == 1:
            result = collector.tier1(prs)
            gate = collector.gate_report(prs)
        else:
            gate = collector.gate_report(prs)
            result = collector.tier2(gate["passing_prs"])
    finally:
        client.close()
    manifest = write_tracked_export(store)
    _append_report({"collector_version": COLLECTOR_VERSION, "window": [args.start, args.end],
                    "tier": args.tier, "started_at": started, "finished_at": _now(),
                    "requests": collector.requests, "result": result,
                    "pre_gate": {k: v for k, v in gate.items() if k != "passing_prs"},
                    "roster": {"path": str(roster_path), "sha256": roster_sha256(roster_path)},
                    "store_content_sha256": manifest["content_sha256"]})
    logger.info("DONE  %s | store now %d PRs | report appended to %s/collection_report.json",
                json.dumps(result), manifest["prs"], PULL_REVIEWS_TRACKED)
    if args.tier == 1:
        logger.info("NEXT  %d PRs pass the pre-gate; tier 2 for %d of them costs ~%d requests "
                    "(~%.1f h). Run with --tier 2.", gate["passing"], gate["tier2_needed"],
                    gate["tier2_request_estimate"], gate["tier2_hours_estimate"])


if __name__ == "__main__":
    main()
