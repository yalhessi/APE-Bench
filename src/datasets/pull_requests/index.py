"""A queryable index over the PR store, and the tracked record that survives the store being wiped.

**The index is a cache.** `index.sqlite3` is rebuilt from the per-PR directories by one command and
is never the source of truth: a corrupt or stale index loses nothing. It pins the store's
`content_digest`, and `open_index` refuses an index built from a different store -- the precedent
index was found silently out of date with its corpus (36,695 rows indexed, 43,874 on disk), and
this is the check that would have caught it.

**It records facts, not policy.** Who wrote a comment, whether that login authored the PR, whether
the body carries a GitHub suggestion block: facts from the payloads. Whether the commenter is a
*reviewer* depends on a roster snapshot and on spec §3.1, so it is decided in projections through
`definitions.classify_commenter`, never frozen into the cache.

**What is tracked.** `data/` is gitignored, and the retrieval corpus vanished from a checkout once
already. So, following the Zulip store's "pin provenance, not bytes": `inputs/pull_requests/
manifest.json` (the store's digest, tier counts, sources) and `prs.jsonl` (one compact row per PR:
tiers, row counts, per-PR digest). A wiped store is then a resumable refetch of a known PR list
whose every PR can be checked against the digest it had.

    python -m src.datasets.pull_requests.index build
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from src.datasets.pull_requests.definitions import DEFINITIONS_VERSION
from src.datasets.pull_requests.store import (
    ENDPOINTS, STORE_VERSION, PullRequestStore, write_atomically,
)
from src.mathlib_review.io import canonical_json_bytes, git_state, sha256_bytes
from src.mathlib_review.paths import PULL_REQUESTS_TRACKED, assert_repo_root

INDEX_VERSION = "pull-request-index/1"
EXPORT_VERSION = "pull-request-export/1"
UNDATED = -1

SUGGESTION = re.compile(r"```suggestion\b")

_SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE prs (
    number INTEGER PRIMARY KEY, state TEXT, draft INTEGER, title TEXT, author TEXT,
    author_association TEXT, created_at TEXT, updated_at TEXT, closed_at TEXT, merged_at TEXT,
    base_ref TEXT, base_sha TEXT, head_sha TEXT, head_repo TEXT, labels TEXT,
    tiers TEXT NOT NULL, has_listing INTEGER NOT NULL, legacy_bundle_sha256 TEXT
);
CREATE TABLE comments (
    kind TEXT NOT NULL, id INTEGER NOT NULL, pr_number INTEGER NOT NULL, author TEXT,
    author_association TEXT, is_pr_author INTEGER NOT NULL, created_at TEXT,
    created_epoch INTEGER NOT NULL, state TEXT, path TEXT, line INTEGER, original_line INTEGER,
    original_position INTEGER, start_line INTEGER, original_start_line INTEGER, side TEXT,
    subject_type TEXT, in_reply_to_id INTEGER, commit_id TEXT, has_suggestion INTEGER NOT NULL,
    body TEXT, diff_hunk TEXT, PRIMARY KEY (kind, id)
);
CREATE INDEX comments_pr ON comments (pr_number);
CREATE INDEX comments_time ON comments (created_epoch);
CREATE INDEX comments_author ON comments (author);
CREATE TABLE fetches (
    pr_number INTEGER NOT NULL, endpoint TEXT NOT NULL, tier INTEGER, present INTEGER NOT NULL,
    rows INTEGER, sha256 TEXT, fetched_at TEXT, source TEXT, PRIMARY KEY (pr_number, endpoint)
);
"""

#: The three conversation endpoints, as they appear in `comments.kind`.
COMMENT_KINDS = (("review_comments", "review_comment"), ("reviews", "review"),
                 ("issue_comments", "issue_comment"))


class StaleIndex(RuntimeError):
    """The index was built from a store that has since changed."""


def _epoch(stamp: Optional[str]) -> int:
    from src.mathlib_review.retrieval_gate import RetrievalGate, UngatedTimestamp

    if not stamp:
        return UNDATED
    try:
        return int(RetrievalGate().epoch_of(stamp, field="created_at"))
    except UngatedTimestamp:
        return UNDATED


