"""
Byte-reproducible serialization helpers.

Deliberately a local ~40-line copy rather than an import of
`src/datasets/pr_review_v4/io.py`: this package must stay free of code edges to any
pipeline generation so that any generation can consume it later.
"""

import hashlib
import json
from pathlib import Path
from typing import Iterable, Tuple

from pydantic import BaseModel


def canonical_json_bytes(payload) -> bytes:
    """Sorted keys, no incidental whitespace, trailing newline. Stable across runs."""
    if isinstance(payload, BaseModel):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2).encode() + b"\n"


def jsonl_bytes(records: Iterable) -> bytes:
    lines = []
    for record in records:
        if isinstance(record, BaseModel):
            record = record.model_dump(mode="json")
        lines.append(json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return ("\n".join(lines) + "\n").encode() if lines else b""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_bytes(path: Path, payload: bytes) -> Tuple[str, int]:
    """Write atomically and return (sha256, byte length)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(payload)
    tmp.replace(path)
    return sha256_bytes(payload), len(payload)


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)
