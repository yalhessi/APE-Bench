"""
Stage 1-3 driver: normalize the pinned archive, tag it, index it, publish provenance.

Corpus bytes stay under `data/` (gitignored). What gets committed is
`inputs/zulip/manifest.json` + `corpus_report.json`: the archive commit, the declared
window and stream set, the tool versions, and a sha256 per artifact. That is what makes
a rebuild checkable — the project's freezing discipline applied to a corpus far too
large to check in, by pinning provenance and determinism instead of bytes.

Usage:
  python -m src.datasets.zulip.build [--since 2024-11-01] [--until …]
                                     [--streams core|all|<name> …]
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ape.utils.project import PROJECT_ROOT

from .config import CORE_STREAMS, ZulipConfig
from .identity import load_identities
from .io import canonical_json_bytes, jsonl_bytes, write_bytes
from .normalize import normalize_corpus
from .schema import (
    NORMALIZE_VERSION,
    STORE_VERSION,
    TAGS_VERSION,
    ArtifactRef,
    ZulipManifest,
)
from .store import ZulipStore
from .sync import load_sync_state


def assert_repo_root() -> None:
    """Manifests record repo-relative paths, so a build must run from the root."""
    if Path.cwd().resolve() != PROJECT_ROOT.resolve():
        raise SystemExit(f"run from the repository root ({PROJECT_ROOT}), not {Path.cwd()}")


def _ref(path: Path, sha: str, size: int, records: int) -> ArtifactRef:
    return ArtifactRef(
        path=str(path.resolve().relative_to(PROJECT_ROOT)),
        sha256=sha,
        records=records,
        bytes=size,
    )


def build(config: ZulipConfig) -> ZulipManifest:
    sync_state = load_sync_state(config)
    identities = load_identities()

    messages, threads, report = normalize_corpus(
        zulip_json_dir=config.zulip_json_dir,
        streams=config.streams,
        identities=identities,
        since=config.since,
        until=config.until,
        archive_commit=sync_state.commit,
        normalize_version=NORMALIZE_VERSION,
        tags_version=TAGS_VERSION,
    )

    artifacts: List[ArtifactRef] = []
    sha, size = write_bytes(config.messages_path, jsonl_bytes(messages))
    artifacts.append(_ref(config.messages_path, sha, size, len(messages)))
    sha, size = write_bytes(config.threads_path, jsonl_bytes(threads))
    artifacts.append(_ref(config.threads_path, sha, size, len(threads)))

    ZulipStore.build(
        config.sqlite_path,
        messages,
        threads,
        meta={
            "archive_commit": sync_state.commit,
            "normalize_version": NORMALIZE_VERSION,
            "tags_version": TAGS_VERSION,
            "since": config.since or "",
            "until": config.until or "",
        },
    )

    sha, size = write_bytes(config.report_path, canonical_json_bytes(report))
    artifacts.append(_ref(config.report_path, sha, size, len(report.streams)))

    manifest = ZulipManifest(
        created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        archive=sync_state,
        since=config.since,
        until=config.until,
        streams=list(config.streams),
        versions={
            "normalize": NORMALIZE_VERSION,
            "tags": TAGS_VERSION,
            "store": STORE_VERSION,
        },
        artifacts=artifacts,
    )
    write_bytes(config.manifest_path, canonical_json_bytes(manifest))
    return manifest


def _resolve_streams(values: Optional[List[str]]) -> List[str]:
    if not values or values == ["core"]:
        return list(CORE_STREAMS)
    if values == ["all"]:
        return []
    return values


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None, help="YAML overrides")
    parser.add_argument("--since", default=None, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--until", default=None, help="YYYY-MM-DD, exclusive")
    parser.add_argument(
        "--streams", nargs="*", default=None,
        help="'core' (default), 'all', or explicit archive stream directory names",
    )
    args = parser.parse_args(argv)
    assert_repo_root()

    settings = {}
    if args.config:
        import yaml

        settings = yaml.safe_load(args.config.read_text(encoding="utf-8")) or {}
    if args.since is not None:
        settings["since"] = args.since
    if args.until is not None:
        settings["until"] = args.until
    if args.streams is not None or "streams" in settings:
        settings["streams"] = _resolve_streams(
            args.streams if args.streams is not None else settings.get("streams")
        )
    config = ZulipConfig(**settings)
    manifest = build(config)

    messages = next(a for a in manifest.artifacts if a.path.endswith("messages.jsonl"))
    threads = next(a for a in manifest.artifacts if a.path.endswith("threads.jsonl"))
    print(f"archive   {manifest.archive.commit[:12]} ({manifest.archive.committed_at})")
    print(f"window    {manifest.since or 'beginning'} .. {manifest.until or 'archive head'}")
    print(f"streams   {len(manifest.streams) or 'all'}")
    print(f"messages  {messages.records:,}  ({messages.sha256[:12]})")
    print(f"threads   {threads.records:,}  ({threads.sha256[:12]})")
    print(f"sqlite    {config.sqlite_path}")
    print(f"manifest  {config.manifest_path}")
    print(f"report    {config.report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
