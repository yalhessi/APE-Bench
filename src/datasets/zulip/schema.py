"""
Record models for the Zulip discussion store.

Field order is the serialization order; every writer goes through `canonical_json`
in `io.py` so a rebuild from the same archive commit is byte-identical.

`SemanticTags` is reserved but never populated by this package: the mechanical tag
pass is free, deterministic and immune to model noise, so it lands first and a later
cached LLM pass can fill the slot without a schema break.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

#: Bumped whenever `normalize.py` changes the bytes it emits for the same input.
NORMALIZE_VERSION = "zulip-normalize/1"

#: Bumped whenever `tags.py` changes a derived tag.
TAGS_VERSION = "zulip-tags/1"

#: Bumped whenever `store.py` changes the SQLite layout.
STORE_VERSION = "zulip-store/1"

DiscussionKind = Literal[
    "convention_decision",
    "library_inventory",
    "api_design",
    "tactic_idiom",
    "proof_technique",
    "pr_triage",
    "tooling_ci",
    "math_question",
    "announcement",
    "other",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CodeBlock(StrictModel):
    lang: str = Field(default="", description="Zulip's data-code-language, '' if untagged")
    code: str


class SemanticTags(StrictModel):
    """Reserved for a later cached LLM pass. Never written by this package."""

    discussion_kind: DiscussionKind
    norm_subject: Optional[str] = None
    resolution: Literal["decided", "contested", "unresolved", "not_applicable"] = "not_applicable"
    tagger_version: str


class ZulipMessage(StrictModel):
    message_id: int
    stream_id: int
    stream: str
    topic: str
    thread_key: str

    sender_full_name: str
    sender_github: Optional[str] = None
    sender_is_maintainer: bool = False
    sender_is_bot: bool = False

    timestamp_epoch: int
    timestamp: str = Field(description="ISO-8601 UTC, second precision")

    text: str
    code_blocks: List[CodeBlock] = Field(default_factory=list)
    permalink: str

    # --- mechanical tags (tags.py) ---
    pr_refs: List[int] = Field(default_factory=list)
    issue_refs: List[int] = Field(default_factory=list)
    decl_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)
    code_langs: List[str] = Field(default_factory=list)
    has_lean_code: bool = False
    is_poll: bool = False
    is_reply_quote: bool = False

    semantic: Optional[SemanticTags] = None


class ZulipThread(StrictModel):
    thread_key: str
    stream_id: int
    stream: str
    topic: str

    first_ts: str
    last_ts: str
    first_ts_epoch: int
    last_ts_epoch: int
    message_count: int

    participants: List[str] = Field(default_factory=list)
    maintainer_participants: List[str] = Field(default_factory=list)

    topic_pr_ref: Optional[int] = Field(
        default=None,
        description="PR number encoded in the topic title itself (the `!4#NNNNN` convention)",
    )
    pr_refs: List[int] = Field(default_factory=list)
    decl_refs: List[str] = Field(default_factory=list)
    file_refs: List[str] = Field(default_factory=list)
    has_lean_code: bool = False
    has_poll: bool = False

    archive_url: str


class SyncState(StrictModel):
    repo_url: str
    commit: str
    committed_at: str
    fetched_at: str
    shallow: bool


class StreamCoverage(StrictModel):
    stream: str
    topics_scanned: int
    topics_kept: int
    topics_dropped: Dict[str, int] = Field(
        default_factory=dict, description="drop reason -> count; no silent loss"
    )
    messages_total: int
    messages_in_window: int
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None


class CorpusReport(StrictModel):
    """The store declares its own coverage; gaps are published, not silent."""

    normalize_version: str
    tags_version: str
    archive_commit: str
    since: Optional[str]
    until: Optional[str]

    streams: List[StreamCoverage]

    messages: int = Field(
        description="Messages stored: every message of every kept thread, including "
        "ones older than `since` (a thread is kept whole so a reader gets its context)"
    )
    messages_in_window: int = Field(description="Of those, the ones inside [since, until)")
    threads: int
    first_ts: Optional[str] = None
    last_ts: Optional[str] = None

    senders_distinct: int
    senders_on_roster: int = Field(
        description="Distinct authors on an admin/maintainer/reviewer team. Expected to "
        "be a small fraction of `senders_distinct`: the roster is ~70 people and the "
        "community is thousands, so a low ratio here is the corpus, not a join failure."
    )
    messages_from_roster: int = Field(description="Message-weighted roster share")
    messages_from_bots: int = Field(default=0, description="Excluded from norm signal by callers")
    top_unrostered_senders: List[str] = Field(
        default_factory=list,
        description="Most prolific authors with no roster mapping, most-first. A "
        "familiar maintainer name appearing here means roster drift, not a quiet author.",
    )

    tag_counts: Dict[str, int] = Field(default_factory=dict)


class ArtifactRef(StrictModel):
    path: str
    sha256: str
    records: int
    bytes: int


class ZulipManifest(StrictModel):
    schema_version: Literal["zulip-manifest-1"] = "zulip-manifest-1"
    created_at: str
    archive: SyncState
    since: Optional[str]
    until: Optional[str]
    streams: List[str]
    versions: Dict[str, str]
    artifacts: List[ArtifactRef]
    window_caveat: str = Field(
        default=(
            "The build window bounds what is stored, not what is safe to read. Leak-freedom "
            "is enforced per-read by store.as_of. A window shorter than ~2 years cannot "
            "support trend/maturity measurement."
        )
    )