def _pr_facts(store: PullRequestStore, number: int) -> Dict[str, Any]:
    """PR-level fields from the listing row when there is one, else from `pr.json`. The two are
    the same GitHub object at different endpoints; seeded PRs have only the latter."""

    endpoints = store.ledger(number)["endpoints"]
    source = None
    for name in ("listing", "pr"):
        if endpoints.get(name, {}).get("present"):
            source = store.read(number, name)
            break
    return source or {}


def _comment_rows(store: PullRequestStore, number: int, pr_author: str) -> Iterator[Tuple]:
    endpoints = store.ledger(number)["endpoints"]
    for endpoint, kind in COMMENT_KINDS:
        if not endpoints.get(endpoint, {}).get("present"):
            continue
        for item in store.read(number, endpoint) or []:
            author = (item.get("user") or {}).get("login")
            created = item.get("created_at") or item.get("submitted_at")
            body = item.get("body") or ""
            yield (kind, int(item["id"]), number, author, item.get("author_association"),
                   int(bool(author) and author.lower() == pr_author.lower()), created,
                   _epoch(created), item.get("state"), item.get("path"), item.get("line"),
                   item.get("original_line"), item.get("original_position"),
                   item.get("start_line"), item.get("original_start_line"), item.get("side"),
                   item.get("subject_type"), item.get("in_reply_to_id"), item.get("commit_id"),
                   int(bool(SUGGESTION.search(body))), body, item.get("diff_hunk"))


def build_index(store: PullRequestStore, out: Optional[Path] = None) -> Dict[str, Any]:
    """Rebuild the index from the tree, atomically. Returns a summary including the index's own
    content digest, which is identical for identical stores."""

    out = Path(out) if out else store.root / "index.sqlite3"
    out.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=out.parent, prefix=".index.", suffix=".sqlite3")
    os.close(handle)
    try:
        con = sqlite3.connect(tmp)
        con.executescript(_SCHEMA)
        counts = collections.Counter()
        for number in store.numbers():
            ledger = store.ledger(number)
            pr = _pr_facts(store, number)
            author = str((pr.get("user") or {}).get("login") or "")
            con.execute("INSERT INTO prs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                number, pr.get("state"), int(bool(pr.get("draft"))), pr.get("title"), author,
                pr.get("author_association"), pr.get("created_at"), pr.get("updated_at"),
                pr.get("closed_at"), pr.get("merged_at"), (pr.get("base") or {}).get("ref"),
                (pr.get("base") or {}).get("sha"), (pr.get("head") or {}).get("sha"),
                ((pr.get("head") or {}).get("repo") or {}).get("full_name"),
                json.dumps(sorted(l.get("name", "") for l in pr.get("labels") or [])),
                ",".join(str(t) for t in sorted(store.tiers(number))),
                int("listing" in ledger["endpoints"]),
                (ledger.get("legacy_bundle") or {}).get("sha256")))
            for row in _comment_rows(store, number, author):
                con.execute(f"INSERT INTO comments VALUES ({','.join('?' * 22)})", row)
                counts[row[0]] += 1
            for endpoint, entry in sorted(ledger["endpoints"].items()):
                con.execute("INSERT INTO fetches VALUES (?,?,?,?,?,?,?,?)", (
                    number, endpoint, entry["tier"], int(entry["present"]), entry["rows"],
                    entry["sha256"], entry.get("fetched_at"), entry.get("source")))
            for head, entry in sorted(ledger["compares"].items()):
                con.execute("INSERT INTO fetches VALUES (?,?,?,?,?,?,?,?)", (
                    number, f"compare:{head}", 2, 1, 1, entry["sha256"],
                    entry.get("fetched_at"), entry.get("source")))
            counts["prs"] += 1
        digest = store.content_digest()
        con.executemany("INSERT INTO meta VALUES (?,?)", [
            ("index_version", INDEX_VERSION), ("store_content_sha256", digest),
            ("store_version", STORE_VERSION),
        ])
        con.commit()
        content = index_content_sha256(con)
        con.close()
        os.replace(tmp, out)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return {"index": str(out), "index_version": INDEX_VERSION, "store_content_sha256": digest,
            "index_content_sha256": content, "prs": counts["prs"],
            "comments": {kind: counts[kind] for _, kind in COMMENT_KINDS}}


