"""
Stage 3: the queryable store, and the temporal gate every read goes through.

SQLite with FTS5 (BM25 ranking is built in), so search costs no new dependency and
the whole corpus is one portable file.

**The gate is the point of this module.** The build window bounds what is stored; it
is not a safety property. What makes a read safe is `gate()`: no message at or after
`as_of`, and no message that references the PR under review. Both rules live in one
function that every public read path calls, mirroring
`src/mathlib_review/retrieval/precedents.py::validate_precedents` — the leak discipline is
auditable in one place instead of re-implemented per call site.

The second rule matters more than it looks. A thread can predate a PR's review and
still be *about* it: someone opens a PR, links it on Zulip, and the thread keeps
running. Time alone does not exclude that; the `pr_refs` tag does.
"""

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple
from urllib.parse import unquote

from .datetimes import iso_to_epoch
from .schema import STORE_VERSION, CodeBlock, ZulipMessage, ZulipThread

#: List-valued message columns stored as JSON text.
_JSON_FIELDS = (
    "code_blocks", "pr_refs", "issue_refs", "decl_refs",
    "file_refs", "mentions", "code_langs",
)
_BOOL_FIELDS = (
    "sender_is_maintainer", "sender_is_bot", "has_lean_code", "is_poll", "is_reply_quote",
)

_SCALAR_FIELDS = (
    "message_id", "stream_id", "stream", "topic", "thread_key",
    "sender_full_name", "sender_github", "timestamp_epoch", "timestamp",
    "text", "permalink",
)
_MESSAGE_COLUMNS = _SCALAR_FIELDS + _BOOL_FIELDS + _JSON_FIELDS

_THREAD_JSON = ("participants", "maintainer_participants", "pr_refs", "decl_refs", "file_refs")
_THREAD_BOOL = ("has_lean_code", "has_poll")
_THREAD_SCALAR = (
    "thread_key", "stream_id", "stream", "topic",
    "first_ts", "last_ts", "first_ts_epoch", "last_ts_epoch",
    "message_count", "topic_pr_ref", "archive_url",
)
_THREAD_COLUMNS = _THREAD_SCALAR + _THREAD_BOOL + _THREAD_JSON

