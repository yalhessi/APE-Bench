"""Deterministic raw-event index over cached GitHub collection bundles."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.mathlib_review.io import canonical_json_bytes, jsonl_bytes, sha256_bytes, sha256_file, write_once
from src.mathlib_review.schema import ArtifactRef, SourceEvent


EVENT_LEDGER_VERSION = "bundle_index_v1"

_COLLECTIONS = (
    ("reviews", "review"),
    ("review_comments", "review_comment"),
    ("issue_comments", "issue_comment"),
    ("commits", "commit"),
    ("files", "file"),
    ("timeline", "timeline"),
    ("review_threads", "review_thread"),
    ("body_edits", "metadata_edit"),
)


def _occurred_at(event_type: str, payload: Dict[str, Any]) -> Optional[str]:
    for key in ("submitted_at", "created_at", "edited_at", "updated_at"):
        if payload.get(key):
            return str(payload[key])
    commit = payload.get("commit") or {}
    for container in (
        commit.get("committer") or {},
        commit.get("author") or {},
        payload.get("committer") or {},
        payload.get("author") or {},
    ):
        if isinstance(container, dict) and container.get("date"):
            return str(container["date"])
    return None


def _actor(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("user", "actor", "author"):
        value = payload.get(key)
        if isinstance(value, dict):
            actor = value.get("login") or value.get("name")
            if actor:
                return str(actor)
    return None


def _external_identity(event_type: str, payload: Dict[str, Any], payload_hash: str) -> str:
    for key in ("id", "node_id", "sha", "thread_id", "filename", "number"):
        if payload.get(key) is not None:
            return f"{key}:{payload[key]}"
    return f"payload:{payload_hash}"


def _event(
    *,
    repo: str,
    pr_number: int,
    event_type: str,
    payload: Dict[str, Any],
    source_object: ArtifactRef,
    source_key: str,
) -> SourceEvent:
    payload_hash = sha256_bytes(canonical_json_bytes(payload))
    identity = _external_identity(event_type, payload, payload_hash)
    id_hash = sha256_bytes(canonical_json_bytes([repo, pr_number, event_type, identity]))[:24]
    return SourceEvent(
        event_id=f"event:{id_hash}",
        repo=repo,
        pr_number=pr_number,
        event_type=event_type,
        occurred_at=_occurred_at(event_type, payload),
        actor=_actor(payload),
        source_object=source_object,
        source_key=source_key,
        payload_sha256=payload_hash,
    )


def events_from_bundle(bundle: Dict[str, Any], *, bundle_path: Path, repo: str) -> List[SourceEvent]:
    pr = bundle.get("pr") or {}
    pr_number = int(pr["number"])
    source_object = ArtifactRef(
        path=bundle_path.as_posix(),
        role="raw_github_bundle",
        sha256=sha256_file(bundle_path),
    )
    events = [
        _event(
            repo=repo,
            pr_number=pr_number,
            event_type="pull_request",
            payload=pr,
            source_object=source_object,
            source_key="/pr",
        )
    ]
    for collection, event_type in _COLLECTIONS:
        values = bundle.get(collection)
        if values is None:
            continue
        if not isinstance(values, list):
            raise ValueError(f"PR {pr_number}: bundle field {collection!r} is not a list")
        for index, payload in enumerate(values):
            if not isinstance(payload, dict):
                raise ValueError(
                    f"PR {pr_number}: {collection}[{index}] is not a JSON object"
                )
            events.append(
                _event(
                    repo=repo,
                    pr_number=pr_number,
                    event_type=event_type,
                    payload=payload,
                    source_object=source_object,
                    source_key=f"/{collection}/{index}",
                )
            )
    return events


def expected_source_keys(bundle: Dict[str, Any]) -> List[str]:
    keys = ["/pr"]
    for collection, _event_type in _COLLECTIONS:
        values = bundle.get(collection)
        if values is not None:
            keys.extend(f"/{collection}/{index}" for index in range(len(values)))
    return keys


def payload_at_source_key(bundle: Dict[str, Any], source_key: str) -> Dict[str, Any]:
    parts = [part for part in source_key.split("/") if part]
    if parts == ["pr"]:
        payload = bundle.get("pr")
    elif len(parts) == 2 and parts[1].isdigit():
        values = bundle.get(parts[0])
        payload = values[int(parts[1])] if isinstance(values, list) else None
    else:
        payload = None
    if not isinstance(payload, dict):
        raise ValueError(f"source key does not resolve to an object: {source_key}")
    return payload


def build_event_ledger(
    *,
    bundles_dir: Path,
    out: Path,
    repo: str = "leanprover-community/mathlib4",
    prs: Optional[Iterable[int]] = None,
) -> Tuple[List[SourceEvent], Dict[str, Any]]:
    wanted = set(prs or [])
    events: List[SourceEvent] = []
    bundle_count = 0
    for bundle_path in sorted(bundles_dir.glob("pr_*.json")):
        bundle = json.loads(bundle_path.read_text())
        pr_number = int((bundle.get("pr") or {})["number"])
        if wanted and pr_number not in wanted:
            continue
        bundle_count += 1
        events.extend(events_from_bundle(bundle, bundle_path=bundle_path, repo=repo))
    present = {event.pr_number for event in events}
    missing = wanted - present
    if missing:
        raise ValueError(f"raw bundles missing requested PRs: {sorted(missing)}")

    events.sort(
        key=lambda event: (
            event.pr_number,
            event.occurred_at is None,
            event.occurred_at or "",
            event.event_type,
            event.event_id,
        )
    )
    ids = [event.event_id for event in events]
    if len(ids) != len(set(ids)):
        duplicates = [event_id for event_id, count in Counter(ids).items() if count > 1]
        raise ValueError(f"duplicate source event identities: {duplicates[:10]}")
    write_once(out, jsonl_bytes(events))
    report = {
        "bundles": bundle_count,
        "events": len(events),
        "prs": len(present),
        "by_type": dict(sorted(Counter(event.event_type for event in events).items())),
        "missing_timestamps": sum(event.occurred_at is None for event in events),
    }
    return events, report
