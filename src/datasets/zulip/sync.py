"""
Stage 0: pin a local copy of the Mathlib Zulip archive.

`leanprover-community/archive` publishes one JSON file per topic under `zulip_json/`,
each a list of `{content, id, sender_full_name, timestamp}`. It needs no credentials
and imposes no rate limit, which is why it is the v1 source: the Zulip REST API
refuses anonymous reads, so using it would mean shipping an API key.

The clone is shallow by default — only the tip tree is ever read — but the commit is
recorded so a build is reproducible from a named archive state.

Usage:
  python -m src.datasets.zulip.sync [--ref main] [--full]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .config import ZulipConfig
from .io import canonical_json_bytes, write_bytes
from .schema import SyncState


class SyncError(RuntimeError):
    pass


def _git(args: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SyncError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sync(config: ZulipConfig, ref: str = "main", full: bool = False) -> SyncState:
    """Clone or update the archive, checkout `ref`, and record the pinned commit."""
    archive_dir = config.archive_dir
    if not (archive_dir / ".git").is_dir():
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        clone = ["clone", "--single-branch", "--branch", "main"]
        if not full:
            clone += ["--depth", "1"]
        clone += [config.archive_repo_url, str(archive_dir)]
        _git(clone)
    else:
        fetch = ["fetch", "origin", ref]
        if not full:
            fetch.insert(1, "--depth=1")
        _git(fetch, cwd=archive_dir)
        _git(["checkout", "--force", "FETCH_HEAD"], cwd=archive_dir)

    commit = _git(["rev-parse", "HEAD"], cwd=archive_dir)
    committed_at = _git(["show", "-s", "--format=%cI", "HEAD"], cwd=archive_dir)
    shallow = (archive_dir / ".git" / "shallow").exists()

    if not config.zulip_json_dir.is_dir():
        raise SyncError(
            f"{config.zulip_json_dir} missing — the archive layout changed; "
            "the builder expects zulip_json/<stream>/<topic>.json"
        )

    state = SyncState(
        repo_url=config.archive_repo_url,
        commit=commit,
        committed_at=committed_at,
        fetched_at=_now(),
        shallow=shallow,
    )
    write_bytes(config.sync_state_path, canonical_json_bytes(state))
    return state


def load_sync_state(config: ZulipConfig) -> SyncState:
    path = config.sync_state_path
    if not path.exists():
        raise SyncError(
            f"{path} missing — run `python -m src.datasets.zulip.sync` first"
        )
    return SyncState.model_validate(json.loads(path.read_text(encoding="utf-8")))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main", help="Branch, tag, or commit to pin")
    parser.add_argument("--full", action="store_true", help="Full clone instead of --depth 1")
    args = parser.parse_args(argv)

    config = ZulipConfig()
    state = sync(config, ref=args.ref, full=args.full)

    topics = sum(1 for _ in config.zulip_json_dir.rglob("*.json"))
    streams = sum(1 for path in config.zulip_json_dir.iterdir() if path.is_dir())
    print(f"archive  {config.archive_dir}")
    print(f"commit   {state.commit}  ({state.committed_at})")
    print(f"content  {streams} streams, {topics} topic files")
    print(f"state    {config.sync_state_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