_SCHEMA = f"""
CREATE TABLE messages (
  {', '.join(f'{c} TEXT' if c not in ('message_id','stream_id','timestamp_epoch') else f'{c} INTEGER' for c in _SCALAR_FIELDS)},
  {', '.join(f'{c} INTEGER' for c in _BOOL_FIELDS)},
  {', '.join(f'{c} TEXT' for c in _JSON_FIELDS)},
  PRIMARY KEY (message_id)
);
CREATE INDEX messages_thread ON messages (thread_key, timestamp_epoch);
CREATE INDEX messages_time ON messages (timestamp_epoch);
CREATE INDEX messages_sender ON messages (sender_full_name);

CREATE TABLE threads (
  thread_key TEXT PRIMARY KEY, stream_id INTEGER, stream TEXT, topic TEXT,
  first_ts TEXT, last_ts TEXT, first_ts_epoch INTEGER, last_ts_epoch INTEGER,
  message_count INTEGER, topic_pr_ref INTEGER, archive_url TEXT,
  {', '.join(f'{c} INTEGER' for c in _THREAD_BOOL)},
  {', '.join(f'{c} TEXT' for c in _THREAD_JSON)}
);
CREATE INDEX threads_stream ON threads (stream_id, topic);

-- Reference lookups are indexed rather than JSON-scanned: "which threads discuss this
-- declaration / this PR" is the store's most common question after full-text search.
CREATE TABLE refs (
  message_id INTEGER NOT NULL,
  thread_key TEXT NOT NULL,
  kind TEXT NOT NULL,      -- pr | issue | decl | file
  value TEXT NOT NULL
);
CREATE INDEX refs_lookup ON refs (kind, value);
CREATE INDEX refs_message ON refs (message_id);

CREATE VIRTUAL TABLE messages_fts USING fts5(
  text, topic, content='messages', content_rowid='message_id', tokenize='unicode61'
);

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""

_NARROW = re.compile(
    r"#narrow/(?:channel|stream)/(?P<stream>[^/]+)"
    r"(?:/topic/(?P<topic>[^/]+))?"
    r"(?:/(?:near|with)/(?P<anchor>\d+))?"
)
_DOT_ESCAPE = re.compile(r"\.([0-9A-F]{2})")


@dataclass
class ThreadView:
    """A thread plus the messages of it that survived the gate."""

    thread: ZulipThread
    messages: List[ZulipMessage]

    @property
    def truncated(self) -> bool:
        """True when the gate removed messages — i.e. the reader is seeing a prefix."""
        return len(self.messages) < self.thread.message_count


def gate(
    messages: Iterable[ZulipMessage],
    as_of: Optional[str] = None,
    exclude_pr: Optional[int] = None,
) -> List[ZulipMessage]:
    """This store's projection of the one retrieval rule. Every read path here calls it.

    The rule -- `as_of` exclusive, plus self-exclusion -- lives in
    `mathlib_review.retrieval_gate`, because four sources were each spelling it themselves and
    their ISO parsers disagreed. What stays here is the part that is genuinely about Zulip:
    self-exclusion is by `pr_refs`, not by origin. A maintainer discussing the PR under review
    in an unrelated thread is still discussing it, and that is not true of a precedent row,
    which leaks only if it came *from* the PR.

    Timestamps are already epochs in this store, so nothing is parsed per message.
    """

    from src.mathlib_review.retrieval_gate import RetrievalGate

    rule = RetrievalGate(as_of=as_of, exclude_pr=exclude_pr)
    cutoff = rule.cutoff_epoch
    return [
        message for message in messages
        if (cutoff is None or message.timestamp_epoch < cutoff)
        and not rule.excludes_pr(pr_refs=message.pr_refs)
    ]


def parse_narrow_url(url: str) -> Tuple[Optional[int], Optional[str], Optional[int]]:
    """`…#narrow/channel/287929-mathlib4/topic/Foo.20bar/near/123` -> (287929, 'Foo bar', 123).

    Handles the `channel`/`stream` spellings, `near`/`with` anchors, and topics that
    are missing, dot-escaped, or percent-escaped.
    """
    match = _NARROW.search(url)
    if not match:
        return None, None, None

    stream_raw = unquote(match.group("stream") or "")
    stream_id: Optional[int] = None
    head = stream_raw.split("-", 1)[0]
    if head.isdigit():
        stream_id = int(head)

    topic = match.group("topic")
    if topic:
        topic = _DOT_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), unquote(topic))

    anchor = match.group("anchor")
    return stream_id, topic, int(anchor) if anchor else None


def _row_to_message(row: sqlite3.Row) -> ZulipMessage:
    payload = {key: row[key] for key in _MESSAGE_COLUMNS}
    for field in _JSON_FIELDS:
        payload[field] = json.loads(payload[field])
    payload["code_blocks"] = [CodeBlock(**block) for block in payload["code_blocks"]]
    for field in _BOOL_FIELDS:
        payload[field] = bool(payload[field])
    return ZulipMessage(**payload)


def _row_to_thread(row: sqlite3.Row) -> ZulipThread:
    payload = {key: row[key] for key in _THREAD_COLUMNS}
    for field in _THREAD_JSON:
        payload[field] = json.loads(payload[field])
    for field in _THREAD_BOOL:
        payload[field] = bool(payload[field])
    return ZulipThread(**payload)


class ZulipStore:
    """Read access to a built store. Open with `ZulipStore(path)`."""

    def __init__(self, path: Path):
        if not Path(path).exists():
            raise FileNotFoundError(
                f"{path} missing — run `python -m src.datasets.zulip.build`"
            )
        self._conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ZulipStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- construction ----------------------------------------------------

    @staticmethod
    def build(
        path: Path,
        messages: Sequence[ZulipMessage],
        threads: Sequence[ZulipThread],
        meta: Optional[dict] = None,
    ) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
        conn = sqlite3.connect(path)
        try:
            conn.executescript(_SCHEMA)
            message_rows = []
            ref_rows = []
            for message in messages:
                dumped = message.model_dump(mode="json")
                message_rows.append(
                    tuple(
                        json.dumps(dumped[c], sort_keys=True, ensure_ascii=False)
                        if c in _JSON_FIELDS
                        else (int(dumped[c]) if c in _BOOL_FIELDS else dumped[c])
                        for c in _MESSAGE_COLUMNS
                    )
                )
                for kind, field in (
                    ("pr", "pr_refs"), ("issue", "issue_refs"),
                    ("decl", "decl_refs"), ("file", "file_refs"),
                ):
                    for value in dumped[field]:
                        ref_rows.append((message.message_id, message.thread_key, kind, str(value)))

            conn.executemany(
                f"INSERT INTO messages ({','.join(_MESSAGE_COLUMNS)}) "
                f"VALUES ({','.join('?' * len(_MESSAGE_COLUMNS))})",
                message_rows,
            )
            conn.executemany("INSERT INTO refs VALUES (?,?,?,?)", ref_rows)

            thread_rows = []
            for thread in threads:
                dumped = thread.model_dump(mode="json")
                thread_rows.append(
                    tuple(
                        json.dumps(dumped[c], sort_keys=True, ensure_ascii=False)
                        if c in _THREAD_JSON
                        else (int(dumped[c]) if c in _THREAD_BOOL else dumped[c])
                        for c in _THREAD_COLUMNS
                    )
                )
            conn.executemany(
                f"INSERT INTO threads ({','.join(_THREAD_COLUMNS)}) "
                f"VALUES ({','.join('?' * len(_THREAD_COLUMNS))})",
                thread_rows,
            )

            conn.execute(
                "INSERT INTO messages_fts (rowid, text, topic) "
                "SELECT message_id, text, topic FROM messages"
            )
            conn.executemany(
                "INSERT INTO meta VALUES (?,?)",
                sorted({"store_version": STORE_VERSION, **(meta or {})}.items()),
            )
            conn.commit()
        finally:
            conn.close()
        return path

    # --- reads -----------------------------------------------------------

    def meta(self) -> dict:
        return {row["key"]: row["value"] for row in self._conn.execute("SELECT * FROM meta")}

    def counts(self) -> Tuple[int, int]:
        messages = self._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        threads = self._conn.execute("SELECT COUNT(*) FROM threads").fetchone()[0]
        return messages, threads

    def message(self, message_id: int) -> Optional[ZulipMessage]:
        row = self._conn.execute(
            "SELECT * FROM messages WHERE message_id = ?", (message_id,)
        ).fetchone()
        return _row_to_message(row) if row else None

    def _thread_row(self, thread_key: str) -> Optional[ZulipThread]:
        row = self._conn.execute(
            "SELECT * FROM threads WHERE thread_key = ?", (thread_key,)
        ).fetchone()
        return _row_to_thread(row) if row else None

    def _view(
        self, thread_key: str, as_of: Optional[str], exclude_pr: Optional[int]
    ) -> Optional[ThreadView]:
        thread = self._thread_row(thread_key)
        if thread is None:
            return None
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE thread_key = ? ORDER BY timestamp_epoch, message_id",
            (thread_key,),
        )
        return ThreadView(thread, gate((_row_to_message(r) for r in rows), as_of, exclude_pr))

    def thread(
        self,
        stream_id: int,
        topic: str,
        as_of: Optional[str] = None,
        exclude_pr: Optional[int] = None,
    ) -> Optional[ThreadView]:
        row = self._conn.execute(
            "SELECT thread_key FROM threads WHERE stream_id = ? AND topic = ?",
            (stream_id, topic),
        ).fetchone()
        if row is None:
            # Zulip topic matching is case-insensitive; an old link may not match byte-wise.
            row = self._conn.execute(
                "SELECT thread_key FROM threads WHERE stream_id = ? "
                "AND lower(topic) = lower(?)",
                (stream_id, topic),
            ).fetchone()
        return self._view(row["thread_key"], as_of, exclude_pr) if row else None

    def resolve_url(
        self,
        url: str,
        as_of: Optional[str] = None,
        exclude_pr: Optional[int] = None,
    ) -> Optional[ThreadView]:
        """Resolve a Zulip permalink to its thread.

        Prefers the message anchor when there is one: a topic can be renamed or moved
        between channels, but a message ID is stable, so the anchor resolves links that
        topic matching would miss.
        """
        stream_id, topic, anchor = parse_narrow_url(url)
        if anchor is not None:
            message = self.message(anchor)
            if message is not None:
                return self._view(message.thread_key, as_of, exclude_pr)
        if stream_id is not None and topic:
            return self.thread(stream_id, topic, as_of, exclude_pr)
        return None

    def _threads_by_ref(
        self, kind: str, value: str, as_of: Optional[str], exclude_pr: Optional[int]
    ) -> List[ThreadView]:
        rows = self._conn.execute(
            "SELECT DISTINCT thread_key FROM refs WHERE kind = ? AND value = ?", (kind, value)
        ).fetchall()
        views = []
        for row in rows:
            view = self._view(row["thread_key"], as_of, exclude_pr)
            if view and view.messages:
                views.append(view)
        views.sort(key=lambda v: v.thread.first_ts_epoch)
        return views

    def threads_for_pr(
        self, pr_number: int, as_of: Optional[str] = None, exclude_self: bool = True
    ) -> List[ThreadView]:
        """Threads that reference this PR.

        `exclude_self` is on by default and is why this is usually *empty* under a
        gate: a thread that names the PR is discussion *of* the PR, which a reviewer
        emulator must not see. Turn it off only for analysis of what was said.
        """
        # A thread whose only PR mentions were the target's is emptied by the gate and
        # dropped by `_threads_by_ref`, which is the intended behaviour.
        return self._threads_by_ref(
            "pr", str(pr_number), as_of, pr_number if exclude_self else None
        )

    def threads_mentioning(
        self, declaration: str, as_of: Optional[str] = None, exclude_pr: Optional[int] = None
    ) -> List[ThreadView]:
        return self._threads_by_ref("decl", declaration, as_of, exclude_pr)

    def search(
        self,
        query: str,
        *,
        since: Optional[str] = None,
        until: Optional[str] = None,
        streams: Optional[Sequence[str]] = None,
        senders: Optional[Sequence[str]] = None,
        maintainers_only: bool = False,
        exclude_bots: bool = True,
        as_of: Optional[str] = None,
        exclude_pr: Optional[int] = None,
        limit: int = 25,
    ) -> List[ZulipMessage]:
        """Full-text search, BM25-ranked. `as_of` still applies on top of `until`.

        `exclude_bots` defaults on: CI and notification bots post ~12k messages that
        match ordinary queries and carry no opinion, so including them by default would
        make the common search worse.
        """
        where = ["messages_fts MATCH ?"]
        params: List = [query]
        if since:
            where.append("m.timestamp_epoch >= ?")
            params.append(iso_to_epoch(since))
        if until:
            where.append("m.timestamp_epoch < ?")
            params.append(iso_to_epoch(until))
        if as_of:
            where.append("m.timestamp_epoch < ?")
            params.append(iso_to_epoch(as_of))
        if streams:
            where.append(f"m.stream IN ({','.join('?' * len(streams))})")
            params += list(streams)
        if senders:
            where.append(f"m.sender_full_name IN ({','.join('?' * len(senders))})")
            params += list(senders)
        if maintainers_only:
            where.append("m.sender_is_maintainer = 1")
        if exclude_bots:
            where.append("m.sender_is_bot = 0")

        # Over-fetch so the gate can drop rows without silently shrinking the page.
        params.append(limit * 4)
        rows = self._conn.execute(
            "SELECT m.* FROM messages_fts f JOIN messages m ON m.message_id = f.rowid "
            f"WHERE {' AND '.join(where)} ORDER BY bm25(messages_fts), m.timestamp_epoch "
            "LIMIT ?",
            params,
        ).fetchall()
        found = gate((_row_to_message(r) for r in rows), as_of, exclude_pr)
        return found[:limit]
