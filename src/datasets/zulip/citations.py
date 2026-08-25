"""
Which Zulip threads do Mathlib maintainers cite when reviewing?

A maintainer who links a Zulip thread in a review comment is telling us, in their own
words, what evidence justified the ask. That makes each citation a labelled pair —
(review ask, the discussion the reviewer treated as authoritative) — and there are
enough of them to matter: the reporting rule in `pr-review-v5-principled-design.md` §D6
only permits effect-size claims where a single flipped verdict is under ~3pp, i.e.
n ≳ 34, and the obligation-level denominators this project usually works with are 8-40.

This module is deliberately the *only* one in the package that reads an earlier
pipeline generation's data, and nothing in the core store imports it, so the store
itself stays free of generation edges.

Usage:
  python -m src.datasets.zulip.citations [--out inputs/zulip/review_citations.jsonl]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Set

from ape.utils.project import PROJECT_ROOT

from .config import ZulipConfig
from .io import canonical_json_bytes, jsonl_bytes, write_bytes
from .store import ZulipStore, parse_narrow_url

#: The v2 corpus of historical Mathlib review comments (34.6k rows).
REVIEW_COMMENTS = PROJECT_ROOT / "inputs" / "pr_review_v2" / "corpus" / "mathlib_review_comments.jsonl"

ZULIP_LINK = re.compile(r"https://leanprover\.zulipchat\.com/[^\s\)\]\">]+")
#: Trailing punctuation swept up by the URL pattern when a link ends a sentence.
_TRAILING = ".,;:!?'\""

MAINTAINER_ASSOCIATIONS = {"MEMBER", "OWNER", "COLLABORATOR"}


def iter_citations(path: Path = REVIEW_COMMENTS) -> Iterator[Dict]:
    """Yield one record per (review comment, Zulip link) pair."""
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            body = row.get("body") or ""
            for raw in ZULIP_LINK.findall(body):
                url = raw.rstrip(_TRAILING)
                stream_id, topic, anchor = parse_narrow_url(url)
                yield {
                    "comment_id": row.get("comment_id"),
                    "pr_number": row.get("pr_number"),
                    "path": row.get("path"),
                    "line": row.get("line"),
                    "commenter": row.get("commenter"),
                    "author_association": row.get("author_association"),
                    "created_at": row.get("created_at"),
                    "html_url": row.get("html_url"),
                    "body": body,
                    "zulip_url": url,
                    "stream_id": stream_id,
                    "topic": topic,
                    "anchor_message_id": anchor,
                }


def _unresolved_reason(citation: Dict, ingested_stream_ids: Set[int]) -> str:
    """Why a citation did not resolve. Distinguishing these matters: 'we chose not to
    ingest that stream' is a config decision, while 'that stream is ingested and the
    thread still is not here' is the build window, and only the second is an argument
    for a longer history."""
    stream_id = citation["stream_id"]
    if stream_id is None:
        return "unparseable_url"
    if stream_id not in ingested_stream_ids:
        return f"stream_not_ingested:{stream_id}"
    return "outside_build_window"


def resolve(
    citations: List[Dict], store: ZulipStore, ingested_stream_ids: Set[int]
) -> List[Dict]:
    """Attach the store's view of each cited thread.

    Resolution is reported, never assumed: a citation the store cannot resolve is kept
    with `resolved=False` and a reason, because the unresolved rate *is* the coverage
    measurement this file exists to publish.
    """
    resolved = []
    for citation in citations:
        record = dict(citation)
        view = store.resolve_url(citation["zulip_url"])
        if view is None:
            record.update(
                resolved=False,
                unresolved_reason=_unresolved_reason(citation, ingested_stream_ids),
                thread_key=None,
            )
        else:
            record.update(
                resolved=True,
                unresolved_reason=None,
                thread_key=view.thread.thread_key,
                thread_stream=view.thread.stream,
                thread_topic=view.thread.topic,
                thread_message_count=view.thread.message_count,
                thread_first_ts=view.thread.first_ts,
                thread_last_ts=view.thread.last_ts,
                thread_maintainers=view.thread.maintainer_participants,
                thread_decl_refs=view.thread.decl_refs,
                # The citing comment postdates the review it belongs to; a thread that
                # only started afterwards could not have informed the reviewer, and
                # that distinction is what makes a citation usable as a retrieval target.
                thread_predates_comment=(
                    view.thread.first_ts < (citation.get("created_at") or "")
                    if citation.get("created_at")
                    else None
                ),
            )
        resolved.append(record)
    return resolved


def summarize(records: List[Dict]) -> Dict:
    total = len(records)
    resolved = [r for r in records if r["resolved"]]
    maintainer = [
        r for r in records
        if (r.get("author_association") or "") in MAINTAINER_ASSOCIATIONS
    ]
    reasons: Dict[str, int] = {}
    for record in records:
        if not record["resolved"]:
            reason = record["unresolved_reason"] or "unknown"
            reasons[reason] = reasons.get(reason, 0) + 1
    return {
        "citations": total,
        "unique_urls": len({r["zulip_url"] for r in records}),
        "unique_prs": len({r["pr_number"] for r in records if r["pr_number"]}),
        "by_maintainer": len(maintainer),
        "with_message_anchor": sum(1 for r in records if r["anchor_message_id"]),
        "resolved": len(resolved),
        "resolved_predating_comment": sum(
            1 for r in resolved if r.get("thread_predates_comment")
        ),
        "unresolved_reasons": dict(sorted(reasons.items())),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comments", type=Path, default=REVIEW_COMMENTS)
    parser.add_argument(
        "--out", type=Path, default=PROJECT_ROOT / "inputs" / "zulip" / "review_citations.jsonl"
    )
    args = parser.parse_args(argv)

    if not args.comments.exists():
        print(f"{args.comments} missing — this needs the pr_review_v2 comment corpus")
        return 1

    citations = list(iter_citations(args.comments))
    config = ZulipConfig()
    ingested = {int(name.split("-", 1)[0]) for name in config.streams}
    with ZulipStore(config.sqlite_path) as store:
        records = resolve(citations, store, ingested)

    write_bytes(args.out, jsonl_bytes(records))
    summary = summarize(records)
    write_bytes(args.out.with_name(args.out.stem + "_report.json"), canonical_json_bytes(summary))

    for key, value in summary.items():
        print(f"{key:28s} {value}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
