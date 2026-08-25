"""Configuration for the Zulip discussion store."""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, model_validator

from ape.utils.project import PROJECT_ROOT

ARCHIVE_REPO_URL = "https://github.com/leanprover-community/archive.git"

#: Streams that carry Mathlib review-relevant discussion. Directory names as they
#: appear under `zulip_json/`, i.e. `{stream_id}-{slug}` with the slug percent-encoded
#: exactly as the archive writes it.
CORE_STREAMS = (
    "287929-mathlib4",
    "144837-PR-reviews",
    "217875-Is-there-code-for-X%3F",
    "113488-general",
    "270676-lean4",
    "239415-metaprogramming-",
    "263328-triage",
    "113538-CI",
    "428973-nightly-testing",
)

#: A year of discussion ending after the Dec-2025 review window used by the PR-review
#: benchmarks. Enough to browse and to answer "is this discussed"; NOT enough to
#: measure a trend — norm-maturity work needs a multi-year window (see module docs).
DEFAULT_SINCE = "2024-11-01"


class ZulipConfig(BaseModel):
    archive_repo_url: str = Field(default=ARCHIVE_REPO_URL)

    # --- storage (data/ is gitignored; inputs/ is tracked) ---
    archive_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "zulip" / "archive",
        description="Clone of leanprover-community/archive, pinned by commit",
    )
    corpus_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "zulip" / "corpus",
        description="Normalized messages/threads + the SQLite index",
    )
    output_dir: Path = Field(
        default=PROJECT_ROOT / "inputs" / "zulip",
        description="Committed provenance: manifest.json + corpus_report.json",
    )

    # --- window ---
    since: Optional[str] = Field(default=DEFAULT_SINCE, description="YYYY-MM-DD, inclusive")
    until: Optional[str] = Field(default=None, description="YYYY-MM-DD, exclusive")

    # --- stream selection ---
    streams: List[str] = Field(
        default_factory=lambda: list(CORE_STREAMS),
        description="Archive stream directory names; empty means every stream",
    )

    @model_validator(mode="after")
    def _check_window(self):
        if self.since and self.until and self.since >= self.until:
            raise ValueError(f"since ({self.since}) must precede until ({self.until})")
        return self

    @property
    def zulip_json_dir(self) -> Path:
        return self.archive_dir / "zulip_json"

    @property
    def messages_path(self) -> Path:
        return self.corpus_dir / "messages.jsonl"

    @property
    def threads_path(self) -> Path:
        return self.corpus_dir / "threads.jsonl"

    @property
    def sqlite_path(self) -> Path:
        return self.corpus_dir / "zulip.sqlite3"

    @property
    def sync_state_path(self) -> Path:
        return self.archive_dir.parent / "sync_state.json"

    @property
    def manifest_path(self) -> Path:
        return self.output_dir / "manifest.json"

    @property
    def report_path(self) -> Path:
        return self.output_dir / "corpus_report.json"