def index_content_sha256(con: sqlite3.Connection) -> str:
    """Digest of the index's rows in a fixed order -- the determinism check. Not the file's
    bytes: sqlite page layout is not a promise, the rows are."""

    parts = []
    for table, order in (("meta", "key"), ("prs", "number"), ("comments", "kind, id"),
                         ("fetches", "pr_number, endpoint")):
        parts.append([list(r) for r in con.execute(f"SELECT * FROM {table} ORDER BY {order}")])
    return sha256_bytes(canonical_json_bytes(parts))


def open_index(store: PullRequestStore, path: Optional[Path] = None) -> sqlite3.Connection:
    """A read-only connection, refused if the index was built from a different store."""

    path = Path(path) if path else store.root / "index.sqlite3"
    if not path.is_file():
        raise FileNotFoundError(f"no index at {path}; build it with "
                                "`python -m src.datasets.pull_requests.index build`")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    pinned = dict(con.execute("SELECT key, value FROM meta"))
    current = store.content_digest()
    if pinned.get("store_content_sha256") != current:
        con.close()
        raise StaleIndex(
            f"index {path} was built from store {pinned.get('store_content_sha256', '?')[:12]}, "
            f"the store is now {current[:12]}; rebuild it rather than read stale rows")
    return con


# --- tracked provenance -----------------------------------------------------------------------

def store_manifest(store: PullRequestStore) -> Dict[str, Any]:
    tiers = collections.Counter()
    sources = collections.Counter()
    rows = collections.Counter()
    compares = 0
    for ledger in store.iter_ledgers():
        recorded = set(ledger["endpoints"])
        for tier in (0, 1, 2):
            if {n for n, (t, _, _) in ENDPOINTS.items() if t == tier} <= recorded:
                tiers[str(tier)] += 1
        for name, entry in ledger["endpoints"].items():
            sources[entry.get("source") or "unknown"] += 1
            rows[name] += entry["rows"] or 0
        compares += len(ledger["compares"])
    commit, tree_state = git_state()
    return {
        "schema_version": STORE_VERSION, "content_sha256": store.content_digest(),
        "prs": len(store.numbers()), "prs_by_complete_tier": dict(sorted(tiers.items())),
        "endpoint_sources": dict(sorted(sources.items())), "rows_by_endpoint": dict(sorted(rows.items())),
        "compares": compares, "definitions_version": DEFINITIONS_VERSION,
        "generator_git_commit": commit, "generator_tree_state": tree_state,
    }


def pr_export_rows(store: PullRequestStore) -> List[Dict[str, Any]]:
    out = []
    for ledger in store.iter_ledgers():
        number = ledger["pr_number"]
        digest = sha256_bytes(canonical_json_bytes({
            "endpoints": {k: v["sha256"] for k, v in sorted(ledger["endpoints"].items())},
            "compares": {k: v["sha256"] for k, v in sorted(ledger["compares"].items())}}))
        out.append({
            "pr_number": number, "tiers": sorted(store.tiers(number)), "digest": digest,
            "rows": {k: v["rows"] for k, v in sorted(ledger["endpoints"].items())},
            "compares": len(ledger["compares"]),
            "sources": sorted({v.get("source") for v in ledger["endpoints"].values()}),
        })
    return out


def write_tracked_export(store: PullRequestStore, tracked: Path = PULL_REQUESTS_TRACKED) -> Dict[str, Any]:
    manifest = store_manifest(store)
    manifest["exported_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest["export_version"] = EXPORT_VERSION
    rows = pr_export_rows(store)
    write_atomically(tracked / "prs.jsonl",
                     b"".join(canonical_json_bytes(r) + b"\n" for r in rows))
    write_atomically(store.root / "manifest.json",
                     (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    write_atomically(tracked / "manifest.json",
                     (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--store", type=Path, default=None)
    args = parser.parse_args()
    assert_repo_root()
    store = PullRequestStore(args.store) if args.store else PullRequestStore()
    summary = build_index(store)
    manifest = write_tracked_export(store)
    print(json.dumps({"index": summary, "manifest": {k: manifest[k] for k in (
        "content_sha256", "prs", "prs_by_complete_tier", "endpoint_sources", "compares")}},
        indent=2))


if __name__ == "__main__":
    main()
