"""
Stage 1: archive topic JSON -> tagged `ZulipMessage` / `ZulipThread` records.

The archive stores one file per topic, `zulip_json/{stream_id}-{slug}/{topic}.json`,
holding every message that topic ever received. Two consequences shape this module:

- A topic file is kept when *any* of its messages falls in the window, and the whole
  thread is then retained. Truncating a thread to the window would hand a reader half
  a conversation; each message carries its own timestamp, so a caller that wants the
  window applied strictly can filter, and `store.as_of` does exactly that.
- Both the stream directory name and the topic file name are percent-and-dot escaped
  by the archive (`.20` for a space, `%3F` for `?`). Decoding is needed to recover the
  real topic string and to rebuild Zulip permalinks.
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .html_text import extract
from .identity import Identities, is_bot
from .schema import (
    CodeBlock,
    CorpusReport,
    StreamCoverage,
    ZulipMessage,
    ZulipThread,
)
from .tags import COUNTED_TAGS, merge_lists, tag_message, topic_pr_ref
from .datetimes import epoch_to_iso, iso_to_epoch

ZULIP_BASE = "https://leanprover.zulipchat.com"
ARCHIVE_BASE = "https://leanprover-community.github.io/archive"

#: The archive escapes a byte as `.XX` (uppercase hex). Percent-escapes also survive
#: in some directory names, so both are decoded.
_DOT_ESCAPE = re.compile(r"\.([0-9A-F]{2})")
_STREAM_DIR = re.compile(r"^(\d+)-(.*)$")


def decode_archive_name(name: str) -> str:
    """`Continuous.20function` -> `Continuous function`; `Is-there-code-for-X%3F` -> `…X?`."""
    from urllib.parse import unquote

    decoded = _DOT_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), name)
    return unquote(decoded)


def split_stream_dir(dirname: str) -> Tuple[int, str]:
    """`287929-mathlib4` -> (287929, 'mathlib4')."""
    match = _STREAM_DIR.match(dirname)
    if not match:
        raise ValueError(f"unrecognised archive stream directory: {dirname!r}")
    return int(match.group(1)), decode_archive_name(match.group(2))


def _permalink(stream_dir: str, topic_file: str, message_id: int) -> str:
    return f"{ZULIP_BASE}/#narrow/channel/{stream_dir}/topic/{topic_file}/near/{message_id}"


def _archive_url(stream_dir: str, topic_file: str) -> str:
    return f"{ARCHIVE_BASE}/stream/{stream_dir}/topic/{topic_file}.html"


def normalize_topic(
    path: Path,
    stream_dir: str,
    identities: Identities,
) -> Tuple[List[ZulipMessage], Optional[ZulipThread]]:
    """Normalize one archive topic file. Returns ([], None) for an empty/unusable topic."""
    stream_id, stream = split_stream_dir(stream_dir)
    topic_file = path.stem
    topic = decode_archive_name(topic_file)
    thread_key = f"{stream_id}/{topic}"

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return [], None
    if not isinstance(raw, list) or not raw:
        return [], None

    messages: List[ZulipMessage] = []
    for entry in raw:
        if not isinstance(entry, dict) or "id" not in entry or "timestamp" not in entry:
            continue
        content = extract(entry.get("content") or "")
        sender = str(entry.get("sender_full_name") or "").strip()
        github, is_maintainer = identities.resolve(sender)
        epoch = int(entry["timestamp"])
        messages.append(
            ZulipMessage(
                message_id=int(entry["id"]),
                stream_id=stream_id,
                stream=stream,
                topic=topic,
                thread_key=thread_key,
                sender_full_name=sender,
                sender_github=github,
                sender_is_maintainer=is_maintainer,
                sender_is_bot=is_bot(sender),
                timestamp_epoch=epoch,
                timestamp=epoch_to_iso(epoch),
                text=content.text,
                code_blocks=[CodeBlock(lang=lang, code=code) for lang, code in content.code_blocks],
                permalink=_permalink(stream_dir, topic_file, int(entry["id"])),
                **tag_message(content),
            )
        )

    if not messages:
        return [], None

    messages.sort(key=lambda m: (m.timestamp_epoch, m.message_id))
    thread = ZulipThread(
        thread_key=thread_key,
        stream_id=stream_id,
        stream=stream,
        topic=topic,
        first_ts=messages[0].timestamp,
        last_ts=messages[-1].timestamp,
        first_ts_epoch=messages[0].timestamp_epoch,
        last_ts_epoch=messages[-1].timestamp_epoch,
        message_count=len(messages),
        participants=sorted({m.sender_full_name for m in messages if m.sender_full_name}),
        maintainer_participants=sorted(
            {m.sender_full_name for m in messages if m.sender_is_maintainer}
        ),
        topic_pr_ref=topic_pr_ref(topic),
        pr_refs=merge_lists(m.pr_refs for m in messages),
        decl_refs=merge_lists(m.decl_refs for m in messages),
        file_refs=merge_lists(m.file_refs for m in messages),
        has_lean_code=any(m.has_lean_code for m in messages),
        has_poll=any(m.is_poll for m in messages),
        archive_url=_archive_url(stream_dir, topic_file),
    )
    return messages, thread


def _descend_to_topics(root: Path) -> Path:
    """Follow a stream whose *name* contains a slash down to its topic files.

    Zulip stream names may contain `/` ("metaprogramming / tactics", "FoMM / Lean
    Together 2020"), and the archive turns that into a nested directory. Descending
    only while the current level holds no `*.json` keeps this unambiguous: a topic
    file and a stream-name continuation never coexist at the same level.
    """
    current = root
    for _ in range(4):  # depth guard; the archive uses at most one level today
        if any(current.glob("*.json")):
            return current
        children = [p for p in current.iterdir() if p.is_dir()]
        if len(children) != 1:
            return current
        current = children[0]
    return current


def _stream_dirs(zulip_json_dir: Path, streams: List[str]) -> List[Tuple[str, Path]]:
    """Returns (stream directory name relative to zulip_json/, resolved topic dir)."""
    if streams:
        roots = []
        for name in streams:
            path = zulip_json_dir / name
            if not path.is_dir():
                raise FileNotFoundError(
                    f"stream directory {name!r} not in the archive; "
                    f"see {zulip_json_dir} for the available names"
                )
            roots.append(path)
    else:
        roots = sorted((p for p in zulip_json_dir.iterdir() if p.is_dir()), key=lambda p: p.name)

    resolved = []
    for root in roots:
        topics_dir = _descend_to_topics(root)
        resolved.append((topics_dir.relative_to(zulip_json_dir).as_posix(), topics_dir))
    return resolved


def normalize_corpus(
    zulip_json_dir: Path,
    streams: List[str],
    identities: Identities,
    since: Optional[str] = None,
    until: Optional[str] = None,
    archive_commit: str = "",
    normalize_version: str = "",
    tags_version: str = "",
) -> Tuple[List[ZulipMessage], List[ZulipThread], CorpusReport]:
    """Walk the selected streams and return (messages, threads, coverage report)."""
    since_epoch = iso_to_epoch(since) if since else None
    until_epoch = iso_to_epoch(until) if until else None

    all_messages: List[ZulipMessage] = []
    all_threads: List[ZulipThread] = []
    coverage: List[StreamCoverage] = []
    total_in_window = 0

    for stream_dir, stream_path in _stream_dirs(zulip_json_dir, streams):
        _, stream_name = split_stream_dir(stream_dir)
        scanned = kept = messages_total = messages_in_window = 0
        dropped: Dict[str, int] = {}
        first_ts: Optional[str] = None
        last_ts: Optional[str] = None

        for topic_path in sorted(stream_path.glob("*.json"), key=lambda p: p.name):
            scanned += 1
            messages, thread = normalize_topic(topic_path, stream_dir, identities)
            if thread is None:
                dropped["unparseable_or_empty"] = dropped.get("unparseable_or_empty", 0) + 1
                continue
            messages_total += len(messages)

            in_window = [
                m for m in messages
                if (since_epoch is None or m.timestamp_epoch >= since_epoch)
                and (until_epoch is None or m.timestamp_epoch < until_epoch)
            ]
            if not in_window:
                dropped["outside_window"] = dropped.get("outside_window", 0) + 1
                continue

            kept += 1
            messages_in_window += len(in_window)
            all_messages.extend(messages)
            all_threads.append(thread)
            first_ts = thread.first_ts if first_ts is None else min(first_ts, thread.first_ts)
            last_ts = thread.last_ts if last_ts is None else max(last_ts, thread.last_ts)

        coverage.append(
            StreamCoverage(
                stream=stream_name,
                topics_scanned=scanned,
                topics_kept=kept,
                topics_dropped=dict(sorted(dropped.items())),
                messages_total=messages_total,
                messages_in_window=messages_in_window,
                first_ts=first_ts,
                last_ts=last_ts,
            )
        )
        total_in_window += messages_in_window

    all_messages.sort(key=lambda m: (m.timestamp_epoch, m.message_id))
    all_threads.sort(key=lambda t: t.thread_key)

    tag_counts: Dict[str, int] = {}
    for tag in COUNTED_TAGS:
        tag_counts[tag] = sum(1 for m in all_messages if getattr(m, tag))

    volume: Counter = Counter()
    rostered: Set[str] = set()
    for message in all_messages:
        volume[message.sender_full_name] += 1
        if message.sender_is_maintainer:
            rostered.add(message.sender_full_name)
    # Bots are excluded from the drift diagnostic: they are correctly unrostered, and
    # leaving them in would bury the human names this list exists to surface.
    unrostered = [
        name for name, _ in volume.most_common()
        if name not in rostered and not is_bot(name)
    ]

    report = CorpusReport(
        normalize_version=normalize_version,
        tags_version=tags_version,
        archive_commit=archive_commit,
        since=since,
        until=until,
        streams=coverage,
        messages=len(all_messages),
        messages_in_window=total_in_window,
        threads=len(all_threads),
        first_ts=all_messages[0].timestamp if all_messages else None,
        last_ts=all_messages[-1].timestamp if all_messages else None,
        senders_distinct=len(volume),
        senders_on_roster=len(rostered),
        messages_from_roster=sum(1 for m in all_messages if m.sender_is_maintainer),
        messages_from_bots=sum(1 for m in all_messages if m.sender_is_bot),
        top_unrostered_senders=unrostered[:25],
        tag_counts=tag_counts,
    )
    return all_messages, all_threads, report
